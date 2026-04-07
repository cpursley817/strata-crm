# Strata CRM — Notes & Worklog

Last updated: March 23, 2026 (Session 18)

---

## Quick Reference

### Login Credentials
- See admin for credentials — passwords must NOT be stored in project files
- Server password still needs reset (PowerShell quoting failed in Session 18, use Command Prompt instead)

### Data Source Quality Ranking
1. AIS — Best contact data (phones, emails, addresses, classification)
2. Pay deck — Best ownership data (NRA, interest amounts, section assignments)
3. idiCore — Supplemental skip tracing (phone lookups, address history)
4. Pipedrive — Deal pipeline data only (worst contact quality)

### Server Access
- **Live URL:** http://147.182.251.233
- **SSH:** `ssh root@147.182.251.233` (SSH key auth configured, password auth disabled)
- **Web Console (fallback):** cloud.digitalocean.com → strata-crm → Console
- **Gunicorn service:** `systemctl status strata-crm` / `systemctl restart strata-crm`
- **Nginx:** `systemctl status nginx` / `nginx -t` to test config
- **App logs:** `journalctl -u strata-crm -n 100 --no-pager`
- **Server .env:** `/var/www/mineral-crm/.env`

### Key File Locations (Local)
- Frontend: `/mineral-crm/frontend/app/index.html` (HTML only, ~260 lines)
- Frontend JS: `/mineral-crm/frontend/app/js/` (11 files, ~83KB total)
- Frontend CSS: `/mineral-crm/frontend/app/css/styles.css` (~19KB)
- Backend: `/mineral-crm/backend/server/app.py` (~1,550+ lines)
- Database (local): `/mineral-crm/database/mineral_crm.db` (1.8 GB)
- Database (server): `/var/www/mineral-crm/database/mineral_crm.db`
- AIS data: `/imports/ais/`
- Pay deck data: `/imports/paydecks/`
- Pipedrive data: `/imports/pipedrive/`
- idiCore data: `/imports/idicore/` (organized by basin)
- Templates: `/templates/` (letters, psa, closing, mail-merge)

### Database Stats (as of Session 18)
- 875,938 owners (reimported from 5 cleaned data files + deduplicated)
- 27,511 ownership_links (Pipedrive sections + Expand pay decks)
- 7,858 owner_aliases (1,508 aka + 6,350 merged)
- 1,025 sections
- 17+ tables total
- Per-field source tracking: every phone (1-6) and email (1-4) tagged with origin source
- 838,889 owners with phone type data, 13,577 with phone last_seen dates
- 9 active users, 11 parishes, 11 pipeline stages
- Data sources imported: AIS SQL dump, AIS Contact Directory, Aethon, idiCore, Pipedrive, Expand Pay Decks
- Fuzzy dedup: 12,681 total duplicates merged across two passes (exact name + Levenshtein)

### File Update Method (bindfs Workaround)
The mount allows creating new files and renaming, but NOT overwriting existing files. To update a file:
```bash
cp working_copy "/mount/path/file_new.ext"
mv "/mount/path/file_new.ext" "/mount/path/file.ext"
```

---

## Session 18 — March 23, 2026

### Full Data Reimport + Per-Field Source Tracking
- Rebuilt reimport pipeline importing all 5 cleaned files with per-field source tracking
- Every phone_N_source and email_N_source column now populated with origin (ais_sql_dump, idicore, aethon, pipedrive, etc.)
- Owner aliases populated: 1,508 from AKA data in source files
- Total after reimport: 888,619 owners, 27,726 ownership links

### Fuzzy Deduplication (Two Passes)
- v1 (exact normalized name): 11,702 merged, 6,350 "merged" aliases created
- v2 (Levenshtein blocking, edit distance ≤ 2): 979 additional merges
- Examples caught by v2: "1010 Mineral LLC" / "1010 Minerals LLC", "Abraham S Aufrichtig" / "Abraham Aufrichtig", "Alfred G Comegys" / "Alfred G. Comgys"
- Known limitation: names differing by >2 chars still won't match. Address/phone/email safety check prevents false positives.
- Final count: 875,938 owners

### Last Seen & Phone Type Population
- populate_lastseen.py matched idiCore data to populate phone_N_last_seen, phone_N_type, email_N_last_seen
- 838,889 with phone type, 13,577 with phone last_seen, 11,141 with email last_seen

### Contact Detail Panel Redesign
- Tabbed layout at top: Contact Info | Sections | Deals | Associated | Activities
- Aliases shown inline under name (aka + merged types)
- White text replacing faded blue accent throughout card
- Phones sorted by last_seen (most recent first), verified as tiebreaker
- Delete buttons on individual phones/emails with new backend DELETE endpoints
- Source badges and "Seen: date" inline with each data point

