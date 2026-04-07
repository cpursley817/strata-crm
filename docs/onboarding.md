**Version:** v1.0
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

# Onboarding

This is the single entry point for anyone — human or AI — coming into the Strata project for the first time. Read this document first, then follow the reading order in Section 4.

---

## 1. Project Overview

Strata is a custom mineral acquisition CRM built for Strata (BBR), an oil and gas company based in Houston, TX. The system tracks mineral owners, land sections, deals, and acquisition workflows across the Haynesville basin in Louisiana.

The project replaces Pipedrive (a general-purpose CRM) with a purpose-built system designed around how mineral buyers actually work: linking contacts to land sections, tracking ownership interests, managing deal pipelines from initial contact through closing, and integrating live drilling activity data from Enverus.

The system currently manages 841,565 contacts sourced from three systems (AIS property records, idiCore skip-tracing data, and Pipedrive CRM exports), with a Flask/Python backend, SQLite database, and a multi-page frontend served locally. Cloud deployment to DigitalOcean is the next infrastructure milestone.

The project is in active development. Core features (contacts, sections, deals, map, calculators, document templates, AI assistant) are functional. Priority work includes pay deck data import, Pipedrive deal re-import, and cloud migration.

---

## 2. Who Is Involved

**Claude** — Lead developer and project architect. Claude has full execution authority: writes all code, manages the database, builds features, maintains documentation, and commits to the repository. Claude makes executive decisions on code structure and implementation and flags architectural decisions to the project owner when input is needed.

**Codex (ChatGPT)** — Code review partner. Codex reviews every commit using a standardized template and returns findings categorized by severity and type. Codex does not write code, make commits, or execute anything. Its role is evaluation only.

**Chase (Project Owner)** — Final decision authority on all matters. Approves or overrides Claude's disposition of Codex findings. Sets project priorities, defines feature requirements, and resolves disagreements between Claude and Codex. Works in mineral acquisition in the Haynesville basin and is the primary end user of the system.

---

## 3. How the System Works

Every code change follows a structured review loop. Claude writes and commits code, then the project owner sends the commit to Codex for review. Codex returns a standardized set of findings rated by category and severity. The project owner pastes the review back to Claude, who categorizes each finding as Adopt (will fix), Reject (not applicable), or Defer (valid but not now). The project owner approves the dispositions, Claude implements any adopted changes, and the cycle is logged in a persistent review log. The full process is defined in `dual_review_workflow.md`.

---

## 4. Recommended Reading Order

After this document, read the following in order:

1. **`doc_standards.md`** — Start here to understand how every document in the repo is structured. This file defines the versioning conventions, header/footer standards, changelog format, and formatting rules that all other documents follow. Reading it first means you will immediately recognize the structure of everything else.

2. **`dual_review_workflow.md`** — The operating manual for how code moves from development to review to merge. Covers the commit protocol, how Claude processes Codex feedback, the standing prompt for Codex sessions, the step-by-step workflow loop, and how edge cases (critical findings, disagreements, goal conflicts) are handled.

3. **`codex_review_template.md`** — The exact template Codex uses for every review. Includes the required format, severity definitions (Critical through Low), and category definitions (Bug, Security, Performance, Architecture, Style, Enhancement). Read this to understand what a review looks like and what the severity and category labels mean.

4. **`review_log.md`** — The living audit log of every completed review cycle. Each row records the commit, date, files reviewed, Codex's assessment, Claude's disposition summary, and any notes. This is the single source of truth for review history — check here instead of scrolling through chat logs.

5. **`onboarding.md`** — This document. You are already here. Return to it as a reference for project context, collaborator roles, or to find the right document for a specific question.

---

## 5. Quick Reference

| Document | What It Governs | When to Use It |
|---|---|---|
| `onboarding.md` | Project context, roles, reading order | First visit to the project or need a refresher on who does what |
| `doc_standards.md` | Formatting, versioning, structural conventions | Creating or updating any repo document |
| `dual_review_workflow.md` | Commit-review-response process | Every development cycle; resolving review disputes |
| `codex_review_template.md` | Review format, severity/category definitions | Starting a Codex review session; interpreting findings |
| `review_log.md` | Audit trail of all completed reviews | Checking past review outcomes; verifying a finding was addressed |

---

## Changelog

Current: v1.0 — Initial document created.

| Version | Date | Change Summary |
|---|---|---|
| v1.0 | 2026-03-18 | Initial document created |

## Pending Changes

1. None.
