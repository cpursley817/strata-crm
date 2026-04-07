"""
Import Pipedrive Deals → CRM Deals table
Matches deals to existing owners and sections in the database.

Usage:
    python import_deals.py --csv <path_to_csv> --db <path_to_db>
"""

import csv
import sqlite3
import argparse
import os
import sys
import re
import hashlib
from datetime import datetime


def parse_date(val):
    """Parse date string to YYYY-MM-DD."""
    if not val or not val.strip():
        return None
    val = val.strip()
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']:
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return val


def parse_value(val):
    """Parse deal value to float."""
    if not val or not val.strip():
        return None
    try:
        return float(val.strip().replace('$', '').replace(',', ''))
    except (ValueError, TypeError):
        return None


def make_dedupe_key(name):
    """Match the same dedupe logic used in import_people.py."""
    n = name.lower().strip()
    n = re.sub(r'[^a-z0-9\s]', '', n)
    n = re.sub(r'\s+', ' ', n).strip()
    for suffix in ['jr', 'sr', 'ii', 'iii', 'iv', 'estate', 'et al', 'etal',
                   'deceased', 'dec', 'trust', 'trustee', 'as trustee']:
        n = re.sub(r'\b' + suffix + r'\b', '', n).strip()
    n = re.sub(r'\s+', ' ', n).strip()
    key_str = f"{n}|"
    return hashlib.md5(key_str.encode()).hexdigest()


