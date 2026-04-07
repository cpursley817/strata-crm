# AIS Data Enrichment Script - Run on local Windows machine
# Imports financial flags and relatives data from AIS CSV source files
# into the mineral_crm.db database.
# SAFE TO RUN MULTIPLE TIMES - overwrites previous values, no duplicates.
import sqlite3
import csv
import json
import os
import sys
import time

# Paths — adjust if your folder structure differs
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'mineral_crm.db')
AIS_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), 'imports', 'ais')

CSV_FILES = [os.path.join(AIS_DIR, f'SQLDump{i}.csv') for i in range(1, 5)]

# AIS CSV column indices (0-based)
FLAG_INDICES = {53: 'has_bankruptcy', 54: 'has_lien', 55: 'has_judgment',
                56: 'has_evictions', 57: 'has_foreclosures', 58: 'has_debt'}
REL_START = 61
REL_FIELDS = ['contact_id', 'name', 'address', 'city', 'zip',
              'phone1', 'phone1_type', 'phone2', 'phone2_type',
              'phone3', 'phone3_type', 'email1', 'email2', 'email3', 'estimated_age']


def parse_flag(val):
    return 1 if val and val.strip().lower() in ('yes', 'true', '1', 'y') else 0


def parse_relatives(row):
    relatives = []
    for r in range(3):
        base = REL_START + (r * 15)
        if base + 1 >= len(row):
            break
        name = row[base + 1].strip() if base + 1 < len(row) else ''
        if not name:
            continue
        rel = {}
        for j, field in enumerate(REL_FIELDS):
            idx = base + j
            rel[field] = row[idx].strip() if idx < len(row) else ''
        relatives.append(rel)
    return relatives


