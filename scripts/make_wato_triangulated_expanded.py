"""
Expand triangulation-based WATO export for target kits.

Behavior:
 - Targets: A044456 (Temara), MX2414682 (Tolbert), AN9982138 (Ivy Lee)
 - Find all triangulation "source" files where the target kits appear,
   then include every kit that appears in any of those source files.
 - Aggregate total cM and hit counts per included kit (from
   `outputs/triangulation_wilma_top.csv`).
 - Map kit -> friendly name via `outputs/one_to_one_combined.csv` when available.
 - Map friendly name -> Estimated Relationship, Cluster Group via
   `outputs/shared_matches_ira_debra.csv` when available.
 - Write:
     - `outputs/wato_triangulated_expanded_kits.csv`
     - `outputs/wato_triangulated_expanded_kits.txt` (WATO-style lines)
     - `outputs/segments_for_plot.csv` (top N kits aggregated min/start -> max/end)

Run from the repo root. The script is defensive about missing inputs.
"""
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'outputs'
TRI_PATH = OUT_DIR / 'triangulation_wilma_top.csv'
KIT_MAP_PATH = OUT_DIR / 'one_to_one_combined.csv'
SHARED_MAP_PATH = OUT_DIR / 'shared_matches_ira_debra.csv'

# Targets (kits requested)
TARGET_KITS = ['A044456', 'MX2414682', 'AN9982138']
TOP_N_SEGMENTS = 10


def read_tri_rows(tri_path):
    rows = []
    if not tri_path.exists():
        print(f'Warning: triangulation file not found: {tri_path}')
        return rows

    with tri_path.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            kit = (r.get('kit') or '').strip()
            src = (r.get('source') or '').strip()
            start = r.get('start') or r.get('Start') or ''
            end = r.get('end') or r.get('End') or ''
            cm = r.get('cM') or r.get('cM') or ''
            try:
                cmv = float(cm) if cm else 0.0
            except Exception:
                cmv = 0.0

            try:
                s = int(start) if start else None
            except Exception:
                s = None
            try:
                e = int(end) if end else None
            except Exception:
                e = None

            rows.append({'kit': kit, 'source': src, 'start': s, 'end': e, 'cM': cmv})

    return rows


def build_source_sets(rows, targets):
    # For each target, collect the set of source files where it appears
    sources = set()
    for r in rows:
        if r['kit'] in targets and r['source']:
            sources.add(r['source'])
    return sources


def expand_kits_by_sources(rows, sources, targets):
    included = set(targets)
    for r in rows:
        if r['source'] in sources:
            included.add(r['kit'])
    return included


def aggregate(rows, included_kits):
    totals = defaultdict(float)
    counts = defaultdict(int)
    sources_by_kit = defaultdict(set)
    spans = defaultdict(lambda: {'min': None, 'max': None})

    for r in rows:
        k = r['kit']
        if k not in included_kits:
            continue
        totals[k] += r['cM']
        counts[k] += 1
        if r['source']:
            sources_by_kit[k].add(r['source'])
        if r['start'] is not None:
            curmin = spans[k]['min']
            spans[k]['min'] = r['start'] if (curmin is None or r['start'] < curmin) else curmin
        if r['end'] is not None:
            curmax = spans[k]['max']
            spans[k]['max'] = r['end'] if (curmax is None or r['end'] > curmax) else curmax

    rows_out = []
    for k in included_kits:
        rows_out.append({'Kit': k,
                         'TotalTriangulatedcM': int(round(totals[k])),
                         'TriHits': counts[k],
                         'Sources': ','.join(sorted(sources_by_kit[k])) if sources_by_kit[k] else '' ,
                         'SpanMin': spans[k]['min'],
                         'SpanMax': spans[k]['max']})

    rows_out.sort(key=lambda r: r['TotalTriangulatedcM'], reverse=True)
    return rows_out


