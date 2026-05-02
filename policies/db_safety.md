# Database Safety Policy

Phase 1 database access is read-only. The agent may only run parser-validated SELECT-like SQL against approved schema-qualified tables.

Forbidden behavior includes INSERT, UPDATE, DELETE, MERGE, DROP, CREATE, ALTER, TRUNCATE, command statements, and any production mutation.
