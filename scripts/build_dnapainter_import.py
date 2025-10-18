#!/usr/bin/env python3
"""Create a DNA Painter import CSV from one-to-one segment exports.

Reads `outputs/one_to_one_combined_perfect.csv` (created by the extractor) and `data/kit_tags.csv`.
Filters segments where either Kit1 or Kit2 matches an anchor/tag (by kit id) and writes
`outputs/dnapainter_import.csv` with columns: Label,Chr,Start,End,cM,Source

Label will be the tag from kit_tags.csv if available, otherwise the kit id.
Source will be the original file marker 'AutoKinship' for provenance.
"""
import csv
from pathlib import Path

ROOT = Path.cwd()
IN = ROOT / 'outputs' / 'one_to_one_combined_perfect.csv'
TAGS = ROOT / 'data' / 'kit_tags.csv'
OUT = ROOT / 'outputs' / 'dnapainter_import.csv'


def load_tags(path: Path):
    tags = {}
    if not path.exists():
        return tags
    with path.open(encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                tags[parts[0]] = parts[1]
    return tags


def build_import():
    tags = load_tags(TAGS)
    if not IN.exists():
        print('Input file missing:', IN)
        return

    with IN.open(encoding='utf-8') as fin, OUT.open('w', encoding='utf-8', newline='') as fout:
        reader = csv.DictReader(fin)
        writer = csv.writer(fout)
        writer.writerow(['Label','Chr','Start','End','cM','Source'])
        count = 0
        for r in reader:
            k1 = r.get('Kit1','').strip()
            k2 = r.get('Kit2','').strip()
            # include if either kit is tagged or equal to GU1800109 (your anchor)
            interested = False
            label = ''
            for k in (k1,k2):
                if k in tags:
                    interested = True
                    label = tags[k]
                    break
            if not interested and (k1 == 'GU1800109' or k2 == 'GU1800109'):
                interested = True
                label = 'Toles_anchor'

            if interested:
                chr_ = r.get('Chr','').strip()
                start = r.get('Start','').strip()
                end = r.get('End','').strip()
                cm = r.get('cM','').strip()
                # ensure numeric types where possible
                try:
                    if cm:
                        cm = float(cm)
                except Exception:
                    pass
                writer.writerow([label or k2 or k1, chr_, start, end, cm, 'AutoKinship'])
                count += 1

    print(f'Wrote {count} rows to {OUT}')


if __name__ == '__main__':
    build_import()
