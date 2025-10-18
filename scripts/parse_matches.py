import re
import csv
from pathlib import Path

repo = Path(r"c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-")
matches_file = repo / 'matches'
out_dir = repo / 'Research Data'
out_dir.mkdir(exist_ok=True)
out_csv = out_dir / 'matches_parsed.csv'
seg_csv = repo / 'scripts' / 'csvsegmatch_.csv'
triang_csv = repo / 'scripts' / 'triang_1250214825.csv'

text = matches_file.read_text(encoding='utf-8')
lines = text.splitlines()

blocks = []
current = []
for line in lines:
    s = line.strip()
    # treat 'Add' as block separator
    if s == 'Add':
        if current:
            blocks.append(current)
            current = []
    else:
        current.append(line)
# final block
if current:
    blocks.append(current)

parsed = []
for blk in blocks:
    # clean empty lines and view markers
    clean = [l.strip() for l in blk if l.strip() and l.strip()!='This match has not been viewed']
    if not clean:
        continue
    # find name: first line that looks like a real name (has letters and at least one space) OR first line otherwise
    name = None
    for l in clean:
        if re.search(r"[A-Za-z]", l) and 'managed by' not in l.lower() and not re.match(r"^[0-9<>,%\s|]+$", l):
            # exclude lines that are just numbers or cM lines
            # prefer lines with space (likely full name)
            if ' ' in l or re.search(r"[A-Z]{2,}", l):
                name = l
                break
    if not name:
        name = clean[0]
    # predicted relationship
    rel = ''
    for l in clean:
        if re.search(r'\b(cousin|uncle|grand|aunt|niece|sibling|half|removed)\b', l, re.I):
            rel = l
            break
    # side
    side = ''
    for l in clean:
        if 'Paternal side' in l:
            side = 'Paternal'
            break
        if 'Maternal side' in l:
            side = 'Maternal'
            break
    # shared cM
    shared_cm = ''
    for l in clean:
        m = re.search(r'([0-9,]+)\s*cM', l)
        if m:
            shared_cm = m.group(1).replace(',','')
            break
    try:
        shared_cm_v = int(shared_cm) if shared_cm else None
    except:
        shared_cm_v = None
    # tree status and size
    tree_status = ''
    tree_size = ''
    for l in clean:
        if re.search(r'linked tree', l, re.I) or re.search(r'No trees', l, re.I) or re.search(r'Unlinked tree', l, re.I):
            tree_status = l
            # next line might be count
            idx = clean.index(l)
            if idx+1 < len(clean) and re.search(r'\d{1,3}(,\d{3})*\s+people', clean[idx+1]):
                tree_size = clean[idx+1]
            break
    notes = '; '.join(clean)
    parsed.append({
        'match_name': name,
        'predicted_relationship': rel,
        'side': side,
        'shared_cm': shared_cm_v,
        'tree_status': tree_status,
        'tree_size': tree_size,
        'notes': notes
    })

# load segment CSV and aggregate cM by MatchedName
seg_map = {}
if seg_csv.exists():
    with seg_csv.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # ensure header names
        for r in reader:
            mname = (r.get('MatchedName') or r.get('MatchedName') or '').strip()
            try:
                seg_cm = float((r.get('Segment cM') or r.get('Segment cM') or '').strip())
            except:
                # try alternate key
                try:
                    seg_cm = float(r.get('Segment cM', 0))
                except:
                    seg_cm = 0.0
            key = mname.lower()
            seg_map.setdefault(key, []).append(seg_cm)

# read triang file into list of lines for substring search
triang_text = ''
if triang_csv.exists():
    triang_text = triang_csv.read_text(encoding='utf-8').lower()

# attach segment totals and triang hits
for p in parsed:
    name = p['match_name']
    name_l = name.lower()
    # find best seg_map key by substring match
    total_seg = 0.0
    seg_count = 0
    for k,v in seg_map.items():
        if name_l in k or k in name_l:
            seg_count = len(v)
            total_seg = sum(v)
            break
    p['segment_total_cm'] = round(total_seg,2)
    p['segment_count'] = seg_count
    p['triangulation_hit'] = False
    if triang_text and name_l in triang_text:
        p['triangulation_hit'] = True

# write CSV
keys = ['match_name','predicted_relationship','side','shared_cm','tree_status','tree_size','segment_total_cm','segment_count','triangulation_hit','notes']
with out_csv.open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    for r in parsed:
        w.writerow({k: r.get(k,'') for k in keys})

# console summary
# sort by shared_cm desc
parsed_sorted = sorted(parsed, key=lambda x: (x['shared_cm'] is None, -(x['shared_cm'] or 0)))
print('Parsed', len(parsed_sorted), 'matches; writing to', out_csv)
print('\nTop matches by shared cM:')
for r in parsed_sorted[:30]:
    print(f"{r['match_name']}	{r['shared_cm']}	{r['side']}	segments:{r['segment_count']}@{r['segment_total_cm']}cm\ttriang:{r['triangulation_hit']}")

# show Toles-like and paternal masks
import re as _re
pat = _re.compile(r"\b(toles|tolles|towles|tolls|tales|toals|toalson)\b", _re.I)
mask = [r for r in parsed_sorted if pat.search(r['match_name'] or '') or pat.search(r['notes'] or '')]
print('\nToles-like matches (from parsed):')
for r in mask:
    print(f"{r['match_name']}	{r['shared_cm']}	{r['side']}	segments:{r['segment_count']}@{r['segment_total_cm']}cm")

pat2 = lambda s: 'paternal' in (s or '').lower()
paternal = [r for r in parsed_sorted if pat2(r['side'])]
print('\nTop paternal-labeled matches:')
for r in paternal[:40]:
    print(f"{r['match_name']}	{r['shared_cm']}	segments:{r['segment_count']}@{r['segment_total_cm']}cm\ttriang:{r['triangulation_hit']}")

print('\nDone.')
