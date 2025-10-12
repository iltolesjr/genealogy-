# Genealogy Search Guide

Quick reference for searching the Ira Toles family tree records.

## How to Search This Repository

### By Name
To search for a specific person by name:
```bash
grep -i "name" ancestor.md
grep -i "NAME.*surname" *.ged
grep -i "name" "Ira Toles Family Tree.csv"
```

### By Surname
To find all individuals with a specific surname:
```bash
grep -i "SURN surname" *.ged
grep -i "surname" ancestor.md
```

### By Location
To find ancestors associated with a location:
```bash
grep -i "location" ancestor.md
grep -i "PLAC.*location" *.ged
```

### By Date/Year
To find records from a specific time period:
```bash
grep "year" ancestor.md
grep -E "DATE.*year" *.ged
```

## Common Searches

### Green/Greene Family Members
All documented Green/Greene family members can be found in:
- `ancestor.md` (lines 128-241)
- GEDCOM file with `SURN Green` or `SURN Greene`

**Key Green Ancestors:**
- Annie Lavinia Green (2nd great-grandmother, 1884-1944)
- Sandy R Greene (3rd great-grandfather, 1860-1943)  
- William Green (5th great-grandfather, 1807-1862)

### Lula Family Members
Currently documented individuals named Lula:
- Lula Johnson (b. Abt 1879, Arkansas)
- Lula Howard
- Lula Halbert
- Lula mae Carter (b. 1908)

**Note:** There is no "Lula Green" or "Lulu Green" in the tree. See [LULA_GREEN_RESEARCH.md](LULA_GREEN_RESEARCH.md)

### DNA Matches
Search DNA match files by:
- Shared cM amount
- Surname patterns
- Geographic locations

Files:
- `dna_matches_cleaned.md`
- `maternal_matches.md`
- `paternal matches.ipynb`

## Research Tips

### Finding Connections
1. Start with the person you know
2. Check ancestor.md for generation level
3. Cross-reference with GEDCOM file for detailed records
4. Use DNA matches to validate connections
5. Check research notebooks for analysis

### Verifying Information
Always cross-reference findings across:
- ✅ ancestor.md (quick reference)
- ✅ GEDCOM file (detailed records)
- ✅ CSV exports (searchable data)
- ✅ Census and historical documents (in PDF files)
- ✅ DNA matches (genetic validation)

### Adding New Information
When documenting new research:
1. Create a research findings document (like LULA_GREEN_RESEARCH.md)
2. Update relevant ancestor files
3. Add to GEDCOM if confirmed
4. Document sources and methodology

## File Formats

### GEDCOM (.ged)
Standard genealogy format with structured data:
- INDI records (individuals)
- FAM records (families)
- SOUR records (sources)

### Markdown (.md)
Human-readable documentation:
- ancestor.md - Complete ancestor list
- Research findings - Documented questions/answers
- DNA matches - Match information tables

### Jupyter Notebooks (.ipynb)
Python-based analysis tools:
- Data parsing
- Pattern matching
- Hypothesis testing
- Geographic analysis

### CSV Files
Spreadsheet-compatible data:
- Complete tree exports
- Match lists
- Location data

## Common Questions

### Q: How do I know if someone is in my tree?
Search all files using the methods above. If found, they will appear in at least one of the core files.

### Q: What if I find conflicting information?
Check the GEDCOM file first (most detailed), then cross-reference with:
- Historical documents (PDFs)
- DNA matches
- Census records

### Q: How do I add someone to the tree?
1. Gather source documents
2. Update GEDCOM file
3. Export new CSV if needed
4. Update ancestor.md
5. Document in research files

---

*For specific research questions, create a new research findings document similar to LULA_GREEN_RESEARCH.md*
