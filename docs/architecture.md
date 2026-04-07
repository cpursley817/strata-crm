# Mineral Buyer CRM — Architecture Overview

Last updated: March 17, 2026 (Session 10)

## System Overview
The Mineral Buyer CRM is a purpose-built system for managing mineral rights acquisition workflows. It replaces Pipedrive's misfit data model with a proper relational structure where owners, sections, and deals are first-class entities with many-to-many relationships.

## Core Problem Solved
In Pipedrive, a mineral owner who owns in 10 sections exists as 10 separate contacts with no linkage. Notes, calls, and deal history are siloed per section. The CRM solves this with a junction table (ownership_links) that connects one canonical owner record to many sections.

## System Components

### Strata CRM (Contact Directory)
- **Role**: Contact research, lookup, and import staging
- **Tech**: Self-contained HTML + embedded JSON, served by PowerShell HTTP server
- **Data**: 41,422+ mineral owner contacts with phone, email, address, ownership details
- **Sources**: idiCore (53K+ rows from 300 files), AIS (5 CSVs including large SQL dumps), Pipedrive (deal/pipeline data)
- **Integration**: Feeds contact data into the CRM via the strata-crm bridge

### Mineral CRM (This System)
- **Role**: Deal pipeline management, activity tracking, section/owner management
- **Tech**: SQLite database (prototype) → PostgreSQL (production), Python/Flask backend, single-page HTML frontend
- **Frontend**: Single HTML file (~2,500 lines) with embedded CSS/JS matching original Strata design
- **Backend**: Flask API (~1,130 lines) with session-based auth, SHA-256+salt password hashing
- **Database**: 418 MB SQLite file with 17 tables, 841,565 owner records, 1,025 sections
- **Scale Target**: 2M+ contacts, 10K+ sections, 15+ concurrent users, 4-5 basins

### Enverus Integration
- **Role**: Real-time basin activity data (active rigs, permits, completions, well activity)
- **Tech**: Enverus V3 Direct Access REST API, per-parish queries for Haynesville
- **Data**: Feeds into section-level context (nearby drilling activity, operator info)
- **Status**: API research complete, integration code migrated, not yet wired to frontend

## Current Feature Set (Session 10)

### Pages
- **Home**: Personalized dashboard — My Sections, My Deals, My Pipeline, data coverage stats
- **Sections**: Sortable table (9 columns), parish/status/assigned filters, full section detail page with tabbed owners/deals/pricing
- **Contacts**: Sortable table with type badges, source badges, deceased flags, phone verification stars, age column
- **Deal Pipeline**: Drag-and-drop Kanban board (11 stages), stats bar, per-stage values
- **Map**: Leaflet map centered on Haynesville (32.0, -93.5), 3 base layers, marker clustering
- **Documents**: 11 BBR document templates with type filter pills
- **My Activity**: User-scoped activity log with date/type filters, stats bar, Log Activity modal
- **Calculators**: ODI, NRI, Lease Bonus, Royalty, Acreage

### Owner Detail Panel (720px slide-in)
- Contact info with name breakdown, mailing address
- Phone numbers with verification stars (clickable ★/☆)
- Email addresses
- Aliases / AKA
- Contact notes (add/delete with timestamps)
- Action buttons: Create Deal, Change Status
- Tabbed sections: Sections / Deals / Activity

### API Endpoints
- Auth: login, logout, me
- Sections: list (sortable, filterable), detail (with owners/deals/pricing), update, parishes lookup
- Owners: list (sortable, filterable), detail (with sections/deals/activities/aliases/notes), update, export CSV
- Deals: list (Kanban-grouped by stage), create, update (stage move)
- Activities: list (filterable by user/type/date), create
- Notes: list per owner, create, delete
- Phone verification: toggle per phone field
- Search: global across sections and owners
- Stats: global counts and distributions
- Dashboard: user-scoped personal dashboard
- Lookups: parishes, operators, buying groups, users, pipeline stages, basins

## Data Import Strategy

The database is built in order of data quality:

### Phase 1: AIS Data — COMPLETE
- **Source**: 5 CSV files (3.4MB + 739MB + 780MB + 764MB + 204MB)
- **Result**: 841,565 owner records (foundation)

### Phase 2: Pay Deck Data — PENDING
- **Source**: XLSX files (paydecks-Aethon-master.xlsx 13.5MB, paydecks-Expand-master.xlsx 1.2MB)
- **Purpose**: Links owners to sections with verified ownership data (NRA, interest amounts)

### Phase 3: Pipedrive Data — PENDING
- **Source**: 5 CSV files from Pipedrive export
- **Purpose**: Imports deal history and pipeline state, matched to existing AIS+PayDeck records

## Data Flow
1. AIS import builds clean contact foundation (names, phones, emails, addresses)
2. Pay deck import adds ownership links (who owns what, NRA, in which sections)
3. Pipedrive import adds deal pipeline data, matched to existing owner records
4. Buyers work sections → contact owners → log activities → create deals
5. Deals progress through 11-stage pipeline to closing
6. Enverus provides real-time drilling/permit activity context (planned)

## Frontend Design System
```css
--bg:#0b0f1e; --s:#1E2657; --s2:#182048; --b:#2a3170;
--t:#dde3ff; --td:#8090c4; --ac:#6b8cde; --ac2:#5270c0;
--g:#00B451; --y:#BD9A5F; --r:#FF671D; --o:#fb923c;
--p:#655DC6; --rad:8px;
```
- Horizontal top nav bar (NOT sidebar) with green bottom border
- Dark theme (with light mode toggle) using blue/navy palette
- Leaflet map with marker clusters
- Owner detail side panel (720px slide-in from right)
- Modal dialogs for Create Deal, Log Activity
- Drag-and-drop Kanban board for deal pipeline

## Scale Considerations
- Current (Haynesville): 1,025 sections, 841,565 contacts, 1-3 users
- Production (company-wide): 10K+ sections, 2M+ contacts, 15+ users, 4-5 basins
- SQLite handles current scale; PostgreSQL required for production multi-user access