def main():
    start = time.time()

    # Verify paths
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    print(f"Database: {DB_PATH}")
    print(f"AIS data: {AIS_DIR}")
    print()

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA cache_size=-200000")  # 200MB cache
    db.row_factory = sqlite3.Row

    # Step 1: Ensure columns exist
    print("Step 1: Checking database columns...")
    existing = [r['name'] for r in db.execute('PRAGMA table_info(owners)').fetchall()]
    for col in FLAG_INDICES.values():
        if col not in existing:
            db.execute(f'ALTER TABLE owners ADD COLUMN {col} INTEGER DEFAULT 0')
            print(f"  Added: {col}")
    db.commit()

    # Step 2: Create index for fast lookups
    print("Step 2: Creating lookup index...")
    db.execute("CREATE INDEX IF NOT EXISTS idx_owners_name_city_state ON owners(full_name, city, state)")
    db.commit()
    print("  Index ready.")

    # Step 3: Build in-memory lookup (Windows has more RAM than the VM)
    print("Step 3: Loading contact lookup into memory...")
    lookup = {}
    cursor = db.execute("SELECT owner_id, full_name, city, state FROM owners")
    count = 0
    while True:
        rows = cursor.fetchmany(100000)
        if not rows:
            break
        for r in rows:
            key = f"{(r['full_name'] or '').strip()}|{(r['city'] or '').strip()}|{(r['state'] or '').strip()}"
            lookup[key] = r['owner_id']
            count += 1
        print(f"  Loaded {count:,} contacts...")
    print(f"  Total: {count:,} contacts indexed in memory")

    # Step 4: Process CSVs
    grand_total = {'rows': 0, 'matched': 0, 'flags': 0, 'relatives': 0}

    for csv_file in CSV_FILES:
        if not os.path.exists(csv_file):
            print(f"\nSkipping {os.path.basename(csv_file)} — file not found")
            continue

        fname = os.path.basename(csv_file)
        print(f"\nStep 4: Processing {fname}...")

        file_stats = {'rows': 0, 'matched': 0, 'flags': 0, 'relatives': 0}
        batch = []

        with open(csv_file, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader)

            # Find name/city/state columns
            name_col = city_col = state_col = None
            for i, h in enumerate(header):
                hl = h.strip().lower()
                if 'ownername' in hl or hl == 'name' or hl == 'full_name':
                    if name_col is None: name_col = i
                elif 'ownercity' in hl or (hl == 'city' and 'relative' not in header[i].lower()):
                    if city_col is None: city_col = i
                elif 'ownerstate' in hl or (hl == 'state' and 'relative' not in header[i].lower()):
                    if state_col is None: state_col = i

            if name_col is None:
                # Fallback: find first column with 'name' that isn't relative
                for i, h in enumerate(header):
                    if 'name' in h.lower() and 'relative' not in h.lower() and name_col is None:
                        name_col = i

            print(f"  Match columns: name=[{name_col}], city=[{city_col}], state=[{state_col}]")

            for row in reader:
                file_stats['rows'] += 1

                if name_col is None or name_col >= len(row):
                    continue

                name = row[name_col].strip() if name_col < len(row) else ''
                city = row[city_col].strip() if city_col and city_col < len(row) else ''
                state = row[state_col].strip() if state_col and state_col < len(row) else ''

                if not name:
                    continue

                key = f"{name}|{city}|{state}"
                owner_id = lookup.get(key)
                if not owner_id:
                    continue

                file_stats['matched'] += 1

                # Extract flags
                flags = {}
                for col_idx, col_name in FLAG_INDICES.items():
                    if col_idx < len(row) and parse_flag(row[col_idx]):
                        flags[col_name] = 1

                if flags:
                    file_stats['flags'] += 1

                # Extract relatives
                relatives = parse_relatives(row)
                rel_json = json.dumps(relatives) if relatives else None
                if relatives:
                    file_stats['relatives'] += 1

                # Build update
                if flags or relatives:
                    sets = []
                    params = []
                    for cn, v in flags.items():
                        sets.append(f"{cn} = ?")
                        params.append(v)
                    if rel_json:
                        sets.append("relatives_json = ?")
                        params.append(rel_json)
                    params.append(owner_id)
                    batch.append((f"UPDATE owners SET {', '.join(sets)} WHERE owner_id = ?", params))

                # Commit in batches
                if len(batch) >= 5000:
                    for sql, p in batch:
                        db.execute(sql, p)
                    db.commit()
                    batch = []

                if file_stats['rows'] % 100000 == 0:
                    print(f"    {file_stats['rows']:,} rows, {file_stats['matched']:,} matched, "
                          f"{file_stats['flags']:,} flags, {file_stats['relatives']:,} relatives")

        # Flush remaining
        if batch:
            for sql, p in batch:
                db.execute(sql, p)
            db.commit()

        print(f"  {fname}: {file_stats['rows']:,} rows, {file_stats['matched']:,} matched, "
              f"{file_stats['flags']:,} flags, {file_stats['relatives']:,} relatives")

        for k in grand_total:
            grand_total[k] += file_stats[k]

    # Final summary
    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"ENRICHMENT COMPLETE — {elapsed:.0f} seconds")
    print(f"{'=' * 60}")
    print(f"Total CSV rows:    {grand_total['rows']:,}")
    print(f"Total matched:     {grand_total['matched']:,}")
    print(f"With flags:        {grand_total['flags']:,}")
    print(f"With relatives:    {grand_total['relatives']:,}")

    # Verification
    print(f"\nVerification:")
    for cn in FLAG_INDICES.values():
        cnt = db.execute(f"SELECT COUNT(*) FROM owners WHERE {cn} = 1").fetchone()[0]
        print(f"  {cn}: {cnt:,}")

    rel_cnt = db.execute("SELECT COUNT(*) FROM owners WHERE relatives_json IS NOT NULL "
                         "AND relatives_json != '' AND relatives_json != '[]'").fetchone()[0]
    print(f"  Has relatives: {rel_cnt:,}")

    db.close()
    print("\nDone! You can close this window.")
    input("\nPress Enter to exit...")


if __name__ == '__main__':
    main()
