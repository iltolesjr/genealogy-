#!/usr/bin/env python3
from pathlib import Path
import csv

ROOT = Path.cwd()
PAT = ROOT / 'outputs' / 'dnapainter_paternal.csv'
MAT = ROOT / 'outputs' / 'dnapainter_maternal.csv'
ALL = ROOT / 'outputs' / 'dnapainter_all_segments.csv'


def sample(path: Path, n=10):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for i,r in enumerate(reader):
            if i>=n: break
            rows.append(r)
    return rows


def count(path: Path):
    if not path.exists():
        return 0
    with path.open(encoding='utf-8') as f:
        return sum(1 for _ in f)-1


print('paternal count:', count(PAT))
print('maternal count:', count(MAT))
print('all count:', count(ALL))
print('\nSample paternal rows:', sample(PAT, 10))
print('\nSample maternal rows:', sample(MAT, 10))
print('\nSample all rows:', sample(ALL, 10))
