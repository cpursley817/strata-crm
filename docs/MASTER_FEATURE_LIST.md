# Strata CRM — Master Feature List
*Updated: March 23, 2026 — Session 18*

---

## PRIORITY 0 — Infrastructure (before new features)

### 0.1 DigitalOcean Cloud Migration
- **Status:** COMPLETE (Session 13)
- **What:** Move from local Windows machine to DigitalOcean cloud hosting. Accessible from anywhere, backed up, scalable.
- **Live at:** http://147.182.251.233
- **Stack:** Ubuntu 24.04 → nginx → gunicorn → Flask/Python → SQLite (1.7GB)
- **Remaining:** Domain + HTTPS (certbot), SSH key auth, revoke exposed API keys

### 0.2 Multi-Tenant Architecture Separation
- **Status:** PLANNED
- **What:** Separate the application code (your IP) from tenant data (company-specific). App is generic and reusable. Data is per-company.
- **How:** Restructure folders: `nexus-crm/` (product code) + `tenants/buffalo-bayou/` (config, branding, data). Environment variables for all company-specific settings. Basin-level data partitioning.
- **Effort:** 1-2 hours (part of migration)

### 0.3 PostgreSQL Migration
- **Status:** PLANNED
- **What:** Replace SQLite with PostgreSQL for concurrent users, backups, and scale.
- **How:** Convert schema (AUTOINCREMENT→SERIAL, datetime functions, etc.). DigitalOcean managed PostgreSQL ($15/mo) with automatic daily backups.
- **Effort:** 2-3 hours

### 0.4 Data Dictionary
- **Status:** WAITING ON CHASE
- **What:** Complete definition of all fields, dropdown choices, status options for contacts, sections, deals, and documents.
- **Why:** Drives database schema, form fields, filter options, multi-tenant configuration.

---

## TIER 1 — Fix Now (data integrity)

### 1.1 Age → Estimated Age (dynamic)
- **Status:** DONE (Session 12)
- **What:** DOB computed for 838K contacts. Frontend calculates Est. Age dynamically.

### 1.2 Phone/Email Labeling in Contact Detail
- **Status:** DONE (Session 12)
- **What:** "Phone 1", "Phone 2" etc. labels in contact detail. Same for emails.

### 1.3 AIS Data Enrichment (Financial Flags + Relatives)
- **Status:** DONE
- **What:** Imported HasBankruptcy, HasLien, HasJudgment, HasEvictions, HasForeclosures, HasDebt + up to 3 relatives per contact from AIS source files.
- **Results:** 297,561 contacts with financial flags. 800,201 contacts with relatives data. 78 seconds on local machine.
- **Verification:** has_debt: 81,774 | has_judgment: 60,167 | has_lien: 55,623 | has_bankruptcy: 36,873 | has_evictions: 11,673 | has_foreclosures: 5,698

### 1.4 Contact Classification Refinement
- **Status:** DONE (basic), NEEDS REVIEW
- **What:** 841K contacts classified by name pattern. May need tuning for edge cases. User wants Individual/Company/Trust as the three primary buckets (LLC+Corp+Business → Company, Estate → Trust).
- **Effort:** 15 min

---

## TIER 2 — Build Next (daily workflow)

### 2.1 Universal Search Bar in Header
- **Status:** DONE (Session 12)
- **What:** Search input in nav bar. Searches contacts + sections + deals. Grouped dropdown results. Click to navigate.

### 2.2 Do Not Contact + Reserved for Buyer
- **Status:** DONE (Session 17)
- **What:** DNC badge (red) and RESERVED badge (yellow) in contacts table. DNC rows dimmed to 60% opacity.

### 2.3 Deal Detail Page
- **Status:** NOT STARTED
- **What:** Full page per deal with editable fields, stage history, notes, documents, activity timeline.
- **Effort:** 2-3 hours

### 2.4 Clickable Stat Cards Everywhere
- **Status:** NOT STARTED
- **What:** All stat cards navigate to filtered views when clicked.
- **Effort:** 1 hour

### 2.5 Pipeline Full-Page View
- **Status:** NOT STARTED
- **What:** Compact columns or list view toggle so entire pipeline fits on one screen.
- **Effort:** 1 hour

### 2.6 Social Media Search + URL Storage
- **Status:** NOT STARTED
- **What:** "Search LinkedIn" / "Search Facebook" buttons on contact detail (pre-filled search URLs). Fields to save found URLs.
- **Effort:** 30 min

### 2.7 Click-to-Text Button
- **Status:** NOT STARTED
- **What:** Opens Messages app with number pre-filled. iMessage API doesn't exist.
- **Effort:** 30 min

---

## TIER 3 — Section Page Enhancements

### 3.1 Pricing History Chart
- **Status:** NOT STARTED
- **What:** Visual line chart of BBR and cost-free price over time on section detail page. Data already exists in pricing_history table.
- **Effort:** 1 hour

