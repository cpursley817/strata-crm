# Enverus Developer API — Research Notes
*Saved: March 2026 | Last Updated: March 13, 2026 | For Strata CRM — Haynesville Acquisitions*

---

## ✅ Integration Status

| Component | Status |
|-----------|--------|
| API field names verified via live portal | **DONE** |
| enverus_query.py rewritten with correct fields | **DONE** |
| /enverus-section endpoint in server.ps1 | **DONE** |
| /enverus-basin endpoint in server.ps1 | **DONE** |
| Section Activity panel in contact profiles | **DONE** |
| Haynesville Basin stats widget on Home page | **DONE** |
| Scheduled nightly cache sync | pending |
| Contact enrichment tagging in contacts_v2.json | pending |

---

## What is Enverus?

Enverus (formerly Drillinginfo) is the oil and gas industry's dominant data platform. It aggregates regulatory, production, permit, and well data from every state and provides programmatic access via its Developer API. For Haynesville Basin mineral acquisition, it's the single most valuable data source available.

**GitHub:** https://github.com/enverus-ea/enverus-developer-api
**API Explorer:** https://app.enverus.com (requires account)
**Provisioning/Keys:** https://app.enverus.com (developer portal)

---

## Authentication — V3 Direct Access REST API

```python
import requests

def get_token(secret_key):
    resp = requests.post(
        'https://api.enverus.com/v3/direct-access/tokens',
        json={'secretKey': secret_key}
    )
    return resp.json()['token']   # Bearer token, valid 8 hours
```

**Secret key** is generated at the Enverus provisioning portal (app.enverus.com).

---

## ⚠️ Critical Field Name Findings (Verified March 2026 via Live Portal)

These were verified by navigating the live Enverus Developer API portal directly. Previous assumptions were wrong.

### CORRECT Filter Parameters

| Parameter | Correct Form | Notes |
|-----------|-------------|-------|
| Parish/County | `County` | Capital C — lowercase `county` does NOT work |
| State | `StateProvince` | Capital S+P — lowercase `stateProvince` does NOT work |
| Basin | `ENVBasin` | e.g., `HAYNESVILLE` |
| Well status | `ENVWellStatus` | Enverus-normalized status |
| Play | `ENVPlay` | |
| Region | `ENVRegion` | |
| Date filter | `UpdatedDate` | For recency filtering on wells |

### WRONG Parameters (do NOT use these)

These do not exist in the V3 API and will return no results or errors:
- `twnshpNo`, `twnshpDir`, `rangNo`, `rangDir`, `section` — no section-level location filters exist
- `stateProvince` (lowercase) — wrong case
- `county` (lowercase) — wrong case

### The STR Field (Critical)

- **`STR`** is a **response field** (not a filter parameter) — format: `"10-12N-13W"` (Section-Township-Range combined)
- To find section-specific data: filter by `County` + `StateProvince`, then match `STR` in Python
- Contact section format matches STR format exactly — direct string comparison works

---

## Endpoints Used in Strata

### active-rigs
```python
GET /v3/direct-access/active-rigs
Params: County=DeSoto, StateProvince=LA, pagesize=500
```
Response fields confirmed: `STR`, `Section`, `Township`, `Range`, `ENVOperator`, `RigNameNumber`, `RigType`, `SpudDate`, `RigJobStartDate`, `PermitNumber`, `PermitType`, `ApprovedDate`

**Note:** Permit data lives here — there is NO separate permits endpoint.

### well-headers
```python
GET /v3/direct-access/well-headers
Params: County=DeSoto, StateProvince=LA, UpdatedDate=gt(2024-01-01), pagesize=1000
```
No section-level location filter — must post-filter by STR in Python.

### Basin-wide query
```python
GET /v3/direct-access/active-rigs
Params: ENVBasin=HAYNESVILLE, StateProvince=LA, pagesize=500
```
Returns all active Haynesville rigs across all Louisiana parishes.

---

## enverus_query.py — Current Implementation

**Location:** `Contact Management System/enverus_query.py`

### Section Query Logic
```python
# 1. Filter by County + StateProvince (no section-level filter exists)
rigs = api_get(token, 'active-rigs', {'County': parish, 'StateProvince': 'LA'})
wells = api_get(token, 'well-headers', {'County': parish, 'StateProvince': 'LA'})

# 2. Match STR in Python (e.g., "10-12N-13W")
section_rigs = [r for r in rigs if r.get('STR','') == section_str]
```

