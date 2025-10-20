import csv
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    ROOT / 'outputs' / 'all_matches_standardized.csv',
    ROOT / 'outputs' / 'one_to_one_combined_perfect.csv',
    ROOT.parent / 'Downloads' / 'csvsegmatch_.csv',
    ROOT.parent / 'Downloads' / 'app.csv',
]
OUT = ROOT / 'outputs' / 'gumatch_interval_all_sources_hits.csv'

INTERVALS = [
    ('17', 37036554, 63111452, 'GU_vs_A064172_chr17'),
    ('20', 24247556, 41711226, 'GU_vs_A064172_chr20'),
]

INT_MIN = 1_00000
INT_MAX = 300_000_000

def find_integers(tokens):
    ints = []
    for t in tokens:
        t2 = t.replace('"','').replace("'","")
        if re.fullmatch(r"\d+", t2):
            v = int(t2)
            if INT_MIN <= v <= INT_MAX:
                ints.append(v)
    return ints

def overlaps(a_start, a_end, b_start, b_end):
    return max(0, min(a_end, b_end) - max(a_start, b_start) + 1)

def scan_file(path, writer):
    if not path.exists():
        return 0
    hits = 0
    with path.open('r', encoding='utf-8', errors='ignore', newline='') as fh:
        sample = fh.read(4096)
        fh.seek(0)
        # try header-based CSV first
        try:
            reader = csv.DictReader(fh)
            headers = [h.lower() for h in (reader.fieldnames or [])]
            has_coords = any(h in headers for h in ('chr','start','end','b37start','b37end'))
            if has_coords:
                for row in reader:
                    # try multiple name variants
                    chrv = row.get('chr') or row.get('Chromosome') or row.get('CHR') or row.get('chrom')
                    start = row.get('B37Start') or row.get('Start') or row.get('start') or row.get('b37start')
                    end = row.get('B37End') or row.get('End') or row.get('end') or row.get('b37end')
                    if not (chrv and start and end):
                        continue
                    try:
                        ch = str(chrv).strip()
                        s = int(re.sub(r'[^0-9]','', start))
                        e = int(re.sub(r'[^0-9]','', end))
                    except Exception:
                        continue
                    for ichr, istart, iend, ilabel in INTERVALS:
                        if ch.lower().replace('chr','') == ichr:
                            ov = overlaps(s,e,istart,iend)
                            if ov>0:
                                out = dict(row)
                                out.update({'Source': str(path), 'IntervalLabel': ilabel, 'IntervalChr': ichr, 'IntervalStart': istart, 'IntervalEnd': iend, 'Overlap_bp': ov})
                                writer.writerow(out)
                                hits += 1
                return hits
        except Exception:
            fh.seek(0)

        # fallback: row-wise token scan
        fh.seek(0)
        rdr = csv.reader(fh)
        for tokens in rdr:
            if not tokens:
                continue
            # quick heuristic: look for chr token and two large integers
            ints = find_integers(tokens)
            if len(ints) < 2:
                # try to find pairs of ints in the whole line string
                continue
            # attempt to find chr token (a small int 1-23) nearby
            chr_token = None
            for t in tokens[:4]:
                if re.fullmatch(r"\d{1,2}", t.strip()):
                    chr_token = t.strip()
                    break
            if chr_token is None:
                # maybe second column is chr (app.csv style)
                if len(tokens) > 1 and re.fullmatch(r"\d{1,2}", tokens[1].strip()):
                    chr_token = tokens[1].strip()
            if chr_token is None:
                continue
            # pick two largest ints as start/end (heuristic)
            ints_sorted = sorted(set(ints))
            start, end = ints_sorted[0], ints_sorted[-1]
            ch = chr_token
            for ichr, istart, iend, ilabel in INTERVALS:
                if ch == ichr:
                    ov = overlaps(start, end, istart, iend)
                    if ov > 0:
                        out = {'Source': str(path), 'Tokens': '|'.join(tokens), 'chr': ch, 'Start': start, 'End': end, 'IntervalLabel': ilabel, 'IntervalStart': istart, 'IntervalEnd': iend, 'Overlap_bp': ov}
                        writer.writerow(out)
                        hits += 1
    return hits

def main():
    out_fields = None
    total = 0
    with OUT.open('w', newline='', encoding='utf-8') as outf:
        # use a flexible writer: write dict keys as they appear; we'll start with a common header
        writer = csv.DictWriter(outf, fieldnames=['Source','PrimaryKit','MatchedKit','chr','Start','End','Segment cM','MatchedName','MatchedEmail','IntervalLabel','IntervalChr','IntervalStart','IntervalEnd','Overlap_bp','Tokens'])
        writer.writeheader()
        for src in SOURCES:
            hits = scan_file(src, writer)
            print(f'Scanned {src} -> {hits} hits')
            total += hits
    print(f'Wrote combined hits to {OUT} ({total} total)')

if __name__ == '__main__':
    main()
