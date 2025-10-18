#!/usr/bin/env python3
"""Extract segment rows from AutoKinship HTML outputs (AutoSegment and AutoKinship files).

Scans the Downloads AutoKinship folder for files containing JS arrays like `var tableDataB = [...]`
or JSON blocks with `segments` entries. For each segment it emits a row with columns:
Kit1,Kit2,Chr,Start,End,cM,SNPs

This produces a much cleaner, high-fidelity export when AutoKinship output is available.
"""
import json
import re
from pathlib import Path

ROOT = Path('c:/Users/irato/Downloads/AutoKinship_2025.10.14.17.46.39')
OUT = Path.cwd() / 'outputs' / 'one_to_one_combined_perfect.csv'


def find_html_files(root: Path):
    if not root.exists():
        return []
    return list(root.rglob('*.html'))


def extract_owner_kit(text: str):
    # Look for subtitle like: <h2 class="subtitle">For: GU1800109 GEDmatch: Ira L Toles October 14 2025 </h2>
    m = re.search(r'For:\s*([A-Z0-9_]+)\b', text)
    if m:
        return m.group(1)
    # fallback: look for "kitNum":"GU..."
    m2 = re.search(r'"kitNum"\s*:\s*"([A-Z0-9_]+)"', text)
    if m2:
        return m2.group(1)
    return ''


def extract_json_arrays(text: str):
    arrays = []
    # find var tableDataB = [ ... ]; or var tableData = [ ... ];
    for name in ('tableDataB', 'tableData'):
        for m in re.finditer(rf'{name}\s*=\s*(\[.*?\]);', text, flags=re.S):
            arrays.append(m.group(1))
    # also look for segments: "segments":"[{...}]" (JSON string inside field)
    for m in re.finditer(r'"segments"\s*:\s*"(\[.*?\])"', text, flags=re.S):
        # unescape quotes
        s = m.group(1).replace('\\"', '"')
        arrays.append(s)
    return arrays


def parse_array_string(arrstr: str):
    try:
        data = json.loads(arrstr)
        if isinstance(data, list):
            return data
    except Exception:
        # Try to fix trailing commas or unquoted keys
        try:
            # replace single quotes with double if present
            s = arrstr
            s = re.sub(r',\s*\]', ']', s)
            data = json.loads(s)
            return data
        except Exception:
            return []
    return []


def extract_segments_from_file(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    owner = extract_owner_kit(text)
    arrays = extract_json_arrays(text)
    rows = []
    for arr in arrays:
        objs = parse_array_string(arr)
        for obj in objs:
            # obj may be a match summary or a segment object depending on file
            # If the object itself contains a 'segments' list, iterate those
            if isinstance(obj, dict) and 'segments' in obj and isinstance(obj['segments'], list):
                # parent may include kitnum
                parent_kit = obj.get('kitnum') or obj.get('kitNum') or obj.get('kitnumber') or ''
                for seg in obj['segments']:
                    k2 = parent_kit
                    chr_ = seg.get('chromosome') or seg.get('chr') or seg.get('chrom')
                    start = seg.get('start') or seg.get('From') or seg.get('from')
                    end = seg.get('end') or seg.get('To') or seg.get('to')
                    cm = seg.get('seg_cm') or seg.get('segCm') or seg.get('cM') or seg.get('total_cM') or seg.get('cm')
                    snps = seg.get('num_snps') or seg.get('snps') or seg.get('snp')
                    # name/kit may be in seg or parent
                    name = seg.get('name') or obj.get('name')
                    matchurl = seg.get('matchurl') or obj.get('matchurl')
                    # try to extract kit id from matchurl like ..\/matches\/GEDmatch_SF088248C1.html
                    kit2 = k2
                    if not kit2 and matchurl:
                        m = re.search(r'GEDmatch_([A-Za-z0-9_]+)\.html', matchurl)
                        if m:
                            kit2 = m.group(1)
                    if not kit2 and isinstance(name, str):
                        # sometimes name is like 'greta mitchell' and kit in another field; skip
                        kit2 = ''

                    rows.append({'Kit1': owner, 'Kit2': kit2, 'Chr': str(chr_) if chr_ is not None else '', 'Start': start or '', 'End': end or '', 'cM': cm or '', 'SNPs': snps or ''})
            else:
                # obj may itself be a segment object
                if isinstance(obj, dict) and ('cM' in obj or 'seg_cm' in obj or 'start' in obj):
                    chr_ = obj.get('chr') or obj.get('chromosome')
                    start = obj.get('start')
                    end = obj.get('end')
                    cm = obj.get('cM') or obj.get('seg_cm') or obj.get('segCm') or obj.get('total_cM')
                    snps = obj.get('snps') or obj.get('num_snps')
                    kit2 = obj.get('kitnumber') or obj.get('kitnum') or ''
                    matchurl = obj.get('matchurl')
                    if not kit2 and matchurl:
                        m = re.search(r'GEDmatch_([A-Za-z0-9_]+)\.html', matchurl)
                        if m:
                            kit2 = m.group(1)
                    rows.append({'Kit1': owner, 'Kit2': kit2, 'Chr': str(chr_) if chr_ is not None else '', 'Start': start or '', 'End': end or '', 'cM': cm or '', 'SNPs': snps or ''})

    return rows


def main():
    files = find_html_files(ROOT)
    print(f'Found {len(files)} HTML files under {ROOT}')
    all_rows = []
    for f in files:
        try:
            rows = extract_segments_from_file(f)
            if rows:
                all_rows.extend(rows)
        except Exception as e:
            print('Error parsing', f, e)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # write CSV
    with OUT.open('w', encoding='utf-8') as fo:
        fo.write('Kit1,Kit2,Chr,Start,End,cM,SNPs\n')
        for r in all_rows:
            fo.write(f"{r['Kit1']},{r['Kit2']},{r['Chr']},{r['Start']},{r['End']},{r['cM']},{r['SNPs']}\n")

    print(f'Wrote {len(all_rows)} rows to {OUT}')


if __name__ == '__main__':
    main()
