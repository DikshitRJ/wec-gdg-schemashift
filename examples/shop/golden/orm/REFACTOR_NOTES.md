# ORM Migration Refactor Notes

The application data access layer has been generated with SQLAlchemy 2.0.

## Review Items
- Fields marked `# REVIEW:`: check JSONB and coerced numeric conversions.
- Repository methods provide standard CRUD (`get`, `list`, `create`, `delete`).
- Verify custom application queries and indices before production cutover.


## Assisted Query Refactor Guidance

Use SQLAlchemy session queries and repository methods for basic CRUD.
