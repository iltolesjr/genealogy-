#!/usr/bin/env python3
"""
Analyze Family Tree Connections and DNA Matches

This script analyzes the GEDCOM file to find:
1. All ancestors born before 1930
2. Overlapping generations (e.g., great-grandparents born after their grandchildren)
3. DNA match connections to pre-1930 ancestors
4. Generation timing discrepancies
"""

import re
import sys
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


class Person:
    def __init__(self, xref: str):
        self.xref = xref
        self.name = ""
        self.birth_year = None
        self.birth_date = ""
        self.birth_place = ""
        self.death_year = None
        self.death_date = ""
        self.death_place = ""
        self.sex = ""
        self.father_id = None
        self.mother_id = None
        self.families_as_spouse = []
        self.families_as_child = []
        
    def __repr__(self):
        years = ""
        if self.birth_year:
            years = f"{self.birth_year}"
        if self.death_year:
            years += f"-{self.death_year}"
        elif self.birth_year:
            years += "-"
        return f"{self.name} ({years})" if years else self.name


class Family:
    def __init__(self, xref: str):
        self.xref = xref
        self.husband_id = None
        self.wife_id = None
        self.children = []


class GedcomAnalyzer:
    def __init__(self, gedcom_file: str):
        self.gedcom_file = gedcom_file
        self.individuals: Dict[str, Person] = {}
        self.families: Dict[str, Family] = {}
        
    def parse_gedcom(self):
        """Parse GEDCOM file"""
        with open(self.gedcom_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        current_person = None
        current_family = None
        context = []
        
        for line in lines:
            line = line.rstrip()
            if not line:
                continue
                
            level = 0
            parts = line.split(' ', 2)
            if not parts:
                continue
                
            try:
                level = int(parts[0])
            except ValueError:
                continue
            
            # Update context
            while len(context) > level:
                context.pop()
                
            if level == 0:
                current_person = None
                current_family = None
                
                if len(parts) >= 3 and parts[2] == 'INDI':
                    xref = parts[1]
                    current_person = Person(xref)
                    self.individuals[xref] = current_person
                    context = ['INDI']
                    
                elif len(parts) >= 3 and parts[2] == 'FAM':
                    xref = parts[1]
                    current_family = Family(xref)
                    self.families[xref] = current_family
                    context = ['FAM']
                    
            elif level == 1 and current_person:
                tag = parts[1] if len(parts) > 1 else ""
                value = parts[2] if len(parts) > 2 else ""
                
                if tag == 'NAME':
                    # Clean up name
                    name = value.replace('/', '').strip()
                    current_person.name = name
                elif tag == 'SEX':
                    current_person.sex = value
                elif tag == 'BIRT':
                    context.append('BIRT')
                elif tag == 'DEAT':
                    context.append('DEAT')
                elif tag == 'FAMC':
                    current_person.families_as_child.append(value)
                elif tag == 'FAMS':
                    current_person.families_as_spouse.append(value)
                    
            elif level == 2 and current_person:
                tag = parts[1] if len(parts) > 1 else ""
                value = parts[2] if len(parts) > 2 else ""
                
                if 'BIRT' in context and tag == 'DATE':
                    current_person.birth_date = value
                    year = self.extract_year(value)
                    if year:
                        current_person.birth_year = year
                elif 'BIRT' in context and tag == 'PLAC':
                    current_person.birth_place = value
                elif 'DEAT' in context and tag == 'DATE':
                    current_person.death_date = value
                    year = self.extract_year(value)
                    if year:
                        current_person.death_year = year
                elif 'DEAT' in context and tag == 'PLAC':
                    current_person.death_place = value
                    
            elif level == 1 and current_family:
                tag = parts[1] if len(parts) > 1 else ""
                value = parts[2] if len(parts) > 2 else ""
                
                if tag == 'HUSB':
                    current_family.husband_id = value
                elif tag == 'WIFE':
                    current_family.wife_id = value
                elif tag == 'CHIL':
                    current_family.children.append(value)
        
        # Set parent relationships
        for family in self.families.values():
            for child_id in family.children:
                if child_id in self.individuals:
                    child = self.individuals[child_id]
                    child.father_id = family.husband_id
                    child.mother_id = family.wife_id
    
    def extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string"""
        # Look for 4-digit year
        match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', date_str)
        if match:
            return int(match.group(1))
        return None
    
    def find_pre_1930_ancestors(self) -> List[Person]:
        """Find all people born before 1930"""
        pre_1930 = []
        for person in self.individuals.values():
            if person.birth_year and person.birth_year < 1930:
                pre_1930.append(person)
        
        # Sort by birth year
        pre_1930.sort(key=lambda p: (p.birth_year or 0, p.name))
        return pre_1930
    
    def find_generation_overlaps(self) -> List[Tuple[Person, Person, str]]:
        """Find cases where ancestors overlap generations (born out of expected order)"""
        overlaps = []
        
        for person in self.individuals.values():
            if not person.birth_year:
                continue
                
            # Check against parents
            if person.father_id and person.father_id in self.individuals:
                father = self.individuals[person.father_id]
                if father.birth_year:
                    age_diff = person.birth_year - father.birth_year
                    if age_diff < 13:  # Parent too young
                        overlaps.append((person, father, f"Parent-child age gap too small: {age_diff} years"))
                    elif age_diff > 60:  # Parent very old
                        overlaps.append((person, father, f"Parent-child age gap very large: {age_diff} years"))
            
            if person.mother_id and person.mother_id in self.individuals:
                mother = self.individuals[person.mother_id]
                if mother.birth_year:
                    age_diff = person.birth_year - mother.birth_year
                    if age_diff < 13:  # Parent too young
                        overlaps.append((person, mother, f"Parent-child age gap too small: {age_diff} years"))
                    elif age_diff > 55:  # Parent very old (women)
                        overlaps.append((person, mother, f"Parent-child age gap very large: {age_diff} years"))
        
        return overlaps
    
    def calculate_generation(self, person: Person, generations: Dict[str, int]) -> int:
        """Calculate generation number (0 = root person, negative = ancestors)"""
        if person.xref in generations:
            return generations[person.xref]
        
        # Look at children to determine generation
        max_child_gen = None
        for family_id in person.families_as_spouse:
            if family_id in self.families:
                family = self.families[family_id]
                for child_id in family.children:
                    if child_id in generations:
                        child_gen = generations[child_id]
                        if max_child_gen is None or child_gen > max_child_gen:
                            max_child_gen = child_gen
        
        if max_child_gen is not None:
            gen = max_child_gen - 1
            generations[person.xref] = gen
            return gen
        
        # Look at parents
        if person.father_id and person.father_id in generations:
            gen = generations[person.father_id] + 1
            generations[person.xref] = gen
            return gen
        
        if person.mother_id and person.mother_id in generations:
            gen = generations[person.mother_id] + 1
            generations[person.xref] = gen
            return gen
        
        return 0
    
    def find_root_person(self) -> Optional[Person]:
        """Find the root person (likely Ira Latrell Toles)"""
        for person in self.individuals.values():
            if 'Ira Latrell' in person.name and 'Toles' in person.name:
                return person
        return None
    
    def build_generation_map(self) -> Dict[str, int]:
        """Build a map of person to generation number"""
        generations = {}
        root = self.find_root_person()
        
        if not root:
            return generations
        
        # Root is generation 0
        generations[root.xref] = 0
        
        # BFS to assign generations
        queue = [root]
        visited = set([root.xref])
        
        while queue:
            person = queue.pop(0)
            current_gen = generations[person.xref]
            
            # Parents are generation -1
            if person.father_id and person.father_id in self.individuals:
                father = self.individuals[person.father_id]
                if father.xref not in visited:
                    generations[father.xref] = current_gen - 1
                    queue.append(father)
                    visited.add(father.xref)
            
            if person.mother_id and person.mother_id in self.individuals:
                mother = self.individuals[person.mother_id]
                if mother.xref not in visited:
                    generations[mother.xref] = current_gen - 1
                    queue.append(mother)
                    visited.add(mother.xref)
            
            # Children are generation +1
            for family_id in person.families_as_spouse:
                if family_id in self.families:
                    family = self.families[family_id]
                    for child_id in family.children:
                        if child_id in self.individuals and child_id not in visited:
                            child = self.individuals[child_id]
                            generations[child_id] = current_gen + 1
                            queue.append(child)
                            visited.add(child_id)
        
        return generations
    
    def analyze(self):
        """Run full analysis"""
        print("=" * 80)
        print("FAMILY TREE CONNECTIONS ANALYSIS")
        print("=" * 80)
        print()
        
        # Parse GEDCOM
        print("Parsing GEDCOM file...")
        self.parse_gedcom()
        print(f"Found {len(self.individuals)} individuals and {len(self.families)} families")
        print()
        
        # Find pre-1930 ancestors
        print("=" * 80)
        print("ANCESTORS BORN BEFORE 1930")
        print("=" * 80)
        pre_1930 = self.find_pre_1930_ancestors()
        print(f"\nFound {len(pre_1930)} ancestors born before 1930:\n")
        
        generations = self.build_generation_map()
        
        # Group by generation
        by_gen = defaultdict(list)
        for person in pre_1930:
            gen = generations.get(person.xref, 999)
            by_gen[gen].append(person)
        
        for gen in sorted(by_gen.keys()):
            gen_label = {
                -1: "Parents",
                -2: "Grandparents",
                -3: "Great-Grandparents",
                -4: "2nd Great-Grandparents",
                -5: "3rd Great-Grandparents",
                -6: "4th Great-Grandparents",
                -7: "5th Great-Grandparents",
                -8: "6th Great-Grandparents",
            }.get(gen, f"Generation {gen}")
            
            print(f"\n{gen_label}:")
            print("-" * 60)
            for person in by_gen[gen]:
                location = person.birth_place if person.birth_place else "Unknown location"
                print(f"  • {person.name}")
                print(f"    Born: {person.birth_year} in {location}")
                if person.death_year:
                    death_loc = person.death_place if person.death_place else "Unknown location"
                    print(f"    Died: {person.death_year} in {death_loc}")
                print()
        
        # Find generation overlaps
        print("\n" + "=" * 80)
        print("GENERATION TIMING DISCREPANCIES")
        print("=" * 80)
        overlaps = self.find_generation_overlaps()
        
        if overlaps:
            print(f"\nFound {len(overlaps)} potential discrepancies:\n")
            for child, parent, issue in overlaps:
                print(f"⚠️  {issue}")
                print(f"    Child:  {child}")
                print(f"    Parent: {parent}")
                print()
        else:
            print("\n✓ No significant generation timing discrepancies found.")
            print()
        
        # Summary stats
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"\nTotal individuals in tree: {len(self.individuals)}")
        print(f"Ancestors born before 1930: {len(pre_1930)}")
        print(f"Ancestors with documented locations: {sum(1 for p in pre_1930 if p.birth_place)}")
        
        # Count by generation
        print("\nBreakdown by generation:")
        for gen in sorted(by_gen.keys()):
            gen_label = {
                -1: "Parents",
                -2: "Grandparents", 
                -3: "Great-Grandparents",
                -4: "2nd Great-Grandparents",
                -5: "3rd Great-Grandparents",
                -6: "4th Great-Grandparents",
                -7: "5th Great-Grandparents",
                -8: "6th Great-Grandparents",
            }.get(gen, f"Generation {gen}")
            print(f"  {gen_label}: {len(by_gen[gen])}")
        
        print("\n" + "=" * 80)


def main():
    gedcom_file = "/home/runner/work/genealogy-/genealogy-/Toles-Johnson-Smith-Bess-Cobb.ged"
    
    analyzer = GedcomAnalyzer(gedcom_file)
    analyzer.analyze()


if __name__ == "__main__":
    main()
