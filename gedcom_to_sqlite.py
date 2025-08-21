#!/usr/bin/env python3
"""
GEDCOM to SQLite Converter

This script parses a GEDCOM file exported as CSV and converts it to SQLite database.
The CSV format contains GEDCOM structure with line numbers preserved.

Usage: python3 gedcom_to_sqlite.py <input_csv> <output_db>
"""

import sys
import csv
import sqlite3
import re
from typing import Dict, List, Optional, Tuple


class GedcomParser:
    """Parser for GEDCOM data in CSV format"""
    
    def __init__(self):
        self.individuals = {}
        self.families = {}
        self.sources = {}
        
    def parse_gedcom_line(self, line: str) -> Optional[Tuple[int, str, str, str]]:
        """Parse a GEDCOM line into level, tag, xref, and value"""
        # Remove line number prefix (e.g., "24.0 " -> "0 ")
        line = re.sub(r'^\d+\.', '', line).strip()
        
        if not line:
            return None
            
        parts = line.split(' ', 2)
        if len(parts) < 2:
            return None
            
        level = int(parts[0])
        
        # Handle xref case: "0 @ID@ TAG"
        if len(parts) >= 3 and parts[1].startswith('@') and parts[1].endswith('@'):
            xref = parts[1]
            tag = parts[2] if len(parts) > 2 else ''
            value = ''
        else:
            # Handle normal case: "1 TAG value"
            xref = ''
            tag = parts[1]
            value = ' '.join(parts[2:]) if len(parts) > 2 else ''
            
        return level, tag, xref, value
    
    def parse_csv(self, csv_file: str):
        """Parse the GEDCOM CSV file"""
        current_individual = None
        current_family = None
        current_source = None
        context_stack = []  # Track nested contexts
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0]:
                    continue
                    
                parsed = self.parse_gedcom_line(row[0])
                if not parsed:
                    continue
                    
                level, tag, xref, value = parsed
                
                # Manage context stack based on level
                while len(context_stack) > level:
                    context_stack.pop()
                
                if level == 0:
                    # Reset current contexts
                    current_individual = None
                    current_family = None
                    current_source = None
                    
                    if tag == 'INDI':
                        current_individual = {
                            'id': xref,
                            'names': [],
                            'sex': '',
                            'birth_date': '',
                            'birth_place': '',
                            'death_date': '',
                            'death_place': '',
                            'father_id': '',
                            'mother_id': '',
                            'families_spouse': [],
                            'families_child': []
                        }
                        self.individuals[xref] = current_individual
                        context_stack.append(('INDI', current_individual))
                        
                    elif tag == 'FAM':
                        current_family = {
                            'id': xref,
                            'husband_id': '',
                            'wife_id': '',
                            'children': [],
                            'marriage_date': '',
                            'marriage_place': ''
                        }
                        self.families[xref] = current_family
                        context_stack.append(('FAM', current_family))
                        
                    elif tag == 'SOUR':
                        current_source = {
                            'id': xref,
                            'title': '',
                            'author': '',
                            'publication': ''
                        }
                        self.sources[xref] = current_source
                        context_stack.append(('SOUR', current_source))
                        
                elif level == 1:
                    context_stack.append((tag, value))
                    
                    if current_individual:
                        if tag == 'NAME':
                            current_individual['names'].append(value)
                        elif tag == 'SEX':
                            current_individual['sex'] = value
                        elif tag == 'FAMC':
                            current_individual['families_child'].append(value)
                        elif tag == 'FAMS':
                            current_individual['families_spouse'].append(value)
                        elif tag == 'BIRT':
                            context_stack.append(('BIRT', None))
                        elif tag == 'DEAT':
                            context_stack.append(('DEAT', None))
                            
                    elif current_family:
                        if tag == 'HUSB':
                            current_family['husband_id'] = value
                        elif tag == 'WIFE':
                            current_family['wife_id'] = value
                        elif tag == 'CHIL':
                            current_family['children'].append(value)
                        elif tag == 'MARR':
                            context_stack.append(('MARR', None))
                            
                    elif current_source:
                        if tag == 'TITL':
                            current_source['title'] = value
                        elif tag == 'AUTH':
                            current_source['author'] = value
                        elif tag == 'PUBL':
                            current_source['publication'] = value
                            
                elif level == 2:
                    if len(context_stack) >= 2:
                        parent_context = context_stack[-1][0]
                        
                        if current_individual:
                            if parent_context == 'BIRT':
                                if tag == 'DATE':
                                    current_individual['birth_date'] = value
                                elif tag == 'PLAC':
                                    current_individual['birth_place'] = value
                            elif parent_context == 'DEAT':
                                if tag == 'DATE':
                                    current_individual['death_date'] = value
                                elif tag == 'PLAC':
                                    current_individual['death_place'] = value
                                    
                        elif current_family and parent_context == 'MARR':
                            if tag == 'DATE':
                                current_family['marriage_date'] = value
                            elif tag == 'PLAC':
                                current_family['marriage_place'] = value


