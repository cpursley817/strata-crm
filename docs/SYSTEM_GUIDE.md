# Strata CRM — System Guide

*Last updated: March 20, 2026 — Session 17*
*If you're reading this and Chase isn't around, this document tells you everything you need to know to understand, run, and maintain this system.*

---

## What Is Strata?

Strata is a personal CRM (Customer Relationship Management) application for **mineral rights acquisition** in the Haynesville basin in Louisiana. It tracks:

- **Sections** — geographic land parcels (identified by Section/Township/Range) where mineral rights exist
- **Contacts** — the 841,000+ people and entities who own those mineral rights
- **Deals** — active purchase negotiations with specific owners
- **Activities** — calls, texts, emails, and other outreach to owners

The system replaces a previous Pipedrive CRM and a separate contact directory, combining everything into one tool.

---

## How the System Is Built (The Big Picture)

Strata has **three parts** that work together:

```
┌─────────────────────────────────────────────────┐
│  YOUR BROWSER (Chrome)                          │
│  ┌───────────────────────────────────────────┐  │
│  │  Frontend — what you see and click on     │  │
│  │  (HTML + CSS + JavaScript files)          │  │
│  └──────────────────┬────────────────────────┘  │
│                     │ talks to                   │
│                     ▼                            │
│  ┌───────────────────────────────────────────┐  │
│  │  Backend — the "engine" that processes    │  │
│  │  requests and retrieves data              │  │
│  │  (Python program using Flask)             │  │
│  │  Runs on: http://147.182.251.233          │  │
│  └──────────────────┬────────────────────────┘  │
│                     │ reads/writes               │
│                     ▼                            │
│  ┌───────────────────────────────────────────┐  │
│  │  Database — where all the data lives      │  │
│  │  (SQLite file: mineral_crm.db)            │  │
│  │  841,565 contacts, 1,025 sections,        │  │
│  │  17 tables                                │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**In plain English:** When you open the app in Chrome, the browser loads the frontend files. Every time you search, filter, click a contact, or drag a deal — the frontend sends a request to the backend. The backend looks up or saves data in the database, then sends results back to the frontend to display.

---

## How to Access the App

**Cloud (live — use this):**
1. Open any browser
2. Go to **http://147.182.251.233**
3. Log in with your credentials

**Local (development only):**
1. Open a terminal in the `mineral-crm` folder
2. Activate the virtual environment and run Flask: `python -m backend.server.app`
3. Open Chrome and go to `http://localhost:5000`
4. Log in with your credentials

**Server Management (if something breaks):**
- SSH in: `ssh root@147.182.251.233`
- Check app status: `systemctl status strata-crm`
- Restart app: `systemctl restart strata-crm`
- View error logs: `journalctl -u strata-crm -n 100 --no-pager`
- Restart nginx: `systemctl restart nginx`

**If the app won't start** (says "Address already in use"):
- The server is probably already running. Either use it as-is, or open Command Prompt, type `fuser -k 5000/tcp` to kill it, then try again.

---

## Where the Files Live

Everything lives inside the `mineral-crm` folder. Here's what each subfolder contains:

