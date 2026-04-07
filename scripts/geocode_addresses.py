# Mass Address Geocoding Script - Run on local Windows machine
# Uses the free US Census Geocoder batch API
# Processes Louisiana addresses first, then Texas
# Run: python scripts\geocode_addresses.py
import sqlite3
import csv
import os
import sys
import time
import io
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'mineral_crm.db')

CENSUS_BATCH_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BATCH_SIZE = 500  # Smaller batches avoid Census API timeouts
RETRY_LIMIT = 5
SLEEP_BETWEEN_BATCHES = 3  # seconds


def geocode_batch(addresses):
    """
    Send a batch of addresses to the Census Geocoder.
    addresses: list of (id, street, city, state, zip)
    Returns: dict of {id: (lat, lng, match_type)}
    """
    # Build CSV for upload
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    for addr in addresses:
        writer.writerow(addr)
    csv_content = csv_buffer.getvalue()

    for attempt in range(RETRY_LIMIT):
        try:
            files = {'addressFile': ('addresses.csv', csv_content, 'text/csv')}
            data = {'benchmark': 'Public_AR_Current', 'returntype': 'locations'}
            resp = requests.post(CENSUS_BATCH_URL, files=files, data=data, timeout=300)

            if resp.status_code != 200:
                print(f"    HTTP {resp.status_code}, retrying ({attempt+1}/{RETRY_LIMIT})...")
                time.sleep(5)
                continue

            results = {}
            reader = csv.reader(io.StringIO(resp.text))
            for row in reader:
                if len(row) >= 6:
                    rec_id = row[0].strip().strip('"')
                    match_status = row[2].strip().strip('"') if len(row) > 2 else ''
                    if match_status == 'Match':
                        # Parse coordinates from the response
                        # Format varies, but coordinates are typically in columns
                        try:
                            # The coordinate is in format "lon,lat" in one of the columns
                            coord_str = ''
                            for col in row:
                                col = col.strip().strip('"')
                                if ',' in col:
                                    parts = col.split(',')
                                    if len(parts) == 2:
                                        try:
                                            lon = float(parts[0])
                                            lat = float(parts[1])
                                            if -180 <= lon <= 0 and 20 <= lat <= 55:
                                                results[rec_id] = (lat, lon, 'census')
                                                break
                                        except ValueError:
                                            continue
                        except Exception:
                            pass
            return results

        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
            print(f" Timeout/connection error, retrying ({attempt+1}/{RETRY_LIMIT})...")
            time.sleep(15 * (attempt + 1))
        except Exception as e:
            print(f" Error: {type(e).__name__}: {e}, retrying ({attempt+1}/{RETRY_LIMIT})...")
            time.sleep(10)

    print(f" Skipping batch after {RETRY_LIMIT} failed attempts")
    return {}


