# Mineral Buyer CRM — Database Schema Design

## Version: 2.0.0 | Date: March 17, 2026

## Current State
The database contains 841,565 owner records from the AIS import (Phase 1 complete). Pay deck data (Phase 2) and Pipedrive deal data (Phase 3) have not yet been imported into the clean database. The schema includes 17 tables with full audit logging.

## Core Design Principle
**One owner, one record, many sections.** The entire schema exists to solve the fundamental problem in Pipedrive: a mineral owner who owns in 10 sections should be ONE contact record linked to 10 sections — not 10 separate contacts with no connection.

## Entity Relationship Summary

```
basins ──< parishes
basins ──< sections
parishes ──< sections
operators ──< sections
buying_groups ──< sections
users ──< sections (assigned_user)

owners >──< sections  (via ownership_links — MANY-TO-MANY)

owners ──< deals
sections ──< deals
pipeline_stages ──< deals
users ──< deals (assigned_user)

owners ──< contact_notes
deals ──< deal_stage_history
sections ──< pricing_history
```

## Tables (17 total)

### Reference Tables
| Table | Purpose | Records |
|-------|---------|---------|
| basins | Operating basins (Haynesville, Permian, etc.) | 4-5 |
| parishes | Counties/parishes per basin | 11 |
| buying_groups | Mesa, Aethon, BPX, etc. | ~10 |
| operators | EXP, CHK, GEP II, etc. | ~20 |
| users | Buyers, managers, admins | 9 |
| pipeline_stages | Deal stages per basin pipeline | 11 |

### Core Tables
| Table | Purpose | Current Records | Production Est. |
|-------|---------|----------------|-----------------|
| sections | S-T-R units with pricing and status | 1,025 | 10,000+ |
| owners | Canonical contact records (ONE per person) | 841,565 | 2,000,000+ |
| owner_aliases | Alternate name forms for matching | 0 (pending import) | 500,000+ |
| ownership_links | Owner ↔ Section relationships with NRA/interest | 0 (pending pay deck) | 5,000,000+ |
| deals | Acquisition deals tied to owner + section | 0 (pending Pipedrive) | 50,000+ |
| contact_notes | Per-contact notes with timestamps and author | dynamic | 1,000,000+ |
| activities | Calls, emails, notes, letters on owner records | dynamic | 10,000,000+ |
| files | Document attachments on deals/owners/sections | TBD | 500,000+ |

### Tracking Tables
| Table | Purpose |
|-------|---------|
| deal_stage_history | Every stage transition for audit trail |
| pricing_history | All price changes on sections |
| login_log | User login audit trail |
| change_log | Data change audit trail |

## Key Fields on Core Tables

### owners
- `owner_id` (PK), `full_name`, `first_name`, `middle_name`, `last_name`, `suffix`
- `phone_1` through `phone_6`, `phone_1_type` through `phone_5_type`
- `phone_work`, `phone_home`, `phone_mobile`
- `phone_1_verified` through `phone_6_verified` (INTEGER DEFAULT 0) — **NEW in Session 10**
- `email_1` through `email_4`
- `mailing_address`, `city`, `state`, `zip_code`
- `classification` (Individual, Trust, Estate, LLC, Corporation, etc.)
- `contact_status` (Not Contacted, Attempted, Reached, Follow Up Needed, No Answer, Bad Contact Info)
- `age`, `is_deceased`
- `latitude`, `longitude` (geocoded from mailing address — not yet populated)
- `data_source` (ais_sql_dump, ais_contact_directory, pipedrive, paydeck, idicore)
- `dedupe_key`, `notes`, `relatives_json`
- `created_at`, `updated_at`

