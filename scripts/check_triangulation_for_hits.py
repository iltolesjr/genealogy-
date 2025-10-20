#!/usr/bin/env python3
"""
Given outputs/gumatch_interval_all_sources_hits_v2.csv, extract kit ids and check for
triangulation evidence in outputs/triangulation_wilma_top.csv and outputs/wilma_candidate_overlaps.csv.
Writes results to outputs/gumatch_interval_hits_triangulation.csv
"""
import csv
from pathlib import Path

W = Path(r"c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-")
HITS = W / 'outputs' / 'gumatch_interval_all_sources_hits_v2.csv'
TRI = W / 'outputs' / 'triangulation_wilma_top.csv'
CAN = W / 'outputs' / 'wilma_candidate_overlaps.csv'
OUT = W / 'outputs' / 'gumatch_interval_hits_triangulation.csv'

def load_hit_kits():
    kits=set()
    if not HITS.exists():
        return kits
    with HITS.open(newline='', encoding='utf-8') as fh:
        rdr = csv.reader(fh)
        next(rdr,None)
        for r in rdr:
            if not r: continue
            kitfield = r[1]
            for k in kitfield.split('|'):
                k2 = k.strip()
                if k2:
                    kits.add(k2)
    return kits

def scan_for_kits(path, kits):
    found=[]
    if not path.exists():
        return found
    with path.open(newline='', encoding='utf-8', errors='replace') as fh:
        rdr = csv.reader(fh)
        for r in rdr:
            if not r: continue
            rowtext = '|'.join(r)
            for k in kits:
                if k in rowtext:
                    found.append((k, rowtext))
    return found

def main():
    kits = load_hit_kits()
    print(f"Loaded {len(kits)} kits from hits file")
    tri_found = scan_for_kits(TRI, kits)
    can_found = scan_for_kits(CAN, kits)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as outfh:
        w = csv.writer(outfh)
        w.writerow(['kit','source','row'])
        for k,r in tri_found:
            w.writerow([k,'triangulation_wilma_top',r])
        for k,r in can_found:
            w.writerow([k,'wilma_candidate_overlaps',r])
    print(f"Wrote {OUT} with {len(tri_found)+len(can_found)} rows")

if __name__=='__main__':
    main()
