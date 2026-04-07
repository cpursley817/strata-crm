# Compute date_of_birth from static age field (snapshot from Jan 2025)
# Run: python scripts\compute_dob.py
import sqlite3, os, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'mineral_crm.db')

start = time.time()
db = sqlite3.connect(DB_PATH)
db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA synchronous=NORMAL")

cols = [r[1] for r in db.execute('PRAGMA table_info(owners)').fetchall()]
if 'date_of_birth' not in cols:
    db.execute('ALTER TABLE owners ADD COLUMN date_of_birth TEXT')
    db.commit()

count = db.execute("""
    UPDATE owners
    SET date_of_birth = (2025 - age) || '-07-01'
    WHERE age IS NOT NULL AND age > 0 AND (date_of_birth IS NULL OR date_of_birth = '')
""").rowcount
db.commit()

print(f"Computed DOB for {count:,} contacts in {time.time()-start:.1f}s")
db.close()
input("Press Enter to exit...")
