#!/usr/bin/env python3
"""Generate a DNA Painter one-to-one CSV enriched with Match Name, Kit and TG group,
grouped and sorted by number of segments (most -> least).

Usage: run from repo root or provide explicit paths inside the script.
"""
import csv
import os
import re
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, 'outputs')

SEG_FILE = os.path.join(OUT_DIR, 'dnapainter_all_segments.csv')
FALLBACK_SEG_FILE = os.path.join(OUT_DIR, 'dnapainter_import.csv')
MAP_FILE = os.path.join(OUT_DIR, 'one_to_one_combined.csv')
EXTRA_FILES = [
    os.path.join(OUT_DIR, 'temara_matches_raw.csv'),
    os.path.join(OUT_DIR, 'wilma_temara_common_triangulation.csv'),
]

OUT_FILE = os.path.join(OUT_DIR, 'dnapainter_import_with_names.csv')


def read_segments(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def build_name_map(map_path, labels):
    name_map = {}
    if not os.path.exists(map_path):
        return name_map
    with open(map_path, newline='', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            # many rows have Kit1,Kit2,... — Kit1 is often the kit id, Kit2 the name
            kit = row[0].strip()
            name = row[1].strip() if len(row) > 1 else ''
            # basic sanity checks
            if kit in labels and name and any(c.isalpha() for c in name):
                name_map[kit] = name
    return name_map


def search_extra_files_for_names(extra_paths, labels, name_map):
    # attempt to find patterns like A044456,"Temara Moore" or kit,name pairs
    kit_re = re.compile(r'([A-Z0-9]{2,12})')
    for p in extra_paths:
        if not os.path.exists(p):
            continue
        with open(p, encoding='utf-8', errors='ignore') as f:
            for line in f:
                if not any(lbl in line for lbl in labels):
                    continue
                # try to find quoted name after a kit
                # patterns: ,"Name" or ,"*Dr. Beasley" or ,Name,
                parts = [s.strip() for s in re.split('[,\t]', line) if s.strip()]
                for i, part in enumerate(parts):
                    for lbl in labels:
                        if lbl == part or lbl in part:
                            # try next field for a name
                            if i+1 < len(parts):
                                cand = parts[i+1].strip('"')
                                if cand and any(c.isalpha() for c in cand):
                                    name_map.setdefault(lbl, cand)
    return name_map


def try_extract_tg_from_extra(extra_paths, labels):
    tg_map = {}
    # look for tokens like TG19_1 or patterns with 'TG' or a numeric group near the kit
    tg_re = re.compile(r'TG\d+(_\d+)?', re.IGNORECASE)
    for p in extra_paths:
        if not os.path.exists(p):
            continue
        with open(p, encoding='utf-8', errors='ignore') as f:
            for line in f:
                for lbl in labels:
                    if lbl in line:
                        m = tg_re.search(line)
                        if m:
                            tg_map.setdefault(lbl, m.group(0))
    return tg_map


def main():
    seg_path = SEG_FILE if os.path.exists(SEG_FILE) else FALLBACK_SEG_FILE
    if not os.path.exists(seg_path):
        print('No segment file found at', SEG_FILE, 'or', FALLBACK_SEG_FILE)
        return

    segs = read_segments(seg_path)
    labels = sorted({r['Label'] for r in segs if r.get('Label')})

    name_map = build_name_map(MAP_FILE, labels)
    name_map = search_extra_files_for_names(EXTRA_FILES, labels, name_map)
    tg_map = try_extract_tg_from_extra(EXTRA_FILES, labels)

    # Count segments per label
    cnt = Counter(r['Label'] for r in segs)
    labels_sorted = [l for l, _ in cnt.most_common()]

    # write enriched file with new header
    header = ['Label','MatchName','KitNumber','Chr','Start','End','cM','Source','TGGroup']
    with open(OUT_FILE, 'w', newline='', encoding='utf-8') as out:
        w = csv.writer(out)
        w.writerow(header)
        for lbl in labels_sorted:
            mname = name_map.get(lbl, '')
            tg = tg_map.get(lbl, '')
            for r in segs:
                if r.get('Label') != lbl:
                    continue
                w.writerow([
                    lbl,
                    mname,
                    lbl,
                    r.get('Chr',''),
                    r.get('Start',''),
                    r.get('End',''),
                    r.get('cM',''),
                    r.get('Source',''),
                    tg,
                ])

    print('Wrote', OUT_FILE)
    print('Top matches by segment count:')
    for i, (lbl, c) in enumerate(cnt.most_common(20), 1):
        print(f'{i}. {lbl} ({c} segments) - name: {name_map.get(lbl, "")}, tg: {tg_map.get(lbl, "")})')


if __name__ == '__main__':
    main()
