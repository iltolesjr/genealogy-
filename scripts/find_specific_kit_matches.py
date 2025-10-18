#!/usr/bin/env python3
"""Search workspace files for specific kit IDs and write matches to outputs file."""
from pathlib import Path
import re

ROOT = Path('c:/Users/irato/OneDrive/Documents/genealogy.2/genealogy-')
OUT = ROOT / 'outputs' / 'kit_matches_MK1835168_FM5793412.txt'
PAT = re.compile(r'MK1835168|FM5793412')

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as fo:
        for p in ROOT.rglob('*'):
            if p.is_file() and p.suffix.lower() in ('.csv', '.txt', '.html'):
                try:
                    txt = p.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue
                for i, line in enumerate(txt.splitlines(), start=1):
                    if PAT.search(line):
                        fo.write(f'{p}\t{ i }\t{ line }\n')

    print('Wrote search results to', OUT)

if __name__ == '__main__':
    main()
