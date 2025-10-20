#!/usr/bin/env python3
"""Build exact overlap table for Wilma (GU1800109), Temara (A044456) and common kits.

Output columns: CommonKit,Pair,Chr,Start,End,cM,SNPs,Source,MatchedName,MatchedEmail
Pairs emitted: GU1800109-CommonKit, A044456-CommonKit, GU1800109-A044456
"""
import csv
from pathlib import Path
import re

ROOT = Path.cwd()
OUT = ROOT / 'outputs' / 'wilma_temara_common_triangulation.csv'
ONE2ONE = ROOT / 'outputs' / 'one_to_one_combined_perfect.csv'
TRI_TOP = ROOT / 'outputs' / 'triangulation_wilma_top.csv'
DOWNLOADS = Path(r"C:\Users\irato\Downloads")

TEMARA = 'A044456'
ME = 'GU1800109'

common_file = ROOT / 'outputs' / 'temara_triangulation_with_GU1800109_summary.csv'

# read common kits
common_kits = []
with common_file.open(encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)
    # find the line with 'common_kits'
    found = False
    for i,r in enumerate(rows):
        if r and r[0] == 'common_kits':
            found = True
            for j in range(i+1, len(rows)):
                if rows[j] and rows[j][0].strip():
                    common_kits.append(rows[j][0].strip())
            break

sources = []
if ONE2ONE.exists():
    sources.append(ONE2ONE)
if TRI_TOP.exists():
    sources.append(TRI_TOP)
# add triang_*.csv files from Downloads
for p in DOWNLOADS.glob('triang_*.csv'):
    sources.append(p)

# function to extract kit fields from a row
kit_fields = ['PrimaryKit','MatchedKit','chr','B37Start','B37End','Segment cM','SNPs','MatchedName','MatchedEmail']

rows_out = []

# helper to normalize and read csv with flexible headers
def read_rows(path: Path):
    out = []
    try:
        with path.open(encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for r in reader:
                out.append((path.name, r))
    except Exception as e:
        # try fallback: plain CSV with known columns
        try:
            with path.open(encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parts = [p.strip().strip('"') for p in line.split(',')]
                    if len(parts) >= 6:
                        out.append((path.name, {'PrimaryKit': parts[0], 'MatchedKit': parts[1], 'chr': parts[2], 'B37Start': parts[3], 'B37End': parts[4], 'Segment cM': parts[5], 'SNPs': parts[6] if len(parts)>6 else ''}))
        except Exception:
            pass
    return out

# scan sources
for p in sources:
    items = read_rows(p)
    for fname, r in items:
        # normalize kit ids and common header variants
        # common triangulation CSVs use columns like 'Kit1 Number', 'Kit1 Name', 'Kit1 Email', 'B37 Start', 'B37 End', 'cM', 'Chr'
        def get(*keys):
            for k in keys:
                if k in r and r[k] is not None:
                    return str(r[k]).strip()
            return ''

        k1 = get('PrimaryKit', 'Kit1', 'Kit1 Number', 'Kit1_Number', 'kit')
        k2 = get('MatchedKit', 'Kit2', 'Kit2 Number', 'Kit2_Number', 'match')
        chr_ = get('chr', 'Chr', 'chromosome')
        start = get('B37Start', 'B37 Start', 'Start', 'From', 'start')
        end = get('B37End', 'B37 End', 'End', 'To', 'end')
        cm = get('Segment cM', 'cM', 'seg_cm')
        snps = get('SNPs', 'snps', 'num_snps')

        kit1_name = get('Kit1 Name', 'Kit1Name', 'Kit1_Name', 'MatchedName', 'name')
        kit2_name = get('Kit2 Name', 'Kit2Name', 'Kit2_Name', 'MatchedName', 'name')
        kit1_email = get('Kit1 Email', 'Kit1Email', 'Kit1_Email', 'Kit1 Email Address', 'Kit1_Email_Address', 'email')
        kit2_email = get('Kit2 Email', 'Kit2Email', 'Kit2_Email', 'Kit2 Email Address', 'Kit2_Email_Address', 'email')

        # check pairs and pick matched name/email from the opposite side
        for ck in common_kits:
            if (k1 == ME and k2 == ck) or (k1 == ck and k2 == ME):
                mn = kit2_name if k1 == ME else kit1_name
                meaddr = kit2_email if k1 == ME else kit1_email
                rows_out.append({'CommonKit': ck, 'Pair': f'{ME}-{ck}', 'Chr': chr_, 'Start': start, 'End': end, 'cM': cm, 'SNPs': snps, 'Source': fname, 'MatchedName': mn, 'MatchedEmail': meaddr})
            if (k1 == TEMARA and k2 == ck) or (k1 == ck and k2 == TEMARA):
                mn = kit2_name if k1 == TEMARA else kit1_name
                meaddr = kit2_email if k1 == TEMARA else kit1_email
                rows_out.append({'CommonKit': ck, 'Pair': f'{TEMARA}-{ck}', 'Chr': chr_, 'Start': start, 'End': end, 'cM': cm, 'SNPs': snps, 'Source': fname, 'MatchedName': mn, 'MatchedEmail': meaddr})
        # Wilma-Temara pair
        if (k1 == ME and k2 == TEMARA) or (k1 == TEMARA and k2 == ME):
            mn = kit2_name if k1 == ME else kit1_name
            meaddr = kit2_email if k1 == ME else kit1_email
            rows_out.append({'CommonKit': TEMARA, 'Pair': f'{ME}-{TEMARA}', 'Chr': chr_, 'Start': start, 'End': end, 'cM': cm, 'SNPs': snps, 'Source': fname, 'MatchedName': mn, 'MatchedEmail': meaddr})

# write output
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', encoding='utf-8', newline='') as fo:
    writer = csv.DictWriter(fo, fieldnames=['CommonKit','Pair','Chr','Start','End','cM','SNPs','Source','MatchedName','MatchedEmail'])
    writer.writeheader()
    for r in rows_out:
        writer.writerow(r)

print(f'Wrote {len(rows_out)} rows to {OUT}')
