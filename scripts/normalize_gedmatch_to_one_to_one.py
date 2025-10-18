#!/usr/bin/env python3
"""Normalize parsed GEDmatch CSV into a one-to-one combined CSV with columns:
Kit1,Kit2,Chr,Start,End,cM,SNPs

This script reads `outputs/gedmatch_segments.csv` (or the tagged variant) and
attempts to extract numeric fields. It tolerates messy rows (commas inside cells,
fenced CSV) by parsing lines and using regex heuristics.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_CSV = ROOT / 'outputs' / 'gedmatch_segments.csv'
OUT_CSV = ROOT / 'outputs' / 'one_to_one_combined.csv'


def parse_line_to_fields(line):
    # Remove leading/trailing code fences/backticks
    line = line.strip()
    if line.startswith('```'):
        line = line.strip('`')

    # Heuristic: split on commas, but if the line contains tabs or multiple spaces, try splitting on whitespace
    if '\t' in line and line.count(',') < 3:
        toks = line.split('\t')
    else:
        toks = [t.strip() for t in line.split(',')]

    return toks


def extract_numeric_from_tokens(tokens):
    # We want: Kit1, Kit2, Chr, Start, End, cM, SNPs
    # Heuristic search for first two tokens that look like kit ids (contain letters+digits)
    kit_pattern = re.compile(r'[A-Za-z0-9_]+')
    num_pattern = re.compile(r'^-?\d+$')
    float_pattern = re.compile(r'^\d+(?:\.\d+)?$')

    kits = []
    nums = []
    for t in tokens:
        if not t:
            continue
        if len(kits) < 2 and kit_pattern.match(t) and not num_pattern.match(t):
            kits.append(t)
            continue
        # strip non-numeric characters
        s = t.replace(' ', '')
        s2 = re.sub(r'[^0-9\.-]', '', s)
        if float_pattern.match(s2):
            nums.append(s2)

    # Try to map numeric positions: prefer last 4 numbers as start,end,cM,snps or start,end,snps,cM
    chr_ = ''
    start = ''
    end = ''
    cm = ''
    snps = ''

    if len(nums) >= 4:
        # last 4 numeric tokens
        a,b,c,d = nums[-4:]
        # heuristics: if c contains a decimal it's probably cM
        if '.' in c:
            start, end, cm, snps = a, b, c, d
        elif '.' in d:
            start, end, snps, cm = a, b, c, d
        else:
            # uncertain: assume start,end,cM,snps with c as cm
            start, end, cm, snps = a, b, c, d
    elif len(nums) == 3:
        start, end, cm = nums
    elif len(nums) == 2:
        start, end = nums

    # attempt to detect chromosome earlier in tokens
    for t in tokens:
        if re.fullmatch(r'\d+|X|chr\d+|CHR\d+', t.strip(), flags=re.I):
            chr_ = re.sub(r'[^0-9Xx]', '', t)
            break

    # If chr not found but kits include forms like '1' near start, try nums[0]
    if not chr_ and len(nums) >= 1:
        # if first numeric is small (1-22) treat as chr
        try:
            val = int(nums[0])
            if 1 <= val <= 23:
                chr_ = str(val)
        except Exception:
            pass

    return {
        'Kit1': kits[0] if kits else '',
        'Kit2': kits[1] if len(kits) > 1 else '',
        'Chr': chr_,
        'Start': start,
        'End': end,
        'cM': cm,
        'SNPs': snps
    }


def main():
    if not IN_CSV.exists():
        print('Input CSV not found:', IN_CSV)
        return

    lines = IN_CSV.read_text(encoding='utf-8').splitlines()
    out_rows = []
    header_seen = False
    for line in lines:
        if not line.strip():
            continue
        # skip code fences
        if line.strip().startswith('```'):
            continue
        # first non-empty line might be header
        if not header_seen:
            header_seen = True
            continue

        toks = parse_line_to_fields(line)
        rec = extract_numeric_from_tokens(toks)
        # Only keep rows where at least Kit1 and Kit2 and cM are present
        if rec['Kit1'] and rec['Kit2'] and (rec['cM'] or rec['Start']):
            out_rows.append(rec)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Kit1','Kit2','Chr','Start','End','cM','SNPs'])
        writer.writeheader()
        for r in out_rows:
            writer.writerow(r)

    print(f'Wrote {len(out_rows)} one-to-one rows to {OUT_CSV}')


if __name__ == '__main__':
    main()
