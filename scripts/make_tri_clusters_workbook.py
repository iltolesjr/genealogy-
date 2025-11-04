"""
Build an Excel workbook with triangulated clusters on the first sheet.

Reads: outputs/wato_triangulated_expanded_kits.csv
Writes: outputs/triangulated_clusters.xlsx with sheet 'Triangulated Clusters'

Columns: Rank, Match (Kit), Kit, TotalTriangulatedcM, TriHits, EstimatedRelationship, ClusterGroup, Sources
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'outputs'
WATO_CSV = OUT_DIR / 'wato_triangulated_expanded_kits.csv'
XLSX_OUT = OUT_DIR / 'triangulated_clusters.xlsx'


def write_xlsx(rows):
    try:
        from openpyxl import Workbook
    except ImportError as e:
        print('openpyxl not installed. Please run: python -m pip install openpyxl')
        raise

    wb = Workbook()
    ws = wb.active
    ws.title = 'Triangulated Clusters'

    headers = ['Rank','Match (Kit)','Kit','TotalTriangulatedcM','TriHits','EstimatedRelationship','ClusterGroup','Sources']
    ws.append(headers)

    for r in rows:
        ws.append([
            r.get('Rank'),
            r.get('MatchName') or '',
            r.get('Kit') or '',
            int(r.get('TotalTriangulatedcM') or 0),
            int(r.get('TriHits') or 0),
            r.get('EstimatedRelationship') or '',
            r.get('ClusterGroup') or '',
            r.get('Sources') or '',
        ])

    wb.save(XLSX_OUT)
    return XLSX_OUT


def main():
    if not WATO_CSV.exists():
        print('Missing input:', WATO_CSV)
        return
    with WATO_CSV.open('r', encoding='utf-8', newline='') as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
    outp = write_xlsx(rows)
    print('Wrote', outp)


if __name__ == '__main__':
    main()
