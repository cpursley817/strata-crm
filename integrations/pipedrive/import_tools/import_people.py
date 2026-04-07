"""
Import Pipedrive People → CRM Owners + Ownership Links + Aliases
Handles deduplication, name cleaning, AKA extraction, and phone normalization.

Usage:
    python import_people.py --csv <path_to_csv> --db <path_to_db>
"""

import csv
import sqlite3
import argparse
import os
import sys
import re
import hashlib
from datetime import datetime
from collections import defaultdict


# ── Name cleaning & AKA extraction ─────────────────────────────────────────

def extract_aliases(name):
    """Extract AKA/FKA/NKA names and return (canonical_name, [(alias, type)])."""
    aliases = []
    cleaned = name

    # Pattern: "Name1 aka Name2" or "Name1 a/k/a Name2"
    aka_patterns = [
        (r'\s+a/?k/?a\.?\s+', 'AKA'),
        (r'\s+f/?k/?a\.?\s+', 'FKA'),
        (r'\s+n/?k/?a\.?\s+', 'NKA'),
        (r',?\s+formerly\s+', 'FKA'),
        (r',?\s+now known as\s+', 'NKA'),
    ]

    for pattern, alias_type in aka_patterns:
        match = re.split(pattern, cleaned, flags=re.IGNORECASE)
        if len(match) > 1:
            cleaned = match[0].strip()
            for alt in match[1:]:
                alt = alt.strip().rstrip(',').strip()
                if alt:
                    aliases.append((alt, alias_type))

    return cleaned, aliases


def clean_name(raw_name):
    """
    Clean a raw Pipedrive name and return (cleaned_name, classification, [(alias, type)]).
    """
    if not raw_name or not raw_name.strip():
        return '', '', []

    name = raw_name.strip()
    classification = ''
    aliases = []

    # Strip leading semicolons
    name = name.lstrip(';').strip()

    # Extract *BA* prefix (Buyer Assignment classification)
    ba_match = re.match(r'^\*BA\*\s*', name)
    if ba_match:
        classification = 'BA'
        name = name[ba_match.end():].strip()

    # Extract AKAs before further processing
    name, aka_aliases = extract_aliases(name)
    aliases.extend(aka_aliases)

    # Normalize case: if ALL CAPS, convert to title case
    # But leave entities (LLC, LP, INC, etc.) and abbreviations alone
    if name == name.upper() and len(name) > 3:
        # Check if it's an entity name (has LLC, INC, LP, etc.)
        entity_words = {'LLC', 'INC', 'LP', 'LLP', 'CORP', 'CO', 'LTD'}
        words = name.split()
        has_entity = any(w.strip('.,()') in entity_words for w in words)

        if not has_entity:
            name = title_case_name(name)

    return name, classification, aliases


def title_case_name(name):
    """Smart title case that handles suffixes, prefixes, and particles correctly."""
    lowercase_words = {'de', 'la', 'le', 'von', 'van', 'du', 'des', 'del', 'di', 'da', 'of', 'the', 'and', 'c/o'}
    suffix_map = {'jr': 'Jr.', 'jr.': 'Jr.', 'sr': 'Sr.', 'sr.': 'Sr.',
                  'ii': 'II', 'iii': 'III', 'iv': 'IV', 'v': 'V'}

    words = name.split()
    result = []
    for i, word in enumerate(words):
        wl = word.lower().rstrip('.,')
        if wl in suffix_map:
            result.append(suffix_map[wl])
        elif i > 0 and wl in lowercase_words:
            result.append(word.lower())
        else:
            # Title case but preserve internal caps for names like McQueen, DeWitt
            result.append(word.capitalize())
    return ' '.join(result)


# ── Phone normalization ─────────────────────────────────────────────────────

