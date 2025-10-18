#!/usr/bin/env python3
"""Find all segment rows in CSV files that overlap a given interval.

Usage: run with no args (script will use hard-coded interval below) or edit interval variables.
It scans CSV files under the repo for files whose header contains Chr/Start/End (case-insensitive).
Outputs matches to stdout and writes `outputs/triangulation_hits_chr{chr}_{start}_{end}.csv`.
"""
import csv
from pathlib import Path
import sys

ROOT = Path.cwd()
OUTDIR = ROOT / 'outputs'
OUTDIR.mkdir(exist_ok=True)

# Interval to search (B37 coordinates)
CHR = '4'
START = 134815036
END = 141236020


def normalize_int(x):
    try:
        return int(str(x).replace(',', '').strip())
    except Exception:
        return None


def header_map(headers):
    # return indices for chr,start,end,cM
    lc = [h.lower() for h in headers]
    def find_keywords(keywords):
        for idx, h in enumerate(lc):
            for k in keywords:
                if k in h:
                    return idx
        return None

    return {
        'chr': find_keywords(['chr', 'chrom', 'chromosome']),
        'start': find_keywords(['start', 'from', "b37 start", 'b37 start pos', 'b37 start posn']),
        'end': find_keywords(['end', 'to', "b37 end", 'b37 end pos', 'b37 end posn']),
        'cM': find_keywords(['cm', 'centimorgan', 'centimorgans'])
    }


def scan_file(path: Path):
    matches = []
    try:
        with path.open(encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            headers = next(reader)
            # try to locate chr,start,end
            hm = header_map(headers)
            if hm['chr'] is None or hm['start'] is None or hm['end'] is None:
                return matches
            for i,row in enumerate(reader, start=2):
                try:
                    chrv = row[hm['chr']].strip()
                except Exception:
                    continue
                if chrv != CHR:
                    continue
                s = normalize_int(row[hm['start']])
                e = normalize_int(row[hm['end']])
                if s is None or e is None:
                    continue
                # overlap test
                if not (e < START or s > END):
                    # capture cM if available
                    cm = ''
                    if hm.get('cM') is not None and hm['cM'] < len(row):
                        cm = row[hm['cM']]
                    matches.append({'file': str(path), 'line': i, 'row': row, 'start': s, 'end': e, 'cM': cm})
    except Exception:
        return matches
    return matches


def main():
    files = list(ROOT.rglob('*.csv'))
    all_matches = []
    for f in files:
        ms = scan_file(f)
        if ms:
            all_matches.extend(ms)

    outpath = OUTDIR / f'triangulation_hits_chr{CHR}_{START}_{END}.csv'
    with outpath.open('w', encoding='utf-8', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(['file','line','start','end','cM','row_preview'])
        for m in all_matches:
            writer.writerow([m['file'], m['line'], m['start'], m['end'], m['cM'], ';'.join(m['row'][:10])])

    print(f'Found {len(all_matches)} overlapping rows; wrote {outpath}')
    for m in all_matches:
        print(m['file'], 'line', m['line'], 'start', m['start'], 'end', m['end'], 'cM', m['cM'])


if __name__ == '__main__':
    main()
