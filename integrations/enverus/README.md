# Enverus Integration

## Overview
Connects to Enverus V3 Direct Access REST API for real-time basin activity data. Provides active rig counts, recent permits, completions, and well activity for the Haynesville basin (expandable to other basins).

## Files
- `enverus_query.py` — Core API query script with basin stats and detail data
- `Enverus_API_Research.md` — API field documentation, verified parameters, known issues

## Key Details
- **Auth**: Bearer token via secret key exchange
- **Endpoints**: `active-rigs`, `well-headers`
- **Filter strategy**: Per-parish queries using `County` filter (not `ENVBasin`)
- **Haynesville parishes**: DeSoto, Red River, Caddo, Bossier, Natchitoches, Bienville, Sabine

## Pending
- Run `--debug-fields` on user machine to confirm exact API field names
- Some detail table columns may be empty until field names are verified
