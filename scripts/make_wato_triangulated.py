#!/usr/bin/env python3
"""
Create a text-based WATO export of triangulated matches.

Produces:
 - outputs/wato_triangulated_top_matches.csv
 - outputs/wato_triangulated_top_matches.txt

Algorithm:
 - Sum cM per kit from outputs/triangulation_wilma_top.csv
 - Map kit -> display name using outputs/one_to_one_combined.csv when available
 - Try to attach Estimated Relationship and Cluster Group using outputs/shared_matches_ira_debra.csv by matching names
 - Output top N matches by total triangulated cM (default 50)
"""
import csv
import os
from collections import defaultdict, namedtuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'outputs')
TRI_FILE = os.path.join(OUT, 'triangulation_wilma_top.csv')
MAP_FILE = os.path.join(OUT, 'one_to_one_combined.csv')
SHARED_FILE = os.path.join(OUT, 'shared_matches_ira_debra.csv')


def read_triagulation_aggregate(path):
    totals = defaultdict(float)
    counts = defaultdict(int)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            kit = r.get('kit') or r.get('Kit') or r.get('Kit1') or ''
            cm = r.get('cM') or r.get('cm') or ''
            try:
                cmv = float(cm) if cm not in (None, '') else 0.0
            except ValueError:
                # sometimes cM fields use commas - remove non-numeric
                cmv = float(''.join(ch for ch in cm if ch.isdigit() or ch == '.')) if cm else 0.0
            totals[kit] += cmv
            counts[kit] += 1
    return totals, counts


def build_kit_name_map(path):
    # Map kit id -> display name (best-effort) using outputs/one_to_one_combined.csv
    name_map = {}
    if not os.path.exists(path):
        return name_map
    with open(path, newline='', encoding='utf-8') as f:
        rdr = csv.reader(f)
        header = next(rdr, None)
        for row in rdr:
            if not row:
                continue
            # safe-guard: some rows are malformed; take first two columns
            kit = row[0].strip()
            name = ''
            if len(row) > 1:
                name = row[1].strip()
            if kit:
                name_map[kit] = name
    return name_map


def build_shared_map(path):
    # Map Match Name -> (Estimated Relationship, Shared cM, Cluster Group)
    shared = {}
    if not os.path.exists(path):
        return shared
    with open(path, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            name = r.get('Match Name') or r.get('MatchName') or ''
            rel = r.get('Estimated Relationship') or r.get('EstimatedRelationship') or ''
            shared_cm = r.get('Shared cM') or r.get('Shared cM') or ''
            cluster = r.get('Cluster Group') or r.get('Cluster Group') or r.get('Cluster') or ''
            if name:
                shared[name.strip()] = (rel.strip(), shared_cm.strip(), cluster.strip())
    return shared


def write_outputs(rows, out_dir, top_n=50):
    csv_path = os.path.join(out_dir, 'wato_triangulated_top_matches.csv')
    txt_path = os.path.join(out_dir, 'wato_triangulated_top_matches.txt')

    fields = ['Rank','MatchName','Kit','TotalTriangulatedcM','TriHits','EstimatedRelationship','ClusterGroup','SourceNames']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(rows[:top_n], start=1):
            w.writerow({
                'Rank': i,
                'MatchName': r.match_name,
                'Kit': r.kit,
                'TotalTriangulatedcM': f"{r.total_cm:.1f}",
                'TriHits': r.hits,
                'EstimatedRelationship': r.estimated_rel,
                'ClusterGroup': r.cluster,
                'SourceNames': r.source or ''
            })

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('WATO triangulated matches export\n')
        f.write('Format: Rank. MatchName (Kit) — TotalTriangulatedcM cM — EstimatedRelationship — Cluster\n\n')
        for i, r in enumerate(rows[:top_n], start=1):
            line = f"{i}. {r.match_name or 'UNKNOWN'} ({r.kit}) — {r.total_cm:.1f} cM — {r.estimated_rel or 'Unknown'} — {r.cluster or ''}\n"
            f.write(line)

    return csv_path, txt_path


def main(top_n=50):
    totals, counts = read_triagulation_aggregate(TRI_FILE)
    name_map = build_kit_name_map(MAP_FILE)
    shared_map = build_shared_map(SHARED_FILE)

    Row = namedtuple('Row', ['kit','match_name','total_cm','hits','estimated_rel','cluster','source'])
    rows = []
    for kit, total in totals.items():
        name = name_map.get(kit, '')
        # try to find shared_map entry by name exact match
        estimated_rel = ''
        cluster = ''
        shared_cm = ''
        if name and name in shared_map:
            estimated_rel, shared_cm, cluster = shared_map[name]
        # fallback: if kit in shared_map keys (some exports may use kit ids as names)
        elif kit and kit in shared_map:
            estimated_rel, shared_cm, cluster = shared_map[kit]

        rows.append(Row(kit=kit, match_name=name or kit, total_cm=total, hits=counts.get(kit,0), estimated_rel=estimated_rel, cluster=cluster, source='triangulation_wilma_top'))

    # sort by total_cm desc
    rows.sort(key=lambda r: r.total_cm, reverse=True)

    csv_out, txt_out = write_outputs(rows, OUT, top_n=top_n)
    print(f'Wrote {csv_out}')
    print(f'Wrote {txt_out}')
    print('\nTop 10 matches:')
    for i, r in enumerate(rows[:10], start=1):
        print(f"{i}. {r.match_name} ({r.kit}) — {r.total_cm:.1f} cM — {r.estimated_rel or 'Unknown'} — {r.cluster or ''}")


if __name__ == '__main__':
    main(top_n=50)
