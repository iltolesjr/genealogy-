#!/usr/bin/env python3
"""Build a DNA Painter CSV containing all segments from one_to_one_combined_perfect.csv meeting a cM threshold."""
import csv
from pathlib import Path

ROOT = Path.cwd()
ONE2ONE = ROOT / 'outputs' / 'one_to_one_combined_perfect.csv'
OUT_ALL = ROOT / 'outputs' / 'dnapainter_all_segments.csv'
MIN_CM = 7.0


def build_all():
    if not ONE2ONE.exists():
        print('Missing', ONE2ONE)
        return
    rows = []
    with ONE2ONE.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                cm = float((r.get('cM') or r.get('cM ') or 0))
            except Exception:
                cm = 0.0
            if cm < MIN_CM:
                continue
            label = (r.get('Kit2') or r.get('Kit1') or '').strip()
            chr_ = (r.get('Chr') or '').strip()
            start = (r.get('Start') or '').strip()
            end = (r.get('End') or '').strip()
            rows.append({'Label': label, 'Chr': chr_, 'Start': start, 'End': end, 'cM': str(cm), 'Source': 'one_to_one_combined_perfect'})

    OUT_ALL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_ALL.open('w', encoding='utf-8', newline='') as fo:
        writer = csv.DictWriter(fo, fieldnames=['Label','Chr','Start','End','cM','Source'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f'Wrote {len(rows)} rows to {OUT_ALL}')

if __name__ == '__main__':
    build_all()
