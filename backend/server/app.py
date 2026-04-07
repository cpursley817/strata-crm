"""
Strata CRM — Flask Backend API
Serves the CRM frontend and provides REST endpoints for all data operations.
"""
import os
import sys
import sqlite3
import secrets
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory, g
from flask_cors import CORS
import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'strata.db')
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# SESSION_COOKIE_SECURE = True should be enabled once HTTPS is in place
# app.config['SESSION_COOKIE_SECURE'] = True

ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5000').split(',')
CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS)

# ---------------------------------------------------------------------------
# Rate limiting — persistent SQLite-backed login throttle
# ---------------------------------------------------------------------------
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 900  # 15 minutes
MAX_IP_ATTEMPTS = 20   # broader IP-level limit before user lookup


def check_rate_limit(db, identifier=None, ip_address=None, user_id=None):
    """Check if login should be throttled. Returns (is_locked, seconds_remaining).
    Checks both IP-level and user-level limits using the login_attempts table."""
    now = time.time()
    cutoff = now - LOCKOUT_SECONDS

    # Clean old attempts
    db.execute('DELETE FROM login_attempts WHERE attempted_at < ?', (cutoff,))
    db.commit()

    # IP-level check (pre-lookup, catches brute-force across multiple usernames)
    if ip_address:
        ip_count = db.execute(
            'SELECT COUNT(*) as cnt FROM login_attempts WHERE ip_address = ? AND attempted_at > ?',
            (ip_address, cutoff)).fetchone()['cnt']
        if ip_count >= MAX_IP_ATTEMPTS:
            oldest = db.execute(
                'SELECT MIN(attempted_at) as oldest FROM login_attempts WHERE ip_address = ? AND attempted_at > ?',
                (ip_address, cutoff)).fetchone()['oldest']
            remaining = int(LOCKOUT_SECONDS - (now - oldest)) if oldest else 0
            return True, remaining

    # User-level check (post-lookup, prevents alias bypass)
    if user_id:
        user_count = db.execute(
            'SELECT COUNT(*) as cnt FROM login_attempts WHERE user_id = ? AND attempted_at > ?',
            (user_id, cutoff)).fetchone()['cnt']
        if user_count >= MAX_LOGIN_ATTEMPTS:
            oldest = db.execute(
                'SELECT MIN(attempted_at) as oldest FROM login_attempts WHERE user_id = ? AND attempted_at > ?',
                (user_id, cutoff)).fetchone()['oldest']
            remaining = int(LOCKOUT_SECONDS - (now - oldest)) if oldest else 0
            return True, remaining

    return False, 0


def record_failed_attempt(db, identifier, ip_address, user_id=None):
    """Record a failed login attempt in the database."""
    db.execute(
        'INSERT INTO login_attempts (identifier, ip_address, user_id, attempted_at) VALUES (?, ?, ?, ?)',
        (identifier.lower(), ip_address, user_id, time.time()))
    db.commit()


def clear_attempts(db, user_id, ip_address):
    """Clear login attempts for a user after successful login."""
    db.execute('DELETE FROM login_attempts WHERE user_id = ? OR ip_address = ?',
               (user_id, ip_address))
    db.commit()


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    """Get a database connection for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False):
    """Execute a query and return results as list of dicts."""
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    if one:
        return dict(rows[0]) if rows else None
    return [dict(row) for row in rows]


def execute_db(sql, args=()):
    """Execute a write query and return lastrowid."""
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated



# ---------------------------------------------------------------------------
# AI Assistant helper
# ---------------------------------------------------------------------------
def get_anthropic_client():
    """Get an Anthropic client with API key from environment variable."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Set it in /var/www/strata-crm/.env on the server, "
            "or export it locally for development."
        )
    return anthropic.Anthropic(api_key=api_key)


# ---------------------------------------------------------------------------
# Startup validation: verify required schema is present
# ---------------------------------------------------------------------------
REQUIRED_TABLES = ['owners', 'sections', 'deals', 'activities', 'ownership_links', 'pipeline_stages', 'change_log', 'contact_notes', 'login_attempts']
REQUIRED_OWNER_COLS = ['owner_id', 'full_name', 'phone_1', 'email_1', 'contact_status', 'classification', 'data_source']


