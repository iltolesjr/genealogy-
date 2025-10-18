#!/usr/bin/env python3
"""
Compute overlaps between a set of user-supplied segments and the project's csvsegmatch_.csv.

Writes Research Data/overlaps_from_user_segments.csv and prints a short top-10 summary.
"""
import csv
import os
from pathlib import Path


CSV_PATH = r"c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\scripts\csvsegmatch_.csv"
OUT_DIR = Path(r"c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\Research Data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "overlaps_from_user_segments.csv"

# User-focused segments collected from the session summary. Each item is a dict with
# an id/label, chromosome (int or str), start and end in basepairs.
USER_SEGMENTS = [
    # user-pasted GEDmatch segment (matched to AK6981890 row earlier)
    {"label": "user_paste_AK6981890_chr5", "chr": "5", "start": 77170584, "end": 103676341},
    # FK5643059 (Vanessa Wakiumu) segments extracted from AutoKinship
    {"label": "FK5643059_chr3", "chr": "3", "start": 2195312, "end": 5791627},
    {"label": "FK5643059_chr11", "chr": "11", "start": 32571594, "end": 44705461},
    {"label": "FK5643059_chr12_a", "chr": "12", "start": 15235173, "end": 25243893},
    {"label": "FK5643059_chr12_b", "chr": "12", "start": 51713586, "end": 99135638},
    {"label": "FK5643059_chr18", "chr": "18", "start": 49488572, "end": 67084661},
    # SF088248C1 (greta mitchell) segments extracted earlier
    {"label": "SF088248C1_chr5", "chr": "5", "start": 127803816, "end": 157191954},
    {"label": "SF088248C1_chr6_a", "chr": "6", "start": 165632, "end": 5923152},
    {"label": "SF088248C1_chr6_b", "chr": "6", "start": 150727036, "end": 162646769},
    {"label": "SF088248C1_chr7", "chr": "7", "start": 32199098, "end": 41241212},
]


def normalize_chr(val):
    s = str(val).strip().lower()
    if s.startswith('chr'):
        s = s[3:]
    return s


def overlaps(a_start, a_end, b_start, b_end):
    lo = max(a_start, b_start)
    hi = min(a_end, b_end)
    if lo <= hi:
        return hi - lo + 1
    return 0


def read_csv_rows(path):
    with open(path, newline='', encoding='utf-8', errors='replace') as fh:
        reader = csv.reader(fh)
        rows = [r for r in reader if r]
    return rows


def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: csvsegmatch file not found at {CSV_PATH}")
        return

    rows = read_csv_rows(CSV_PATH)
    print(f"Read {len(rows)} rows from {CSV_PATH}")

    # Prepare output rows
    out_rows = []
    header = [
        'user_label', 'user_chr', 'user_start', 'user_end', 'user_len_bp',
        'csv_kitA', 'csv_kitB', 'csv_chr', 'csv_start', 'csv_end', 'csv_len_bp',
        'overlap_bp', 'overlap_fraction_of_user', 'overlap_fraction_of_csv', 'csv_raw_row'
    ]

    for us in USER_SEGMENTS:
        u_chr = normalize_chr(us['chr'])
        u_start = int(us['start'])
        u_end = int(us['end'])
        u_len = u_end - u_start + 1

        for r in rows:
            # Expect at least 5 columns: kitA, kitB, chr, start, end, ...
            if len(r) < 5:
                continue
            kitA = r[0].strip()
            kitB = r[1].strip() if len(r) > 1 else ''
            chr_field = r[2].strip()
            try:
                csv_chr = normalize_chr(chr_field)
            except Exception:
                continue
            # only compare same chromosome
            if csv_chr != u_chr:
                continue
            try:
                csv_start = int(r[3].strip())
                csv_end = int(r[4].strip())
            except Exception:
                continue
            csv_len = csv_end - csv_start + 1
            ov = overlaps(u_start, u_end, csv_start, csv_end)
            if ov > 0:
                out_rows.append([
                    us['label'], u_chr, u_start, u_end, u_len,
                    kitA, kitB, csv_chr, csv_start, csv_end, csv_len,
                    ov, round(ov / u_len, 6), round(ov / csv_len, 6), '|'.join(r)
                ])

    # sort by overlap descending
    out_rows.sort(key=lambda x: x[11], reverse=True)

    # write CSV
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} overlapping rows to {OUT_CSV}")
    print('\nTop 10 overlaps:')
    for i, r in enumerate(out_rows[:10], 1):
        print(f"{i}. user={r[0]} chr{r[1]} {r[2]}-{r[3]} overlaps kit={r[5]} vs {r[6]} chr{r[7]} {r[8]}-{r[9]} overlap_bp={r[11]} ({r[12]*100:.2f}% of user, {r[13]*100:.2f}% of csv)")


if __name__ == '__main__':
    main()
