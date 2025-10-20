#!/usr/bin/env python3
"""
Scan multiple CSV sources for overlaps with specified GEDmatch intervals.
Writes results to outputs/gumatch_interval_all_sources_hits_v2.csv

Usage: run with the workspace python; script is self-contained and uses only stdlib.
"""
import csv
import os
from pathlib import Path

WORKSPACE = Path(r"c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-")
OUT = WORKSPACE / 'outputs' / 'gumatch_interval_all_sources_hits_v2.csv'

# Intervals from the GU1800109 vs A064172 one-to-one
INTERVALS = [
    ('17', 37036554, 63111452),
    ('20', 24247556, 41711226),
]

SOURCES = [
    WORKSPACE / 'outputs' / 'all_matches_standardized.csv',
    WORKSPACE / 'outputs' / 'one_to_one_combined_perfect.csv',
    Path(r"c:\Users\irato\Downloads\csvsegmatch_.csv"),
    Path(r"c:\Users\irato\Downloads\app.csv"),
    WORKSPACE / 'outputs' / 'triangulation_wilma_top.csv',
]

def parse_int(s):
    try:
        return int(s)
    except Exception:
        s2 = ''.join(ch for ch in s if ch.isdigit())
        return int(s2) if s2 else None

def overlap(a1,a2,b1,b2):
    lo = max(a1,b1)
    hi = min(a2,b2)
    return max(0, hi - lo + 1)

def find_fields(header):
    # lower header tokens
    low = [h.strip().lower() for h in header]
    # find kit columns
    kit_cols = []
    for name in ('primarykit','kit1','kit','k1','kit_a','kit_a_id','kit_a_name'):
        if name in low:
            kit_cols.append(low.index(name))
            break
    for name in ('matchedkit','kit2','match','k2','kit_b','kit_b_id','kit_b_name'):
        if name in low:
            kit_cols.append(low.index(name))
            break
    # try more general heuristics
    if not kit_cols:
        for i,h in enumerate(low):
            if 'kit' in h or 'match' in h or 'id' in h:
                kit_cols.append(i)
                if len(kit_cols)>=2:
                    break
    # find start/end columns (b37)
    start=None; end=None; chrcol=None
    for i,h in enumerate(low):
        if h in ('b37start','start','startpos','b37_start'):
            start=i
        if h in ('b37end','end','endpos','b37_end'):
            end=i
        if h in ('chr','chrom','chromosome'):
            chrcol=i
    return kit_cols, chrcol, start, end

def scan_source(path, writer):
    path = Path(path)
    if not path.exists():
        return 0
    hits=0
    with path.open(newline='', encoding='utf-8', errors='replace') as fh:
        rdr = csv.reader(fh)
        try:
            header = next(rdr)
        except StopIteration:
            return 0
        kit_cols, chrcol, startcol, endcol = find_fields(header)
        # fallbacks: expect columns by position if header is data
        for row in rdr:
            if not row: continue
            # ensure row is long enough
            rlen = len(row)
            # determine chr
            chrv = None
            if chrcol is not None and chrcol < rlen:
                chrv = row[chrcol].strip().lower().lstrip('chr')
            else:
                # try token that looks like a chromosome
                for token in row:
                    t = token.strip().lower()
                    if t in [str(i) for i in range(1,23)]+['x','y','mt']:
                        chrv = t
                        break
            if not chrv: continue
            # parse start/end
            s=None; e=None
            if startcol is not None and startcol < rlen:
                s = parse_int(row[startcol])
            if endcol is not None and endcol < rlen:
                e = parse_int(row[endcol])
            # fallback: try columns that look like numbers
            if s is None or e is None:
                nums = [parse_int(tok) for tok in row]
                nums = [n for n in nums if n is not None and n>1000]
                if len(nums)>=2:
                    s = nums[0]; e = nums[1]
            if s is None or e is None: continue
            # check intervals
            for ch, astart, aend in INTERVALS:
                if chrv == ch:
                    ov = overlap(astart,aend,s,e)
                    if ov>0:
                        # find kit ids
                        kits = []
                        for kc in kit_cols:
                            if kc < rlen:
                                kits.append(row[kc].strip())
                            else:
                                kits.append('')
                        # write a row with source, kits, chr, start, end, overlap, raw row joined
                        writer.writerow([str(path), '|'.join(kits), kits[0] if kits else '', kits[1] if len(kits)>1 else '', ch, s, e, ov, '|'.join(row)])
                        hits+=1
                        break
    return hits

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    total=0
    with OUT.open('w', newline='', encoding='utf-8') as outfh:
        w = csv.writer(outfh)
        w.writerow(['source','kits','kit_a','kit_b','chr','start','end','overlap_bp','raw'])
        for s in SOURCES:
            h = scan_source(s, w)
            print(f"Scanned {s} -> {h} hits")
            total+=h
    print(f"Done. total hits={total}. Wrote {OUT}")

if __name__=='__main__':
    main()