def import_deals(csv_path, db_path):
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found: {csv_path}")
        sys.exit(1)

    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = sqlite3.Row

    # Build lookups
    # Sections by display_name (lowercase)
    section_lookup = {}
    for row in db.execute("SELECT section_id, display_name FROM sections"):
        section_lookup[row['display_name'].strip().lower()] = row['section_id']

    # Pipeline stages by name (lowercase) + pipeline
    stage_lookup = {}
    for row in db.execute("SELECT stage_id, pipeline_name, name FROM pipeline_stages"):
        key = f"{row['pipeline_name'].lower()}|{row['name'].lower()}"
        stage_lookup[key] = row['stage_id']

    # Users by name (lowercase)
    user_lookup = {}
    for row in db.execute("SELECT user_id, name FROM users"):
        user_lookup[row['name'].strip().lower()] = row['user_id']

    # Owners by dedupe_key AND by full_name (lowercase) for fuzzy matching
    owner_by_dedupe = {}
    owner_by_name = {}
    for row in db.execute("SELECT owner_id, full_name, dedupe_key FROM owners"):
        if row['dedupe_key']:
            owner_by_dedupe[row['dedupe_key']] = row['owner_id']
        owner_by_name[row['full_name'].strip().lower()] = row['owner_id']

    # Also check aliases
    alias_lookup = {}
    for row in db.execute("SELECT owner_id, alias_name FROM owner_aliases"):
        alias_lookup[row['alias_name'].strip().lower()] = row['owner_id']

    print(f"Loaded: {len(section_lookup)} sections, {len(stage_lookup)} stages, "
          f"{len(user_lookup)} users, {len(owner_by_name)} owners, {len(alias_lookup)} aliases")

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    print(f"Read {len(rows)} deals from CSV")

    # Import
    imported = 0
    owner_not_found = 0
    section_not_found = 0
    errors = []

    for i, raw in enumerate(rows):
        try:
            title = raw.get('Deal - Title', '').strip()
            if not title:
                continue

            # Match section from Organization field
            org_name = raw.get('Deal - Organization', '').strip()
            section_id = section_lookup.get(org_name.lower())

            if not section_id:
                section_not_found += 1
                errors.append(f"Row {i+2}: Section not found for '{org_name}' — Deal: {title}")
                continue

            # Match owner from Contact person field
            person_name = raw.get('Deal - Contact person', '').strip()
            owner_id = None

            if person_name:
                # Try exact name match first
                owner_id = owner_by_name.get(person_name.lower())

                # Try dedupe key match
                if not owner_id:
                    dk = make_dedupe_key(person_name)
                    owner_id = owner_by_dedupe.get(dk)

                # Try alias match
                if not owner_id:
                    owner_id = alias_lookup.get(person_name.lower())

                # Try partial match — last name in owner names
                if not owner_id:
                    words = person_name.lower().split()
                    if len(words) >= 2:
                        # Try "last, first" and "first last" patterns
                        for oname, oid in owner_by_name.items():
                            if all(w in oname for w in words):
                                owner_id = oid
                                break

            if not owner_id:
                owner_not_found += 1
                # Still import the deal — just without an owner link
                # Create a placeholder note about the unmatched person

            # Match stage
            pipeline = raw.get('Deal - Pipeline', 'Haynesville').strip()
            stage_name = raw.get('Deal - Stage', '').strip()
            stage_key = f"{pipeline.lower()}|{stage_name.lower()}"
            stage_id = stage_lookup.get(stage_key)

            if not stage_id:
                # Try to find stage by name alone
                for sk, sid in stage_lookup.items():
                    if stage_name.lower() in sk:
                        stage_id = sid
                        break

            if not stage_id:
                errors.append(f"Row {i+2}: Stage not found '{stage_name}' — Deal: {title}")
                continue

            # Match user/owner
            deal_owner = raw.get('Deal - Owner', '').strip()
            user_id = user_lookup.get(deal_owner.lower())

            # Status mapping
            status_raw = raw.get('Deal - Status', 'open').strip().lower()
            status = status_raw if status_raw in ('open', 'won', 'lost') else 'open'

            # Value
            value = parse_value(raw.get('Deal - Value'))

            # Dates
            created = parse_date(raw.get('Deal - Deal created'))
            won_time = parse_date(raw.get('Deal - Won time'))
            lost_time = parse_date(raw.get('Deal - Lost time'))
            closed_on = parse_date(raw.get('Deal - Deal closed on'))
            actual_close = won_time or closed_on

            # Insert deal
            cursor = db.execute("""
                INSERT INTO deals (
                    owner_id, section_id, stage_id, assigned_user_id,
                    title, value, status,
                    actual_close, pipedrive_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                owner_id,  # May be None if not matched
                section_id,
                stage_id,
                user_id,
                title,
                value,
                status,
                actual_close,
                int(raw.get('Deal - ID', 0)) if raw.get('Deal - ID', '').strip() else None,
                created or datetime.now().strftime('%Y-%m-%d'),
            ))

            imported += 1

        except Exception as e:
            errors.append(f"Row {i+2}: {e} — {raw.get('Deal - Title', '?')}")

    db.commit()

    # Report
    print(f"\n{'='*50}")
    print(f"DEALS IMPORT COMPLETE")
    print(f"{'='*50}")
    print(f"  Imported:            {imported}")
    print(f"  Owner not found:     {owner_not_found} (deals imported without owner link)")
    print(f"  Section not found:   {section_not_found} (deals skipped)")
    print(f"  Other errors:        {len(errors) - section_not_found}")

    if errors[:15]:
        print(f"\nFirst 15 issues:")
        for e in errors[:15]:
            print(f"  - {e}")

    # Verification
    cursor = db.execute("SELECT COUNT(*) FROM deals")
    print(f"\nTotal deals in DB: {cursor.fetchone()[0]}")

    cursor = db.execute("SELECT status, COUNT(*) FROM deals GROUP BY status ORDER BY COUNT(*) DESC")
    print("\nBy status:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cursor = db.execute("""
        SELECT ps.name, COUNT(*) FROM deals d
        JOIN pipeline_stages ps ON d.stage_id = ps.stage_id
        GROUP BY ps.name ORDER BY ps.sort_order
    """)
    print("\nBy stage:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cursor = db.execute("SELECT COUNT(*) FROM deals WHERE owner_id IS NOT NULL")
    matched = cursor.fetchone()[0]
    cursor = db.execute("SELECT COUNT(*) FROM deals WHERE owner_id IS NULL")
    unmatched = cursor.fetchone()[0]
    print(f"\nOwner matching: {matched} matched, {unmatched} unmatched")

    cursor = db.execute("""
        SELECT u.name, COUNT(*) FROM deals d
        JOIN users u ON d.assigned_user_id = u.user_id
        GROUP BY u.name ORDER BY COUNT(*) DESC
    """)
    print("\nBy buyer:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    db.close()
    print(f"\nDone. Database: {db_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import Pipedrive Deals into CRM')
    parser.add_argument('--csv', required=True, help='Path to Pipedrive Deals CSV')
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    args = parser.parse_args()

    import_deals(args.csv, args.db)