def normalize_phone(raw):
    """Normalize phone to 10-digit format. Returns None if invalid."""
    if not raw or not raw.strip():
        return None
    # Strip all non-digits
    digits = re.sub(r'\D', '', raw.strip())
    # Remove leading 1 (country code)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) == 10:
        return digits
    return None  # Invalid phone


def collect_phones(row):
    """Collect all unique normalized phones from a Pipedrive row."""
    phone_fields = [
        'Person - Phone 1', 'Person - Phone 2', 'Person - Phone 3',
        'Person - Phone 4', 'Person - Phone 5', 'Person - Phone 6',
        'Person - Phone - Work', 'Person - Phone - Home',
        'Person - Phone - Mobile', 'Person - Phone - Other',
    ]
    phones = []
    seen = set()
    for field in phone_fields:
        normalized = normalize_phone(row.get(field, ''))
        if normalized and normalized not in seen:
            phones.append(normalized)
            seen.add(normalized)
    return phones


# ── Email normalization ─────────────────────────────────────────────────────

def normalize_email(raw):
    """Normalize email to lowercase, strip whitespace."""
    if not raw or not raw.strip():
        return None
    # Handle comma-separated emails in one field
    emails = [e.strip().lower() for e in raw.split(',') if '@' in e]
    return emails[0] if emails else None


def collect_emails(row):
    """Collect all unique emails from a Pipedrive row."""
    email_fields = [
        'Person - Email - Work', 'Person - Email - Home',
        'Person - Email - Other', 'Person - Email 2',
        'Person - Email 3', 'Person - Email 4',
    ]
    emails = []
    seen = set()
    for field in email_fields:
        raw = row.get(field, '')
        # Some fields have comma-separated emails
        for part in raw.split(','):
            email = normalize_email(part)
            if email and email not in seen:
                emails.append(email)
                seen.add(email)
    return emails


# ── Deduplication key ───────────────────────────────────────────────────────

def make_dedupe_key(name, address='', city='', state=''):
    """
    Create a normalized dedup key from name + location.
    Strips punctuation, lowercases, removes common suffixes.
    """
    # Normalize name
    n = name.lower().strip()
    n = re.sub(r'[^a-z0-9\s]', '', n)  # Remove punctuation
    n = re.sub(r'\s+', ' ', n).strip()  # Collapse whitespace

    # Remove common suffixes that vary
    for suffix in ['jr', 'sr', 'ii', 'iii', 'iv', 'estate', 'et al', 'etal',
                   'deceased', 'dec', 'trust', 'trustee', 'as trustee']:
        n = re.sub(r'\b' + suffix + r'\b', '', n).strip()

    n = re.sub(r'\s+', ' ', n).strip()

    # Normalize location (just state for now — address is too inconsistent)
    s = state.strip().lower()[:2] if state else ''

    key_str = f"{n}|{s}"
    return hashlib.md5(key_str.encode()).hexdigest()


# ── Merge logic for duplicate owners ────────────────────────────────────────

def merge_owner_data(existing, new_data):
    """Merge new data into existing owner record, preferring non-empty values."""
    merged = dict(existing)

    # For each field, keep the existing value if non-empty, else use new
    skip_keys = {'owner_id', 'dedupe_key', 'pipedrive_ids', 'created_at', 'updated_at',
                  'aliases', 'raw_name', 'pipedrive_id'}
    for key in new_data:
        if key in skip_keys:
            continue
        new_val = new_data[key]
        old_val = merged.get(key)
        if isinstance(new_val, (list, dict)):
            continue
        if new_val and (not old_val or (isinstance(old_val, str) and old_val.strip() == '')):
            merged[key] = new_val

    # Merge phone lists
    for i in range(1, 7):
        pkey = f'phone_{i}'
        if new_data.get(pkey) and not merged.get(pkey):
            merged[pkey] = new_data[pkey]

    # Merge email lists
    for i in range(1, 5):
        ekey = f'email_{i}'
        if new_data.get(ekey) and not merged.get(ekey):
            merged[ekey] = new_data[ekey]

    return merged


