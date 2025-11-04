"""
Aggregate triangulated cM for a set of target kit IDs and produce
WATO-style CSV and text outputs using kit IDs (not friendly names).

Targets included by default: A044456 (Temara), MX2414682 (Tolbert - Debbie), AN9982138 (Ivy Lee)

Usage: run from repo root. Outputs written to outputs/wato_triangulated_filtered_kits.csv
and outputs/wato_triangulated_filtered_kits.txt
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'outputs'
TRI_PATH = OUT_DIR / 'triangulation_wilma_top.csv'

# Kits to include (use kit IDs as the label in WATO)
TARGET_KITS = ['A044456', 'MX2414682', 'AN9982138']


def aggregate_for_kits(tri_path, targets):
    totals = {k: 0.0 for k in targets}
    counts = {k: 0 for k in targets}
    if not tri_path.exists():
        raise FileNotFoundError(tri_path)

    with tri_path.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            kit = r.get('kit', '').strip()
            cm = r.get('cM', '').strip()
            try:
                cmv = float(cm) if cm else 0.0
            except Exception:
                cmv = 0.0

            if kit in targets:
                totals[kit] += cmv
                counts[kit] += 1

    rows = []
    for k in targets:
        rows.append({'Kit': k, 'TotalTriangulatedcM': round(totals[k], 3), 'TriHits': counts[k]})
    # sort by total cM desc
    rows.sort(key=lambda r: r['TotalTriangulatedcM'], reverse=True)
    return rows


def write_outputs(rows, out_dir):
    csv_out = out_dir / 'wato_triangulated_filtered_kits.csv'
    txt_out = out_dir / 'wato_triangulated_filtered_kits.txt'

    with csv_out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Rank', 'Kit', 'TotalTriangulatedcM', 'TriHits'])
        writer.writeheader()
        for i, r in enumerate(rows, start=1):
            writer.writerow({'Rank': i, 'Kit': r['Kit'], 'TotalTriangulatedcM': r['TotalTriangulatedcM'], 'TriHits': r['TriHits']})

    with txt_out.open('w', encoding='utf-8') as f:
        for i, r in enumerate(rows, start=1):
            line = f"{i}. {r['Kit']} ({r['Kit']}) — {r['TotalTriangulatedcM']} cM — TriHits: {r['TriHits']}\n"
            f.write(line)

    return csv_out, txt_out


def main():
    print('Aggregating triangulated cM for target kits:', ', '.join(TARGET_KITS))
    rows = aggregate_for_kits(TRI_PATH, TARGET_KITS)
    csv_out, txt_out = write_outputs(rows, OUT_DIR)
    print('Wrote', csv_out)
    print('Wrote', txt_out)
    print('\nTop results:')
    for i, r in enumerate(rows[:10], start=1):
        print(f"{i}. {r['Kit']} — {r['TotalTriangulatedcM']} cM — hits={r['TriHits']}")


if __name__ == '__main__':
    main()
