#!/usr/bin/env python3
"""
Minimal memory import. Reads CSV line by line as raw text, parses manually.
No csv module, no DictReader, no batch accumulation.
"""
import hashlib, os, re, sqlite3, sys, gc

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DB = os.environ.get('DB_PATH', os.path.join(REPO_ROOT, 'database', 'mineral_crm.db'))
EXTRACTED = os.environ.get('AIS_EXTRACTED', os.path.join(REPO_ROOT, '..', 'imports', 'ais', 'extracted_contacts'))

FNUM = int(sys.argv[1])
fp = os.path.join(EXTRACTED, f'contacts_{FNUM}.csv')

def parse_csv_line(line):
    """Simple CSV parser for our controlled data (no embedded commas in fields)."""
    # Our extracted files are clean — split by comma, strip quotes
    fields = []
    in_quote = False
    current = []
    for ch in line:
        if ch == '"':
            in_quote = not in_quote
        elif ch == ',' and not in_quote:
            fields.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    fields.append(''.join(current).strip())
    return fields

def cp(p):
    if not p: return None
    d = re.sub(r'[^\d]', '', p)
    if len(d)==11 and d[0]=='1': d=d[1:]
    return f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d)==10 else None

def ce(e):
    if not e: return None
    v = e.lower()
    return v if '@' in v and '.' in v else None

def dk(name, addr, city, st, z):
    n = re.sub(r'\s+', ' ', name.upper())
    n = re.sub(r'\b(JR|SR|III|II|IV)\b\.?', '', n).strip(' ,.')
    return hashlib.md5(f"{n}|{(addr or '').upper()}|{(city or '').upper()}|{(st or '').upper()}|{(z or '')[:5]}".encode()).hexdigest()

def pn(fn):
    name = fn.strip(); suf=None
    m = re.search(r'\b(JR|SR|III|II|IV)\b\.?\s*$', name, re.I)
    if m: suf=m.group(1).upper(); name=name[:m.start()].strip(' ,')
    ps = name.split()
    if len(ps)==0: return fn,None,None,suf
    if len(ps)==1: return ps[0],None,None,suf
    return ps[0], ' '.join(ps[1:-1]) if len(ps)>2 else None, ps[-1], suf

INS = """INSERT OR IGNORE INTO owners (
    full_name, first_name, middle_name, last_name, suffix,
    mailing_address, city, state, zip_code,
    phone_1, phone_2, phone_3, phone_4, phone_5, phone_6,
    phone_1_type, phone_2_type, phone_3_type, phone_4_type, phone_5_type,
    email_1, email_2, email_3, email_4,
    classification, contact_status, dedupe_key,
    data_source, ais_owner_id, age, is_deceased, notes, relatives_json
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

conn = sqlite3.connect(DB)
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-8000")  # Only 8MB cache
conn.execute("PRAGMA journal_mode=WAL")
cur = conn.cursor()
before = cur.execute("SELECT COUNT(*) FROM owners").fetchone()[0]
print(f"contacts_{FNUM}.csv | DB={before:,}")

n = 0; inserted = 0

with open(fp, 'r', encoding='utf-8', errors='replace') as f:
    f.readline()  # skip header

    while True:
        line = f.readline()
        if not line: break
        n += 1
        line = line.strip()
        if not line: continue

        row = parse_csv_line(line)
        if len(row) < 6: continue

        on = row[1]
        if not on: continue

        addr = row[2] or None
        city = row[3] or None
        st = row[4] or None
        zc = row[5] or None
        d = dk(on, addr, city, st, zc)

        # Quick check if already exists (avoid building full tuple)
        cur.execute("SELECT 1 FROM owners WHERE dedupe_key=? LIMIT 1", (d,))
        if cur.fetchone():
            continue

        ph = [cp(row[i]) if i < len(row) and row[i] else None for i in (6,8,10,12,14)]
        pt = [row[i] or None if i < len(row) else None for i in (7,9,11,13,15)]
        em = [ce(row[i]) if i < len(row) and row[i] else None for i in (16,17,18)]

        age = None
        if len(row) > 19 and row[19]:
            try: age = int(float(row[19])); age = age if 0 < age < 131 else None
            except: pass

        isd = 0
        if len(row) > 20: isd = 1 if row[20].upper() in ('TRUE','YES','1') else 0

        fi,mi,la,su = pn(on)
        aid = row[0] or None

        cur.execute(INS, (on,fi,mi,la,su, addr,city,st,zc,
            ph[0],ph[1],ph[2],ph[3],ph[4],None,
            pt[0],pt[1],pt[2],pt[3],pt[4],
            em[0],em[1],em[2],None,
            None,'Not Contacted',d, 'ais_sql_dump',aid,age,isd,None,None))
        inserted += 1

        if inserted % 1000 == 0:
            conn.commit()

        if n % 100000 == 0:
            conn.commit()
            gc.collect()
            print(f"  {n:,} rows, {inserted:,} new")

conn.commit()
after = cur.execute("SELECT COUNT(*) FROM owners").fetchone()[0]
print(f"Done: {n:,} rows → {inserted:,} new ({after:,} total)")
conn.close()