### 3.2 Section Activity Timeline
- **Status:** NOT STARTED
- **What:** New "Activity" tab on section detail showing all calls, emails, notes tied to that section.
- **Effort:** 30 min

### 3.3 Per-Section Mini Map
- **Status:** NOT STARTED
- **What:** Interactive Leaflet map on section detail showing only geocoded contacts for that section.
- **Depends on:** Geocoding (4.1)
- **Effort:** 1 hour

### 3.4 Ownership Breakdown Pie Chart
- **Status:** NOT STARTED
- **What:** Visual showing % of NRA accounted for vs unknown. Requires ownership_links data.
- **Effort:** 1 hour

### 3.5 Section Contact Status Summary
- **Status:** DONE (Session 17)
- **What:** Contact status summary bar on section detail showing breakdown of owner statuses.

### 3.6 "Work This Section" Button
- **Status:** NOT STARTED
- **What:** Generates prioritized call queue (largest NRA first, verified phones first).
- **Effort:** 1-2 hours

### 3.7 Section Assignment History
- **Status:** NOT STARTED
- **What:** Track who was assigned to this section and when it changed.
- **Effort:** 30 min

### 3.8 Attached Files + Generated Documents
- **Status:** NOT STARTED
- **What:** File upload system for deeds, title opinions, PSAs, etc. + "Generate Offer Letter" buttons using templates with auto-fill.
- **Effort:** 2-3 hours

### 3.9 SONRIS + eClerk Auto-Links
- **Status:** DONE (Session 17)
- **What:** Auto-generated links to SONRIS well search and eClerk records pre-filled with S/T/R on section detail page.

### 3.10 Comparable Sections
- **Status:** NOT STARTED
- **What:** Show sections in same parish with similar pricing for comp validation.
- **Effort:** 1 hour

### 3.11 Pricing Change Alerts + Stale Section Warnings
- **Status:** NOT STARTED
- **What:** Banners for recent pricing changes and sections with no activity in X days.
- **Effort:** 30 min

---

## TIER 4 — User System & Gamification

### 4.1 User Profile / Settings Page
- **Status:** NOT STARTED
- **What:** Personal info (name, email, phone, title, signature block), preferences (theme, default basin, default page, items per page), integrations (API keys), account management (change password, login history).
- **Effort:** 2-3 hours

### 4.2 Self-Service Signup + Account Creation
- **Status:** NOT STARTED
- **What:** "Create Account" on login page with name, email, password. Admin approval flow or invite code. Forgot password link.
- **Effort:** 1-2 hours

### 4.3 Goal System
- **Status:** NOT STARTED
- **What:** Personal goals (user-set) + manager-assigned goals. Timeframes: daily, weekly, monthly, quarterly, yearly. Progress bars, celebrations, goal templates. Goals: contacts reached, deals started, deal value, etc.
- **Effort:** 3-4 hours

### 4.4 Gamification System
- **Status:** NOT STARTED
- **What:** Streaks (consecutive activity days), leaderboards (toggleable), daily call counter in nav bar, achievement badges, completeness scores per contact/section, "hot streak" mode, first-contact-of-day bonus, deal velocity tracker, milestone celebrations, monthly MVP, basin race, team challenges, onboarding quest line, "undiscovered territory" pioneer badges.
- **Effort:** 4-5 hours (phased rollout)

### 4.5 Home Page as Command Center
- **Status:** NOT STARTED
- **What:** Priority sections/contacts for the week, section updates for assigned user, goal progress, suggested next action card, morning agenda, overdue follow-up alerts.
- **Effort:** 2-3 hours

---

## TIER 5 — AI Assistant Enhancements

### 5.1 Conversation Memory
- **Status:** NOT STARTED
- **What:** Assistant remembers previous messages in the chat for follow-up queries.
- **Effort:** 1 hour

### 5.2 Report / Dashboard / Export Generation
- **Status:** NOT STARTED
- **What:** "Generate a report of DeSoto sections" → formatted document or dashboard. "Export contacts in Section 12" → CSV download.
- **Effort:** 2-3 hours

### 5.3 Outreach Assistance with Preview/Approval
- **Status:** NOT STARTED
- **What:** Multi-step: "Send updated offers to owners in 12-10N-11W" → assistant asks template, prices → generates previews → user approves → executes. Pending actions queue.
- **Effort:** 4-5 hours

### 5.4 Enverus Data Queries
- **Status:** NOT STARTED
- **What:** "Show me sections with permits in last 6 months" — queries Enverus data tables via AI.
- **Depends on:** Enverus API connection (6.1)
- **Effort:** 1 hour (after Enverus connected)

### 5.5 Saved Queries / Report Templates
- **Status:** NOT STARTED
- **What:** Save frequent queries as one-click templates. "My Reports" section.
- **Effort:** 1-2 hours

### 5.6 Scheduled Reports
- **Status:** NOT STARTED
- **What:** "Every Monday, generate pipeline summary and email it." Ties into scheduled tasks.
- **Effort:** 2 hours