### contact_notes — **NEW in Session 10**
- `note_id` (PK, AUTOINCREMENT)
- `owner_id` (FK → owners, NOT NULL)
- `user_id` (FK → users, NOT NULL)
- `body` (TEXT, NOT NULL)
- `is_pinned` (INTEGER DEFAULT 0)
- `created_at` (TEXT, DEFAULT datetime('now'))
- `updated_at` (TEXT, DEFAULT datetime('now'))
- Indexes: `idx_contact_notes_owner(owner_id)`, `idx_contact_notes_date(created_at)`

### sections
- `section_id` (PK), `display_name`, `section_number`, `township`, `range`
- `parish_id` (FK → parishes), `basin_id` (FK → basins)
- `operator_id` (FK → operators), `buying_group_id` (FK → buying_groups)
- `assigned_user_id` (FK → users)
- `status` (Active, Research, Hold, Complete)
- `bbr_exit_price`, `cost_free_price`, `pricing_date`
- `people_count` (auto-updated by triggers)
- `section_notes`, `legal_desc`, `pricing_royalty`
- `latitude`, `longitude` (section centroid)

### ownership_links
- `link_id` (PK), `owner_id` (FK), `section_id` (FK)
- `nra`, `ownership_pct`, `royalty_interest`, `working_interest`
- `source` (title_research, pipedrive, idicore, ais, paydeck, manual)
- `interest_type`
- `verified`, `verified_date`

### deals
- `deal_id` (PK), `owner_id` (FK), `section_id` (FK)
- `stage_id` (FK → pipeline_stages), `assigned_user_id` (FK → users)
- `title`, `value`, `nra`, `price_per_nra`
- `status` (open, won, lost)
- `lost_reason`, `expected_close`, `actual_close`
- `created_at`, `updated_at`

## Key Design Decisions

### 1. Activities attach to OWNERS, not sections
When you call an owner, that call note lives on their owner record and is visible from every section they own in. Activities optionally link to a section (for context) and/or a deal, but the owner is the anchor.

### 2. Deals link to BOTH owner AND section
A deal is "buy minerals from Owner X in Section Y." You need both relationships to track what you're buying and from whom.

### 3. Pricing history is structured, not notes
Pricing changes are stored in a dedicated pricing_history table so you can query, chart, and compare across sections.

### 4. Contact notes are separate from legacy notes field
The `owners.notes` field contains imported legacy notes. The `contact_notes` table stores structured, timestamped notes with author tracking. Both are displayed in the UI.

### 5. Phone verification is per-phone-field
Each phone field (phone_1 through phone_6) has its own verified flag. Verification status persists across sessions and is tracked in the change_log.

### 6. Deduplication key on owners
The `dedupe_key` field stores a normalized hash of name + address for matching during imports.

### 7. Source tracking on ownership links
Every ownership link records where it came from and the source file for data provenance.

### 8. Pipeline stages are per-basin
Different basins may have different deal workflows. Stages are table-driven, not hardcoded.

### 9. Multi-source data model
Owner records track `data_source` and ownership links track `source`. The frontend displays color-coded source badges.

## Indexes
All foreign keys and frequently-queried columns are indexed. Key indexes:
- `sections(section_number, township, range)` — S-T-R lookup
- `owners(city, state)` — Geographic filtering
- `owners(dedupe_key)` — Import deduplication
- `activities(created_at)` — Chronological timeline views
- `ownership_links(owner_id, section_id)` — Junction table lookups
- `contact_notes(owner_id)` — Notes per owner
- `contact_notes(created_at)` — Chronological note views
- `change_log(table_name)`, `change_log(user_id)`, `change_log(changed_at)` — Audit queries
- `login_log(user_id)` — Login audit

## Triggers (auto-fire)
- `updated_at` timestamps auto-refresh on row updates
- Deal stage changes auto-log to `deal_stage_history`
- Ownership link inserts/deletes auto-update `sections.people_count`

## Migration Path: SQLite → PostgreSQL
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `TEXT` date fields → `TIMESTAMP WITH TIME ZONE`
- `REAL` → `NUMERIC(12,2)` for money fields
- Add connection pooling and row-level security for multi-user access