def validate_schema():
    """Check that required tables and columns exist. Fails fast if migrations are missing."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Check required tables
    tables = {row['name'] for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    missing_tables = [t for t in REQUIRED_TABLES if t not in tables]
    if missing_tables:
        db.close()
        print(f"\nFATAL: Missing required tables: {', '.join(missing_tables)}")
        print("Run migrations first: python database/migrate.py")
        sys.exit(1)

    # Check required owner columns
    owner_cols = {row['name'] for row in db.execute('PRAGMA table_info(owners)').fetchall()}
    missing_owner = [c for c in REQUIRED_OWNER_COLS if c not in owner_cols]
    if missing_owner:
        db.close()
        print(f"\nFATAL: Missing columns in owners table: {', '.join(missing_owner)}")
        print("Run migrations first: python database/migrate.py")
        sys.exit(1)

    # Create login_attempts table for persistent rate limiting if missing
    db.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            attempt_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier   TEXT NOT NULL,
            ip_address   TEXT NOT NULL,
            user_id      INTEGER,
            attempted_at REAL NOT NULL
        )
    ''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_attempts_identifier ON login_attempts(identifier)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_attempts_ip ON login_attempts(ip_address)')
    db.commit()

    db.close()
    print("Schema validation: OK")


# ---------------------------------------------------------------------------
# AUTH ROUTES
# ---------------------------------------------------------------------------
# Password gate — single password from environment variable
GATE_PASSWORD = os.environ.get('GATE_PASSWORD', 'change-me')


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password', '')
    ip = request.remote_addr

    if not password:
        return jsonify({'error': 'Password required'}), 401

    db = get_db()
    is_locked, remaining = check_rate_limit(db, ip_address=ip)
    if is_locked:
        return jsonify({'error': f'Too many attempts. Try again in {remaining // 60} minutes.'}), 429

    if password != GATE_PASSWORD:
        record_failed_attempt(db, 'gate', ip)
        return jsonify({'error': 'Invalid password'}), 401

    db.execute('DELETE FROM login_attempts WHERE ip_address = ?', (ip,))
    db.commit()

    session.permanent = True
    session['user_id'] = 1
    session['name'] = 'Chase Pursley'
    session['role'] = 'admin'

    return jsonify({
        'user_id': 1,
        'name': 'Chase Pursley',
        'email': 'chase@capursley.com',
        'role': 'admin'
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({
        'user_id': 1,
        'name': 'Chase Pursley',
        'email': 'chase@capursley.com',
        'role': 'admin'
    })

# ---------------------------------------------------------------------------
# SECTIONS
# ---------------------------------------------------------------------------
@app.route('/api/sections', methods=['GET'])
@login_required
def list_sections():
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(max(1, int(request.args.get('per_page', 50))), 250)
    search = request.args.get('search', '').strip()
    parish = request.args.get('parish', '')
    status = request.args.get('status', '')
    operator = request.args.get('operator_id', '')
    sort = request.args.get('sort', 'display_name')
    order = request.args.get('order', 'asc')

    where = []
    params = []

    if search:
        where.append("(s.display_name LIKE ? OR s.section_number LIKE ? OR s.township LIKE ? OR s.range LIKE ?)")
        params.extend([f'%{search}%'] * 4)
    if parish:
        where.append("s.parish_id = ?")
        params.append(int(parish))
    if status:
        where.append("s.status = ?")
        params.append(status)
    if assigned:
        where.append("s.assigned_user_id = ?")
        params.append(int(assigned))
    if operator:
        where.append("s.operator_id = ?")
        params.append(int(operator))

    where_clause = ' AND '.join(where) if where else '1=1'

    # Validate sort column
    valid_sorts = {'display_name', 'section_number', 'township', 'range', 'status',
                   'exit_price', 'cost_free_price', 'people_count', 'updated_at', 'created_at',
                   'pricing_date', 'parish_name', 'operator_name', 'assigned_user_name', 'total_contacts'}
    if sort not in valid_sorts:
        sort = 'pricing_date'
    # Handle joined column sorts (need table alias)
    sort_col = sort
    if sort in ('parish_name',):
        sort_col = 'p.name'
    elif sort in ('operator_name',):
        sort_col = 'o.name'
    elif sort in ('assigned_user_name',):
        sort_col = 'u.name'
    elif sort == 'total_contacts':
        sort_col = 'total_contacts'
    else:
        sort_col = f's.{sort}'
    order = 'DESC' if order.lower() == 'desc' else 'ASC'

    total = query_db(f'SELECT COUNT(*) as cnt FROM sections s WHERE {where_clause}',
                     params, one=True)['cnt']

    offset = (page - 1) * per_page
    sections = query_db(f'''
        SELECT s.*, p.name as parish_name, o.name as operator_name,
               (SELECT COUNT(*) FROM ownership_links ol WHERE ol.section_id = s.section_id) as total_contacts
        FROM sections s
        LEFT JOIN parishes p ON s.parish_id = p.parish_id
        LEFT JOIN operators o ON s.operator_id = o.operator_id
        WHERE {where_clause}
        ORDER BY {sort_col} {order} NULLS LAST
        LIMIT ? OFFSET ?
    ''', params + [per_page, offset])

    return jsonify({
        'sections': sections,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/sections/<int:sid>', methods=['GET'])
@login_required
def get_section(sid):
    section = query_db('''
        SELECT s.*, p.name as parish_name, o.name as operator_name
        FROM sections s
        LEFT JOIN parishes p ON s.parish_id = p.parish_id
        LEFT JOIN operators o ON s.operator_id = o.operator_id
        WHERE s.section_id = ?
    ''', (sid,), one=True)

    if not section:
        return jsonify({'error': 'Section not found'}), 404

    # Get owners in this section
    owners = query_db('''
        SELECT o.owner_id, o.full_name, o.phone_1, o.email_1, o.contact_status,
               o.city, o.state, ol.nra, ol.ownership_pct,
               ol.source, ol.interest_type
        FROM ownership_links ol
        JOIN owners o ON ol.owner_id = o.owner_id
        WHERE ol.section_id = ?
        ORDER BY o.full_name
    ''', (sid,))

    # Get deals for this section
    deals = query_db('''
        SELECT d.*, ps.name as stage_name, o.full_name as owner_name, u.name as assigned_name
        FROM deals d
        LEFT JOIN pipeline_stages ps ON d.stage_id = ps.stage_id
        LEFT JOIN owners o ON d.owner_id = o.owner_id
        LEFT JOIN users u ON d.assigned_user_id = u.user_id
        WHERE d.section_id = ?
        ORDER BY d.created_at DESC
    ''', (sid,))

    # Get pricing history
    pricing = query_db('''
        SELECT ph.*
        FROM pricing_history ph
        WHERE ph.section_id = ?
        ORDER BY ph.effective_date DESC
    ''', (sid,))

    section['owners'] = owners
    section['deals'] = deals
    section['pricing_history'] = pricing
    return jsonify(section)


@app.route('/api/sections/<int:sid>', methods=['PUT'])
@login_required
def update_section(sid):
    data = request.json
    allowed = ['exit_price', 'cost_free_price', 'pricing_date', 'operator_id',
               'status', 'section_notes', 'ownership_data']

    sets = []
    params = []
    for key in allowed:
        if key in data:
            sets.append(f"{key} = ?")
            params.append(data[key])

    if not sets:
        return jsonify({'error': 'No valid fields to update'}), 400

    # Log pricing change if prices are being updated
    if 'exit_price' in data or 'cost_free_price' in data:
        old = query_db('SELECT exit_price, cost_free_price FROM sections WHERE section_id = ?',
                       (sid,), one=True)
        execute_db('''
            INSERT INTO pricing_history (section_id, exit_price, cost_free_price, effective_date, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (sid, data.get('exit_price', old['exit_price']),
              data.get('cost_free_price', old['cost_free_price']),
              data.get('pricing_date', datetime.now().strftime('%Y-%m-%d')),
              data.get('pricing_notes', '')))

    params.append(sid)
    execute_db(f"UPDATE sections SET {', '.join(sets)} WHERE section_id = ?", params)

    # Log the change
    execute_db('''
        INSERT INTO change_log (user_id, table_name, record_id, action, new_values)
        VALUES (?, 'sections', ?, 'update', ?)
    ''', (session['user_id'], sid, json.dumps(data)))

    return jsonify({'message': 'Section updated'})


@app.route('/api/sections/parishes', methods=['GET'])
@login_required
def get_parishes():
    """Get distinct parishes with section counts for filters."""
    parishes = query_db('''
        SELECT p.parish_id, p.name,
               COUNT(s.section_id) as section_count
        FROM parishes p
        LEFT JOIN sections s ON p.parish_id = s.parish_id
        GROUP BY p.parish_id, p.name
        ORDER BY p.name
    ''')

    return jsonify(parishes)


# ---------------------------------------------------------------------------
# OWNERS
# ---------------------------------------------------------------------------
@app.route('/api/owners/states', methods=['GET'])
@login_required
def get_owner_states():
    """Returns distinct states with contact counts for the filter dropdown."""
    states = query_db('''
        SELECT state, COUNT(*) as cnt
        FROM owners
        WHERE state IS NOT NULL AND state != ''
        GROUP BY state
        ORDER BY cnt DESC
    ''')
    return jsonify(states)


@app.route('/api/owners', methods=['GET'])
@login_required
def list_owners():
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(max(1, int(request.args.get('per_page', 50))), 250)
    search = request.args.get('search', '').strip()
    status = request.args.get('contact_status', '')
    classification = request.args.get('classification', '')
    section_id = request.args.get('section_id', '')
    sort = request.args.get('sort', 'full_name')
    order = request.args.get('order', 'asc')

    where = []
    params = []

    if search:
        where.append("(o.full_name LIKE ? OR o.phone_1 LIKE ? OR o.email_1 LIKE ? OR o.city LIKE ?)")
        params.extend([f'%{search}%'] * 4)
    if status:
        where.append("o.contact_status = ?")
        params.append(status)
    if classification:
        where.append("o.classification = ?")
        params.append(classification)
    state = request.args.get('state', '')
    if state:
        where.append("o.state = ?")
        params.append(state)
    data_source = request.args.get('data_source', '')
    if data_source:
        if data_source == 'ais':
            where.append("(o.data_source = 'ais_sql_dump' OR o.data_source = 'ais_contact_directory')")
        else:
            where.append("o.data_source = ?")
            params.append(data_source)
    deceased = request.args.get('deceased', '')
    if deceased == '0':
        where.append("(o.is_deceased IS NULL OR o.is_deceased = 0)")
    elif deceased == '1':
        where.append("o.is_deceased = 1")
    if section_id:
        where.append("o.owner_id IN (SELECT owner_id FROM ownership_links WHERE section_id = ?)")
        params.append(int(section_id))

    where_clause = ' AND '.join(where) if where else '1=1'

    # Validate sort column
    valid_sorts = {'full_name', 'phone_1', 'email_1', 'city', 'state', 'classification',
                   'contact_status', 'created_at', 'updated_at'}
    if sort not in valid_sorts:
        sort = 'full_name'
    order = 'DESC' if order.lower() == 'desc' else 'ASC'

    # Fast path: skip exact count, fetch one extra row to detect "has more"
    offset = (page - 1) * per_page
    owners = query_db(f'''
        SELECT o.owner_id, o.full_name, o.classification, o.contact_status, o.data_source,
               o.phone_1, o.phone_1_verified, o.email_1, o.mailing_address, o.city, o.state,
               o.date_of_birth, o.age, o.is_deceased, o.do_not_contact, o.reserved_for_user_id,
               o.has_bankruptcy, o.has_lien, o.has_judgment, o.has_evictions,
               o.has_foreclosures, o.has_debt, o.updated_at,
               (SELECT COUNT(*) FROM ownership_links ol WHERE ol.owner_id = o.owner_id) as section_count
        FROM owners o
        WHERE {where_clause}
        ORDER BY o.{sort} {order}
        LIMIT ? OFFSET ?
    ''', params + [per_page + 1, offset])

    has_more = len(owners) > per_page
    if has_more:
        owners = owners[:per_page]

    # Never run COUNT on filtered queries — it's too slow on 841K rows.
    # Use the unfiltered total from stats cache, or estimate for filtered results.
    if where_clause == '1=1':
        total = query_db('SELECT COUNT(*) as cnt FROM owners', one=True)['cnt']
    else:
        # Estimate: we know at least this many exist
        total = offset + len(owners) + (500 if has_more else 0)

    return jsonify({
        'owners': owners,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total else page + (1 if has_more else 0),
        'has_more': has_more
    })


@app.route('/api/owners/<int:oid>', methods=['GET'])
@login_required
def get_owner(oid):
    owner = query_db('''
        SELECT owner_id, full_name, first_name, middle_name, last_name, suffix, entity_name,
               phone_1, phone_2, phone_3, phone_4, phone_5, phone_6,
               phone_1_source, phone_2_source, phone_3_source,
               phone_4_source, phone_5_source, phone_6_source,
               phone_1_verified, phone_2_verified, phone_3_verified,
               phone_4_verified, phone_5_verified, phone_6_verified,
               phone_1_verified_by, phone_1_verified_date,
               phone_2_verified_by, phone_2_verified_date,
               phone_3_verified_by, phone_3_verified_date,
               phone_4_verified_by, phone_4_verified_date,
               phone_5_verified_by, phone_5_verified_date,
               phone_6_verified_by, phone_6_verified_date,
               phone_1_last_seen, phone_2_last_seen, phone_3_last_seen,
               phone_4_last_seen, phone_5_last_seen, phone_6_last_seen,
               phone_1_type, phone_2_type, phone_3_type,
               phone_4_type, phone_5_type, phone_6_type,
               email_1, email_2, email_3, email_4,
               email_1_source, email_2_source, email_3_source, email_4_source,
               email_1_last_seen, email_2_last_seen, email_3_last_seen, email_4_last_seen,
               mailing_address, city, state, zip_code,
               alt_address, alt_city, alt_state, alt_zip,
               classification, contact_status, data_source, age,
               date_of_birth, is_deceased, deceased_date,
               has_bankruptcy, has_lien, has_judgment, has_evictions,
               has_foreclosures, has_debt, relatives_json,
               do_not_contact, dnc_reason, dnc_date,
               reserved_for_user_id, reserved_reason, reserved_date,
               latitude, longitude, notes, created_at, updated_at
        FROM owners WHERE owner_id = ?
    ''', (oid,), one=True)
    if not owner:
        return jsonify({'error': 'Owner not found'}), 404

    # Add reserved-for user name if set
    if owner.get('reserved_for_user_id'):
        reserved_user = query_db('SELECT name FROM users WHERE user_id = ?',
                                 (owner['reserved_for_user_id'],), one=True)
        owner['reserved_for_name'] = reserved_user['name'] if reserved_user else None

    # Sections this owner is linked to
    sections = query_db('''
        SELECT s.section_id, s.display_name, s.status, s.exit_price, s.cost_free_price,
               ol.nra, ol.ownership_pct, ol.source, ol.interest_type,
               u.name as assigned_user_name, p.name as parish_name
        FROM ownership_links ol
        JOIN sections s ON ol.section_id = s.section_id
        LEFT JOIN parishes p ON s.parish_id = p.parish_id
        WHERE ol.owner_id = ?
        ORDER BY s.display_name
    ''', (oid,))

    # Deals for this owner
    deals = query_db('''
        SELECT d.*, ps.name as stage_name, s.display_name as section_name, u.name as assigned_name
        FROM deals d
        JOIN pipeline_stages ps ON d.stage_id = ps.stage_id
        JOIN sections s ON d.section_id = s.section_id
        LEFT JOIN users u ON d.assigned_user_id = u.user_id
        WHERE d.owner_id = ?
        ORDER BY d.created_at DESC
    ''', (oid,))

    # Activities for this owner
    activities = query_db('''
        SELECT a.*, u.name as user_name, s.display_name as section_name
        FROM activities a
        LEFT JOIN users u ON a.user_id = u.user_id
        LEFT JOIN sections s ON a.section_id = s.section_id
        WHERE a.owner_id = ?
        ORDER BY a.created_at DESC
        LIMIT 100
    ''', (oid,))

    # Aliases
    aliases = query_db(
        'SELECT * FROM owner_aliases WHERE owner_id = ? ORDER BY alias_type', (oid,))

    owner['sections'] = sections
    owner['deals'] = deals
    owner['activities'] = activities
    owner['aliases'] = aliases

    # Contact notes
    notes = query_db('''
        SELECT cn.*
        FROM contact_notes cn
        WHERE cn.owner_id = ?
        ORDER BY cn.is_pinned DESC, cn.created_at DESC
    ''', (oid,))
    owner['contact_notes'] = notes

    # Associated contacts loaded lazily via /api/owners/:id/associated
    owner['associated_contacts'] = []

    return jsonify(owner)


@app.route('/api/owners/<int:oid>/associated', methods=['GET'])
@login_required
def get_owner_associated(oid):
    """Lazy-loaded associated contacts — called when user clicks the Associated tab."""
    owner = query_db('SELECT phone_1, phone_2, phone_3, phone_4, phone_5, phone_6, '
                     'phone_work, phone_home, phone_mobile, '
                     'email_1, email_2, email_3, email_4, '
                     'mailing_address, city FROM owners WHERE owner_id = ?', (oid,), one=True)
    if not owner:
        return jsonify([])

    associated = []
    phones = [owner.get(f'phone_{i}') for i in range(1, 7)] + \
             [owner.get('phone_work'), owner.get('phone_home'), owner.get('phone_mobile')]
    phones = [p for p in phones if p]

    emails = [owner.get(f'email_{i}') for i in range(1, 5)]
    emails = [e for e in emails if e]

    addr = owner.get('mailing_address')
    city = owner.get('city')

    # Match on primary phone only (indexed) for speed
    if phones:
        placeholders = ','.join(['?'] * len(phones))
        phone_matches = query_db(f'''
            SELECT owner_id, full_name, phone_1, email_1, city, state, classification, contact_status,
                   'phone' as match_type
            FROM owners
            WHERE owner_id != ? AND phone_1 IN ({placeholders})
            LIMIT 25
        ''', [oid] + phones)
        associated.extend(phone_matches)

    if emails:
        placeholders = ','.join(['?'] * len(emails))
        email_matches = query_db(f'''
            SELECT owner_id, full_name, phone_1, email_1, city, state, classification, contact_status,
                   'email' as match_type
            FROM owners
            WHERE owner_id != ?
              AND owner_id NOT IN ({",".join(str(a["owner_id"]) for a in associated) or "0"})
              AND email_1 IN ({placeholders})
            LIMIT 25
        ''', [oid] + emails)
        associated.extend(email_matches)

    if addr and city and len(addr) > 5:
        seen_ids = {a['owner_id'] for a in associated}
        addr_matches = query_db('''
            SELECT owner_id, full_name, phone_1, email_1, city, state, classification, contact_status,
                   'address' as match_type
            FROM owners
            WHERE owner_id != ? AND mailing_address = ? AND city = ?
            LIMIT 25
        ''', (oid, addr, city))
        associated.extend([a for a in addr_matches if a['owner_id'] not in seen_ids])

    return jsonify(associated)


@app.route('/api/owners/<int:oid>', methods=['PUT'])
@login_required
def update_owner(oid):
    data = request.json
    allowed = ['first_name', 'middle_name', 'last_name', 'full_name', 'suffix',
               'mailing_address', 'city', 'state', 'zip_code',
               'phone_1', 'phone_2', 'phone_3', 'phone_4', 'phone_5', 'phone_6',
               'phone_1_type', 'phone_2_type', 'phone_3_type', 'phone_4_type', 'phone_5_type',
               'phone_work', 'phone_home', 'phone_mobile',
               'email_1', 'email_2', 'email_3', 'email_4',
               'classification', 'contact_status',
               'age', 'is_deceased', 'notes', 'data_source',
               'do_not_contact', 'dnc_reason', 'dnc_date',
               'reserved_for_user_id', 'reserved_reason', 'reserved_date',
               'linkedin_url', 'facebook_url']

    sets = []
    params = []
    for key in allowed:
        if key in data:
            sets.append(f"{key} = ?")
            params.append(data[key])

    if not sets:
        return jsonify({'error': 'No valid fields to update'}), 400

    params.append(oid)
    execute_db(f"UPDATE owners SET {', '.join(sets)} WHERE owner_id = ?", params)

    execute_db('''
        INSERT INTO change_log (user_id, table_name, record_id, action, new_values)
        VALUES (?, 'owners', ?, 'update', ?)
    ''', (session['user_id'], oid, json.dumps(data)))

    return jsonify({'message': 'Owner updated'})


@app.route('/api/owners/<int:oid>/phone/<int:slot>', methods=['DELETE'])
@login_required
def delete_owner_phone(oid, slot):
    """Delete a specific phone slot (1-6) from an owner."""
    if slot < 1 or slot > 6:
        return jsonify({'error': 'Invalid phone slot'}), 400
    cols = [f'phone_{slot} = NULL', f'phone_{slot}_source = NULL',
            f'phone_{slot}_verified = 0', f'phone_{slot}_verified_by = NULL',
            f'phone_{slot}_verified_date = NULL', f'phone_{slot}_last_seen = NULL',
            f'phone_{slot}_type = NULL']
    execute_db(f"UPDATE owners SET {', '.join(cols)}, updated_at = datetime('now') WHERE owner_id = ?", (oid,))
    execute_db('''INSERT INTO change_log (user_id, table_name, record_id, action, new_values)
                  VALUES (?, 'owners', ?, 'delete_phone', ?)''',
               (session['user_id'], oid, json.dumps({'slot': slot})))
    return jsonify({'message': f'Phone {slot} deleted'})


@app.route('/api/owners/<int:oid>/email/<int:slot>', methods=['DELETE'])
@login_required
def delete_owner_email(oid, slot):
    """Delete a specific email slot (1-4) from an owner."""
    if slot < 1 or slot > 4:
        return jsonify({'error': 'Invalid email slot'}), 400
    cols = [f'email_{slot} = NULL', f'email_{slot}_source = NULL',
            f'email_{slot}_last_seen = NULL']
    execute_db(f"UPDATE owners SET {', '.join(cols)}, updated_at = datetime('now') WHERE owner_id = ?", (oid,))
    execute_db('''INSERT INTO change_log (user_id, table_name, record_id, action, new_values)
                  VALUES (?, 'owners', ?, 'delete_email', ?)''',
               (session['user_id'], oid, json.dumps({'slot': slot})))
    return jsonify({'message': f'Email {slot} deleted'})


# ---------------------------------------------------------------------------
# CONTACT NOTES
# ---------------------------------------------------------------------------
@app.route('/api/owners/<int:oid>/notes', methods=['GET'])
@login_required
def get_owner_notes(oid):
    """Get all notes for a specific owner."""
    notes = query_db('''
        SELECT cn.*
        FROM contact_notes cn
        WHERE cn.owner_id = ?
        ORDER BY cn.is_pinned DESC, cn.created_at DESC
    ''', (oid,))
    return jsonify(notes)


@app.route('/api/owners/<int:oid>/notes', methods=['POST'])
@login_required
def create_owner_note(oid):
    """Add a note to a contact."""
    data = request.json
    body = data.get('body', '').strip()
    if not body:
        return jsonify({'error': 'Note body is required'}), 400

    note_id = execute_db('''
        INSERT INTO contact_notes (owner_id, body, is_pinned)
        VALUES (?, ?, ?)
    ''', (oid, body, data.get('is_pinned', 0)))

    return jsonify({'note_id': note_id, 'message': 'Note added'}), 201


@app.route('/api/notes/<int:nid>', methods=['DELETE'])
@login_required
def delete_note(nid):
    """Delete a contact note."""
    note = query_db('SELECT note_id FROM contact_notes WHERE note_id = ?',
                    (nid,), one=True)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    execute_db('DELETE FROM contact_notes WHERE note_id = ?', (nid,))
    return jsonify({'message': 'Note deleted'})


# ---------------------------------------------------------------------------
# PHONE VERIFICATION
# ---------------------------------------------------------------------------
@app.route('/api/owners/<int:oid>/verify-phone', methods=['PUT'])
@login_required
def verify_phone(oid):
    """Toggle phone verification status."""
    data = request.json
    phone_field = data.get('phone_field', '')  # e.g. 'phone_1'
    verified = data.get('verified', 1)

    valid_fields = [f'phone_{i}_verified' for i in range(1, 7)]
    verify_col = f'{phone_field}_verified'
    if verify_col not in valid_fields:
        return jsonify({'error': 'Invalid phone field'}), 400

    today = datetime.now().strftime('%Y-%m-%d')
    by_col = f'{phone_field}_verified_by'
    date_col = f'{phone_field}_verified_date'

    if verified:
        execute_db(f'UPDATE owners SET {verify_col} = 1, {by_col} = ?, {date_col} = ? WHERE owner_id = ?',
                   (session['user_id'], today, oid))
    else:
        execute_db(f'UPDATE owners SET {verify_col} = 0, {by_col} = NULL, {date_col} = NULL WHERE owner_id = ?',
                   (oid,))

    execute_db('''
        INSERT INTO change_log (user_id, table_name, record_id, action, new_values)
        VALUES (?, 'owners', ?, 'verify_phone', ?)
    ''', (session['user_id'], oid, json.dumps({
        verify_col: verified,
        by_col: session['user_id'] if verified else None,
        date_col: today if verified else None
    })))

    return jsonify({'message': 'Phone verification updated'})


@app.route('/api/owners/<int:oid>/activities', methods=['GET'])
@login_required
def get_owner_activities(oid):
    """Get paginated activities for a specific owner."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(max(1, int(request.args.get('per_page', 50))), 250)

    total = query_db('''
        SELECT COUNT(*) as cnt FROM activities WHERE owner_id = ?
    ''', (oid,), one=True)['cnt']

    offset = (page - 1) * per_page
    activities = query_db('''
        SELECT a.*, u.name as user_name, s.display_name as section_name
        FROM activities a
        LEFT JOIN users u ON a.user_id = u.user_id
        LEFT JOIN sections s ON a.section_id = s.section_id
        WHERE a.owner_id = ?
        ORDER BY a.created_at DESC
        LIMIT ? OFFSET ?
    ''', (oid, per_page, offset))

    return jsonify({
        'activities': activities,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/owners/export', methods=['GET'])
@login_required
def export_owners():
    """Export filtered owners as CSV."""
    import csv
    from io import StringIO

    search = request.args.get('search', '').strip()
    status = request.args.get('contact_status', '')
    section_id = request.args.get('section_id', '')

    where = []
    params = []

    if search:
        where.append("(o.full_name LIKE ? OR o.phone_1 LIKE ? OR o.email_1 LIKE ? OR o.city LIKE ?)")
        params.extend([f'%{search}%'] * 4)
    if status:
        where.append("o.contact_status = ?")
        params.append(status)
    if section_id:
        where.append("o.owner_id IN (SELECT owner_id FROM ownership_links WHERE section_id = ?)")
        params.append(int(section_id))

    where_clause = ' AND '.join(where) if where else '1=1'

    owners = query_db(f'''
        SELECT o.*,
            (SELECT COUNT(*) FROM ownership_links WHERE owner_id = o.owner_id) as section_count
        FROM owners o
        WHERE {where_clause}
        ORDER BY o.full_name
    ''', params)

    # Create CSV
    output = StringIO()
    fieldnames = ['owner_id', 'full_name', 'classification', 'contact_status', 'phone_1', 'email_1',
                  'mailing_address', 'city', 'state', 'zip_code', 'section_count', 'created_at']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for owner in owners:
        row = {k: owner.get(k, '') for k in fieldnames}
        writer.writerow(row)

    response_text = output.getvalue()
    output.close()

    from flask import make_response
    response = make_response(response_text)
    response.headers['Content-Disposition'] = 'attachment; filename=owners_export.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


# ---------------------------------------------------------------------------
# DEALS
# ---------------------------------------------------------------------------
@app.route('/api/deals', methods=['GET'])
@login_required
def list_deals():
    pipeline = request.args.get('pipeline', 'Haynesville')
    status = request.args.get('status', 'open')
    where = ['ps.pipeline_name = ?', 'd.status = ?']
    params = [pipeline, status]

    if assigned:
        where.append('d.assigned_user_id = ?')
        params.append(int(assigned))

    deals = query_db(f'''
        SELECT d.*, ps.name as stage_name, ps.sort_order,
               o.full_name as owner_name, s.display_name as section_name,
               u.name as assigned_name
        FROM deals d
        JOIN pipeline_stages ps ON d.stage_id = ps.stage_id
        LEFT JOIN owners o ON d.owner_id = o.owner_id
        JOIN sections s ON d.section_id = s.section_id
        LEFT JOIN users u ON d.assigned_user_id = u.user_id
        WHERE {' AND '.join(where)}
        ORDER BY ps.sort_order, d.created_at DESC
    ''', params)

    # Group by stage for Kanban view
    stages = query_db('''
        SELECT stage_id, name, sort_order FROM pipeline_stages
        WHERE pipeline_name = ? AND is_active = 1
        ORDER BY sort_order
    ''', (pipeline,))

    kanban = {s['stage_id']: {'stage': dict(s), 'deals': []} for s in stages}
    for d in deals:
        if d['stage_id'] in kanban:
            kanban[d['stage_id']]['deals'].append(d)

    return jsonify({
        'stages': [kanban[s['stage_id']] for s in stages],
        'total_deals': len(deals),
        'total_value': sum(d['value'] or 0 for d in deals)
    })


@app.route('/api/deals', methods=['POST'])
@login_required
def create_deal():
    data = request.json
    did = execute_db('''
        INSERT INTO deals (owner_id, section_id, stage_id,
                          title, value, nra, price_per_nra, status, expected_close)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?)
    ''', (data.get('owner_id'), data['section_id'], data['stage_id'],
          data['title'], data.get('value'), data.get('nra'),
          data.get('price_per_nra'), data.get('expected_close')))

    # Log initial stage
    execute_db('''
        INSERT INTO deal_stage_history (deal_id, to_stage_id)
        VALUES (?, ?)
    ''', (did, data['stage_id']))

    return jsonify({'deal_id': did, 'message': 'Deal created'}), 201


@app.route('/api/deals/<int:did>', methods=['GET'])
@login_required
def get_deal(did):
    deal = query_db('''
        SELECT d.*, ps.name as stage_name, ps.pipeline_name,
               o.full_name as owner_name, o.phone_1 as owner_phone, o.email_1 as owner_email,
               o.city as owner_city, o.state as owner_state, o.classification as owner_classification,
               s.display_name as section_name, s.exit_price, s.cost_free_price,
               s.parish_id, p.name as parish_name,
               u.name as assigned_name
        FROM deals d
        JOIN pipeline_stages ps ON d.stage_id = ps.stage_id
        LEFT JOIN owners o ON d.owner_id = o.owner_id
        LEFT JOIN sections s ON d.section_id = s.section_id
        LEFT JOIN parishes p ON s.parish_id = p.parish_id
        LEFT JOIN users u ON d.assigned_user_id = u.user_id
        WHERE d.deal_id = ?
    ''', (did,), one=True)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404

    # Activities for this deal
    activities = query_db('''
        SELECT a.*, u.name as user_name
        FROM activities a
        LEFT JOIN users u ON a.user_id = u.user_id
        WHERE a.deal_id = ? OR (a.owner_id = ? AND a.section_id = ?)
        ORDER BY a.created_at DESC LIMIT 50
    ''', (did, deal['owner_id'], deal['section_id']))
    deal['activities'] = activities

    # Stage history from change_log
    history = query_db('''
        SELECT cl.*, u.name as user_name
        FROM change_log cl
        LEFT JOIN users u ON cl.user_id = u.user_id
        WHERE cl.table_name = 'deals' AND cl.record_id = ?
        ORDER BY cl.changed_at DESC LIMIT 20
    ''', (did,))
    deal['history'] = history

    return jsonify(deal)


@app.route('/api/deals/<int:did>', methods=['PUT'])
@login_required
def update_deal(did):
    data = request.json

    if 'stage_id' in data:
        old = query_db('SELECT stage_id FROM deals WHERE deal_id = ?', (did,), one=True)
        if old and old['stage_id'] != data['stage_id']:
            execute_db('''
                INSERT INTO deal_stage_history (deal_id, from_stage_id, to_stage_id)
                VALUES (?, ?, ?)
            ''', (did, old['stage_id'], data['stage_id']))

    allowed = ['stage_id', 'value', 'nra', 'price_per_nra', 'status',
               'lost_reason', 'expected_close', 'actual_close']
    sets = []
    params = []
    for key in allowed:
        if key in data:
            sets.append(f"{key} = ?")
            params.append(data[key])

    if sets:
        params.append(did)
        execute_db(f"UPDATE deals SET {', '.join(sets)} WHERE deal_id = ?", params)

    return jsonify({'message': 'Deal updated'})


@app.route('/api/deals/<int:did>', methods=['DELETE'])
@login_required
def delete_deal(did):
    """Delete a deal and its stage history. Requires assignment or admin role."""
    deal = query_db('SELECT deal_id, title, owner_id, section_id, value, status, assigned_user_id FROM deals WHERE deal_id = ?',
                    (did,), one=True)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404

    # Authorization: only assigned user or admin can delete
    user_id = session['user_id']
    user = query_db('SELECT role FROM users WHERE user_id = ?', (user_id,), one=True)
    is_admin = user and user.get('role') in ('admin', 'manager')
    if deal['assigned_user_id'] != user_id and not is_admin:
        return jsonify({'error': 'Not authorized to delete this deal'}), 403

    # Atomic delete with structured audit
    db = get_db()
    try:
        db.execute('''
            INSERT INTO change_log (table_name, record_id, field_name, old_value, new_value, user_id)
            VALUES ('deals', ?, 'action', ?, 'DELETED', ?)
        ''', (did, json.dumps({
            'title': deal['title'], 'status': deal['status'], 'value': deal['value'],
            'owner_id': deal['owner_id'], 'section_id': deal['section_id'],
            'assigned_user_id': deal['assigned_user_id']
        }), user_id))
        db.execute('DELETE FROM deal_stage_history WHERE deal_id = ?', (did,))
        db.execute('DELETE FROM deals WHERE deal_id = ?', (did,))
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

    return jsonify({'message': 'Deal deleted', 'deal_id': did})


# ---------------------------------------------------------------------------
# ACTIVITIES
# ---------------------------------------------------------------------------
@app.route('/api/activities', methods=['GET'])
@login_required
def list_activities():
    """List all activities with optional filters and pagination."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(max(1, int(request.args.get('per_page', 50))), 250)
    user_id = request.args.get('user_id', '')
    activity_type = request.args.get('type', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    where = []
    params = []

    if user_id:
        where.append("a.user_id = ?")
        params.append(int(user_id))
    if activity_type:
        where.append("a.type = ?")
        params.append(activity_type)
    if start_date:
        where.append("DATE(a.created_at) >= ?")
        params.append(start_date)
    if end_date:
        where.append("DATE(a.created_at) <= ?")
        params.append(end_date)

    where_clause = ' AND '.join(where) if where else '1=1'

    total = query_db(f'SELECT COUNT(*) as cnt FROM activities a WHERE {where_clause}',
                     params, one=True)['cnt']

    offset = (page - 1) * per_page
    activities = query_db(f'''
        SELECT a.*, u.name as user_name, o.full_name as owner_name, s.display_name as section_name
        FROM activities a
        LEFT JOIN users u ON a.user_id = u.user_id
        LEFT JOIN owners o ON a.owner_id = o.owner_id
        LEFT JOIN sections s ON a.section_id = s.section_id
        WHERE {where_clause}
        ORDER BY a.created_at DESC
        LIMIT ? OFFSET ?
    ''', params + [per_page, offset])

    return jsonify({
        'activities': activities,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/activities', methods=['POST'])
@login_required
def create_activity():
    data = request.json
    aid = execute_db('''
        INSERT INTO activities (owner_id, section_id, deal_id, user_id, type, subject, body,
                               call_duration, call_outcome, email_direction, email_subject,
                               letter_type, letter_sent_date, is_pinned)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['owner_id'], data.get('section_id'), data.get('deal_id'),
          session['user_id'], data['type'], data.get('subject'), data.get('body'),
          data.get('call_duration'), data.get('call_outcome'),
          data.get('email_direction'), data.get('email_subject'),
          data.get('letter_type'), data.get('letter_sent_date'),
          data.get('is_pinned', 0)))

    return jsonify({'activity_id': aid, 'message': 'Activity logged'}), 201


# ---------------------------------------------------------------------------
# SEARCH
# ---------------------------------------------------------------------------
@app.route('/api/search', methods=['GET'])
@login_required
def global_search():
    """Global search across sections and owners."""
    q = request.args.get('q', '').strip()

    # Require at least 3 characters — prevents full-table scans on every keystroke
    if not q or len(q) < 3:
        return jsonify({'sections': [], 'owners': [], 'deals': []})

    search_term = f'%{q}%'

    # Search sections (only 1,025 rows — wildcard scan is acceptable here)
    sections = query_db('''
        SELECT s.section_id, s.display_name, s.section_number, s.township, s.range,
               p.name as parish_name, s.status
        FROM sections s
        LEFT JOIN parishes p ON s.parish_id = p.parish_id
        WHERE s.display_name LIKE ? OR s.section_number LIKE ? OR s.township LIKE ? OR s.range LIKE ?
        LIMIT 10
    ''', (search_term, search_term, search_term, search_term))

    # Search owners — full_name only to avoid multi-column wildcard scans on 841K rows.
    # Phone/email search deferred to FTS5 implementation (Session 13).
    owners = query_db('''
        SELECT o.owner_id, o.full_name, o.phone_1, o.email_1, o.city, o.state, o.classification
        FROM owners o
        WHERE o.full_name LIKE ?
        LIMIT 10
    ''', (search_term,))

    # Search deals — title only; owner/section joins kept for display but not searched
    deals = query_db('''
        SELECT d.deal_id, d.title, d.value, d.status,
               o.full_name as owner_name, s.display_name as section_name,
               ps.name as stage_name
        FROM deals d
        LEFT JOIN owners o ON d.owner_id = o.owner_id
        LEFT JOIN sections s ON d.section_id = s.section_id
        LEFT JOIN pipeline_stages ps ON d.stage_id = ps.stage_id
        WHERE d.title LIKE ?
        LIMIT 10
    ''', (search_term,))

    return jsonify({
        'sections': sections,
        'owners': owners,
        'deals': deals
    })


# ---------------------------------------------------------------------------
# STATS
# ---------------------------------------------------------------------------
@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get global statistics for the stats bar."""

    # Total counts
    total_owners = query_db('SELECT COUNT(*) as cnt FROM owners', one=True)['cnt']
    total_sections = query_db('SELECT COUNT(*) as cnt FROM sections', one=True)['cnt']
    total_deals = query_db('SELECT COUNT(*) as cnt FROM deals', one=True)['cnt']

    # Owners by classification
    classifications = query_db('''
        SELECT classification, COUNT(*) as count
        FROM owners
        WHERE classification IS NOT NULL
        GROUP BY classification
    ''')
    owners_by_classification = {c['classification']: c['count'] for c in classifications}

    # Owners by contact status
    contact_statuses = query_db('''
        SELECT contact_status, COUNT(*) as count
        FROM owners
        WHERE contact_status IS NOT NULL
        GROUP BY contact_status
    ''')
    owners_by_contact_status = {c['contact_status']: c['count'] for c in contact_statuses}

    # Total with phone
    total_with_phone = query_db('''
        SELECT COUNT(*) as cnt FROM owners
        WHERE phone_1 IS NOT NULL AND phone_1 != ''
    ''', one=True)['cnt']

    # Total with email
    total_with_email = query_db('''
        SELECT COUNT(*) as cnt FROM owners
        WHERE email_1 IS NOT NULL AND email_1 != ''
    ''', one=True)['cnt']

    # Deals by status
    deal_statuses = query_db('''
        SELECT status, COUNT(*) as count, COALESCE(SUM(value), 0) as total_value
        FROM deals
        GROUP BY status
    ''')
    deals_by_status = {d['status']: {'count': d['count'], 'value': d['total_value']} for d in deal_statuses}

    # Recent activity count (last 7 days)
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent_activity_count = query_db('''
        SELECT COUNT(*) as cnt FROM activities
        WHERE created_at > ?
    ''', (seven_days_ago,), one=True)['cnt']

    return jsonify({
        'total_owners': total_owners,
        'total_sections': total_sections,
        'total_deals': total_deals,
        'owners_by_classification': owners_by_classification,
        'owners_by_contact_status': owners_by_contact_status,
        'total_with_phone': total_with_phone,
        'total_with_email': total_with_email,
        'deals_by_status': deals_by_status,
        'recent_activity_count': recent_activity_count
    })


# ---------------------------------------------------------------------------
# DASHBOARD / LANDING PAGE
# ---------------------------------------------------------------------------
@app.route('/api/dashboard', methods=['GET'])
@login_required
def dashboard():
    uid = session['user_id']

    # My sections
    my_sections = query_db('''
        SELECT COUNT(*) as cnt FROM sections WHERE assigned_user_id = ?
    ''', (uid,), one=True)['cnt']

    # My open deals
    my_deals = query_db('''
        SELECT COUNT(*) as cnt, COALESCE(SUM(value), 0) as total_value
        FROM deals WHERE assigned_user_id = ? AND status = 'open'
    ''', (uid,), one=True)

    # Recent changes to my sections
    recent_changes = query_db('''
        SELECT cl.*
        FROM change_log cl
        ORDER BY cl.changed_at DESC
        LIMIT 20
    ''')

    # Pipeline summary
    pipeline_summary = query_db('''
        SELECT ps.name as stage_name, ps.sort_order,
               COUNT(d.deal_id) as deal_count,
               COALESCE(SUM(d.value), 0) as stage_value
        FROM pipeline_stages ps
        LEFT JOIN deals d ON ps.stage_id = d.stage_id
            AND d.assigned_user_id = ? AND d.status = 'open'
        WHERE ps.pipeline_name = 'Haynesville'
        GROUP BY ps.stage_id
        ORDER BY ps.sort_order
    ''', (uid,))

    return jsonify({
        'my_sections': my_sections,
        'my_open_deals': my_deals['cnt'],
        'my_deal_value': my_deals['total_value'],
        'recent_changes': recent_changes,
        'pipeline_summary': pipeline_summary
    })


# ---------------------------------------------------------------------------
# MAP DATA — lightweight endpoint for geocoded contacts
# ---------------------------------------------------------------------------
@app.route('/api/map/markers', methods=['GET'])
@login_required
def get_map_markers():
    """Returns lightweight marker data for geocoded contacts.
    Supports filtering by state, classification, and limit."""
    state = request.args.get('state', '')
    classification = request.args.get('classification', '')
    limit = min(int(request.args.get('limit', 50000)), 100000)

    where = ['latitude IS NOT NULL', 'latitude > 0']
    params = []

    if state:
        where.append('(state = ? OR state = ?)')
        # Handle both abbreviation and full name
        state_map = {'LA': 'Louisiana', 'TX': 'Texas', 'OK': 'Oklahoma', 'OH': 'Ohio',
                     'PA': 'Pennsylvania', 'CO': 'Colorado', 'CA': 'California',
                     'WV': 'West Virginia', 'FL': 'Florida', 'ND': 'North Dakota'}
        full = state_map.get(state, state)
        params.extend([state, full])

    if classification:
        where.append('classification = ?')
        params.append(classification)

    deceased = request.args.get('deceased', '')
    if deceased == '0':
        where.append('(is_deceased IS NULL OR is_deceased = 0)')
    elif deceased == '1':
        where.append('is_deceased = 1')

    where_clause = ' AND '.join(where)
    params.append(limit)

    markers = query_db(f'''
        SELECT owner_id, full_name, latitude, longitude, classification, city, state,
               contact_status, phone_1
        FROM owners
        WHERE {where_clause}
        LIMIT ?
    ''', params)

    return jsonify({
        'markers': markers,
        'count': len(markers)
    })


# LOOKUP DATA
# ---------------------------------------------------------------------------
@app.route('/api/lookups', methods=['GET'])
@login_required
def get_lookups():
    return jsonify({
        'parishes': query_db('SELECT * FROM parishes ORDER BY name'),
        'operators': query_db('SELECT * FROM operators WHERE is_active = 1 ORDER BY name'),
        'pipeline_stages': query_db('SELECT * FROM pipeline_stages WHERE is_active = 1 ORDER BY sort_order'),
        'basins': query_db('SELECT * FROM basins WHERE is_active = 1 ORDER BY name')
    })


# ---------------------------------------------------------------------------
# AI ASSISTANT — Safe query intents (no raw SQL execution)
# ---------------------------------------------------------------------------
ASSISTANT_QUERY_INTENTS = {
    'search_owners': {
        'description': 'Search contacts by name, phone, email, city, state, classification, status, age range, or deceased flag',
        'sql': '''SELECT owner_id, full_name, classification, contact_status,
                         phone_1, email_1, city, state, age, is_deceased, data_source
                  FROM owners WHERE {conditions} ORDER BY full_name LIMIT {limit}''',
        'allowed_filters': ['full_name', 'phone_1', 'email_1', 'city', 'state',
                           'classification', 'contact_status', 'is_deceased', 'data_source'],
        'supports_age_range': True
    },
    'count_owners': {
        'description': 'Count contacts matching criteria',
        'sql': '''SELECT COUNT(*) as total, {group_col}
                  FROM owners WHERE {conditions} {group_by}''',
        'allowed_filters': ['classification', 'contact_status', 'state', 'city',
                           'is_deceased', 'data_source'],
        'supports_age_range': True,
        'supports_group_by': ['classification', 'contact_status', 'state', 'is_deceased', 'data_source']
    },
    'search_sections': {
        'description': 'Search sections by name, township, range, parish, status, or operator',
        'sql': '''SELECT s.section_id, s.display_name, s.section_number, s.township, s.range,
                         s.status, s.exit_price, s.cost_free_price,
                         p.name as parish_name, o.name as operator_name, u.name as assigned_to,
                         (SELECT COUNT(*) FROM ownership_links ol WHERE ol.section_id = s.section_id) as owner_count
                  FROM sections s
                  LEFT JOIN parishes p ON s.parish_id = p.parish_id
                  LEFT JOIN operators o ON s.operator_id = o.operator_id
                  WHERE {conditions} ORDER BY s.display_name LIMIT {limit}''',
        'allowed_filters': ['display_name', 'section_number', 'township', 'range', 'status']
    },
    'section_owners': {
        'description': 'List all owners linked to a specific section',
        'sql': '''SELECT o.owner_id, o.full_name, o.phone_1, o.email_1, o.city, o.state,
                         o.classification, o.contact_status, ol.nra, ol.ownership_pct, ol.interest_type
                  FROM ownership_links ol
                  JOIN owners o ON ol.owner_id = o.owner_id
                  WHERE ol.section_id = ? ORDER BY o.full_name LIMIT {limit}''',
        'requires': ['section_id']
    },
    'owner_sections': {
        'description': 'List all sections linked to a specific owner',
        'sql': '''SELECT s.section_id, s.display_name, s.status, s.exit_price,
                         p.name as parish_name, ol.nra, ol.ownership_pct
                  FROM ownership_links ol
                  JOIN sections s ON ol.section_id = s.section_id
                  LEFT JOIN parishes p ON s.parish_id = p.parish_id
                  WHERE ol.owner_id = ? ORDER BY s.display_name LIMIT {limit}''',
        'requires': ['owner_id']
    },
    'deal_summary': {
        'description': 'Summarize deals by status, stage, or assigned user',
        'sql': '''SELECT ps.name as stage, d.status, COUNT(*) as deal_count,
                         COALESCE(SUM(d.value), 0) as total_value,
                         u.name as assigned_to
                  FROM deals d
                  LEFT JOIN pipeline_stages ps ON d.stage_id = ps.stage_id
                  LEFT JOIN users u ON d.assigned_user_id = u.user_id
                  WHERE {conditions}
                  GROUP BY ps.name, d.status, u.name
                  ORDER BY ps.sort_order LIMIT {limit}''',
        'allowed_filters': ['status']
    },
    'recent_activities': {
        'description': 'Show recent activities, optionally filtered by type or user',
        'sql': '''SELECT a.activity_id, a.type, a.subject, a.created_at,
                         u.name as user_name, o.full_name as owner_name,
                         s.display_name as section_name
                  FROM activities a
                  LEFT JOIN users u ON a.user_id = u.user_id
                  LEFT JOIN owners o ON a.owner_id = o.owner_id
                  LEFT JOIN sections s ON a.section_id = s.section_id
                  WHERE {conditions}
                  ORDER BY a.created_at DESC LIMIT {limit}''',
        'allowed_filters': ['type']
    },
    'parish_stats': {
        'description': 'Get contact and section counts by parish',
        'sql': '''SELECT p.name as parish, COUNT(DISTINCT s.section_id) as sections,
                         COUNT(DISTINCT ol.owner_id) as owners
                  FROM parishes p
                  LEFT JOIN sections s ON p.parish_id = s.parish_id
                  LEFT JOIN ownership_links ol ON s.section_id = ol.section_id
                  GROUP BY p.name ORDER BY sections DESC LIMIT {limit}'''
    }
}

MAX_ASSISTANT_ROWS = 50

# Pending assistant action confirmations: token -> {action, params, user_id, expires}
PENDING_CONFIRMATIONS = {}


def execute_safe_intent(intent_name, params, limit=50):
    """Execute a pre-defined query intent with validated parameters."""
    intent = ASSISTANT_QUERY_INTENTS.get(intent_name)
    if not intent:
        return None, f"Unknown query intent: {intent_name}"

    limit = min(max(1, limit), MAX_ASSISTANT_ROWS)
    sql_template = intent['sql']
    query_params = []

    # Handle intents with required params (e.g., section_id, owner_id)
    if 'requires' in intent:
        for req in intent['requires']:
            if req not in params:
                return None, f"Missing required parameter: {req}"
            query_params.append(params[req])
        sql = sql_template.format(limit=limit)
        return query_db(sql, query_params), None

    # Build WHERE conditions from allowed filters
    conditions = []
    allowed = intent.get('allowed_filters', [])

    for key, value in params.items():
        if key == 'age_min' and intent.get('supports_age_range'):
            conditions.append('age >= ?')
            query_params.append(int(value))
        elif key == 'age_max' and intent.get('supports_age_range'):
            conditions.append('age <= ?')
            query_params.append(int(value))
        elif key == 'parish_name':
            conditions.append('p.name LIKE ?')
            query_params.append(f'%{value}%')
        elif key in allowed:
            if isinstance(value, str) and '%' not in value:
                # Exact match for status/classification, LIKE for names/cities
                if key in ('classification', 'contact_status', 'status', 'is_deceased', 'data_source', 'type'):
                    conditions.append(f'{key} = ?')
                    query_params.append(value)
                else:
                    conditions.append(f'{key} LIKE ?')
                    query_params.append(f'%{value}%')

    where = ' AND '.join(conditions) if conditions else '1=1'

    # Handle group_by for count queries
    group_col = "'all' as group_value"
    group_by = ''
    if intent.get('supports_group_by') and 'group_by' in params:
        gb = params['group_by']
        if gb in intent['supports_group_by']:
            group_col = gb
            group_by = f'GROUP BY {gb}'

    sql = sql_template.format(conditions=where, limit=limit,
                              group_col=group_col, group_by=group_by)
    return query_db(sql, query_params), None


@app.route('/api/assistant', methods=['POST'])
@login_required
def ask_assistant():
    """AI assistant endpoint — uses predefined query intents, not raw SQL."""
    try:
        data = request.json or {}
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'No message provided'}), 400

        user_name = session.get('name', 'User')

        # Build available intents description for the AI
        intents_desc = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in ASSISTANT_QUERY_INTENTS.items()
        ])

        system_prompt = f"""You are an AI assistant for Strata, a personal mineral rights acquisition CRM.

AVAILABLE QUERY INTENTS (you MUST use these — no raw SQL):
{intents_desc}

WRITE ACTIONS (require user confirmation):
- update_contact_status: Update a contact's status (owner_id, new_status required)
- create_deal: Create a new deal (owner_id, section_id, stage_id, title required)
- log_activity: Log an activity (owner_id, type, subject required)

VALID VALUES:
- classification: Individual, Trust, LLC, Estate, Corporation, Business
- contact_status: Not Contacted, Attempted, Reached, Follow Up Needed, No Answer, Bad Contact Info
- section status: ACTIVE, PROSPECT, CLOSED, INACTIVE, HOLD
- activity type: call, voicemail, text, email, letter, note, document, meeting

RESPONSE FORMAT — respond with ONLY a JSON block in ```json ... ``` markers:

For queries:
{{"type": "query", "intent": "<intent_name>", "params": {{"filter_field": "value", ...}}, "limit": 50, "message": "Explanation"}}

For write actions:
{{"type": "action", "action": "<action_name>", "params": {{"owner_id": N, ...}}, "message": "What this will do", "confirm": true}}

For text responses:
{{"type": "text", "message": "..."}}

Current user: {user_name}
IMPORTANT: Never include raw SQL. Use only the intents listed above."""

        client = get_anthropic_client()

        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1024,
            system=system_prompt,
            messages=[{'role': 'user', 'content': message}]
        )

        response_text = response.content[0].text

        # Extract JSON from markdown code block
        if '```json' in response_text:
            start = response_text.index('```json') + 7
            end = response_text.index('```', start)
            json_str = response_text[start:end].strip()
        else:
            json_str = response_text.strip()

        claude_response = json.loads(json_str)
        response_type = claude_response.get('type', 'text')

        if response_type == 'query':
            intent_name = claude_response.get('intent', '')
            params = claude_response.get('params', {})
            limit = claude_response.get('limit', MAX_ASSISTANT_ROWS)

            results, error = execute_safe_intent(intent_name, params, limit)
            if error:
                return jsonify({'response': error, 'type': 'error'}), 400

            return jsonify({
                'response': claude_response.get('message', 'Here are the results.'),
                'data': results,
                'type': 'query',
                'intent': intent_name
            })

        elif response_type == 'action':
            action = claude_response.get('action', '')
            action_params = claude_response.get('params', {})

            valid_actions = ('update_contact_status', 'create_deal', 'log_activity')
            if action not in valid_actions:
                return jsonify({'error': f'Unknown action: {action}'}), 400

            # ALL write actions require server-side confirmation.
            # Generate a token, store the pending action, return to frontend for user approval.
            token = secrets.token_urlsafe(32)
            PENDING_CONFIRMATIONS[token] = {
                'action': action,
                'params': action_params,
                'user_id': session['user_id'],
                'expires': time.time() + 300  # 5 minute expiry
            }
            # Clean expired tokens
            expired = [k for k, v in PENDING_CONFIRMATIONS.items() if v['expires'] < time.time()]
            for k in expired:
                del PENDING_CONFIRMATIONS[k]

            return jsonify({
                'response': claude_response.get('message', f'Ready to execute: {action}'),
                'type': 'confirm_action',
                'action': action,
                'params': action_params,
                'confirmation_token': token
            })

        # Text response
        return jsonify({
            'response': claude_response.get('message', response_text),
            'type': 'text'
        })

    except json.JSONDecodeError as e:
        return jsonify({'error': f'Failed to parse AI response: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/assistant/suggestions', methods=['GET'])
@login_required
def get_assistant_suggestions():
    """Get example queries users can try with the AI assistant."""
    suggestions = [
        "Show me all individuals over 70 in DeSoto Parish",
        "How many contacts have we reached vs not contacted?",
        "Find all trusts with email addresses",
        "What sections have the highest exit price?",
        "Show contacts in Shreveport who haven't been contacted",
        "How many contacts are deceased?",
        "What's the average age of individual contacts by parish?",
        "Find all LLCs with phone numbers"
    ]
    return jsonify({'suggestions': suggestions})


@app.route('/api/assistant/confirm', methods=['POST'])
@login_required
def confirm_assistant_action():
    """Execute a previously confirmed assistant write action using a server-generated token."""
    data = request.json or {}
    token = data.get('confirmation_token', '')

    if not token or token not in PENDING_CONFIRMATIONS:
        return jsonify({'error': 'Invalid or expired confirmation token'}), 400

    pending = PENDING_CONFIRMATIONS.pop(token)

    # Verify token hasn't expired
    if pending['expires'] < time.time():
        return jsonify({'error': 'Confirmation token has expired'}), 400

    # Verify same user who initiated the action
    if pending['user_id'] != session['user_id']:
        return jsonify({'error': 'Confirmation token does not match current user'}), 403

    action = pending['action']
    action_params = pending['params']

    if action == 'update_contact_status':
        owner_id = action_params.get('owner_id')
        new_status = action_params.get('new_status')
        if not owner_id or not new_status:
            return jsonify({'error': 'Missing owner_id or new_status'}), 400
        execute_db('UPDATE owners SET contact_status = ? WHERE owner_id = ?',
                  (new_status, owner_id))
        execute_db('''INSERT INTO change_log (user_id, table_name, record_id, action, new_values)
                      VALUES (?, 'owners', ?, 'assistant_update', ?)''',
                   (session['user_id'], owner_id, json.dumps({'contact_status': new_status})))
        return jsonify({'response': f'Updated contact {owner_id} status to {new_status}', 'type': 'action'})

    elif action == 'create_deal':
        owner_id = action_params.get('owner_id')
        section_id = action_params.get('section_id')
        stage_id = action_params.get('stage_id', 1)
        title = action_params.get('title', '')
        value = action_params.get('value', 0)
        nra = action_params.get('nra', 0)
        price = action_params.get('price_per_nra', 0)
        if not owner_id or not section_id:
            return jsonify({'error': 'Missing owner_id or section_id'}), 400
        deal_id = execute_db(
            'INSERT INTO deals (owner_id, section_id, stage_id, value, nra, price_per_nra, title, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (owner_id, section_id, stage_id, value, nra, price, title, 'open'))
        return jsonify({'response': f'Created deal {deal_id}', 'data': {'deal_id': deal_id}, 'type': 'action'})

    elif action == 'log_activity':
        owner_id = action_params.get('owner_id')
        if not owner_id:
            return jsonify({'error': 'Missing owner_id'}), 400
        activity_id = execute_db(
            'INSERT INTO activities (owner_id, section_id, user_id, type, subject, body, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (owner_id, action_params.get('section_id'), session['user_id'],
             action_params.get('type', 'note'), action_params.get('subject', ''),
             action_params.get('body', ''), datetime.now().isoformat()))
        return jsonify({'response': f'Logged activity {activity_id}', 'data': {'activity_id': activity_id}, 'type': 'action'})

    return jsonify({'error': f'Unknown action: {action}'}), 400


# ---------------------------------------------------------------------------
# STATIC FILE SERVING
# ---------------------------------------------------------------------------
@app.route('/')
def serve_index():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'app'), 'index.html')