### 5.7 Bulk Operations with Approval
- **Status:** NOT STARTED
- **What:** "Mark all contacts in Section 12 as Attempted" → shows count → waits for approval.
- **Effort:** 1 hour

### 5.8 Undo Support
- **Status:** NOT STARTED
- **What:** Reverse actions taken through the assistant. Leverages change_log table.
- **Effort:** 1-2 hours

---

## TIER 6 — External Integrations

### 6.1 Enverus API Reconnection
- **Status:** NOT STARTED
- **What:** Live permits, rigs, completions, lease data → sections. Drilling activity on section pages.
- **Depends on:** Enverus API credentials
- **Effort:** 4+ hours

### 6.2 Engineering / Pricing Portal (ComboCurve)
- **Status:** NOT STARTED
- **What:** Separate portal integrating with petroleum engineer models + ComboCurve. Real-time values per section per NRA per owner. Multiple pricing scenarios (base/upside/downside). CRM consumes pricing, doesn't produce it.
- **Architecture:** Standalone service pushing data to CRM via API. Separate product module.
- **Effort:** Multi-session project

### 6.3 OpenCorporates Enrichment
- **Status:** NOT STARTED
- **What:** One-time batch enrichment for company contacts. Registration state, status, officers, filings.
- **Effort:** 2 hours

### 6.4 Automated Newsletters
- **Status:** NOT STARTED
- **What:** User-configurable scheduled emails. Content blocks: tasks, priority contacts, pipeline summary, section updates, goal progress, team leaderboard, aggregated industry news (RSS/Google News). Multiple newsletter profiles per user.
- **Requires:** Email delivery service (SendGrid/Mailgun)
- **Effort:** 3-4 hours

### 6.5 Weekly Summary Reports (Auto-Friday)
- **Status:** NOT STARTED
- **What:** Auto-generated Friday summary: contacts reached, deals created/advanced/closed, activities by type, sections worked, goal progress, notable events. Sent to user + their manager. Manager gets team rollup. Comparison to prior week. Exportable to PDF. Historical archive.
- **Effort:** 2-3 hours

---

## TIER 7 — Calendar & Scheduling

### 7.1 Built-in Calendar
- **Status:** NOT STARTED
- **What:** Calendar page + mini-calendar on home. Day/week/month views. Follow-up reminders, deal milestones, scheduled outreach, meetings, deadlines. Drag-to-reschedule. Color coding by type.
- **Effort:** 3-4 hours

### 7.2 Auto-Generated Follow-ups
- **Status:** NOT STARTED
- **What:** Log a call → "When should we follow up?" → calendar event created automatically.
- **Effort:** 1 hour

### 7.3 Overdue Alert System
- **Status:** NOT STARTED
- **What:** Missed follow-ups show as overdue in red. Roll forward until addressed.
- **Effort:** 1 hour

### 7.4 Team Calendar View (Manager)
- **Status:** NOT STARTED
- **What:** Managers see team calendars overlaid/side-by-side.
- **Effort:** 1-2 hours

### 7.5 Google Calendar Sync (Future)
- **Status:** NOT STARTED
- **What:** Bidirectional sync with Google Calendar.
- **Effort:** 2-3 hours

---

## TIER 8 — Section Master Database & Wells

### 8.1 Section Master Data Layer
- **Status:** NOT STARTED
- **What:** Comprehensive section records: unit name, unit size (acres), legal description, lat/lng, boundary GeoJSON. Single source of truth for calculations and templates.
- **Effort:** 2-3 hours

### 8.2 Wells Table
- **Status:** NOT STARTED
- **What:** Separate `wells` table (well_name, API14, operator, permit/spud/completion/first_prod dates, status, type, target formation, lateral length). Multiple wells per section. Target for Enverus sync.
- **Effort:** 2 hours

### 8.3 Field Orders Table
- **Status:** NOT STARTED
- **What:** Louisiana Office of Conservation field orders: order number, effective date, unit description, PDF attachment. Linked to sections.
- **Effort:** 1 hour

### 8.4 Basin Configuration
- **Status:** NOT STARTED
- **What:** `basins` table with basin-specific config: default royalty assumptions, pricing methodology, active operators, parishes. Data partitioned by basin_id (not separate databases).
- **Effort:** 1 hour

### 8.5 Section Completeness Dashboard
- **Status:** NOT STARTED
- **What:** % of master data filled per section. "Section 12: 45% complete — missing wells, field order, unit size."
- **Effort:** 1 hour

### 8.6 Template Variable Registry
- **Status:** NOT STARTED
- **What:** Maps template placeholders to section fields: {{unit_size}} → sections.unit_size. Self-documenting, easy to extend.
- **Effort:** 1 hour

---

## TIER 9 — Tools Page Redesign

### 9.1 Tools Page Reorganization
- **Status:** NOT STARTED
- **What:** Categories: Calculators (existing 5), Data Processing, Export Tools, Research. Drag-and-drop file upload zone.
- **Effort:** 1 hour