### Contacts Table Updates
- Added Sections count and Sources count columns
- formatSourceName() utility for human-readable labels

### Codex Review Cycle 9
- 3 findings, all adopted: delete onclick param mismatch, stored XSS in DOM construction, phone sort precedence
- Added sanitizePhone()/sanitizeEmail() utilities

### Remaining from This Session
- Server password not yet reset (PowerShell quoting issue — use Command Prompt)
- Improved fuzzy dedup could be run with higher edit distance threshold for entity names specifically
- CSS styles.css not modified — accent color var(--ac) still defined as #6b8cde but overridden inline in contact card

---

## Session 17 — March 20, 2026

### Data File Cleanup — 5 Files Approved for Import
- Aethon Owners v5: 15,956 contacts (phone/email from operator, split joint names, C/O extracted)
- Expand Pay Decks v2: 6,720 ownership records, 113 sections (NRI preserved, no est NRA, multi-section deferred)
- idiCore Contacts v3: 16,001 contacts (middle names extracted, phones sorted by recency, trust classification expanded)
- Pipedrive People v2: 25,393 contacts across 674 sections (within-section dedup, cross-section matching)
- Pipedrive Sections: 956 sections (Dead removed, pricing/status/operator/notes preserved)

Key decisions made during cleanup:
- Joint names in pay decks kept as-is (NRI belongs to combined entity, can't split)
- Multi-section STRs (& in STR) deferred to future session
- No estimated NRA in pay decks (CRM will calculate dynamically based on leased vs unleased)
- Contacts import AFTER sections so ownership links can reference existing section IDs
- Aethon phone/email data is operator-confirmed — highest quality contact data after AIS

### Features
- DNC badges (red DNC + yellow RESERVED) in contacts table, DNC rows dimmed
- Human-readable display IDs: formatDisplayId() utility, BBR-S-00089 format in sections
- Section detail: SONRIS + eClerk auto-links, contact status summary bar, pricing trend chart
- Contacts states dropdown populated from new /api/owners/states endpoint
- Backend filters: state, data_source, deceased all server-side now

### Performance
- Contacts list query: removed SELECT o.* (50+ cols → 22), removed 3 correlated subqueries per row
- Eliminated COUNT query for filtered results (was 10+ seconds for stacked filters)
- Composite indexes on server: (classification, state), (classification, is_deceased), (state, is_deceased)
- ANALYZE run on SQLite

### Data
- Full proper case cleanup: 36,675 names fixed, 1,202 reclassified
- Pay deck import profiled (Expand: 4,182 rows, 53/58 S-T-Rs matched). Deferred — wrong files.

### Codex Cycle 8
- SONRIS XSS fixed with encodeURIComponent
- Cleanup script batched (10K rows) instead of loading all 841K

### Reorganization
- All markdown files moved to docs/ folder

---

## Session 16 — March 19, 2026

### Features Built
- **Deal Deletion:** DELETE endpoint with authorization (assigned user or admin/manager), atomic transaction, structured JSON audit. Frontend delete button with confirmation.
- **Phone Verification Attribution:** 12 new columns (verified_by + verified_date per phone 1-6). Shows "Verified [date]" in contact detail panel. Startup validation updated to require new columns.
- **Home Page Redesign:** Removed welcome banner and Quick Actions. Compact stat bar at top. Two-column layout: pipeline + activity on left, quick links + alerts on right.
- **AI Assistant Conversation History:** Two new DB tables (assistant_conversations, assistant_messages). 7 new API endpoints. Frontend sidebar with conversation list (pin, delete, auto-title). Messages persist across sessions. Right-click context menu.
- **User Creation Script:** scripts/create_user.py for adding users via SSH. Created manager account for boss.
- **Data Cleanup:** 65 names fixed with proper case script. Mc Donald collapse fixed after Codex caught the bug.

### Codex Review Cycle 7
8 findings: 7 adopted, 1 deferred. Key fixes: deal authorization, atomic delete, startup validation, Mc Donald collapse.

### Documentation
- Master Plan PDF updated: Priority 0/1 completion status, new Map & GIS section
- MASTER_FEATURE_LIST expanded: Tier 12 now has 7 map features (land grid, polygon, shapefiles, side-by-side, viewport)
- All Session 15 findings fully captured in all docs (was previously missing map enhancements)

---

## Session 15 — March 19, 2026

### Security Audit & SSH Key Auth
- Full security audit: GitHub (private, no PII/credentials), server (gunicorn behind nginx, DB not web-accessible), git history (password in test_all.py — already changed)
- SSH key authentication: generated ed25519 key on Windows, added to server authorized_keys, disabled password auth in sshd_config
- Generated Security Assessment PDF (7 pages) for management presentation: 12 of 13 security checklist items SECURE, 1 PENDING (HTTPS)
- HTTPS blocked until domain purchased — only remaining security gap

### Bug Findings Dump (17 items)
Chase tested the CRM hands-on and reported 17 findings one-by-one with analysis/feedback loop. Categories: performance (1), data model (1), UI fixes (6), missing features (3), data quality (2), bugs (1), major redesigns (3), map enhancements (1).

**Implemented this session:**
- Contact panel auto-closes on nav (#8)
- Google Maps link under address, removed coordinates (#3)
- Age column + DECEASED tag on contacts table (#6)
- Section status inline dropdown (#13)
- Renamed # → People column (#14)
- Bulk action bar for checkboxes (#16)
- Map default filters + Load button (#17 partial)
- Unreserve button on contact detail (#5)
- "Search in CRM" link for relatives (#9)
- Contact card performance fix — lazy-loaded associated contacts (#1)
- Database indexes on server (9 indexes)

**Production bugs caused and fixed:**
- closeOwnerPanel() crash on load — typeof guard (contacts.js loads after app.js)
- Stray closing brace in contacts.js from coordinates refactor — SyntaxError broke all contact pages
- Lesson learned: always run `node -c` on all JS files before committing

**Codex Cycle 6:**
- XSS in relative search link (apostrophes in names like O'Neil) — fixed with dedicated function
- Map deceased filter non-functional — wired to backend
- People column hardcoded to 0 regression — restored

**Documented for future sessions:**
- #2: Phone verification date/user attribution
- #4: Social media links (need saved URLs)
- #7 + #15: Proper case cleanup for names/cities + "L L C" classification fix
- #10: Home page redesign
- #11: Deal deletion
- #12: AI Assistant redesign + conversation history
- #17: Map layers, polygon selection, shapefile upload, side-by-side drilling map

---

## Session 14 — March 18, 2026

### IMPORTANT — Manager Implementation Psychology (Build Before Rollout)

**Chase's note:** Many of the management features (whale dashboard, buyer comparisons, SLA timers, call analytics, conversion funnels) could have a negative effect on users if managers implement them too aggressively or use them as surveillance tools instead of coaching tools. The CRM will fail if buyers associate it with being watched rather than being helped.

**Action item (pre-rollout):** Research the psychology behind management implementation of new workplace systems. Topics to cover: change management theory, intrinsic vs. extrinsic motivation, surveillance vs. coaching dynamics, gamification psychology (when leaderboards help vs. harm), opt-in vs. forced adoption, transparency in data collection, and how to frame analytics as self-improvement tools rather than performance monitoring.

**Deliverable:** Build a **Manager Implementation Guide** specific to Strata that covers:
- How to introduce each feature category to the team (sequencing matters)
- What to say and what NOT to say when rolling out analytics and tracking
- How to use the whale dashboard and performance data for coaching conversations, not punishment
- When to share leaderboards (team morale is high) vs. when to keep them private (new hires, struggling reps)
- How to set SLA timers and goals that motivate without creating anxiety
- How to present the priority scoring engine as "the system helps you work smarter" not "the system tells you what to do"
- Red flags that indicate the system is being perceived negatively (declining logins, minimal call logging, feedback)
- Best practices from sales operations research (Gartner, HBR, etc.)

This guide should be written and reviewed BEFORE the management features go live to the team. It's not a technical doc — it's a leadership playbook.

### Brain Dump — 6 Major Feature Modules Captured

Captured and analyzed 6 new feature modules across Tiers 13-18 in MASTER_FEATURE_LIST.md. Each idea was brainstormed individually with detailed analysis, red flags, and suggested enhancements — all adopted by Chase.

**Tier 13 — Mobile App & Calling Infrastructure**
- Phase 1: Web-based click-to-call via Twilio with auto-recording, AI transcription (Whisper/Deepgram), and Claude-powered call summaries. Auto-extracts action items, tags sentiment, updates contact status.
- Phase 2: Full native mobile app (React Native/Flutter) as field companion. Syncs with web CRM. Offline mode.
- Legal flag: Louisiana is one-party consent, Texas is two-party. App needs per-state consent check.

**Tier 14 — Messaging Portal & AI Chatbot**
- SMS inbox in Strata (Twilio-powered). iMessage-style conversation threads per owner. Auto-logs to CRM.
- AI chatbot for inbound mineral owner texts. Workflow: mail offer letters with phone number → owners text back → consent established by inbound initiation → chatbot handles triage.
- Smart triage: classifies inbound as interested/questions/not interested/angry → different response flows.
- Campaign tracking: unique number per mailing auto-links to section/owner/deal.
- TCPA compliance, bot disclosure, opt-out management required. Lawyer review before launch.

**Tier 15 — Owner Self-Service Portal**
- Public "Request an Offer" page (offers.buffalobayou.com). Owners submit contact info + upload documents (revenue statements, leases).
- Revenue statements serve as identity verification — contains owner name, address, well/unit, operator, interest, payment amounts. Cross-referenced against 841K existing contacts.
- AI document parsing on upload (Claude extracts key fields). Auto-match to existing records.
- Verification tiers: Unverified (gray) → Contacted (yellow) → Verified Owner (green checkmark).
- Document vault, instant offer estimate range, referral tracking, buyer notification on submission.

**Tier 16 — Management Controls & Assignment System**
- Contact ownership model: Soft assignment by section (default) → Hard lock only on active deals or manager override.
- Contacts in overlapping sections visible to all assigned buyers. No ownership conflicts unless a deal is created.
- Whale assignment: when engineering portal shows high-value owner, manager assigns to top buyer.
- Tagged notes with @mentions, notification tiers (urgent/standard/FYI), notification center in nav.
- Inbound routing rules: visual rule builder, round-robin, SLA timers, auto-escalation.

**Tier 17 — Priority Scoring & Whale Detection**
- Nightly scoring engine: priority_score per contact based on NRA, pricing changes, permits, status, verified phone, recency, inbound activity. Stored on contact record for fast reads.
- Buyer dashboard: auto-ranked daily call list with reason tags ("Repriced +15%", "Inbound text"). "Start My Day" button loads #1 contact and advances through queue.
- Manager whale dashboard: system-wide value rankings, biggest movers, unassigned whale detection, buyer portfolio summary, geographic heat map, threshold-based auto-alerts.

**Tier 18 — Call Analytics Engine**
- Inspired by JustCall (screenshots reviewed) but integrated with CRM data for contextual metrics.
- Outcome tagging, best time to call heat map, age-bracket analysis, parish-level patterns, conversion funnel, anti-gaming metrics (connect rate > volume).
- AI-powered optimal call scheduling: per-contact best call window based on historical connect data.
- Architecture: single call_events table joins to contacts/sections/users for all analytics.

### JustCall Reference
- Screenshots captured from JustCall dashboard showing: call analytics (outbound/inbound/missed), busy hours heat map, best time to call heat map, agent analytics with leaderboard, campaign metrics.
- JustCall data was mostly empty — team didn't adopt it because it was a standalone dialer with no CRM context.
- Strata will do this better because call data lives alongside contact, deal, and section data.

### Security — Credential Revocation COMPLETE
- GitHub PAT revoked and deleted from GitHub settings
- Anthropic API key revoked → new key generated → deployed to server `/var/www/mineral-crm/.env` → verified AI assistant working
- Server git remote URL updated with new read-only PAT for pull access
- `config/api_keys.env` deleted from repo, `app.py` fallback removed, `test_all.py` hardcoded password removed

### Project Cleanup
- Deleted: `start_crm.bat`, `start_crm.py`, `config/api_keys.env`, old PDF, stale backup
- Removed 6 empty directories, 5 placeholder READMEs
- Moved import scripts to `scripts/imports/`, parameterized hardcoded paths
- Codex review cycle 5: all 6 findings adopted and fixed

### UI Redesign — Design Dump & Implementation
Chase provided design ideas one-by-one with analysis/feedback loop (same format as Session 11 brainstorm). Three design changes implemented and deployed to production:

**1. Header Redesign**
- Tabs reordered: Home → AI Assistant | Deal Pipeline → Sections → Contacts | Map → Documents → Tools → Activities
- Renamed "My Activity" → "Activities" (future-proofs for team-wide view)
- Nav separators between logical groups (subtle 1px dividers)
- Search bar enlarged to 380px and centered
- Active tab style changed from filled background to green bottom border
- Adopted enhancements: tab grouping separators

**2. Sections Table Redesign**
- Compact 32px rows (was ~48px), matching old contact manager density
- New column order: checkbox, ID, Name, County/Parish, Status, Assigned, #, Exit $/NRA, Cost-Free $/NRA, Pricing Date, Operator
- Renamed: BBR Price → "Exit $/NRA", CF Price → "Cost-Free $/NRA"
- Color-coded status badges (ACTIVE green, INACTIVE gray, EXHAUSTED orange, NO PRICE red)
- Pricing date conditional coloring: green (≤30 days), yellow (≤90 days), red (>90 days)
- Added: operator filter, select-all checkbox, EXHAUSTED/NO PRICE status options
- Adopted enhancements: conditional pricing colors, status badges, checkbox column, sticky header concept

**3. Contacts Table & Detail Panel Redesign**
- Compact rows matching previous contact manager screenshots Chase provided
- Separate search inputs: name, phone, email (was single combined search)
- New columns: checkbox, Name, Type, Address, City, State, Phone, Email, Status, Updated, Flags
- Flags column: source badge (AIS blue, Pipedrive orange, idiCore green) + financial flag count (red/orange number badge)
- Added filters: state, source
- Detail panel: coordinates with clickable Google Maps link, Risk Flags section with red left border (moved up after contact info), all sections have colored left borders
- Adopted enhancements: financial flags in list table, contact completeness concept, sticky filter bar concept

### Data Dictionary — Full Rebuild
- Analyzed both Pipedrive export sets (Haynesville 2026-03-16 + all-basins 2026-03-19)
- Identified 33+ new contact fields, 16 new section fields, 14 new deal fields from Pipedrive
- Rebuilt `docs/DATA_DICTIONARY.xlsx` from scratch: Contacts (110 fields), Sections (56), Deals (38), Activities (18), Dropdown Options (58 rows)
- All NEW fields highlighted in blue text. Full Pipedrive field mapping in column G.
- Key new field categories: Ownership Data (NRA, NMA, decimal interest, ownership type), Instrument/Title (number, date, type, link), External IDs (Enverus DI ID, mineral registry), Call Analytics (outcome, duration, direction, recording URL)

### Server Deployment
- All Session 14 changes deployed to production via `git pull` on DigitalOcean server
- Server remote URL updated from expired PAT to new read-only PAT
- Resolved `app.py` local changes conflict with `git checkout --`
- App verified working at http://147.182.251.233 with new UI

---

## Session 13 — March 18, 2026

### DigitalOcean Cloud Migration — COMPLETE

Strata is live at **http://147.182.251.233**. Full migration completed in a single session.

**Server Stack**
- DigitalOcean Droplet: strata-crm, Ubuntu 24.04.4 LTS, 2GB RAM, 50GB SSD, SFO3
- gunicorn 25.1.0 as WSGI server — 2 workers, bound to 127.0.0.1:5000
- nginx as reverse proxy — port 80 → gunicorn, 100MB max upload, 300s timeout
- Systemd service: auto-starts on reboot, restarts on crash

**Deployment Steps Completed**
1. System updated (apt upgrade, kernel 6.8.0-106), rebooted
2. Python 3.12, pip, venv, nginx, git installed
3. Repo cloned: `git clone https://<PAT>@github.com/cpursley817/mineral-crm.git /var/www/mineral-crm`
4. Virtual environment created, requirements.txt installed + gunicorn added
5. `.env` written to `/var/www/mineral-crm/.env` with FLASK_SECRET_KEY, ANTHROPIC_API_KEY, DATABASE_PATH
6. Systemd service file written to `/etc/systemd/system/strata-crm.service`
7. nginx site config written to `/etc/nginx/sites-available/strata-crm`, default site removed
8. mineral_crm.db uploaded via SCP from Windows (1,734MB in 51 sec at 33.8MB/s)
9. Database moved to `/var/www/mineral-crm/database/` to match hardcoded DB_PATH

**Schema Fixes Applied on Server**
- Added missing columns: entity_name, alt_address, alt_city, alt_state, alt_zip, deceased_date
- Created missing table: login_attempts (required for rate limiting at login)
- Fixed column name mismatches in app.py SELECT query: zip_code AS zip, latitude AS lat, longitude AS lng

**Issues Encountered and Resolved**
- SSH "Permission denied" — DigitalOcean imported GitHub SSH key; no root password set. Fixed via web console → `passwd`
- GitHub clone failed interactively — PAT doesn't paste correctly in web console. Fixed by embedding in clone URL
- Sessions expiring every ~10 seconds — `.env` used `SECRET_KEY` but app reads `FLASK_SECRET_KEY`. Fixed with `sed -i`
- Contact cards crashing — `entity_name` column missing. Added via ALTER TABLE
- Column name mismatch — local DB uses `zip_code/latitude/longitude`, app expected `zip/lat/lng`. Fixed with SQL aliases in SELECT

**Security Notes**
- GitHub PAT exposed in chat — MUST revoke and regenerate
- Anthropic API key exposed in chat — MUST revoke and regenerate
- Root password auth active — should upgrade to SSH key auth
- HTTPS not yet configured — HTTP only at this time

---

## Session 11 — March 17, 2026

### Comprehension Debt Audit
- Researched comprehension debt in AI-generated code (Addy Osmani, Simon Willison articles)
- Identified risks: 3,000-line monolith frontend, no tests, no separation of concerns
- Decision: stop adding features, reorganize codebase first

### Frontend File Split (14 Files)
Split the 125KB monolith index.html into 14 organized files:
- `index.html` — HTML structure only (26KB, was 125KB)
- `css/styles.css` — All visual styling (19KB)
- `js/utils.js` — Shared helpers: classBadge, statusBadge, esc, formatCurrency (3KB)
- `js/api.js` — apiCall() server communication (1KB)
- `js/app.js` — Login, navigation, theme, startup + DOMContentLoaded (6KB)
- `js/home.js` — Dashboard: loadDashboard, loadParishes (6KB)
- `js/sections.js` — Sections list + detail: loadSections, viewSectionDetail (16KB)
- `js/contacts.js` — Contacts list + detail panel: loadOwners, viewOwnerDetail + 12 more functions (27KB)
- `js/pipeline.js` — Kanban board: loadPipeline, moveDeal (5KB)
- `js/map.js` — Leaflet map: initMap, loadMapMarkers (3KB)
- `js/tools.js` — 5 calculators (3KB)
- `js/documents.js` — Document templates (4KB)
- `js/activity.js` — Activity log (9KB)
- `js/assistant.js` — AI Assistant chat UI (new)

Backend updated with `/css/` and `/js/` static file serving routes.

### System Guide Created
- `SYSTEM_GUIDE.md` — comprehensive plain-English guide to the entire system
- Explains every page, every API endpoint, every database table
- Written for someone with zero coding experience
- Includes glossary, troubleshooting, session history
- Will be updated with every future change

### Name Cleanup
- Fixed 8,803 names: Llc→LLC (7,996), Lp→LP (690), Llp→LLP (114), plus L.l.c. variants
- Zero remaining miscapitalized suffixes

### Contact Classification
- Populated classification for all 841,565 contacts (was 100% NULL)
- Name-pattern classification: Individual (800,470), Trust (21,534), LLC (7,949), Corporation (5,850), Business (3,856), Estate (1,906)

### Associated Contacts Feature (#5)
- Backend: New logic in get_owner() finds contacts sharing phone, email, or address
- Frontend: New "Associated" tab in contact detail panel, grouped by match type (Shared Phone, Shared Email, Same Address)
- Clickable associated contacts jump to their profile
- Tested with real data: 20 contacts at shared address correctly surfaced

### AI Assistant (#2)
- Backend: POST /api/assistant — sends user query to Claude Sonnet via Anthropic API
- Claude receives full database schema, generates SQL queries or takes actions
- Safety: Only SELECT queries allowed, no destructive SQL
- Actions supported: update contact status, create deal, log activity
- Backend: GET /api/assistant/suggestions — example queries
- Frontend: js/assistant.js — chat UI with suggestion chips, data tables, collapsible SQL
- Config: API key stored in config/api_keys.env

### Logo Fix
- Replaced broken base64 PNG logo with actual buffalo-logo.png in /assets/
- Both login screen and nav header updated

### Master Feature List Created
- `MASTER_FEATURE_LIST.md` — prioritized list of all remaining features
- 4 tiers: Fix Now, Build Next, Build Soon, Future
- 16 features tracked with status, effort estimates, and dependencies

### Social Media Search
- Added to master feature list: Search LinkedIn/Facebook buttons + URL storage fields
- Approach: generate pre-filled search URLs (free, legal), store URLs when found manually

### Evening Brainstorm — Major Feature Dump
Captured and organized ~70 new features across 12 tiers. Key new modules:
- **DigitalOcean cloud migration** (Priority 0) — private GitHub repo, env var config, PostgreSQL, multi-tenant folder structure, domain + HTTPS
- **Multi-tenant architecture** — separate code (IP) from data. Sell to other mineral companies.
- **Section page enhancements** (12 items) — pricing chart, activity timeline, mini map, ownership breakdown, "work this section" queue, SONRIS/eClerk auto-links, comparable sections, stale section warnings
- **User system + gamification** — profile/settings page, self-service signup, goal system (personal + manager-set, daily through yearly), streaks, leaderboards, achievement badges, team challenges
- **AI assistant v2** — conversation memory, report/dashboard/export generation, outreach assistance with preview/approval, Enverus queries, saved queries, scheduled reports, bulk operations, undo
- **Engineering/Pricing Portal** — ComboCurve integration, real-time per-owner valuations, multiple pricing scenarios. Separate product module.
- **Calendar system** — built-in calendar, auto follow-ups, overdue alerts, team view, Google Calendar sync
- **Section Master Database** — wells table, field orders, basin config, unit size, completeness dashboard, template variable registry
- **Legal/Title Research** — document index, runsheet generator, AI document reader, chain of title builder, interest calculator, alias/relationship extraction from documents
- **Data Import System** — templates, smart multi-pass matching, review queue, duplicate detection, merge tool, conflict resolution
- **Tools redesign** — revenue statement analyzer (Claude skill), Enverus formatter (Claude skill), unit economics calculator, title chain tool
- **Newsletters + weekly summaries** — user-configurable scheduled emails, auto-Friday reports to managers

### Session 12 Evaluation Cadence Established
- Run evaluation every 2 sessions: grade performance, check comprehension debt, identify improvements
- Claude to make executive decisions on code structure proactively — don't wait for Chase to notice problems
- Set standard: flag files over 500 lines, suggest splits before they become painful

---

## Session 12 — March 18, 2026

### Database Backup Created
- Copied mineral_crm.db (1.7GB) to backups folder + secondary location
- Added backup reminder to process — should happen every session

### Overnight Results
- **Geocoding complete:** 717,633 addresses geocoded (85.3% of 841K) via US Census batch API. 82,837 no match. 234 minutes.
- **DOB computed:** 838,067 contacts now have date_of_birth column (estimated from age + Jan 2025 snapshot)

### Features Built
- **Estimated age (dynamic):** Frontend computes age from DOB instead of using static age field. Shows "Est. Age" in badges and tables.
- **Phone/email labeling:** "Phone 1", "Phone 2" etc. labels in contact detail panel matching AIS data order. Same for emails.
- **Financial flags display:** New "Financial Flags" section in contact detail showing bankruptcy, lien, judgment, eviction, foreclosure, debt badges. Only appears if contact has flags.
- **Relatives display:** New "Relatives" section parsing relatives_json. Shows name, age, phone (clickable), email (clickable), location. Up to 3 relatives per contact.
- **Universal search bar:** Search input in top nav bar. Searches contacts, sections, and deals simultaneously. Dropdown shows grouped results. Click to navigate. Escape to close.

### Security Fixes
- Removed plaintext credentials from NOTES.md and SYSTEM_GUIDE.md
- Created .gitignore (excludes database, API keys, imports, logs)
- Created requirements.txt (Flask, flask-cors, anthropic, httpx)

### Migration Prep Started
- requirements.txt and .gitignore created
- DigitalOcean account created (March 18, 2026)
- Droplet (VPS) selected as deployment target — Ubuntu-based, runs Flask/Python directly
- Next: Git init → private GitHub repo → environment variable config → Droplet provisioning

### AIS Data Enrichment (Completed Session 11)
- Confirmed AIS source files accessible at /imports/ais/
- Financial flag columns BB:BG confirmed: HasBankruptcy, HasLien, HasJudgment, HasEvictions, HasForeclosures, HasDebt
- Relatives columns BJ+ confirmed: 3 relatives per contact with full contact info (name, address, phone, email, age)
- Database columns added (has_bankruptcy through has_debt)
- Enrichment script needs optimization — row-by-row DB lookups too slow for 2.4GB of CSVs. Will redesign with chunked batch approach next session.

### IP / Ownership Discussion
- Discussed legal risk of code ownership (built on company computer/time/data)
- Recommended: talk to IP attorney in Houston
- Technical strategy: separate code from data, multi-tenant architecture, private GitHub repo with timestamped commits
- Pricing/valuation data to come from Engineering Portal (not embedded in CRM)

---

## Session 10 — March 17, 2026

### Features Completed (8 of 13 from the feature dump)

**1. Sections Page Redesign (#13)**
Sortable column headers on all columns (name, parish, operator, status, BBR price, CF price, pricing date, contacts, assigned). Default sort is pricing_date DESC. Added total_contacts subquery in backend. Full section detail page with stat cards, detail grid, tabbed owners/deals/pricing tables. Assigned user filter dropdown populated from /api/lookups.

**2. Deal Pipeline — Drag-and-Drop (#10, #11)**
Renamed "Pipeline" to "Deal Pipeline" in nav. HTML5 drag-and-drop Kanban board — cards are draggable, columns are drop zones. moveDeal() API call updates deal stage on drop. Pipeline stats bar shows open deals, total value, stage count. Per-stage value totals displayed.

**3. Contact Notes (#8)**
New `contact_notes` table (note_id, owner_id, user_id, body, is_pinned, timestamps). GET/POST /api/owners/:id/notes, DELETE /api/notes/:id. Notes section in owner panel with add form, timestamps, author, delete. Legacy notes field shown as fallback.

**4. Phone Verification Stars (#6)**
New columns phone_1_verified through phone_6_verified on owners table. PUT /api/owners/:id/verify-phone toggles verification. Gold star (★) for verified, outline (☆) for unverified, clickable to toggle. Shows in both owner detail panel and contacts list table.

**5. Contacts Page Redesign (#4)**
Renamed "Owners" to "Contacts" in nav. New columns: Name (with deceased badge), Type, Status, Phone (with verification star), Email, Location, Age, Source, Sections. Sortable headers on Name and Location. Data source badges (AIS blue, Pipedrive green, Pay Deck gold, idiCore purple). Deceased filter dropdown. Expanded classification filter (Individual, Trust, Estate, LLC, Corporation, Business).

**6. Create Deal from Contact (#9)**
"+ Create Deal" button on owner detail panel. Modal form with Title (pre-filled), Section dropdown (1,025 sections), Stage dropdown (11 stages), NRA, Price/NRA. Auto-calculates deal value. Also added inline contact status quick-change dropdown.

**7. Home Page Personalization (#1)**
"Welcome back, Chase Pursley" greeting. Personal stats: My Sections (395), My Open Deals, My Deal Value. My Pipeline stage-by-stage cards. Data Coverage panel (phone %, email %, total sections, total deals). Contact Status breakdown. Uses /api/dashboard for user-scoped data.

**8. Activity Log Overhaul (#12)**
Renamed "Activity" to "My Activity" in nav. User-scoped (only logged-in user's activities). Date filters: Today, This Week, This Month, All Time. Expanded type filter: Call, Voicemail, Text, Email, Letter, Note, Document, Meeting. Activity stats bar with type icons. "+ Log Activity" modal with owner typeahead search.

### Technical Changes
- Backend: ~1,130 lines (was ~1,068). New endpoints for notes, phone verification. Updated list_sections() with total_contacts subquery. ensure_auth_columns() creates contact_notes table and phone_N_verified columns.
- Frontend: ~2,500 lines (was ~1,970). New JS functions: sortOwners, sourceBadge, showCreateDealForm, createDealFromContact, updateContactStatus, addContactNote, deleteContactNote, togglePhoneVerify, showLogActivityForm, submitLogActivity, moveDeal.

---

## Session 9 — March 17, 2026

### AIS Data Import
- Imported all 5 AIS CSV files into clean database rebuild
- 841,565 total owner records loaded (830,675 from SQL dumps, 10,890 from Contact Directory)
- Fixed database corruption and OOM kills during import
- Verified database integrity: all 16 tables present, PRAGMA integrity_check OK

### Feature Dump (13 Items)
Captured all 13 feature requests. Recommended build order established:
- Do first: Sections redesign, Deal Pipeline, Notes — all completed in Session 10
- Do second: Contacts redesign, Phone verification, Associated contacts, Create Deal — mostly completed in Session 10
- Do third: Home page, AI Assistant, Enverus, Activity log — home page and activity log completed in Session 10

### Frontend Fixes
- Rewrote viewOwnerDetail() to dynamically build HTML into panel-body (replaced static element references that broke when HTML was restructured)
- Rewrote viewSectionDetail() as full-page render with tabbed content
- Fixed data_source label mapping (ais_sql_dump → "AIS", ais_contact_directory → "AIS Directory")

---

## Session 8 — March 16, 2026

### Project Initialization
- Established folder structure. Organized 300+ idiCore files by basin. Sorted document templates. Migrated Enverus integration code. Migrated Pipedrive exports.

### Architecture Decisions
- Separate systems: Strata (contact directory) and Mineral CRM (new system)
- Many-to-many data model via ownership_links junction table
- SQLite for prototype, PostgreSQL for production
- 11-stage deal pipeline: Interested → Eval Requested → Letter Offer Sent → PSA Sent → PSA Signed → Due Diligence → Curative → Title Review Complete → Closing Package Sent → Ready to Close → Seller Paid

### Database Build (Pipedrive Import — First Pass)
- Created 16 tables. Imported Pipedrive data: 1,025 sections, 22,427 owners, 25,491 ownership links, 823 deals.
- Identified Pipedrive data as weakest source. Decided to rebuild from AIS data.

### Frontend Rebuild
- Complete rewrite of index.html (~1,970 lines) matching original Strata design system
- Horizontal top nav, dark theme, owner detail side panel, 11 document templates, 5 calculators, Leaflet map

---

## Ideas & Notes

- **[2026-03-16]** `[DATA]` Database rebuild strategy: AIS first → pay deck second → Pipedrive last.
- **[2026-03-16]** `[IDEA]` Enverus lease data per section — lease expirations could time outreach. Unleased acreage = acquisition opportunity.
- **[2026-03-16]** `[FEATURE]` Survey plats — upload and view plat images per section. Stretch: georeferenced overlay on map.
- **[2026-03-16]** `[FEATURE]` Pricing trend tracking — structured pricing_history table replaces Pipedrive notes-based tracking. Chart prices over time.
- **[2026-03-16]** `[PROCESS]` The old Strata design/layout is the target — horizontal nav, dark theme, owner detail side panel.
- **[2026-03-17]** `[FEATURE]` Associated contacts (#5) — show contacts sharing phone/email/address. Needs SQL query matching on shared data points.
- **[2026-03-17]** `[FEATURE]` AIS relatives (#7) — parse relatives_json field, display in profile, link to existing DB records if found.
- **[2026-03-17]** `[FEATURE]` AI Assistant (#2) — natural language search, smart suggestions, data quality alerts.
- **[2026-03-17]** `[FEATURE]` Enverus API (#3) — reconnect for live permits, rigs, completions. Needs API credentials and proxy setup.