```
mineral-crm/
├── MASTER_FEATURE_LIST.md ← All features (completed + planned) by tier
├── NOTES.md              ← Session notes and worklog
├── TODO.md               ← Master to-do list
├── SYSTEM_GUIDE.md       ← This file
├── requirements.txt      ← Python dependencies
│
├── backend/
│   └── server/
│       └── app.py        ← THE BACKEND — all server logic (~1,498 lines)
│                            This is the "engine" of the app
│
├── frontend/
│   ├── app/
│   │   ├── index.html    ← THE MAIN PAGE — loads in the browser
│   │   ├── css/          ← Styles (how things look)
│   │   │   └── styles.css
│   │   └── js/           ← JavaScript (how things behave)
│   │       ├── app.js        ← Startup, login, navigation, search
│   │       ├── api.js        ← All communication with the backend
│   │       ├── utils.js      ← Shared helper functions
│   │       ├── home.js       ← Home/dashboard page
│   │       ├── sections.js   ← Sections list + section detail page
│   │       ├── contacts.js   ← Contacts list + contact detail panel
│   │       ├── pipeline.js   ← Deal pipeline (Kanban board)
│   │       ├── deal.js       ← Deal detail page
│   │       ├── map.js        ← Interactive map
│   │       ├── tools.js      ← Calculators (ODI, NRI, bonus, etc.)
│   │       ├── documents.js  ← Document templates page
│   │       ├── activity.js   ← Activity log page
│   │       └── assistant.js  ← AI Assistant chat UI
│   └── assets/           ← Images, logos
│
├── database/
│   ├── mineral_crm.db   ← THE DATABASE — all your data (841K+ contacts)
│   ├── schema.sql        ← Database schema definition
│   └── migrations/       ← SQL migration scripts
│
├── scripts/
│   ├── imports/          ← One-time data import scripts (AIS, etc.)
│   ├── ais_enrichment.py ← AIS financial flags + relatives enrichment
│   ├── compute_dob.py    ← Estimated DOB from age field
│   ├── geocode_addresses.py ← US Census batch geocoding
│   └── test_all.py       ← Automated test suite
│
├── config/               ← Configuration templates (secrets via env vars only)
├── integrations/         ← External API integrations (Enverus, Pipedrive)
│
└── docs/
    ├── Strata_Master_Plan.pdf ← Full feature roadmap (17 pages)
    ├── architecture.md   ← Technical architecture overview
    ├── changelog.md      ← What changed in each session
    ├── review_log.md     ← Codex review findings log
    └── schema_design.md  ← Database table definitions
```

---

## Navigation Bar

The top navigation bar contains:
- **Page links** — Home, AI Assistant, Deal Pipeline, Sections, Contacts, Map, Documents, Tools, Activities
- **Universal Search** — A search input in the nav bar that searches contacts, sections, and deals simultaneously. Results appear in a grouped dropdown (Contacts / Sections / Deals). Click any result to navigate directly to it. Press Escape to close. This is the fastest way to find anything in the system.
- **Theme toggle** — Switch between dark and light mode
- **Logout button**

---

## The Pages of the App (What Each One Does)

### Home Page
**What it shows:** Welcome message, your personal stats (your sections, your open deals, your deal value), total contacts in the system, data coverage percentages, your pipeline stage summary, and quick-action buttons.

**How it works:** When you navigate to Home, the frontend calls two backend endpoints (`/api/dashboard` for your personal data and `/api/stats` for system-wide numbers), then displays the results.

**File:** `js/home.js` → function `loadDashboard()`

---

### Sections Page
**What it shows:** A sortable, filterable table of all 1,025 land sections. Each row shows the section name, parish, operator, status, exit pricing, cost-free pricing, pricing date, number of linked contacts, and assigned user.

**How it works:** Filters (parish, status, assigned user) and search text are sent to `/api/sections`. The backend queries the database and returns a paginated list. You can click column headers to sort. Clicking a section row opens the **Section Detail** page.

**Section Detail** shows full pricing history, all linked owners, and any deals tied to that section — organized in tabs (Owners / Deals / Pricing History).

**File:** `js/sections.js` → functions `loadSections()`, `sortSections()`, `viewSectionDetail()`

---

### Contacts Page (formerly "Owners")
**What it shows:** A searchable, filterable table of all 841,000+ mineral rights owners. Each row shows name, type (Individual/Trust/LLC/etc.), contact status, phone, email, location, age, data source, and number of linked sections.

**How it works:** Search text and filters (type, status, deceased/living) are sent to `/api/owners`. Results are paginated (25 per page). Clicking a contact opens the **Contact Detail Panel** — a slide-out panel on the right side of the screen.

