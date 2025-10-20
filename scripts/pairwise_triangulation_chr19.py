"""Scan triang_*.csv files in Downloads for Chr 19 rows where both kits are in the target set.
Write two outputs:
- outputs/pairwise_triangulation_pairs.csv : one row per observed triangulation (kitA,kitB,chr,start,end,cM,snps,source)
- outputs/pairwise_triangulation_matrix.csv : matrix (CSV) with counts of observed triangulations between kits

This script is conservative: it canonicalizes kit ids by stripping whitespace and uppercasing.
"""
import csv
import glob
import os
from collections import defaultdict

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOWNLOADS = os.path.expanduser(r"C:\Users\irato\Downloads")
OUT_DIR = os.path.join(WORKSPACE, 'outputs')
os.makedirs(OUT_DIR, exist_ok=True)

# The nine common kits discovered earlier
TARGET_KITS = {
    'A159092','A189271','A605663','A715132','LF8212927','M130633','M297536','TJ5054086','XT5583147'
}

def norm(s):
    return (s or '').strip().upper()

pairs = []
matrix = defaultdict(lambda: defaultdict(int))

files = glob.glob(os.path.join(DOWNLOADS, 'triang_*.csv'))
files.sort()

for f in files:
    try:
        with open(f, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            # normalize common header names mapping
            hdr = {h.lower(): h for h in reader.fieldnames}
            def get(row, *names):
                for n in names:
                    key = n.lower()
                    if key in hdr:
                        return row[hdr[key]]
                return ''

            for row in reader:
                chrval = norm(get(row, 'Chr', 'Chromosome'))
                if chrval not in ('19', 'CHR19'):
                    continue
                k1 = norm(get(row, 'Kit1 Number', 'Kit1', 'Kit1_Number', 'kit1 number'))
                k2 = norm(get(row, 'Kit2 Number', 'Kit2', 'Kit2_Number', 'kit2 number'))
                if not k1 or not k2:
                    # try fallback: some exports put kit id in first name column
                    k1 = norm(get(row, 'Kit1 Name', 'Kit1 Name'))
                    k2 = norm(get(row, 'Kit2 Name', 'Kit2 Name'))

                # only consider rows where both kits are in our target set
                if k1 in TARGET_KITS and k2 in TARGET_KITS and k1 != k2:
                    start = get(row, 'B37 Start', 'B37_Start', 'Start', 'b37 start')
                    end = get(row, 'B37 End', 'B37_End', 'End', 'b37 end')
                    cm = get(row, 'cM', 'CM', 'cM ') or ''
                    snps = get(row, 'SNPs', 'snps') or ''
                    source = os.path.basename(f)
                    a,b = sorted([k1,k2])
                    pairs.append({'KitA':a,'KitB':b,'Chr':'19','Start':start,'End':end,'cM':cm,'SNPs':snps,'Source':source})
                    matrix[a][b] += 1
    except Exception as e:
        print(f"Warning: failed reading {f}: {e}")

# write pairs CSV
pairs_out = os.path.join(OUT_DIR, 'pairwise_triangulation_pairs.csv')
with open(pairs_out, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=['KitA','KitB','Chr','Start','End','cM','SNPs','Source'])
    writer.writeheader()
    for row in pairs:
        writer.writerow(row)

# write matrix CSV (square, sorted keys)
kits = sorted(TARGET_KITS)
matrix_out = os.path.join(OUT_DIR, 'pairwise_triangulation_matrix.csv')
with open(matrix_out, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.writer(fh)
    writer.writerow([''] + kits)
    for a in kits:
        row = [a]
        for b in kits:
            if a==b:
                row.append('')
            else:
                x,y = sorted([a,b])
                row.append(str(matrix[x].get(y,0)))
        writer.writerow(row)

print(f"Wrote {len(pairs)} pair rows to {pairs_out}")
print(f"Wrote matrix to {matrix_out}")
