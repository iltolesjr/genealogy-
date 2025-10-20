import re
import csv
from glob import glob
from pathlib import Path

ROOT = Path(r"C:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-")
DOWNLOADS = Path(r"C:\Users\irato\Downloads")
OUT_TEMARA = ROOT / 'outputs' / 'temara_matches_raw.csv'
OUT_TRI = ROOT / 'outputs' / 'temara_triangulation_with_GU1800109_summary.csv'

TEMARA = 'A044456'
ME = 'GU1800109'

# Files to search
candidates = []
candidates.append(ROOT / 'outputs' / 'all_matches_standardized.csv')
candidates.append(ROOT / 'outputs' / 'triangulation_wilma_top.csv')
# downloads patterns
candidates += list(DOWNLOADS.glob('csvsegmatch*.csv'))
candidates += list(DOWNLOADS.glob('csvsegmatch_*.csv'))
candidates += list(DOWNLOADS.glob('triang_*.csv'))
candidates += list(DOWNLOADS.glob('MY-Segment Search*.txt'))
candidates += list(DOWNLOADS.glob('app.csv'))
candidates += list(DOWNLOADS.glob('app*.csv'))

# normalize unique list
files = []
for p in candidates:
    if p.exists() and p not in files:
        files.append(p)

kit_re = re.compile(r"\b[A-Z]{1,3}\d{3,9}\b")

temara_lines = []
me_lines = []

kits_temara = set()
kits_me = set()

for p in files:
    try:
        with p.open('r', encoding='utf-8', errors='ignore') as f:
            for ln in f:
                if TEMARA in ln:
                    temara_lines.append((str(p), ln.strip()))
                    kits = set(kit_re.findall(ln))
                    kits_temara.update(kits)
                if ME in ln:
                    me_lines.append((str(p), ln.strip()))
                    kits = set(kit_re.findall(ln))
                    kits_me.update(kits)
    except Exception as e:
        print(f"Error reading {p}: {e}")

# remove self IDs
kits_temara.discard(TEMARA)
kits_temara.discard(ME)
kits_me.discard(ME)
kits_me.discard(TEMARA)

common = kits_temara.intersection(kits_me)

# Write raw temara matches
with OUT_TEMARA.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['source_file','line'])
    for src, ln in temara_lines:
        writer.writerow([src, ln])

# Write triangulation summary
with OUT_TRI.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['temara_kits_count','me_kits_count','common_kits_count'])
    writer.writerow([len(kits_temara), len(kits_me), len(common)])
    writer.writerow([])
    writer.writerow(['common_kits'])
    for k in sorted(common):
        writer.writerow([k])

print(f"Searched {len(files)} files")
print(f"Found {len(temara_lines)} Temara lines and {len(me_lines)} ME lines")
print(f"Kits touching Temara: {len(kits_temara)}; Kits touching ME: {len(kits_me)}; Common: {len(common)}")
