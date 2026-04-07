**Version:** v1.1
**Last Updated:** 2026-03-18

## Related Documents

| Document | Description |
|---|---|
| `onboarding.md` | Entry point for the repo; recommended reading order and project overview |
| `dual_review_workflow.md` | Governs the commit, review, and response process |
| `codex_review_template.md` | Standardized template Codex uses for all reviews |
| `review_log.md` | Living audit log of all completed review cycles |
| `doc_standards.md` | Documentation conventions and standards for this repo |

---

# Dual-Review Workflow

This document governs the commit-review-response cycle between Claude (lead developer), Codex (code reviewer), and the project owner. Every code change flows through this process.

---

## 1. Commit Protocol

### What Triggers a Codex Review

**Every push to the remote repository triggers a review.** There is no distinction between milestone and incremental commits. If it was worth committing, it is worth reviewing.

**Cycle-closing commits are exempt.** The commit at the end of each workflow cycle (Step 8) contains adopted fixes, the review log update, and any cross-reference updates as a single atomic push. This commit does not trigger a new review cycle — it closes the current one. The next review cycle begins when the next development commit is pushed.

If multiple commits are pushed in a batch before a review is initiated, Codex reviews the full diff across all commits in the batch as a single review cycle. The Review Log records the range (e.g., `abc1234..def5678`).

### What to Send Codex

When initiating a review, provide Codex with:

1. **The commit ID(s)** or branch diff being reviewed.
2. **A one-sentence summary** of what the commit accomplishes.
3. **Files touched** — listed explicitly so Codex can focus its review.
4. **Focus areas** (optional) — specific concerns to prioritize, such as "pay attention to SQL injection surface" or "validate the migration logic." If no focus area is specified, Codex performs a general review.
5. **A reminder to use the standardized review format** defined in `codex_review_template.md`.

### Standing Codex Prompt

The following block should be pasted to Codex at the start of every review session to establish context. Adjust the commit-specific fields each time:

```
You are Codex, the code review partner for the Strata project — a mineral acquisition
CRM built for Strata. Your role is evaluation only; you do not execute code
or make commits.

Review the following commit using the standardized format in codex_review_template.md
(available in mineral-crm/docs/ in the repo).

Governance docs are in mineral-crm/docs/:
- onboarding.md — project overview and collaborator roles
- dual_review_workflow.md — the full review process you are participating in
- codex_review_template.md — the format you must use for reviews
- doc_standards.md — documentation conventions for the repo

Project context files are elsewhere in the repo:
- MASTER_FEATURE_LIST.md — prioritized feature backlog (repo root)
- TODO.md — current sprint items (repo root)
- docs/architecture.md — system architecture
- docs/schema_design.md — database schema

Commit: [COMMIT_ID]
Summary: [ONE_SENTENCE_SUMMARY]
Files changed: [FILE_LIST]
Focus areas: [OPTIONAL_FOCUS or "General review"]
```

---

## 2. Claude Response Protocol

### Processing Codex Feedback

When the project owner pastes Codex's review into the chat, Claude will:

1. **Parse every numbered finding** from the review.
2. **Categorize each finding** with one of three dispositions:
   - **Adopt** — The finding is valid and will be implemented. Claude states what will change and in which file.
   - **Reject** — The finding is not applicable, is based on a misunderstanding, or conflicts with a deliberate design decision. Claude states the specific reason.
   - **Defer** — The finding is valid but not actionable in the current cycle (e.g., requires architectural work, depends on a future feature, or is low priority). Claude states when it will be addressed or what it is waiting on.
3. **Present the disposition table** to the project owner before making any code changes, so the owner can override any categorization.

### Disposition Table Format

```
| Finding # | Category | Severity | Disposition | Reasoning |
|---|---|---|---|---|
| 1 | Bug | High | Adopt | Off-by-one in pagination query; fixing in app.py |
| 2 | Architecture | Medium | Defer | Valid concern; requires schema migration planned for Session 14 |
| 3 | Style | Low | Reject | Project uses single quotes per existing convention |
```

### Escalation

If Claude and Codex fundamentally disagree on a finding — meaning Claude believes adopting the suggestion would harm the system and Codex has flagged it as High or Critical — Claude will:

1. Present both positions to the project owner with explicit tradeoffs.
2. State its recommended disposition and the reasoning.
3. **Not proceed** until the project owner makes the call.

Low and Medium findings where Claude and Codex disagree do not require escalation. Claude states its reasoning in the disposition table and moves on unless the owner intervenes.

---

## 3. Shared Context Protocol

### Codex Onboarding

Before the first review session, the project owner should direct Codex to read the following files in the repo (in this order):

