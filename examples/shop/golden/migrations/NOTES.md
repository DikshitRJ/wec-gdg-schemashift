# Migration Risk & Script Notes

**Risk Level:** `MEDIUM`
**Summary:** Automated migration scripts generated from frozen schema map.

## Key Observations
- DDL statements use IF NOT EXISTS for safe repeated application.
- Tables are ordered topologically to preserve foreign key referential integrity.
- Foreign key constraints enforce referential integrity across root and child tables.
- JSONB columns detected. Ensure application queries use appropriate JSON operators.
