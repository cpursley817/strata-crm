#!/usr/bin/env python3
"""
Enverus Direct Access V3 Query Script
Queries section-level activity for Strata mineral acquisition.

Field names verified directly from Enverus Developer API Portal (March 2026).

Key findings from API docs:
  - NO Section/Township/Range as filter params on any endpoint
  - Filter by County (Parish name) + StateProvince, then match STR in Python
  - STR field in response = "Section-TownshipDir-RangeDir" e.g. "10-12N-13W"
  - County = Parish name in Louisiana (e.g. "DeSoto", "Bossier")
  - StateProvince = state abbreviation (e.g. "LA")
  - Permit data (PermitNumber, PermitType, ApprovedDate) lives in active-rigs response
  - ENVBasin is NOT a reliable REST filter param — use County per-parish queries instead
  - Date range filters use gt(YYYY-MM-DD) syntax, NOT a bare date string

Usage:
  python3 enverus_query.py --section 10-12N-13W --parish DeSoto
  python3 enverus_query.py --test
  python3 enverus_query.py --section 10-12N-13W --parish DeSoto --days 180
  python3 enverus_query.py --basin yes --days 90
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

# ── Config ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATHS = [
    os.path.join(SCRIPT_DIR, 'enverus_config.txt'),
    os.path.join(SCRIPT_DIR, 'enverus_config.txt.txt'),
]
API_BASE = 'https://api.enverus.com/v3/direct-access'
TOKEN_URL = 'https://api.enverus.com/v3/direct-access/tokens'

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_secret_key():
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            with open(path, 'r') as f:
                key = f.read().strip()
            if key:
                return key
    raise FileNotFoundError(
        "enverus_config.txt not found. Create it in the project folder "
        "and paste your Enverus secret key as the only content."
    )

def get_token(secret_key):
    payload = json.dumps({"secretKey": secret_key}).encode('utf-8')
    req = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    token = data.get('token') or data.get('access_token') or data.get('Token')
    if not token:
        raise ValueError(f"No token in response: {data}")
    return token

# ── API GET ───────────────────────────────────────────────────────────────────

def api_get(token, endpoint, params):
    """GET from Enverus API with params, return list of records."""
    qs = urllib.parse.urlencode(params)
    url = f"{API_BASE}/{endpoint}?{qs}"
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode('utf-8')
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get('items') or data.get('results') or data.get('data') or []
        return []

# ── Section Parser ────────────────────────────────────────────────────────────

def parse_section_str(section_str):
    """
    Parse '10-12N-13W' into components.
    The STR format used by Enverus matches our contact section format exactly.
    e.g. contact stores 'DeSoto_10-12N-13W' → section_str = '10-12N-13W'
    """
    section_str = section_str.strip()
    parts = section_str.split('-')
    sec_num = parts[0] if parts else section_str
    return {
        'str': section_str,   # e.g. '10-12N-13W' — matches Enverus STR response field
        'section': sec_num,   # e.g. '10'
    }

# ── Query Functions ───────────────────────────────────────────────────────────

def query_active_rigs(token, parish, str_value):
    """
    Find active rigs in the parish, then filter response by STR field.
    Confirmed filter params: County, StateProvince, ENVBasin, ENVOperator, ENVRegion
    STR is a response field, not a filter param — we filter in Python.
    Response fields: STR, Section, Township, Range, ENVOperator, RigNameNumber,
                     RigType, SpudDate, RigJobStartDate, PermitNumber, PermitType,
                     ApprovedDate, ENVRigID
    """
    try:
        records = api_get(token, 'active-rigs', {
            'County': parish,
            'StateProvince': 'LA',
            'pagesize': 200,
        })
        section_rigs = [r for r in records if r.get('STR', '').upper() == str_value.upper()]
        return records, section_rigs
    except Exception:
        return [], []

def query_well_headers(token, parish, str_value):
    """
    Get well headers for the parish filtered by producing status.
    Confirmed filter params: County, StateProvince, ENVWellStatus, ENVWellType,
                             ENVBasin, ENVOperator, ENVRegion, UpdatedDate
    STR may be in the response — we attempt to filter in Python.
    """
    try:
        all_wells = api_get(token, 'well-headers', {
            'County': parish,
            'StateProvince': 'LA',
            'pagesize': 1000,
        })
        has_str = any('STR' in w for w in all_wells[:10]) if all_wells else False
        section_wells = [w for w in all_wells if w.get('STR', '').upper() == str_value.upper()] if has_str else []
        producing = [w for w in section_wells if 'PRODUC' in w.get('ENVWellStatus', '').upper()]
        parish_producing = [w for w in all_wells if 'PRODUC' in w.get('ENVWellStatus', '').upper()]
        return {
            'all_wells': all_wells,
            'section_wells': section_wells,
            'section_producing': producing,
            'parish_producing': parish_producing,
            'has_str_data': has_str,
        }
    except Exception:
        return {'all_wells': [], 'section_wells': [], 'section_producing': [],
                'parish_producing': [], 'has_str_data': False}

def query_recent_wells(token, parish, str_value, days=90):
    """
    Query well-headers updated within the last N days for the section.
    Uses gt(YYYY-MM-DD) filter syntax for date range — bare date strings do exact match.
    """
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
        records = api_get(token, 'well-headers', {
            'County': parish,
            'StateProvince': 'LA',
            'UpdatedDate': f'gt({cutoff})',
            'pagesize': 500,
        })
        section_recent = [r for r in records if r.get('STR', '').upper() == str_value.upper()]
        return records, section_recent
    except Exception:
        return [], []

# ── Status Classifier ─────────────────────────────────────────────────────────

def classify_status(section_rigs, section_wells, recent_wells):
    if section_rigs:
        return 'RIG ON LOCATION'
    if recent_wells:
        for r in recent_wells:
            status = r.get('ENVWellStatus', '').upper()
            if 'PERMIT' in status:
                return 'PERMITTED'
        return 'RECENT ACTIVITY'
    if section_wells:
        return 'PRODUCING'
    return 'WHITE SPACE'

# ── Main Query ────────────────────────────────────────────────────────────────

def query_section(section_str, parish, days=90):
    """Full section activity query. Returns JSON-serializable dict."""
    try:
        secret_key = get_secret_key()
        token = get_token(secret_key)
    except Exception as e:
        return {"error": str(e)}

    parsed = parse_section_str(section_str)
    str_value = parsed['str']

    all_rigs, section_rigs = query_active_rigs(token, parish, str_value)
    well_data = query_well_headers(token, parish, str_value)
    _, section_recent = query_recent_wells(token, parish, str_value, days)

    status = classify_status(section_rigs, well_data['section_wells'], section_recent)

    # Build rig detail
    rig_detail = None
    if section_rigs:
        r = section_rigs[0]
        rig_detail = {
            'name': r.get('RigNameNumber', 'Unknown'),
            'operator': r.get('ENVOperator', ''),
            'type': r.get('RigType', ''),
            'spud_date': (r.get('SpudDate') or '')[:10],
            'job_start': (r.get('RigJobStartDate') or '')[:10],
            'permit_number': r.get('PermitNumber', ''),
            'permit_type': r.get('PermitType', ''),
            'approved_date': (r.get('ApprovedDate') or '')[:10],
        }

    # Primary operator
    operator = ''
    if section_rigs:
        operator = section_rigs[0].get('ENVOperator', '')
    elif well_data['section_producing']:
        operator = well_data['section_producing'][0].get('ENVOperator', '')
    elif well_data['section_wells']:
        operator = well_data['section_wells'][0].get('ENVOperator', '')
    elif well_data['parish_producing']:
        operator = well_data['parish_producing'][0].get('ENVOperator', '')

    # Last activity date
    last_date = ''
    if section_recent:
        dates = [(r.get('UpdatedDate') or r.get('SpudDate') or '') for r in section_recent]
        dates = [d[:10] for d in dates if d]
        if dates:
            last_date = sorted(dates)[-1]

    return {
        "status": status,
        "str": str_value,
        "parish": parish,
        "operator": operator,
        "rigs_in_section": len(section_rigs),
        "rigs_in_parish": len(all_rigs),
        "wells_in_section": len(well_data['section_wells']),
        "producing_in_section": len(well_data['section_producing']),
        "producing_in_parish": len(well_data['parish_producing']),
        "total_wells_in_parish": len(well_data['all_wells']),
        "recent_activity_count": len(section_recent),
        "last_activity_date": last_date,
        "has_str_data": well_data['has_str_data'],
        "rig_detail": rig_detail,
    }

# ── Record Trimmers ───────────────────────────────────────────────────────────

def _build_str(r):
    """
    Build a Section-Township-Range string from whatever location fields exist.
    Tries STR combined field first, then constructs from components.
    """
    # Combined field (confirmed on active-rigs)
    if r.get('STR'):
        return r['STR']
    # Component fields — multiple naming conventions across endpoints
    sec  = r.get('Section')       or r.get('SectionNumber') or r.get('Sec')  or ''
    twp  = r.get('Township')      or r.get('TownshipNumber') or r.get('Twp') or ''
    tdir = r.get('TownshipDirection') or r.get('TwnshpDir') or r.get('TwpDir') or ''
    rng  = r.get('Range')         or r.get('RangeNumber')   or r.get('Rng')  or ''
    rdir = r.get('RangeDirection') or r.get('RangeDir')     or r.get('RngDir') or ''
    if sec and twp:
        return f"{sec}-{twp}{tdir}-{rng}{rdir}".strip('-')
    return ''

def _first(*vals):
    """Return the first non-empty value from a list of candidates."""
    for v in vals:
        if v:
            return str(v)[:10] if isinstance(v, str) and len(v) > 10 and '-' in str(v) else str(v)
    return ''

def _date(*vals):
    """Return the first non-empty date value, truncated to YYYY-MM-DD."""
    for v in vals:
        if v:
            return str(v)[:10]
    return ''

def _trim_rig(r):
    """Return only the fields needed for the basin detail table."""
    return {
        'operator':    r.get('ENVOperator', '') or r.get('Operator', ''),
        'parish':      r.get('County', ''),
        'str':         _build_str(r),
        'rig':         r.get('RigNameNumber', '') or r.get('RigName', '') or r.get('Rig', ''),
        'spud':        _date(r.get('SpudDate'), r.get('RigJobStartDate')),
        'permit':      r.get('PermitNumber', '') or r.get('StatePermitNumber', ''),
        'permit_type': r.get('PermitType', '') or r.get('WellType', '') or r.get('ENVWellType', ''),
        'approved':    _date(r.get('ApprovedDate'), r.get('PermitDate'), r.get('PermitApprovedDate')),
        'play':        r.get('ENVPlay', '') or r.get('Play', '') or r.get('Formation', '') or r.get('FormationAtTD', ''),
        'sort_date':   _date(r.get('SpudDate'), r.get('RigJobStartDate'), r.get('ApprovedDate')),
    }

def _trim_well(w):
    """Return only the fields needed for the basin detail table."""
    well_id = (w.get('WellName') or w.get('WellNameNumber') or w.get('ENVWellName')
               or w.get('API14') or w.get('API10') or w.get('APINumber') or '')
    permit_date = _date(
        w.get('PermitDate'), w.get('ApprovedDate'), w.get('PermitApprovedDate'),
        w.get('ApprovalDate'), w.get('StatePermitDate'),
    )
    completion_date = _date(
        w.get('CompletionDate'), w.get('FirstProductionDate'),
        w.get('CompletedDate'), w.get('PerfDate'),
    )
    # Best date for sorting this record
    sort_date = _date(
        w.get('PermitDate'), w.get('CompletionDate'), w.get('SpudDate'),
        w.get('ApprovedDate'), w.get('UpdatedDate'),
    )
    return {
        'operator':        w.get('ENVOperator', '') or w.get('Operator', ''),
        'parish':          w.get('County', ''),
        'str':             _build_str(w),
        'well_name':       well_id,
        'status':          w.get('ENVWellStatus', '') or w.get('WellStatus', ''),
        'play':            w.get('ENVPlay', '') or w.get('Play', '') or w.get('Formation', '') or w.get('FormationAtTD', ''),
        'permit_num':      w.get('PermitNumber', '') or w.get('StatePermitNumber', ''),
        'permit_type':     w.get('PermitType', '') or w.get('WellType', '') or w.get('ENVWellType', ''),
        'permit_date':     permit_date,
        'completion_date': completion_date,
        'spud':            _date(w.get('SpudDate')),
        'updated':         _date(w.get('UpdatedDate')),
        'sort_date':       sort_date,
    }

# ── Basin Query ───────────────────────────────────────────────────────────────

# Louisiana parishes that make up the Haynesville Basin play area
HAYNESVILLE_PARISHES = [
    'DeSoto', 'Red River', 'Caddo', 'Bossier',
    'Natchitoches', 'Bienville', 'Sabine',
]

def query_basin(days=90):
    """
    Haynesville Basin-wide stats for the home page dashboard.

    Strategy: query each of the 7 Haynesville parishes using the verified
    County + StateProvince filter (ENVBasin is not a reliable REST filter param).
    Date filters use gt(YYYY-MM-DD) syntax — bare dates do exact match only.
    """
    try:
        secret_key = get_secret_key()
        token = get_token(secret_key)
    except Exception as e:
        return {"error": str(e)}

    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')

        all_rigs = []
        recent_wells_all = []

        for parish in HAYNESVILLE_PARISHES:
            # Active rigs per parish (no date filter needed — active-rigs is live)
            try:
                parish_rigs = api_get(token, 'active-rigs', {
                    'County': parish,
                    'StateProvince': 'LA',
                    'pagesize': 500,
                })
                all_rigs.extend(parish_rigs)
            except Exception:
                pass

            # Recent well activity per parish using gt() date syntax
            try:
                parish_recent = api_get(token, 'well-headers', {
                    'County': parish,
                    'StateProvince': 'LA',
                    'UpdatedDate': f'gt({cutoff})',
                    'pagesize': 500,
                })
                recent_wells_all.extend(parish_recent)
            except Exception:
                pass

        active_rig_count = len(all_rigs)

        # Unique operators from active rigs, with per-operator rig counts
        op_counts = {}
        for r in all_rigs:
            op = r.get('ENVOperator', '')
            if op:
                op_counts[op] = op_counts.get(op, 0) + 1
        operators_list = sorted(
            [{'name': k, 'rigs': v} for k, v in op_counts.items()],
            key=lambda x: -x['rigs']
        )
        operators = [o['name'] for o in operators_list]

        # Permits and completions from recent well activity window
        permits = [w for w in recent_wells_all
                   if 'PERMIT' in w.get('ENVWellStatus', '').upper()]
        completions = [w for w in recent_wells_all
                       if 'COMPLET' in w.get('ENVWellStatus', '').upper()]
        producing_recent = [w for w in recent_wells_all
                            if 'PRODUC' in w.get('ENVWellStatus', '').upper()]

        # Sort each list most-recent-first before trimming
        def _sort_key_well(w):
            return _date(w.get('PermitDate'), w.get('CompletionDate'),
                         w.get('SpudDate'), w.get('ApprovedDate'), w.get('UpdatedDate'))
        def _sort_key_rig(r):
            return _date(r.get('SpudDate'), r.get('RigJobStartDate'), r.get('ApprovedDate'))

        all_rigs.sort(key=_sort_key_rig, reverse=True)
        permits.sort(key=_sort_key_well, reverse=True)
        completions.sort(key=_sort_key_well, reverse=True)
        producing_recent.sort(key=_sort_key_well, reverse=True)
        recent_wells_all.sort(key=_sort_key_well, reverse=True)

        return {
            "active_rigs":      active_rig_count,
            "rigs_list":        [_trim_rig(r) for r in all_rigs],
            "recent_permits":   len(permits),
            "permits_list":     [_trim_well(w) for w in permits],
            "new_completions":  len(completions),
            "completions_list": [_trim_well(w) for w in completions],
            "producing_wells":  len(producing_recent),
            "producing_list":   [_trim_well(w) for w in producing_recent],
            "total_wells":      len(recent_wells_all),
            "wells_list":       [_trim_well(w) for w in recent_wells_all],
            "operator_count":   len(operators),
            "operators_list":   operators_list,
            "top_operators":    operators[:6],
            "days":             days,
            "updated":          datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        }
    except Exception as e:
        return {"error": str(e)}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    arg_map = {}
    i = 0
    while i < len(args):
        if args[i].startswith('--') and i + 1 < len(args):
            arg_map[args[i][2:]] = args[i+1]
            i += 2
        else:
            i += 1

    if 'test' in arg_map or '--test' in args:
        try:
            key = get_secret_key()
            token = get_token(key)
            print(json.dumps({"status": "AUTH_OK", "token_length": len(token)}))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        return

    # Debug: dump all field names + sample values from first record of each endpoint
    # Usage: python3 enverus_query.py --debug-fields yes --parish DeSoto
    if 'debug-fields' in arg_map:
        parish = arg_map.get('parish', 'DeSoto')
        try:
            key = get_secret_key()
            token = get_token(key)
            cutoff = (datetime.utcnow() - timedelta(days=90)).strftime('%Y-%m-%d')
            out = {}
            for ep, params in [
                ('active-rigs',  {'County': parish, 'StateProvince': 'LA', 'pagesize': 5}),
                ('well-headers', {'County': parish, 'StateProvince': 'LA', 'UpdatedDate': f'gt({cutoff})', 'pagesize': 5}),
            ]:
                records = api_get(token, ep, params)
                if records:
                    out[ep] = {
                        'field_names': sorted(records[0].keys()),
                        'sample': records[0],
                    }
                else:
                    out[ep] = {'field_names': [], 'sample': {}}
            print(json.dumps(out, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        return

    if 'basin' in arg_map or '--basin' in args:
        days = int(arg_map.get('days', '90'))
        result = query_basin(days)
        print(json.dumps(result))
        return

    section_str = arg_map.get('section', '')
    parish = arg_map.get('parish', '')
    days = int(arg_map.get('days', '90'))

    if not section_str or not parish:
        print(json.dumps({"error": "--section, --parish, --basin, or --test required"}))
        return

    result = query_section(section_str, parish, days)
    print(json.dumps(result))

if __name__ == '__main__':
    main()
