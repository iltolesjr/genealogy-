import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / 'outputs' / 'all_matches_standardized.csv'
OUTPUT = ROOT / 'outputs' / 'gumatch_intervals_hits.csv'

# intervals from the GU1800109 vs A064172 one-to-one
INTERVALS = [
    ('chr17', 37036554, 63111452, 'GU_vs_A064172_chr17'),
    ('chr20', 24247556, 41711226, 'GU_vs_A064172_chr20'),
]

def overlaps(a_start, a_end, b_start, b_end):
    return max(0, min(a_end, b_end) - max(a_start, b_start) + 1)

def main():
    if not INPUT.exists():
        print(f'Missing input: {INPUT}')
        return

    with INPUT.open('r', newline='', encoding='utf-8') as inf, \
         OUTPUT.open('w', newline='', encoding='utf-8') as outf:
        reader = csv.DictReader(inf)
        fieldnames = reader.fieldnames + ['IntervalLabel', 'IntervalChr', 'IntervalStart', 'IntervalEnd', 'Overlap_bp']
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            try:
                row_chr = row['chr'].strip()
                bstart = int(row['B37Start'])
                bend = int(row['B37End'])
            except Exception:
                # skip malformed rows
                continue

            for int_chr_label, int_start, int_end, label in INTERVALS:
                # input uses numeric chr values or 'X' etc; standardize to 'chrN' form for comparison
                norm_row_chr = f'chr{row_chr}' if not str(row_chr).lower().startswith('chr') else row_chr.lower()
                if norm_row_chr.lower() == int_chr_label.lower():
                    ov = overlaps(bstart, bend, int_start, int_end)
                    if ov > 0:
                        out = dict(row)
                        out['IntervalLabel'] = label
                        out['IntervalChr'] = int_chr_label
                        out['IntervalStart'] = int_start
                        out['IntervalEnd'] = int_end
                        out['Overlap_bp'] = ov
                        writer.writerow(out)
                        # if a row overlaps both intervals, it will be written twice (one per interval)

    print(f'Wrote hits to {OUTPUT}')

if __name__ == '__main__':
    main()