def main():
    start = time.time()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    print(f"Database: {DB_PATH}")
    print()

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.row_factory = sqlite3.Row

    # Normalize state names to abbreviations for consistency
    state_map = {
        'Louisiana': 'LA', 'Texas': 'TX', 'Oklahoma': 'OK', 'Ohio': 'OH',
        'Pennsylvania': 'PA', 'Colorado': 'CO', 'California': 'CA',
        'West Virginia': 'WV', 'Florida': 'FL', 'North Dakota': 'ND',
        'Washington': 'WA', 'Arizona': 'AZ', 'Montana': 'MT',
        'Minnesota': 'MN', 'New Mexico': 'NM', 'South Dakota': 'SD',
        'Georgia': 'GA', 'Alabama': 'AL', 'Mississippi': 'MS',
        'Arkansas': 'AR', 'Tennessee': 'TN', 'Kentucky': 'KY',
        'Virginia': 'VA', 'North Carolina': 'NC', 'South Carolina': 'SC',
        'New York': 'NY', 'Michigan': 'MI', 'Illinois': 'IL',
        'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
        'Nebraska': 'NE', 'Wyoming': 'WY', 'Utah': 'UT',
        'Nevada': 'NV', 'Oregon': 'OR', 'Idaho': 'ID',
        'Hawaii': 'HI', 'Alaska': 'AK', 'Maine': 'ME',
        'New Hampshire': 'NH', 'Vermont': 'VT', 'Massachusetts': 'MA',
        'Rhode Island': 'RI', 'Connecticut': 'CT', 'New Jersey': 'NJ',
        'Delaware': 'DE', 'Maryland': 'MD', 'Missouri': 'MO',
        'Wisconsin': 'WI', 'District of Columbia': 'DC'
    }

    # Process ALL individual contacts with addresses — Louisiana and Texas first, then everything else
    total_need = db.execute("""
        SELECT COUNT(*) FROM owners
        WHERE classification = 'Individual'
          AND mailing_address IS NOT NULL AND mailing_address != ''
          AND city IS NOT NULL AND city != ''
          AND (latitude IS NULL OR latitude = 0)
    """).fetchone()[0]

    print(f"\n{'='*60}")
    print(f"GEOCODING ALL INDIVIDUALS: {total_need:,} addresses")
    print(f"{'='*60}")

    # Show breakdown by state
    print("\nTop states:")
    for row in db.execute("""
        SELECT COALESCE(state,'Unknown') as st, COUNT(*) as cnt FROM owners
        WHERE classification = 'Individual'
          AND mailing_address IS NOT NULL AND mailing_address != ''
          AND city IS NOT NULL AND city != ''
          AND (latitude IS NULL OR latitude = 0)
        GROUP BY state ORDER BY cnt DESC LIMIT 10
    """).fetchall():
        print(f"  {row[0]}: {row[1]:,}")
    print()

    if total_need == 0:
        print("No addresses to geocode!")
    else:
        total_geocoded = 0
        total_failed = 0
        batch_num = 0

        while True:
            # Fetch a batch — Louisiana and Texas first (ORDER BY prioritizes them)
            rows = db.execute(f"""
                SELECT owner_id, mailing_address, city, state, zip_code
                FROM owners
                WHERE classification = 'Individual'
                  AND mailing_address IS NOT NULL AND mailing_address != ''
                  AND city IS NOT NULL AND city != ''
                  AND (latitude IS NULL OR latitude = 0)
                ORDER BY CASE
                    WHEN state IN ('LA','Louisiana') THEN 0
                    WHEN state IN ('TX','Texas') THEN 1
                    ELSE 2
                END, state
                LIMIT {BATCH_SIZE}
            """).fetchall()

            if not rows:
                break

            batch_num += 1
            batch_addresses = []
            id_map = {}

            for r in rows:
                oid = r['owner_id']
                street = r['mailing_address'] or ''
                city = r['city'] or ''
                state = r['state'] or ''
                zipcode = r['zip_code'] or ''

                # Normalize state to abbreviation
                if state in state_map:
                    state = state_map[state]

                rec_id = str(oid)
                batch_addresses.append((rec_id, street, city, state, zipcode))
                id_map[rec_id] = oid

            print(f"  Batch {batch_num}: {len(batch_addresses)} addresses...", end='', flush=True)

            try:
                results = geocode_batch(batch_addresses)
                batch_geocoded = 0

                # Update database with results
                for rec_id, (lat, lng, match_type) in results.items():
                    oid = id_map.get(rec_id)
                    if oid and lat and lng:
                        db.execute(
                            "UPDATE owners SET latitude = ?, longitude = ? WHERE owner_id = ?",
                            (lat, lng, oid)
                        )
                        batch_geocoded += 1

                # Mark non-matches so we don't retry them (set lat/lng to -1 as sentinel)
                non_matched_ids = [id_map[rid] for rid in id_map if rid not in results]
                for oid in non_matched_ids:
                    db.execute(
                        "UPDATE owners SET latitude = -1, longitude = -1 WHERE owner_id = ?",
                        (oid,)
                    )

                db.commit()
            except Exception as e:
                print(f" BATCH ERROR: {e} — skipping batch, continuing...")
                # Still mark these as attempted so we don't loop forever
                for oid in id_map.values():
                    db.execute("UPDATE owners SET latitude = -1, longitude = -1 WHERE owner_id = ?", (oid,))
                db.commit()
                batch_geocoded = 0

            total_geocoded += batch_geocoded
            total_failed += len(non_matched_ids)

            pct = (total_geocoded / total_need * 100) if total_need > 0 else 0
            print(f" {batch_geocoded}/{len(batch_addresses)} matched. "
                  f"Total: {total_geocoded:,}/{total_need:,} ({pct:.1f}%)")

            time.sleep(SLEEP_BETWEEN_BATCHES)

        print(f"\n  Processing complete: {total_geocoded:,} geocoded, {total_failed:,} no match")

    # Clean up sentinel values (-1 means "attempted but no match")
    no_match_count = db.execute("SELECT COUNT(*) FROM owners WHERE latitude = -1").fetchone()[0]

    # Final stats
    elapsed = time.time() - start
    total_geocoded_all = db.execute(
        "SELECT COUNT(*) FROM owners WHERE latitude IS NOT NULL AND latitude > 0"
    ).fetchone()[0]

    print(f"\n{'='*60}")
    print(f"GEOCODING COMPLETE - {elapsed:.0f} seconds ({elapsed/60:.1f} minutes)")
    print(f"{'='*60}")
    print(f"Total successfully geocoded: {total_geocoded_all:,}")
    print(f"No match (attempted): {no_match_count:,}")

    # By state
    print(f"\nGeocoded by state:")
    for row in db.execute("""
        SELECT state, COUNT(*) as cnt FROM owners
        WHERE latitude IS NOT NULL AND latitude > 0
        GROUP BY state ORDER BY cnt DESC LIMIT 10
    """).fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    db.close()
    print("\nDone! You can close this window.")
    input("\nPress Enter to exit...")


if __name__ == '__main__':
    main()