**Contact Detail Panel** shows:
- Full contact info (all phones labeled "Phone 1", "Phone 2" etc., all emails labeled "Email 1", "Email 2" etc., address)
- Estimated age (computed dynamically from date of birth — updates automatically)
- Phone verification stars (click to mark a phone as verified — turns gold)
- Action buttons: Create Deal, Change Status
- Tabbed sections: Sections (linked properties), Deals, Associated, Activity
- Notes section: add/delete timestamped notes about this contact
- **Financial Flags section**: Displays color-coded warning badges for bankruptcy, liens, judgments, evictions, foreclosures, and debt. Only appears if the contact has at least one flag. 297,561 contacts in the database have flags.
- **Relatives section**: Shows up to 3 relatives from AIS data, each with name, estimated age, clickable phone number, clickable email, and location. 800,201 contacts have relatives data.
- **Associated Contacts tab**: Shows other contacts who share a phone number, email address, or mailing address with this contact. Matches are grouped by type (Shared Phone, Shared Email, Same Address). Click any associated contact to view their detail panel. This helps identify family members, business partners, or duplicate records.

**File:** `js/contacts.js` → functions `loadOwners()`, `viewOwnerDetail()`, `addContactNote()`, `togglePhoneVerify()`

---

### Deal Pipeline Page
**What it shows:** A Kanban board (columns for each deal stage: Lead, Contacted, Negotiating, Under Contract, Closed Won, Closed Lost). Each deal is a card showing the deal title, owner name, section, and value.

**How it works:** Deals are loaded from `/api/deals` and grouped by stage. You can **drag and drop** cards between columns to move a deal to a different stage. The backend updates the deal's stage when you drop it.

**File:** `js/pipeline.js` → functions `loadPipeline()`, `moveDeal()`

---

### Map Page
**What it shows:** An interactive map (powered by Leaflet.js) showing owner locations as markers. When there are many markers close together, they cluster into numbered bubbles.

**How it works:** Loads owner location data and plots markers. Click a marker to see the owner's name and contact info.

**File:** `js/map.js` → functions `initMap()`, `loadMapMarkers()`

---

### Tools Page
**What it shows:** Five mineral-rights calculators:
1. **Ownership Decimal Interest** — converts a fraction (like 1/320) to a decimal
2. **Net Revenue Interest** — calculates NRI from gross interest and royalty rate
3. **Lease Bonus** — calculates total bonus from acreage × price per acre
4. **Royalty Estimator** — estimates monthly royalty from NRI and revenue
5. **Acreage Calculator** — converts sections to acres

**How it works:** Pure math — these don't talk to the backend at all. Enter numbers, click Calculate, see result.

**File:** `js/tools.js` → functions `calculateODI()`, `calculateNRI()`, `calculateBonus()`, `calculateRoyalty()`, `calculateAcreage()`

---

### Documents Page
**What it shows:** Document templates organized by type (PSA, Offer Letter, OOP Closing, Mail Merge). Each template appears as a card.

**How it works:** Templates are defined in the JavaScript — this page is static and doesn't pull from the backend (yet).

**File:** `js/documents.js` → functions `loadDocuments()`, `filterDocs()`

---

### My Activity Page
**What it shows:** A log of your outreach activities (calls, voicemails, texts, emails, letters, notes, meetings). Filterable by type and date range. Shows daily/weekly/monthly stats.

**How it works:** Loads activities from `/api/activities` filtered to the logged-in user. The "+ Log Activity" button opens a form where you can record a new activity — you type an owner's name, it searches and lets you select them, then you fill in the activity type, subject, and description.

**File:** `js/activity.js` → functions `loadActivities()`, `showLogActivityForm()`, `submitLogActivity()`

---

### AI Assistant Page
**What it shows:** A chat interface with persistent conversation history. The page has two panels: a sidebar on the left showing your conversation history, and the main chat area on the right with suggestion chips, messages, and an input box.

