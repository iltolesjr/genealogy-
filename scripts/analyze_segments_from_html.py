#!/usr/bin/env python3
"""
Parse a GEDmatch/segment table HTML file and produce a CSV and summary.

Usage:
  python scripts/analyze_segments_from_html.py path/to/segmenttable.html

Outputs:
  - path/to/segmenttable_parsed.csv
  - summary printed to stdout

This script uses BeautifulSoup if available. If it's not installed, it falls back to a simple HTML tag parser.
"""
import sys
import csv
import statistics
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    _have_bs4 = True
except Exception:
    _have_bs4 = False


def text_or_none(el):
    if el is None:
        return None
    return el.get_text().strip()


def parse_with_bs4(html):
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        return []

    # Try to find a table with Chromosome header
    def headers_from_table(t):
        ths = t.find_all('th')
        if ths:
            return [text_or_none(th).lower() for th in ths]
        # fallback: first row cells
        first_row = t.find('tr')
        if first_row:
            tds = first_row.find_all(['td','th'])
            return [text_or_none(td).lower() for td in tds]
        return []

    selected = None
    for t in tables:
        headers = headers_from_table(t)
        if any('chrom' in h for h in headers):
            selected = t
            break
    if selected is None:
        selected = tables[0]

    rows = []
    # read header names
    header_cells = selected.find_all('th')
    if header_cells:
        headers = [text_or_none(h) for h in header_cells]
        data_rows = selected.find_all('tr')[1:]
    else:
        # maybe header is first row
        first = selected.find('tr')
        headers = [text_or_none(c) for c in first.find_all(['td','th'])]
        data_rows = selected.find_all('tr')[1:]

    for tr in data_rows:
        cells = tr.find_all(['td','th'])
        if not cells:
            continue
        rows.append([text_or_none(c) for c in cells])

    return headers, rows


def parse_with_regex(html):
    # Very small fallback: extract contents of <tr>...</tr> then <td>...</td>
    import re
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', html, flags=re.S|re.I)
    parsed = []
    for tr in trs:
        tds = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, flags=re.S|re.I)
        # strip tags
        clean = [re.sub(r'<[^>]+>', '', td).strip() for td in tds]
        if clean:
            parsed.append(clean)
    if not parsed:
        return [], []
    headers = parsed[0]
    rows = parsed[1:]
    return headers, rows


def normalize_row(headers, row):
    # map common column names
    mapping = {}
    for i, h in enumerate(headers):
        if h is None:
            continue
        key = h.lower()
        if 'chrom' in key or key.startswith('chr'):
            mapping['chrom'] = i
        elif 'start' in key and 'position' not in key:
            mapping['start'] = i
        elif 'end' in key:
            mapping['end'] = i
        elif 'cM' in h or 'cM' in key or 'centimorgan' in key:
            mapping['cm'] = i
        elif 'snp' in key:
            mapping['snps'] = i
        elif 'name' in key or 'match' in key:
            mapping['name'] = i
        elif 'kit' in key or 'id' in key:
            mapping['kit'] = i

    # fallback positional guesses
    out = {
        'chrom': None, 'start': None, 'end': None, 'cm': None, 'snps': None, 'name': None, 'kit': None
    }
    for k, idx in mapping.items():
        if idx < len(row):
            out[k] = row[idx]

    # Additional heuristics: if not found, try to fill by length
    rest = [c for c in row]
    # try parse numbers from row to fill start,end,cm,snps
    def to_num(x):
        if x is None:
            return None
        s = str(x).replace(',', '').replace('\xa0','').strip()
        try:
            if '.' in s:
                return float(s)
            return int(s)
        except Exception:
            try:
                return float(s)
            except Exception:
                return None

    # simple guesses for cm/snps: any numeric with decimal likely cM; any large int maybe positions
    numeric_vals = [(i, to_num(c)) for i, c in enumerate(row)]
    for i, val in numeric_vals:
        if val is None:
            continue
        if out['cm'] is None and isinstance(val, float):
            out['cm'] = row[i]
        if out['snps'] is None and isinstance(val, int) and val < 200000:
            # SNP counts typically < 1e6; but positions can be >1e6
            if val < 200000:
                # ambiguous: treat moderate ints as snps
                out['snps'] = row[i]
        if out['start'] is None and isinstance(val, int) and val > 1000 and val < 400000000:
            if out['start'] is None:
                out['start'] = row[i]
        if out['end'] is None and isinstance(val, int) and val > 1000 and val < 400000000 and out['end'] is None:
            out['end'] = row[i]

    return out


def to_number(s):
    if s is None:
        return None
    ss = str(s).replace(',', '').replace('\xa0','').strip()
    if ss == '':
        return None
    try:
        if '.' in ss:
            return float(ss)
        return int(ss)
    except Exception:
        try:
            return float(ss)
        except Exception:
            return None


def analyze(path: Path, debug=False):
    html = path.read_text(encoding='utf-8', errors='ignore')
    if _have_bs4:
        headers, rows = parse_with_bs4(html)
    else:
        headers, rows = parse_with_regex(html)

    if not rows:
        print('No rows parsed from the HTML file.')
        return 1

    if debug:
        print('\nDEBUG: headers:')
        print(headers)
        print('\nDEBUG: first 10 raw rows:')
        for r in rows[:10]:
            print(r)

    # normalize headers
    simple_headers = [h.lower() if h else '' for h in headers]

    parsed_rows = []
    for r in rows:
        normalized = normalize_row(simple_headers, r)
        parsed_rows.append(normalized)

    # convert to statistics
    cms = []
    snps = []
    chrom_counts = {}
    for r in parsed_rows:
        cm = to_number(r.get('cm'))
        s = to_number(r.get('snps'))
        chrom = r.get('chrom')
        if chrom:
            chrom_counts[chrom] = chrom_counts.get(chrom, 0) + 1
        if cm is not None:
            cms.append(cm)
        if s is not None:
            snps.append(s)

    out_csv = path.with_name(path.stem + '_parsed.csv')
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['chrom','start','end','cm','snps','name','kit'])
        writer.writeheader()
        for r in parsed_rows:
            writer.writerow({k: (r.get(k) or '') for k in writer.fieldnames})

    print(f'Parsed {len(parsed_rows)} segment rows')
    if cms:
        print(f'Total cM: {sum(cms):.2f}, mean: {statistics.mean(cms):.2f}, median: {statistics.median(cms):.2f}, max: {max(cms):.2f}')
    else:
        print('No cM values parsed')
    print(f'Wrote CSV to: {out_csv}')

    # top segments by cM
    rows_with_cm = [(to_number(r.get('cm')) or 0, r) for r in parsed_rows]
    rows_with_cm.sort(reverse=True, key=lambda x: x[0])
    print('\nTop 10 segments by cM:')
    for cm, r in rows_with_cm[:10]:
        print(f"{cm}\tc {r.get('chrom')}\t{r.get('start')}\t{r.get('end')}\t{r.get('name')}")

    print('\nCounts by chromosome (sample):')
    for k, v in sorted(chrom_counts.items(), key=lambda x: x[0]):
        print(f'{k}: {v}')

    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python analyze_segments_from_html.py path/to/segmenttable.html [--debug]')
        sys.exit(2)
    p = Path(sys.argv[1])
    debug = '--debug' in sys.argv[2:]
    if not p.exists():
        print(f'File not found: {p}')
        sys.exit(2)
    sys.exit(analyze(p, debug=debug))
