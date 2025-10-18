#!/usr/bin/env python3
"""Scan CSV files for segments overlapping a specified interval and annotate with kit tags.

Defaults target TG4_2 interval used in the conversation: chr=4, start=80989462, end=93198845
Outputs `outputs/triangulation_query_chr{chr}_{start}_{end}.csv` with file, line, chr,start,end,cM,kit1,kit2,tag1,tag2
"""
import csv
from pathlib import Path
import re

ROOT = Path.cwd()
OUTDIR = ROOT / 'outputs'
OUTDIR.mkdir(exist_ok=True)

# Query interval (TG4_2 block approx from page)
CHR = '4'
START = 80989462
END = 93198845


def load_tags(path: Path):
    tags = {}
    if not path.exists():
        return tags
    with path.open(encoding='utf-8') as f:
        for line in f:
            parts = [p.strip() for p in line.split(',')]
            if not parts or parts[0].startswith('#'):
                continue
            kit = parts[0]
            tag = parts[1] if len(parts) > 1 else ''
            tags[kit] = tag
    return tags


def normalize_int(x):
    try:
        return int(str(x).replace(',', '').strip())
    except Exception:
        return None


def scan_csv_for_overlap(path: Path, chrq, startq, endq):
    matches = []
    with path.open(encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return matches
        # find candidate positions for chr,start,end,cM and kit columns
        lc = [h.lower() for h in headers]
        def find_keywords(keywords):
            for idx, h in enumerate(lc):
                for k in keywords:
                    if k in h:
                        return idx
            return None

        idx_chr = find_keywords(['chr','chromosome'])
        idx_start = find_keywords(['start','b37 start','from'])
        idx_end = find_keywords(['end','b37 end','to'])
        idx_cm = find_keywords(['cm','centimorgan'])
        # kit columns often first two
        idx_kit1 = 0 if len(headers) > 0 else None
        idx_kit2 = 1 if len(headers) > 1 else None

        if idx_chr is None or idx_start is None or idx_end is None:
            return matches

        for lineno, row in enumerate(reader, start=2):
            try:
                ch = row[idx_chr].strip()
            except Exception:
                continue
            if ch != chrq:
                continue
            s = normalize_int(row[idx_start])
            e = normalize_int(row[idx_end])
            if s is None or e is None:
                continue
            if not (e < startq or s > endq):
                cm = ''
                if idx_cm is not None and idx_cm < len(row):
                    cm = row[idx_cm].strip()
                k1 = row[idx_kit1].strip() if idx_kit1 is not None and idx_kit1 < len(row) else ''
                k2 = row[idx_kit2].strip() if idx_kit2 is not None and idx_kit2 < len(row) else ''
                matches.append({'file': str(path), 'line': lineno, 'chr': ch, 'start': s, 'end': e, 'cM': cm, 'kit1': k1, 'kit2': k2})
    return matches


def main():
    tags = load_tags(ROOT / 'data' / 'kit_tags.csv')
    files = list(ROOT.rglob('*.csv'))
    hits = []
    for p in files:
        hits.extend(scan_csv_for_overlap(p, CHR, START, END))

    outpath = OUTDIR / f'triangulation_query_chr{CHR}_{START}_{END}.csv'
    with outpath.open('w', encoding='utf-8', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(['file','line','chr','start','end','cM','kit1','kit2','tag1','tag2'])
        for h in hits:
            tag1 = tags.get(h['kit1'], '')
            tag2 = tags.get(h['kit2'], '')
            writer.writerow([h['file'], h['line'], h['chr'], h['start'], h['end'], h['cM'], h['kit1'], h['kit2'], tag1, tag2])

    print(f'Wrote {len(hits)} hits to {outpath}')
    # print summary counts by tag
    counts = {}
    for h in hits:
        for k in (h['kit1'], h['kit2']):
            if not k:
                continue
            t = tags.get(k,'(untagged)')
            counts[t] = counts.get(t,0) + 1
    print('Tag counts (approx):')
    for t,c in sorted(counts.items(), key=lambda x:-x[1]):
        print(f'{t}: {c}')


if __name__ == '__main__':
    main()
