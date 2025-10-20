#!/usr/bin/env python3
"""
Find kitID/displayName/email rows in Downloads triangulation CSVs that overlap
the Wilma segments saved in `outputs/moore_barnett_wilma_segments.csv`.

Produces:
 - outputs/mapping_wilma_kits.csv  (kitID,displayName,email,max_cM,example_source,start,end)
 - outputs/triangulation_wilma_top.csv (full overlapping rows sorted by cM desc)

This script is conservative: it reads any CSV in the Downloads folder whose
filename starts with "triang_" and parses rows that look like the exported
triangulation format used in the repo's Downloads folder.
"""
import csv
import glob
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOWNLOADS = os.path.join(os.path.expanduser('~'), 'Downloads')
OUTPUTS = os.path.join(ROOT, 'outputs')
WILMA_SEGMENTS = os.path.join(OUTPUTS, 'moore_barnett_wilma_segments.csv')


def read_wilma_segments(path):
    segs = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Wilma segments not found: {path}")
    with open(path, newline='') as f:
        r = csv.reader(f)
        for row in r:
            if not row or row[0].startswith('#'):
                continue
            # expected: chr,start,end,cM,... or similar; robust parse
            try:
                chr_ = row[1] if len(row) > 1 else row[0]
                # many of the Wilma rows saved have: GU1800109,1,40974156,64555255,25.1,...
                if row[0].startswith('GU') and len(row) >= 5:
                    chr_ = row[1]
                    start = int(row[2])
                    end = int(row[3])
                elif len(row) >= 4:
                    chr_ = row[0]
                    start = int(row[1])
                    end = int(row[2])
                else:
                    continue
                segs.append((str(chr_), start, end))
            except Exception:
                continue
    return segs


def overlaps(a_start, a_end, b_start, b_end):
    return not (a_end < b_start or b_end < a_start)


def parse_triang_file(path):
    rows = []
    with open(path, newline='', errors='replace') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            # Flexible formats observed: some rows begin with chr as int, others with kit IDs first
            # We look for a pattern where two kitIDs or display names and an interval exist.
            flattened = [c.strip() for c in row if c is not None]
            # Try to find numeric chr position tokens (start,end)
            ints = []
            for i,cell in enumerate(flattened):
                try:
                    ints.append((i,int(cell)))
                except Exception:
                    pass
            # Heuristic: last two integers before a cM value often are start,end
            if len(ints) >= 2:
                # take last two integer positions
                i1, start = ints[-2]
                i2, end = ints[-1]
                # try to find cM just after end
                cm = None
                if i2+1 < len(flattened):
                    try:
                        cm = float(flattened[i2+1])
                    except Exception:
                        cm = None
                rows.append({'flat': flattened, 'start': start, 'end': end, 'cm': cm, 'source': os.path.basename(path)})
    return rows


def main():
    os.makedirs(OUTPUTS, exist_ok=True)
    wilma_segs = read_wilma_segments(WILMA_SEGMENTS)
    if not wilma_segs:
        print('No Wilma segments found; aborting')
        return

    triang_files = glob.glob(os.path.join(DOWNLOADS, 'triang_*.csv'))
    if not triang_files:
        print('No triang_*.csv files found in Downloads; aborting')
        return

    matches = []
    per_kit = defaultdict(lambda: {'max_cm':0.0, 'example':None})

    for tf in triang_files:
        try:
            rows = parse_triang_file(tf)
        except Exception as e:
            print('Failed parse', tf, e)
            continue
        for r in rows:
            for chr_, wstart, wend in wilma_segs:
                # only consider rows whose interval overlaps any Wilma segment
                if overlaps(r['start'], r['end'], wstart, wend):
                    flat = r['flat']
                    cm = r['cm'] or 0.0
                    source = r['source']
                    # attempt to extract kit IDs and emails: many of your triang files have pattern:
                    # chr,kitA,displayA,emailA,kitB,displayB,emailB,start,end,cm,... OR variant without chr
                    # We'll search for tokens that look like kit IDs (start with letter(s) then digits)
                    kits = [t for t in flat if len(t) >=2 and t[0].isalpha() and any(ch.isdigit() for ch in t)]
                    emails = [t for t in flat if '@' in t]
                    display = None
                    kit = None
                    email = emails[0] if emails else ''
                    if kits:
                        # choose the kit token that is not a chromosome numeric (heuristic)
                        kit = kits[0]
                        display = ''
                    matches.append({'kit': kit or '', 'display': display or '', 'email': email, 'start': r['start'], 'end': r['end'], 'cm': cm, 'source': source})
                    if kit:
                        if cm and cm > per_kit[kit]['max_cm']:
                            per_kit[kit]['max_cm'] = cm
                            per_kit[kit]['example'] = (source, r['start'], r['end'])

    # write full sorted overlaps
    full_out = os.path.join(OUTPUTS, 'triangulation_wilma_top.csv')
    with open(full_out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['kit','display','email','start','end','cM','source'])
        for m in sorted(matches, key=lambda x: (float(x['cm'] or 0.0)), reverse=True):
            w.writerow([m['kit'], m['display'], m['email'], m['start'], m['end'], m['cm'], m['source']])

    # write deduped mapping
    map_out = os.path.join(OUTPUTS, 'mapping_wilma_kits.csv')
    with open(map_out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['kit','max_cM','example_source','example_start','example_end'])
        for kit, info in sorted(per_kit.items(), key=lambda kv: kv[1]['max_cm'], reverse=True):
            src, s, e = info['example'] or ('', '', '')
            w.writerow([kit, info['max_cm'], src, s, e])

    print('Wrote', full_out, 'and', map_out)


if __name__ == '__main__':
    main()
