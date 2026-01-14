#!/usr/bin/env python3
"""
Generate comprehensive DNA segment report for Ivy Lee (AN9982138).

This script produces a markdown report showing:
1. Direct segments shared between Ira and Ivy
2. Triangulated segments (TRI) - where Ira, Ivy, and others all match
3. In Common With (ICW) matches - people who match both Ira and Ivy
4. Chromosome-by-chromosome breakdown
5. Statistical summary

Usage: python generate_ivy_segment_report.py
Output: outputs/ivy_shared_segments_report.md
"""

from pathlib import Path
import csv
from collections import defaultdict
from datetime import datetime

# Constants
ROOT = Path(__file__).parent.parent
IVY_KIT = "AN9982138"
IVY_NAME = "Ivy Lee"
IVY_EMAIL = "ivjole9@gmail.com"
IRA_KIT = "GU1800109"

# Input files
TRIANGULATION_FILE = ROOT / 'outputs' / 'triangulation_wilma_top.csv'
WATO_FILTERED = ROOT / 'outputs' / 'wato_triangulated_filtered_kits.csv'
AUTO_CLUSTER = ROOT / 'Research Data' / 'auto_cluster_mapping.csv'
ONE_TO_ONE = ROOT / 'outputs' / 'one_to_one_combined_perfect.csv'

# Output file
OUTPUT_FILE = ROOT / 'outputs' / 'ivy_shared_segments_report.md'


