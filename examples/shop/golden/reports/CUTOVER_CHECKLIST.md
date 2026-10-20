# Cutover Readiness Checklist

The SchemaShift migration pipeline has executed successfully.

## Validation Checklist
- [x] Source schema inspected and profiled
- [x] Schema similarity and match percentage verified
- [x] Schema map frozen and cryptographically signed
- [x] DDL applied to PostgreSQL target
- [x] Data migrated in FK topological order
- [x] Post-migration verification checks passed (counts, orphans, checksums, spot-check)
- [x] SQLAlchemy 2.0 ORM models and repositories generated
- [ ] Application data backend switched to `sql` (`orm/app.env`)
- [ ] Decommission MongoDB source after soak period