### 9.2 Revenue Statement Analyzer (Claude Skill)
- **Status:** NOT STARTED
- **What:** Upload revenue statement PDF → Claude extracts line items (owner, well, interest, revenue, deductions) → outputs clean workbook. Batch processing support.
- **Effort:** 2-3 hours

### 9.3 Enverus Lease Pull Formatter (Claude Skill)
- **Status:** NOT STARTED
- **What:** Takes raw Enverus export → reformats to user's preferred scratch sheet template. Multiple output templates supported.
- **Effort:** 2 hours

### 9.4 Unit Economics Calculator
- **Status:** NOT STARTED
- **What:** NRA × price/NRA → payback period, ROI, IRR based on estimated monthly royalty.
- **Effort:** 1 hour

### 9.5 Title Chain Tool
- **Status:** NOT STARTED
- **What:** Paste/upload chain of title → parse conveyances → calculate current ownership fractions. Stretch goal.
- **Effort:** 4+ hours

### 9.6 Saved Calculator Results
- **Status:** NOT STARTED
- **What:** "Save to Section" or "Save to Deal" buttons on calculator results.
- **Effort:** 30 min

---

## TIER 10 — Legal / Title Research

### 10.1 Document Index Manager
- **Status:** NOT STARTED
- **What:** Per-section list of recorded courthouse documents (type, date, book/page, grantor, grantee, instrument number). Searchable.
- **Effort:** 2-3 hours

### 10.2 Runsheet Generator
- **Status:** NOT STARTED
- **What:** Claude skill takes document index → generates formatted runsheet workbook. Chronological, columns pre-filled.
- **Effort:** 2 hours

### 10.3 AI Document Reader
- **Status:** NOT STARTED
- **What:** Upload deed/conveyance PDF → Claude extracts parties, date, legal description, interest, reservations. Auto-adds to document index.
- **Effort:** 2-3 hours

### 10.4 Chain of Title Builder
- **Status:** NOT STARTED
- **What:** Auto-build ownership chain from extracted documents. Show work + source docs. Flag gaps and uncertainties. Human validates.
- **Effort:** 3-4 hours

### 10.5 Interest Calculator
- **Status:** NOT STARTED
- **What:** Auto-calculate ownership fractions from chain of title. Shows math, requires approval.
- **Effort:** 2-3 hours

### 10.6 Alias/Address Extraction from Documents
- **Status:** NOT STARTED
- **What:** When documents show different names or addresses than contact record, auto-add as aliases and alternate addresses.
- **Effort:** 1 hour

### 10.7 Relationship Extraction from Documents
- **Status:** NOT STARTED
- **What:** When multiple parties appear on same document (family members on a lease, co-signers), create associated contact links with document reference.
- **Effort:** 1 hour

### 10.8 Title Status Tracking
- **Status:** NOT STARTED
- **What:** Per-section title status: Not Started / In Progress / Under Review / Complete / Has Defects. Column on sections table.
- **Effort:** 30 min

### 10.9 Title Cost Tracking
- **Status:** NOT STARTED
- **What:** Track abstracting fees, attorney fees, curative costs per section. Compare against deal value.
- **Effort:** 1 hour

### 10.10 Title Researcher Assignment
- **Status:** NOT STARTED
- **What:** Assign sections to title researchers, track their progress.
- **Effort:** 30 min

---

## TIER 11 — Data Import System

### 11.1 Import Template System
- **Status:** NOT STARTED
- **What:** Downloadable Excel templates for owner import. Column mapping UI for non-template files. Templates per data source (pay deck, title runsheet, AIS).
- **Effort:** 2 hours

### 11.2 Smart Matching Engine
- **Status:** NOT STARTED
- **What:** Multi-pass matching: exact name+address → fuzzy name → phone/email match → address match → no match (new). Match confidence scoring.
- **Effort:** 3-4 hours

### 11.3 Import Review Queue
- **Status:** NOT STARTED
- **What:** Three buckets: Auto-matched (green, bulk approve), Needs Review (yellow, confirm each), New Contacts (blue, confirm batch). Side-by-side comparison.
- **Effort:** 2-3 hours

### 11.4 Duplicate Detection + Merge Tool
- **Status:** NOT STARTED
- **What:** Post-import duplicate report. Merge tool: combine phones, emails, notes, activities, ownership into one record.
- **Effort:** 2-3 hours

### 11.5 Conflict Resolution Rules
- **Status:** NOT STARTED
- **What:** When import conflicts with existing data, configurable priority: pay deck > AIS > Pipedrive. Override option.
- **Effort:** 1 hour

### 11.6 Import History + Audit Trail
- **Status:** NOT STARTED
- **What:** Track every import: who, when, what file, match counts, new records created.
- **Effort:** 1 hour

---

## TIER 12 — Map & GIS

