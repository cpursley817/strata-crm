# Strata CRM — Master To-Do List

Last updated: March 23, 2026 (Session 18)

---

## COMPLETED — Session 8-13

### Database Foundation
- [x] Build AIS import pipeline and import all 5 CSV files (841,565 owners)
- [x] Verify database integrity (16 tables, PRAGMA integrity_check OK)
- [x] Auth system with SHA-256+salt, session-based login, login logging

### Frontend Features (Session 10)
- [x] Sections page redesign — sortable columns, pricing date, total contacts, assigned filter, full detail page
- [x] Deal Pipeline — renamed from "Pipeline", drag-and-drop Kanban, stats bar, per-stage values
- [x] Contact Notes — contact_notes table, add/delete notes on any contact, timestamps + author
- [x] Phone verification stars — clickable ★/☆ on each phone, toggle verified status
- [x] Contacts page redesign — renamed from "Owners", source badges, deceased flags, age, sorting
- [x] Create Deal from contact — modal form with section/stage/NRA/price picker
- [x] Home page personalization — user-scoped stats, My Pipeline, welcome message
- [x] Activity log overhaul — user-scoped, date filters, type icons, Log Activity form with owner search
- [x] Contact status quick-change dropdown on owner detail panel

### Frontend Foundation (Session 8)
- [x] Complete frontend rewrite matching Strata design system (~2,500 lines)
- [x] Horizontal top nav, dark theme, owner detail side panel (720px)
- [x] 11 document templates with type filter pills
- [x] 5 calculators: ODI, NRI, Lease Bonus, Royalty, Acreage
- [x] Leaflet map with 3 base layers, marker clustering
- [x] Login page, theme toggle, global search bar

