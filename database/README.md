# Database

## Overview
SQLite database for the Mineral Buyer CRM prototype. Stores owners, sections, ownership links, deals, activities, and supporting reference data.

## Files
- `schema.sql` — Full database schema (tables, indexes, triggers)
- `migrations/` — Incremental schema changes, numbered sequentially (001_, 002_, etc.)
- `seeds/` — Sample/test data for development

## Usage
Initialize database: `sqlite3 mineral_crm.db < schema.sql`
Apply migration: `sqlite3 mineral_crm.db < migrations/001_description.sql`
