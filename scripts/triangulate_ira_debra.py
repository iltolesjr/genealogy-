#!/usr/bin/env python3
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
ONE = ROOT / 'outputs' / 'one_to_one_combined_perfect.csv'
SHARED = ROOT / 'outputs' / 'shared_matches_ira_debra.csv'
OUT = ROOT / 'outputs' / 'triangulation_ira_debra.csv'

# load the shared names
shared_names = set()
with SHARED.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        shared_names.add(r['Match Name'].strip())

# read one_to_one file and find rows where either kit name matches GU1800109 or match name in shared list
hits = []
with ONE.open('r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        # expected columns: Kit1,Kit2,Chr,Start,End,cM,SNPs (some files have different shapes)
        if len(row) < 6:
            continue
        k1, k2 = row[0].strip(), row[1].strip()
        # try to find name fields in extras
        name = ''
        if len(row) >= 3:
            # heuristic: some rows include name in third column when Kit2 blank
            pass
        # match by kit id or name: we only have names in shared_names, so match where any field contains shared name
        line = ','.join(row)
        for nm in shared_names:
            if nm and nm in line:
                hits.append(row)
                break
# write results
with OUT.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Kit1','Kit2','Chr','Start','End','cM','SNPs','source_line'])
    for r in hits:
        writer.writerow(r + [','.join(r)])
print(f'Wrote {len(hits)} triangulation rows to {OUT}')
