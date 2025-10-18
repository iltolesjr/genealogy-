#!/usr/bin/env python3
"""Tag parsed GEDmatch segments with tags from data/kit_tags.csv.

Usage: python scripts/tag_gedmatch_segments.py
Reads:
  - outputs/gedmatch_segments.csv
  - data/kit_tags.csv
Writes:
  - outputs/gedmatch_segments_tagged.csv

This script does lightweight matching: it searches each input row for any kit IDs
present in `data/kit_tags.csv` and appends a `tags` column (comma-separated tags).
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_CSV = ROOT / 'outputs' / 'gedmatch_segments.csv'
TAGS_CSV = ROOT / 'data' / 'kit_tags.csv'
OUT_CSV = ROOT / 'outputs' / 'gedmatch_segments_tagged.csv'


def load_tags(path):
    tags = {}
    if not path.exists():
        return tags
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader([l.strip('`\n') for l in f if l.strip()])
        for r in reader:
            kit = r.get('kit') or r.get('Kit')
            tag = r.get('tag') or r.get('Tag')
            if kit and tag:
                tags[kit.strip()] = tag.strip()
    return tags


def tag_rows(input_path, tags_map, out_path):
    if not input_path.exists():
        print('Input file not found:', input_path)
        return 0

    # Read entire file as lines (robust to malformed CSVs)
    text = input_path.read_text(encoding='utf-8')
    # strip leading/trailing code fences if present
    text = text.strip('\n')
    if text.startswith('```'):
        # remove the first line if it's a fence
        lines = text.splitlines()
        # drop fence lines that are exactly ``` or ```csv
        lines = [l for l in lines if not re.match(r'^```', l)]
    else:
        lines = text.splitlines()

    out_lines = []
    header_written = False
    tagged_count = 0

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        # For the header line (first non-empty), append tags column
        if not header_written:
            out_lines.append(line + ',tags')
            header_written = True
            continue

        # Find tags by checking if any kit token appears in the line
        found_tags = set()
        for kit, tag in tags_map.items():
            if kit in line:
                found_tags.add(tag)

        tags_str = ';'.join(sorted(found_tags))
        if tags_str:
            tagged_count += 1

        out_lines.append(line + (',' + tags_str if tags_str else ','))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text('\n'.join(out_lines), encoding='utf-8')
    print(f'Wrote tagged CSV to: {out_path}')
    print(f'Tagged rows: {tagged_count} / {max(0, len(out_lines)-1)}')
    if tags_map:
        print('Known kits checked:', ', '.join(sorted(tags_map.keys())))

    return tagged_count


def main():
    tags_map = load_tags(TAGS_CSV)
    tag_rows(IN_CSV, tags_map, OUT_CSV)


if __name__ == '__main__':
    main()
