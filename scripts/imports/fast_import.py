#!/usr/bin/env python3
"""
Ultra-fast import using csv.reader (not DictReader) and line skipping.
Usage: python3 fast_import.py <file_num> [start_line] [chunk_size]
"""
import csv, hashlib, os, re, sqlite3, sys

csv.field_size_limit(10*1024*1024)
REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DB = os.environ.get('DB_PATH', os.path.join(REPO_ROOT, 'database', 'mineral_crm.db'))
EXTRACTED = os.environ.get('AIS_EXTRACTED', os.path.join(REPO_ROOT, '..', 'imports', 'ais', 'extracted_contacts'))

FNUM = int(sys.argv[1])
START = int(sys.argv[2]) if len(sys.argv) > 2 else 0
CHUNK = int(sys.argv[3]) if len(sys.argv) > 3 else 999999999

fp = os.path.join(EXTRACTED, f'contacts_{FNUM}.csv')

# Column indices in extracted files (fixed order from extract_contacts.py):
# 0:Owner_OwnerID 1:OwnerName 2:OwnerAddress 3:OwnerCity 4:OwnerState 5:OwnerZip
# 6:OwnerPhone1 7:OwnerPhone1Type 8:OwnerPhone2 9:OwnerPhone2Type
# 10:OwnerPhone3 11:OwnerPhone3Type 12:OwnerPhone4 13:OwnerPhone4Type
# 14:OwnerPhone5 15:OwnerPhone5Type 16:OwnerEmail1 17:OwnerEmail2 18:OwnerEmail3
# 19:OwnerEstimatedAge 20:IsDeceased

def cp(p):
    if not p: return None
    d = re.sub(r'[^\d]', '', p)
    if len(d)==11 and d[0]=='1': d=d[1:]
    return f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d)==10 else None

def ce(e):
    if not e: return None
    v = e.strip().lower()
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
conn.execute("PRAGMA cache_size=-16000")
cur = conn.cursor()
before = cur.execute("SELECT COUNT(*) FROM owners").fetchone()[0]
print(f"contacts_{FNUM}.csv | skip={START} chunk={CHUNK} | DB={before:,}")

batch=[]; processed=0; line=0

with open(fp, 'r', encoding='utf-8', errors='replace') as f:
    hdr = f.readline()  # skip header

    # Skip lines efficiently
    for _ in range(START):
        f.readline()
        line += 1

    reader = csv.reader(f)
    for row in reader:
        line += 1
        if processed >= CHUNK: break
        processed += 1

        if len(row) < 6: continue
        on = row[1].strip()
        if not on: continue

        addr = row[2].strip() or None
        city = row[3].strip() or None
        st = row[4].strip() or None
        zc = row[5].strip() or None
        d = dk(on, addr, city, st, zc)

        ph = [cp(row[i].strip()) if i<len(row) else None for i in (6,8,10,12,14)]
        pt = [row[i].strip() or None if i<len(row) else None for i in (7,9,11,13,15)]
        em = [ce(row[i].strip()) if i<len(row) else None for i in (16,17,18)]

        age=None
        if len(row)>19 and row[19].strip():
            try: age=int(float(row[19].strip())); age=age if 0<age<131 else None
            except: pass

        isd=0
        if len(row)>20: isd = 1 if row[20].strip().upper() in ('TRUE','YES','1') else 0

        fi,mi,la,su = pn(on)
        aid = row[0].strip() or None

        batch.append((on,fi,mi,la,su, addr,city,st,zc,
            ph[0],ph[1],ph[2],ph[3],ph[4],None,
            pt[0],pt[1],pt[2],pt[3],pt[4],
            em[0],em[1],em[2],None,
            None,'Not Contacted',d, 'ais_sql_dump',aid,age,isd,None,None))

        if len(batch)>=500:
            cur.executemany(INS, batch); conn.commit(); batch=[]

    if batch: cur.executemany(INS, batch); conn.commit()

after = cur.execute("SELECT COUNT(*) FROM owners").fetchone()[0]
print(f"Done: {processed:,} rows → {after-before:,} new ({after:,} total)")
if processed >= CHUNK:
    print(f"NEXT: python3 fast_import.py {FNUM} {START+processed} {CHUNK}")
else:
    print(f"FILE COMPLETE")
conn.close()
