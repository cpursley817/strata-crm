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

# Codex Review Template

This is the standardized format Codex must use for every code review. The template is designed to be parseable by Claude for automated disposition processing. Do not deviate from this structure.

---

## Template

Codex should copy the structure below and fill in the bracketed fields for each review.

---

### Review Summary

**Commit:** [commit ID or range]
**Date:** [YYYY-MM-DD]
**Summary:** [one-sentence description of what the commit accomplishes]
**Files Reviewed:**

- [file1.py]
- [file2.js]
- [...]

---

### Findings

Each finding is a numbered entry with the following fields. All fields are required. If a field is not applicable (e.g., no specific line reference), write "N/A".

If there are no findings, write: "No findings." and proceed to Overall Assessment.

---

**Finding #1**

- **Category:** [Bug / Security / Performance / Architecture / Style / Enhancement]
- **Severity:** [Critical / High / Medium / Low]
- **File:** [filename]
- **Line(s):** [line number or range, or N/A]
- **Description:** [What the issue or suggestion is. Be specific — reference variable names, function names, or logic paths.]
- **Suggested Fix:** [Concrete recommendation. If the fix involves code, include a brief snippet or pseudocode. If the fix involves a design change, describe the alternative approach.]

---

**Finding #2**

- **Category:**
- **Severity:**
- **File:**
- **Line(s):**
- **Description:**
- **Suggested Fix:**

---

*(Repeat for each finding. Number sequentially.)*

---

### Overall Assessment

**Assessment:** [Approve / Approve with Minor Concerns / Needs Revision / Block]

**Rationale:** [Two to three sentences explaining the overall assessment. Reference the most significant findings by number.]

---

### Open Questions

Items Codex is uncertain about or lacks sufficient project context to evaluate. These are not findings — they are questions directed at Claude or the project owner for clarification.

1. [Question or uncertainty, with enough context for Claude to respond.]
2. [...]

If none, write: "No open questions."

---

## Severity Definitions

These definitions ensure consistent severity ratings across all reviews.

**Critical:** The code will cause data loss, a security vulnerability, or a system crash in production. Must be resolved before merge.

**High:** The code has a significant bug, a meaningful performance regression, or an architectural issue that will compound if not addressed now. Should be resolved before merge; may be deferred only with explicit project owner approval.

**Medium:** The code works but has a noticeable quality issue — unclear logic, missing validation, suboptimal patterns, or technical debt that will slow future development. Should be addressed but does not block merge.

**Low:** Style issues, minor naming concerns, documentation gaps, or suggestions that improve code quality but have no functional impact. Address at convenience.

---

## Category Definitions

**Bug:** The code does not behave as intended. Includes logic errors, off-by-one errors, incorrect return values, unhandled edge cases.

**Security:** The code exposes a vulnerability. Includes SQL injection, unvalidated input, exposed credentials, missing authentication checks, insecure defaults.

**Performance:** The code is functionally correct but inefficient. Includes unnecessary queries, N+1 patterns, missing indexes, unoptimized loops, excessive memory usage.

**Architecture:** The code's structure or design will cause problems at scale or contradicts established patterns. Includes coupling issues, responsibility violations, schema design concerns.

**Style:** The code does not follow project conventions. Includes naming, formatting, comment quality, file organization.

**Enhancement:** The code works and meets requirements, but Codex sees an opportunity to improve it. Includes better error messages, additional validation, UX improvements, refactoring suggestions.

---

## Changelog

Current: v1.1 — Added zero-findings instruction.

| Version | Date | Change Summary |
|---|---|---|
| v1.1 | 2026-03-18 | Added instruction for rendering Findings section when there are no findings |
| v1.0 | 2026-03-18 | Initial document created |

## Pending Changes

1. None.
