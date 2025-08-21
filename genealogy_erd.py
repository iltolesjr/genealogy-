#!/usr/bin/env python3
"""
ERD for genealogy DNA workflow using graphviz

This script creates an Entity Relationship Diagram (ERD) showing the relationships
between DNA matches, hypothesis data, and citations in the genealogy workflow.
"""

import sys
import os
from pathlib import Path

try:
    import graphviz
except ImportError:
    print("Installing graphviz...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'graphviz'])
    import graphviz


def create_genealogy_erd(output_dir=".", view_diagram=False):
    """
    Create the genealogy DNA workflow ERD using graphviz.
    
    Args:
        output_dir (str): Directory to save the ERD files
        view_diagram (bool): Whether to automatically view the diagram after creation
    
    Returns:
        str: Path to the generated PNG file
    """
    
    # Create graphviz diagram
    dot = graphviz.Digraph(comment="Genealogy DNA Workflow ERD", format='png')
    
    # Set graph attributes for better layout
    dot.attr(rankdir='TB', size='12,8')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
    dot.attr('edge', color='darkblue', fontsize='10')
    
    # Entities - Define the main data structures
    dot.node('M', 'paternal_matches_template.csv\n(match_id, match_name, shared_cm, key_surnames, key_locations, cluster_id, ...)', 
             fillcolor='lightgreen')
    dot.node('H', 'lum_sellers_hypothesis.csv\n(person_id, name, birth_year, relation, citations, ...)', 
             fillcolor='lightyellow')
    dot.node('C', 'citations.csv\n(citation_id, type, title, year, place, detail, url, ...)', 
             fillcolor='lightcoral')
    
    # Relationships - Define how entities connect
    dot.edge('M', 'H', label='possible MRCA link\n(match → hypothesis person)', color='green')
    dot.edge('H', 'C', label='source\n(hypothesis node → citation)', color='red')
    
    # Optional: show clusters as a separate entity if needed
    dot.node('CL', 'cluster_id\n(manual or auto-assigned)', fillcolor='lightgray')
    dot.edge('CL', 'M', label='has many matches', color='gray')
    
    # Output path
    output_path = Path(output_dir) / 'genealogy_erd'
    
    # Render and save
    try:
        dot.render(str(output_path), view=view_diagram)
        png_path = f"{output_path}.png"
        print(f"ERD successfully created: {png_path}")
        return png_path
    except Exception as e:
        print(f"Error creating ERD: {e}")
        print("Note: You may need to install Graphviz system package:")
        print("  - Ubuntu/Debian: sudo apt-get install graphviz")
        print("  - macOS: brew install graphviz")
        print("  - Windows: Download from https://graphviz.org/download/")
        return None


def check_csv_files():
    """
    Check if the CSV files referenced in the ERD exist and provide guidance if they don't.
    """
    csv_files = {
        'paternal_matches_template.csv': 'Research Data/paternal_matches_template.csv',
        'lum_sellers_hypothesis.csv': 'Research Data/hypotheses/lum_sellers_hypothesis.csv',
        'citations.csv': 'Research Data/hypotheses/citations.csv'
    }
    
    print("Checking for referenced CSV files:")
    all_exist = True
    
    for name, path in csv_files.items():
        if Path(path).exists():
            print(f"  ✓ {name} found at {path}")
        else:
            print(f"  ✗ {name} missing at {path}")
            all_exist = False
    
    if not all_exist:
        print("\nNote: Some CSV files are missing. The ERD shows the intended structure.")
        print("Create these files as your genealogy research progresses.")
    
    return all_exist


def main():
    """Main function to create the ERD and check files."""
    print("Creating Genealogy DNA Workflow ERD...")
    
    # Check if CSV files exist
    check_csv_files()
    
    # Create the ERD
    png_path = create_genealogy_erd(view_diagram=False)
    
    if png_path and Path(png_path).exists():
        print(f"\nERD diagram saved to: {png_path}")
        print("You can view the diagram by opening the PNG file.")
    else:
        print("\nERD creation failed. Check error messages above.")


if __name__ == "__main__":
    main()