def load_triangulated_segments():
    """Load triangulated segments involving Ivy from triangulation_wilma_top.csv"""
    segments = []
    if not TRIANGULATION_FILE.exists():
        return segments
    
    try:
        with open(TRIANGULATION_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('kit') == IVY_KIT:
                    segments.append({
                        'kit': row.get('kit', ''),
                        'email': row.get('email', ''),
                        'start': row.get('start', ''),
                        'end': row.get('end', ''),
                        'cM': row.get('cM', ''),
                        'source': row.get('source', '')
                    })
    except Exception as e:
        print(f"Warning: Could not load triangulation file: {e}")
    
    return segments


def load_wato_stats():
    """Load triangulation statistics from wato_triangulated_filtered_kits.csv"""
    stats = {}
    if not WATO_FILTERED.exists():
        return stats
    
    try:
        with open(WATO_FILTERED, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Kit') == IVY_KIT:
                    stats = {
                        'rank': row.get('Rank', 'N/A'),
                        'total_triangulated_cM': row.get('TotalTriangulatedcM', '0'),
                        'tri_hits': row.get('TriHits', '0')
                    }
                    break
    except Exception as e:
        print(f"Warning: Could not load WATO stats: {e}")
    
    return stats


def load_cluster_info():
    """Load cluster information from auto_cluster_mapping.csv"""
    cluster_info = {}
    if not AUTO_CLUSTER.exists():
        return cluster_info
    
    try:
        with open(AUTO_CLUSTER, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('kit') == IVY_KIT:
                    cluster_info = {
                        'name': row.get('name', IVY_NAME),
                        'cluster': row.get('cluster', 'N/A'),
                        'cm': row.get('cm', '0'),
                        'avg_seg_size': row.get('avg_seg_size', '0'),
                        'email': row.get('email', IVY_EMAIL),
                        'notes': row.get('notes', '')
                    }
                    break
    except Exception as e:
        print(f"Warning: Could not load cluster info: {e}")
    
    return cluster_info


def load_one_to_one_segments():
    """Load direct one-to-one segments with Ivy"""
    segments = []
    if not ONE_TO_ONE.exists():
        return segments
    
    try:
        with open(ONE_TO_ONE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Look for rows where Kit1 or Kit2 is Ivy
                kit1 = row.get('Kit1', '')
                kit2 = row.get('Kit2', '')
                if IVY_KIT in kit1 or IVY_KIT in kit2:
                    segments.append({
                        'chr': row.get('Chr', ''),
                        'start': row.get('Start', ''),
                        'end': row.get('End', ''),
                        'cM': row.get('cM', ''),
                        'snps': row.get('SNPs', '')
                    })
    except Exception as e:
        print(f"Warning: Could not load one-to-one segments: {e}")
    
    return segments


def get_icw_matches(triangulated_segments):
    """Extract In Common With (ICW) matches from triangulated segments"""
    # ICW matches are the other kits in the triangulation files
    icw_kits = set()
    source_files = set()
    
    for seg in triangulated_segments:
        source = seg.get('source', '')
        if source:
            source_files.add(source)
    
    return source_files


def load_detailed_icw_from_sources():
    """Load detailed ICW match information from triangulation source files"""
    icw_matches = []
    tri_files = []
    
    # Look for triangulation files in scripts and outputs directories
    for pattern_dir in [ROOT / 'scripts', ROOT / 'outputs']:
        if pattern_dir.exists():
            tri_files.extend(pattern_dir.glob('triang_*.csv'))
    
    for tri_file in tri_files:
        try:
            with open(tri_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check if Ivy is in this triangulation
                    kit1 = row.get('Kit1 Number', '')
                    kit2 = row.get('Kit2 Number', '')
                    
                    if IVY_KIT in kit1 or IVY_KIT in kit2:
                        # Get the other kit
                        other_kit = kit2 if IVY_KIT in kit1 else kit1
                        other_name = row.get('Kit2 Name', '') if IVY_KIT in kit1 else row.get('Kit1 Name', '')
                        other_email = row.get('Kit2 Email', '') if IVY_KIT in kit1 else row.get('Kit1 Email', '')
                        
                        icw_matches.append({
                            'kit': other_kit,
                            'name': other_name,
                            'email': other_email,
                            'chr': row.get('Chr', ''),
                            'start': row.get('B37 Start', ''),
                            'end': row.get('B37 End', ''),
                            'cM': row.get('cM', ''),
                            'tg': row.get('TG', ''),
                            'source': tri_file.name
                        })
        except Exception as e:
            print(f"Warning: Could not process {tri_file}: {e}")
    
    return icw_matches


def group_segments_by_chromosome(segments):
    """Group segments by chromosome and calculate totals"""
    chr_groups = defaultdict(list)
    
    for seg in segments:
        chr_val = seg.get('chr', 'Unknown')
        chr_groups[chr_val].append(seg)
    
    return chr_groups


def safe_sort_chromosome(chr_val):
    """Safely sort chromosome values, handling non-numeric cases"""
    try:
        if chr_val and chr_val.isdigit():
            return int(chr_val)
    except (ValueError, AttributeError):
        pass
    return 99  # Put non-numeric chromosomes at the end


def generate_markdown_report(triangulated_segs, wato_stats, cluster_info, one_to_one_segs, icw_sources, icw_matches):
    """Generate comprehensive markdown report"""
    
    report = []
    report.append(f"# DNA Segment Report: Ivy Lee (Kit {IVY_KIT})")
    report.append("")
    report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    report.append("")
    report.append("---")
    report.append("")
    
    # Section 1: Overview
    report.append("## 1. Overview")
    report.append("")
    report.append(f"**Match Name:** {cluster_info.get('name', IVY_NAME)}")
    report.append(f"**Kit Number:** {IVY_KIT}")
    report.append(f"**Email:** {cluster_info.get('email', IVY_EMAIL)}")
    report.append(f"**Cluster:** {cluster_info.get('cluster', 'N/A')}")
    report.append("")
    
    # Section 2: Summary Statistics
    report.append("## 2. Summary Statistics")
    report.append("")
    report.append("| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| Direct Shared cM | {cluster_info.get('cm', 'N/A')} cM |")
    report.append(f"| Average Segment Size | {cluster_info.get('avg_seg_size', 'N/A')} cM |")
    report.append(f"| Total Triangulated cM (TRI) | {wato_stats.get('total_triangulated_cM', 'N/A')} cM |")
    report.append(f"| Triangulation Hits | {wato_stats.get('tri_hits', 'N/A')} |")
    report.append(f"| Triangulation Rank | #{wato_stats.get('rank', 'N/A')} |")
    report.append("")
    
    # Section 3: Triangulated Segments (TRI)
    report.append("## 3. Triangulated Segments (TRI)")
    report.append("")
    report.append("**Triangulation** means that you (Ira), Ivy, and at least one other person all share DNA ")
    report.append("on the same chromosome segment. This strongly indicates the DNA comes from a common ancestor.")
    report.append("")
    
    if triangulated_segs:
        report.append(f"**Total Triangulated Segments Found:** {len(triangulated_segs)}")
        report.append("")
        
        # Group by unique segments (start-end-cM combinations)
        unique_segments = {}
        for seg in triangulated_segs:
            key = (seg['start'], seg['end'], seg['cM'])
            if key not in unique_segments:
                unique_segments[key] = {'count': 0, 'sources': set()}
            unique_segments[key]['count'] += 1
            unique_segments[key]['sources'].add(seg.get('source', 'unknown'))
        
        report.append("### Unique Triangulated Segments")
        report.append("")
        report.append("| Segment Range | cM | Occurrences | Sources |")
        report.append("|---------------|-----|-------------|---------|")
        
        # Filter and sort segments
        def safe_float(val, default=0.0):
            try:
                return float(val) if val else default
            except (ValueError, TypeError):
                return default
        
        for (start, end, cm), data in sorted(unique_segments.items(), 
                                             key=lambda x: safe_float(x[0][2]), 
                                             reverse=True):
            # Skip segments with 0 cM as they are likely data quality issues
            if safe_float(cm) <= 0:
                continue
            sources_str = ', '.join(sorted(data['sources']))[:50] + '...' if len(', '.join(sorted(data['sources']))) > 50 else ', '.join(sorted(data['sources']))
            report.append(f"| {start} - {end} | {cm} | {data['count']} | {sources_str} |")
        
        report.append("")
    else:
        report.append("*No triangulated segment data found in processed files.*")
        report.append("")
    
    # Section 4: In Common With (ICW) Matches
    report.append("## 4. In Common With (ICW) Matches")
    report.append("")
    report.append("**In Common With (ICW)** refers to people who match both you and Ivy. ")
    report.append("These matches can help identify the common ancestral line.")
    report.append("")
    
    if icw_matches:
        # Group ICW matches by unique kit
        icw_by_kit = defaultdict(list)
        for match in icw_matches:
            icw_by_kit[match['kit']].append(match)
        
        report.append(f"**Number of Unique ICW Matches:** {len(icw_by_kit)}")
        report.append(f"**Total ICW Triangulations:** {len(icw_matches)}")
        report.append("")
        
        # Show top ICW matches by number of triangulations
        sorted_icw = sorted(icw_by_kit.items(), key=lambda x: len(x[1]), reverse=True)
        
        report.append("### Top In Common With Matches")
        report.append("")
        report.append("| Kit | Name | Email | Triangulations | Chromosomes |")
        report.append("|-----|------|-------|----------------|-------------|")
        
        for kit, matches in sorted_icw[:25]:  # Show top 25
            name = matches[0]['name'] if matches else ''
            email = matches[0]['email'] if matches else ''
            tri_count = len(matches)
            chrs = ', '.join(sorted(set(m['chr'] for m in matches if m['chr'])))[:30]
            report.append(f"| {kit} | {name} | {email} | {tri_count} | {chrs} |")
        
        if len(sorted_icw) > 25:
            report.append(f"| ... | ... | ... | ... | ... |")
            report.append(f"| *{len(sorted_icw) - 25} more matches* | | | | |")
        
        report.append("")
    elif icw_sources:
        report.append(f"**Number of Triangulation Groups:** {len(icw_sources)}")
        report.append("")
        report.append("### Triangulation Source Files")
        report.append("")
        for source in sorted(icw_sources)[:20]:  # Show first 20
            report.append(f"- {source}")
        if len(icw_sources) > 20:
            report.append(f"- *...and {len(icw_sources) - 20} more*")
        report.append("")
    else:
        report.append("*No ICW data available from triangulation files.*")
        report.append("")
    
    # Section 5: Direct Segments (One-to-One)
    report.append("## 5. Direct Shared Segments (One-to-One)")
    report.append("")
    report.append("Direct segments shared between you and Ivy on a one-to-one comparison.")
    report.append("")
    
    if one_to_one_segs:
        chr_groups = group_segments_by_chromosome(one_to_one_segs)
        
        report.append("### By Chromosome")
        report.append("")
        report.append("| Chromosome | Start | End | cM | SNPs |")
        report.append("|------------|-------|-----|-----|------|")
        
        for chr_num in sorted(chr_groups.keys(), key=safe_sort_chromosome):
            for seg in chr_groups[chr_num]:
                report.append(f"| {seg['chr']} | {seg['start']} | {seg['end']} | {seg['cM']} | {seg.get('snps', 'N/A')} |")
        
        report.append("")
        
        # Calculate totals with safe float conversion
        def safe_float_conv(val):
            try:
                return float(val) if val else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        total_cm = sum(safe_float_conv(seg.get('cM')) for seg in one_to_one_segs)
        report.append(f"**Total Direct Shared DNA:** {total_cm:.1f} cM across {len(one_to_one_segs)} segments")
        report.append("")
    else:
        report.append("*No direct one-to-one segment data found.*")
        report.append("")
        report.append("*Note: Direct segment data with Ivy may be in other data sources not yet processed.*")
        report.append("")
    
    # Section 6: Notes
    report.append("## 6. Additional Notes")
    report.append("")
    if cluster_info.get('notes'):
        report.append(f"**Cluster Notes:** {cluster_info['notes']}")
        report.append("")
    
    report.append("### Understanding the Data")
    report.append("")
    report.append("- **TRI (Triangulated)**: Segments where you, Ivy, and at least one other person all match")
    report.append("- **ICW (In Common With)**: People who match both you and Ivy")
    report.append("- **cM (centiMorgans)**: Unit of genetic distance; higher = more DNA shared")
    report.append("- **SNPs**: Number of Single Nucleotide Polymorphisms (genetic markers) in the segment")
    report.append("")
    
    report.append("---")
    report.append("")
    report.append("*This report is automatically generated from DNA data files in the repository.*")
    report.append(f"*For questions or updates, contact: {IVY_EMAIL}*")
    
    return '\n'.join(report)


def main():
    """Main execution function"""
    print(f"Generating DNA segment report for Ivy Lee ({IVY_KIT})...")
    print()
    
    # Load data
    print("Loading triangulated segments...")
    triangulated_segs = load_triangulated_segments()
    print(f"  Found {len(triangulated_segs)} triangulated segment entries")
    
    print("Loading WATO statistics...")
    wato_stats = load_wato_stats()
    print(f"  Triangulated cM: {wato_stats.get('total_triangulated_cM', 'N/A')}")
    
    print("Loading cluster information...")
    cluster_info = load_cluster_info()
    print(f"  Cluster: {cluster_info.get('cluster', 'N/A')}")
    
    print("Loading one-to-one segments...")
    one_to_one_segs = load_one_to_one_segments()
    print(f"  Found {len(one_to_one_segs)} direct segments")
    
    print("Extracting ICW matches...")
    icw_sources = get_icw_matches(triangulated_segs)
    print(f"  Found {len(icw_sources)} triangulation groups")
    
    print("Loading detailed ICW matches from source files...")
    icw_matches = load_detailed_icw_from_sources()
    print(f"  Found {len(icw_matches)} detailed ICW matches")
    
    print()
    print("Generating markdown report...")
    
    # Generate report
    report_content = generate_markdown_report(
        triangulated_segs,
        wato_stats,
        cluster_info,
        one_to_one_segs,
        icw_sources,
        icw_matches
    )
    
    # Write to file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✓ Report saved to: {OUTPUT_FILE}")
    print()
    print("Report sections included:")
    print("  1. Overview")
    print("  2. Summary Statistics")
    print("  3. Triangulated Segments (TRI)")
    print("  4. In Common With (ICW) Matches")
    print("  5. Direct Shared Segments")
    print("  6. Additional Notes")
    print()
    print("Done!")


if __name__ == '__main__':
    main()
