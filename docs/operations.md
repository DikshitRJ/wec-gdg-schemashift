# SchemaShift Operations & Runbook

This runbook covers day-to-day operations, environment setup, CLI commands, approval gate management, and disaster recovery procedures.

---

## 1. Quickstart & Service Stack

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (or `uv` package manager)

### Starting the Infrastructure
```bash
# Start MongoDB and PostgreSQL containers and wait for healthchecks
make up

# Deterministically seed MongoDB shop database (~200 users, 50 products, 500 orders, 300 reviews)
make seed

# Run automated demo with zero-shot replay cache
make demo

# Tear down the stack and clean volumes
make down
```

---

## 2. Configuration & Environment Variables

SchemaShift configuration is managed in `workspace/schemashift.yaml` and enriched via environment variables:

| Variable | Default Value | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection URI |
| `PG_URI` | `postgresql://schemashift:schemashift@localhost:5432/schemashift` | PostgreSQL connection URI |
| `SCHEMASHIFT_LLM_PROVIDER` | `none` | LLM provider (`none`, `replay`, `openai`) |
| `SCHEMASHIFT_LLM_API_BASE` | `https://api.openai.com/v1` | Base URL for OpenAI-compatible endpoint |
| `SCHEMASHIFT_LLM_API_KEY` | *(empty)* | API key for OpenAI-compatible endpoint |
| `SCHEMASHIFT_LLM_MODEL` | `gemini-2.5-flash` | Model identifier |

---

## 3. CLI Command Reference

SchemaShift provides an intuitive Typer CLI:

### 1. `schemashift run`
Executes the full LangGraph migration pipeline.
```bash
# Interactive mode (halts at approval gate if manual review required)
uv run python -m schemashift run

# Non-interactive CI mode (auto-approves guessed mappings, halts only on critical blocked items)
uv run python -m schemashift run --ci --provider replay

# Override output directory
uv run python -m schemashift run --out-dir /path/to/custom/out
```

### 2. `schemashift resume`
Resumes an execution suspended at an approval or remap gate.
```bash
# Approve suspended run
uv run python -m schemashift resume --run-id <run-id> --action approve

# Reject suspended run
uv run python -m schemashift resume --run-id <run-id> --action reject
```

### 3. `schemashift seed`
Populates MongoDB with deterministic test data.
```bash
uv run python -m schemashift seed --database shop --uri mongodb://localhost:27017
```

### 4. `schemashift verify`
Executes independent dual-database verification against migrated PostgreSQL.
```bash
uv run python -m schemashift verify --config workspace/schemashift.yaml
```

---

## 4. Approval Gate & Overrides

When SchemaShift detects ambiguous fields or low confidence mappings, it marks them for review:
- **`matched`**: $\ge 85\%$ confidence, auto-approved.
- **`guessed`**: $70\% - 85\%$ confidence, auto-approved in CI mode, flagged in interactive mode.
- **`needs_review`**: $< 70\%$ confidence or low type purity, blocks until approved or overridden.

### Applying Schema Overrides
Create or edit `workspace/overrides.yaml`:
```yaml
overrides:
  - target: "reviews.rating"
    set:
      pg_type: "INTEGER"
      on_error: "coerce_int"
  - target: "users.email"
    set:
      rename: "email_address"
```

Re-running `schemashift run` incorporates these overrides into `schema_map.frozen.json` with an incremented `map_version` and recalculates the canonical SHA-256 hash.

---

## 5. Artifact Directory Layout

All outputs are written into `workspace/out/`:
```
workspace/out/
├── schema_map.frozen.json    # Canonical read-only schema mapping (chmod 444)
├── migrations/
│   ├── 001_schema.sql        # PostgreSQL DDL
│   ├── 001_schema.down.sql   # Rollback DDL
│   └── NOTES.md              # Migration overview and risk notes
├── etl/
│   ├── etl_plan.json         # Topological ETL step plan
│   └── etl_pipeline.md       # Human-readable pipeline explanation
├── orm/
│   ├── db.py                 # SQLAlchemy engine and session factory
│   ├── models.py             # SQLAlchemy 2.0 Declarative Models
│   ├── repositories.py       # CRUD repositories for root entities
│   ├── crud_demo.py          # Validated smoke test script
│   ├── app.env               # Application environment toggle (DATA_BACKEND=sql)
│   └── REFACTOR_NOTES.md     # Codebase refactoring guide
├── reports/
│   ├── profile.json          # MongoDB source database profile
│   ├── similarity.json       # Mathematical similarity scoring report
│   ├── similarity.md         # Rich similarity report table
│   ├── verify.json           # Dual-database verification report
│   ├── drift.md              # Drift analysis
│   └── CUTOVER_CHECKLIST.md  # Production cutover checklist
└── state/
    ├── checkpoints.sqlite    # LangGraph checkpoint store
    └── maps/                 # Versioned schema map archive (v1.json, v2.json)
```
