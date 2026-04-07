"""
Import Pipedrive Organizations → CRM Sections table
Reads the Pipedrive Organizations CSV export and inserts into the SQLite database.

Usage:
    python import_organizations.py --csv <path_to_csv> --db <path_to_db>

Example:
    python import_organizations.py \
        --csv ../../imports/pipedrive/pipedrive-organizations_2026-03-16.csv \
        --db ../../database/mineral_crm.db
"""

import csv
import sqlite3
import argparse
import os
import sys
from datetime import datetime


# ── Column mapping: Pipedrive CSV header → our field names ──────────────────
CSV_MAP = {
    'Organization - ID':                'pipedrive_id',
    'Organization - Basin':             'basin',
    'Organization - State':             'state',
    'Organization - County/Parish':     'parish',
    'Organization - Name':              'display_name',
    'Organization - Section(s)':        'section_number',
    'Organization - Township':          'township',
    'Organization - Range or Block':    'range',
    'Organization - Labels':            'status',
    'Organization - Owner':             'assigned_user',
    'Organization - People':            'people_count',
    'Organization - Total activities':  'total_contacts',
    'Organization - BBR Exit $/NRA':    'bbr_exit_price',
    'Organization - Cost-Free $/NRA':   'cost_free_price',
    'Organization - Pricing Date':      'pricing_date',
    'Organization - Prev. BBR Exit Price':   'prev_bbr_price',
    'Organization - Prev. Cost-Free $/NRA':  'prev_cost_free',
    'Organization - Prev. Pricing Date':     'prev_pricing_date',
    'Organization - Buying Group':      'buying_group',
    'Organization - Operator':          'operator',
    'Organization - Ownership Data':    'ownership_data',
    'Organization - Section Notes':     'section_notes',
    'Organization - Survey':            'survey',
    'Organization - BBR Start Price':   'bbr_start_price',
    'Organization - Pricing Royalty':   'pricing_royalty',
    'Organization - Legal Description': 'legal_desc',
    'Organization - Organization created': 'created_at',
}


# ── Normalization helpers ───────────────────────────────────────────────────

def normalize_state(val):
    """Normalize state to 2-letter abbreviation."""
    mapping = {
        'louisiana': 'LA', 'la': 'LA',
        'texas': 'TX', 'tx': 'TX',
        'oklahoma': 'OK', 'ok': 'OK',
        'north dakota': 'ND', 'nd': 'ND',
        'new mexico': 'NM', 'nm': 'NM',
    }
    return mapping.get(val.strip().lower(), val.strip().upper())


def normalize_status(val):
    """Normalize status labels to consistent uppercase."""
    mapping = {
        'active': 'ACTIVE',
        'inactive': 'INACTIVE',
        'exhausted': 'EXHAUSTED',
        'no price': 'NO PRICE',
        'dead': 'DEAD',
    }
    return mapping.get(val.strip().lower(), val.strip().upper())


def parse_price(val):
    """Parse a price string to float, handling currency symbols and commas."""
    if not val or not val.strip():
        return None
    cleaned = val.strip().replace('$', '').replace(',', '')
    try:
        result = float(cleaned)
        return result if result > 0 else None
    except (ValueError, TypeError):
        return None


def parse_date(val):
    """Parse various date formats to YYYY-MM-DD."""
    if not val or not val.strip():
        return None
    val = val.strip()

    # Try common formats
    for fmt in [
        '%Y-%m-%d %H:%M:%S',   # 2023-07-26 15:53:47
        '%Y-%m-%d',             # 2023-07-26
        '%m/%d/%Y',             # 3/11/2026
        '%m/%d/%y',             # 3/11/26
        '%m-%d-%Y',             # 03-11-2026
        '%B %d, %Y',           # March 11, 2026
    ]:
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return val  # Return as-is if no format matches


def parse_int(val):
    """Parse an integer, returning 0 for empty/invalid."""
    if not val or not val.strip():
        return 0
    try:
        return int(float(val.strip()))
    except (ValueError, TypeError):
        return 0


# ── Lookup cache builders ───────────────────────────────────────────────────

def build_lookup(db, table, name_col, id_col):
    """Build a name→id lookup dict from a reference table."""
    cursor = db.execute(f"SELECT {id_col}, {name_col} FROM {table}")
    return {row[1].strip().lower(): row[0] for row in cursor.fetchall()}


