#!/usr/bin/env python3
"""
Step 1: Extract only contact columns from SQL dumps into small CSV files.
This drastically reduces file size so the import step doesn't OOM.
"""
import csv, os, sys

csv.field_size_limit(10*1024*1024)

AIS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'imports', 'ais')
AIS = os.path.normpath(AIS)
OUT = os.path.join(AIS, 'extracted_contacts')
os.makedirs(OUT, exist_ok=True)

NEEDED = ['Owner_OwnerID','OwnerName','OwnerAddress','OwnerCity','OwnerState','OwnerZip',
          'OwnerPhone1','OwnerPhone1Type','OwnerPhone2','OwnerPhone2Type',
          'OwnerPhone3','OwnerPhone3Type','OwnerPhone4','OwnerPhone4Type',
          'OwnerPhone5','OwnerPhone5Type','OwnerEmail1','OwnerEmail2','OwnerEmail3',
          'OwnerEstimatedAge','IsDeceased']

for i in range(1, 5):
    src = os.path.join(AIS, f'SQLDump{i}.csv')
    dst = os.path.join(OUT, f'contacts_{i}.csv')
    print(f"Extracting SQLDump{i}.csv → contacts_{i}.csv ...")

    if not os.path.exists(src):
        print(f"  NOT FOUND"); continue

    seen_ids = set()
    written = 0; total = 0

    with open(src, 'r', encoding='utf-8', errors='replace') as fin, \
         open(dst, 'w', newline='', encoding='utf-8') as fout:

        reader = csv.reader(fin)
        hdr = next(reader)
        ci = {h.strip(): idx for idx, h in enumerate(hdr)}

        # Get indices
        indices = []
        for col in NEEDED:
            if col in ci:
                indices.append(ci[col])
            else:
                print(f"  WARNING: column {col} not found!")
                indices.append(-1)

        writer = csv.writer(fout)
        writer.writerow(NEEDED)
        ncols = len(hdr)

        for row in reader:
            total += 1
            if len(row) < ncols:
                row.extend([''] * (ncols - len(row)))

            # Dedup by OwnerID within this file
            oid = row[indices[0]].strip()
            if not oid or oid in seen_ids:
                continue
            seen_ids.add(oid)

            # Skip if no name
            name = row[indices[1]].strip()
            if not name:
                continue

            out_row = []
            for idx in indices:
                if idx >= 0 and idx < len(row):
                    out_row.append(row[idx].strip())
                else:
                    out_row.append('')

            writer.writerow(out_row)
            written += 1

            if total % 500000 == 0:
                print(f"    {total:,} rows → {written:,} unique contacts")

    del seen_ids
    print(f"  Done: {total:,} rows → {written:,} unique contacts")
    sz = os.path.getsize(dst) / (1024*1024)
    print(f"  Output size: {sz:.1f} MB\n")

print("Extraction complete. Files in:", OUT)
