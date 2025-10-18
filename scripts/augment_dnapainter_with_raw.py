#!/usr/bin/env python3
"""Augment the DNAPainter CSV (`outputs/dnapainter_import.csv`) with raw segment files
found in the workspace (Downloads csvsegmatch files, triangulation exports, etc.).

It looks for rows that mention the anchor `GU1800109` or any kit in `data/kit_tags.csv` and
appends them (deduplicated) to `outputs/dnapainter_import_allsources.csv`.
"""
from pathlib import Path
import csv
import re

ROOT = Path.cwd()
BASE = ROOT / 'outputs' / 'dnapainter_import.csv'
OUT = ROOT / 'outputs' / 'dnapainter_import_allsources.csv'
TAGS = ROOT / 'data' / 'kit_tags.csv'

ANCHOR = 'GU1800109'
MIN_CM = 7.0


def load_tags(path):
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


def read_existing(path):
    seen = set()
    rows = []
    if not path.exists():
        return seen, rows
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (r['Label'], r['Chr'], r['Start'], r['End'], r['cM'])
            seen.add(key)
            rows.append(r)
    return seen, rows


def parse_raw_csv(path, tags, seen, rows):
    # attempt to read each row; common positional format: Kit1,Kit2,Chr,Start,End,cM,SNPs,...
    with path.open(encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        try:
            first = next(reader)
        except StopIteration:
            return
        # determine if first row looks like header
        header_like = any('kit' in c.lower() or 'chr' in c.lower() or 'start' in c.lower() for c in first)
        if header_like:
            # push back
            f.seek(0)
            reader = csv.reader(f)
        for row in reader:
            if len(row) < 6:
                continue
            k1 = row[0].strip()
            k2 = row[1].strip()
            chr_ = row[2].strip()
            start = row[3].strip().replace(' ', '').replace(',', '')
            end = row[4].strip().replace(' ', '').replace(',', '')
            cm_raw = row[5].strip()
            try:
                cm = float(cm_raw)
            except Exception:
                continue
            if cm < MIN_CM:
                continue
            # include if anchor present or either kit in tags
            if ANCHOR in (k1, k2) or k1 in tags or k2 in tags:
                other = k2 if k1 == ANCHOR or k1 in tags else k1
                label = tags.get(other, other)
                key = (label, chr_, start, end, str(cm))
                if key in seen:
                    continue
                seen.add(key)
                rows.append({'Label': label, 'Chr': chr_, 'Start': start, 'End': end, 'cM': str(cm), 'Source': f'raw:{path.name}'})


def main():
    tags = load_tags(TAGS)
    seen, rows = read_existing(BASE)

    # scan for raw CSVs likely to contain segments
    for p in (ROOT / 'c:\\Users\\irato\\Downloads').glob('**/*.csv') if False else Path('c:/Users/irato/Downloads').glob('**/*.csv'):
        # include files with csvsegmatch or triang or segmatch in name
        if any(tok in p.name.lower() for tok in ('csvsegmatch', 'triang', 'segmatch')):
            try:
                parse_raw_csv(p, tags, seen, rows)
            except Exception:
                continue

    # also scan workspace CSVs
    for p in ROOT.rglob('*.csv'):
        if p.parts and 'Downloads' in str(p):
            continue
        if any(tok in p.name.lower() for tok in ('csvsegmatch', 'triang', 'segmatch')):
            try:
                parse_raw_csv(p, tags, seen, rows)
            except Exception:
                continue

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8', newline='') as fo:
        writer = csv.DictWriter(fo, fieldnames=['Label','Chr','Start','End','cM','Source'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f'Wrote {len(rows)} rows to {OUT}')


if __name__ == '__main__':
    main()
