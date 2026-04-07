-- ============================================================
-- STRATA CRM — Database Schema
-- Version: 3.0.0
-- Date: April 7, 2026
-- Engine: SQLite
-- Personal mineral acquisition CRM for Chase Pursley
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ============================================================
-- REFERENCE / LOOKUP TABLES
-- ============================================================

-- Basins
CREATE TABLE basins (
    basin_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    state           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Parishes/counties within basins
CREATE TABLE parishes (
    parish_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    basin_id        INTEGER NOT NULL REFERENCES basins(basin_id),
    name            TEXT NOT NULL,
    state           TEXT NOT NULL DEFAULT 'LA',
    UNIQUE(name, state)
);

-- Operators
CREATE TABLE operators (
    operator_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    is_active       INTEGER NOT NULL DEFAULT 1
);

-- Deal pipeline stages (ordered)
CREATE TABLE pipeline_stages (
    stage_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name   TEXT NOT NULL,
    name            TEXT NOT NULL,
    sort_order      INTEGER NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    UNIQUE(pipeline_name, name)
);

-- ============================================================
-- CORE ENTITY TABLES
-- ============================================================

-- SECTIONS — one record per S-T-R unit
CREATE TABLE sections (
    section_id      INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Location
    basin_id        INTEGER NOT NULL REFERENCES basins(basin_id),
    parish_id       INTEGER REFERENCES parishes(parish_id),
    section_number  TEXT NOT NULL,
    township        TEXT NOT NULL,
    range           TEXT NOT NULL,
    display_name    TEXT NOT NULL,

    -- Pricing
    exit_price      REAL,                          -- $/NRA
    cost_free_price REAL,                          -- $/NRA
    pricing_date    TEXT,

    -- Assignment
    operator_id     INTEGER REFERENCES operators(operator_id),

    -- Status
    status          TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, EXHAUSTED, NO PRICE
    section_notes   TEXT,
    ownership_data  TEXT,
    deck_name       TEXT,                          -- Pay deck name

    -- Migration tracking
    pipedrive_id    INTEGER,

    -- Cached counts
    people_count    INTEGER DEFAULT 0,
    total_contacts  INTEGER DEFAULT 0,

    -- Metadata
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_sections_basin ON sections(basin_id);
CREATE INDEX idx_sections_parish ON sections(parish_id);
CREATE INDEX idx_sections_status ON sections(status);
CREATE INDEX idx_sections_str ON sections(section_number, township, range);
CREATE INDEX idx_sections_display ON sections(display_name);


-- OWNERS — one canonical record per person or entity
CREATE TABLE owners (
    owner_id        INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Name
    first_name      TEXT,
    middle_name     TEXT,
    last_name       TEXT,
    full_name       TEXT NOT NULL,
    suffix          TEXT,

    -- Contact info
    mailing_address TEXT,
    city            TEXT,
    state           TEXT,
    zip_code        TEXT,

    -- Phones
    phone_1         TEXT,
    phone_2         TEXT,
    phone_3         TEXT,
    phone_4         TEXT,
    phone_5         TEXT,
    phone_6         TEXT,
    phone_work      TEXT,
    phone_home      TEXT,
    phone_mobile    TEXT,

    -- Emails
    email_1         TEXT,
    email_2         TEXT,
    email_3         TEXT,
    email_4         TEXT,

    -- Phone types
    phone_1_type    TEXT,
    phone_2_type    TEXT,
    phone_3_type    TEXT,
    phone_4_type    TEXT,
    phone_5_type    TEXT,

    -- Phone verification (0 = unverified, 1 = verified)
    phone_1_verified INTEGER DEFAULT 0,
    phone_2_verified INTEGER DEFAULT 0,
    phone_3_verified INTEGER DEFAULT 0,
    phone_4_verified INTEGER DEFAULT 0,
    phone_5_verified INTEGER DEFAULT 0,
    phone_6_verified INTEGER DEFAULT 0,

    -- Classification / status
    classification  TEXT,                          -- Individual, Trust, LLC, Estate, Corporation, Business
    contact_status  TEXT DEFAULT 'Not Contacted',
    data_source     TEXT,                          -- AIS, Pay Deck, idiCore, etc.

    -- Demographics
    age             INTEGER,
    date_of_birth   TEXT,
    is_deceased     INTEGER DEFAULT 0,
    notes           TEXT,

    -- DNC
    do_not_contact  INTEGER DEFAULT 0,
    dnc_reason      TEXT,
    dnc_date        TEXT,

    -- Social media
    linkedin_url    TEXT,
    facebook_url    TEXT,

    -- Geocoding
    latitude        REAL,
    longitude       REAL,

    -- Financial flags (AIS enrichment)
    has_bankruptcy  INTEGER DEFAULT 0,
    has_lien        INTEGER DEFAULT 0,
    has_judgment    INTEGER DEFAULT 0,
    has_evictions   INTEGER DEFAULT 0,
    has_foreclosures INTEGER DEFAULT 0,
    has_debt        INTEGER DEFAULT 0,

    -- Relatives
    relatives_json  TEXT,

    -- Deduplication
    dedupe_key      TEXT,

    -- Metadata
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_owners_name ON owners(full_name);
CREATE INDEX idx_owners_last ON owners(last_name);
CREATE INDEX idx_owners_status ON owners(contact_status);
CREATE INDEX idx_owners_dedupe ON owners(dedupe_key);
CREATE INDEX idx_owners_city_state ON owners(city, state);
CREATE INDEX idx_owners_classification ON owners(classification);
CREATE INDEX idx_owners_geocoded ON owners(latitude, longitude);
CREATE INDEX idx_owners_data_source ON owners(data_source);


-- OWNER ALIASES — alternate names found during dedup
CREATE TABLE owner_aliases (
    alias_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id        INTEGER NOT NULL REFERENCES owners(owner_id) ON DELETE CASCADE,
    alias_name      TEXT NOT NULL,
    alias_type      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_aliases_owner ON owner_aliases(owner_id);
CREATE INDEX idx_aliases_name ON owner_aliases(alias_name);


-- OWNERSHIP LINKS — connects owners to sections
CREATE TABLE ownership_links (
    link_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id        INTEGER NOT NULL REFERENCES owners(owner_id) ON DELETE CASCADE,
    section_id      INTEGER NOT NULL REFERENCES sections(section_id) ON DELETE CASCADE,

    -- Ownership details
    nra             REAL,
    interest_type   TEXT,
    ownership_pct   REAL,

    -- Source tracking
    source          TEXT,
    source_file     TEXT,

    -- Metadata
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(owner_id, section_id)
);

CREATE INDEX idx_ownership_owner ON ownership_links(owner_id);
CREATE INDEX idx_ownership_section ON ownership_links(section_id);
CREATE INDEX idx_ownership_type ON ownership_links(interest_type);


-- ============================================================
-- DEAL PIPELINE
-- ============================================================

-- DEALS — tied to both an owner and a section
CREATE TABLE deals (
    deal_id         INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relationships
    owner_id        INTEGER NOT NULL REFERENCES owners(owner_id),
    section_id      INTEGER NOT NULL REFERENCES sections(section_id),
    stage_id        INTEGER NOT NULL REFERENCES pipeline_stages(stage_id),

    -- Deal info
    title           TEXT NOT NULL,
    value           REAL,
    nra             REAL,
    price_per_nra   REAL,

    -- Status
    status          TEXT NOT NULL DEFAULT 'open',
    lost_reason     TEXT,
    expected_close  TEXT,
    actual_close    TEXT,

    -- Metadata
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_deals_owner ON deals(owner_id);
CREATE INDEX idx_deals_section ON deals(section_id);
CREATE INDEX idx_deals_stage ON deals(stage_id);
CREATE INDEX idx_deals_status ON deals(status);


-- DEAL STAGE HISTORY — tracks every stage transition
CREATE TABLE deal_stage_history (
    history_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id         INTEGER NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
    from_stage_id   INTEGER REFERENCES pipeline_stages(stage_id),
    to_stage_id     INTEGER NOT NULL REFERENCES pipeline_stages(stage_id),
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_stage_history_deal ON deal_stage_history(deal_id);


-- ============================================================
-- ACTIVITY TRACKING
-- ============================================================

-- ACTIVITIES — calls, emails, notes, letters, etc.
-- Attached to the OWNER so they follow the person everywhere
CREATE TABLE activities (
    activity_id     INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relationships
    owner_id        INTEGER NOT NULL REFERENCES owners(owner_id) ON DELETE CASCADE,
    section_id      INTEGER REFERENCES sections(section_id),
    deal_id         INTEGER REFERENCES deals(deal_id),

    -- Activity details
    type            TEXT NOT NULL,
    subject         TEXT,
    body            TEXT,

    -- Call-specific fields
    call_duration   INTEGER,
    call_outcome    TEXT,
    call_recording_url TEXT,

    -- Email-specific fields
    email_direction TEXT,
    email_subject   TEXT,

    -- Letter-specific fields
    letter_type     TEXT,
    letter_sent_date TEXT,

    -- Metadata
    is_pinned       INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_activities_owner ON activities(owner_id);
CREATE INDEX idx_activities_section ON activities(section_id);
CREATE INDEX idx_activities_deal ON activities(deal_id);
CREATE INDEX idx_activities_type ON activities(type);
CREATE INDEX idx_activities_date ON activities(created_at);


-- ============================================================
-- FILE ATTACHMENTS
-- ============================================================

CREATE TABLE files (
    file_id         INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relationships (at least one must be set)
    deal_id         INTEGER REFERENCES deals(deal_id),
    owner_id        INTEGER REFERENCES owners(owner_id),
    section_id      INTEGER REFERENCES sections(section_id),
    activity_id     INTEGER REFERENCES activities(activity_id),

    -- File info
    filename        TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_size       INTEGER,
    file_type       TEXT,
    category        TEXT,

    -- Metadata
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_files_deal ON files(deal_id);
CREATE INDEX idx_files_owner ON files(owner_id);
CREATE INDEX idx_files_section ON files(section_id);
CREATE INDEX idx_files_category ON files(category);


-- ============================================================
-- PRICING HISTORY
-- ============================================================

CREATE TABLE pricing_history (
    pricing_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id      INTEGER NOT NULL REFERENCES sections(section_id) ON DELETE CASCADE,
    exit_price      REAL,
    cost_free_price REAL,
    effective_date  TEXT NOT NULL,
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_pricing_section ON pricing_history(section_id);
CREATE INDEX idx_pricing_date ON pricing_history(effective_date);


-- ============================================================
-- OPERATIONAL TABLES
-- ============================================================

-- CHANGE LOG — audit trail for data modifications
CREATE TABLE change_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name      TEXT NOT NULL,
    record_id       INTEGER,
    action          TEXT NOT NULL,
    old_values      TEXT,
    new_values      TEXT,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_changelog_table ON change_log(table_name);
CREATE INDEX idx_changelog_date ON change_log(changed_at);

-- CONTACT NOTES — per-contact notes
CREATE TABLE contact_notes (
    note_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id        INTEGER NOT NULL REFERENCES owners(owner_id),
    body            TEXT NOT NULL,
    is_pinned       INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_contact_notes_owner ON contact_notes(owner_id);
CREATE INDEX idx_contact_notes_date ON contact_notes(created_at);

-- LOGIN ATTEMPTS — rate limiting for gate password
CREATE TABLE login_attempts (
    attempt_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier   TEXT NOT NULL,
    ip_address   TEXT NOT NULL,
    attempted_at REAL NOT NULL
);

CREATE INDEX idx_attempts_identifier ON login_attempts(identifier);
CREATE INDEX idx_attempts_ip ON login_attempts(ip_address);


-- ============================================================
-- SEED DATA
-- ============================================================

-- Default pipeline stages (Haynesville)
INSERT INTO pipeline_stages (pipeline_name, name, sort_order) VALUES
    ('Haynesville', 'Interested', 1),
    ('Haynesville', 'Eval Requested', 2),
    ('Haynesville', 'Letter Offer Sent', 3),
    ('Haynesville', 'PSA Sent', 4),
    ('Haynesville', 'PSA Signed', 5),
    ('Haynesville', 'Due Diligence', 6),
    ('Haynesville', 'Curative', 7),
    ('Haynesville', 'Title Review Complete', 8),
    ('Haynesville', 'Closing Package Sent', 9),
    ('Haynesville', 'Ready to Close', 10),
    ('Haynesville', 'Seller Paid - Post Closing', 11);

-- Haynesville basin
INSERT INTO basins (name, state) VALUES ('Haynesville', 'LA');

-- Haynesville parishes
INSERT INTO parishes (basin_id, name, state) VALUES
    (1, 'DeSoto', 'LA'),
    (1, 'Red River', 'LA'),
    (1, 'Caddo', 'LA'),
    (1, 'Bossier', 'LA'),
    (1, 'Natchitoches', 'LA'),
    (1, 'Bienville', 'LA'),
    (1, 'Sabine', 'LA');

-- Known operators
INSERT INTO operators (name) VALUES
    ('EXP'),
    ('CHK'),
    ('GEP II'),
    ('Expand'),
    ('BPX'),
    ('LTO'),
    ('PLD'),
    ('Aethon'),
    ('Mesa');


-- ============================================================
-- TRIGGERS
-- ============================================================

CREATE TRIGGER trg_sections_updated AFTER UPDATE ON sections
BEGIN
    UPDATE sections SET updated_at = datetime('now') WHERE section_id = NEW.section_id;
END;

CREATE TRIGGER trg_owners_updated AFTER UPDATE ON owners
BEGIN
    UPDATE owners SET updated_at = datetime('now') WHERE owner_id = NEW.owner_id;
END;

CREATE TRIGGER trg_deals_updated AFTER UPDATE ON deals
BEGIN
    UPDATE deals SET updated_at = datetime('now') WHERE deal_id = NEW.deal_id;
END;

CREATE TRIGGER trg_ownership_updated AFTER UPDATE ON ownership_links
BEGIN
    UPDATE ownership_links SET updated_at = datetime('now') WHERE link_id = NEW.link_id;
END;

-- Auto-log deal stage changes
CREATE TRIGGER trg_deal_stage_change AFTER UPDATE OF stage_id ON deals
WHEN OLD.stage_id != NEW.stage_id
BEGIN
    INSERT INTO deal_stage_history (deal_id, from_stage_id, to_stage_id)
    VALUES (NEW.deal_id, OLD.stage_id, NEW.stage_id);
END;

-- Auto-update section people count when ownership links change
CREATE TRIGGER trg_ownership_insert_count AFTER INSERT ON ownership_links
BEGIN
    UPDATE sections SET people_count = (
        SELECT COUNT(*) FROM ownership_links WHERE section_id = NEW.section_id
    ) WHERE section_id = NEW.section_id;
END;

CREATE TRIGGER trg_ownership_delete_count AFTER DELETE ON ownership_links
BEGIN
    UPDATE sections SET people_count = (
        SELECT COUNT(*) FROM ownership_links WHERE section_id = OLD.section_id
    ) WHERE section_id = OLD.section_id;
END;
