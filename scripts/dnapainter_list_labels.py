#!/usr/bin/env python3
from pathlib import Path
import csv

ROOT = Path.cwd()
PAT = ROOT / 'outputs' / 'dnapainter_paternal.csv'
MAT = ROOT / 'outputs' / 'dnapainter_maternal.csv'
ALL = ROOT / 'outputs' / 'dnapainter_all_segments.csv'


def labels(path):
    s = set()
    if not path.exists():
        return s
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            s.add((r.get('Label') or '').strip())
    return s

p = labels(PAT)
m = labels(MAT)
a = labels(ALL)

print('paternal unique labels:', len(p))
print('\n'.join(sorted(list(p))[:50]))
print('\n---\n')
print('maternal unique labels:', len(m))
print('\n'.join(sorted(list(m))[:50]))
print('\n---\n')
print('all unique labels (sample 50):', len(a))
print('\n'.join(sorted(list(a))[:50]))
