#!/usr/bin/env python3
import re
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: find_segment_table.py path/to/segmenttable.html')
    sys.exit(2)

p = Path(sys.argv[1])
txt = p.read_text(encoding='utf-8', errors='ignore')
keywords=['Chromosome','chr','cM','Start','End','SNP','match','Match','GEDmatch','Segment']
for kw in keywords:
    m = re.search(kw, txt, flags=re.I)
    if m:
        i = m.start()
        print('---',kw,'at',i,'---')
        print(txt[max(0,i-200):i+200].replace('\n',' '))
    else:
        print('---',kw,'not found')