def create_database(db_file: str) -> sqlite3.Connection:
    """Create SQLite database with genealogy schema"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create individuals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS individuals (
            id TEXT PRIMARY KEY,
            name TEXT,
            given_name TEXT,
            surname TEXT,
            sex TEXT,
            birth_date TEXT,
            birth_place TEXT,
            death_date TEXT,
            death_place TEXT,
            father_id TEXT,
            mother_id TEXT
        )
    ''')
    
    # Create families table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS families (
            id TEXT PRIMARY KEY,
            husband_id TEXT,
            wife_id TEXT,
            marriage_date TEXT,
            marriage_place TEXT,
            FOREIGN KEY (husband_id) REFERENCES individuals (id),
            FOREIGN KEY (wife_id) REFERENCES individuals (id)
        )
    ''')
    
    # Create family_children table for many-to-many relationship
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS family_children (
            family_id TEXT,
            child_id TEXT,
            PRIMARY KEY (family_id, child_id),
            FOREIGN KEY (family_id) REFERENCES families (id),
            FOREIGN KEY (child_id) REFERENCES individuals (id)
        )
    ''')
    
    # Create sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            publication TEXT
        )
    ''')
    
    conn.commit()
    return conn


def insert_data(conn: sqlite3.Connection, parser: GedcomParser):
    """Insert parsed GEDCOM data into SQLite database"""
    cursor = conn.cursor()
    
    # Insert individuals
    for individual in parser.individuals.values():
        # Extract given name and surname from first name
        name = individual['names'][0] if individual['names'] else ''
        given_name = ''
        surname = ''
        
        if name:
            # GEDCOM format: "Given /Surname/"
            name_match = re.match(r'([^/]*)\s*/([^/]*)/.*', name)
            if name_match:
                given_name = name_match.group(1).strip()
                surname = name_match.group(2).strip()
            else:
                given_name = name.strip()
        
        # Determine father and mother from family relationships
        father_id = ''
        mother_id = ''
        for family_id in individual['families_child']:
            if family_id in parser.families:
                family = parser.families[family_id]
                if family['husband_id']:
                    father_id = family['husband_id']
                if family['wife_id']:
                    mother_id = family['wife_id']
                break
        
        cursor.execute('''
            INSERT OR REPLACE INTO individuals 
            (id, name, given_name, surname, sex, birth_date, birth_place, 
             death_date, death_place, father_id, mother_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            individual['id'], name, given_name, surname, individual['sex'],
            individual['birth_date'], individual['birth_place'],
            individual['death_date'], individual['death_place'],
            father_id, mother_id
        ))
    
    # Insert families
    for family in parser.families.values():
        cursor.execute('''
            INSERT OR REPLACE INTO families 
            (id, husband_id, wife_id, marriage_date, marriage_place)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            family['id'], family['husband_id'], family['wife_id'],
            family['marriage_date'], family['marriage_place']
        ))
        
        # Insert family-children relationships
        for child_id in family['children']:
            cursor.execute('''
                INSERT OR REPLACE INTO family_children (family_id, child_id)
                VALUES (?, ?)
            ''', (family['id'], child_id))
    
    # Insert sources
    for source in parser.sources.values():
        cursor.execute('''
            INSERT OR REPLACE INTO sources (id, title, author, publication)
            VALUES (?, ?, ?, ?)
        ''', (
            source['id'], source['title'], source['author'], source['publication']
        ))
    
    conn.commit()


def main():
    """Main function"""
    if len(sys.argv) != 3:
        print("Usage: python3 gedcom_to_sqlite.py <input_csv> <output_db>")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_db = sys.argv[2]
    
    try:
        # Parse GEDCOM CSV
        print(f"Parsing GEDCOM CSV file: {input_csv}")
        parser = GedcomParser()
        parser.parse_csv(input_csv)
        
        print(f"Found {len(parser.individuals)} individuals")
        print(f"Found {len(parser.families)} families")
        print(f"Found {len(parser.sources)} sources")
        
        # Create database
        print(f"Creating SQLite database: {output_db}")
        conn = create_database(output_db)
        
        # Insert data
        print("Inserting data into database...")
        insert_data(conn, parser)
        
        # Close connection
        conn.close()
        
        print(f"Successfully converted {input_csv} to {output_db}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()