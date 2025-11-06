#!/usr/bin/env python3
"""
DNA Segment Visualization Script

Creates an HTML visualization showing DNA segment matches with different colors
for different match groups or chromosomes.
"""

import csv
import random
from collections import defaultdict


def generate_color(index):
    """Generate distinct colors for different matches"""
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
        '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788',
        '#FF6F61', '#6A4C93', '#1982C4', '#8AC926', '#FFCA3A',
        '#C9ADA7', '#4A7C59', '#F25F5C', '#70C1B3', '#247BA0'
    ]
    return colors[index % len(colors)]


def read_segment_data():
    """Read segment data from available CSV files"""
    segments = []
    
    # Try reading from segments_for_plot.csv
    try:
        with open('/home/runner/work/genealogy-/genealogy-/outputs/segments_for_plot.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                segments.append({
                    'name': row.get('Name', ''),
                    'chr': 1,  # Default chromosome
                    'start': int(row.get('Start', 0)),
                    'end': int(row.get('End', 0)),
                    'cm': 0
                })
    except FileNotFoundError:
        pass
    
    # Try reading from gedmatch_segments.csv
    try:
        with open('/home/runner/work/genealogy-/genealogy-/outputs/gedmatch_segments.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    chr_val = row.get('chr', '1')
                    if chr_val and chr_val != 'chr':
                        segments.append({
                            'name': row.get('name1', row.get('kit1', 'Unknown')),
                            'chr': int(chr_val) if chr_val.isdigit() else 1,
                            'start': int(row.get('start', 0)),
                            'end': int(row.get('end', 0)),
                            'cm': float(row.get('cm', 0))
                        })
                except (ValueError, TypeError):
                    continue
    except FileNotFoundError:
        pass
    
    return segments


def create_chromosome_visualization(segments, output_file):
    """Create HTML visualization of DNA segments"""
    
    if not segments:
        print("No segment data found!")
        return
    
    # Group segments by chromosome
    by_chr = defaultdict(list)
    for seg in segments:
        by_chr[seg['chr']].append(seg)
    
    # Calculate statistics
    total_segments = len(segments)
    unique_matches = len(set(seg['name'] for seg in segments))
    chromosomes = len(by_chr)
    avg_cm = sum(seg['cm'] for seg in segments) / len(segments) if segments else 0
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>DNA Segment Visualization</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .chromosome {{
            margin: 30px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chr-label {{
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
            color: #555;
        }}
        .chr-container {{
            position: relative;
            height: 50px;
            background: #e0e0e0;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .segment {{
            position: absolute;
            height: 40px;
            top: 5px;
            border-radius: 3px;
            opacity: 0.8;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .segment:hover {{
            opacity: 1;
            border: 2px solid #333;
        }}
        .segment-info {{
            font-size: 10px;
            color: white;
            padding: 2px 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .legend {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .legend-item {{
            display: inline-block;
            margin: 5px 10px;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-box {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .tooltip {{
            position: fixed;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            display: none;
        }}
    </style>
</head>
<body>
    <h1>🧬 DNA Segment Visualization</h1>
    
    <div class="stats">
        <h2>Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-value">{total_segments}</div>
                <div class="stat-label">Total Segments</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{unique_matches}</div>
                <div class="stat-label">Unique Matches</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{chromosomes}</div>
                <div class="stat-label">Chromosomes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{avg_cm:.1f} cM</div>
                <div class="stat-label">Average Segment Size</div>
            </div>
        </div>
    </div>
"""
    
    # Create legend with top matches
    match_counts = defaultdict(int)
    for seg in segments:
        match_counts[seg['name']] += 1
    top_matches = sorted(match_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    html += '<div class="legend">\n'
    html += '<h3>Top DNA Matches</h3>\n'
    for i, (name, count) in enumerate(top_matches):
        color = generate_color(i)
        html += f'<span class="legend-item" style="background-color: {color};">{name} ({count} segments)</span>\n'
    html += '</div>\n'
    
    # Create chromosome visualizations
    for chr_num in sorted(by_chr.keys()):
        chr_segments = by_chr[chr_num]
        
        # Find max position for scaling
        max_pos = max(seg['end'] for seg in chr_segments)
        min_pos = min(seg['start'] for seg in chr_segments)
        range_pos = max_pos - min_pos
        
        html += f'<div class="chromosome">\n'
        html += f'<div class="chr-label">Chromosome {chr_num} ({len(chr_segments)} segments)</div>\n'
        html += '<div class="chr-container">\n'
        
        # Assign colors to matches
        match_colors = {}
        color_index = 0
        for seg in chr_segments:
            if seg['name'] not in match_colors:
                match_colors[seg['name']] = generate_color(color_index)
                color_index += 1
        
        # Add segments
        for seg in chr_segments:
            left_pct = ((seg['start'] - min_pos) / range_pos * 100) if range_pos > 0 else 0
            width_pct = ((seg['end'] - seg['start']) / range_pos * 100) if range_pos > 0 else 1
            color = match_colors[seg['name']]
            
            tooltip = f"{seg['name']}: {seg['start']:,} - {seg['end']:,}"
            if seg['cm'] > 0:
                tooltip += f" ({seg['cm']} cM)"
            
            html += f'<div class="segment" style="left: {left_pct}%; width: {width_pct}%; background-color: {color};" '
            html += f'title="{tooltip}">\n'
            html += f'<div class="segment-info">{seg["name"]}</div>\n'
            html += '</div>\n'
        
        html += '</div>\n'
        html += '</div>\n'
    
    html += """
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        // Enhanced tooltip
        document.addEventListener('DOMContentLoaded', function() {
            const tooltip = document.getElementById('tooltip');
            const segments = document.querySelectorAll('.segment');
            
            segments.forEach(segment => {
                segment.addEventListener('mouseenter', function(e) {
                    tooltip.textContent = this.title;
                    tooltip.style.display = 'block';
                });
                
                segment.addEventListener('mousemove', function(e) {
                    tooltip.style.left = (e.pageX + 10) + 'px';
                    tooltip.style.top = (e.pageY + 10) + 'px';
                });
                
                segment.addEventListener('mouseleave', function() {
                    tooltip.style.display = 'none';
                });
            });
        });
    </script>
</body>
</html>
"""
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Visualization created: {output_file}")
    print(f"Total segments: {total_segments}")
    print(f"Unique matches: {unique_matches}")
    print(f"Chromosomes covered: {chromosomes}")


def main():
    print("Reading DNA segment data...")
    segments = read_segment_data()
    
    if not segments:
        print("ERROR: No segment data found!")
        print("Looked in:")
        print("  - /home/runner/work/genealogy-/genealogy-/outputs/segments_for_plot.csv")
        print("  - /home/runner/work/genealogy-/genealogy-/outputs/gedmatch_segments.csv")
        return
    
    output_file = '/home/runner/work/genealogy-/genealogy-/visualizations/dna_segments_colored.html'
    create_chromosome_visualization(segments, output_file)


if __name__ == "__main__":
    main()