# ── Main import ─────────────────────────────────────────────────────────────

def import_people(csv_path, db_path):
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found: {csv_path}")
        sys.exit(1)

    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = sqlite3.Row

    # Build section lookup by Pipedrive Org name
    section_lookup = {}
    for row in db.execute("SELECT section_id, display_name, pipedrive_id FROM sections"):
        section_lookup[row['display_name'].strip().lower()] = row['section_id']
        if row['pipedrive_id']:
            section_lookup[f"pid_{row['pipedrive_id']}"] = row['section_id']

    print(f"Loaded {len(section_lookup)//2} sections for matching")

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Read {len(rows)} people from CSV")

    # ── Phase 1: Group by dedupe key ──
    # Each group = same person across multiple sections
    groups = defaultdict(list)

    for raw in rows:
        raw_name = raw.get('Person - Name', '').strip()
        if not raw_name:
            continue

        cleaned_name, classification, aliases = clean_name(raw_name)
        if not cleaned_name:
            continue

        dedupe_key = make_dedupe_key(
            cleaned_name,
            raw.get('Person - Mailing Address', ''),
            raw.get('Person - Owner City', ''),
            raw.get('Person - Owner State', ''),
        )

        phones = collect_phones(raw)
        emails = collect_emails(raw)

        # Build owner data dict
        first = raw.get('Person - First Name*', '').strip() or raw.get('Person - First name', '').strip()
        middle = raw.get('Person - Middle Name*', '').strip()
        last = raw.get('Person - Last Name*', '').strip() or raw.get('Person - Last name', '').strip()

        # Clean up parenthesized first names like "(William) Codie"
        if first and first.startswith('('):
            paren_match = re.match(r'\(([^)]+)\)\s*(.*)', first)
            if paren_match:
                real_first = paren_match.group(1)
                remaining = paren_match.group(2)
                if remaining and not middle:
                    middle = remaining
                first = real_first

        owner_data = {
            'full_name': cleaned_name,
            'first_name': first,
            'middle_name': middle,
            'last_name': last,
            'mailing_address': raw.get('Person - Mailing Address', '').strip(),
            'city': raw.get('Person - Owner City', '').strip(),
            'state': raw.get('Person - Owner State', '').strip(),
            'zip_code': raw.get('Person - Owner Zip Code', '').strip(),
            'classification': classification or raw.get('Person - Classification', '').strip(),
            'dedupe_key': dedupe_key,
            'raw_name': raw_name,  # Keep original for alias tracking
            'aliases': aliases,
            'pipedrive_id': raw.get('Person - ID', '').strip(),
        }

        # Assign phones
        for i, phone in enumerate(phones[:6], 1):
            owner_data[f'phone_{i}'] = phone

        # Assign emails
        for i, email in enumerate(emails[:4], 1):
            owner_data[f'email_{i}'] = email

        # Ownership link data (section-specific)
        org_name = raw.get('Person - Organization', '').strip()
        org_id = raw.get('Person - Organization ID', '').strip()
        link_data = {
            'org_name': org_name,
            'org_id': org_id,
            'nra': raw.get('Person - Net Mineral Acres', '').strip(),
            'gross_acres': raw.get('Person - Gross Tract Acres', '').strip(),
            'interest_type': raw.get('Person - Ownership Type', '').strip(),
            'ownership_pct': raw.get('Person - Tract Ownership Percentage', '').strip(),
            'ownership_decimal': raw.get('Person - Ownership Decimal Interest', '').strip(),
            'lease_royalty': raw.get('Person - Lease Royalty', '').strip(),
            'net_royalty_acres': raw.get('Person - Net Royalty Acres', '').strip(),
            'total_est_nra': raw.get('Person - Total Estimated NRA', '').strip(),
            'instrument_no': raw.get('Person - Instrument No.', '').strip(),
            'instrument_date': raw.get('Person - Instrument Date', '').strip(),
            'pipedrive_person_id': raw.get('Person - ID', '').strip(),
        }

        groups[dedupe_key].append((owner_data, link_data))

    print(f"Grouped into {len(groups)} unique owners (from {len(rows)} rows)")
    print(f"  Cross-section duplicates collapsed: {len(rows) - len(groups)}")

    # ── Phase 2: Insert owners, links, and aliases ──
    owners_inserted = 0
    links_inserted = 0
    aliases_inserted = 0
    link_errors = 0
    all_pipedrive_ids = {}  # owner_id → set of pipedrive IDs

    for dedupe_key, entries in groups.items():
        # Merge all entries for this person into one canonical record
        merged = {}
        all_aliases = []
        all_pd_ids = set()
        all_raw_names = set()

        for owner_data, _ in entries:
            if not merged:
                merged = dict(owner_data)
            else:
                merged = merge_owner_data(merged, owner_data)

            all_aliases.extend(owner_data.get('aliases', []))
            if owner_data.get('pipedrive_id'):
                all_pd_ids.add(owner_data['pipedrive_id'])
            all_raw_names.add(owner_data.get('raw_name', ''))

        # Insert owner
        try:
            cursor = db.execute("""
                INSERT INTO owners (
                    first_name, middle_name, last_name, full_name,
                    mailing_address, city, state, zip_code,
                    phone_1, phone_2, phone_3, phone_4, phone_5, phone_6,
                    email_1, email_2, email_3, email_4,
                    classification, dedupe_key, pipedrive_ids
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                merged.get('first_name', ''),
                merged.get('middle_name', ''),
                merged.get('last_name', ''),
                merged['full_name'],
                merged.get('mailing_address', ''),
                merged.get('city', ''),
                merged.get('state', ''),
                merged.get('zip_code', ''),
                merged.get('phone_1'), merged.get('phone_2'), merged.get('phone_3'),
                merged.get('phone_4'), merged.get('phone_5'), merged.get('phone_6'),
                merged.get('email_1'), merged.get('email_2'),
                merged.get('email_3'), merged.get('email_4'),
                merged.get('classification', ''),
                dedupe_key,
                ','.join(sorted(all_pd_ids)) if all_pd_ids else None,
            ))
            owner_id = cursor.lastrowid
            owners_inserted += 1

        except Exception as e:
            print(f"  ERROR inserting owner '{merged.get('full_name', '?')}': {e}")
            continue

        # Insert aliases (AKAs extracted from names)
        for alias_name, alias_type in all_aliases:
            try:
                db.execute(
                    "INSERT INTO owner_aliases (owner_id, alias_name, alias_type) VALUES (?, ?, ?)",
                    (owner_id, alias_name, alias_type)
                )
                aliases_inserted += 1
            except Exception:
                pass

        # If the raw names varied across entries (different spellings), store alternates as aliases
        canonical = merged['full_name'].lower().strip()
        for raw_name in all_raw_names:
            cleaned_raw = raw_name.strip().lstrip(';').strip()
            # Remove *BA* prefix for comparison
            cleaned_raw = re.sub(r'^\*BA\*\s*', '', cleaned_raw).strip()
            if cleaned_raw.lower() != canonical and cleaned_raw:
                try:
                    db.execute(
                        "INSERT INTO owner_aliases (owner_id, alias_name, alias_type) VALUES (?, ?, ?)",
                        (owner_id, cleaned_raw, 'SPELLING')
                    )
                    aliases_inserted += 1
                except Exception:
                    pass

        # Insert ownership links for each section this person appears in
        for _, link_data in entries:
            org_name = link_data['org_name']
            section_id = section_lookup.get(org_name.lower()) or section_lookup.get(f"pid_{link_data['org_id']}")

            if not section_id:
                link_errors += 1
                continue

            def parse_float(v):
                if not v:
                    return None
                try:
                    return float(v)
                except:
                    return None

            try:
                db.execute("""
                    INSERT OR IGNORE INTO ownership_links (
                        owner_id, section_id, nra, gross_acres,
                        interest_type, ownership_pct, ownership_decimal,
                        lease_royalty, net_royalty_acres, total_est_nra,
                        instrument_no, instrument_date,
                        source, pipedrive_person_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    owner_id,
                    section_id,
                    parse_float(link_data.get('nra')),
                    parse_float(link_data.get('gross_acres')),
                    link_data.get('interest_type') or None,
                    parse_float(link_data.get('ownership_pct')),
                    parse_float(link_data.get('ownership_decimal')),
                    link_data.get('lease_royalty') or None,
                    parse_float(link_data.get('net_royalty_acres')),
                    parse_float(link_data.get('total_est_nra')),
                    link_data.get('instrument_no') or None,
                    link_data.get('instrument_date') or None,
                    'pipedrive_import',
                    int(link_data['pipedrive_person_id']) if link_data.get('pipedrive_person_id') else None,
                ))
                links_inserted += 1
            except Exception as e:
                link_errors += 1

    db.commit()

    # ── Report ──
    print(f"\n{'='*50}")
    print(f"PEOPLE IMPORT COMPLETE")
    print(f"{'='*50}")
    print(f"  CSV rows:            {len(rows)}")
    print(f"  Unique owners:       {owners_inserted}")
    print(f"  Duplicates merged:   {len(rows) - owners_inserted}")
    print(f"  Ownership links:     {links_inserted}")
    print(f"  Aliases saved:       {aliases_inserted}")
    print(f"  Link errors:         {link_errors} (section not found)")

    # Verification queries
    print(f"\n--- Verification ---")

    cursor = db.execute("SELECT COUNT(*) FROM owners")
    print(f"Total owners in DB: {cursor.fetchone()[0]}")

    cursor = db.execute("SELECT COUNT(*) FROM ownership_links")
    print(f"Total ownership links: {cursor.fetchone()[0]}")

    cursor = db.execute("SELECT COUNT(*) FROM owner_aliases")
    print(f"Total aliases: {cursor.fetchone()[0]}")

    # Top multi-section owners
    cursor = db.execute("""
        SELECT o.full_name, COUNT(ol.section_id) as section_count
        FROM owners o
        JOIN ownership_links ol ON o.owner_id = ol.owner_id
        GROUP BY o.owner_id
        HAVING section_count > 5
        ORDER BY section_count DESC
        LIMIT 10
    """)
    print(f"\nTop 10 multi-section owners (the dedup working):")
    for row in cursor.fetchall():
        print(f"  {row[1]} sections: {row[0]}")

    # Owners with aliases
    cursor = db.execute("""
        SELECT o.full_name, GROUP_CONCAT(a.alias_name, ' | ')
        FROM owners o
        JOIN owner_aliases a ON o.owner_id = a.owner_id
        WHERE a.alias_type IN ('AKA', 'FKA', 'NKA')
        LIMIT 10
    """)
    rows_alias = cursor.fetchall()
    if rows_alias:
        print(f"\nSample owners with AKA/FKA aliases:")
        for row in rows_alias:
            print(f"  {row[0]} → {row[1]}")

    # Phone normalization check
    cursor = db.execute("SELECT COUNT(*) FROM owners WHERE phone_1 IS NOT NULL")
    print(f"\nOwners with at least 1 phone: {cursor.fetchone()[0]}")

    cursor = db.execute("SELECT COUNT(*) FROM owners WHERE email_1 IS NOT NULL")
    print(f"Owners with at least 1 email: {cursor.fetchone()[0]}")

    db.close()
    print(f"\nDone. Database: {db_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import Pipedrive People into CRM')
    parser.add_argument('--csv', required=True, help='Path to Pipedrive People CSV')
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    args = parser.parse_args()

    import_people(args.csv, args.db)