### Session 11
- [x] Frontend file split — 125KB monolith → 14 organized files (HTML + CSS + 12 JS)
- [x] System guide (SYSTEM_GUIDE.md) — plain-English documentation for non-developers
- [x] Name cleanup — 8,803 names fixed (Llc→LLC, Lp→LP, Llp→LLP)
- [x] Contact classification — 841K contacts classified (Individual/Trust/LLC/Corp/Business/Estate)
- [x] Associated Contacts (#5) — new tab showing contacts sharing phone/email/address
- [x] AI Assistant (#2) — Claude-powered natural language CRM queries + actions
- [x] Logo fix — buffalo-logo.png serving correctly
- [x] Master feature list (MASTER_FEATURE_LIST.md) — prioritized backlog

### Session 12
- [x] DOB column computed — 838,067 contacts now have date_of_birth (estimated from age + Jan 2025 snapshot)
- [x] Mass geocoding — 717,633 addresses geocoded (85.3%) overnight via US Census batch API
- [x] Estimated Age (dynamic) — frontend computes age from DOB, shows "Est. Age" label
- [x] Phone/email labeling — "Phone 1", "Phone 2" etc. in contact detail panel
- [x] Financial Flags Display — badges in contact detail for bankruptcy, lien, judgment, eviction, foreclosure, debt
- [x] Relatives Display — up to 3 relatives per contact with clickable phone/email
- [x] Universal search bar — nav bar search across contacts, sections, and deals
- [x] Credentials removed from NOTES.md and SYSTEM_GUIDE.md
- [x] .gitignore and requirements.txt created
- [x] DigitalOcean account created — Droplet (VPS) selected for cloud deployment

### Session 14
- [x] GitHub PAT revoked and deleted
- [x] Anthropic API key revoked, new key generated and deployed to server
- [x] config/api_keys.env deleted, app.py fallback removed, test_all.py password removed
- [x] Project cleanup — deleted dead files, empty dirs, placeholder READMEs
- [x] Import scripts moved to scripts/imports/ with parameterized paths
- [x] Codex review cycle 5 — all 6 findings fixed
- [x] Brain dump: 6 new feature modules captured (Tiers 13-18, ~60 task items)
- [x] Manager implementation psychology note captured (pre-rollout requirement)
- [x] UI redesign: header reorder, nav separators, larger search bar
- [x] UI redesign: sections table — compact rows, new columns, status badges, pricing colors
- [x] UI redesign: contacts table — compact rows, separate search fields, flags column
- [x] UI redesign: contact detail panel — Google Maps link, Risk Flags section, colored borders
- [x] Data dictionary rebuilt from scratch — merged Pipedrive fields (110 contacts, 56 sections, 38 deals)
- [x] All changes deployed to production server
- [x] Server git remote URL updated with new PAT

### Session 15
- [x] Full security audit (GitHub, server, git history, data exposure)
- [x] Security Assessment PDF generated for management
- [x] SSH key authentication configured (ed25519, password auth disabled)
- [x] Contact panel auto-closes on page navigation (#8)
- [x] Google Maps link under address, coordinates removed (#3)
- [x] Age column + DECEASED tag on contacts table (#6)
- [x] Section status inline dropdown (#13)
- [x] Renamed # → People column (#14)
- [x] Bulk action bar for checkboxes (#16)
- [x] Map default filters (Individual, Living, LA) + Load button (#17)
- [x] Unreserve button on contact detail (#5)
- [x] "Search in CRM" link for relatives (#9)
- [x] Contact card performance: lazy-loaded associated contacts (#1)
- [x] Database indexes created on server (9 indexes)
- [x] Hotfix: closeOwnerPanel typeof guard
- [x] Hotfix: stray brace in contacts.js
- [x] Codex cycle 6: XSS fix, map deceased filter, People column restored

### Session 18
- [x] Full data reimport with per-field source tracking (phone_N_source, email_N_source for all 6 phones/4 emails)
- [x] Owner aliases populated from AKA data (1,508 aka aliases + 6,350 merged aliases)
- [x] Fuzzy dedup v1 — exact normalized name grouping with address/phone/email overlap (11,702 merged)
- [x] Fuzzy dedup v2 — Levenshtein blocking for near-duplicate names (979 additional merges, e.g. "1010 Mineral LLC" / "1010 Minerals LLC")
- [x] populate_lastseen.py — phone_N_last_seen, phone_N_type, email_N_last_seen from idiCore data (838K+ with phone type, 13.5K with phone last_seen)
- [x] Tabbed contact detail panel — tabs at top (Contact Info, Sections, Deals, Associated, Activities)
- [x] Contact Info tab — all default contact data reorganized into dedicated tab
- [x] Inline aliases under contact name ("aka: John Smith, J. Smith")
- [x] White text (#fff) replacing faded blue accent (#6b8cde) throughout contact card
- [x] Phone numbers sorted by last_seen date (most recent first), verified as tiebreaker
- [x] "Seen: date" display next to each phone/email
- [x] Source badges inline with each phone and email
- [x] Delete buttons (red) on individual phone and email rows
- [x] DELETE /api/owners/:id/phone/:slot and /api/owners/:id/email/:slot backend endpoints with change logging
- [x] Sections count and Sources count columns added to contacts table
- [x] formatSourceName() utility for human-readable source labels
- [x] sanitizePhone() and sanitizeEmail() utilities for XSS-safe href attributes
- [x] Codex review cycle 9 — all 3 findings fixed (delete param mismatch, stored XSS, phone sort order)
- [x] All changes deployed to production server (147.182.251.233)

### Session 17
- [x] DNC badges (red DNC + yellow RESERVED) in contacts table
- [x] Human-readable display IDs (BBR-S-00089 format)
- [x] Cleaned Aethon owners (15,956 contacts, v5 approved)
- [x] Cleaned Expand pay decks (6,720 ownership records, v2 approved)
- [x] Cleaned idiCore contacts (16,001 contacts, v3 approved)
- [x] Cleaned Pipedrive people (25,393 contacts, v2 approved)
- [x] Cleaned Pipedrive sections (956 sections, approved)
- [x] Section enhancements: SONRIS/eClerk auto-links, status summary bar, pricing chart
- [x] Contacts states dropdown + backend state/source/deceased filters
- [x] Contacts list query optimization (SELECT o.* → 22 cols, removed subqueries)
- [x] Eliminated COUNT query for filtered contacts (10s → instant)
- [x] Composite indexes: (classification, state), (classification, is_deceased), (state, is_deceased)
- [x] Full proper case cleanup: 36,675 names fixed, 1,202 reclassified
- [x] Codex cycle 8: SONRIS XSS fix, batched cleanup processing
- [x] Pay deck profiled (Expand) — deferred, wrong files
- [x] All markdown files moved to docs/ folder

### Session 16
- [x] Deal deletion — DELETE endpoint with authorization + atomic transaction + audit
- [x] Phone verification attribution — verified_by + verified_date columns, frontend display
- [x] Home page redesign — compact stat bar, two-column layout, quick links moved up
- [x] AI Assistant conversation history — sidebar, persistent messages, pin/delete
- [x] User creation script (scripts/create_user.py) — manager account created for boss
- [x] Data cleanup — 65 names fixed (proper case + Mc Donald collapse)
- [x] Codex cycle 7 — deal auth, atomic delete, startup validation, Mc collapse
- [x] Master Plan PDF — marked completed Priority 0/1, added Map & GIS section
- [x] Map features documented in MASTER_FEATURE_LIST (Tier 12: 7 items)

### Session 13 — Cloud Migration COMPLETE
- [x] Ubuntu 24.04 Droplet provisioned — strata-crm, 147.182.251.233, 2GB RAM / 50GB SSD
- [x] System updated, kernel upgraded to 6.8.0-106-generic
- [x] Python 3.12, pip, venv, nginx, git installed
- [x] GitHub repo cloned to /var/www/mineral-crm via PAT
- [x] Python venv created, all dependencies installed (Flask, anthropic, gunicorn, etc.)
- [x] gunicorn systemd service created and enabled (auto-starts on reboot)
- [x] nginx configured as reverse proxy (port 80 → localhost:5000)
- [x] .env file created on server with correct env var names
- [x] mineral_crm.db (1.7GB) uploaded via SCP in 51 seconds
- [x] Database relocated to /var/www/mineral-crm/database/ to match DB_PATH
- [x] Schema fixes: 6 missing columns added, column name aliases corrected in app.py
- [x] login_attempts table created on server
- [x] Root password set — SSH access working from Windows terminal
- [x] Strata live at http://147.182.251.233 — login, contacts, map all verified

---

## NEXT — Post-Migration Cleanup (Priority 0)

### Security
- [x] Revoke and regenerate GitHub Personal Access Token (was exposed in chat) — DONE Session 14
- [x] Revoke and regenerate Anthropic API key, update server .env — DONE Session 14
- [x] Remove config/api_keys.env from repo, remove app.py fallback — DONE Session 14
- [x] Remove hardcoded password from test_all.py — DONE Session 14
- [x] Set up SSH key authentication (ed25519 key, password auth disabled) — DONE Session 15
- [ ] Enable HTTPS — requires domain name pointed to 147.182.251.233, then Let's Encrypt SSL (certbot). No domain purchased yet.

### Quick Fixes (do after migration)
- [x] Social media search links (LinkedIn/Facebook) on contact detail — DONE (Session 11)
- [x] Click-to-text button on contact detail — DONE (Session 11)
- [x] Do Not Contact tags (DNC — contact requested + Reserved for Buyer — two separate systems) — DONE (Session 17)
- [x] Human-readable display IDs (BBR-C-00412, BBR-S-0089, BBR-D-0001) — DONE (Session 17)
- [ ] OpenCorporates one-time enrichment for company contacts

---

## PRIORITY 1 — Data Imports (Next Major Work)

### 1.1 Pay Deck Import (Best Ownership Data)
- [ ] Profile paydecks-Aethon-master.xlsx (13.5MB) — columns, data types, section format
- [ ] Profile paydecks-Expand-master.xlsx (1.2MB) — columns, overlap with Aethon
- [ ] Build pay deck import script — parse S-T-R references, owner names, NRA/interest amounts
- [ ] Match pay deck owners to existing AIS owner records (fuzzy name + address matching)
- [ ] Create new owner records for unmatched pay deck owners
- [ ] Populate ownership_links (owner ↔ section with NRA/interest)
- [ ] Validate import — check ownership counts per section, verify matching accuracy

### 1.2 Pipedrive Re-Import (Deal/Pipeline Data)
- [ ] Rebuild Pipedrive import to match against AIS+PayDeck owner records
- [ ] Import deals with correct owner_id and section_id foreign keys
- [ ] Import deal stage history
- [ ] Import activities (calls, notes, emails) linked to matched owners
- [ ] Resolve unmatched deal owners (32 known unmatched)
- [ ] Validate — verify deal counts, stage history, activity linkage

### 1.3 idiCore Integration
- [x] Profile 300+ idiCore files organized by basin
- [x] idiCore contacts cleaned (16,001, v3) and imported into CRM with per-field source tracking — DONE (Session 18)
- [x] Last seen dates and phone types populated from idiCore data — DONE (Session 18)
- [ ] Build idiCore import/matching pipeline for remaining basin files (only Haynesville done so far)

### 1.4 Geocoding
- [ ] Batch geocode all owner mailing addresses (latitude/longitude)
- [ ] Geocoding quality tracking (rooftop, range, approximate)
- [ ] Load map markers from geocoded addresses

---

## PRIORITY 2 — Remaining Feature Requests

### 2.1 Associated Contacts (#5) — DONE (Session 11)
- [x] SQL queries to find contacts sharing phone, email, or mailing address
- [x] "Associated Contacts" tab in owner detail panel (grouped by match type)
- [x] Click through to associated contact profiles

### 2.2 AIS Relatives (#7) — BLOCKED
- [ ] relatives_json column exists but is empty — needs re-import from AIS source
- [ ] Parse relatives, display in contact detail, link to existing DB records

### 2.3 AI Assistant (#2) — DONE (Session 11)
- [x] Natural language search via Claude Sonnet API
- [x] SQL generation from plain English queries
- [x] Action support: update status, create deals, log activities
- [x] Chat UI with suggestion chips, data tables, collapsible SQL
- [ ] Smart suggestions (next best action, recommended sections to work) — future enhancement
- [ ] Data quality alerts (missing phones, stale info, unworked sections) — future enhancement

### 2.4 Enverus API Reconnection (#3)
- [ ] Run Enverus --debug-fields to catalog all available fields
- [ ] Wire Enverus API to backend endpoints
- [ ] Per-section activity context: active rigs, permits, completions within radius
- [ ] Per-parish summary: total rigs, permit count, recent completions
- [ ] Lease data per section (expirations, operators, terms)
- [ ] Real-time alerts: new permits, rig movements, completions

---

## PRIORITY 3 — Contact Management Enhancements

- [ ] Click-to-copy on phone numbers and addresses
- [ ] Cross-source matching score display
- [ ] Bulk status update (select multiple owners → change status)
- [ ] Bulk classification update
- [ ] Bulk assign to buyer
- [ ] Contact search across ALL fields (name, phone, email, address, notes)
- [ ] Full-text search indexing for performance at scale

---

## PRIORITY 4 — Map Enhancements (Session 15 Findings + Original)

- [ ] Land grid overlay — Section/Township/Range grid from SONRIS/PLSS data, toggleable, clickable sections
- [ ] Polygon selection tool (Leaflet.draw) — draw boundaries, select contacts within, export/bulk-action list
- [ ] Shapefile upload with drag-and-drop — .shp/.geojson → server converts → Leaflet renders as toggleable layer
- [ ] Side-by-side drilling activity map — contacts on left, Enverus data on right, synced viewport
- [ ] Viewport-based map loading — only load markers in current map bounds (eliminates 717K+ full load)
- [ ] Survey plat overlays on map (georeferenced plat images)
- [ ] Map filters: parish, classification, status, verified phone (partially done — classification, state, deceased done)
- [ ] Color-coded markers by classification or status
- [ ] Click marker → open owner detail panel

---

## PRIORITY 5 — Pricing & Valuation

- [ ] Pricing history chart on section detail page (price per NRA over time)
- [ ] Parish-level pricing summary (avg, median, high, low per NRA)
- [ ] Basin-level pricing dashboard
- [ ] Price comparables — find similar sections to comp a price
- [ ] Wire calculators to save results to section/deal records

---

## PRIORITY 6 — Document Management

- [ ] Build mail_merge.py — generate personalized letters from templates
- [ ] PSA templates with auto-fill (owner name, section, NRA, price)
- [ ] Bulk mail merge — generate letters for all owners in a section
- [ ] Upload files to owner/section/deal records
- [ ] File categorization (deed, psa, oop, offer_letter, etc.)
- [ ] File preview in browser (PDF, images)

---

## PRIORITY 7 — Calling Module

- [ ] Click-to-call from owner detail panel
- [ ] Call logging — auto-create activity record
- [ ] Call outcome tracking (answered, no answer, voicemail, bad number)
- [ ] Call queue — list of owners to call per section, sorted by priority
- [ ] Bulk dialing mode — work through section owner list sequentially

---

## PRIORITY 8 — Analytics Dashboard

- [ ] Deal Pipeline chart (deals by stage, bar chart)
- [ ] Contact Status breakdown (pie/donut)
- [ ] Activity Timeline (calls, notes, emails over time, area/line chart)
- [ ] Section Coverage heat map (worked vs. unworked sections)
- [ ] Pricing Trends by section/parish (line chart over time)
- [ ] Conversion funnel (contact → interested → deal → closed)

---

## PRIORITY 9 — Production Readiness

- [ ] PostgreSQL migration (schema, connection pooling, row-level security)
- [ ] User roles and permissions (admin, manager, buyer, viewer)
- [ ] Per-basin pipeline configuration
- [ ] Map marker virtualization for 100K+ points
- [ ] Database query optimization for production scale

---

## SESSION 14 BRAIN DUMP — New Feature Modules (Tiers 13-18)

### Mobile App & Calling (Tier 13)
- [ ] Phase 1: Twilio click-to-call with auto-recording + AI transcription + Claude summaries
- [ ] Phase 2: Full native mobile app (React Native/Flutter) as field companion
- [ ] Per-state consent check (one-party vs two-party recording states)
- [ ] AI-extracted action items from call transcripts → auto-create tasks/calendar events
- [ ] Sentiment tagging (positive/neutral/negative) on every call
- [ ] Auto-status update on call outcome (Reached/Attempted)
- [ ] Pre-call screen with owner details, section info, pricing, suggested script

### Messaging Portal & AI Chatbot (Tier 14)
- [ ] Twilio SMS integration — send/receive texts from CRM
- [ ] iMessage-style messaging inbox with conversation threads per owner
- [ ] AI chatbot for inbound owner responses (Claude with locked system prompt)
- [ ] Campaign tracking — unique number per mailing → auto-link to section/owner/deal
- [ ] Smart triage — classify inbound (interested/questions/not interested/angry/wrong number)
- [ ] Template library for common responses (NRA explanation, PSA process, pricing)
- [ ] Bot → human handoff with full conversation history
- [ ] Scheduled follow-up texts from bot ("checking in per our conversation")
- [ ] TCPA compliance, bot disclosure, opt-out management

### Owner Self-Service Portal (Tier 15)
- [ ] Public "Request an Offer" page (offers.buffalobayou.com)
- [ ] Document upload (revenue statements, leases, deeds)
- [ ] AI document parsing on upload (Claude extracts key fields)
- [ ] Auto-match to existing 841K contacts (name + address)
- [ ] Verification tiers: Unverified → Contacted → Verified Owner
- [ ] Document vault per contact profile
- [ ] Instant offer estimate range on submission
- [ ] Referral tracking, buyer notification, CAPTCHA + email verification

### Management Controls & Assignment (Tier 16)
- [ ] Contact ownership model (soft assignment by section, hard lock on deals/manager override)
- [ ] Assignment dashboard for managers (workload per buyer)
- [ ] Auto-assignment rules (parish-based routing)
- [ ] Tagged notes with @mentions and notification tiers (urgent/standard/FYI)
- [ ] Notification center (bell icon, unread count, click to jump)
- [ ] Note types (Action Required, FYI, Question, Escalation) with thread replies
- [ ] Inbound routing rules — visual rule builder, round-robin, SLA timers
- [ ] Auto-escalation on missed SLA

### Priority Scoring & Whale Detection (Tier 17)
- [ ] Nightly scoring engine — priority_score per contact (NRA, pricing, status, recency, inbound)
- [ ] Buyer dashboard: auto-ranked daily priority queue with reason tags
- [ ] "Start My Day" button — loads #1 contact, click Next to advance
- [ ] Priority score badges visible everywhere (contacts list, section detail, search)
- [ ] Weekly priority digest (Monday email: top 10 contacts this week)
- [ ] Manager whale dashboard — system-wide value rankings
- [ ] Biggest movers, unassigned whale detection, buyer portfolio summary
- [ ] Geographic heat map (portfolio value by section/parish)
- [ ] Threshold-based auto-notifications for managers

### Call Analytics Engine (Tier 18)
- [ ] call_events table (contact_id, user_id, section_id, timestamp, duration, direction, outcome)
- [ ] Outcome tagging on every call (Connected, Voicemail, No Answer, Wrong Number, etc.)
- [ ] Best time to call heat map (day × hour, builds over 2-3 months of data)
- [ ] Contact-type segmented analytics (Individual vs Trust vs LLC)
- [ ] Age-bracket analysis (connect rates by estimated age group)
- [ ] Parish-level call pattern heat maps
- [ ] Conversion funnel (Calls Made → Connected → Interested → Deal → Closed)
- [ ] Manager comparison view (side-by-side buyer performance)
- [ ] AI-powered per-contact optimal call scheduling
- [ ] Weekly trend lines, export to PDF/CSV, scheduled reports

---

## BACKLOG

- [ ] Deal probability scoring based on engagement
- [ ] Predictive pricing model (historical data + Enverus)
- [ ] Integration with title company systems
- [ ] Automated county record searches
- [x] Duplicate detection — fuzzy dedup v1 (exact name) + v2 (Levenshtein) merged 12,681 total duplicates — DONE (Session 18)
- [ ] Duplicate detection dashboard (visual tool for manual review)
- [ ] Cross-basin owner matching
- [ ] Reporting builder (custom reports with filters, grouping, export)