def get_or_create(db, table, name_col, id_col, name, extra_cols=None):
    """Get ID for a name, creating the record if it doesn't exist."""
    if not name or not name.strip():
        return None
    name = name.strip()
    cursor = db.execute(
        f"SELECT {id_col} FROM {table} WHERE LOWER({name_col}) = LOWER(?)", (name,)
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    # Create new record
    if extra_cols:
        cols = f"{name_col}, " + ", ".join(extra_cols.keys())
        placeholders = "?, " + ", ".join(["?"] * len(extra_cols))
        vals = [name] + list(extra_cols.values())
    else:
        cols = name_col
        placeholders = "?"
        vals = [name]

    cursor = db.execute(
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", vals
    )
    return cursor.lastrowid


# ── Main import logic ───────────────────────────────────────────────────────

def import_organizations(csv_path, db_path):
    """Import Pipedrive Organizations CSV into the sections table."""

    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        sys.exit(1)

    if not os.path.exists(db_path):
        print(f"ERROR: Database not found: {db_path}")
        print(f"  Run: sqlite3 {db_path} < schema.sql")
        sys.exit(1)

    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys=ON")

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Read {len(rows)} organizations from CSV")

    # Stats
    imported = 0
    skipped = 0
    errors = []

    for i, raw in enumerate(rows):
        try:
            # Map CSV columns to our field names
            r = {}
            for csv_col, our_col in CSV_MAP.items():
                r[our_col] = raw.get(csv_col, '').strip()

            # Skip rows with no name
            if not r.get('display_name'):
                skipped += 1
                continue

            # ── Resolve foreign keys ──

            # Basin
            basin_name = r.get('basin', 'Haynesville')
            basin_id = get_or_create(db, 'basins', 'name', 'basin_id', basin_name,
                                     {'state': normalize_state(r.get('state', 'LA'))})

            # Parish
            parish_name = r.get('parish', '')
            parish_id = None
            if parish_name:
                parish_id = get_or_create(db, 'parishes', 'name', 'parish_id', parish_name,
                                          {'basin_id': basin_id, 'state': normalize_state(r.get('state', 'LA'))})

            # Operator
            operator_name = r.get('operator', '')
            operator_id = get_or_create(db, 'operators', 'name', 'operator_id', operator_name) if operator_name else None

            # Buying group
            bg_name = r.get('buying_group', '')
            bg_id = get_or_create(db, 'buying_groups', 'name', 'group_id', bg_name) if bg_name else None

            # Assigned user
            user_name = r.get('assigned_user', '')
            user_id = get_or_create(db, 'users', 'name', 'user_id', user_name) if user_name else None

            # ── Insert section ──
            db.execute("""
                INSERT OR IGNORE INTO sections (
                    basin_id, parish_id, section_number, township, range,
                    legal_desc, display_name,
                    bbr_exit_price, cost_free_price, pricing_date,
                    prev_bbr_price, prev_cost_free, prev_pricing_date,
                    bbr_start_price, pricing_royalty,
                    operator_id, buying_group_id, assigned_user_id,
                    status, section_notes, ownership_data, survey,
                    pipedrive_id, people_count, total_contacts,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                basin_id,
                parish_id,
                r.get('section_number', ''),
                r.get('township', ''),
                r.get('range', ''),
                r.get('legal_desc', '') or None,
                r['display_name'],
                parse_price(r.get('bbr_exit_price')),
                parse_price(r.get('cost_free_price')),
                parse_date(r.get('pricing_date')),
                parse_price(r.get('prev_bbr_price')),
                parse_price(r.get('prev_cost_free')),
                parse_date(r.get('prev_pricing_date')),
                parse_price(r.get('bbr_start_price')),
                r.get('pricing_royalty', '') or None,
                operator_id,
                bg_id,
                user_id,
                normalize_status(r.get('status', 'ACTIVE')),
                r.get('section_notes', '') or None,
                r.get('ownership_data', '') or None,
                r.get('survey', '') or None,
                parse_int(r.get('pipedrive_id')),
                parse_int(r.get('people_count')),
                parse_int(r.get('total_contacts')),
                parse_date(r.get('created_at')) or datetime.now().strftime('%Y-%m-%d'),
            ))

            imported += 1

        except Exception as e:
            errors.append(f"Row {i+2}: {e} — {r.get('display_name', 'UNKNOWN')}")

    db.commit()

    # ── Report ──
    print(f"\n{'='*50}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*50}")
    print(f"  Imported:  {imported}")
    print(f"  Skipped:   {skipped}")
    print(f"  Errors:    {len(errors)}")

    if errors:
        print(f"\nFirst 10 errors:")
        for e in errors[:10]:
            print(f"  - {e}")

    # Verify counts
    cursor = db.execute("SELECT COUNT(*) FROM sections")
    print(f"\nDatabase now has {cursor.fetchone()[0]} sections")

    cursor = db.execute("SELECT status, COUNT(*) FROM sections GROUP BY status ORDER BY COUNT(*) DESC")
    print("\nBy status:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cursor = db.execute("""
        SELECT u.name, COUNT(*) FROM sections s
        JOIN users u ON s.assigned_user_id = u.user_id
        GROUP BY u.name ORDER BY COUNT(*) DESC
    """)
    print("\nBy buyer:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cursor = db.execute("""
        SELECT p.name, COUNT(*) FROM sections s
        JOIN parishes p ON s.parish_id = p.parish_id
        GROUP BY p.name ORDER BY COUNT(*) DESC
    """)
    print("\nBy parish:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    db.close()
    print(f"\nDone. Database: {db_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import Pipedrive Organizations into CRM')
    parser.add_argument('--csv', required=True, help='Path to Pipedrive Organizations CSV')
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    args = parser.parse_args()

    import_organizations(args.csv, args.db)
