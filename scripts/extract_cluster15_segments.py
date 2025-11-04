"""
Extract segments for cluster-15 candidates by fuzzy-matching names.

Behavior:
 - Targets: names supplied in the repository conversation (Tiffanie Harrison, Juanita Bradberry, Aesha Uqdah, DIANE TOLBERT, Erin Kabbae, Clarence Ervin, Nford)
 - Read `scripts/csvsegmatch_.csv` (PrimaryKit,MatchedKit,chr,Start,End,Segment cM,SNPs,MatchedName,...)
 - Fuzzy-match MatchedName to targets (difflib ratio) and also accept substring/email matches.
 - Mark rows that have the MatchedKit present in `outputs/triangulation_wilma_top.csv` as triangulated (prefer these when writing results).
 - Write `outputs/cluster15_segments.csv` with header: hr,Start,End,cM,SNPs,Match Name

Run from repo root.
"""
import csv
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'outputs'
CSVSEG = Path(__file__).resolve().parents[0] / 'csvsegmatch_.csv'
TRI = OUT_DIR / 'triangulation_wilma_top.csv'

# Target names to fuzzy-match (from user paste)
TARGET_NAMES = [
    'Tiffanie Harrison',
    'Juanita Bradberry',
    'Aesha Uqdah',
    'DIANE TOLBERT',
    'Erin Kabbae',
    'Clarence Ervin',
    'Nford'
]

MATCH_THRESHOLD = 0.65


def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def load_triangulated_kits(tri_path):
    kits = set()
    if not tri_path.exists():
        return kits
    with tri_path.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            k = (r.get('kit') or '').strip()
            if k:
                kits.add(k)
    return kits


def match_row(name):
    if not name:
        return False
    n = name.strip()
    for t in TARGET_NAMES:
        if t.lower() in n.lower():
            return True
        if n.lower() in t.lower():
            return True
        if similar(n, t) >= MATCH_THRESHOLD:
            return True
    return False


def main():
    tri_kits = load_triangulated_kits(TRI)
    if not CSVSEG.exists():
        print('Error: segment file not found:', CSVSEG)
        return

    out_path = OUT_DIR / 'cluster15_segments.csv'
    rows = []
    with CSVSEG.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get('MatchedName') or r.get('MatchedName') or '').strip()
            # some files have asterisk prefix; strip
            if name.startswith('*'):
                name = name[1:].strip()

            if match_row(name):
                kits = (r.get('MatchedKit') or r.get('MatchedKit') or '').strip()
                is_tri = kits in tri_kits
                rows.append({'chr': r.get('chr') or r.get('chr') , 'Start': (r.get('Start') or '').strip(), 'End': (r.get('End') or '').strip(), 'cM': (r.get('Segment cM') or r.get('Segment cM') or '').strip(), 'SNPs': (r.get('SNPs') or '').strip(), 'Match Name': name, 'MatchedKit': kits, 'Tri': is_tri})

    # Sort: triangulated rows first, then by cM desc
    def cmi(x):
        try:
            return float(x['cM'])
        except Exception:
            return 0.0

    rows.sort(key=lambda r: (not r['Tri'], -cmi(r)))

    with out_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['hr','Start','End','cM','SNPs','Match Name'])
        for r in rows:
            # hr should be chromosome number
            hr = r.get('chr') or ''
            # int cM only
            try:
                cm_int = int(float(r['cM']))
            except Exception:
                cm_int = r['cM']
            # int SNPs only
            try:
                snps_int = int(float(r['SNPs'])) if r['SNPs'] else ''
            except Exception:
                snps_int = r['SNPs']
            # append kit after name
            name_with_kit = r['Match Name']
            if r.get('MatchedKit'):
                name_with_kit = f"{name_with_kit} ({r['MatchedKit']})"
            writer.writerow([hr, r['Start'], r['End'], cm_int, snps_int, name_with_kit])

    print(f'Wrote {out_path} with {len(rows)} rows (triangulated rows prioritized).')


if __name__ == '__main__':
    main()
