**Version:** v2.0
**Last Updated:** 2026-03-23

## Related Documents

| Document | Description |
|---|---|
| `onboarding.md` | Entry point for the repo; recommended reading order and project overview |
| `dual_review_workflow.md` | Governs the commit, review, and response process |
| `codex_review_template.md` | Standardized template Codex uses for all reviews |
| `review_log.md` | Living audit log of all completed review cycles |
| `doc_standards.md` | Documentation conventions and standards for this repo |

---

# Review Log

This is the living audit log of all completed review cycles. A new row is added at the end of every workflow cycle per Step 9 of the Workflow Loop in `dual_review_workflow.md`. The **Last Updated** date in the header must be updated each time a new row is added.

This log is the single source of truth for review history. It eliminates the need to search through chat logs to find past review outcomes.

---

## Review History

| Commit ID | Date | Files Reviewed | Codex Overall Assessment | Claude Disposition Summary | Notes |
|---|---|---|---|---|---|
| 17b495b | 2026-03-23 | backend/server/app.py, frontend/app/index.html, frontend/app/js/contacts.js, frontend/app/js/utils.js | Needs Revision | 3 Adopt, 0 Reject, 0 Defer | Review cycle 9. (1-High/Bug) Delete button onclick passed event+field_name instead of numeric slot — fixed onclick to pass integer slot directly, added event.stopPropagation(). (2-High/Security) Stored XSS in alt address, tel/mailto/sms href attributes — added sanitizePhone()/sanitizeEmail() utils, wrapped alt address in esc(), applied sanitizers to all href attributes. (3-Med/Bug) Phone sort prioritized verified over last_seen — reversed to last_seen primary, verified tiebreaker. Open Q1: detail-only refresh on delete is intentional. Open Q2: phone_1 stays as Quick Actions SMS target by design. |
| e7a0237, 2db8a09 | 2026-03-20 | frontend/app/js/sections.js, contacts.js, utils.js, scripts/cleanup_names.py, backend/server/app.py | Needs Revision | 2 Adopt, 0 Reject, 0 Defer | Review cycle 8. (1-High) SONRIS link XSS — unescaped data in href; fixed with encodeURIComponent. (2-Med) Cleanup script loads all 841K into memory; fixed with batched processing (10K rows per batch with per-batch commits). JS syntax and display ID formatting confirmed clean. |
| 307f939 | 2026-03-19 | backend/server/app.py, database/migrations/003, frontend/app/js/deal.js, contacts.js, index.html, css/styles.css, scripts/cleanup_names.py | Needs Revision | 7 Adopt, 0 Reject, 1 Defer | Review cycle 7. (1-High) DELETE no authorization — added assigned_user_id + admin check. (2-Med) Delete not atomic — wrapped in transaction with rollback. (3-Med) Audit trail weak — structured JSON with all deal fields. (4-High) Startup validation missing new cols — added phone_1_verified_by/date to REQUIRED_OWNER_COLS. (5-Med) Verify audit omits attribution — added verified_by + date to log entry. (6-Med) Mc Donald not collapsed — added regex pre-pass. (7-Low) Reclassification scope narrow — deferred, intentional design. (8-Low) JS syntax clean — no action. Cycle-closing commit: pending. |
| 49a3377, 65ff6eb, 0ad5ef2, 20122e6, 45e32b8 | 2026-03-19 | frontend/app/js/contacts.js, sections.js, app.js, utils.js, map.js, index.html, css/styles.css, backend/server/app.py | Needs Revision | 3 Adopt, 0 Reject, 1 Defer | Review cycle 6 (5 commits). (1-High/Security) XSS in relative Search in CRM onclick — fixed with safe escaping + dedicated function. (2-Med) Map deceased filter non-functional + initMap ignoring UI defaults — wired up deceased param to backend + initMap now calls filterMap(). (3-Med) People column hardcoded to 0 regression — restored original count logic. (4-Low) Phone_1 index claim overstated — deferred; indexes created on server directly, not in schema.sql. Cycle-closing commit: pending. |
| ad5c294, 94bb524, 1f82ef3 | 2026-03-18 | docs/generate_master_plan.py, MASTER_FEATURE_LIST.md, NOTES.md, TODO.md, changelog.md, SYSTEM_GUIDE.md, .gitignore, start_crm.bat, start_crm.py, config/api_keys.env, scripts/imports/*, backend/server/app.py, scripts/test_all.py | Needs Revision | 6 Adopt, 0 Reject, 0 Defer | Review cycle 5 (3 commits). Findings: (1-High) hardcoded password in test_all.py — removed, now uses env vars. (2-MedHigh) app.py fallback to config/api_keys.env — removed, env-var-only. (3-Med) SYSTEM_GUIDE.md stale refs to start_crm.bat/py and api_keys.env — all updated to cloud workflow. (4-Med) import scripts hardcoded session paths — parameterized with repo-relative + env var override. (5-LowMed) generate_master_plan.py hardcoded output path — now repo-relative. (6-Low) SYSTEM_GUIDE.md date bump without content — resolved by fixes 1-5 adding real content. Cycle-closing commit: pending. |
| 783224f | 2026-03-18 | backend/server/app.py | Needs Revision | 1 Adopt, 0 Reject, 0 Defer | Review cycle 4. Finding #1 (High): SQL aliases zip_code AS zip / latitude AS lat / longitude AS lng changed API response shape — frontend reads zip_code/latitude/longitude so zip codes and coordinates would disappear. Fix: removed aliases, SELECT now uses canonical DB column names directly. Cycle-closing commit: 8315903. |
| 8c9b665 | 2026-03-18 | backend/server/app.py, frontend/app/js/contacts.js, frontend/app/js/app.js, scripts/compute_dob.py, scripts/geocode_addresses.py, scripts/ais_enrichment.py, database/migrations/002_add_missing_columns.sql, requirements.txt | Approve with Minor Concerns | 2 Adopt, 0 Reject, 0 Defer | Review cycle 3. Finding #1 (Security/High): SELECT * replaced with explicit field allowlist — financial flags visible to all buyers per owner decision; Codex retracted as blocking after disposition clarification. Finding #2 (Performance/High): search minimum raised to 3 chars, owner/deal search narrowed to single column; FTS5 deferred to Session 13 per roadmap. Codex revised assessment from Needs Revision to Approve with Minor Concerns after follow-up. |
| 0fe9044 | 2026-03-18 | backend/server/app.py, database/schema.sql, database/migrate.py, database/migrations/001_security_hardening.sql, requirements.txt | Needs Revision | 3 Adopt, 0 Reject, 0 Defer | Review cycle 2. Server-side confirmation tokens for assistant writes, migration 002 for ALTER TABLE column additions, persistent SQLite-backed rate limiting with user_id + IP throttle. |
| 0ae1d2c | 2026-03-18 | docs/doc_standards.md, docs/dual_review_workflow.md, docs/codex_review_template.md, docs/review_log.md, docs/onboarding.md | Needs Revision | 4 Adopt, 0 Reject, 0 Defer | First formal review cycle. Pre-governance Codex reviews (security, tech stack, codebase walkthrough) informed project direction but are not logged here. |

---

## Changelog

Current: v2.0 — Logged review cycle 9 (commit 17b495b), all 3 findings adopted.

| Version | Date | Change Summary |
|---|---|---|
| v2.0 | 2026-03-23 | Logged review cycle 9 (commit 17b495b) — delete button params fixed, XSS in contact detail DOM patched, phone sort order corrected |
| v1.5 | 2026-03-18 | Logged review cycle 4 (commit 783224f) — API contract regression fixed, cycle closed with 8315903 |
| v1.4 | 2026-03-18 | Session 13 infrastructure note added — no Codex cycle triggered (infra-only session, no app code changes) |
| v1.3 | 2026-03-18 | Updated cycle 3 assessment — Codex retracted Finding #1 as blocking, confirmed Finding #2 defer; revised to Approve with Minor Concerns |
| v1.2 | 2026-03-18 | Logged review cycle 3 (commit 8c9b665) |
| v1.1 | 2026-03-18 | Logged review cycle 2 (commit 0fe9044) |
| v1.0 | 2026-03-18 | Logged first formal review cycle (commit 0ae1d2c) |

## Pending Changes

1. None.

---

## Session Notes

**Session 13 (2026-03-18):** Infrastructure-only session — no application code committed. Full DigitalOcean cloud migration completed. No Codex review cycle triggered (no app.py or frontend changes). Next code commit should trigger cycle 4.
