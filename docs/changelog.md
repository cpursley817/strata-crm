# Mineral Buyer CRM — Changelog

## Session 18 — March 23, 2026

### Full Data Reimport with Per-Field Source Tracking
- Rebuilt reimport pipeline (`reimport_with_sources.py`) importing all 5 cleaned data files: AIS SQL dump, AIS Contact Directory, Aethon, idiCore, Pipedrive, Expand Pay Decks
- Every phone (1-6) and email (1-4) now tagged with origin source (e.g., `phone_1_source = 'idicore'`)
- Owner aliases populated from AKA data: 1,508 "aka" aliases from source files
- Total after reimport: 888,619 owners, 27,726 ownership links, 1,508 aliases, 100% source tag coverage

### Fuzzy Deduplication (Two Passes)
- **v1 (exact name grouping):** Groups by normalized name (uppercase, suffix-stripped), merges within groups based on address/phone/email overlap. Merged 11,702 duplicates. Created 6,350 "merged" aliases.
- **v2 (Levenshtein blocking):** Catches near-duplicates the v1 missed (e.g., "1010 Mineral LLC" vs "1010 Minerals LLC", "Abraham S Aufrichtig" vs "Abraham Aufrichtig"). Edit distance ≤ 2 with ratio ≥ 0.85, plus address/phone/email safety checks. Merged 979 additional duplicates.
- Final count: **875,938 owners** (down from 888,619 after reimport)

### Last Seen & Phone Type Data
- `populate_lastseen.py` populated phone_N_last_seen, phone_N_type, email_N_last_seen from idiCore data
- 838,889 owners with phone type data (Residential/Mobile/etc.)
- 13,577 owners with phone last_seen dates, 11,141 with email last_seen

