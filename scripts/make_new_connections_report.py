"""
Create a 'new connections' report from triangulated WATO CSV.

Heuristic:
 - Use targets: A044456 (Temara), MX2414682 (Tolbert), AN9982138 (Ivy).
 - Build union of their 'Sources' from `outputs/wato_triangulated_expanded_kits.csv`.
 - For each kit row, compute how many of those target sources it shares (overlap count).
 - Load name mapping from the same CSV (MatchName) and append (Kit) for clarity.
 - Load EstimatedRelationship and ClusterGroup from the WATO CSV (already merged earlier via shared matches when available).
 - Filter to likely relationships up to ~5th cousin by parsing the text.
 - Output CSV: outputs/new_connections_report.csv with Rank, Kit, Name, TotalTriangulatedcM (int), TriHits, SharedSourceOverlap, EstimatedRelationship, ClusterGroup.

Note: Relationship parsing is approximate and conservative.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'outputs'
WATO = OUT_DIR / 'wato_triangulated_expanded_kits.csv'

TARGET_KITS = {'A044456','MX2414682','AN9982138'}


def parse_degree(rel_text: str) -> int | None:
    if not rel_text:
        return None
    t = rel_text.lower()
    # quick wins
    for n in range(2, 8):
        if f"{n}th cousin" in t or f"{n} rd cousin" in t or f"{n} nd cousin" in t or f"{n} st cousin" in t or f"{n} cousin" in t:
            return n
    if 'half ' in t:
        # half cousins are often same degree for this filter
        for n in range(2, 8):
            if f"half {n}" in t:
                return n
    # unparsed
    return None


def split_sources(src: str) -> set[str]:
    if not src:
        return set()
    return {s.strip() for s in src.split(',') if s.strip()}


def main():
    if not WATO.exists():
        print('Missing WATO CSV:', WATO)
        return

    rows = []
    targets_sources = set()
    with WATO.open('r', encoding='utf-8', newline='') as f:
        rdr = csv.DictReader(f)
        all_rows = list(rdr)

    # collect target sources
    for r in all_rows:
        if (r.get('Kit') or '').strip() in TARGET_KITS:
            targets_sources |= split_sources(r.get('Sources',''))

    for r in all_rows:
        kit = (r.get('Kit') or '').strip()
        if not kit:
            continue
        try:
            cm = int(float(r.get('TotalTriangulatedcM') or '0'))
        except Exception:
            cm = 0
        hits = int(r.get('TriHits') or 0)
        name = (r.get('MatchName') or '').strip() or kit
        name_kit = f"{name} ({kit})"
        rel = (r.get('EstimatedRelationship') or '').strip()
        cluster = (r.get('ClusterGroup') or '').strip()
        srcs = split_sources(r.get('Sources',''))
        overlap = len(srcs & targets_sources)
        deg = parse_degree(rel)
        # filter: focus on <=5th cousin when known; if unknown, keep but rank lower by deg
        ok = (deg is None) or (deg <= 5)
        if not ok:
            continue
        rows.append({'Kit': kit, 'Name': name_kit, 'TotalTriangulatedcM': cm, 'TriHits': hits, 'SharedSourceOverlap': overlap, 'EstimatedRelationship': rel, 'ClusterGroup': cluster})

    # sort by overlap desc, then cm desc, then hits desc
    rows.sort(key=lambda x: (x['SharedSourceOverlap'], x['TotalTriangulatedcM'], x['TriHits']), reverse=True)

    outp = OUT_DIR / 'new_connections_report.csv'
    with outp.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['Rank','Kit','Name','TotalTriangulatedcM','TriHits','SharedSourceOverlap','EstimatedRelationship','ClusterGroup'])
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            rr = dict(r)
            rr['Rank'] = i
            w.writerow(rr)

    print('Wrote', outp, 'with', len(rows), 'rows')


if __name__ == '__main__':
    main()
