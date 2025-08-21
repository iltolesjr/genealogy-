# GEDCOM to SQLite Database Converter

This project provides tools to convert GEDCOM genealogy data from CSV format into a SQLite database and query the resulting data.

## Files

- `gedcom_to_sqlite.py` - Main converter script that parses GEDCOM data and creates SQLite database
- `query_genealogy.py` - Interactive query interface for exploring the genealogy database
- `genealogy.db` - SQLite database containing the imported GEDCOM data (created after running converter)

## Database Schema

The SQLite database contains the following tables:

### individuals
- `id` - Individual ID from GEDCOM (e.g., I122674294101)
- `given_name` - First/given name
- `surname` - Last/family name  
- `full_name` - Complete name
- `sex` - M/F/Unknown
- `birth_date` - Birth date
- `birth_place` - Birth location
- `death_date` - Death date
- `death_place` - Death location
- `father_family_id` - ID of family where this person is a child
- `spouse_family_ids` - Comma-separated list of family IDs where this person is a spouse
- `notes` - Additional notes
- `created_at` - Timestamp when record was created

### families
- `id` - Family ID from GEDCOM (e.g., F123)
- `husband_id` - ID of husband/father
- `wife_id` - ID of wife/mother
- `marriage_date` - Marriage date
- `marriage_place` - Marriage location
- `children_ids` - Comma-separated list of children IDs
- `notes` - Additional notes
- `created_at` - Timestamp when record was created

### sources
- `id` - Source ID from GEDCOM (e.g., S123)
- `title` - Source title
- `author` - Source author
- `publication_info` - Publication information
- `repository` - Repository information
- `notes` - Additional notes
- `url` - Web URL if available
- `created_at` - Timestamp when record was created

### events
- `id` - Auto-generated event ID
- `person_id` - ID of person associated with event
- `family_id` - ID of family associated with event
- `event_type` - Type of event (BIRT, DEAT, MARR, etc.)
- `date_value` - Date of event
- `place_value` - Location of event
- `source_id` - ID of source documenting the event
- `notes` - Additional notes
- `created_at` - Timestamp when record was created

### citations
- `id` - Auto-generated citation ID
- `source_id` - ID of source being cited
- `person_id` - ID of person the citation relates to
- `family_id` - ID of family the citation relates to
- `event_id` - ID of event the citation relates to
- `page_info` - Page or section information
- `notes` - Additional notes
- `created_at` - Timestamp when record was created

## Usage

### Convert GEDCOM CSV to SQLite Database

```bash
python3 gedcom_to_sqlite.py "Ira Toles Family Tree.csv" genealogy.db
```

This will:
1. Parse the GEDCOM data from the CSV file
2. Create a SQLite database with the schema described above
3. Import all individuals, families, and sources
4. Display statistics about the imported data

### Query the Database

```bash
python3 query_genealogy.py genealogy.db
```

This opens an interactive query interface with the following commands:

- `search <name>` - Search for individuals by name (searches given name, surname, and full name)
- `surname <surname>` - Search for individuals with a specific surname
- `location <place>` - Search for individuals associated with a location (birth or death place)
- `detail <id>` - Get detailed information about a specific individual including family relationships
- `family <id>` - Get detailed information about a specific family including children
- `stats` - Show database statistics
- `quit` - Exit the interface

### Example Query Session

```
genealogy> stats

Database Statistics:
  Total Individuals: 499
    Males: 247
    Females: 234
    With Birth Dates: 434
    With Death Dates: 271
  Total Families: 204
  Total Sources: 74

genealogy> surname Toles

Found 12 people with surname 'Toles':
--------------------------------------------------
ID: I122674294103
Name: Betty D Toles
Sex: F
Birth: 24 Jul 1957
  Place: Missouri
Death: Unknown
  Place: Unknown location
--------------------------------------------------

genealogy> search Ira

Found 7 matches:
--------------------------------------------------
ID: I122674294101
Name: Ira latrell Toles
Sex: M
Birth: 1986
  Place: East Saint Louis, St Clair, Illinois, USA
Death: Unknown
  Place: Unknown location
--------------------------------------------------

genealogy> detail I122674294101

============================================================
INDIVIDUAL DETAILS: Ira latrell Toles
============================================================
ID: I122674294101
Given Name: Ira latrell
Surname: Toles
Sex: M
Birth: 1986
  Birth Place: East Saint Louis, St Clair, Illinois, USA
Death: Unknown

PARENTS:
  Father: Ira L Toles
  Mother: Gloria J Johnson

genealogy> quit
```

## Data Import Statistics

From the "Ira Toles Family Tree.csv" file:
- **499 individuals** imported successfully
- **204 families** imported successfully  
- **74 sources** imported successfully
- **247 males, 234 females** identified by sex
- **434 individuals** have birth dates
- **271 individuals** have death dates

## Features

- **Comprehensive GEDCOM parsing** - Handles individuals, families, sources, dates, places, and relationships
- **Relational database design** - Proper foreign key relationships between tables
- **Flexible search capabilities** - Search by name, surname, location
- **Family relationship tracking** - Links between parents, children, spouses
- **Source documentation** - Tracks citations and sources for genealogical claims
- **Data validation** - Handles missing data gracefully
- **Interactive interface** - User-friendly command-line query tool

## Technical Details

- **Database**: SQLite (included with Python, no additional installation required)
- **Input format**: CSV file containing GEDCOM data (one line per GEDCOM record)
- **Output**: SQLite database file with normalized relational schema
- **Dependencies**: Only Python standard library modules (sqlite3, csv, re, pathlib)

## Future Enhancements

Potential improvements could include:
- Web-based interface for querying
- Export functionality (back to GEDCOM format)
- Data visualization (family trees, timelines)
- Advanced search with date ranges and location filtering
- Import from other genealogy formats
- Data validation and duplicate detection
- Integration with online genealogy services