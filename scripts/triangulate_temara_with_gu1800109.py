import csv
from collections import defaultdict

src = r"C:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\outputs\all_matches_standardized.csv"
out1 = r"C:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\outputs\temara_matches.csv"
out2 = r"C:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\outputs\temara_triangulation_with_GU1800109.csv"

TEMARA = 'A044456'
ME = 'GU1800109'

# Read source and collect rows
rows = []
with open(src, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

# Extract matches involving Temara and me
temara_rows = [r for r in rows if r['PrimaryKit']==TEMARA or r['MatchedKit']==TEMARA]
me_rows = [r for r in rows if r['PrimaryKit']==ME or r['MatchedKit']==ME]

# Write temara_rows
if temara_rows:
    with open(out1, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(temara_rows)

# Find kits that appear in both sets (excluding TEMARA and ME)
kits_temara = set()
for r in temara_rows:
    kits_temara.add(r['PrimaryKit'])
    kits_temara.add(r['MatchedKit'])
kits_temara.discard(TEMARA)

kits_me = set()
for r in me_rows:
    kits_me.add(r['PrimaryKit'])
    kits_me.add(r['MatchedKit'])
kits_me.discard(ME)

common_kits = kits_temara.intersection(kits_me)

# Prepare triangulation rows: any row where both kits are in common_kits or one is ME/TEMARA and the other in common_kits
tri_rows = []
for r in rows:
    a = r['PrimaryKit']
    b = r['MatchedKit']
    if (a in common_kits and b in common_kits) or ((a==TEMARA and b in kits_me) or (b==TEMARA and a in kits_me)) or ((a==ME and b in kits_temara) or (b==ME and a in kits_temara)):
        tri_rows.append(r)

# Write triangulation rows
if tri_rows:
    with open(out2, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(tri_rows)

print(f"Wrote {len(temara_rows)} temara rows to {out1}")
print(f"Found {len(common_kits)} common kits; wrote {len(tri_rows)} triangulation rows to {out2}")