1. `onboarding.md` — project overview and roles
2. `doc_standards.md` — document structure and versioning conventions
3. `dual_review_workflow.md` — the process Codex participates in
4. `codex_review_template.md` — the format Codex must use
5. `architecture.md` — system design
6. `schema_design.md` — database schema
7. `MASTER_FEATURE_LIST.md` — feature backlog and priorities

This only needs to happen once. After the initial onboarding, Codex can reference these files directly from the repo as needed.

### Per-Session Context

At the start of each review session, paste the Standing Codex Prompt from Section 1 above. This ensures Codex has the commit-specific context it needs without requiring a full re-read of the project docs.

If the commit touches a subsystem Codex has not previously reviewed (e.g., the Enverus integration, the geocoding proxy), add a one-line pointer to the relevant file or doc so Codex can pull additional context from the repo.

### Document Availability

Governed workflow documents live in `mineral-crm/docs/`. Project context files (`MASTER_FEATURE_LIST.md`, `TODO.md`) live at the repo root. Codex has read access to the full repository and can reference any file directly. There is no need to paste document contents into the chat unless Codex explicitly requests clarification on a specific section.

---

## 4. Workflow Loop

The following numbered sequence repeats for every development cycle:

1. **Claude writes code.** Feature work, bug fixes, refactoring, or documentation changes are developed and tested locally.

2. **Claude commits and pushes.** The commit message follows conventional format: a short summary line, optionally followed by a body with additional context.

3. **Project owner sends the commit to Codex for review.** The owner pastes the Standing Codex Prompt (Section 1) with the commit-specific details filled in, and instructs Codex to review using the format in `codex_review_template.md`.

4. **Codex returns a review.** The review follows the standardized template: summary, numbered findings, overall assessment, and open questions.

5. **Project owner pastes Codex's review into the Claude chat.** No additional instructions are needed — Claude knows to process it per this document.

6. **Claude processes the review and presents a disposition table.** Each finding is categorized as Adopt / Reject / Defer with reasoning. Claude waits for owner approval before proceeding.

7. **Project owner approves the disposition** (or overrides specific items).

8. **Claude implements adopted findings, updates the Review Log, and updates cross-references — all in one atomic commit.** This single cycle-closing commit includes:
   - Code changes for all adopted findings. Rejected and deferred items require no code changes.
   - A new row in `review_log.md` with the commit ID, date, files reviewed, Codex's overall assessment, a summary of Claude's dispositions, and any relevant notes. The Last Updated field in the header is updated.
   - If any new document was committed to the repo during this cycle: an updated Document Registry in `doc_standards.md` and updated Related Documents sections in all existing governed documents.

   This commit is then pushed. Per Section 1, cycle-closing commits are exempt from triggering a new review. The cycle is now closed.

---

## 5. Edge Cases

### Critical or Block-Level Finding Mid-Sprint

If Codex returns an overall assessment of **Block** or flags any individual finding as **Critical**:

1. Claude stops all other work in progress.
2. Claude presents the Critical/Block findings to the project owner immediately with a recommended resolution.
3. No further feature work is committed until the Critical/Block items are resolved or the project owner explicitly overrides.

### Fundamental Disagreement Between Claude and Codex

If Claude believes a Codex recommendation would introduce a regression, violate an architectural constraint, or degrade the system, and Codex has rated the finding as High or Critical:

1. Claude writes up both positions with concrete tradeoffs (not abstract concerns).
2. The project owner makes the final call.
3. The decision and reasoning are recorded in the Notes column of the Review Log for that cycle.

For Medium and Low disagreements, Claude states its reasoning in the disposition table and proceeds. The owner can intervene if they disagree with Claude's call.

### Conflict with Long-Term Goals

If Codex suggests a direction that contradicts the priorities, architecture decisions, or roadmap documented in the repo's markdown files (e.g., `MASTER_FEATURE_LIST.md`, `architecture.md`, `TODO.md`):

1. Claude flags the conflict in the disposition table with a specific reference to the contradicted document and section.
2. The finding is categorized as **Reject** with the reasoning: "Conflicts with [document] — [brief explanation]."
3. If the project owner believes the long-term goals should be updated to accommodate the suggestion, that becomes a separate discussion and a separate commit.

---

## Changelog

Current: v1.1 — Clarified workflow loop termination, fixed file path guidance, added doc_standards.md to Codex onboarding.

| Version | Date | Change Summary |
|---|---|---|
| v1.1 | 2026-03-18 | Clarified cycle-closing commits are exempt from review; consolidated workflow Steps 8-10 into one atomic commit; split governed docs vs project context file paths in standing prompt and Document Availability; added doc_standards.md to Codex onboarding reading order |
| v1.0 | 2026-03-18 | Initial document created |

## Pending Changes

1. None.
