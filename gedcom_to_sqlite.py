#!/usr/bin/env python3
"""
GEDCOM to SQLite Converter

This script parses GEDCOM data from a CSV file and stores it in a SQLite database.
It handles individuals, families, sources, and their relationships.
"""

import sqlite3
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GedcomParser:
    """Parser for GEDCOM data stored in CSV format."""
    
    def __init__(self, db_path: str):
        """Initialize the parser with database path."""
        self.db_path = Path(db_path)
        self.conn = None
        self.current_record = None
        self.current_id = None
        self.current_type = None
        
    def create_schema(self):
        """Create the database schema for genealogical data."""
        cursor = self.conn.cursor()
        
        # Individuals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS individuals (
                id TEXT PRIMARY KEY,
                given_name TEXT,
                surname TEXT,
                full_name TEXT,
                sex TEXT,
                birth_date TEXT,
                birth_place TEXT,
                death_date TEXT,
                death_place TEXT,
                father_family_id TEXT,
                spouse_family_ids TEXT,  -- Comma-separated list
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Families table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS families (
                id TEXT PRIMARY KEY,
                husband_id TEXT,
                wife_id TEXT,
                marriage_date TEXT,
                marriage_place TEXT,
                children_ids TEXT,  -- Comma-separated list
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (husband_id) REFERENCES individuals (id),
                FOREIGN KEY (wife_id) REFERENCES individuals (id)
            )
        ''')
        
        # Sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                title TEXT,
                author TEXT,
                publication_info TEXT,
                repository TEXT,
                notes TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Events table (births, deaths, marriages, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT,
                family_id TEXT,
                event_type TEXT,  -- BIRT, DEAT, MARR, etc.
                date_value TEXT,
                place_value TEXT,
                source_id TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES individuals (id),
                FOREIGN KEY (family_id) REFERENCES families (id),
                FOREIGN KEY (source_id) REFERENCES sources (id)
            )
        ''')
        
        # Citations table (links between records and sources)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                person_id TEXT,
                family_id TEXT,
                event_id INTEGER,
                page_info TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources (id),
                FOREIGN KEY (person_id) REFERENCES individuals (id),
                FOREIGN KEY (family_id) REFERENCES families (id),
                FOREIGN KEY (event_id) REFERENCES events (id)
            )
        ''')
        
        self.conn.commit()
        print("Database schema created successfully.")
    
    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        print(f"Connected to database: {self.db_path}")
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def parse_gedcom_line(self, line: str) -> Tuple[int, str, str]:
        """Parse a GEDCOM line into level, tag, and value."""
        if not line.strip():
            return None, None, None
            
        parts = line.strip().split(' ', 2)
        level = int(parts[0])
        tag = parts[1] if len(parts) > 1 else ''
        value = parts[2] if len(parts) > 2 else ''
        
        return level, tag, value
    
    def extract_id_from_tag(self, tag: str) -> str:
        """Extract ID from GEDCOM tag like @I123@ or @F456@."""
        match = re.match(r'@([^@]+)@', tag)
        return match.group(1) if match else tag
    
    def parse_name(self, name_value: str) -> Tuple[str, str, str]:
        """Parse GEDCOM name value into given name, surname, and full name."""
        # Handle format like "John /Smith/" or "John Smith"
        match = re.match(r'([^/]*)/([^/]*)/?(.*)', name_value)
        if match:
            given = match.group(1).strip()
            surname = match.group(2).strip()
            full_name = f"{given} {surname}".strip()
        else:
            # No surname markers, treat as full name
            given = name_value.strip()
            surname = ""
            full_name = given
        
        return given, surname, full_name
    
    def insert_individual(self, individual_data: Dict):
        """Insert an individual record into the database."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO individuals 
            (id, given_name, surname, full_name, sex, birth_date, birth_place, 
             death_date, death_place, father_family_id, spouse_family_ids, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            individual_data.get('id'),
            individual_data.get('given_name'),
            individual_data.get('surname'),
            individual_data.get('full_name'),
            individual_data.get('sex'),
            individual_data.get('birth_date'),
            individual_data.get('birth_place'),
            individual_data.get('death_date'),
            individual_data.get('death_place'),
            individual_data.get('father_family_id'),
            ','.join(individual_data.get('spouse_family_ids', [])),
            individual_data.get('notes')
        ))
    
    def insert_family(self, family_data: Dict):
        """Insert a family record into the database."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO families 
            (id, husband_id, wife_id, marriage_date, marriage_place, children_ids, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            family_data.get('id'),
            family_data.get('husband_id'),
            family_data.get('wife_id'),
            family_data.get('marriage_date'),
            family_data.get('marriage_place'),
            ','.join(family_data.get('children_ids', [])),
            family_data.get('notes')
        ))
    
    def insert_source(self, source_data: Dict):
        """Insert a source record into the database."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sources 
            (id, title, author, publication_info, repository, notes, url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            source_data.get('id'),
            source_data.get('title'),
            source_data.get('author'),
            source_data.get('publication_info'),
            source_data.get('repository'),
            source_data.get('notes'),
            source_data.get('url')
        ))
    
    def parse_gedcom_csv(self, csv_path: str):
        """Parse GEDCOM data from CSV file and populate database."""
        print(f"Parsing GEDCOM data from: {csv_path}")
        
        individuals = {}
        families = {}
        sources = {}
        current_record = None
        current_id = None
        current_type = None
        current_event = None
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            for row_num, row in enumerate(reader, 1):
                if not row or not row[0].strip():
                    continue
                
                line = row[0].strip()
                level, tag, value = self.parse_gedcom_line(line)
                
                if level is None:
                    continue
                
                try:
                    if level == 0:
                        # Save previous record
                        if current_record and current_id and current_type:
                            if current_type == 'INDI':
                                individuals[current_id] = current_record
                            elif current_type == 'FAM':
                                families[current_id] = current_record
                            elif current_type == 'SOUR':
                                sources[current_id] = current_record
                        
                        # Start new record
                        if tag.startswith('@') and tag.endswith('@'):
                            current_id = self.extract_id_from_tag(tag)
                            current_type = value
                            current_record = {'id': current_id, 'type': current_type}
                            current_event = None
                        else:
                            current_record = None
                            current_id = None
                            current_type = None
                    
                    elif level == 1 and current_record:
                        if tag == 'NAME':
                            given, surname, full_name = self.parse_name(value)
                            current_record['given_name'] = given
                            current_record['surname'] = surname
                            current_record['full_name'] = full_name
                        elif tag == 'SEX':
                            current_record['sex'] = value
                        elif tag == 'BIRT':
                            current_event = 'birth'
                        elif tag == 'DEAT':
                            current_event = 'death'
                        elif tag == 'MARR':
                            current_event = 'marriage'
                        elif tag == 'FAMC':
                            current_record['father_family_id'] = self.extract_id_from_tag(value)
                        elif tag == 'FAMS':
                            if 'spouse_family_ids' not in current_record:
                                current_record['spouse_family_ids'] = []
                            current_record['spouse_family_ids'].append(self.extract_id_from_tag(value))
                        elif tag == 'HUSB':
                            current_record['husband_id'] = self.extract_id_from_tag(value)
                        elif tag == 'WIFE':
                            current_record['wife_id'] = self.extract_id_from_tag(value)
                        elif tag == 'CHIL':
                            if 'children_ids' not in current_record:
                                current_record['children_ids'] = []
                            current_record['children_ids'].append(self.extract_id_from_tag(value))
                        elif tag == 'TITL':
                            current_record['title'] = value
                        elif tag == 'AUTH':
                            current_record['author'] = value
                        elif tag == 'PUBL':
                            current_record['publication_info'] = value
                        elif tag == 'REPO':
                            current_record['repository'] = value
                        elif tag == 'NOTE':
                            current_record['notes'] = value
                    
                    elif level == 2 and current_record and current_event:
                        if tag == 'DATE':
                            current_record[f'{current_event}_date'] = value
                        elif tag == 'PLAC':
                            current_record[f'{current_event}_place'] = value
                
                except Exception as e:
                    print(f"Error processing line {row_num}: {line}")
                    print(f"Error: {e}")
                    continue
        
        # Save last record
        if current_record and current_id and current_type:
            if current_type == 'INDI':
                individuals[current_id] = current_record
            elif current_type == 'FAM':
                families[current_id] = current_record
            elif current_type == 'SOUR':
                sources[current_id] = current_record
        
        # Insert data into database
        print(f"Inserting {len(individuals)} individuals...")
        for individual in individuals.values():
            self.insert_individual(individual)
        
        print(f"Inserting {len(families)} families...")
        for family in families.values():
            self.insert_family(family)
        
        print(f"Inserting {len(sources)} sources...")
        for source in sources.values():
            self.insert_source(source)
        
        self.conn.commit()
        print(f"Successfully imported {len(individuals)} individuals, {len(families)} families, and {len(sources)} sources.")
    
    def query_individuals(self, limit: int = 10):
        """Query and display sample individuals."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, full_name, sex, birth_date, birth_place, death_date, death_place
            FROM individuals 
            ORDER BY full_name
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        print(f"\nSample individuals ({len(results)} shown):")
        print("-" * 80)
        for row in results:
            print(f"ID: {row[0]}")
            print(f"Name: {row[1]}")
            print(f"Sex: {row[2] or 'Unknown'}")
            print(f"Birth: {row[3] or 'Unknown'} in {row[4] or 'Unknown location'}")
            print(f"Death: {row[5] or 'Unknown'} in {row[6] or 'Unknown location'}")
            print("-" * 40)
    
    def get_statistics(self):
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM individuals")
        individuals_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM families")
        families_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sources")
        sources_count = cursor.fetchone()[0]
        
        print(f"\nDatabase Statistics:")
        print(f"Individuals: {individuals_count}")
        print(f"Families: {families_count}")
        print(f"Sources: {sources_count}")


def main():
    """Main function to run the GEDCOM to SQLite conversion."""
    if len(sys.argv) < 2:
        print("Usage: python3 gedcom_to_sqlite.py <csv_file> [db_file]")
        print("Example: python3 gedcom_to_sqlite.py 'Ira Toles Family Tree.csv' genealogy.db")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    db_file = sys.argv[2] if len(sys.argv) > 2 else "genealogy.db"
    
    if not Path(csv_file).exists():
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)
    
    parser = GedcomParser(db_file)
    
    try:
        parser.connect()
        parser.create_schema()
        parser.parse_gedcom_csv(csv_file)
        parser.get_statistics()
        parser.query_individuals(5)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        parser.close()
    
    print(f"\nGEDCOM data successfully imported to: {db_file}")


if __name__ == "__main__":
    main()