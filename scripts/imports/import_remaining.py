#!/usr/bin/env python3
"""Continue importing remaining extracted contact files into existing DB."""
import csv, hashlib, os, re, sqlite3, gc, sys

csv.field_size_limit(10*1024*1024)

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DB = os.environ.get('DB_PATH', os.path.join(REPO_ROOT, 'database', 'mineral_crm.db'))
EXTRACTED = os.environ.get('AIS_EXTRACTED', os.path.join(REPO_ROOT, '..', 'imports', 'ais', 'extracted_contacts'))

# Process just one file at a time — pass file number as arg
FILE_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 0

def cp(phone):
    if not phone or not phone.strip(): return None
    d = re.sub(r'[^\d]', '', phone.strip())
    if len(d)==11 and d[0]=='1': d=d[1:]
    return f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d)==10 else None

def ce(email):
    if not email or not email.strip(): return None
    e = email.strip().lower()
    return e if '@' in e and '.' in e else None

def cs(v):
    return v.strip() if v and v.strip() else None

def dk(name, addr='', city='', st='', z=''):
    n = re.sub(r'\s+', ' ', (name or '').upper().strip())
    n = re.sub(r'\b(JR|SR|III|II|IV)\b\.?', '', n).strip(' ,.')
    p = [n, (addr or '').upper().strip(), (city or '').upper().strip(),
         (st or '').upper().strip(), (z or '').strip()[:5]]
    return hashlib.md5('|'.join(p).encode()).hexdigest()

def pn(fn):
    if not fn: return None,None,None,None
    name = fn.strip(); suf=None
    m = re.search(r'\b(JR|SR|III|II|IV)\b\.?\s*$', name, re.I)
    if m: suf=m.group(1).upper(); name=name[:m.start()].strip(' ,')
    ps = name.split()
    if not ps: return fn,None,None,suf
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

def import_file(conn, filepath):
    fname = os.path.basename(filepath)
    print(f"Importing {fname}...")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM owners"); before=cur.fetchone()[0]
    batch=[]; n=0

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n += 1
            on = cs(row.get('OwnerName',''))
            if not on: continue

            aid = cs(row.get('Owner_OwnerID',''))
            addr = cs(row.get('OwnerAddress',''))
            city = cs(row.get('OwnerCity',''))
            st = cs(row.get('OwnerState',''))
            zc = cs(row.get('OwnerZip',''))
            d = dk(on, addr, city, st, zc)

            phones = [cp(row.get(f'OwnerPhone{i}','')) for i in range(1,6)]
            ptypes = [cs(row.get(f'OwnerPhone{i}Type','')) for i in range(1,6)]
            emails = [ce(row.get(f'OwnerEmail{i}','')) for i in range(1,4)]

            age=None
            try: age=int(float(row.get('OwnerEstimatedAge','').strip())); age=age if 0<age<131 else None
            except: pass
            isd = 1 if row.get('IsDeceased','').strip().upper() in ('TRUE','YES','1') else 0
            fi,mi,la,su = pn(on)

            batch.append((on,fi,mi,la,su, addr,city,st,zc,
                phones[0],phones[1],phones[2],phones[3],phones[4],None,
                ptypes[0],ptypes[1],ptypes[2],ptypes[3],ptypes[4],
                emails[0],emails[1],emails[2],None,
                None,'Not Contacted',d, 'ais_sql_dump',aid,age,isd,None,None))

            if len(batch)>=2000:
                cur.executemany(INS, batch); batch=[]
                if n % 100000 == 0:
                    conn.commit(); gc.collect()
                    cur.execute("SELECT COUNT(*) FROM owners"); now=cur.fetchone()[0]
                    print(f"  {n:,} → {now-before:,} new")

        if batch: cur.executemany(INS, batch)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM owners"); after=cur.fetchone()[0]
    print(f"  {fname}: {n:,} rows → {after-before:,} new ({after:,} total)\n")
    gc.collect()

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=OFF")
conn.execute("PRAGMA cache_size=-32000")
conn.execute("PRAGMA synchronous=OFF")

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM owners"); print(f"Starting with {cur.fetchone()[0]:,} owners\n")

if FILE_NUM > 0:
    # Import specific file
    f = os.path.join(EXTRACTED, f'contacts_{FILE_NUM}.csv')
    import_file(conn, f)
else:
    # Import all
    for i in range(1, 5):
        f = os.path.join(EXTRACTED, f'contacts_{i}.csv')
        if os.path.exists(f):
            import_file(conn, f)

cur.execute("SELECT COUNT(*) FROM owners"); total=cur.fetchone()[0]
print(f"Final total: {total:,} owners")
cur.execute("SELECT data_source, COUNT(*) FROM owners GROUP BY data_source")
for r in cur.fetchall(): print(f"  {r[0]}: {r[1]:,}")
conn.close()
