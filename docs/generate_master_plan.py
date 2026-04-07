import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import date

# ── Colors ──────────────────────────────────────────────────────────────────
DARK_BG    = colors.HexColor("#1a1f2e")
NAVY       = colors.HexColor("#1e2744")
GREEN      = colors.HexColor("#4CAF50")
GREEN_DARK = colors.HexColor("#388E3C")
TEAL       = colors.HexColor("#26a69a")
WHITE      = colors.white
LIGHT_GRAY = colors.HexColor("#e8eaf0")
MID_GRAY   = colors.HexColor("#9098b1")
YELLOW     = colors.HexColor("#FFC107")
RED        = colors.HexColor("#ef5350")
BLUE       = colors.HexColor("#42a5f5")

# ── Styles ───────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

COVER_TITLE = S("CoverTitle",
    fontName="Helvetica-Bold", fontSize=36, textColor=WHITE,
    alignment=TA_CENTER, spaceAfter=8, leading=42)

COVER_SUB = S("CoverSub",
    fontName="Helvetica", fontSize=14, textColor=GREEN,
    alignment=TA_CENTER, spaceAfter=4, leading=18)

COVER_DATE = S("CoverDate",
    fontName="Helvetica", fontSize=11, textColor=MID_GRAY,
    alignment=TA_CENTER, leading=14)

SECTION_HEADER = S("SectionHeader",
    fontName="Helvetica-Bold", fontSize=18, textColor=WHITE,
    spaceAfter=6, spaceBefore=18, leading=22,
    backColor=NAVY, borderPadding=(8, 12, 8, 12))

TIER_HEADER = S("TierHeader",
    fontName="Helvetica-Bold", fontSize=13, textColor=GREEN,
    spaceAfter=4, spaceBefore=14, leading=16)

FEATURE_NAME = S("FeatureName",
    fontName="Helvetica-Bold", fontSize=10, textColor=DARK_BG,
    spaceAfter=2, leading=13)

BODY = S("Body",
    fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#333333"),
    spaceAfter=3, leading=13)

BODY_SMALL = S("BodySmall",
    fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#555555"),
    spaceAfter=2, leading=11)

NOTE = S("Note",
    fontName="Helvetica-Oblique", fontSize=8, textColor=MID_GRAY,
    spaceAfter=2, leading=11)

LABEL = S("Label",
    fontName="Helvetica-Bold", fontSize=8, textColor=WHITE, leading=10)

# ── Helpers ──────────────────────────────────────────────────────────────────
def hr(color=GREEN, thickness=1.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=2)

def effort_badge(effort, done=False):
    if done:
        return ("[DONE]", GREEN_DARK, WHITE)
    mapping = {
        "30 min": (colors.HexColor("#4caf50"), WHITE),
        "1 hour": (colors.HexColor("#8bc34a"), WHITE),
        "1-2 hours": (colors.HexColor("#cddc39"), DARK_BG),
        "2-3 hours": (YELLOW, DARK_BG),
        "3-4 hours": (colors.HexColor("#ff9800"), WHITE),
        "4-5 hours": (colors.HexColor("#ff5722"), WHITE),
        "4+ hours": (RED, WHITE),
        "Multi-session": (colors.HexColor("#9c27b0"), WHITE),
    }
    for key, val in mapping.items():
        if key.lower() in effort.lower():
            return (effort, val[0], val[1])
    return (effort, MID_GRAY, WHITE)

def feature_row(name, what, effort, notes=None, done=False, depends=None):
    """Returns a KeepTogether block for one feature."""
    badge_text, badge_bg, badge_fg = effort_badge(effort, done)

    badge_table = Table(
        [[Paragraph(badge_text, ParagraphStyle("b", fontName="Helvetica-Bold",
            fontSize=7.5, textColor=badge_fg, leading=9))]],
        colWidths=[1.1*inch]
    )
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), badge_bg),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("ROUNDEDCORNERS", [3,3,3,3]),
    ]))

    detail = [Paragraph(f"<b>{name}</b>", FEATURE_NAME),
              Paragraph(what, BODY_SMALL)]
    if notes:
        detail.append(Paragraph(f"<i>{notes}</i>", NOTE))
    if depends:
        detail.append(Paragraph(f"Depends on: {depends}", NOTE))

    row = Table([[detail, badge_table]],
                colWidths=[5.5*inch, 1.2*inch])
    row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (0,-1), 0),
        ("RIGHTPADDING", (0,0), (0,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))

    container = Table([[row]], colWidths=[6.8*inch])
    container.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GRAY),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#d0d4df")),
    ]))
    return KeepTogether([container, Spacer(1, 4)])

def tier_block(number, title, subtitle, color=GREEN):
    badge = Table([[Paragraph(f"TIER {number}", ParagraphStyle("tb",
        fontName="Helvetica-Bold", fontSize=9, textColor=WHITE, leading=11))]],
        colWidths=[0.65*inch])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), color),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))

    title_col = [
        Paragraph(f"<b>{title}</b>", ParagraphStyle("TH",
            fontName="Helvetica-Bold", fontSize=12, textColor=DARK_BG, leading=14)),
        Paragraph(subtitle, ParagraphStyle("TS",
            fontName="Helvetica", fontSize=8.5, textColor=MID_GRAY, leading=11))
    ]

    row = Table([[badge, title_col]], colWidths=[0.75*inch, 5.95*inch])
    row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]))

    container = Table([[row]], colWidths=[6.8*inch])
    container.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#dff0e0")),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("LINEBELOW", (0,0), (-1,-1), 2, color),
    ]))
    return KeepTogether([Spacer(1, 8), container, Spacer(1, 6)])

SECTION_HEADER_DONE = S("SectionHeaderDone",
    fontName="Helvetica-Bold", fontSize=18, textColor=WHITE,
    spaceAfter=6, spaceBefore=18, leading=22,
    backColor=colors.HexColor("#1b3a2e"), borderPadding=(8, 12, 8, 12))

# ── Cover Page ────────────────────────────────────────────────────────────────
def build_cover(story):
    # Dark header band
    header = Table(
        [[Paragraph("BUFFALO NEXUS CRM", COVER_TITLE)],
         [Paragraph("Master Feature Plan &amp; Execution Roadmap", COVER_SUB)],
         [Paragraph(f"Buffalo Bayou Resources  ·  {date.today().strftime('%B %d, %Y')}  ·  Session 17", COVER_DATE)]],
        colWidths=[7*inch]
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK_BG),
        ("TOPPADDING", (0,0), (-1,-1), 36),
        ("BOTTOMPADDING", (0,0), (-1,-1), 36),
        ("LEFTPADDING", (0,0), (-1,-1), 24),
        ("RIGHTPADDING", (0,0), (-1,-1), 24),
    ]))
    story.append(header)
    story.append(Spacer(1, 20))

    # Status bar
    status_data = [
        [Paragraph("841,565\nContacts", ParagraphStyle("sv", fontName="Helvetica-Bold",
            fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=14)),
         Paragraph("LIVE\nCloud", ParagraphStyle("sv", fontName="Helvetica-Bold",
            fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=14)),
         Paragraph("1,025\nSections", ParagraphStyle("sv", fontName="Helvetica-Bold",
            fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=14)),
         Paragraph("Session 17\nComplete", ParagraphStyle("sv", fontName="Helvetica-Bold",
            fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=14))]
    ]
    status_table = Table(status_data, colWidths=[1.75*inch]*4)
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), GREEN_DARK),
        ("BACKGROUND", (1,0), (1,-1), TEAL),
        ("BACKGROUND", (2,0), (2,-1), NAVY),
        ("BACKGROUND", (3,0), (3,-1), colors.HexColor("#5c6bc0")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("GRID", (0,0), (-1,-1), 1, WHITE),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 20))

    # Intro paragraph
    intro = (
        "This document defines every remaining feature for Buffalo Nexus, "
        "organized by execution priority. Each feature includes a plain-English description, "
        "effort estimate, and any dependencies. The roadmap is structured so that "
        "high-value, low-effort items are front-loaded, while larger infrastructure "
        "work is sequenced after the daily-workflow features are stable."
    )
    story.append(Paragraph(intro, ParagraphStyle("Intro",
        fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#333333"),
        leading=15, spaceAfter=12, alignment=TA_LEFT,
        leftIndent=0, borderPadding=0)))

    # Effort legend
    story.append(Paragraph("Effort Legend", ParagraphStyle("LH",
        fontName="Helvetica-Bold", fontSize=9, textColor=DARK_BG,
        spaceAfter=6)))
    legend_items = [
        ("30 min – 1 hr", colors.HexColor("#4caf50"), WHITE, "Quick wins — can ship same session"),
        ("1-2 hrs", colors.HexColor("#cddc39"), DARK_BG, "Small features — 1 session"),
        ("2-3 hrs", YELLOW, DARK_BG, "Medium features — plan ahead"),
        ("3-4 hrs", colors.HexColor("#ff9800"), WHITE, "Larger features — may span sessions"),
        ("4+ hrs / Multi-session", RED, WHITE, "Major projects — requires planning"),
    ]
    leg_rows = [[
        Table([[Paragraph(label, ParagraphStyle("LL", fontName="Helvetica-Bold",
            fontSize=7.5, textColor=fg, leading=9))]],
            colWidths=[1.5*inch]),
        Paragraph(desc, BODY_SMALL)
    ] for label, bg, fg, desc in legend_items]

    for i, (label, bg, fg, desc) in enumerate(legend_items):
        row_table = Table(
            [[Table([[Paragraph(label, ParagraphStyle("LL", fontName="Helvetica-Bold",
                fontSize=7.5, textColor=fg, leading=9))]],
                colWidths=[1.4*inch]),
              Paragraph(desc, BODY_SMALL)]],
            colWidths=[1.5*inch, 5.3*inch])
        row_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,-1), bg),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING", (0,0), (0,-1), 6),
            ("RIGHTPADDING", (0,0), (0,-1), 6),
        ]))
        story.append(row_table)
        story.append(Spacer(1, 2))

    story.append(PageBreak())