@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), path)


@app.route('/components/<path:path>')
def serve_components(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'components'), path)


@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'app', 'css'), path)


@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'app', 'js'), path)


# ---------------------------------------------------------------------------
# ASSISTANT CONVERSATION HISTORY
# ---------------------------------------------------------------------------
@app.route('/api/assistant/conversations', methods=['GET'])
@login_required
def list_conversations():
    """List all conversations for the current user."""
    convos = query_db('''
        SELECT c.conversation_id, c.title, c.is_pinned, c.created_at, c.updated_at,
               (SELECT COUNT(*) FROM assistant_messages WHERE conversation_id = c.conversation_id) as message_count
        FROM assistant_conversations c
        WHERE c.user_id = ?
        ORDER BY c.is_pinned DESC, c.updated_at DESC
        LIMIT 50
    ''', (session['user_id'],))
    return jsonify(convos)


@app.route('/api/assistant/conversations', methods=['POST'])
@login_required
def create_conversation():
    """Create a new conversation."""
    data = request.json or {}
    title = data.get('title', 'New conversation')
    cid = execute_db(
        'INSERT INTO assistant_conversations (user_id, title) VALUES (?, ?)',
        (session['user_id'], title)
    )
    return jsonify({'conversation_id': cid, 'title': title}), 201


