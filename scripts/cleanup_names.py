#!/usr/bin/env python3
"""
Name & City Proper Case Cleanup + Classification Fix
Fixes:
  - ALL CAPS names → Proper Case (JOHN SMITH → John Smith)
  - ALL CAPS cities → Proper Case (BOSSIER CITY → Bossier City)
  - Spaced abbreviations: L L C → LLC, L P → LP, L L P → LLP, I N C → Inc
  - McNames: Mc Donald → McDonald, MCDONALD → McDonald
  - Reclassifies contacts whose name contains LLC/LP/LLP/Inc/Corp after fix
  - Preserves: suffixes (Jr, Sr, III, IV), company abbreviations (LLC, LP, etc.),
    directional abbreviations (NW, NE, SW, SE), state abbreviations, P.O. Box

Usage: python3 scripts/cleanup_names.py [--dry-run]
"""

import sqlite3
import sys
import os
import re

DRY_RUN = '--dry-run' in sys.argv
REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DB_PATH = os.environ.get('DB_PATH', os.path.join(REPO_ROOT, 'database', 'mineral_crm.db'))

print(f"Database: {DB_PATH}")
print(f"Mode: {'DRY RUN (no changes)' if DRY_RUN else 'LIVE — will modify database'}")

# Words to keep uppercase
UPPER_WORDS = {
    'LLC', 'LP', 'LLP', 'INC', 'CORP', 'CO', 'LTD', 'PC', 'PA', 'NA',
    'NW', 'NE', 'SW', 'SE', 'PO', 'II', 'III', 'IV', 'VI', 'VII', 'VIII',
    'JR', 'SR', 'USA', 'US', 'TX', 'LA', 'OK', 'AR', 'MS', 'AL', 'FL',
    'GA', 'TN', 'NC', 'SC', 'VA', 'WV', 'KY', 'OH', 'PA', 'NY', 'NJ',
    'CT', 'MA', 'MD', 'DE', 'NH', 'VT', 'ME', 'RI', 'CO', 'NM', 'AZ',
    'UT', 'NV', 'CA', 'OR', 'WA', 'ID', 'MT', 'WY', 'ND', 'SD', 'NE',
    'KS', 'MN', 'IA', 'MO', 'WI', 'MI', 'IN', 'IL', 'HI', 'AK',
    'DBA', 'FBO', 'AKA', 'ETAL', 'ETUX', 'ETVIR',
}

# Words to keep lowercase
LOWER_WORDS = {'of', 'the', 'and', 'de', 'la', 'le', 'van', 'von', 'del', 'da', 'di'}

def proper_case(name):
    if not name or not name.strip():
        return name

    # Step 1: Collapse spaced abbreviations BEFORE doing anything else
    s = name
    s = re.sub(r'\bL\s+L\s+C\b', 'LLC', s, flags=re.IGNORECASE)
    s = re.sub(r'\bL\s+L\s+P\b', 'LLP', s, flags=re.IGNORECASE)
    s = re.sub(r'\bL\s+P\b', 'LP', s, flags=re.IGNORECASE)
    s = re.sub(r'\bI\s+N\s+C\b', 'Inc', s, flags=re.IGNORECASE)
    s = re.sub(r'\bC\s+O\s+R\s+P\b', 'Corp', s, flags=re.IGNORECASE)
    s = re.sub(r'\bL\s*\.\s*L\s*\.\s*C\s*\.?', 'LLC', s, flags=re.IGNORECASE)
    s = re.sub(r'\bL\s*\.\s*P\s*\.?', 'LP', s, flags=re.IGNORECASE)

    # Step 1b: Collapse "Mc " + word → "Mc<Word>" (e.g., "Mc Donald" → "McDonald")
    s = re.sub(r'\bMc\s+([A-Za-z])', lambda m: 'Mc' + m.group(1).upper(), s)
    s = re.sub(r'\bMC\s+([A-Za-z])', lambda m: 'Mc' + m.group(1).upper(), s, flags=re.IGNORECASE)

    # Step 2: Title case each word
    words = s.split()
    result = []
    for i, word in enumerate(words):
        upper = word.upper().rstrip('.,')

        # Keep known uppercase words
        if upper in UPPER_WORDS:
            result.append(upper + word[len(upper):])
        # Handle Mc/Mac prefixes
        elif upper.startswith('MC') and len(word) > 2:
            result.append('Mc' + word[2:].capitalize())
        elif upper.startswith('MAC') and len(word) > 3 and word.upper() not in ('MACK', 'MACHINE', 'MACRO'):
            result.append('Mac' + word[3:].capitalize())
        # Handle O' prefixes (O'Brien, O'Neil)
        elif "'" in word and len(word) > 2:
            parts = word.split("'")
            result.append("'".join(p.capitalize() for p in parts))
        # Handle hyphenated names
        elif '-' in word:
            result.append('-'.join(p.capitalize() for p in word.split('-')))
        # P.O. Box
        elif upper == 'P.O.' or upper == 'PO':
            result.append('P.O.' if '.' in word else 'PO')
        # Single letter (middle initial)
        elif len(word) == 1:
            result.append(word.upper())
        # Lowercase words (except first word)
        elif upper.lower() in LOWER_WORDS and i > 0:
            result.append(word.lower())
        # Default: capitalize first letter
        else:
            result.append(word.capitalize())

    return ' '.join(result)