# ── Completed Features ────────────────────────────────────────────────────────
def build_completed(story):
    story.append(Paragraph("✓  COMPLETED FEATURES — Sessions 8–13", SECTION_HEADER_DONE))
    story.append(hr(GREEN))
    story.append(Paragraph(
        "Everything below has been built and is live in production at http://147.182.251.233. "
        "This is the full feature history of Buffalo Nexus from initial build through cloud deployment.",
        BODY))
    story.append(Spacer(1, 8))

    # ── Session 8 ──────────────────────────────────────────────────────────────
    story.append(tier_block("8", "Frontend Foundation", "Complete frontend rewrite from scratch — the core platform", GREEN))
    story.append(feature_row("Complete Frontend Rewrite (~2,500 lines)",
        "Built the entire Buffalo Nexus UI from scratch. Horizontal top nav, dark theme, modular layout, owner detail side panel (720px sliding). Replaced a placeholder prototype with a production-grade interface.",
        "DONE", done=True))
    story.append(feature_row("11 Document Templates",
        "Letter templates for offers, PSAs, LOIs, and other acquisition documents. Filter pills by document type. Ready-to-use in every session.",
        "DONE", done=True))
    story.append(feature_row("5 Calculators",
        "ODI (Overriding Royalty Interest), NRI (Net Revenue Interest), Lease Bonus, Royalty Revenue, and Acreage calculators built into the Tools page.",
        "DONE", done=True))
    story.append(feature_row("Leaflet Map with Clustering",
        "Interactive map with 3 base layers (Street, Satellite, Topo). Marker clustering for performance. Geocoded contacts visible on map.",
        "DONE", done=True))
    story.append(feature_row("Auth System",
        "SHA-256 + salt password hashing, session-based login, login attempt logging. Upgraded to support scrypt in Session 13. Rate limiting with SQLite-backed user_id + IP throttle.",
        "DONE", done=True))

    # ── Session 10 ─────────────────────────────────────────────────────────────
    story.append(tier_block(10, "Frontend Features", "Full feature build-out for daily acquisition work", GREEN))
    story.append(feature_row("Sections Page Redesign",
        "Sortable columns, pricing date, total contacts per section, assigned filter, full section detail page with owner list, pricing history, and assignment controls.",
        "DONE", done=True))
    story.append(feature_row("Deal Pipeline (Kanban)",
        "Renamed from 'Pipeline.' Drag-and-drop Kanban board, stats bar showing total value per stage, per-stage deal counts. Create deal, move deal, close deal all in one view.",
        "DONE", done=True))
    story.append(feature_row("Contact Notes",
        "contact_notes table. Add and delete notes on any contact. Timestamps and author on every note. Visible in the contact detail panel.",
        "DONE", done=True))
    story.append(feature_row("Phone Verification Stars",
        "Clickable ★/☆ on each phone number toggles verified status. Persists to database. Verified phones surface first in call queues.",
        "DONE", done=True))
    story.append(feature_row("Contacts Page Redesign",
        "Renamed from 'Owners.' Source badges (AIS, Pipedrive, idiCore). Deceased flags. Estimated age column. Sorting by any column. Full filter bar.",
        "DONE", done=True))
    story.append(feature_row("Create Deal from Contact",
        "Modal form on contact detail: select section, stage, NRA, price/NRA, assign to user. Creates linked deal and ownership record in one step.",
        "DONE", done=True))
    story.append(feature_row("Home Page Personalization",
        "User-scoped stats: my open deals, my contacts, my sections. My Pipeline widget. Personalized welcome message. Activity feed filtered to current user.",
        "DONE", done=True))
    story.append(feature_row("Activity Log Overhaul",
        "User-scoped activity feed. Date range filters. Type icons (call, email, note, etc.). Log Activity form with owner search. Full audit trail of all field actions.",
        "DONE", done=True))
    story.append(feature_row("Contact Status Quick-Change Dropdown",
        "One-click status change (Not Contacted → Attempted → Reached → Interested → Deal → Closed) directly from the owner detail panel. No page reload required.",
        "DONE", done=True))

    story.append(PageBreak())

    # ── Session 11 ─────────────────────────────────────────────────────────────
    story.append(tier_block(11, "Data, AI &amp; Architecture", "File split, AI assistant, contact classification, name cleanup", GREEN))
    story.append(feature_row("Frontend File Split",
        "Broke the 125KB monolith app.js into 14 organized files: 1 HTML, 1 CSS, and 12 JS modules (contacts.js, sections.js, deals.js, map.js, etc.). Much easier to maintain and debug.",
        "DONE", done=True))
    story.append(feature_row("System Guide (SYSTEM_GUIDE.md)",
        "Plain-English documentation for non-developers. Covers every page, every feature, every script, and all server management commands. Updated each session.",
        "DONE", done=True))
    story.append(feature_row("Name Cleanup (8,803 Names Fixed)",
        "Batch-corrected capitalization errors in company names: Llc → LLC, Lp → LP, Llp → LLP. Ran across all 841,565 contacts.",
        "DONE", done=True))
    story.append(feature_row("Contact Classification (841K Records)",
        "Classified all 841,565 contacts into: Individual, Trust, LLC, Corp, Business, Estate. Classification logic based on name patterns. Displayed as color badges in the UI.",
        "DONE", done=True))
    story.append(feature_row("Associated Contacts Tab",
        "New tab in the contact detail panel showing all contacts who share a phone number, email, or mailing address. Groups by match type. Click through to any associated contact's profile.",
        "DONE", done=True))
    story.append(feature_row("AI Assistant (Claude-Powered)",
        "Natural language CRM queries powered by Claude Sonnet API. SQL generation from plain English. Action support: update status, create deals, log activities. Chat UI with suggestion chips, data tables, and collapsible SQL view.",
        "DONE", done=True))
    story.append(feature_row("AIS Data Import (841,565 Contacts)",
        "Imported all 5 AIS CSV files. 16-table schema. PRAGMA integrity_check OK. Full Haynesville basin owner database in production.",
        "DONE", done=True))

    # ── Session 12 ─────────────────────────────────────────────────────────────
    story.append(tier_block(12, "Data Enrichment", "Geocoding, DOB, financial flags, relatives, universal search", GREEN))
    story.append(feature_row("DOB Computed (838,067 Records)",
        "Estimated date_of_birth for 838,067 contacts from age field + January 2025 snapshot date. Stored in database. Drives dynamic age calculation in frontend.",
        "DONE", done=True))
    story.append(feature_row("Mass Geocoding — 85.3% Complete",
        "717,633 of 841,565 addresses geocoded via US Census Batch Geocoding API. Latitude/longitude stored on each contact. Powers the map and mini-map features.",
        "DONE", done=True))
    story.append(feature_row("Estimated Age (Dynamic)",
        "Frontend computes current age from date_of_birth at render time — no stale values. Displays 'Est. Age' label to signal the estimate. Updates automatically each year.",
        "DONE", done=True))
    story.append(feature_row("Phone and Email Labeling",
        "Phone numbers display as 'Phone 1', 'Phone 2', etc. in the contact detail panel. Emails similarly labeled. Eliminates confusion when contacts have multiple numbers.",
        "DONE", done=True))
    story.append(feature_row("Financial Flags Display",
        "Color-coded badges in contact detail for: bankruptcy, lien, judgment, eviction, foreclosure, debt. Sourced from AIS data. Critical risk signal for buyer conversations.",
        "DONE", done=True))
    story.append(feature_row("Relatives Display",
        "Up to 3 relatives per contact shown in the detail panel. Clickable phone and email links on each relative. Useful for skip-tracing and reaching estate contacts.",
        "DONE", done=True))
    story.append(feature_row("Universal Search Bar",
        "Navigation bar search across contacts, sections, and deals simultaneously. Results grouped by type. Click any result to jump directly to that record.",
        "DONE", done=True))

    # ── Session 13 ─────────────────────────────────────────────────────────────
    story.append(tier_block(13, "Cloud Migration", "DigitalOcean Droplet — Buffalo Nexus is live in the cloud", GREEN))
    story.append(feature_row("DigitalOcean Droplet Provisioned",
        "Ubuntu 24.04.4 LTS, 2GB RAM / 50GB SSD, SFO3 data center. Server name: buffalo-nexus. IP: 147.182.251.233. Python 3.12, venv, nginx, git installed.",
        "DONE", done=True))
    story.append(feature_row("gunicorn + nginx Production Stack",
        "gunicorn 25.1.0 serving Flask on localhost:5000 with 2 workers. nginx reverse proxy on port 80. Systemd service auto-starts on reboot. Persistent across server restarts.",
        "DONE", done=True))
    story.append(feature_row("1.7GB Database Uploaded to Production",
        "mineral_crm.db (1.7GB, 841,565 contacts) transferred via SCP in 51 seconds. Relocated to /database/ subdirectory to match hardcoded DB_PATH. All 16 tables verified.",
        "DONE", done=True))
    story.append(feature_row("Schema Fixes Applied (6 Missing Columns)",
        "Added entity_name, alt_address, alt_city, alt_state, alt_zip, deceased_date via ALTER TABLE. Created login_attempts table for rate limiting. Fixed column name aliases (zip_code, latitude, longitude).",
        "DONE", done=True))
    story.append(feature_row("Buffalo Nexus Live at http://147.182.251.233",
        "Login, contacts, map, AI assistant, deal pipeline — all verified working in production. App accessible from any device on any network. No localhost required.",
        "DONE", done=True))

    # ── Session 14 ─────────────────────────────────────────────────────────────
    story.append(tier_block(14, "Security, UI Redesign &amp; Data Dictionary", "Credentials revoked, UI overhauled, data dictionary rebuilt", GREEN))
    story.append(feature_row("Credential Revocation (Priority 0 Security)",
        "GitHub PAT revoked and deleted. Anthropic API key revoked, new key generated and deployed to server. config/api_keys.env deleted from repo. app.py fallback removed. test_all.py hardcoded password removed.",
        "DONE", done=True))
    story.append(feature_row("Project Cleanup &amp; Codex Cycle 5",
        "Deleted dead files (start_crm.bat/py, stale backup, old PDF). Removed empty dirs and placeholder READMEs. Moved import scripts to scripts/imports/. Codex review: all 6 findings fixed.",
        "DONE", done=True))
    story.append(feature_row("UI Redesign — Header, Tables, Detail Panel",
        "Header tabs reordered with separators. Sections and contacts tables redesigned with compact 32px rows, checkboxes, status badges, and color-coded pricing dates. Contact detail panel: Google Maps link, Risk Flags section, colored left borders.",
        "DONE", done=True))
    story.append(feature_row("Data Dictionary Rebuilt with Pipedrive Merge",
        "Analyzed Pipedrive exports (Haynesville + all-basins). Contacts: 77→110 fields. Sections: 40→56. Deals: 24→38. Added ownership data, instrument/title, external IDs, call analytics fields. All NEW fields in blue.",
        "DONE", done=True))

    # ── Session 16 ─────────────────────────────────────────────────────────────
    story.append(tier_block(15, "Security, Performance &amp; Bug Fixes", "SSH key auth, contact card speed, 17 bug fixes, Codex cycle 6", GREEN))
    story.append(feature_row("SSH Key Auth + Security Audit",
        "Full security audit completed. SSH key authentication (ed25519) configured, password auth disabled. 7-page Security Assessment PDF generated for management. 12 of 13 checklist items SECURE.",
        "DONE", done=True))
    story.append(feature_row("Contact Card Performance Fix",
        "Contact card loading reduced from 5+ seconds to instant. Moved associated contacts query to lazy-loaded endpoint. 9 database indexes created on production server.",
        "DONE", done=True))
    story.append(feature_row("17 Bug Fixes &amp; UI Improvements",
        "Auto-close contact panel on nav, Google Maps link under address, Age column + DECEASED tag, section status inline dropdown, unreserve button, relatives Search in CRM link, bulk action bar, map default filters + Load button.",
        "DONE", done=True))
    story.append(feature_row("Codex Review Cycle 6",
        "Fixed XSS vulnerability in relative search link (names with apostrophes). Wired up map deceased filter to backend. Restored People column count. 3 adopted, 1 deferred.",
        "DONE", done=True))

    # ── Session 16 ─────────────────────────────────────────────────────────────
    story.append(tier_block(16, "Features, AI History &amp; Data Cleanup", "Deal deletion, phone verification, home page, AI conversations, data cleanup", GREEN))
    story.append(feature_row("Deal Deletion with Authorization",
        "DELETE endpoint with assigned_user_id + admin/manager check. Atomic transaction with rollback. Structured JSON audit trail. Frontend delete button with confirmation dialog.",
        "DONE", done=True))
    story.append(feature_row("Phone Verification Attribution",
        "12 new columns tracking who verified each phone number and when. Shows 'Verified 2026-03-19' next to verified stars. Startup validation requires new columns.",
        "DONE", done=True))
    story.append(feature_row("Home Page Redesign",
        "Removed welcome banner and Quick Actions. Compact stat bar. Two-column layout: pipeline + activity on left, quick links + alerts on right.",
        "DONE", done=True))
    story.append(feature_row("AI Assistant Conversation History",
        "Two new DB tables. 7 new API endpoints. Sidebar with persistent conversation list. Messages survive navigation and logout. Auto-titles, pin, delete, right-click context menu.",
        "DONE", done=True))
    story.append(feature_row("Data Cleanup + Codex Cycle 7",
        "65 names fixed with proper case script. Mc Donald collapse. Codex cycle 7: deal authorization, atomic delete, startup validation, structured audit. 7 adopted, 1 deferred.",
        "DONE", done=True))

    # ── Session 17 ─────────────────────────────────────────────────────────────
    story.append(tier_block(17, "DNC, Display IDs, Section Enhancements &amp; Performance", "Filters, proper case cleanup, composite indexes, Codex cycle 8", GREEN))
    story.append(feature_row("DNC Badges + Display IDs + Section Enhancements",
        "DNC/RESERVED badges in contacts table. BBR-S-00089 display IDs. Section detail: SONRIS/eClerk auto-links, contact status summary bar, pricing trend chart. Pricing labels renamed to Exit $/NRA.",
        "DONE", done=True))
    story.append(feature_row("Contacts Filters &amp; Performance",
        "States dropdown, backend state/source/deceased filters. Query optimized: SELECT o.* removed, COUNT eliminated for filtered queries. Composite indexes. Contacts filter now instant.",
        "DONE", done=True))
    story.append(feature_row("Full Proper Case Cleanup + Codex Cycle 8",
        "36,675 names fixed, 1,202 reclassified. Batched processing (10K/batch). SONRIS XSS fixed. All markdown files moved to docs/ folder.",
        "DONE", done=True))

    # ── Data Cleanup (Session 17) ──
    story.append(tier_block("17b", "Data Import Preparation", "5 data files cleaned, reviewed, and approved for import", GREEN))
    story.append(feature_row("5 Import Files Cleaned &amp; Approved",
        "Aethon owners (15,956 contacts with operator-confirmed phone/email), Expand pay decks (6,720 ownership records "
        "across 113 sections with NRI), idiCore contacts (16,001 with up to 6 phones + 5 emails sorted by recency), "
        "Pipedrive people (25,393 contacts linked to 674 sections with cross-section dedup), Pipedrive sections "
        "(956 sections with pricing, status, operator, buyer assignment, notes). Ready for import next session.",
        "DONE", done=True))

    story.append(PageBreak())

