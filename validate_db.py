#!/usr/bin/env python3
"""
Database Validation Script

This script validates the integrity of the genealogy SQLite database
and reports any data quality issues.
"""

import sqlite3
from pathlib import Path


def validate_database(db_path: str):
    """Validate the genealogy database and report issues."""
    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Validating database: {db_path}")
    print("=" * 50)
    
    # Basic counts
    cursor.execute("SELECT COUNT(*) FROM individuals")
    individuals_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM families")
    families_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sources")
    sources_count = cursor.fetchone()[0]
    
    print(f"Records found:")
    print(f"  Individuals: {individuals_count}")
    print(f"  Families: {families_count}")
    print(f"  Sources: {sources_count}")
    print()
    
    # Check for missing names
    cursor.execute("SELECT COUNT(*) FROM individuals WHERE full_name IS NULL OR full_name = ''")
    missing_names = cursor.fetchone()[0]
    if missing_names > 0:
        print(f"⚠️  Warning: {missing_names} individuals have missing names")
    else:
        print("✅ All individuals have names")
    
    # Check for orphaned family references
    cursor.execute('''
        SELECT COUNT(*) FROM individuals 
        WHERE father_family_id IS NOT NULL 
        AND father_family_id NOT IN (SELECT id FROM families)
    ''')
    orphaned_family_refs = cursor.fetchone()[0]
    if orphaned_family_refs > 0:
        print(f"⚠️  Warning: {orphaned_family_refs} individuals reference non-existent families")
    else:
        print("✅ All family references are valid")
    
    # Check for invalid sex values
    cursor.execute("SELECT COUNT(*) FROM individuals WHERE sex NOT IN ('M', 'F', '', NULL)")
    invalid_sex = cursor.fetchone()[0]
    if invalid_sex > 0:
        print(f"⚠️  Warning: {invalid_sex} individuals have invalid sex values")
    else:
        print("✅ All sex values are valid")
    
    # Check for families without parents
    cursor.execute("SELECT COUNT(*) FROM families WHERE husband_id IS NULL AND wife_id IS NULL")
    families_no_parents = cursor.fetchone()[0]
    if families_no_parents > 0:
        print(f"⚠️  Warning: {families_no_parents} families have no parents")
    else:
        print("✅ All families have at least one parent")
    
    # Data completeness statistics
    print("\nData Completeness:")
    
    cursor.execute("SELECT COUNT(*) FROM individuals WHERE birth_date IS NOT NULL AND birth_date != ''")
    with_birth_dates = cursor.fetchone()[0]
    print(f"  Birth dates: {with_birth_dates}/{individuals_count} ({100*with_birth_dates/individuals_count:.1f}%)")
    
    cursor.execute("SELECT COUNT(*) FROM individuals WHERE birth_place IS NOT NULL AND birth_place != ''")
    with_birth_places = cursor.fetchone()[0]
    print(f"  Birth places: {with_birth_places}/{individuals_count} ({100*with_birth_places/individuals_count:.1f}%)")
    
    cursor.execute("SELECT COUNT(*) FROM individuals WHERE death_date IS NOT NULL AND death_date != ''")
    with_death_dates = cursor.fetchone()[0]
    print(f"  Death dates: {with_death_dates}/{individuals_count} ({100*with_death_dates/individuals_count:.1f}%)")
    
    cursor.execute("SELECT COUNT(*) FROM individuals WHERE death_place IS NOT NULL AND death_place != ''")
    with_death_places = cursor.fetchone()[0]
    print(f"  Death places: {with_death_places}/{individuals_count} ({100*with_death_places/individuals_count:.1f}%)")
    
    # Most common surnames
    print("\nMost Common Surnames:")
    cursor.execute('''
        SELECT surname, COUNT(*) as count 
        FROM individuals 
        WHERE surname IS NOT NULL AND surname != ''
        GROUP BY surname 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    
    surnames = cursor.fetchall()
    for surname, count in surnames:
        print(f"  {surname}: {count}")
    
    # Most common birth places
    print("\nMost Common Birth Places:")
    cursor.execute('''
        SELECT birth_place, COUNT(*) as count 
        FROM individuals 
        WHERE birth_place IS NOT NULL AND birth_place != ''
        GROUP BY birth_place 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    
    places = cursor.fetchall()
    for place, count in places:
        print(f"  {place}: {count}")
    
    conn.close()
    print("\nValidation complete! ✅")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 validate_db.py <database_file>")
        print("Example: python3 validate_db.py genealogy.db")
        sys.exit(1)
    
    validate_database(sys.argv[1])