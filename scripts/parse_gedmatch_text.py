#!/usr/bin/env python3
"""
Parse a GEDmatch 3D Chromosome Browser plain-text export (like the pasted content) and extract:
- 'Segments in common' matrix
- 'Total Shared cM' matrix (Chr 1-22 and X)
- 'Segment Details' rows (Kit1, Kit2, Chr, From, To, cM)

Produces:
- outputs/gedmatch_segments.csv (detailed per-segment rows)
- outputs/gedmatch_summary.txt (basic stats)

Usage:
  python scripts/parse_gedmatch_text.py path/to/gedmatch_text.txt

"""
import sys
import re
from pathlib import Path
import csv
from statistics import mean, median


def parse_segment_details(text):
    # Find the 'Segment Details:' section
    m = re.search(r'Segment Details:\s*(.*?)\n\n', text, flags=re.S|re.I)
    seg_text = None
    if m:
        # segment details are likely long; instead, extract from 'Segment Details:' to 'Your results' or end
        start = m.start()
        tail = text[start:]
        end_marker = re.search(r"Your results have been generated|Software Ver:|$", tail, flags=re.I)
        seg_text = tail[:end_marker.start()] if end_marker else tail
    else:
        # fallback: try to find lines that look like Kit1\tKit2\tChr\tFrom\tTo\tcM
        seg_text = text

    # Now parse lines that look like: A082033\t*rlmaupin53\tGU1800109\tIra L Toles\t1\t40974156\t64555255\t25.1
    segs = []
    for line in seg_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # tokens split by whitespace but names may contain spaces; use regex to capture k1 k1name k2 k2name chr from to cm
        # We'll search for pattern: ^(\S+)\s+(.*?)\s+(\S+)\s+(.*?)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9.]+)
        m = re.match(r'^(\S+)\s+(.+?)\s+(\S+)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9.]+)$', line)
        if m:
            k1, k1n, k2, k2n, chr_, start, end, cm = m.groups()
            segs.append({'kit1':k1,'name1':k1n,'kit2':k2,'name2':k2n,'chr':chr_,'start':int(start),'end':int(end),'cm':float(cm)})
            continue
        # try variant with kit numbers and names reversed or reduced columns
        m2 = re.match(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9.]+)$', line)
        if m2:
            k1,k1n,k2,k2n,start,end,_,cm = m2.groups()
            segs.append({'kit1':k1,'name1':k1n,'kit2':k2,'name2':k2n,'chr':None,'start':int(start),'end':int(end),'cm':float(cm)})
            continue
        # try lines with 6 columns: Kit1 Kit2 Chr From To cM
        m3 = re.match(r'^(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9.]+)$', line)
        if m3:
            k1,k2,chr_,start,end,cm=m3.groups()
            segs.append({'kit1':k1,'name1':'','kit2':k2,'name2':'','chr':chr_,'start':int(start),'end':int(end),'cm':float(cm)})

    return segs


def write_outputs(segs, outdir:Path):
    outdir.mkdir(parents=True, exist_ok=True)
    csvp = outdir / 'gedmatch_segments.csv'
    with csvp.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['kit1','name1','kit2','name2','chr','start','end','cm'])
        writer.writeheader()
        for s in segs:
            writer.writerow(s)

    # summary
    cms = [s['cm'] for s in segs if s.get('cm') is not None]
    kits = {}
    for s in segs:
        kits[s['kit1']] = kits.get(s['kit1'],0)+1
        kits[s['kit2']] = kits.get(s['kit2'],0)+1

    summary = []
    summary.append(f'Parsed {len(segs)} segments')
    if cms:
        summary.append(f'Total cM: {sum(cms):.1f}')
        summary.append(f'Mean cM: {mean(cms):.2f}')
        summary.append(f'Median cM: {median(cms):.2f}')
        summary.append(f'Max cM: {max(cms):.2f}')

    summary.append('\nTop 10 kits by segment count:')
    for k,v in sorted(kits.items(), key=lambda x:-x[1])[:10]:
        summary.append(f'{k}: {v}')

    (outdir / 'gedmatch_summary.txt').write_text('\n'.join(summary), encoding='utf-8')
    print('\n'.join(summary))
    print('\nWrote CSV to', csvp)


def main():
    if len(sys.argv) < 2:
        print('Usage: parse_gedmatch_text.py path/to/gedmatch_text.txt')
        sys.exit(2)
    p = Path(sys.argv[1])
    txt = p.read_text(encoding='utf-8', errors='ignore')
    segs = parse_segment_details(txt)
    write_outputs(segs, Path('outputs'))


if __name__ == '__main__':
    main()