# ── Priority 0 ────────────────────────────────────────────────────────────────
def build_priority_zero(story):
    story.append(Paragraph("PRIORITY 0 — Security &amp; Infrastructure", SECTION_HEADER))
    story.append(hr(RED))
    story.append(Paragraph(
        "Security and infrastructure items. Three of four items are complete. "
        "Only HTTPS remains — blocked until a domain name is purchased.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(Paragraph("0.1  SECURITY ACTIONS", TIER_HEADER))
    story.append(feature_row("Revoke &amp; Regenerate GitHub PAT",
        "COMPLETED Session 14 — PAT revoked, new read-only token generated for server deployments.",
        "DONE", done=True))
    story.append(feature_row("Revoke &amp; Regenerate Anthropic API Key",
        "COMPLETED Session 14 — Key revoked, new key generated and deployed to server .env. AI Assistant verified working.",
        "DONE", done=True))
    story.append(feature_row("SSH Key Authentication",
        "COMPLETED Session 16 — ed25519 key generated, added to server. Password auth disabled in sshd_config. Brute-force attacks impossible.",
        "DONE", done=True))
    story.append(feature_row("Enable HTTPS (Let's Encrypt / certbot)",
        "PENDING — requires a domain name pointed to 147.182.251.233. Let's Encrypt issues free SSL certificates but only for domains, not bare IPs. Cost: ~$12/year for a domain. LOW risk for current use case (small team on corporate network).",
        "1-2 hours",
        notes="Blocked until domain purchased. Only remaining security gap."))

# ── Priority 1 — Daily Workflow ───────────────────────────────────────────────
def build_priority_one(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 1 — Daily Workflow Features", SECTION_HEADER))
    story.append(hr(GREEN))
    story.append(Paragraph(
        "These are the features you'll use every day in the field. "
        "They have the highest ROI and lowest effort. Build these next, in order.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(2, "Build Next — Daily Workflow", "Features you'll use on every call, every day"))
    story.append(feature_row("Click-to-Text Button",
        "COMPLETED Session 11 — Opens the device's Messages app with the phone number pre-filled via sms: URL scheme. One-click outreach from the contact detail panel.",
        "DONE", done=True))
    story.append(feature_row("Social Media Search + URL Storage",
        "COMPLETED Session 11 — Search LinkedIn and Facebook buttons on contact detail open pre-filled search URLs. linkedin_url and facebook_url columns exist in DB for saving found profiles.",
        "DONE", done=True))
    story.append(feature_row("Do Not Contact (DNC) System",
        "Two separate systems: (1) DNC — contact requested no calls; red warning badge blocks outreach. (2) Reserved for Buyer — a specific buyer 'owns' the relationship; other buyers see a warning. Uses existing do_not_contact, dnc_reason, dnc_date columns and reserved_for_user_id columns already in the DB. Reserve and Unreserve buttons already built (Session 16).",
        "1-2 hours"))
    story.append(feature_row("Human-Readable Display IDs",
        "Formatted IDs displayed in the UI: BBR-C-00412 (contacts), BBR-S-0089 (sections), BBR-D-0001 (deals). The numeric IDs stay in the database — this is a pure frontend formatting change.",
        "1 hour"))
    story.append(feature_row("Click-to-Copy on Phone Numbers &amp; Addresses",
        "Click any phone number or address to copy it to clipboard. Small copy icon appears on hover. Eliminates manual selection for calling and mailing.",
        "30 min"))
    story.append(feature_row("Bulk Status Update",
        "Select multiple contacts in the contacts list → change status for all at once. Checkbox column and Select All already built (Session 16). Needs: bulk action dropdown to apply status changes to selected contacts.",
        "1 hour"))
    story.append(feature_row("Deal Detail Page",
        "Full page per deal with editable fields, stage history timeline, notes, documents, and activity log. Currently deals only exist as Kanban cards with no detail view.",
        "2-3 hours"))
    story.append(feature_row("Clickable Stat Cards",
        "All dashboard stat cards navigate to filtered views when clicked. Example: 'My Open Deals' card → Deal Pipeline filtered to your deals.",
        "1 hour"))

# ── Priority 2 — Section Enhancements ────────────────────────────────────────
def build_priority_two(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 2 — Section Page Enhancements", SECTION_HEADER))
    story.append(hr(TEAL))
    story.append(Paragraph(
        "The section page is the core unit of work in mineral acquisition. "
        "These features make it a command center for working each section efficiently.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(3, "Section Enhancements", "Make the section page a complete workspace", TEAL))
    story.append(feature_row("Pricing History Chart",
        "Line chart of BBR price and cost-free price over time on the section detail page. Data already exists in the pricing_history table. Uses Chart.js (already loaded in frontend).",
        "1 hour"))
    story.append(feature_row("Section Activity Timeline",
        "New 'Activity' tab on section detail showing all calls, emails, notes, and deals tied to that section, in chronological order.",
        "30 min"))
    story.append(feature_row("Per-Section Mini Map",
        "Interactive Leaflet map embedded on the section detail page showing only the geocoded contacts for that section. Geocoding is already 85.3% complete.",
        "1 hour", depends="Geocoding (already done)"))
    story.append(feature_row("Contact Status Summary Bar",
        "Visual bar on section detail showing '12 Not Contacted, 3 Attempted, 5 Reached' for all owners in that section. Instant read on section health.",
        "30 min"))
    story.append(feature_row("'Work This Section' Button",
        "Generates a prioritized call queue: largest NRA owners first, verified phones first, not-yet-contacted first. One click to start working a section systematically.",
        "1-2 hours"))
    story.append(feature_row("SONRIS + eClerk Auto-Links",
        "Auto-generated links on section detail to SONRIS well search and parish clerk records, pre-filtered to the section's S/T/R. Free external data in one click.",
        "30 min"))
    story.append(feature_row("Comparable Sections",
        "Show sections in the same parish with similar pricing for comp validation. Pulls from existing section and pricing_history data.",
        "1 hour"))
    story.append(feature_row("Pricing Change Alerts + Stale Section Warnings",
        "Banner alerts for sections with recent pricing changes or no activity in X days. Keeps the team focused on current opportunities.",
        "30 min"))
    story.append(feature_row("Ownership Breakdown Pie Chart",
        "Visual showing % of NRA accounted for vs. unknown on section detail. Requires pay deck data import first.",
        "1 hour", depends="Pay Deck Import (Priority 5)"))
    story.append(feature_row("Section Assignment History",
        "Track who was assigned to a section and when the assignment changed. Audit trail for accountability.",
        "30 min"))

# ── Priority 3 — Data Imports ──────────────────────────────────────────────
def build_priority_three(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 3 — Data Imports", SECTION_HEADER))
    story.append(hr(YELLOW))
    story.append(Paragraph(
        "The CRM is only as good as its data. These imports bring in the ownership data "
        "(pay deck) and supplemental contact data (idiCore) that complete the picture. "
        "The pay deck import is the single most impactful data task remaining.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(5, "Data Imports", "Pay deck → idiCore → Pipedrive re-import", YELLOW))
    story.append(feature_row("Pay Deck Import — Aethon (13.5MB)",
        "Profile paydecks-Aethon-master.xlsx. Parse S-T-R references, owner names, NRA/interest. Match to existing AIS owner records (fuzzy name + address). Populate ownership_links. This unlocks the Ownership Breakdown chart and NRA-based prioritization.",
        "Multi-session"))
    story.append(feature_row("Pay Deck Import — Expand (1.2MB)",
        "Profile paydecks-Expand-master.xlsx. Check column overlap with Aethon. Import and merge into ownership_links.",
        "2-3 hours", depends="Aethon import first"))
    story.append(feature_row("idiCore Integration (300+ files)",
        "Profile 300+ idiCore files by basin. Build import/matching pipeline. Use as supplemental skip-tracing source (additional phone numbers, address history, relatives).",
        "Multi-session"))
    story.append(feature_row("Pipedrive Re-Import (Deal Data)",
        "Re-import Pipedrive deals matched against AIS + pay deck owner records. Import deal stage history and activities linked to matched owners. Resolve 32 known unmatched deal owners.",
        "2-3 hours", depends="Pay Deck Import"))
    story.append(feature_row("OpenCorporates Enrichment",
        "One-time batch enrichment for company-type contacts (LLC, Corp, Business — ~17K records). Pull registration state, status, officers, and filings from OpenCorporates API.",
        "2 hours"))

# ── Priority 4 — User System ──────────────────────────────────────────────
def build_priority_four(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 4 — User System &amp; Gamification", SECTION_HEADER))
    story.append(hr(BLUE))
    story.append(Paragraph(
        "These features transform Buffalo Nexus from a solo tool into a team platform. "
        "Build these when the team expands beyond the current user base.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(4, "User System", "Profile, goals, gamification, self-service signup", BLUE))
    story.append(feature_row("User Profile / Settings Page",
        "Personal info (name, email, phone, title, signature block), preferences (theme, default basin, items per page), account management (change password, login history).",
        "2-3 hours"))
    story.append(feature_row("Self-Service Signup + Account Creation",
        "'Create Account' on login page with name, email, password. Admin approval flow or invite code. Forgot password link with email reset.",
        "1-2 hours"))
    story.append(feature_row("Goal System",
        "Personal goals (user-set) and manager-assigned goals. Timeframes: daily, weekly, monthly, quarterly, yearly. Progress bars, goal templates. Goals: contacts reached, deals started, deal value closed.",
        "3-4 hours"))
    story.append(feature_row("Gamification System",
        "Streaks (consecutive activity days), leaderboards, daily call counter in nav bar, achievement badges, contact completeness scores, hot streak mode, milestone celebrations, monthly MVP, basin race, team challenges.",
        "4-5 hours"))
    story.append(feature_row("Home Page as Command Center",
        "Priority sections/contacts for the week, section updates for assigned user, goal progress, suggested next action card, morning agenda, overdue follow-up alerts.",
        "2-3 hours"))

# ── Priority 5 — AI Assistant ──────────────────────────────────────────────
def build_priority_five(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 5 — AI Assistant Enhancements", SECTION_HEADER))
    story.append(hr(colors.HexColor("#ab47bc")))
    story.append(Paragraph(
        "The AI Assistant is currently functional for basic queries. "
        "These enhancements make it a genuine operational tool for bulk actions, "
        "report generation, and eventually Enverus data queries.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(5, "AI Assistant v2", "Memory, reports, bulk ops, scheduled reports",
        colors.HexColor("#ab47bc")))
    story.append(feature_row("Conversation Memory",
        "Assistant remembers previous messages in the session for follow-up queries. 'Show me sections in DeSoto' → 'Now filter to just the ones with verified phones' — without re-stating the context.",
        "1 hour"))
    story.append(feature_row("Report / Dashboard / Export Generation",
        "'Generate a report of DeSoto sections' → formatted document. 'Export contacts in Section 12' → CSV download. Leverages existing query infrastructure.",
        "2-3 hours"))
    story.append(feature_row("Bulk Operations with Approval",
        "'Mark all contacts in Section 12 as Attempted' → assistant shows count → waits for confirmation → executes. Prevents accidental bulk changes.",
        "1 hour"))
    story.append(feature_row("Outreach Assistance with Preview",
        "Multi-step: 'Send updated offers to owners in 12-10N-11W' → assistant asks template and prices → generates previews → user approves → executes. Pending actions queue.",
        "4-5 hours"))
    story.append(feature_row("Saved Queries / Report Templates",
        "Save frequent queries as one-click templates. 'My Reports' section in the assistant panel.",
        "1-2 hours"))
    story.append(feature_row("Scheduled Reports",
        "'Every Monday, generate pipeline summary.' Auto-Friday summaries to managers. Ties into scheduled task system.",
        "2 hours"))

# ── Priority 6 — Integrations ─────────────────────────────────────────────
def build_priority_six(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 6 — External Integrations", SECTION_HEADER))
    story.append(hr(colors.HexColor("#ff7043")))
    story.append(Paragraph(
        "These integrations connect Buffalo Nexus to external data sources and tools. "
        "Enverus is the highest-value integration — live drilling data directly in the CRM. "
        "The Engineering Portal is a separate product module.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(6, "External Integrations", "Enverus, Engineering Portal, Newsletters",
        colors.HexColor("#ff7043")))
    story.append(feature_row("Enverus API Reconnection",
        "Live permits, rigs, completions, and lease data on section pages. Drilling activity context for every section. Per-parish summaries. Real-time alerts for new permits and rig movements.",
        "4+ hours", depends="Enverus API credentials"))
    story.append(feature_row("Engineering / Pricing Portal (ComboCurve)",
        "Separate portal integrating with petroleum engineer models and ComboCurve. Real-time per-owner valuations, multiple pricing scenarios. CRM consumes pricing — does not produce it. Standalone service pushing data via API.",
        "Multi-session"))
    story.append(feature_row("Automated Newsletters",
        "User-configurable scheduled emails with content blocks: tasks, priority contacts, pipeline summary, section updates, goal progress, industry news. Multiple newsletter profiles per user. Requires SendGrid or Mailgun.",
        "3-4 hours"))
    story.append(feature_row("Weekly Summary Reports (Auto-Friday)",
        "Auto-generated Friday summary: contacts reached, deals advanced, activities by type, goal progress vs. prior week. Sent to user and their manager. Manager gets team rollup. Exportable to PDF.",
        "2-3 hours"))

# ── Priority 7 — Calendar ────────────────────────────────────────────────
def build_priority_seven(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 7 — Calendar &amp; Scheduling", SECTION_HEADER))
    story.append(hr(TEAL))
    story.append(Paragraph(
        "A built-in calendar keeps follow-ups from falling through the cracks. "
        "These features should be built after the daily workflow features are stable.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(7, "Calendar System", "Built-in calendar, auto follow-ups, team view", TEAL))
    story.append(feature_row("Built-in Calendar",
        "Calendar page with day/week/month views. Follow-up reminders, deal milestones, scheduled outreach, meetings, deadlines. Drag-to-reschedule. Color coding by activity type. Mini-calendar on the home page.",
        "3-4 hours"))
    story.append(feature_row("Auto-Generated Follow-ups",
        "Log a call → 'When should we follow up?' → calendar event created automatically. Eliminates the need to manually schedule every follow-up.",
        "1 hour"))
    story.append(feature_row("Overdue Alert System",
        "Missed follow-ups appear in red and roll forward until addressed. Persistent reminders that don't let anything slip.",
        "1 hour"))
    story.append(feature_row("Team Calendar View (Manager)",
        "Managers see all team member calendars overlaid or side-by-side. Useful for coordinating outreach and avoiding duplicate contact.",
        "1-2 hours"))
    story.append(feature_row("Google Calendar Sync",
        "Bidirectional sync — CRM events appear in Google Calendar and vice versa. Requires Google OAuth.",
        "2-3 hours"))

# ── Priority 8 — Section Master DB + Tools ───────────────────────────────
def build_priority_eight(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 8 — Section Master Database &amp; Tools", SECTION_HEADER))
    story.append(hr(MID_GRAY))
    story.append(Spacer(1, 8))

    story.append(tier_block(8, "Section Master Data", "Wells, field orders, basin config, completeness", MID_GRAY))
    story.append(feature_row("Section Master Data Layer",
        "Comprehensive section records: unit name, unit size (acres), legal description, lat/lng, boundary GeoJSON. Single source of truth for calculations and document templates.",
        "2-3 hours"))
    story.append(feature_row("Wells Table",
        "Separate wells table: well name, API14, operator, permit/spud/completion/first production dates, status, type, target formation, lateral length. Multiple wells per section. Target for Enverus sync.",
        "2 hours"))
    story.append(feature_row("Field Orders Table",
        "Louisiana Office of Conservation field orders: order number, effective date, unit description, PDF attachment. Linked to sections.",
        "1 hour"))
    story.append(feature_row("Basin Configuration",
        "basins table with basin-specific config: default royalty assumptions, pricing methodology, active operators, parishes. Data partitioned by basin_id.",
        "1 hour"))
    story.append(Spacer(1, 8))

    story.append(tier_block(9, "Tools Page Redesign", "Revenue analyzer, Enverus formatter, unit economics", MID_GRAY))
    story.append(feature_row("Revenue Statement Analyzer (Claude Skill)",
        "Upload a revenue statement PDF → Claude extracts line items (owner, well, interest, revenue, deductions) → outputs clean workbook. Batch processing support.",
        "2-3 hours"))
    story.append(feature_row("Enverus Lease Pull Formatter (Claude Skill)",
        "Takes raw Enverus export → reformats to preferred scratch sheet template. Multiple output templates supported.",
        "2 hours"))
    story.append(feature_row("Unit Economics Calculator",
        "NRA × price/NRA → payback period, ROI, IRR based on estimated monthly royalty. Save results to section or deal records.",
        "1 hour"))

# ── Priority 9 — Legal/Title + Infrastructure ────────────────────────────
def build_priority_nine(story):
    story.append(PageBreak())
    story.append(Paragraph("PRIORITY 9 — Legal / Title Research", SECTION_HEADER))
    story.append(hr(RED))
    story.append(Spacer(1, 8))

    story.append(tier_block(10, "Legal / Title", "Document index, runsheets, chain of title, AI reader", RED))
    story.append(feature_row("Document Index Manager",
        "Per-section list of recorded courthouse documents: type, date, book/page, grantor, grantee, instrument number. Searchable.",
        "2-3 hours"))
    story.append(feature_row("Runsheet Generator (Claude Skill)",
        "Claude takes a document index → generates a formatted runsheet workbook. Chronological, columns pre-filled.",
        "2 hours"))
    story.append(feature_row("AI Document Reader",
        "Upload a deed/conveyance PDF → Claude extracts parties, date, legal description, interest, reservations → auto-adds to document index.",
        "2-3 hours"))
    story.append(feature_row("Chain of Title Builder",
        "Auto-build ownership chain from extracted documents. Flag gaps and uncertainties. Human validates. Shows source documents for every link in the chain.",
        "3-4 hours"))
    story.append(feature_row("Interest Calculator",
        "Auto-calculate ownership fractions from chain of title. Shows full math, requires human approval before saving.",
        "2-3 hours"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PRIORITY 10 — Production Infrastructure", SECTION_HEADER))
    story.append(hr(DARK_BG))
    story.append(Spacer(1, 8))
    story.append(tier_block(11, "Production Readiness", "PostgreSQL, multi-tenant, roles, map at scale", DARK_BG))
    story.append(feature_row("PostgreSQL Migration",
        "Replace SQLite with DigitalOcean Managed PostgreSQL ($15/mo). Supports concurrent users, automatic daily backups, row-level security. Required for multi-user team rollout.",
        "2-3 hours"))
    story.append(feature_row("Multi-Tenant Architecture",
        "Separate application code (IP) from tenant data. Folder structure: nexus-crm/ (product code) + tenants/buffalo-bayou/ (data). Enables selling to other mineral companies.",
        "Multi-session"))
    story.append(feature_row("User Roles &amp; Permissions",
        "Admin, Manager, Buyer, Viewer roles. Per-role access controls on data and features. Required before onboarding more team members.",
        "3-4 hours"))
    story.append(feature_row("Map Marker Virtualization",
        "Current map loads all 717K geocoded markers at once. At scale this will be slow. Implement viewport-based loading or clustering at the API level.",
        "2-3 hours"))

# ── Map & GIS Enhancements ───────────────────────────────────────────────
def build_map_gis(story):
    story.append(PageBreak())
    story.append(Paragraph("MAP &amp; GIS ENHANCEMENTS", SECTION_HEADER))
    story.append(hr(colors.HexColor("#0277bd")))
    story.append(Paragraph(
        "The map is the visual command center for mineral acquisition. These features transform it from "
        "a basic pin map into a full GIS workspace with land grids, polygon selection, shapefile overlays, "
        "and side-by-side drilling activity views.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(12, "Map &amp; GIS", "Land grid, polygon select, shapefiles, drilling map, viewport loading",
        colors.HexColor("#0277bd")))
    story.append(feature_row("Land Grid Overlay (Section/Township/Range)",
        "Toggleable GeoJSON layer showing the S-T-R grid over the Haynesville basin. Sourced from "
        "SONRIS/Louisiana DNR GIS data or public PLSS shapefiles. Each section polygon is clickable — "
        "shows section name and links to section detail page. Appears as a toggle in the map layer control panel.",
        "2-3 hours"))
    story.append(feature_row("Polygon Selection Tool",
        "Leaflet.draw plugin lets users draw rectangles, circles, and freeform polygons on the map. "
        "All contacts within the boundary get selected into a list panel on the side. That list is "
        "exportable, bulk-actionable (assign, change status, create mail merge), and clickable to open "
        "contact detail. Critical for field work — 'draw a circle around this neighborhood and show me "
        "everyone inside.'",
        "2-3 hours"))
    story.append(feature_row("Shapefile Upload &amp; Drag-and-Drop",
        "User uploads a .shp/.dbf/.shx bundle or .geojson file → server converts shapefile to GeoJSON "
        "using Python's fiona or geopandas → Leaflet renders it as a new toggleable layer. Drag-and-drop "
        "supported — drop a file onto the map area, it gets processed and displayed immediately. Each "
        "uploaded layer appears in a layer control panel with name, color picker, and on/off toggle. "
        "Layers can be saved permanently to the database.",
        "3-4 hours"))
    story.append(feature_row("Side-by-Side Drilling Activity Map",
        "Two map panels: left shows contacts (current map), right shows drilling activity (wells, permits, "
        "rigs, completions). Uses Leaflet side-by-side plugin or two independent map instances with synced "
        "viewport — pan and zoom on one mirrors the other. Build the dual-pane layout now, populate the "
        "drilling map when Enverus is connected.",
        "2-3 hours", depends="Enverus API connection (6.1)"))
    story.append(feature_row("Viewport-Based Map Loading",
        "Only fetch markers visible in the current map bounds instead of loading all contacts for a state. "
        "As user pans and zooms, new markers are loaded dynamically via spatial query "
        "(WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?). Eliminates the need to load "
        "717K+ markers at once. The most impactful map performance fix.",
        "2-3 hours"))

# ── Tier 13 — Mobile App & Calling ────────────────────────────────────────
def build_tier_thirteen(story):
    story.append(PageBreak())
    story.append(Paragraph("TIER 13 — Mobile App &amp; Calling Infrastructure", SECTION_HEADER))
    story.append(hr(colors.HexColor("#00897b")))
    story.append(Paragraph(
        "The mobile app is the field companion to the web CRM. Phase 1 delivers 80% of the value "
        "at 20% of the effort by using Twilio for click-to-call with auto-recording and AI processing. "
        "Phase 2 is a full native app for when the team scales.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(13, "Mobile &amp; Calling", "Twilio click-to-call, AI transcription, native app", colors.HexColor("#00897b")))
    story.append(feature_row("Phase 1: Web-Based Click-to-Call + Twilio",
        "Click a phone number in the CRM → Twilio triggers a call on the buyer's phone → call is recorded automatically → "
        "Whisper/Deepgram/AssemblyAI transcribes the audio → Claude generates a summary with action items. "
        "AI extracts follow-up tasks ('call back after April 1') and auto-creates calendar events. "
        "Sentiment tagging (positive/neutral/negative) on every call. Auto-status update: contact changes from "
        "'Not Contacted' to 'Reached' if answered, 'Attempted' if voicemail. Pre-call screen shows owner details, "
        "section info, pricing, and a suggested script based on classification and deal stage.",
        "Multi-session",
        notes="Louisiana is one-party consent. Texas is two-party — app needs per-state consent check."))
    story.append(feature_row("Phase 2: Native Mobile App",
        "Full React Native or Flutter app as the field companion. Syncs bidirectionally with the web CRM. "
        "All calls through the app are recorded, transcribed, and summarized. Offline mode for areas with poor "
        "cell service — queues changes locally and syncs when connectivity returns. Push notifications for "
        "inbound messages, deal updates, and manager assignments.",
        "Multi-session"))

# ── Tier 14 — Messaging Portal & AI Chatbot ──────────────────────────────
def build_tier_fourteen(story):
    story.append(PageBreak())
    story.append(Paragraph("TIER 14 — Messaging Portal &amp; AI Chatbot", SECTION_HEADER))
    story.append(hr(colors.HexColor("#5c6bc0")))
    story.append(Paragraph(
        "A dedicated SMS messaging portal turns Buffalo Nexus into a communication hub. The AI chatbot "
        "handles inbound responses from mineral owners who text back after receiving offer letters. "
        "The key insight: owners initiate contact by texting, which establishes consent and makes AI "
        "response legally defensible.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(14, "Messaging &amp; Chatbot", "SMS inbox, AI chatbot, campaign tracking, TCPA compliance",
        colors.HexColor("#5c6bc0")))
    story.append(feature_row("SMS Messaging Portal",
        "New tab in Buffalo Nexus with an iMessage-style inbox UI. Conversation threads per owner. "
        "Send and receive text messages directly from the CRM. Every message auto-logged as an activity on "
        "the owner's contact record with status auto-updates. Powered by Twilio SMS infrastructure with "
        "dedicated phone numbers, opt-out management (STOP keyword), and delivery tracking.",
        "Multi-session"))
    story.append(feature_row("AI SMS Chatbot (Inbound Automation)",
        "Workflow: mail offer letters with a phone number → owners text back → consent established → "
        "AI chatbot handles initial response and triage. Smart classification: Interested (schedule call), "
        "Questions (answer from template library), Not Interested (log and close), Angry/Emotional (immediate "
        "human escalation), Wrong Number (auto-close). Campaign tracking with unique numbers per mailing that "
        "auto-link to the right section, owner, and deal. Scheduled follow-ups ('checking in per our conversation'). "
        "Bot → human handoff with full conversation history visible to the buyer. Claude powers responses with "
        "a locked system prompt enforcing company tone, offer details, and compliance rules.",
        "Multi-session",
        notes="TCPA compliance, FTC bot disclosure, opt-out management required. Lawyer review before launch."))

# ── Tier 15 — Owner Self-Service Portal ──────────────────────────────────
def build_tier_fifteen(story):
    story.append(PageBreak())
    story.append(Paragraph("TIER 15 — Owner Self-Service Portal", SECTION_HEADER))
    story.append(hr(colors.HexColor("#8d6e63")))
    story.append(Paragraph(
        "Instead of chasing owners, they come to you. A public 'Request an Offer' page lets mineral owners "
        "submit contact info and upload documents. Revenue statements serve as built-in identity verification — "
        "they contain owner name, address, well/unit info, operator, interest type, and payment amounts that "
        "can be cross-referenced against the 841K existing contacts.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(15, "Owner Portal", "Public signup, document upload, AI parsing, verification tiers",
        colors.HexColor("#8d6e63")))
    story.append(feature_row("'Request an Offer' Public Portal",
        "Clean, professional public page at offers.buffalobayou.com. Owners submit contact info and upload "
        "documents (revenue statements, leases, deeds, tax records) — no CRM login required. AI document parsing "
        "on upload via Claude extracts owner name, well/unit, operator, interest type, NRA, and monthly revenue. "
        "Auto-matches against 841K existing contacts by name + address. Three verification tiers: Unverified (gray) → "
        "Contacted (yellow) → Verified Owner (green checkmark). Document vault stores all uploads on the contact profile. "
        "Instant offer estimate range after submission keeps owners engaged. Referral tracking ('How did you hear about us?') "
        "for marketing ROI. Buyer notification on submission with parsed data and matched records. "
        "CAPTCHA + email verification prevents spam. Privacy policy and encrypted document storage required — "
        "revenue statements may contain SSN.",
        "Multi-session"))

# ── Tier 16 — Management Controls ────────────────────────────────────────
def build_tier_sixteen(story):
    story.append(PageBreak())
    story.append(Paragraph("TIER 16 — Management Controls &amp; Assignment System", SECTION_HEADER))
    story.append(hr(colors.HexColor("#f44336")))
    story.append(Paragraph(
        "These features transform Buffalo Nexus from a solo tool into a managed team platform. "
        "The contact ownership model, notification system, and routing rules are prerequisites for "
        "scaling beyond the current user base. A Manager Implementation Guide must be written BEFORE "
        "these features go live — management misuse can kill CRM adoption.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(16, "Management Controls", "Contact ownership, notifications, routing rules",
        colors.HexColor("#f44336")))
    story.append(feature_row("Contact Ownership Model (Soft Assignment, Hard Lock on Deals)",
        "Three-tier system: (1) Section assignment — managers assign sections to buyers, all contacts in the "
        "section are available but not locked. (2) Overlap resolution — contacts in multiple sections visible to "
        "all assigned buyers; no conflict unless a deal starts. (3) Hard lock — contact locked to a buyer only "
        "when a deal is created (automatic) or manager manually assigns (whale scenario). Lock is global while "
        "a deal is active; manager can override for different sections. Lock auto-expires after 90+ days of "
        "inactivity, triggering a manager review. Assignment dashboard shows workload per buyer. Auto-assignment "
        "rules route new contacts by parish. Reassignment includes handoff notes.",
        "3-4 hours", depends="User Roles &amp; Permissions (Tier 4)"))
    story.append(feature_row("Tagged Notes &amp; Notification System",
        "Managers can add notes anywhere in the system that tag users via @mention and send notifications. "
        "Universal notes with polymorphic reference (entity_type + entity_id — works on contacts, sections, "
        "deals, or other notes). Notification tiers: urgent (red push), standard (in-app), FYI (record only). "
        "Notification center with bell icon in nav, unread count, click to jump to record. Note types: "
        "Action Required, FYI, Question, Escalation — each with different visual treatment. Thread replies "
        "on notes for in-context discussion. Optional daily digest email summarizing all notifications.",
        "2-3 hours"))
    story.append(feature_row("Inbound Routing Rules",
        "Visual rule builder for routing inbound messages (SMS), portal submissions, and calls to the right "
        "buyer. IF section is in [DeSoto Parish] AND contact type is [Individual] THEN route to [Chase]. "
        "Fallback rules for unmatched inbound. Round-robin distribution for teams without geographic "
        "specialization. SLA timers: text messages 2 hours, portal submissions 24 hours — auto-escalate to "
        "manager on expiry. Auto-response on assignment ('Thanks for reaching out — a team member will be "
        "in touch shortly'). Routing analytics showing average response time per buyer, per channel, per parish.",
        "2-3 hours", depends="Messaging Portal (14.1), Owner Portal (15.1)"))

# ── Tier 17 — Priority Scoring & Whale Detection ────────────────────────
def build_tier_seventeen(story):
    story.append(PageBreak())
    story.append(Paragraph("TIER 17 — Priority Scoring &amp; Whale Detection", SECTION_HEADER))
    story.append(hr(colors.HexColor("#ff6f00")))
    story.append(Paragraph(
        "A nightly scoring engine calculates a priority score for every contact, driving auto-ranked "
        "daily call lists for buyers and system-wide value dashboards for managers. Buyers see their "
        "slice; managers see the whole ocean. Same scoring engine powers both views.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(17, "Priority Scoring", "Nightly scoring engine, buyer queue, manager whale dashboard",
        colors.HexColor("#ff6f00")))
    story.append(feature_row("Contact Priority Scoring Engine",
        "Background job calculates priority_score per contact nightly. Scoring factors (weighted, adjustable): "
        "portfolio value (when engineering portal is live), NRA size, recent pricing changes, new permits/rig "
        "activity (when Enverus connected), contact status, verified phone, time since last contact, inbound "
        "activity (text/portal/call — highest priority override), deceased/DNC exclusion. Each contact shows "
        "WHY it's ranked: tag like 'Repriced +15%', 'Large NRA', 'Inbound text'. List recalculates daily "
        "and flags what changed since yesterday. 'Start My Day' button loads #1 contact's full profile and "
        "advances through queue. Priority score badge visible everywhere — contacts list, section detail, search.",
        "3-4 hours"))
    story.append(feature_row("Manager Whale Dashboard",
        "System-wide contact rankings by total portfolio value. Every contact across every section, buyer, and "
        "parish. Biggest Movers section shows contacts with largest value change over 24hrs, 7 days, 30 days — "
        "this is the killer feature, not static rankings. Unassigned whale detection: high-value contacts with "
        "no buyer, sorted by value, one-click assignment. Buyer portfolio summary: total assigned value, contacts, "
        "active deals, and conversion rate per buyer. Geographic heat map colored by total portfolio value per "
        "section or parish — instantly see where the highest concentration of value is. Threshold-based "
        "auto-notifications: 'Notify me when any contact exceeds $100K' or 'when an unassigned contact crosses "
        "$50K.' Deal velocity overlay flags whales stuck in a stage too long.",
        "3-4 hours", depends="Engineering/Pricing Portal (6.2) for real valuations. Works with NRA/pricing before that."))

# ── Tier 18 — Call Analytics Engine ──────────────────────────────────────
def build_tier_eighteen(story):
    story.append(PageBreak())
    story.append(Paragraph("TIER 18 — Call Analytics Engine", SECTION_HEADER))
    story.append(hr(colors.HexColor("#e91e63")))
    story.append(Paragraph(
        "Deep performance tracking inspired by JustCall but integrated with the CRM where call data lives "
        "alongside contact, deal, and section data. Every metric is contextual — not just '14 calls Tuesday' "
        "but '14 calls into DeSoto sections with pricing increases, 6 connects, 2 moved to Interested.' "
        "JustCall failed because it was a standalone dialer with no business context. Buffalo Nexus solves this.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(tier_block(18, "Call Analytics", "Outcome tracking, heat maps, conversion funnel, AI scheduling",
        colors.HexColor("#e91e63")))
    story.append(feature_row("Call Analytics Dashboard",
        "Outcome tagging on every call: Connected, Voicemail, No Answer, Wrong Number, Disconnected, DNC — "
        "one tap after call ends, auto-prompted by mobile app. Best time to call heat map (day × hour grid) "
        "builds from thousands of data points over 2-3 months — shows when owners actually answer. "
        "Contact-type segmented analytics: Individuals vs Trusts vs LLCs answer at different rates and times. "
        "Age-bracket analysis from estimated age data (838K contacts with DOB). Parish-level heat maps for "
        "rural vs urban answer patterns. Conversion funnel: Calls Made → Connected → Interested → Deal Created "
        "→ Deal Closed. Anti-gaming: tracks connect rate and conversation duration, not just volume — a buyer "
        "dialing 50 numbers and hanging up shows 0% connect rate. Manager comparison view for coaching "
        "(not punishment). Weekly trend lines, export to PDF/CSV, scheduled Monday morning summary.",
        "Multi-session",
        notes="Architecture: single call_events table joined to contacts/sections/users for all analytics."))
    story.append(feature_row("AI-Powered Optimal Call Scheduling",
        "Once enough data accumulates (2-3 months of call logging), the system recommends the best time to call "
        "each specific contact — not just a generic heat map. 'John Smith: best window Tuesday 9-10am based on "
        "3 previous connects at that time.' The daily priority queue factors this into ranking: contacts whose "
        "optimal call window is NOW get boosted to the top.",
        "2-3 hours", depends="Call Analytics with sufficient data (2-3 months)"))

# ── Execution Summary ─────────────────────────────────────────────────────
def build_summary(story):
    story.append(PageBreak())
    story.append(Paragraph("EXECUTION SUMMARY", SECTION_HEADER))
    story.append(hr(GREEN))
    story.append(Spacer(1, 8))

    summary_data = [
        [Paragraph("Priority", ParagraphStyle("SH", fontName="Helvetica-Bold",
            fontSize=9, textColor=WHITE, alignment=TA_CENTER, leading=11)),
         Paragraph("Focus Area", ParagraphStyle("SH", fontName="Helvetica-Bold",
            fontSize=9, textColor=WHITE, alignment=TA_CENTER, leading=11)),
         Paragraph("# Items", ParagraphStyle("SH", fontName="Helvetica-Bold",
            fontSize=9, textColor=WHITE, alignment=TA_CENTER, leading=11)),
         Paragraph("Est. Total Effort", ParagraphStyle("SH", fontName="Helvetica-Bold",
            fontSize=9, textColor=WHITE, alignment=TA_CENTER, leading=11)),
         Paragraph("Do When", ParagraphStyle("SH", fontName="Helvetica-Bold",
            fontSize=9, textColor=WHITE, alignment=TA_CENTER, leading=11))],
        ["0 — Security", "HTTPS only remaining (3/4 DONE)", "1", "~1 hour", "When domain purchased"],
        ["1 — Daily Workflow", "DNC, Bulk update, Deal page, Display IDs (2/8 DONE)", "6", "~7 hours", "Session 16-17"],
        ["2 — Section Page", "Pricing chart, Mini map, Work queue, SONRIS", "10", "~8 hours", "Session 16-17"],
        ["3 — Data Imports", "Pay deck, idiCore, Pipedrive re-import", "5", "Multi-session", "Session 16+"],
        ["4 — User System", "Profile, Goals, Gamification, Signup", "5", "~15 hours", "When team grows"],
        ["5 — AI Assistant", "Memory, Reports, Bulk ops, Scheduled", "6", "~12 hours", "Session 17+"],
        ["6 — Integrations", "Enverus, Eng Portal, Newsletters", "4", "Multi-session", "After Enverus creds"],
        ["7 — Calendar", "Built-in calendar, Follow-ups, Team view", "5", "~9 hours", "Session 18+"],
        ["8 — Section DB/Tools", "Wells, Field orders, Revenue analyzer", "8", "~14 hours", "Session 18+"],
        ["9-10 — Legal/Infra", "Title research, PostgreSQL, Multi-tenant", "10", "Multi-session", "Long term"],
        ["12 — Map/GIS", "Land grid, polygon select, shapefiles, drilling map", "5", "~13 hours", "Session 17+"],
        ["13 — Mobile/Calling", "Twilio click-to-call, AI transcription, native app", "2", "Multi-session", "After Twilio"],
        ["14 — Messaging", "SMS portal, AI chatbot, campaign tracking", "2", "Multi-session", "After Twilio"],
        ["15 — Owner Portal", "Public signup, doc upload, AI parsing", "1", "Multi-session", "After team rollout"],
        ["16 — Management", "Ownership model, notifications, routing", "3", "~8 hours", "Before team rollout"],
        ["17 — Whale Detection", "Priority scoring, buyer queue, manager dashboard", "2", "~7 hours", "After Eng Portal"],
        ["18 — Call Analytics", "Heat maps, conversion funnel, AI scheduling", "2", "Multi-session", "After calling live"],
    ]

    row_colors = [
        NAVY,
        RED, GREEN_DARK, TEAL, YELLOW,
        BLUE, colors.HexColor("#ab47bc"),
        colors.HexColor("#ff7043"), TEAL, MID_GRAY, DARK_BG,
        colors.HexColor("#0277bd"),
        colors.HexColor("#00897b"), colors.HexColor("#5c6bc0"),
        colors.HexColor("#8d6e63"), colors.HexColor("#f44336"),
        colors.HexColor("#ff6f00"), colors.HexColor("#e91e63"),
    ]
    text_colors = [WHITE]*18

    col_widths = [1.7*inch, 2.5*inch, 0.65*inch, 1.2*inch, 1.2*inch]
    table = Table(summary_data, colWidths=col_widths, repeatRows=1)

    table_style = [
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,-1), 8.5),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("GRID", (0,0), (-1,-1), 0.5, WHITE),
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
    ]
    for i, (bg, fg) in enumerate(zip(row_colors[1:], text_colors[1:]), start=1):
        table_style.append(("BACKGROUND", (0,i), (-1,i), bg))
        table_style.append(("TEXTCOLOR", (0,i), (-1,i), fg))
        # Make text readable on yellow
        if bg in [YELLOW]:
            table_style.append(("TEXTCOLOR", (0,i), (-1,i), DARK_BG))

    table.setStyle(TableStyle(table_style))
    story.append(table)

    story.append(Spacer(1, 20))
    story.append(Paragraph("Recommended Next Session (Session 14)", ParagraphStyle("RN",
        fontName="Helvetica-Bold", fontSize=11, textColor=DARK_BG, spaceAfter=6)))
    story.append(hr(GREEN, 1))
    next_steps = [
        ("1", "Revoke GitHub PAT and Anthropic API key — takes 10 minutes, eliminates active security risk."),
        ("2", "Enable HTTPS via certbot — makes the app production-grade and removes browser warnings."),
        ("3", "Build the DNC / Reserved for Buyer system — first daily workflow feature, blocks outreach mistakes."),
        ("4", "Add click-to-text and social media search — fast wins, immediate daily value."),
        ("5", "Start pay deck import — largest single data value unlock in the entire roadmap."),
    ]
    for num, text in next_steps:
        row = Table([[
            Table([[Paragraph(num, ParagraphStyle("NUM", fontName="Helvetica-Bold",
                fontSize=10, textColor=WHITE, alignment=TA_CENTER, leading=12))]],
                colWidths=[0.3*inch]),
            Paragraph(text, BODY)
        ]], colWidths=[0.45*inch, 6.3*inch])
        row.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,-1), GREEN_DARK),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (0,-1), 4),
        ]))
        story.append(row)
        story.append(Spacer(1, 3))

# ── Footer/Header ─────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, letter[0], 28, fill=1, stroke=0)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(0.75*inch, 10, "Buffalo Nexus CRM — Master Feature Plan")
    canvas.drawRightString(letter[0] - 0.75*inch, 10,
        f"Page {doc.page}  ·  Confidential  ·  Buffalo Bayou Resources")
    canvas.restoreState()

# ── Main ──────────────────────────────────────────────────────────────────────
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Buffalo_Nexus_Master_Plan.pdf")

doc = SimpleDocTemplate(
    output_path,
    pagesize=letter,
    leftMargin=0.75*inch,
    rightMargin=0.75*inch,
    topMargin=0.65*inch,
    bottomMargin=0.55*inch,
)

story = []
build_cover(story)
build_completed(story)
build_priority_zero(story)
build_priority_one(story)
build_priority_two(story)
build_priority_three(story)
build_priority_four(story)
build_priority_five(story)
build_priority_six(story)
build_priority_seven(story)
build_priority_eight(story)
build_priority_nine(story)
build_map_gis(story)
build_tier_thirteen(story)
build_tier_fourteen(story)
build_tier_fifteen(story)
build_tier_sixteen(story)
build_tier_seventeen(story)
build_tier_eighteen(story)
build_summary(story)

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF saved to: {output_path}")
