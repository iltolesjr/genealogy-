"""
Simple segment-table analysis tool.
Usage: python analyze_segments.py /path/to/segmatch.csv --out-dir ./out

Produces a console summary and writes CSVs with per-match aggregates and top segments.
"""
import argparse
import os
import sys
import pandas as pd
import numpy as np


def summarize(df):
    lines = []
    lines.append(f"Rows: {len(df):,}")
    lines.append("\nColumns and types:")
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        lines.append(df.dtypes.astype(str).to_string())
    lines.append("\nMissing values per column:")
    missing = df.isnull().sum()
    lines.append(missing[missing>0].to_string() if missing.sum()>0 else "None")
    return "\n".join(lines)


def numeric_stats(df, numeric_cols):
    out = []
    for c in numeric_cols:
        s = df[c].dropna()
        if s.empty:
            out.append(f"{c}: no numeric data")
            continue
        out.append(f"{c}: count={s.count()}, mean={s.mean():.3f}, std={s.std():.3f}, min={s.min()}, 25%={s.quantile(0.25)}, median={s.median()}, 75%={s.quantile(0.75)}, max={s.max()}")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('csv', help='segment match CSV file')
    p.add_argument('--out-dir', default='.', help='output directory')
    p.add_argument('--top-n', type=int, default=20, help='top N results to write')
    args = p.parse_args()

    if not os.path.exists(args.csv):
        print(f"File not found: {args.csv}")
        sys.exit(2)

    os.makedirs(args.out_dir, exist_ok=True)

    df = pd.read_csv(args.csv)

    # Basic summary
    print('--- Basic summary ---')
    print(summarize(df))

    # Attempt to find numeric columns likely to be segment measures
    candidates = [c for c in df.columns if any(k in c.lower() for k in ['cm','cM','centim','length','start','end','snp','markers','pos'])]
    # fallback to numeric dtype columns
    numeric_cols = [c for c in candidates if pd.api.types.is_numeric_dtype(df[c])] or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    print('\n--- Numeric column stats ---')
    print(numeric_stats(df, numeric_cols))

    # Try to standardize column names we care about
    colmap = {k.lower():k for k in df.columns}
    def find(colnames):
        for name in colnames:
            nl = name.lower()
            if nl in colmap:
                return colmap[nl]
        return None

    match_col = find(['match_id','match','person','match_name','name','displayname'])
    cm_col = find(['cm','cM','centimorgans','shared_cm','shared cM','shared cM'.lower()])
    start_col = find(['start','segment_start','chr_start','bp_start','from'])
    end_col = find(['end','segment_end','chr_end','bp_end','to'])
    chr_col = find(['chr','chrom','chromosome'])
    snp_col = find(['snp','snps','markers'])

    # print detected important columns
    print('\n--- Detected key columns ---')
    print(f'match_col: {match_col}')
    print(f'cm_col: {cm_col}')
    print(f'start_col: {start_col}')
    print(f'end_col: {end_col}')
    print(f'chr_col: {chr_col}')
    print(f'snp_col: {snp_col}')

    # Compute segment length if start/end present
    if start_col and end_col and pd.api.types.is_numeric_dtype(df[start_col]) and pd.api.types.is_numeric_dtype(df[end_col]):
        df['seg_len_bp'] = (df[end_col] - df[start_col]).abs()
        print('\nComputed seg_len_bp column (bp).')
    else:
        df['seg_len_bp'] = np.nan

    # Ensure cm column numeric
    if cm_col:
        try:
            df['_cm'] = pd.to_numeric(df[cm_col], errors='coerce')
        except Exception:
            df['_cm'] = pd.to_numeric(df[cm_col].astype(str).str.replace('[^0-9eE.+-]','',regex=True), errors='coerce')
    else:
        # fallback: use any numeric column named like 'length' or first numeric
        fallback = None
        for c in numeric_cols:
            if 'len' in c.lower() or 'cm' in c.lower() or 'shared' in c.lower():
                fallback = c
                break
        if not fallback and numeric_cols:
            fallback = numeric_cols[0]
        if fallback:
            print(f"No explicit cM column found; using '{fallback}' as cm proxy")
            df['_cm'] = pd.to_numeric(df[fallback], errors='coerce')
        else:
            df['_cm'] = np.nan

    # Per-match aggregates
    if match_col:
        agg = df.groupby(match_col).agg(
            segments=('seg_len_bp','count'),
            total_cm=('_cm','sum'),
            mean_cm=('_cm','mean'),
            max_cm=('_cm','max')
        ).reset_index().sort_values('total_cm', ascending=False)
        agg.to_csv(os.path.join(args.out_dir,'per_match_aggregates.csv'), index=False)
        print(f"\nWrote per-match aggregates to {os.path.join(args.out_dir,'per_match_aggregates.csv')}")

        # Top N matches
        topn = agg.head(args.top_n)
        topn.to_csv(os.path.join(args.out_dir,'top_matches.csv'), index=False)
        print(f"Wrote top {args.top_n} matches to {os.path.join(args.out_dir,'top_matches.csv')}")
    else:
        print('No match identifier column found; skipping per-match aggregates.')

    # Top segments by cm
    if '_cm' in df.columns:
        top_seg = df.sort_values('_cm', ascending=False).head(args.top_n)
        top_seg.to_csv(os.path.join(args.out_dir,'top_segments.csv'), index=False)
        print(f"Wrote top {args.top_n} segments by cM to {os.path.join(args.out_dir,'top_segments.csv')}")

    # Simple histogram info
    if '_cm' in df.columns and df['_cm'].notnull().any():
        s = df['_cm'].dropna()
        print('\n--- cM distribution ---')
        print(f'mean={s.mean():.3f}, median={s.median():.3f}, std={s.std():.3f}, min={s.min()}, max={s.max()}')
        print('Counts by bins:')
        bins = [0,1,5,7,10,20,30,50,100,1000]
        print(s.groupby(pd.cut(s, bins)).count().to_string())

    # Save a short text report
    report = []
    report.append('Basic summary:')
    report.append(summarize(df))
    report.append('\nNumeric stats:')
    report.append(numeric_stats(df, numeric_cols))
    report.append('\nDetected key columns:')
    report.append(f'match_col: {match_col}\ncm_col: {cm_col}\nstart_col: {start_col}\nend_col: {end_col}\nchr_col: {chr_col}\nsnp_col: {snp_col}')

    with open(os.path.join(args.out_dir,'segment_analysis_report.txt'),'w',encoding='utf-8') as fh:
        fh.write('\n'.join(report))
    print(f"Wrote text report to {os.path.join(args.out_dir,'segment_analysis_report.txt')}")

if __name__=='__main__':
    main()