def load_kit_map(path):
    m = {}
    if not path.exists():
        return m
    with path.open('r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        for r in reader:
            if not r: 
                continue
            # Expect kit,name pairs; be defensive about malformed rows
            kit = r[0].strip()
            name = (r[1].strip() if len(r) > 1 else '')
            if kit:
                m[kit] = name
    return m


def load_shared_map(path):
    # Map Match Name -> (Estimated Relationship, Cluster Group)
    m = {}
    if not path.exists():
        return m
    with path.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get('Match Name') or r.get('MatchName') or '').strip()
            rel = (r.get('Estimated Relationship') or r.get('Estimated Relationship') or '').strip()
            cluster = (r.get('Cluster Group') or r.get('Cluster') or '').strip()
            if name:
                m[name] = {'EstimatedRelationship': rel, 'ClusterGroup': cluster}
    return m


def write_outputs(rows, kit_map, shared_map, out_dir):
    csv_out = out_dir / 'wato_triangulated_expanded_kits.csv'
    txt_out = out_dir / 'wato_triangulated_expanded_kits.txt'

    fieldnames = ['Rank', 'Kit', 'MatchName', 'TotalTriangulatedcM', 'TriHits', 'EstimatedRelationship', 'ClusterGroup', 'Sources']
    with csv_out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, r in enumerate(rows, start=1):
            kit = r['Kit']
            name = kit_map.get(kit, '')
            rel = ''
            cluster = ''
            if name and name in shared_map:
                rel = shared_map[name].get('EstimatedRelationship','')
                cluster = shared_map[name].get('ClusterGroup','')

            # Append kit after name when present
            matchname = f"{name} ({kit})" if name else kit
            writer.writerow({'Rank': i, 'Kit': kit, 'MatchName': matchname, 'TotalTriangulatedcM': r['TotalTriangulatedcM'], 'TriHits': r['TriHits'], 'EstimatedRelationship': rel, 'ClusterGroup': cluster, 'Sources': r['Sources']})

    with txt_out.open('w', encoding='utf-8') as f:
        for i, r in enumerate(rows, start=1):
            kit = r['Kit']
            name = kit_map.get(kit, '') or kit
            rel = ''
            cluster = ''
            if name in shared_map:
                rel = shared_map[name].get('EstimatedRelationship','')
                cluster = shared_map[name].get('ClusterGroup','')
            # Use 'Name (KIT)' format in text
            if name != kit:
                display = f"{name} ({kit})"
            else:
                display = kit
            line = f"{i}. {display} — {r['TotalTriangulatedcM']} cM — {rel} — {cluster} — sources: {r['Sources']}\n"
            f.write(line)

    return csv_out, txt_out


def write_segments(rows, out_dir, top_n=TOP_N_SEGMENTS):
    seg_out = out_dir / 'segments_for_plot.csv'
    # top N by total cM
    top = rows[:top_n]
    with seg_out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name','Start','End'])
        for r in top:
            name = r['Kit']
            s = r.get('SpanMin')
            e = r.get('SpanMax')
            if s is None or e is None:
                # skip if no span
                continue
            writer.writerow([name, s, e])
    return seg_out


def main():
    print('Reading triangulation rows...')
    rows = read_tri_rows(TRI_PATH)
    if not rows:
        print('No triangulation rows found; exiting')
        return

    print('Building source set for targets:', ', '.join(TARGET_KITS))
    sources = build_source_sets(rows, TARGET_KITS)
    print(f'Found {len(sources)} source files containing target kits')

    included_kits = expand_kits_by_sources(rows, sources, TARGET_KITS)
    print(f'Including {len(included_kits)} kits (targets + shared sources)')

    aggregated = aggregate(rows, included_kits)

    kit_map = load_kit_map(KIT_MAP_PATH)
    shared_map = load_shared_map(SHARED_MAP_PATH)

    csv_out, txt_out = write_outputs(aggregated, kit_map, shared_map, OUT_DIR)
    seg_out = write_segments(aggregated, OUT_DIR, top_n=TOP_N_SEGMENTS)

    print('Wrote', csv_out)
    print('Wrote', txt_out)
    print('Wrote', seg_out)

    print('\nTop 10 kits by triangulated cM:')
    for i, r in enumerate(aggregated[:10], start=1):
        print(f"{i}. {r['Kit']} — {r['TotalTriangulatedcM']} cM — hits={r['TriHits']}")


if __name__ == '__main__':
    main()