### 12.1 Mass Address Geocoding
- **Status:** DONE (Session 11/12)
- **What:** 717,633 addresses geocoded overnight via US Census batch API (85.3% match rate). Script: scripts/geocode_addresses.py

### 12.2 Land Grid Overlay (Section/Township/Range)
- **Status:** NOT STARTED
- **What:** Toggleable GeoJSON layer showing the Section-Township-Range grid over the Haynesville basin. Sourced from SONRIS/Louisiana DNR GIS data or public PLSS (Public Land Survey System) shapefiles. Each section polygon is clickable — shows section name and links to section detail page. Layer toggle in map control panel.
- **Effort:** 2-3 hours

### 12.3 Polygon Selection Tool
- **Status:** NOT STARTED
- **What:** Leaflet.draw plugin lets users draw rectangles, circles, and freeform polygons on the map. All contacts within the boundary get selected into a list panel on the side. That list is exportable, bulk-actionable (assign, change status, create mail merge), and clickable to open contact detail. Critical for field work — "draw a circle around this neighborhood and show me everyone inside."
- **Effort:** 2-3 hours

### 12.4 Shapefile Upload & Drag-and-Drop
- **Status:** NOT STARTED
- **What:** User uploads a .shp/.dbf/.shx bundle (or .geojson file) → server converts shapefile to GeoJSON using Python's fiona or geopandas → sends GeoJSON back to frontend → Leaflet renders it as a new toggleable layer. Drag-and-drop supported — user drops a file onto the map area, it gets processed and displayed immediately. Each uploaded layer appears in a layer control panel with a name, color picker, and on/off toggle. Layers persist per user session or saved to database for permanent layers.
- **Depends on:** geopandas or fiona on server
- **Effort:** 3-4 hours

### 12.5 Side-by-Side Drilling Activity Map
- **Status:** NOT STARTED
- **What:** Two map panels: left shows contacts (current map), right shows drilling activity (wells, permits, rigs, completions). Requires Enverus data. Uses Leaflet side-by-side plugin or two independent map instances with synced viewport (pan/zoom on one mirrors the other). Build dual-pane layout now, populate drilling map when Enverus is connected.
- **Depends on:** Enverus API connection (6.1)
- **Effort:** 2-3 hours

### 12.6 Viewport-Based Map Loading
- **Status:** NOT STARTED
- **What:** Only fetch markers visible in the current map bounds instead of loading all contacts for a state. As user pans/zooms, new markers are loaded dynamically. Requires backend spatial query (WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?). Eliminates the need to load 717K+ markers at once.
- **Effort:** 2-3 hours

### 12.7 Complete Haynesville Section Grid (Database)
- **Status:** NOT STARTED
- **What:** Section record for every S/T/R in the Haynesville. Source: SONRIS/DNR GIS data.
- **Effort:** 2 hours

### 12.8 Survey Plat Upload
- **Status:** NOT STARTED
- **What:** Upload plat PDFs/images per section.
- **Effort:** 1-2 hours

---

## TIER 13 — Mobile App & Calling Infrastructure

### 13.1 Mobile Companion App (Phase 1 — Web-Based Click-to-Call + Twilio)
- **Status:** NOT STARTED
- **What:** Start with web-based click-to-call button that triggers a call on the buyer's phone via Twilio integration. Records the call, auto-transcribes via Whisper/Deepgram/AssemblyAI, and generates an AI summary (Claude). This is the 80/20 version — 80% of the value of a native app at 20% of the effort.
- **Key features:** Auto-recording, AI transcription, AI call summary, AI-extracted action items (auto-create calendar events/tasks from "call back after April 1"), sentiment tagging (positive/neutral/negative), auto-status update (Not Contacted → Reached if answered, → Attempted if voicemail), pre-call screen with owner details/section info/pricing/suggested script.
- **Legal:** Louisiana is one-party consent. Texas is two-party — app needs per-state consent check or standard disclosure prompt. Recording disclosure for two-party states.
- **Depends on:** Twilio account, transcription API (Whisper/Deepgram/AssemblyAI)
- **Effort:** Multi-session

### 13.2 Native Mobile App (Phase 2)
- **Status:** NOT STARTED
- **What:** Full native mobile app (React Native or Flutter) as the field companion to the web CRM. Syncs with online program. All calls made through the app get recorded, transcribed, and summarized automatically. Offline mode for areas with poor cell service.
- **Effort:** Multi-session (major project)

---

## TIER 14 — Messaging Portal & AI Chatbot

### 14.1 SMS Messaging Portal (Twilio)
- **Status:** NOT STARTED
- **What:** New tab/portal in Strata for sending and receiving text messages. iMessage-style inbox UI with conversation threads per owner. Powered by Twilio SMS infrastructure. Messages auto-logged as activities on the owner's contact record.
- **Key features:** Real-time inbox, conversation threads per owner, send/receive SMS, auto-log to CRM activity, number provisioning, opt-out management (STOP keyword).
- **Legal:** TCPA compliance required. Inbound-initiated conversations give more flexibility. Must include opt-out language. FTC bot disclosure for AI responses.
- **Depends on:** Twilio account, dedicated phone numbers
- **Effort:** Multi-session

