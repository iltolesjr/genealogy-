#!/usr/bin/env python3
"""Build a DNA Painter import CSV from the perfect one-to-one CSV and kit tags.

Output columns: Label,Chr,Start,End,cM,Source
Filters: include segments where Kit1==GU1800109 or Kit2==GU1800109 OR either kit is in data/kit_tags.csv.
Default cM threshold: 7.0 (configurable)
"""
import csv
from pathlib import Path

ROOT = Path.cwd()
ONE2ONE = ROOT / 'outputs' / 'one_to_one_combined_perfect.csv'
TAGS = ROOT / 'data' / 'kit_tags.csv'
OUT = ROOT / 'outputs' / 'dnapainter_import.csv'

MIN_CM = 7.0
ANCHOR = 'GU1800109'


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


def build():
    tags = load_tags(TAGS)
    if not ONE2ONE.exists():
        print('Missing one-to-one CSV:', ONE2ONE)
        return

    out_rows = []
    with ONE2ONE.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # ensure numeric cM
            try:
                cm = float(r.get('cM') or r.get('cM') or r.get('cM ' ) or 0)
            except Exception:
                # try lowercase
                try:
                    cm = float(r.get('cM') or r.get('cM') or 0)
                except Exception:
                    cm = 0.0

            k1 = (r.get('Kit1') or '').strip()
            k2 = (r.get('Kit2') or '').strip()
            chr_ = (r.get('Chr') or '').strip()
            start = (r.get('Start') or '').strip()
            end = (r.get('End') or '').strip()

            include = False
            label = ''
            src = 'one_to_one_combined_perfect'

            if cm >= MIN_CM:
                if k1 == ANCHOR or k2 == ANCHOR:
                    include = True
                    label = tags.get(k1 if k1 != ANCHOR else k2, k2 if k1==ANCHOR else k1)
                elif k1 in tags or k2 in tags:
                    include = True
                    # prefer tag value
                    label = tags.get(k1) or tags.get(k2) or k2 or k1

            if include:
                if not label:
                    label = k2 or k1
                out_rows.append({'Label': label, 'Chr': chr_, 'Start': start, 'End': end, 'cM': str(cm), 'Source': src})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8', newline='') as fo:
        writer = csv.DictWriter(fo, fieldnames=['Label','Chr','Start','End','cM','Source'])
        writer.writeheader()
        for r in out_rows:
            writer.writerow(r)

    print(f'Wrote {len(out_rows)} rows to {OUT}')


if __name__ == '__main__':
    build()
