#!/usr/bin/env python3
"""Build DNA Painter CSVs grouped by paternal/maternal using AutoSegment/AutoKinship extracts.

Steps:
 - Ensure outputs/one_to_one_combined_perfect.csv exists (runs extract_autokinship_segments.py if needed)
 - Read data/kit_tags.csv to tag kits; heuristic: tag contains 'pat' -> paternal, 'mat' -> maternal
 - For each segment row where either Kit1 or Kit2 is tagged paternal or maternal and cM >= MIN_CM, emit a DNA Painter row into the corresponding CSV.
 - Output files: outputs/dnapainter_paternal.csv, outputs/dnapainter_maternal.csv
"""
from pathlib import Path
import csv
import subprocess
import sys

ROOT = Path.cwd()
ONE2ONE = ROOT / 'outputs' / 'one_to_one_combined_perfect.csv'
TAGS = ROOT / 'data' / 'kit_tags.csv'
OUT_PAT = ROOT / 'outputs' / 'dnapainter_paternal.csv'
OUT_MAT = ROOT / 'outputs' / 'dnapainter_maternal.csv'
MIN_CM = 7.0


def ensure_one2one():
    if not ONE2ONE.exists():
        print('one_to_one_combined_perfect.csv missing; running extract_autokinship_segments.py')
        script = ROOT / 'scripts' / 'extract_autokinship_segments.py'
        if not script.exists():
            print('Missing helper script:', script)
            return False
        subprocess.check_call([sys.executable, str(script)])
    return ONE2ONE.exists()


def load_tags(path: Path):
    tags = {}
    if not path.exists():
        return tags
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            kit = (r.get('kit') or '').strip()
            tag = (r.get('tag') or '').strip()
            if kit:
                tags[kit] = tag
    return tags


def tag_to_side(tag: str):
    if not tag:
        return 'unknown'
    t = tag.lower()
    if 'pat' in t:
        return 'paternal'
    if 'mat' in t:
        return 'maternal'
    # also allow cluster names containing known maternal anchors
    if 'tate' in t or 'hoskins' in t or 'moore' in t:
        return 'maternal'
    if 'williams' in t or 'barnett' in t or 'toles' in t:
        # ambiguous but treat as paternal default for now
        return 'paternal'
    return 'unknown'


def build():
    ok = ensure_one2one()
    if not ok:
        print('Cannot proceed without', ONE2ONE)
        return

    tags = load_tags(TAGS)

    paternal_rows = []
    maternal_rows = []

    with ONE2ONE.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                cm = float(r.get('cM') or r.get('cM ') or 0)
            except Exception:
                cm = 0.0
            if cm < MIN_CM:
                continue
            k1 = (r.get('Kit1') or '').strip()
            k2 = (r.get('Kit2') or '').strip()
            chr_ = (r.get('Chr') or '').strip()
            start = (r.get('Start') or '').strip()
            end = (r.get('End') or '').strip()

            # determine side: if either kit has a tag indicating paternal or maternal
            side = 'unknown'
            t1 = tag_to_side(tags.get(k1, ''))
            t2 = tag_to_side(tags.get(k2, ''))
            if t1 == 'paternal' or t2 == 'paternal':
                side = 'paternal'
            if t1 == 'maternal' or t2 == 'maternal':
                # maternal wins if any maternal tag (prefer maternal when ambiguous)
                side = 'maternal'

            label = tags.get(k1) or tags.get(k2) or (k2 or k1)
            src = 'one_to_one_combined_perfect'
            row = {'Label': label, 'Chr': chr_, 'Start': start, 'End': end, 'cM': str(cm), 'Source': src}

            if side == 'paternal':
                paternal_rows.append(row)
            elif side == 'maternal':
                maternal_rows.append(row)

    OUT_PAT.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PAT.open('w', encoding='utf-8', newline='') as fo:
        writer = csv.DictWriter(fo, fieldnames=['Label','Chr','Start','End','cM','Source'])
        writer.writeheader()
        for r in paternal_rows:
            writer.writerow(r)

    with OUT_MAT.open('w', encoding='utf-8', newline='') as fo:
        writer = csv.DictWriter(fo, fieldnames=['Label','Chr','Start','End','cM','Source'])
        writer.writeheader()
        for r in maternal_rows:
            writer.writerow(r)

    print(f'Wrote {len(paternal_rows)} paternal and {len(maternal_rows)} maternal rows to outputs')


if __name__ == '__main__':
    build()