### Contact Detail Panel Redesign
- **Tabbed layout** moved to top of panel: Contact Info | Sections | Deals | Associated | Activities
- **Contact Info tab** contains all default contact data (name, address, phones, emails, flags, quick actions, relatives, notes)
- **Aliases inline** under contact name ("aka: John Smith, J. Smith") for both AKA and merged aliases
- **White text** (#fff) replaced faded blue accent (#6b8cde) throughout the contact card
- **Phone sorting** by last_seen date (most recent first), verified as tiebreaker
- **"Seen: date"** displayed next to each phone and email
- **Source badges** inline with each phone and email (AIS, idiCore, Aethon, etc.)
- **Delete buttons** (red) on individual phone and email rows
- **Delete endpoints:** DELETE /api/owners/:id/phone/:slot and /api/owners/:id/email/:slot with change logging

### Contact List Table Updates
- Added **Sections count** column (how many sections a contact is linked to)
- Added **Sources count** column (number of data sources)
- `formatSourceName()` utility for human-readable source labels

### Codex Review Cycle 9 — 3 Findings (3 Adopted)
- (High/Bug) Delete button onclick passed event+field_name instead of numeric slot — fixed to pass integer slot directly
- (High/Security) Stored XSS in alt address and tel/mailto/sms href attributes — added sanitizePhone()/sanitizeEmail() utils, wrapped alt address in esc()
- (Med/Bug) Phone sort prioritized verified over last_seen — reversed to last_seen primary, verified tiebreaker

### Deployment
- All changes deployed to production (147.182.251.233): app.py, contacts.js, utils.js, index.html, mineral_crm.db (1.8GB)
- Service restarted and verified running

---

## Session 17 — March 20, 2026

### Data File Cleanup (5 files cleaned and approved)
All files cleaned, reviewed, and approved for import in next session:

1. **Aethon Owners (v5)** — 15,956 contacts. Proper case, classifications fixed, joint names split into individual contacts with AKA/associated links, C/O extracted, PO Box normalized, entity merge. 52% have phone, 39% have email (operator-confirmed).
2. **Expand Pay Decks (v2)** — 6,720 ownership records across 113 sections. Joint names kept (NRI tied to combined entity). Multi-section STRs deferred (972 rows). NRI formatted to 8 decimals. No estimated NRA (will be CRM-calculated).
3. **idiCore Contacts (v3)** — 16,001 contacts. Middle names extracted from entity names. Entity Name cleared for individuals. Phones sorted by Last Seen (most recent first). 99.8% have phone, 84% have email. Trust classification expanded (1,168 trusts caught). 183 near-duplicates merged.
4. **Pipedrive People (v2)** — 25,393 contacts linked to 674 sections. 2,235 within-section duplicates removed. Cross-section contact matching (23,386 unique contacts). Phones/emails consolidated from 7+ source fields.
5. **Pipedrive Sections** — 956 sections (57 Dead removed, 15 duplicates merged). Pricing, status, operator, assigned buyer, notes preserved. Ready to UPDATE existing 1,025 sections in CRM.

### Features Built
- **DNC System:** DNC badge (red) and RESERVED badge (yellow) shown in contacts table next to name. DNC rows dimmed to 60% opacity for visual distinction.
- **Human-Readable Display IDs:** New formatDisplayId() utility. Sections table shows BBR-S-00089 format. Section detail header shows display ID.
- **Section Page Enhancements:** SONRIS Wells + eClerk Records auto-links pre-filled with S/T/R. Contact Status Summary Bar showing owner status breakdown. Pricing Trend visual bar chart (green=Exit, blue=Cost-Free). Renamed pricing labels to Exit $/NRA and Cost-Free $/NRA.
- **Contacts Filter Fixes:** New GET /api/owners/states endpoint populates states dropdown with counts. Backend filters added for state, data_source, and deceased (moved from client-side). States dropdown shows "TX (245,000)" format.

### Performance Fixes
- **Contacts list query optimized:** Removed SELECT o.* (was returning all 50+ columns including massive relatives_json). Now returns only 22 columns needed for table display. Removed 3 correlated subqueries per row.
- **COUNT query eliminated for filtered results:** Was taking 10+ seconds when stacking filters. Now uses fast table COUNT for unfiltered, estimates for filtered. SELECT with LIMIT 25 returns instantly.
- **Composite indexes created on server:** (classification, state), (classification, is_deceased), (state, is_deceased). ANALYZE run to optimize SQLite query planner.

### Data Cleanup
- Full ALL CAPS → Title Case cleanup run on all 841K contacts. 36,675 names fixed, 1,202 classifications corrected. Script widened from edge-case-only to full scan with batched processing (10K per batch).

### Codex Review Cycle 8 — 2 Findings (2 Adopted)
- (High) SONRIS link XSS — fixed with encodeURIComponent
- (Med) Cleanup script memory — fixed with batched processing

### Pay Deck Import — Profiled but Deferred
- Expand pay deck profiled: 4,182 rows (Raw sheet), 58 unique S-T-Rs, 53 of 58 matched to existing sections (91%). Deferred because wrong deck files were in the imports folder.

### Project Reorganization
- All markdown files moved from repo root to docs/ folder: MASTER_FEATURE_LIST.md, NOTES.md, TODO.md, SYSTEM_GUIDE.md, requirements.txt

---

## Session 16 — March 19, 2026

### Features Built
- **Deal Deletion:** New DELETE /api/deals/:id endpoint with authorization (assigned user or admin/manager only). Atomic transaction with rollback. Structured JSON audit trail in change_log. Frontend delete button on deal detail page with confirmation dialog.
- **Phone Verification Attribution:** Migration 003 adds phone_N_verified_by and phone_N_verified_date columns. Backend saves user_id and date on verify, clears on unverify. Frontend shows "Verified [date]" next to verified phone stars.
- **Home Page Redesign:** Removed welcome banner and Quick Actions (duplicated nav). Compact stat bar. Two-column layout: left (pipeline + recent activity), right (quick links + alerts placeholder). Quick links moved from bottom to prominent position.
- **AI Assistant Conversation History:** Migration 004 creates assistant_conversations and assistant_messages tables. 7 new API endpoints (list/create/get/delete conversations, pin toggle, save message). Frontend redesigned with 240px sidebar showing conversation list, compact chat area. Conversations persist — messages survive navigation and logout. Auto-titles from first user message. Right-click context menu for pin/delete. Pinned conversations float to top.
- **User Creation Script:** scripts/create_user.py — interactive tool to add users on the server. Prompts for name, username, email, password, role. Uses werkzeug password hashing. New manager account created for boss.
- **Data Cleanup Script:** scripts/cleanup_names.py — proper case for ALL CAPS names/cities/addresses, collapses spaced abbreviations (L L C → LLC), McName normalization (Mc Donald → McDonald), reclassifies contacts after fix. 65 names fixed on production.

### Codex Review Cycle 7 — 8 Findings (7 Adopted, 1 Deferred)
- (High) Deal DELETE had no authorization — added assigned_user_id + admin/manager check
- (Med) Deal delete not atomic — wrapped in transaction with rollback
- (Med) Deal audit trail weak — structured JSON with all deal fields
- (High) Startup validation missing phone verification columns — added to REQUIRED_OWNER_COLS
- (Med) Phone verify audit omitted attribution — added verified_by + date to log
- (Med) "Mc Donald" not collapsed in cleanup script — added regex pre-pass
- (Low) Reclassification scope narrow — deferred (intentional design)
- (Low) JS syntax clean — no issues found

### Documentation Updates
- Master Plan PDF updated: marked completed Priority 0/1 items, added Map & GIS section with 5 new features (land grid, polygon selection, shapefile upload, side-by-side drilling map, viewport loading)
- All Session 15 map findings added to MASTER_FEATURE_LIST (Tier 12, items 12.2-12.8)
- TODO.md Priority 4 expanded with full map enhancement list

---

## Session 15 — March 19, 2026

### Security Audit & SSH Key Authentication
- Full security audit of GitHub repo, server, codebase, and git history
- Generated 7-page Security Assessment & Data Protection Report PDF for management
- GitHub repo confirmed PRIVATE (404 to unauthenticated users)
- No database, PII, or raw data files in repo — confirmed clean
- SSH key authentication configured (ed25519) — password auth disabled on server
- Only remaining security gap: HTTPS (requires domain purchase)

### Bug Fixes — 17 Findings Dump
Captured 17 findings from hands-on CRM testing. Fixes implemented in batches:

**Batch 1 (UI fixes):**
- #3: Removed coordinates display, added "Open in Google Maps" link under geocoded addresses
- #6: Added Age column to contacts table with inline DECEASED tag
- #8: Contact side panel auto-closes on page navigation (was overlapping map)
- #13: Section status changed from static badge to inline dropdown (immediate API update)
- #14: Renamed "#" column to "People" in sections table
- #16: Bulk action bar — floating bar appears when checkboxes selected (Export CSV, Clear)
- #17: Map defaults to Individual + Living Only + Louisiana. Added deceased filter. "Load Map" button replaces auto-load.

**Batch 2 (features):**
- #5: Added Unreserve button on contact detail (with confirmation dialog)
- #9: Added "Search in CRM" link next to each relative's name in contact detail

**Hotfixes (production bugs from batch 1):**
- Fixed closeOwnerPanel() crash — function called before contacts.js loaded (typeof guard added)
- Fixed stray closing brace in contacts.js that caused SyntaxError breaking all contact pages

**Performance fix:**
- #1: Contact card loading reduced from 5+ seconds to instant. Moved associated contacts query from get_owner() to new lazy-loaded endpoint GET /api/owners/:id/associated. Associated contacts now only load when user clicks the tab. Simplified phone matching to use phone_1 only (indexed).
- Database indexes created on server: phone_1, email_1, city, state, classification, full_name, mailing_address, contact_status, contact_notes.owner_id

### Codex Review Cycle 6 — 4 Findings (3 Adopted, 1 Deferred)
- (High/Security) XSS vulnerability in relative "Search in CRM" onclick — fixed with safe escaping + dedicated searchRelativeInCRM() function
- (Med) Map deceased filter was non-functional + initMap ignored UI defaults — wired up deceased param to backend, initMap now calls filterMap()
- (Med) People column hardcoded to 0 was a regression — restored original count logic
- (Low) Phone_1 index claim overstated — deferred; indexes created on server directly, not in schema.sql

### Documented for Future Sessions (not built yet)
- #2: Phone verification needs date + user attribution (schema change)
- #4: Social media links need saved login session or URL fields
- #7 + #15: Name/city proper case cleanup + classification fix for "L L C", "L P", "Mc Donald"
- #10: Home page full redesign
- #11: Deal deletion functionality
- #12: AI Assistant redesign + conversation history
- #17 (partial): Map layers, polygon selection, side-by-side drilling map, shapefile upload

---

## Session 14 — March 19, 2026

### Security — Credential Revocation (Priority 0 COMPLETE)
- GitHub Personal Access Token revoked and deleted (was exposed in Session 13 chat)
- Anthropic API key revoked and regenerated — new key deployed to server `.env`, verified working
- Server remote URL updated with new read-only PAT for git pull access
- `config/api_keys.env` deleted from repo (contained exposed key)
- `scripts/test_all.py` hardcoded password removed — now requires env vars
- `backend/server/app.py` fallback to `config/api_keys.env` removed — env-var-only

### Project Cleanup
- Deleted dead files: `start_crm.bat`, `start_crm.py`, `config/api_keys.env`, `docs/Buffalo_Nexus_Feature_List.pdf`, `database/mineral_crm.db.backup_before_ais`
- Removed 6 empty directories: `backend/api/`, `backend/services/`, `backend/utils/`, `database/seeds/`, `frontend/components/`, `integrations/strata-crm/bridge/`
- Removed 5 placeholder README files
- Moved 6 import scripts from `database/` to `scripts/imports/` — parameterized hardcoded session paths
- `.gitignore` updated: `/imports/` root-anchored so `scripts/imports/` is trackable

### Codex Review Cycle 5 — All 6 Findings Fixed
- (High) Hardcoded password in `test_all.py` removed
- (Med-High) `app.py` fallback to `config/api_keys.env` removed
- (Med) `SYSTEM_GUIDE.md` stale refs to `start_crm.bat/py` and `api_keys.env` updated
- (Med) Import script hardcoded session paths parameterized
- (Low-Med) `generate_master_plan.py` output path made repo-relative
- (Low) `SYSTEM_GUIDE.md` received real content updates (file tree, troubleshooting, AI config)

### Brain Dump — 6 Major Feature Modules (Tiers 13-18)
Captured, analyzed, and documented 6 new feature modules. Each idea brainstormed individually with full analysis, red flags, and suggested enhancements — all adopted.

- **Tier 13 — Mobile App & Calling:** Twilio click-to-call (Phase 1), native mobile app (Phase 2). Auto-recording, AI transcription, Claude call summaries, sentiment tagging, action item extraction, auto-status updates. Per-state consent handling.
- **Tier 14 — Messaging Portal & AI Chatbot:** SMS inbox (Twilio), AI chatbot for inbound owner responses. Offer letters → owner texts back → consent established → chatbot handles triage. Campaign tracking, template library, bot → human handoff. TCPA compliance.
- **Tier 15 — Owner Self-Service Portal:** Public "Request an Offer" page. Document upload (revenue statements as identity verification). AI parsing, auto-match to 841K contacts, verification tiers, document vault, instant estimate range.
- **Tier 16 — Management Controls:** Soft contact assignment by section, hard lock on deals or manager override. @mention tagged notes, notification center, inbound routing rules with SLA timers.
- **Tier 17 — Priority Scoring & Whale Detection:** Nightly scoring engine (priority_score per contact). Buyer auto-ranked priority queue. Manager whale dashboard with biggest movers, unassigned detection, geographic heat map.
- **Tier 18 — Call Analytics Engine:** Contextual call metrics (JustCall-inspired but CRM-integrated). Best time to call heat map, conversion funnel, age/parish segmentation, AI-powered per-contact optimal scheduling.

### UI Redesign — Deployed to Production
- **Header:** Tabs reordered (Home → AI Assistant | Deal Pipeline → Sections → Contacts | Map → Documents → Tools → Activities). Renamed "My Activity" to "Activities". Added nav separators. Larger centered search bar (380px). Active tab uses green bottom border.
- **Sections table:** Compact 32px rows with checkboxes. New column order: ID, Name, County/Parish, Status, Assigned, #, Exit $/NRA, Cost-Free $/NRA, Pricing Date, Operator. Renamed BBR Price → Exit $/NRA, CF Price → Cost-Free $/NRA. Color-coded status badges. Pricing date conditional coloring (green ≤30d, yellow ≤90d, red >90d). Operator filter added.
- **Contacts table:** Compact rows matching old contact manager design. Separate search inputs (name, phone, email). New columns: checkbox, Name, Type, Address, City, State, Phone, Email, Status, Updated, Flags. Flags column shows source badge + financial flag count badge. Added source and state filter dropdowns.
- **Contact detail panel:** Coordinates with clickable Google Maps link. Risk Flags section (red left border) moved up after contact info. All panel sections now have colored left borders.

### Data Dictionary — Full Rebuild with Pipedrive Merge
- Analyzed Pipedrive exports: Haynesville (2026-03-16, 5 files) and all-basins (2026-03-19, 3 files, 360K people, 10K orgs, 3.7K deals)
- **Contacts:** 77 → 110 fields. Added ownership data (NRA, NMA, decimal interest, ownership type, gross tract acres), instrument/title fields, external IDs (Enverus DI ID, mineral registry), call summary, job title, parent company, level of interest, BBR $/NRA per contact.
- **Sections:** 40 → 56 fields. Added state, survey, abstract, quarter call, WKT, DSU ID, BBR start price, BBR exit $/NMA, buyer status, section development, ownership data notes, source, research date, labels.
- **Deals:** 24 → 38 fields. Added pipeline, probability, won/lost times, last stage change, PSA signed date, auto extension date, title responsibility, SIV title link, pay status, label, participants, WKT.
- **Activities:** 16 → 18 fields. Added outcome, duration, direction, recording URL, transcription ID (for future call analytics/Twilio).
- **Dropdowns:** Added ownership_type, call_outcome, title_responsibility, pay_status option sets. NEW fields highlighted in blue text.

---

## Session 13 (cont.) — March 18, 2026

### Master Plan PDF — Completed Features Section Added
- Added "Completed Features — Sessions 8–13" section to `Buffalo_Nexus_Master_Plan.pdf`
- Organized into 5 tier blocks by session (Session 8 Foundation, 9 AIS Import, 10 Features, 11 Data/AI, 12 Enrichment, 13 Cloud)
- All 34 completed features listed with green [DONE] badges, same dark navy/green color scheme as remaining features
- PDF now 17 pages (was 12). Source: `docs/generate_master_plan.py`
- Confirmed Sessions 1–7 predate the changelog — Session 8 is the true project start

---

## Session 13 — March 18, 2026

### DigitalOcean Cloud Migration — COMPLETE

Strata is now live at **http://147.182.251.233** — accessible from any browser, anywhere.

**Server Provisioning**
- Ubuntu 24.04.4 LTS Droplet (2GB RAM, 50GB SSD, SFO3) — strata-crm, IP 147.182.251.233
- System updated (150 packages, kernel upgraded to 6.8.0-106-generic)
- Installed: Python 3.12, pip, python3-venv, nginx, git

**Application Deployment**
- GitHub repo cloned to `/var/www/mineral-crm` using Personal Access Token
- Python virtual environment created, all requirements.txt dependencies installed
- gunicorn 25.1.0 installed as WSGI server
- Gunicorn systemd service (`strata-crm.service`) created, enabled, running on startup
- nginx configured as reverse proxy (port 80 → gunicorn 127.0.0.1:5000)
- `.env` file created on server with FLASK_SECRET_KEY, ANTHROPIC_API_KEY, DATABASE_PATH

**Database Migration**
- mineral_crm.db (1,734MB) uploaded via SCP from Windows at 33.8MB/s (51 seconds)
- Database relocated to `/var/www/mineral-crm/database/mineral_crm.db` to match hardcoded DB_PATH
- Missing columns added: entity_name, alt_address, alt_city, alt_state, alt_zip, deceased_date
- Column name aliases fixed in app.py SELECT: zip_code AS zip, latitude AS lat, longitude AS lng
- login_attempts table created (missing from uploaded DB, required for rate limiting)

**Issues Resolved**
- SSH password auth failed initially — resolved by setting root password via DigitalOcean web console
- GitHub PAT auth failed interactively — resolved by embedding token in clone URL
- Sessions expiring every ~10 seconds — caused by `.env` using `SECRET_KEY` instead of `FLASK_SECRET_KEY`; fixed by correcting env var name
- Contact cards erroring — `entity_name` column missing from DB schema; added via ALTER TABLE
- Column name mismatch — DB uses `zip_code`, `latitude`, `longitude`; app expected `zip`, `lat`, `lng`; fixed with SQL aliases

**Verification**
- Login page renders at http://147.182.251.233 ✓
- Sessions persist across requests ✓
- Contact cards open with full detail ✓
- Map loads with geocoded coordinates ✓
- 841,565 contacts accessible from cloud ✓

---

## Session 12 — March 18, 2026

### Overnight Data Processing (Completed Unattended)
- **Mass geocoding:** 717,633 addresses geocoded (85.3% of 841K) via US Census batch API. 82,837 no match. 234 minutes runtime.
- **DOB computation:** 838,067 contacts now have date_of_birth column (estimated from static age field + Jan 2025 AIS snapshot date)

### New Features
- **Estimated Age (dynamic):** Frontend computes current age from DOB instead of static age field. Displays "Est. Age" label in badges and contact tables.
- **Phone/Email Labeling:** "Phone 1", "Phone 2", "Email 1", "Email 2" etc. labels in contact detail panel.
- **Financial Flags Display:** New "Financial Flags" section in contact detail showing HasBankruptcy, HasLien, HasJudgment, HasEvictions, HasForeclosures, HasDebt as color-coded badges. Only renders if contact has at least one flag. 297,561 contacts have at least one flag.
- **Relatives Display:** New "Relatives" section in contact detail parsing relatives_json. Shows name, estimated age, clickable phone (tel:), clickable email (mailto:), and location. Up to 3 relatives per contact. 800,201 contacts have relatives data.
- **Universal Search Bar:** Search input in top nav. Queries /api/search across contacts, sections, and deals simultaneously. Grouped dropdown results. Click to navigate. Escape to close.

### Security & Migration Prep
- Removed plaintext credentials from NOTES.md and SYSTEM_GUIDE.md
- Created `.gitignore` — excludes database files, API keys, import CSVs, log files, environment configs
- Created `requirements.txt` — Flask, flask-cors, anthropic, httpx
- DigitalOcean account created. Droplet (VPS) selected as deployment target for Flask/Python backend.

### AIS Enrichment (Confirmed)
- Financial flags imported: has_bankruptcy, has_lien, has_judgment, has_evictions, has_foreclosures, has_debt columns added
- Relatives imported: relatives_json column added with up to 3 relatives per contact (name, address, phone, email, age)
- Enrichment runtime: 78 seconds

### Frontend Changes
- `js/contacts.js`: dynamic age from DOB, phone/email labels, financial flags section, relatives section
- `js/app.js`: universal search bar, dropdown rendering, keyboard dismiss

---

## Session 11 — March 17, 2026

### Frontend Architecture Overhaul
- Split 125KB monolith `index.html` into 14 separate files (1 HTML, 1 CSS, 12 JS)
- Each page has its own JS file with documented functions
- Backend updated with `/css/` and `/js/` static file serving routes
- Zero logic changes — pure organizational refactor, all functionality preserved

### Data Quality
- **Name cleanup**: Fixed 8,803 names (Llc→LLC: 7,996, Lp→LP: 690, Llp→LLP: 114)
- **Classification populated**: All 841,565 contacts classified by name pattern (800K Individual, 21K Trust, 8K LLC, 6K Corp, 4K Business, 2K Estate)

### New Features
- **Associated Contacts**: New tab in contact detail panel showing contacts sharing phone/email/address, grouped by match type
- **AI Assistant**: Claude-powered chat interface for natural language CRM queries. Generates SQL, returns data tables, supports actions (update status, create deals, log activities). Config: `config/api_keys.env`
- **Logo fix**: Replaced broken base64 with actual buffalo-logo.png from assets folder

### New Documentation
- `SYSTEM_GUIDE.md`: Plain-English guide to entire system (for non-developers)
- `MASTER_FEATURE_LIST.md`: Prioritized feature backlog with 16 items across 4 tiers

### Backend Changes
- `app.py` grew from ~1,130 to ~1,498 lines
- New: `get_anthropic_client()` helper, `/api/assistant` POST endpoint, `/api/assistant/suggestions` GET endpoint
- New: `/css/` and `/js/` static file routes
- Associated contacts logic added to `get_owner()` response

---

## Session 10 — March 17, 2026

### Features Built (8 of 13 from Feature Dump)
- **Sections page redesign**: Sortable column headers on all 9 columns, pricing_date default sort DESC, total_contacts subquery, assigned user filter from lookups API, full section detail page with stat cards and tabbed owners/deals/pricing tables
- **Deal Pipeline overhaul**: Renamed to "Deal Pipeline", HTML5 drag-and-drop Kanban (cards draggable, columns are drop zones), moveDeal() API call on drop, pipeline stats bar (open deals, total value, stages), per-stage value totals
- **Contact Notes**: New `contact_notes` table, GET/POST /api/owners/:id/notes, DELETE /api/notes/:id, add form in owner panel, timestamped entries with author, legacy notes fallback
- **Phone verification stars**: phone_1_verified through phone_6_verified columns, PUT /api/owners/:id/verify-phone, clickable gold ★/outline ☆ in owner panel and contacts list
- **Contacts page redesign**: Renamed "Owners" → "Contacts", added Type/Source/Age/Deceased/Location columns, data source badges (AIS, Pipedrive, Pay Deck, idiCore), sortable Name/Location headers, deceased filter dropdown
- **Create Deal from contact**: "+ Create Deal" button on owner panel, modal with section/stage/NRA/price pickers, auto-calculated value, contact status quick-change dropdown
- **Home page personalization**: User-scoped dashboard (My Sections, My Deals, My Pipeline), welcome message, data coverage stats, uses /api/dashboard endpoint
- **Activity log overhaul**: Renamed to "My Activity", user-scoped, date filters (Today/Week/Month), expanded types (8 types with icons), activity stats bar, "+ Log Activity" modal with owner typeahead search

### Backend Changes
- `app.py` grew from ~1,068 to ~1,130 lines
- New `contact_notes` table via migration in ensure_auth_columns()
- New columns: owners.phone_1_verified through phone_6_verified
- New endpoints: notes CRUD, phone verification toggle
- Updated list_sections() with total_contacts subquery and expanded sort columns
- Owner detail now includes contact_notes in response

### Frontend Changes
- `index.html` grew from ~1,970 to ~2,500 lines
- 11 new JS functions: sortOwners, sourceBadge, showCreateDealForm, createDealFromContact, updateContactStatus, addContactNote, deleteContactNote, togglePhoneVerify, showLogActivityForm, submitLogActivity, moveDeal
- New CSS: pipeline stats, kanban drag states (.drag-over, .dragging), source badges, pipeline stat cards

---

## Session 9 — March 17, 2026

### AIS Data Import (Database Rebuild)
- Imported all 5 AIS CSV files into clean SQLite database
- 841,565 total owner records: 830,675 from SQL dumps + 10,890 from Contact Directory
- Fixed database corruption and OOM kills during import process
- Verified: all 16 tables present, PRAGMA integrity_check OK
- Data quality: 99.7% have phone, 82.7% have email, 838K have age, 80K deceased

### Feature Request Capture
- Captured 13 feature requests from user brainstorm session
- Established recommended build order (3 tiers)
- Created NOTES_session9.md to work around bindfs overwrite restriction

### Frontend Fixes
- Rewrote viewOwnerDetail() for dynamic HTML rendering into panel-body
- Rewrote viewSectionDetail() as full-page render with tabbed content
- Fixed data_source label mapping for AIS data source variants
- Tested Flask API with Python requests.Session() (curl doesn't handle cookies well)

---

## Session 8 — March 16, 2026

### Project Initialization
- Established project folder structure separating Strata (contact directory) from Mineral CRM (new system)
- Organized 300+ idiCore files by basin (Haynesville: 32, Permian: 111, Canadian: 19, Bakken: 12, Other: 126)
- Sorted document templates into letters/, psa/, closing/, mail-merge/
- Migrated Enverus integration code and research docs
- Migrated Pipedrive export data to imports/
- Created database schema design (see schema_design.md)

### Architecture Decisions
- **Separate systems**: Strata remains the contact research/import layer; Mineral CRM is the new relational system
- **Many-to-many data model**: Owners ↔ Sections via ownership_links junction table — solves Pipedrive's duplicate contact problem
- **SQLite for prototype**: Single-file database, no server setup needed. PostgreSQL for company-wide rollout.
- **11-stage deal pipeline preserved**: Interested → Eval Requested → Letter Offer Sent → PSA Sent → PSA Signed → Due Diligence → Curative → Title Review Complete → Closing Package Sent → Ready to Close → Seller Paid

### Database Build (Pipedrive Import — First Pass)
- Imported Pipedrive CSV exports into SQLite database
- Created 16+ tables: sections, owners, owner_aliases, ownership_links, deals, deal_stage_history, activities, files, pricing_history, users, login_log, change_log, basins, parishes, buying_groups, operators, pipeline_stages
- Initial data counts: 1,025 sections, 22,427 owners, 25,491 ownership links, 900 aliases, 823 deals
- Known limitation: Pipedrive data is the weakest source — lacks classification, geocoded addresses, rich contact metadata

### Frontend — Complete Rebuild
- Complete rewrite of index.html (~1,970 lines) to match the original Strata design system
- Restored horizontal top nav bar with green bottom border
- Restored Strata branding, color scheme, and design tokens
- Fixed all JavaScript API field name mappings
- Added owner detail side panel, 11 document templates, 5 calculators
- Map centered on Haynesville Basin with 3 base layers and marker clustering

### Backend (app.py — ~1,068 lines)
- Flask API serving the CRM on localhost:5000
- Auth: SHA-256 + salt password hashing, session-based
- Login matches on username, name, or email fields
- ensure_auth_columns() handles schema migration
- Key endpoints: auth, stats, sections, owners, deals, activities, search, dashboard, lookups

### Data Strategy Decision
- Rebuild database from scratch: AIS first (best contacts) → pay deck second (best ownership) → Pipedrive last (deal data only)

### Documentation
- Created architecture.md, schema_design.md, changelog.md, TODO.md, NOTES.md