@app.route('/api/assistant/conversations/<int:cid>', methods=['GET'])
@login_required
def get_conversation(cid):
    """Get a conversation with all its messages."""
    convo = query_db(
        'SELECT * FROM assistant_conversations WHERE conversation_id = ? AND user_id = ?',
        (cid, session['user_id']), one=True)
    if not convo:
        return jsonify({'error': 'Conversation not found'}), 404
    messages = query_db(
        'SELECT * FROM assistant_messages WHERE conversation_id = ? ORDER BY created_at ASC',
        (cid,))
    convo['messages'] = messages
    return jsonify(convo)


@app.route('/api/assistant/conversations/<int:cid>', methods=['DELETE'])
@login_required
def delete_conversation(cid):
    """Delete a conversation and all its messages."""
    convo = query_db(
        'SELECT conversation_id FROM assistant_conversations WHERE conversation_id = ? AND user_id = ?',
        (cid, session['user_id']), one=True)
    if not convo:
        return jsonify({'error': 'Conversation not found'}), 404
    execute_db('DELETE FROM assistant_messages WHERE conversation_id = ?', (cid,))
    execute_db('DELETE FROM assistant_conversations WHERE conversation_id = ?', (cid,))
    return jsonify({'message': 'Conversation deleted'})


@app.route('/api/assistant/conversations/<int:cid>/pin', methods=['PUT'])
@login_required
def toggle_pin_conversation(cid):
    """Toggle pin status of a conversation."""
    convo = query_db(
        'SELECT is_pinned FROM assistant_conversations WHERE conversation_id = ? AND user_id = ?',
        (cid, session['user_id']), one=True)
    if not convo:
        return jsonify({'error': 'Conversation not found'}), 404
    new_pin = 0 if convo['is_pinned'] else 1
    execute_db('UPDATE assistant_conversations SET is_pinned = ? WHERE conversation_id = ?', (new_pin, cid))
    return jsonify({'is_pinned': new_pin})


