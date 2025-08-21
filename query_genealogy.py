#!/usr/bin/env python3
"""
Genealogy Database Query Interface

This script provides a simple interface to query the genealogy SQLite database
created by the GEDCOM to SQLite converter.
"""

import sqlite3
import sys
from pathlib import Path


class GenealogyDB:
    """Interface for querying the genealogy database."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = Path(db_path)
        self.conn = None
    
    def connect(self):
        """Connect to the database."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        print(f"Connected to database: {self.db_path}")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def search_by_name(self, name_pattern: str):
        """Search individuals by name pattern."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, full_name, sex, birth_date, birth_place, death_date, death_place
            FROM individuals 
            WHERE full_name LIKE ? OR given_name LIKE ? OR surname LIKE ?
            ORDER BY full_name
        ''', (f'%{name_pattern}%', f'%{name_pattern}%', f'%{name_pattern}%'))
        
        return cursor.fetchall()
    
    def get_individual_details(self, person_id: str):
        """Get detailed information about an individual."""
        cursor = self.conn.cursor()
        
        # Get individual info
        cursor.execute('''
            SELECT * FROM individuals WHERE id = ?
        ''', (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return None
        
        # Get family as child
        father_family = None
        if person['father_family_id']:
            cursor.execute('''
                SELECT f.*, 
                       h.full_name as father_name,
                       w.full_name as mother_name
                FROM families f
                LEFT JOIN individuals h ON f.husband_id = h.id
                LEFT JOIN individuals w ON f.wife_id = w.id
                WHERE f.id = ?
            ''', (person['father_family_id'],))
            father_family = cursor.fetchone()
        
        # Get families as spouse
        spouse_families = []
        if person['spouse_family_ids']:
            family_ids = person['spouse_family_ids'].split(',')
            for fam_id in family_ids:
                if fam_id.strip():
                    cursor.execute('''
                        SELECT f.*, 
                               h.full_name as husband_name,
                               w.full_name as wife_name
                        FROM families f
                        LEFT JOIN individuals h ON f.husband_id = h.id
                        LEFT JOIN individuals w ON f.wife_id = w.id
                        WHERE f.id = ?
                    ''', (fam_id.strip(),))
                    fam = cursor.fetchone()
                    if fam:
                        spouse_families.append(fam)
        
        return {
            'person': person,
            'father_family': father_family,
            'spouse_families': spouse_families
        }
    
    def get_family_details(self, family_id: str):
        """Get detailed information about a family."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT f.*, 
                   h.full_name as husband_name,
                   w.full_name as wife_name
            FROM families f
            LEFT JOIN individuals h ON f.husband_id = h.id
            LEFT JOIN individuals w ON f.wife_id = w.id
            WHERE f.id = ?
        ''', (family_id,))
        family = cursor.fetchone()
        
        if not family:
            return None
        
        # Get children
        children = []
        if family['children_ids']:
            child_ids = family['children_ids'].split(',')
            for child_id in child_ids:
                if child_id.strip():
                    cursor.execute('''
                        SELECT id, full_name, sex, birth_date, birth_place
                        FROM individuals WHERE id = ?
                    ''', (child_id.strip(),))
                    child = cursor.fetchone()
                    if child:
                        children.append(child)
        
        return {
            'family': family,
            'children': children
        }
    
    def search_by_location(self, location_pattern: str):
        """Search individuals by birth or death location."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, full_name, sex, birth_date, birth_place, death_date, death_place
            FROM individuals 
            WHERE birth_place LIKE ? OR death_place LIKE ?
            ORDER BY full_name
        ''', (f'%{location_pattern}%', f'%{location_pattern}%'))
        
        return cursor.fetchall()
    
    def search_by_surname(self, surname: str):
        """Search individuals by surname."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, full_name, sex, birth_date, birth_place, death_date, death_place
            FROM individuals 
            WHERE surname LIKE ?
            ORDER BY full_name
        ''', (f'%{surname}%',))
        
        return cursor.fetchall()
    
    def get_statistics(self):
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM individuals")
        stats['total_individuals'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM families")
        stats['total_families'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sources")
        stats['total_sources'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE sex = 'M'")
        stats['males'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE sex = 'F'")
        stats['females'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE birth_date IS NOT NULL")
        stats['with_birth_dates'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE death_date IS NOT NULL")
        stats['with_death_dates'] = cursor.fetchone()[0]
        
        return stats


def print_individual(person):
    """Print individual information."""
    print(f"ID: {person['id']}")
    print(f"Name: {person['full_name']}")
    print(f"Sex: {person['sex'] or 'Unknown'}")
    print(f"Birth: {person['birth_date'] or 'Unknown'}")
    if person['birth_place']:
        print(f"  Place: {person['birth_place']}")
    print(f"Death: {person['death_date'] or 'Unknown'}")
    if person['death_place']:
        print(f"  Place: {person['death_place']}")
    print("-" * 50)


def print_detailed_individual(details):
    """Print detailed individual information including family relationships."""
    person = details['person']
    print(f"\n{'='*60}")
    print(f"INDIVIDUAL DETAILS: {person['full_name']}")
    print(f"{'='*60}")
    print(f"ID: {person['id']}")
    print(f"Given Name: {person['given_name'] or 'Unknown'}")
    print(f"Surname: {person['surname'] or 'Unknown'}")
    print(f"Sex: {person['sex'] or 'Unknown'}")
    print(f"Birth: {person['birth_date'] or 'Unknown'}")
    if person['birth_place']:
        print(f"  Birth Place: {person['birth_place']}")
    print(f"Death: {person['death_date'] or 'Unknown'}")
    if person['death_place']:
        print(f"  Death Place: {person['death_place']}")
    
    # Parents
    if details['father_family']:
        fam = details['father_family']
        print(f"\nPARENTS:")
        print(f"  Father: {fam['father_name'] or 'Unknown'}")
        print(f"  Mother: {fam['mother_name'] or 'Unknown'}")
    
    # Spouses and children
    if details['spouse_families']:
        print(f"\nFAMILIES:")
        for i, fam in enumerate(details['spouse_families'], 1):
            spouse_name = fam['wife_name'] if person['sex'] == 'M' else fam['husband_name']
            print(f"  Family {i}: Spouse - {spouse_name or 'Unknown'}")
            if fam['marriage_date']:
                print(f"    Marriage: {fam['marriage_date']}")
            if fam['marriage_place']:
                print(f"    Marriage Place: {fam['marriage_place']}")


def interactive_mode(db):
    """Run interactive query mode."""
    print("\nGenealogy Database Query Interface")
    print("=" * 40)
    print("Commands:")
    print("  search <name>     - Search by name")
    print("  surname <surname> - Search by surname")
    print("  location <place>  - Search by location")
    print("  detail <id>       - Get individual details")
    print("  family <id>       - Get family details")
    print("  stats             - Show database statistics")
    print("  quit              - Exit")
    print()
    
    while True:
        try:
            command = input("genealogy> ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'q']:
                break
            
            parts = command.split(' ', 1)
            cmd = parts[0].lower()
            
            if cmd == 'search' and len(parts) > 1:
                results = db.search_by_name(parts[1])
                print(f"\nFound {len(results)} matches:")
                print("-" * 50)
                for person in results:
                    print_individual(person)
            
            elif cmd == 'surname' and len(parts) > 1:
                results = db.search_by_surname(parts[1])
                print(f"\nFound {len(results)} people with surname '{parts[1]}':")
                print("-" * 50)
                for person in results:
                    print_individual(person)
            
            elif cmd == 'location' and len(parts) > 1:
                results = db.search_by_location(parts[1])
                print(f"\nFound {len(results)} people associated with '{parts[1]}':")
                print("-" * 50)
                for person in results:
                    print_individual(person)
            
            elif cmd == 'detail' and len(parts) > 1:
                details = db.get_individual_details(parts[1])
                if details:
                    print_detailed_individual(details)
                else:
                    print(f"Individual not found: {parts[1]}")
            
            elif cmd == 'family' and len(parts) > 1:
                family_details = db.get_family_details(parts[1])
                if family_details:
                    fam = family_details['family']
                    children = family_details['children']
                    print(f"\nFamily ID: {fam['id']}")
                    print(f"Husband: {fam['husband_name'] or 'Unknown'}")
                    print(f"Wife: {fam['wife_name'] or 'Unknown'}")
                    if fam['marriage_date']:
                        print(f"Marriage: {fam['marriage_date']}")
                    if fam['marriage_place']:
                        print(f"Marriage Place: {fam['marriage_place']}")
                    if children:
                        print(f"\nChildren ({len(children)}):")
                        for child in children:
                            print(f"  - {child['full_name']} ({child['birth_date'] or 'Unknown birth'})")
                else:
                    print(f"Family not found: {parts[1]}")
            
            elif cmd == 'stats':
                stats = db.get_statistics()
                print(f"\nDatabase Statistics:")
                print(f"  Total Individuals: {stats['total_individuals']}")
                print(f"    Males: {stats['males']}")
                print(f"    Females: {stats['females']}")
                print(f"    With Birth Dates: {stats['with_birth_dates']}")
                print(f"    With Death Dates: {stats['with_death_dates']}")
                print(f"  Total Families: {stats['total_families']}")
                print(f"  Total Sources: {stats['total_sources']}")
            
            else:
                print("Unknown command. Type 'quit' to exit.")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 query_genealogy.py <database_file>")
        print("Example: python3 query_genealogy.py genealogy.db")
        sys.exit(1)
    
    db_file = sys.argv[1]
    db = GenealogyDB(db_file)
    
    try:
        db.connect()
        interactive_mode(db)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()