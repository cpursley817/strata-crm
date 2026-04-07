#!/usr/bin/env python3
"""
AIS Contact Import — Uses pre-extracted contact CSVs for low memory usage.
Run extract_contacts.py first to create the small contact-only CSV files.
"""

import csv, hashlib, os, re, shutil, sqlite3, gc

csv.field_size_limit(10*1024*1024)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIS = os.path.join(os.path.dirname(BASE), 'imports', 'ais')
DB = os.path.join(BASE, 'database', 'mineral_crm.db')
CD = os.path.join(AIS, 'AIS_Contact Directory.csv')
EXTRACTED = os.path.join(AIS, 'extracted_contacts')
CONTACT_FILES = [os.path.join(EXTRACTED, f'contacts_{i}.csv') for i in range(1, 5)]


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


def setup(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(owners)")
    ex = {r[1] for r in cur.fetchall()}
    for c,t in [('data_source',"TEXT DEFAULT 'unknown'"),('ais_owner_id','TEXT'),
                ('latitude','REAL'),('longitude','REAL'),('age','INTEGER'),
                ('is_deceased','INTEGER DEFAULT 0'),('phone_1_type','TEXT'),
                ('phone_2_type','TEXT'),('phone_3_type','TEXT'),('phone_4_type','TEXT'),
                ('phone_5_type','TEXT'),('notes','TEXT'),('relatives_json','TEXT')]:
        if c not in ex:
            try: cur.execute(f"ALTER TABLE owners ADD COLUMN {c} {t}"); print(f"  +{c}")
            except: pass

    cur.execute("SELECT COUNT(*) FROM owners"); old=cur.fetchone()[0]
    print(f"Clearing {old:,} old owners...")
    for t in ['activities','ownership_links','owner_aliases','deals','deal_stage_history','files','owners']:
        cur.execute(f"DELETE FROM {t}")
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('owners','ownership_links','owner_aliases','deals','deal_stage_history','activities','files')")
    cur.execute("UPDATE sections SET people_count=0")
    cur.execute("DROP INDEX IF EXISTS idx_owners_dedupe")
    cur.execute("DROP INDEX IF EXISTS idx_owners_dedupe_unique")
    cur.execute("CREATE UNIQUE INDEX idx_owners_dedupe_unique ON owners(dedupe_key)")
    conn.commit()
    print("Ready.\n")


def phase1(conn):
    """Import AIS Contact Directory (13.7K)."""
    print("Phase 1: Contact Directory")
    cur = conn.cursor()
    batch = []; n=0

    with open(CD, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = cs(row.get('Owner Name',''))
            if not fn: continue
            n += 1
            addr = cs(row.get('Address2','')) or cs(row.get('Address',''))
            city = cs(row.get('City3','')) or cs(row.get('City',''))
            st = cs(row.get('State4','')) or cs(row.get('State',''))
            zc = cs(row.get('Zip Code5','')) or cs(row.get('Zip Code',''))
            d = dk(fn, addr, city, st, zc)
            ph = [cp(row.get(f'PhoneNumber0{i}','')) for i in range(1,6)]
            em = [ce(row.get(f'EmailAddress0{i}','')) for i in range(1,3)]
            age=None
            try: age=int(row.get('age','').strip()); age=age if 0<age<131 else None
            except: pass
            isd = 1 if (row.get('IsDeceased','') or '').upper()=='TRUE' else 0
            fi = cs(row.get('First_name','')); la = cs(row.get('Last_Name',''))

            batch.append((fn,fi,None,la,None, addr,city,st,zc,
                ph[0],ph[1],ph[2],ph[3],ph[4],None, None,None,None,None,None,
                em[0],em[1] if len(em)>1 else None,None,None,
                None,'Not Contacted',d, 'ais_contact_directory',None,age,isd,None,None))

            if len(batch)>=2000:
                cur.executemany(INS, batch); batch=[]

        if batch: cur.executemany(INS, batch)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM owners"); ct=cur.fetchone()[0]
    print(f"  {n:,} rows → {ct:,} unique owners\n")
    return ct


def phase2(conn):
    """Import pre-extracted contact CSVs from SQL dumps."""
    print("Phase 2: Extracted SQL Dump Contacts")
    cur = conn.cursor()
    total_added = 0

    for cfile in CONTACT_FILES:
        fname = os.path.basename(cfile)
        if not os.path.exists(cfile):
            print(f"  {fname}: NOT FOUND"); continue

        print(f"  {fname}...")
        cur.execute("SELECT COUNT(*) FROM owners"); before=cur.fetchone()[0]
        batch=[]; n=0

        with open(cfile, 'r', encoding='utf-8', errors='replace') as f:
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

                if len(batch)>=3000:
                    cur.executemany(INS, batch); batch=[]
                    if n % 100000 == 0:
                        conn.commit()
                        cur.execute("SELECT COUNT(*) FROM owners"); now=cur.fetchone()[0]
                        print(f"    {n:,} → {now-before:,} new")

            if batch: cur.executemany(INS, batch)
        conn.commit()
        gc.collect()

        cur.execute("SELECT COUNT(*) FROM owners"); after=cur.fetchone()[0]
        added = after - before; total_added += added
        print(f"    {n:,} rows → {added:,} new owners")

    print(f"\n  SQL dump total: {total_added:,}")
    return total_added


def validate(conn):
    print(f"\n{'='*60}")
    print("VALIDATION")
    print(f"{'='*60}")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM owners"); total=cur.fetchone()[0]
    print(f"\nTotal owners: {total:,}")

    cur.execute("SELECT data_source, COUNT(*) FROM owners GROUP BY data_source ORDER BY COUNT(*) DESC")
    print("\nBy source:")
    for r in cur.fetchall(): print(f"  {r[0]}: {r[1]:,}")

    p = lambda x: f"{100*x/total:.1f}%" if total else "0%"
    print("\nCompleteness:")
    for l,w in [("Phone","phone_1 IS NOT NULL"),("Email","email_1 IS NOT NULL"),
                ("Address","mailing_address IS NOT NULL"),("Age","age IS NOT NULL"),
                ("Deceased","is_deceased=1"),("Relatives","relatives_json IS NOT NULL")]:
        cur.execute(f"SELECT COUNT(*) FROM owners WHERE {w}"); n=cur.fetchone()[0]
        print(f"  {l:12s} {n:>10,} ({p(n)})")

    cur.execute("SELECT state, COUNT(*) c FROM owners WHERE state IS NOT NULL GROUP BY state ORDER BY c DESC LIMIT 15")
    print("\nTop 15 states:")
    for r in cur.fetchall(): print(f"  {r[0]}: {r[1]:,}")

    print("\nSample Contact Directory records:")
    cur.execute("SELECT owner_id,full_name,city,state,phone_1,email_1 FROM owners WHERE data_source='ais_contact_directory' LIMIT 3")
    for r in cur.fetchall(): print(f"  [{r[0]}] {r[1]} | {r[2]},{r[3]} | {r[4]} | {r[5]}")

    print("\nSample SQL Dump records:")
    cur.execute("SELECT owner_id,full_name,city,state,phone_1,email_1 FROM owners WHERE data_source='ais_sql_dump' LIMIT 3")
    for r in cur.fetchall(): print(f"  [{r[0]}] {r[1]} | {r[2]},{r[3]} | {r[4]} | {r[5]}")

    cur.execute("SELECT COUNT(*) FROM sections"); print(f"\nSections: {cur.fetchone()[0]:,}")
    print(f"{'='*60}\nDone. Next: pay deck import for ownership links.\n{'='*60}")


def main():
    print("="*60)
    print("AIS CONTACT IMPORT")
    print("="*60)

    # Check extracted files exist
    for f in CONTACT_FILES:
        if not os.path.exists(f):
            print(f"ERROR: {f} not found. Run extract_contacts.py first!")
            return

    bk = DB + '.backup_before_ais'
    if not os.path.exists(bk): shutil.copy2(DB, bk); print(f"Backup: {os.path.basename(bk)}")

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=MEMORY")

    try:
        setup(conn)
        c1 = phase1(conn)
        c2 = phase2(conn)
        print(f"\nGrand total: {c1+c2:,}")
        conn.execute("PRAGMA foreign_keys=ON")
        validate(conn)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback; traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