@app.route('/api/assistant/conversations/<int:cid>/messages', methods=['POST'])
@login_required
def save_message(cid):
    """Save a message to a conversation."""
    convo = query_db(
        'SELECT conversation_id FROM assistant_conversations WHERE conversation_id = ? AND user_id = ?',
        (cid, session['user_id']), one=True)
    if not convo:
        return jsonify({'error': 'Conversation not found'}), 404
    data = request.json
    mid = execute_db(
        'INSERT INTO assistant_messages (conversation_id, role, content, sql_query, result_data) VALUES (?, ?, ?, ?, ?)',
        (cid, data['role'], data['content'], data.get('sql_query'), data.get('result_data'))
    )
    # Update conversation title from first user message if still default
    if data['role'] == 'user':
        current = query_db('SELECT title FROM assistant_conversations WHERE conversation_id = ?', (cid,), one=True)
        if current and current['title'] == 'New conversation':
            title = data['content'][:60] + ('...' if len(data['content']) > 60 else '')
            execute_db('UPDATE assistant_conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE conversation_id = ?',
                       (title, cid))
        else:
            execute_db('UPDATE assistant_conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = ?', (cid,))
    return jsonify({'message_id': mid}), 201


# ---------------------------------------------------------------------------
# STARTUP
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    validate_schema()
    print(f"Database: {DB_PATH}")
    print(f"Frontend: {FRONTEND_DIR}")
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