### CLI Usage
```bash
# Section-level query
python3 enverus_query.py --section 10-12N-13W --parish DeSoto

# Haynesville basin stats (for home page dashboard)
python3 enverus_query.py --basin yes --days 90

# Auth test only
python3 enverus_query.py --test
```

### Output Format (flat JSON — no summary wrapper)
```json
{
  "status": "RIG ON LOCATION",
  "operator": "Comstock Resources",
  "rigs_in_section": 1,
  "wells_in_section": 3,
  "last_spud": "2025-11-15",
  "permit_number": "12345",
  "permit_type": "horizontal",
  "permit_date": "2025-09-01",
  "total_wells_in_parish": 412
}
```

### Section Status Levels (priority order)
1. **RIG ON LOCATION** — active rig on section right now (red highlight)
2. **PERMITTED** — permit approved, rig not yet on location (amber)
3. **RECENT ACTIVITY** — wells spudded within `--days` threshold (blue)
4. **PRODUCING** — known producing wells (green)
5. **WHITE SPACE** — no Enverus data for this section (gray)

---

## Core Data Available

| Dataset | What It Contains | Haynesville Relevance |
|---------|-----------------|----------------------|
| **active-rigs** | Active rigs, operator, spud dates, permits, STR location | Know which sections have drilling RIGHT NOW + permit data |
| **well-headers** | Well records, county, operator, spud date, status | Active/completed wells on target sections |
| **production** | Monthly production by well (gas, oil, water) | Calculate royalty income potential for offer pricing |
| **acreage** | Lease data, expiration dates, operator | Operators assembling acreage near targets |

---

## Haynesville-Specific Use Cases

### 1. Active Section Intelligence (Highest Priority)
Run `enverus_query.py --section X-YN-ZW --parish DeSoto` from the Section Activity panel on any contact's profile. Tells you immediately whether a rig is on location before you call.

### 2. Haynesville Basin Dashboard (Home Page)
Run `enverus_query.py --basin yes` to get rig count, recent spuds, permits, and top operators across all of Louisiana Haynesville. Displays as live widget on the Strata Home tab.

### 3. Well Production — Inform Offer Pricing (Future)
```python
# Filter by county, post-filter by STR, pull production data
wells = api_get(token, 'well-headers', {'County': parish, 'StateProvince': 'LA', 'ENVWellStatus': 'PRODUCING'})
```

### 4. Scheduled Contact Enrichment (Future)
Nightly script tags contacts in contacts_v2.json with:
- `has_active_permit`: true/false
- `active_rig_on_section`: true/false
- `last_spud_date`: ISO date string

---

## server.ps1 Endpoints

### /enverus-section
```
GET /enverus-section?section=10-12N-13W&parish=DeSoto
```
Runs `python3 enverus_query.py --section {section} --parish {parish}` and returns JSON.

**JSON fix:** Removed `2>&1` — only stdout captured. Secondary filter extracts only lines starting with `{` to prevent Windows path stderr from corrupting JSON response.

### /enverus-basin
```
GET /enverus-basin?days=90
```
Runs `python3 enverus_query.py --basin yes --days {days}` and returns Haynesville stats JSON. Same JSON-only filtering applied.

---

## Setup Requirements

```bash
pip install requests   # standard — usually already installed
```

**Config:** Add your Enverus secret key to `enverus_config.txt` in the Contact Management System folder:
```
ENVERUS_SECRET_KEY=your_secret_key_here
```

**Note:** The VM sandbox blocks outbound API calls — the script must run on the user's Windows machine via server.ps1. Running `--test` from inside the VM will return 403.

---

## Cost Consideration

Enverus is a paid enterprise platform. Pricing is subscription-based, typically $5,000–$20,000+/year depending on data access tier. Developer API access is included with data subscriptions. BBR already has an active account.

---

## Key Decisions & Rationale

1. **County + StateProvince filter, then STR post-filter in Python:** No section-level location filter params exist in V3. This is the only viable approach.
2. **active-rigs for permits:** Enverus has no standalone permits endpoint — permit data comes through the active-rigs response.
3. **Flat JSON output (no summary wrapper):** Server passes Python stdout straight through; JS reads `data.status`, `data.operator`, etc. directly.
4. **Remove `2>&1` from PowerShell exec:** Prevents Windows path output (e.g., `C:\Users\...`) on Python stderr from being captured alongside JSON and breaking `JSON.parse`.
5. **Section Activity deferred when server offline:** The panel shows "Server offline — start server.ps1" gracefully rather than breaking the contact profile view.