### 14.2 AI SMS Chatbot (Inbound Response Automation)
- **Status:** NOT STARTED
- **What:** Trained AI chatbot that responds to inbound text messages from mineral owners. Workflow: mail offer letters with a phone number → owners text back → consent is established by inbound initiation → AI chatbot handles initial response and triage. Human buyer can jump into any thread at any time.
- **Key features:** Campaign tracking (unique number per mailing → auto-links to section/owner/deal), smart triage (classifies inbound as: interested, questions, not interested, angry/emotional → routes accordingly), template library (pre-approved responses for common questions about NRA, PSAs, pricing), conversation → CRM auto-logging and status updates, scheduled follow-ups (bot creates tasks from "call me next week"), escalation path (bot → human handoff with full conversation history), multi-language support.
- **Architecture:** Twilio for SMS, Claude for response generation with locked system prompt (company tone, offer details, compliance rules). Human buyers see all conversations and can intervene.
- **Legal:** Bot disclosure required. Response frequency rules. Opt-out management. Lawyer review before launch.
- **Effort:** Multi-session

---

## TIER 15 — Owner Self-Service Portal

### 15.1 "Request an Offer" Public Portal
- **Status:** NOT STARTED
- **What:** Public-facing web page (e.g., offers.buffalobayou.com) where mineral owners can sign up, input contact information, and upload documents (revenue statements, leases) to request an offer. Document uploads serve as built-in identity verification — a revenue statement proves ownership with name, address, well/unit info, operator, interest type, and payment amounts.
- **Key features:** Clean signup form (no login required), document upload (revenue statements, leases, deeds, tax records), AI document parsing on upload (Claude extracts owner name, well/unit, operator, interest type, NRA, monthly revenue), auto-match to existing 841K contacts (name + address), verification tiers (Unverified gray → Contacted yellow → Verified Owner green checkmark), document vault per contact profile, instant offer estimate range after upload, referral tracking ("How did you hear about us?"), notification to assigned buyer on submission, CAPTCHA + email verification to prevent spam.
- **Architecture:** Separate public-facing section of Strata — no CRM login required for owner. Submissions appear in "New Submissions" queue in CRM with parsed data and matched records.
- **Privacy:** Encrypted document storage, clear privacy policy, data retention policy. Revenue statements may contain SSN — must handle securely.
- **Effort:** Multi-session

---

## TIER 16 — Management Controls & Assignment System

### 16.1 Contact Ownership Model (Soft Assignment, Hard Lock on Deals)
- **Status:** NOT STARTED
- **What:** Three-tier ownership model: (1) Section assignment — managers assign sections to buyers, all contacts in the section are available. (2) Overlap resolution — contacts in multiple sections visible to all assigned buyers, no conflict unless a deal starts. (3) Hard lock — contact locked to a buyer only when a deal is created (automatic) or manager manually assigns (whale scenario). Lock is global while deal is active; manager can override for different sections. Lock expires after 90+ days of inactivity (triggers manager review).
- **Key features:** Assignment dashboard for managers (workload per buyer), auto-assignment rules (parish-based), reassignment with handoff notes, visibility rules (locked contacts show banner but remain viewable), lock expiration on stale deals.
- **Depends on:** User Roles & Permissions (Tier 4)
- **Effort:** 3-4 hours

### 16.2 Tagged Notes & Notification System
- **Status:** NOT STARTED
- **What:** Managers can go anywhere in the system and add a note that tags a user via @mention and sends a notification. Universal notes system with polymorphic reference (entity_type + entity_id — works on contacts, sections, deals, or other notes).
- **Key features:** @mention auto-complete, notification tiers (urgent red push / standard in-app / FYI record-only), notification center (bell icon, unread count, click to jump to record), note types (Action Required, FYI, Question, Escalation), thread replies on notes, daily digest email option.
- **Effort:** 2-3 hours

### 16.3 Inbound Routing Rules
- **Status:** NOT STARTED
- **What:** Configurable rules for routing inbound messages (SMS), portal submissions, and calls to the right buyer. Visual rule builder UI with conditions (parish, section, contact type) and actions (assign to buyer, round-robin, manager queue).
- **Key features:** Fallback rules for unmatched inbound, round-robin distribution, SLA timers (text: 2hrs, portal: 24hrs — escalate to manager on expiry), auto-response on assignment ("Thanks for reaching out — a team member will be in touch shortly"), routing analytics (avg response time per buyer/channel/parish).
- **Depends on:** Messaging Portal (14.1), Owner Self-Service Portal (15.1)
- **Effort:** 2-3 hours

---

## TIER 17 — Priority Scoring & Whale Detection