**How it works:** Your message is sent to the backend (`POST /api/assistant`), which forwards it to the Anthropic Claude API along with a description of your database schema. Claude interprets your question and either generates a SQL query (for data questions), takes an action (for requests like "update this contact's status"), or responds with plain text (for general questions). The backend executes the SQL, gets the results, and sends them back to the frontend as a formatted table. Every message (yours and the assistant's) is saved to the database so you can revisit conversations later.

**Conversation History:**
- Click "+ New" in the sidebar to start a new conversation
- Click any conversation in the sidebar to reload it with all previous messages
- Right-click a conversation to pin it (stays at top) or delete it
- Conversations auto-title from your first message
- All conversations are per-user — other users see only their own history

**What it can do:**
- Search and filter data: "Show me all trusts with email addresses"
- Aggregate and count: "How many contacts are deceased?"
- Answer business questions: "What does NRA stand for?"
- Take actions: "Mark contact #12345 as Reached" (asks for confirmation first)
- Cross-reference data: "What sections have the highest exit price?"

**API key:** Set via the `ANTHROPIC_API_KEY` environment variable on the server (in `/var/www/mineral-crm/.env`). If the assistant stops working, SSH into the server and check that the key is set correctly, then restart: `systemctl restart strata-crm`.

**File:** `js/assistant.js` → functions `loadAssistant()`, `sendAssistantMessage()`, `loadConversationList()`, `loadConversation()`

---

## The Backend API Endpoints (How Data Flows)

Every time the frontend needs data, it calls one of these endpoints. They all start with `/api/`.

### Authentication
| Endpoint | What it does |
|---|---|
| `POST /api/auth/login` | Authenticates with password gate |
| `POST /api/auth/logout` | Logs you out |
| `GET /api/auth/me` | Checks if you're still logged in |

### Sections
| Endpoint | What it does |
|---|---|
| `GET /api/sections` | Gets the list of sections (with search, filter, sort, pagination) |
| `GET /api/sections/{id}` | Gets full detail for one section (including owners, deals, pricing history) |
| `PUT /api/sections/{id}` | Updates a section's info |
| `GET /api/sections/parishes` | Gets the list of parishes (for the filter dropdown) |

### Contacts (Owners)
| Endpoint | What it does |
|---|---|
| `GET /api/owners` | Gets the contact list (with search, filter, sort, pagination) |
| `GET /api/owners/{id}` | Gets full detail for one contact (all fields, notes, activities) |
| `PUT /api/owners/{id}` | Updates a contact's info (status, etc.) |
| `GET /api/owners/{id}/notes` | Gets all notes for a contact |
| `POST /api/owners/{id}/notes` | Adds a new note to a contact |
| `DELETE /api/notes/{id}` | Deletes a note |
| `PUT /api/owners/{id}/verify-phone` | Toggles phone verification star |
| `GET /api/owners/export` | Exports contacts to CSV |

### Deals
| Endpoint | What it does |
|---|---|
| `GET /api/deals` | Gets all deals (used by pipeline page) |
| `POST /api/deals` | Creates a new deal |
| `PUT /api/deals/{id}` | Updates a deal (used when dragging cards between stages) |

### Activities
| Endpoint | What it does |
|---|---|
| `GET /api/activities` | Gets activity log (filtered by user, type, date) |
| `POST /api/activities` | Logs a new activity |

### Other
| Endpoint | What it does |
|---|---|
| `GET /api/stats` | System-wide statistics (total contacts, phone/email coverage, etc.) |
| `GET /api/dashboard` | Personal dashboard data (your sections, your deals, your pipeline) |
| `GET /api/search` | Global search across contacts, sections, and deals |
| `GET /api/lookups` | Gets dropdown options (users, parishes, stages, etc.) |
| `GET /api/users` | Lists all user accounts |
| `POST /api/users` | Creates a new user account |

### AI Assistant
| Endpoint | What it does |
|---|---|
| `POST /api/assistant` | Sends a natural language question to Claude, gets back data or text |
| `GET /api/assistant/suggestions` | Gets example queries the user can try |
| `GET /api/assistant/conversations` | Lists all conversations for the current user |
| `POST /api/assistant/conversations` | Creates a new conversation |
| `GET /api/assistant/conversations/:id` | Gets a conversation with all its messages |
| `DELETE /api/assistant/conversations/:id` | Deletes a conversation and all its messages |
| `PUT /api/assistant/conversations/:id/pin` | Toggles pin status on a conversation |
| `POST /api/assistant/conversations/:id/messages` | Saves a message to a conversation |

---

## The Database (Where Your Data Lives)

The database is a single file: `database/mineral_crm.db`. It uses SQLite (a simple, file-based database — no server needed).

### Key Tables

| Table | What it stores | Row count |
|---|---|---|
| `owners` | All 841,565 contacts — names, phones, emails, addresses, age, classification | 841,565 |
| `sections` | All 1,025 land sections — location, pricing, status, operator | 1,025 |
| `ownership_links` | Links contacts to sections (who owns what) | 0 (pending pay deck import) |
| `deals` | Purchase deals — owner, section, stage, value | 0 (pending Pipedrive re-import) |
| `deal_stages` | The pipeline columns (Lead, Contacted, etc.) | 6 |
| `activities` | Activity log — calls, emails, texts, etc. | 0 |
| `contact_notes` | Notes written about specific contacts | 0 |
| `users` | User accounts for login | ~2 |
| `parishes` | Louisiana parishes | ~8 |
| `operators` | Oil/gas operators active in these sections | varies |
| `pricing_history` | Historical pricing snapshots for sections | varies |
| `buying_groups` | Groups of sections bought together | varies |
| `documents` | Document template metadata | varies |
| `login_log` | Login attempt history | varies |

### Important Database Concepts

**owners** is the biggest table. Each row has ~70+ columns because it stores all the data imported from AIS (Acquisition Intelligence Systems): up to 6 phone numbers, up to 4 emails, full address, age, date of birth, deceased flag, classification, relatives (as JSON), and more.

**ownership_links** connects owners to sections. One owner can own minerals in multiple sections, and one section has many owners. This table is currently empty because the "pay deck" data hasn't been imported yet — that's the spreadsheet data showing exactly who owns what and how much.

**deals** tracks each purchase negotiation. A deal ties one owner to one section and moves through stages (Lead → Contacted → Negotiating → Under Contract → Closed).

---

## How the Frontend and Backend Talk to Each Other

All communication uses a pattern called **REST API** — which just means:

1. The frontend sends a **request** to a URL like `/api/owners?search=smith&page=2`
2. The backend receives the request, queries the database, and sends back **JSON data** (structured text)
3. The frontend takes that JSON and builds the HTML to display it

Every request goes through one function: `apiCall()` in `js/api.js`. If the backend responds with a 401 (not authorized), it automatically shows the login screen.

---

## Common Tasks and Where to Find the Code

| "I want to..." | Look in this file | Key function |
|---|---|---|
| Change how the login works | `js/app.js` | `handleLogin()` |
| Change what the home page shows | `js/home.js` | `loadDashboard()` |
| Change the sections table columns | `js/sections.js` | `loadSections()` |
| Change the section detail layout | `js/sections.js` | `viewSectionDetail()` |
| Change the contacts table columns | `js/contacts.js` | `loadOwners()` |
| Change the contact detail panel | `js/contacts.js` | `viewOwnerDetail()` |
| Change the pipeline board | `js/pipeline.js` | `loadPipeline()` |
| Change the map | `js/map.js` | `initMap()` |
| Change the calculators | `js/tools.js` | `calculateODI()` etc. |
| Add a new API endpoint | `backend/server/app.py` | Add a new `@app.route()` |
| Change the color scheme | `css/styles.css` | `:root` variables at the top |
| Add a new nav button/page | `index.html` + `js/app.js` | HTML nav section + `setPage()` |

---

## The Design System (Colors and Styles)

The app uses CSS custom properties (variables) for all colors. Both dark and light themes are supported.

| Variable | Dark Theme | What it's for |
|---|---|---|
| `--bg` | `#0b0f1e` | Page background |
| `--s` | `#1E2657` | Card/surface background |
| `--s2` | `#182048` | Secondary surface (table cells, inputs) |
| `--b` | `#2a3170` | Borders |
| `--t` | `#dde3ff` | Primary text |
| `--td` | `#8090c4` | Dimmed/secondary text |
| `--ac` | `#6b8cde` | Accent color (links, active states) |
| `--g` | `#00B451` | Green (success, money) |
| `--y` | `#BD9A5F` | Gold (warnings, prospect status) |
| `--r` | `#FF671D` | Red/orange (danger, errors) |
| `--p` | `#655DC6` | Purple (trust badges, secondary cards) |

---

## Known Limitations and What's Not Done Yet

1. **ownership_links is empty** — contacts aren't linked to sections yet. This requires importing "pay deck" spreadsheet data.
2. **deals is empty** — deal data needs to be re-imported from the old Pipedrive CRM.
3. **No automated tests** — if something breaks, you find out by using the app.
4. **No backup system** — the database is a single file on the server. If it gets corrupted, data is lost. Consider periodic SCP backups of `mineral_crm.db`.
5. **Single-user optimized** — works for 1-3 users. Not designed for 50+ concurrent users. PostgreSQL migration planned.
6. **No HTTPS** — the app is live at http://147.182.251.233 but uses HTTP, not HTTPS. SSL certificate via Let's Encrypt is planned.

---

## If Something Goes Wrong

### The app won't load at all
- Is the server running? SSH in: `ssh root@147.182.251.233`
- Check status: `systemctl status strata-crm`
- Restart: `systemctl restart strata-crm`
- View logs: `journalctl -u strata-crm -n 100 --no-pager`

### You see "Connection Error" when logging in
- The backend probably crashed. SSH into the server and check the logs.
- Restart: `systemctl restart strata-crm`

### A page shows no data / is blank
- Open the browser's developer tools (F12 → Console tab) and look for red error messages.
- Check that the database file exists: `database/mineral_crm.db`

### You made a change and broke something
- The `docs/changelog.md` file documents every change made. Look at the most recent entry to understand what was changed.
- The original, unmodified files are not backed up anywhere currently — this is a risk.

---

## Glossary

| Term | Meaning |
|---|---|
| **Section** | A geographic land parcel, identified by Section number, Township, and Range (e.g., "Section 12, T14N, R12W") |
| **Owner / Contact** | A person or entity that owns mineral rights in a section |
| **NRA** | Net Revenue Acres — the effective acreage an owner controls after accounting for their fractional interest |
| **Exit Price** | Target purchase price per NRA |
| **Cost Free Price** | Purchase price that factors out costs |
| **Pay Deck** | A spreadsheet showing who owns what interest in a section — used by operators to distribute royalty payments |
| **AIS** | Acquisition Intelligence Systems — the data provider that supplied contact information |
| **Pipedrive** | The old CRM system — deal data may be re-imported from here |
| **Enverus** | An oil & gas data provider for well/permit/completion information |
| **Pipeline / Kanban** | The visual board showing deals in columns by stage |
| **Flask** | The Python framework that runs the backend server |
| **SQLite** | The database engine — stores everything in a single .db file |
| **API** | Application Programming Interface — how the frontend and backend communicate |
| **JSON** | JavaScript Object Notation — the data format used for communication |
| **REST** | A pattern for organizing API endpoints (GET to read, POST to create, PUT to update, DELETE to remove) |
| **CSS Variables** | Named colors/values that can be changed in one place to update the entire app's look |

---

## Session History

| Session | Date | What Was Built |
|---|---|---|
| 1-7 | Pre-March 2026 | Initial database import, basic frontend, authentication, sections, owners tables |
| 8 | Mar 16, 2026 | Contact directory integration, data verification, AIS field mapping |
| 9 | Mar 16, 2026 | Sections page redesign (sortable, filterable), section detail page, pipeline Kanban with drag-and-drop |
| 10 | Mar 17, 2026 | Contacts page redesign, phone verification stars, contact notes, create deal from contact, activity log, home page personalization |
| 11 | Mar 17, 2026 | Comprehension debt audit, system guide creation, frontend file split (14 files), name cleanup (8,803 LLC/LP/LLP fixes), Associated Contacts feature, AI Assistant (Claude-powered natural language CRM queries) |

---

*Last updated: Session 11, March 17, 2026*
*This guide should be updated every time a change is made to the codebase. If a new page is added, a new API endpoint is created, or the database structure changes — update the relevant section of this document.*
