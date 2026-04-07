# Documentation Standards Reference

This document defines the formatting conventions, versioning rules, and structural standards for all documentation in the Strata CRM repository. It is the canonical reference for anyone creating or updating a repo document.

This document does not follow the universal header, footer, or Related Documents conventions it defines. It **is** the definition of those conventions.

---

## 1. Purpose

This file exists so that every document in the repo looks, reads, and behaves the same way. Reference it whenever you create a new document, add a section to an existing one, or are unsure how to format a changelog entry or version bump. If a convention is not covered here, propose it in the Pending Changes section of the relevant document and flag it for the next versioning cycle.

---

## 2. Document Registry

This table lists every governed document in the repo. It must be updated in the **same commit** that introduces any new document — never deferred to a later cycle.

| Filename | Purpose | Owner |
|---|---|---|
| `onboarding.md` | Entry point for the repo; recommended reading order and project overview | Claude |
| `dual_review_workflow.md` | Governs the commit, review, and response process | Shared |
| `codex_review_template.md` | Standardized template Codex uses for all reviews | Shared |
| `review_log.md` | Living audit log of all completed review cycles | Shared |
| `doc_standards.md` | Documentation conventions and standards for this repo | Claude |

---

## 3. Universal Header Standard

Every governed document (except `doc_standards.md` itself) must begin with the following two fields before any other content:

```
**Version:** v{MAJOR}.{MINOR}
**Last Updated:** YYYY-MM-DD
```

Rules:

- **Version** starts at `v1.0` for new documents.
- **Last Updated** is set to the date of the commit that changes the document. Any commit that modifies a document's content must update this date. Whitespace-only or tooling-generated changes do not require an update.
- The header appears on the very first lines of the file, before the document title or any other content.

---

## 4. Versioning Conventions

These definitions apply to all versioned documents in the repo.

**Minor version bump** (e.g., v1.0 → v1.1): Wording changes, formatting corrections, typo fixes, clarifications, or additions to reference tables (e.g., adding a row to the Document Registry or Review Log) that do not alter process or structure.

**Major version bump** (e.g., v1.0 → v2.0): Structural changes, process changes, addition or removal of sections, changes to severity definitions or categories, or any change that affects how Claude or Codex behaves during the workflow.

When in doubt, ask: "Would someone following the old version do something differently?" If yes, it is a major bump.

---

## 5. Related Documents Section Standard

Every governed document (except `doc_standards.md`) must include a **Related Documents** section immediately after the universal header and before the first content section.

Format:

```
## Related Documents

| Document | Description |
|---|---|
| `onboarding.md` | Entry point for the repo; recommended reading order and project overview |
| `dual_review_workflow.md` | Governs the commit, review, and response process |
| `codex_review_template.md` | Standardized template Codex uses for all reviews |
| `review_log.md` | Living audit log of all completed review cycles |
| `doc_standards.md` | Documentation conventions and standards for this repo |
```

Rules:

- Every governed document must be listed in every other governed document's Related Documents table.
- When a new document is added to the repo, its entry must be added to the Related Documents section of **all** existing governed documents in the same commit. This is enforced by the Workflow Loop in `dual_review_workflow.md`.
- The current document may be included in its own table for completeness but is not required.

---

## 6. Changelog Standard

Every governed document (except `doc_standards.md`) must end with a **Changelog** section as the final content before the Pending Changes list.

Structure (in order):

1. **Version History note** — A single line immediately above the Changelog table summarizing the current version. Format: `Current: v{X}.{Y} — {one-phrase summary}.` This line must be updated every time a new Changelog row is added.

2. **Changelog table** — Columns: `Version | Date | Change Summary`. One row per version. Newest version on top. Date format: `YYYY-MM-DD`.

```
Current: v1.1 — Added edge case for offline reviews.

| Version | Date | Change Summary |
|---|---|---|
| v1.1 | 2026-03-20 | Added edge case for offline reviews |
| v1.0 | 2026-03-18 | Initial document created |
```

Rules:

- A new row is added whenever the document's version is bumped.
- The Change Summary should be a single concise sentence.
- Refer to Section 4 (Versioning Conventions) to determine whether a change warrants a minor or major bump.

---

## 7. Pending Changes Standard

Every governed document (except `doc_standards.md`) must include a **Pending Changes** section as the very last content in the file, immediately after the Changelog.

Format:

```
## Pending Changes

1. None.
```

Rules:

- Items are numbered sequentially so they can be referenced individually (e.g., "Promote Pending Change #2 to the next version").
- An item is added here when a revision is proposed but not yet formally versioned — for example, when a Codex review suggests a documentation update that will be batched into a future version bump.
- When a pending item is promoted to a formal version, it is removed from this list and recorded in the Changelog table instead.
- If all pending items have been promoted or discarded, reset the list to `1. None.`

---

## 8. General Formatting Conventions

The following rules apply to all markdown files in the repo:

**Headings:** Use `#` for the document title (one per file), `##` for top-level sections, `###` for subsections. Do not skip heading levels.

**Tables:** Use standard markdown pipe tables. Include a header row and a separator row. Align columns with `|---|` (no colon alignment required).

**Filenames:** All governed documentation files use `snake_case.md`. Code files follow the conventions of their language.

**Line length:** No hard wrap. Let the editor or renderer handle wrapping.

**Code blocks:** Use fenced code blocks (triple backticks) with a language identifier when applicable.

**Emphasis:** Use `**bold**` for key terms on first use or for field labels. Use `*italic*` sparingly for secondary emphasis. Do not use bold for entire sentences.

**Lists:** Use numbered lists for ordered sequences (steps, reading orders). Use bulleted lists for unordered sets. Maintain consistent indentation (2 or 4 spaces for nesting).

**Horizontal rules:** Use `---` to separate major structural sections. Do not use them between subsections.

**Internal references:** Refer to other repo documents by filename in backticks (e.g., `dual_review_workflow.md`). Do not use relative links unless the repo tooling supports them.
