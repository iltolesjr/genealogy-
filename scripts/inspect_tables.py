#!/usr/bin/env python3
from pathlib import Path
import sys
try:
    from bs4 import BeautifulSoup
except Exception:
    print('BeautifulSoup not available. Please install bs4 to run this inspector.')
    sys.exit(1)

if len(sys.argv) < 2:
    print('Usage: inspect_tables.py path/to/segmenttable.html')
    sys.exit(2)

p = Path(sys.argv[1])
html = p.read_text(encoding='utf-8', errors='ignore')
soup = BeautifulSoup(html, 'html.parser')
tables = soup.find_all('table')
print('Found', len(tables), 'tables')
for i, t in enumerate(tables[:40]):
    rows = t.find_all('tr')
    print('\n--- Table', i, 'rows=', len(rows), '---')
    # print header cells
    header = None
    ths = t.find_all('th')
    if ths:
        header = [th.get_text().strip() for th in ths]
    else:
        first = t.find('tr')
        if first:
            header = [c.get_text().strip() for c in first.find_all(['td','th'])]
    print('header sample:', header[:10] if header else [])
    # print first 3 data rows
    for r in rows[1:4]:
        cells = [c.get_text().strip() for c in r.find_all(['td','th'])]
        print(' row:', cells[:12])
