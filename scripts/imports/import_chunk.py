#!/usr/bin/env python3
"""
Import a single extracted contacts file in chunks.
Usage: python3 import_chunk.py <file_num> <start_line> <chunk_size>
Example: python3 import_chunk.py 3 0 100000
"""
import csv, hashlib, os, re, sqlite3, sys

csv.field_size_limit(10*1024*1024)
REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DB = os.environ.get('DB_PATH', os.path.join(REPO_ROOT, 'database', 'mineral_crm.db'))
EXTRACTED = os.environ.get('AIS_EXTRACTED', os.path.join(REPO_ROOT, '..', 'imports', 'ais', 'extracted_contacts'))

FNUM = int(sys.argv[1])
START = int(sys.argv[2]) if len(sys.argv) > 2 else 0
CHUNK = int(sys.argv[3]) if len(sys.argv) > 3 else 100000

filepath = os.path.join(EXTRACTED, f'contacts_{FNUM}.csv')

def cp(p):
    if not p or not p.strip(): return None
    d = re.sub(r'[^\d]', '', p.strip())
    if len(d)==11 and d[0]=='1': d=d[1:]
    return f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d)==10 else None

def ce(e):
    if not e or not e.strip(): return None
    v = e.strip().lower()
    return v if '@' in v and '.' in v else None

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

conn = sqlite3.connect(DB)
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-16000")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM owners"); before=cur.fetchone()[0]

print(f"File: contacts_{FNUM}.csv | Start: {START} | Chunk: {CHUNK} | DB has {before:,} owners")

batch=[]; n=0; processed=0

with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        n += 1
        if n <= START: continue
        if processed >= CHUNK: break
        processed += 1

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

        if len(batch)>=1000:
            cur.executemany(INS, batch); conn.commit(); batch=[]

    if batch: cur.executemany(INS, batch); conn.commit()

cur.execute("SELECT COUNT(*) FROM owners"); after=cur.fetchone()[0]
print(f"Processed {processed:,} rows (lines {START+1}-{START+processed}) → {after-before:,} new ({after:,} total)")
print(f"NEXT: python3 import_chunk.py {FNUM} {START+processed} {CHUNK}")
conn.close()
