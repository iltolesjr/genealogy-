# Genealogy DNA Workflow ERD

This directory contains tools for creating and viewing Entity Relationship Diagrams (ERD) for the genealogy DNA workflow.

## Files

- `genealogy_erd.py` - Python script to generate the ERD
- `genealogy_erd.ipynb` - Jupyter notebook version with explanations
- `genealogy_erd.png` - Generated ERD diagram
- `Research Data/` - Directory containing CSV data files

## Usage

### Using the Python Script

```bash
python3 genealogy_erd.py
```

### Using the Jupyter Notebook

Open `genealogy_erd.ipynb` in Jupyter and run all cells.

## Data Structure

The ERD shows relationships between:

1. **paternal_matches_template.csv** - DNA match data
   - match_id, match_name, shared_cm
   - key_surnames, key_locations 
   - cluster_id, probable_mrca, confidence

2. **lum_sellers_hypothesis.csv** - Hypothesis/ancestor data
   - person_id, name, birth_year, relation
   - citations, notes

3. **citations.csv** - Source citations
   - citation_id, type, title, year, place
   - detail, url, person_id

4. **cluster_id** - Grouping mechanism for related matches

## Relationships

- DNA matches → Hypothesis persons (possible MRCA links)
- Hypothesis persons → Citations (source documentation)
- Clusters → Multiple DNA matches (grouping)

## Requirements

- Python 3.6+
- graphviz (Python package): `pip install graphviz`
- Graphviz system package:
  - Ubuntu/Debian: `sudo apt-get install graphviz`
  - macOS: `brew install graphviz`
  - Windows: Download from https://graphviz.org/download/

## Sample Data

The `Research Data/` directory contains sample CSV files that demonstrate the expected structure. Replace these with your actual genealogy data as your research progresses.