def classify_name(name):
    """Reclassify based on cleaned name."""
    if not name:
        return None
    upper = name.upper()
    if any(kw in upper for kw in [' LLC', ',LLC', ' L.L.C']):
        return 'LLC'
    if any(kw in upper for kw in [' LP', ',LP', ' L.P']):
        return 'LLC'  # LP goes to LLC bucket per Chase's preference
    if any(kw in upper for kw in [' LLP', ',LLP']):
        return 'LLC'
    if any(kw in upper for kw in [' INC', ',INC', ' CORP', ',CORP', ' CO.', ' COMPANY', ' ENTERPRISES']):
        return 'Corporation'
    if any(kw in upper for kw in [' TRUST', ' LIVING TRUST', ' FAMILY TRUST', ' REVOCABLE', ' IRREVOCABLE']):
        return 'Trust'
    if any(kw in upper for kw in [' ESTATE', 'ESTATE OF', 'SUCCESSION']):
        return 'Estate'
    if any(kw in upper for kw in [' CHURCH', ' MINISTRY', ' FOUNDATION', ' ASSOCIATION', ' PARTNERSHIP']):
        return 'Business'
    return None  # Don't change if we can't determine


db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
c = db.cursor()

# Count totals
total = c.execute('SELECT COUNT(*) FROM owners').fetchone()[0]
print(f"\nTotal contacts: {total:,}")

# Process names in batches to avoid loading all 841K into memory at once
BATCH_SIZE = 10000
total_to_check = c.execute("SELECT COUNT(*) FROM owners WHERE full_name IS NOT NULL AND full_name != ''").fetchone()[0]
print(f"Contacts to check: {total_to_check:,}")

# Find contacts needing city cleanup
needs_city_fix = c.execute("""
    SELECT owner_id, city
    FROM owners
    WHERE city IS NOT NULL AND city != '' AND city = UPPER(city) AND LENGTH(city) > 2
""").fetchall()

print(f"Contacts needing city fix: {len(needs_city_fix):,}")

name_updates = 0
city_updates = 0
class_updates = 0

# Process name fixes in batches
print("\nProcessing name fixes...")
offset = 0
while offset < total_to_check:
    batch = c.execute("""
        SELECT owner_id, full_name, first_name, middle_name, last_name, entity_name,
               city, mailing_address, classification
        FROM owners
        WHERE full_name IS NOT NULL AND full_name != ''
        LIMIT ? OFFSET ?
    """, (BATCH_SIZE, offset)).fetchall()
    if not batch:
        break
    print(f"  Batch {offset // BATCH_SIZE + 1}: rows {offset + 1}-{offset + len(batch)}")
    for row in batch:
        oid = row['owner_id']
        updates = {}

        if row['full_name']:
            new_name = proper_case(row['full_name'])
            if new_name != row['full_name']:
                updates['full_name'] = new_name

        if row['first_name'] and row['first_name'] == row['first_name'].upper() and len(row['first_name']) > 1:
            updates['first_name'] = proper_case(row['first_name'])

        if row['middle_name'] and row['middle_name'] == row['middle_name'].upper() and len(row['middle_name']) > 1:
            updates['middle_name'] = proper_case(row['middle_name'])

        if row['last_name'] and row['last_name'] == row['last_name'].upper() and len(row['last_name']) > 1:
            updates['last_name'] = proper_case(row['last_name'])

        if row['entity_name'] and row['entity_name'] == row['entity_name'].upper():
            updates['entity_name'] = proper_case(row['entity_name'])

        # Check if classification should change based on cleaned name
        cleaned = updates.get('full_name', row['full_name'])
        new_class = classify_name(cleaned)
        if new_class and new_class != row['classification']:
            updates['classification'] = new_class
            class_updates += 1

        if updates and not DRY_RUN:
            set_clause = ', '.join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [oid]
            c.execute(f"UPDATE owners SET {set_clause} WHERE owner_id = ?", values)
            name_updates += 1
        elif updates:
            name_updates += 1

    # Commit after each batch
    if not DRY_RUN:
        db.commit()
    offset += len(batch)

# Process city fixes
print("Processing city fixes...")
for row in needs_city_fix:
    new_city = proper_case(row['city'])
    if new_city != row['city']:
        if not DRY_RUN:
            c.execute("UPDATE owners SET city = ? WHERE owner_id = ?", (new_city, row['owner_id']))
        city_updates += 1

# Also fix mailing_address ALL CAPS
needs_addr_fix = c.execute("""
    SELECT owner_id, mailing_address
    FROM owners
    WHERE mailing_address IS NOT NULL AND mailing_address != ''
      AND mailing_address = UPPER(mailing_address) AND LENGTH(mailing_address) > 5
""").fetchall()

addr_updates = 0
print("Processing address fixes...")
for row in needs_addr_fix:
    new_addr = proper_case(row['mailing_address'])
    if new_addr != row['mailing_address']:
        if not DRY_RUN:
            c.execute("UPDATE owners SET mailing_address = ? WHERE owner_id = ?", (new_addr, row['owner_id']))
        addr_updates += 1

if not DRY_RUN:
    db.commit()

db.close()

print(f"\n{'='*50}")
print(f"RESULTS {'(DRY RUN)' if DRY_RUN else '(APPLIED)'}:")
print(f"  Names fixed: {name_updates:,}")
print(f"  Cities fixed: {city_updates:,}")
print(f"  Addresses fixed: {addr_updates:,}")
print(f"  Classifications changed: {class_updates:,}")
print(f"{'='*50}")

if DRY_RUN:
    print("\nRe-run without --dry-run to apply changes.")