### 17.1 Contact Priority Scoring Engine
- **Status:** NOT STARTED
- **What:** Background scoring engine that calculates a priority_score for every contact nightly. Scores drive the buyer's daily priority queue on their home dashboard — auto-ranked list of who to call today. Scoring factors (weighted, adjustable): portfolio value (when engineering portal is live), NRA size, recent pricing changes, new permits/rig activity (when Enverus is connected), contact status, verified phone, time since last contact, inbound activity (text/portal/call — highest priority), deceased/DNC exclusion. Each contact shows WHY it's ranked where it is (tag: "Repriced +15%", "Large NRA", "Inbound text"). List recalculates daily and flags what's new.
- **Key features:** "Start My Day" button (loads #1 contact's full profile, click Next to advance), priority score badge visible everywhere (contacts list, section detail, search results), weekly priority digest (Monday email: "Your top 10 priority contacts this week").
- **Architecture:** Nightly batch job writes priority_score to contacts table. Dashboard reads pre-computed scores — stays fast at 841K contacts. New scoring signals (Enverus, ComboCurve) plugged in as they come online.
- **Effort:** 3-4 hours

### 17.2 Manager Whale Dashboard
- **Status:** NOT STARTED
- **What:** System-wide high-value contact rankings visible to managers. Every contact across every section, every buyer, every parish — ranked by total portfolio value. Answers: where is the most unrealized value? Which contacts are unassigned? Which buyers are sitting on gold?
- **Key features:** Biggest Movers section (contacts with largest value change in 24hrs/7d/30d), unassigned whale detection (high-value contacts with no buyer — one-click assignment), buyer portfolio summary table (total assigned value, contacts, active deals, conversion rate per buyer), geographic heat map (portfolio value by section/parish), threshold-based auto-notifications (alert when contact crosses $100K, unassigned contact crosses $50K), deal velocity overlay (flag whales stuck in a stage too long).
- **Depends on:** Engineering/Pricing Portal (6.2) for real portfolio valuations. Works with available data (NRA, pricing) before that.
- **Effort:** 3-4 hours

---

## TIER 18 — Call Analytics Engine

### 18.1 Call Analytics Dashboard
- **Status:** NOT STARTED
- **What:** Deep performance tracking inspired by JustCall but built into the CRM where call data lives alongside contact, deal, and section data. Every call metric is contextual — not just "14 calls Tuesday" but "14 calls into DeSoto sections with pricing increases, 6 connects, 2 moved to Interested."
- **Key features:** Outcome tagging on every call (Connected, Voicemail, No Answer, Wrong Number, Disconnected, DNC — one tap after call ends), best time to call heat map (day × hour grid, builds from thousands of data points over 2-3 months), contact-type segmented analytics (Individual vs Trust vs LLC — different answer patterns), age-bracket analysis (connect rates by age group from estimated age data), parish-level heat maps (rural vs urban answer patterns), conversion funnel (Calls Made → Connected → Interested → Deal Created → Deal Closed), call streak tracking (feeds into gamification), manager comparison view (side-by-side buyer performance for coaching), weekly trend lines (all key metrics over time), export to PDF/CSV, scheduled weekly summary.
- **Anti-gaming:** Track connect rate and conversation duration, not just call volume. A buyer dialing 50 numbers and hanging up after 2 rings shows 0% connect rate.
- **Architecture:** Single `call_events` table: contact_id, user_id, section_id, timestamp, duration, direction, outcome, recording_url, transcription_id. All dashboards are aggregation queries against this table joined to contacts/sections/users.
- **Depends on:** Mobile App or Twilio integration (13.1) for automatic data capture. Manual call logging as fallback.
- **Effort:** Multi-session

### 18.2 AI-Powered Optimal Call Scheduling
- **Status:** NOT STARTED
- **What:** Once enough data exists, system recommends the best time to call each specific contact — not just a generic heat map. "John Smith: best window Tuesday 9-10am based on 3 previous connects." Priority queue factors optimal call window into daily ranking — contacts whose window is NOW get boosted.
- **Depends on:** Call Analytics (18.1) with sufficient data (2-3 months of call logging)
- **Effort:** 2-3 hours

---

## COMPLETED FEATURES

| # | Feature | Session |
|---|---|---|
| ✅ | Sections page redesign (sortable, filterable) | 9 |
| ✅ | Deal Pipeline rename + drag-and-drop Kanban | 9 |
| ✅ | Notes on contacts | 10 |
| ✅ | Contacts page redesign | 10 |
| ✅ | Phone verification stars | 10 |
| ✅ | Associated contacts (shared phone/email/address) | 11 |
| ✅ | Create Deal from contact | 10 |
| ✅ | Home page personalization | 10 |
| ✅ | Activity log overhaul | 10 |
| ✅ | Name cleanup (LLC/LP/LLP — 8,803 fixed) | 11 |
| ✅ | Frontend file split (14 files) | 11 |
| ✅ | Plain-English system guide (SYSTEM_GUIDE.md) | 11 |
| ✅ | AI Assistant (Claude-powered NL queries) | 11 |
| ✅ | Contact classification (841K classified) | 11 |
| ✅ | Unique IDs (owner_id, section_id, deal_id) | Built-in |
| ✅ | Logo fix (buffalo-logo.png) | 11 |
| ✅ | AIS financial flags enrichment (297K contacts) | 11 |
| ✅ | AIS relatives enrichment (800K contacts) | 11 |
| ✅ | Data dictionary spreadsheet (6 sheets) | 11 |
| ✅ | Investor/boss presentation (11 slides) | 11 |
| ✅ | Mass geocoding — 717,633 addresses (85.3%) | 11/12 |
| ✅ | DOB computed — 838K contacts | 12 |
| ✅ | Estimated age (dynamic from DOB) | 12 |
| ✅ | Phone/email labeling in contact detail | 12 |
| ✅ | Financial flags display in contact detail | 12 |
| ✅ | Relatives display in contact detail | 12 |
| ✅ | Universal search bar in header | 12 |
| ✅ | Credentials removed from project files | 12 |
| ✅ | .gitignore + requirements.txt created | 12 |
| ✅ | DigitalOcean cloud migration — live at 147.182.251.233 | 13 |
| ✅ | gunicorn + nginx production stack configured | 13 |
| ✅ | Database uploaded to cloud (1.7GB via SCP) | 13 |
| ✅ | SSH access from Windows terminal | 13 |
| ✅ | GitHub PAT revoked and regenerated | 14 |
| ✅ | Anthropic API key revoked and regenerated, deployed to server | 14 |
| ✅ | Project cleanup — dead files deleted, folders reorganized | 14 |
| ✅ | Codex review cycle 5 — 6 findings fixed (credentials, stale docs, paths) | 14 |
| ✅ | UI redesign — header reorder, nav separators, larger search bar | 14 |
| ✅ | UI redesign — sections table compact rows, new columns, status badges | 14 |
| ✅ | UI redesign — contacts table compact rows, flags column, separate searches | 14 |
| ✅ | UI redesign — contact detail panel: Google Maps, Risk Flags, colored borders | 14 |
| ✅ | Data dictionary rebuilt with Pipedrive field merge (110/56/38 fields) | 14 |
| ✅ | Master Plan PDF — completed features section added (17 pages) | 14 |
| ✅ | SSH key authentication + password auth disabled on server | 15 |
| ✅ | Security Assessment PDF (7-page report for management) | 15 |
| ✅ | Contact card performance fix — lazy-loaded associated contacts | 15 |
| ✅ | Database indexes (9) created on production server | 15 |
| ✅ | Contact panel auto-closes on page navigation | 15 |
| ✅ | Google Maps link under address (replaced coordinates) | 15 |
| ✅ | Age column + DECEASED tag on contacts table | 15 |
| ✅ | Section status inline dropdown (immediate save) | 15 |
| ✅ | Unreserve button on contact detail | 15 |
| ✅ | Relatives "Search in CRM" link | 15 |
| ✅ | Bulk action bar for checkboxes (sections + contacts) | 15 |
| ✅ | Map defaults (Individual, Living, LA) + Load button + deceased filter | 15 |
| ✅ | Codex cycle 6 — XSS fix, map filter wiring, People column restored | 15 |
| ✅ | Deal deletion with authorization + atomic transaction + audit trail | 16 |
| ✅ | Phone verification attribution (verified_by + verified_date per phone) | 16 |
| ✅ | Home page redesign (compact stats, two-column, quick links) | 16 |
| ✅ | AI Assistant conversation history (sidebar, persistent, pin/delete) | 16 |
| ✅ | User creation script (scripts/create_user.py) | 16 |
| ✅ | Data cleanup — 65 names fixed (proper case + Mc Donald collapse) | 16 |
| ✅ | Codex cycle 7 — deal auth, atomic delete, startup validation | 16 |
| ✅ | Map & GIS features documented (Tier 12: land grid, polygon, shapefiles) | 16 |
| ✅ | Master Plan PDF — Priority 0/1 completion marked, Map section added | 16 |
| ✅ | DNC badges + RESERVED badges in contacts table | 17 |
| ✅ | Human-readable display IDs (BBR-S-00089) | 17 |
| ✅ | Section detail: SONRIS/eClerk auto-links, status bar, pricing chart | 17 |
| ✅ | Contacts states dropdown + backend state/source/deceased filters | 17 |
| ✅ | Contacts list performance: optimized query + eliminated COUNT | 17 |
| ✅ | Full proper case cleanup: 36,675 names + 1,202 reclassifications | 17 |
| ✅ | Composite DB indexes for filter combos | 17 |
| ✅ | Codex cycle 8 — SONRIS XSS, batched cleanup | 17 |
| ✅ | Data cleanup: 5 import files cleaned + approved (Aethon, Expand, idiCore, Pipedrive people/sections) | 17 |
