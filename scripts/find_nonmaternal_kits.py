#!/usr/bin/env python3
import csv
from collections import Counter, defaultdict

inpath = r"c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\Research Data\overlaps_from_user_segments.csv"
outpath = r"c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\Research Data\ak_non_maternal_partners.csv"

lines = []
with open(inpath, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip().startswith('```'):
            continue
        if not line.strip():
            continue
        lines.append(line)

reader = csv.reader(lines)
header = next(reader)
# Expected header indexes
# 0:user_label, 5:csv_kitA, 6:csv_kitB, 14:csv_raw_row
idx_user_label = header.index('user_label')
idx_kitA = header.index('csv_kitA')
idx_kitB = header.index('csv_kitB')
idx_raw = header.index('csv_raw_row')

ak = 'AK6981890'
maternal_labels = {'FK5643059', 'SF088248C1'}

ak_partners = []
maternal_kits = set()
raw_by_partner = defaultdict(set)
counts = Counter()

for row in reader:
    user_label = row[idx_user_label].strip()
    kitA = row[idx_kitA].strip()
    kitB = row[idx_kitB].strip()
    raw = row[idx_raw].strip()

    # collect maternal kits from rows where user_label matches Vanessa or Greta
    for ml in maternal_labels:
        if user_label.startswith(ml):
            maternal_kits.add(kitA)
            maternal_kits.add(kitB)
    # collect AK partners
    if kitA == ak:
        ak_partners.append(kitB)
        counts[kitB] += 1
        raw_by_partner[kitB].add(raw)
    elif kitB == ak:
        ak_partners.append(kitA)
        counts[kitA] += 1
        raw_by_partner[kitA].add(raw)

ak_partners_set = set(ak_partners)
non_maternal = sorted(ak_partners_set - maternal_kits)

with open(outpath, 'w', encoding='utf-8', newline='') as out:
    w = csv.writer(out)
    w.writerow(['kit','count','sample_raw_rows'])
    for kit in non_maternal:
        w.writerow([kit, counts.get(kit,0), ' || '.join(sorted(raw_by_partner.get(kit,[]))[:5])])

print(f"Total AK partners found: {len(ak_partners_set)}")
print(f"Maternal kits (seen with FK5643059 or SF088248C1): {len(maternal_kits)}")
print(f"Non-maternal AK partners written: {len(non_maternal)} -> {outpath}")
