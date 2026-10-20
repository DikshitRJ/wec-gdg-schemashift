# SchemaShift

[![CI](https://github.com/DikshitRJ/wec-gdg-schemashift/actions/workflows/ci.yml/badge.svg)](https://github.com/DikshitRJ/wec-gdg-schemashift/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![SQLAlchemy 2.0](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-red.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**SchemaShift** is a developer tool for migrating an application from **MongoDB** to **PostgreSQL**. It inspects the source database, infers a normalized relational schema, computes a mathematical similarity score (match %), gates low-confidence mappings behind a human operator, freezes an immutable schema map, generates PostgreSQL DDL/ETL/rollback scripts, executes streaming migration, independently verifies the migrated data, and synthesizes a modern **SQLAlchemy 2.0** declarative data-access layer.

The entire pipeline is orchestrated as an explicit **22-node LangGraph** state machine running entirely inside **Docker Compose** with rich terminal UI.

Every layer is **hybrid**: deterministic rule-based algorithms own truth, execution, and side effects; an optional LLM (supporting OpenAI-compatible APIs, Google Gemini, Anthropic Claude, or local replay cache) assists by proposing idiomatic names, explaining ambiguous score divergences, annotating migration risk, and providing ORM refactoring notes. **The pipeline operates end-to-end with 100% determinism with the LLM turned off (`provider=none`).**

---

## Table of Contents

- [Quickstart](#quickstart)
- [Pipeline Architecture](#pipeline-architecture)
- [Hybrid Design & Layer Justification](#hybrid-design--layer-justification)
- [Mathematical Similarity Scoring (Match %)](#mathematical-similarity-scoring-match-)
- [Live Run Sample Report](#live-run-sample-report)
- [CLI Reference](#cli-reference)
- [Configuration & Environment Variables](#configuration--environment-variables)
- [Interactive Approval Gate & Overrides](#interactive-approval-gate--overrides)
- [Generated Artifacts](#generated-artifacts)
- [Testing & Quality Verification](#testing--quality-verification)
- [Documentation Index](#documentation-index)

---

## Quickstart

### 1. Launch Services & Seed Data
```bash
# Clone the repository
git clone https://github.com/DikshitRJ/wec-gdg-schemashift.git
cd wec-gdg-schemashift

# Spin up MongoDB and PostgreSQL containers
make up

# Deterministically seed MongoDB shop database (~200 users, 50 products, 500 orders, 300 reviews)
make seed
```

### 2. Run Migration Pipeline
```bash
# Automated CI / Replay mode (non-interactive, zero external network calls)
docker compose run --rm schemashift run --ci --provider replay

# Interactive mode (human-in-the-loop review at approval gate)
docker compose run --rm schemashift run

# Run full test suite across docker stack (unit + integration + e2e)
docker compose run --rm tests pytest
```

### 3. Make Shortcuts
| Command | Description |
|---|---|
| `make up` | Start MongoDB and PostgreSQL containers and wait for healthchecks |
| `make down` | Tear down containers and delete test volumes |
| `make seed` | Deterministically seed MongoDB `shop` database |
| `make demo` | Full end-to-end non-interactive run with replay cache |
| `make demo-interactive` | Interactive run with rich terminal approval prompt |
| `make test` | Run complete unit, integration, and e2e test suites |
| `make determinism` | Verify byte-for-byte reproducibility against golden copies |
| `make verify-fast` | Fast Ruff lint, format check, unit tests, and OpenSpec validation |

---

## Pipeline Architecture

The migration is driven by an explicit 22-node LangGraph state machine:

```mermaid
flowchart TD
    START --> load_config["load_config (D)"]
    load_config --> sample_source["sample_source (D)"]
    sample_source --> infer_candidates["infer_candidates (D)"]
    infer_candidates --> suggest_schema["suggest_schema (ND)"]
    suggest_schema --> merge_proposals["merge_proposals (D)"]
    merge_proposals --> similarity_report["similarity_report (D)"]
    similarity_report --> explain_similarity["explain_similarity (ND)"]
    explain_similarity --> approval_gate{"approval_gate (D)"}
    approval_gate -->|Approved| freeze_map["freeze_map (D)"]
    approval_gate -->|Rejected / Overrides| merge_proposals
    freeze_map --> generate_scripts["generate_scripts (D)"]
    generate_scripts --> annotate_scripts["annotate_scripts (ND)"]
    annotate_scripts --> apply_ddl["apply_ddl (D)"]
    apply_ddl --> migrate_data["migrate_data (D)"]
    migrate_data -->|Success| verify["verify (D)"]
    migrate_data -->|Failed| diagnose_failures["diagnose_failures (ND)"]
    diagnose_failures --> remap_gate{"remap_gate (D)"}
    remap_gate -->|Attempts Left| merge_proposals
    remap_gate -->|Max Exceeded| rollback["rollback (D)"]
    verify --> drift_summary["drift_summary (ND)"]
    drift_summary -->|Passed| generate_orm["generate_orm (D)"]
    drift_summary -->|Failed| rollback
    generate_orm --> refactor_notes["refactor_notes (ND)"]
    refactor_notes --> orm_smoke["orm_smoke (D)"]
    orm_smoke --> cutover["cutover (D)"]
    cutover --> END
    rollback --> END
```

---

## Hybrid Design & Layer Justification

| Layer | Deterministic Core ($D$) | Non-deterministic Assist ($ND$) | Justification | Safety Gate | Match-% |
|---|---|---|---|---|---|
| **Inspect / Infer** | Systematic sampling by `_id` stride, type purity statistics, rule-based nesting & reference detection | LLM proposes clean snake_case table and column names | Schema structure is computable and reproducible; naming is ergonomic judgment | Proposals validated against strict rules; invalid ideas dropped; freeze only after gate | Inferred candidate coverage feeds similarity report |
| **Similarity / Match %** | Levenshtein name distance, type compatibility matrix, constraint alignment scoring | LLM synthesizes natural-language explanations for score drags | A match percentage must be objective and recomputable | Fields with score $< 0.85$ or low type purity trigger human gate | Produced here: overall, per-entity, per-field |
| **Script Generation** | Jinja-based PostgreSQL DDL (`001_schema.sql`), rollback (`001_schema.down.sql`), topological ETL plan | LLM generates risk warnings and review notes in sidecar `NOTES.md` | DDL and data scripts have direct production side effects | Hash-verified frozen map required; assist text isolated in markdown sidecars | Report header in script metadata |
| **Data Migration** | Streaming cursor batch loader, type coercion, retry loops, foreign key ordering | Failure diagnosis, remapping patch suggestions | Mission-critical data transfer must be safe and repeatable | Patches apply only after gate approval, re-freeze, and re-run | Per-table load statistics and error logs |
| **Verify / Rollback** | Row count comparison, SHA-256 row checksums, seeded spot-checks, orphan FK scans | LLM drift summary and likely root-cause explanations | Verification must be mathematically objective pass/fail | Automatic rollback executed if verification fails | Objective verification checklist |
| **ORM Migration** | SQLAlchemy 2.0 declarative models, session factory, repository pattern CRUD | Application refactor suggestions and query idioms | Application runtime code must strictly align with target schema | Bytecode compilation (`py_compile`) + live CRUD smoke test (`crud_demo.py`) | Generated model coverage |
| **Orchestration** | Execution, verification, and cutover nodes, routing logic, bounded retries | Schema suggestion and script annotation nodes | Explicit, auditable state machine with replayability | Checkpoint interrupts at approval gate and remap gate | Step progress streamed to terminal |

*Detailed architectural breakdown:* [docs/hybrid-layers.md](docs/hybrid-layers.md).

---

## Mathematical Similarity Scoring (Match %)

Each MongoDB source field is evaluated against its target PostgreSQL column:

$$\text{Score}_{\text{field}} = 0.35 \cdot S_{\text{name}} + 0.35 \cdot S_{\text{type}} + 0.20 \cdot S_{\text{struct}} + 0.10 \cdot S_{\text{constraints}}$$

- **$S_{\text{name}}$**: Token-set ratio and normalized Levenshtein distance.
- **$S_{\text{type}}$**: Type compatibility matrix (exact = 1.0, clean coercion = 0.8, JSONB fallback = 0.6).
- **$S_{\text{struct}}$**: Structural alignment (1:1 column = 1.0, flattened sub-object = 0.85, decomposed child table = 0.80).
- **$S_{\text{constraints}}$**: Nullability and uniqueness alignment.
- **Ambiguity Cap**: Any field with polymorphic uncoercible types or ambiguity is capped at a maximum of `0.80`.

### Confidence Bands
- **`matched`** ($\ge 0.85$): Auto-approved in interactive and CI modes.
- **`guessed`** ($0.60 - 0.85$): Auto-approved in CI mode; flagged for review in interactive mode.
- **`needs_review`** ($< 0.60$): Halts execution until approved by human operator or overridden.

---

## Live Run Sample Report

Captured directly from an end-to-end run on the `shop` dataset:

```
╭─────────────────────── Database Similarity Assessment ───────────────────────╮
│ Overall Schema Match: 93.5% (MATCHED)                                        │
│ Matched: 31 | Guessed: 7 | Needs Review: 0                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Per-Entity Alignment

| Collection | Target Tables | Match % | Fields | Matched | Guessed | Needs Review |
|---|---|---|---|---|---|---|
| `orders` | `orders, orders_items` | `94.5%` | 13 | 12 | 1 | 0 |
| `products` | `products, products_categories` | `96.3%` | 7 | 6 | 1 | 0 |
| `reviews` | `reviews` | `92.6%` | 6 | 4 | 2 | 0 |
| `users` | `users, users_tags` | `91.3%` | 12 | 9 | 3 | 0 |

### Top Score Drags (Ambiguous / Divergent Fields)

| Source Field | Target Column | Score | Band | Reason Codes |
|---|---|---|---|---|
| `userId` | `orders.user_id` | `75.5%` | `guessed` | Foreign key convention (`userId` $\to$ `user_id`) |
| `userId` | `reviews.user_id` | `75.5%` | `guessed` | Foreign key convention (`userId` $\to$ `user_id`) |
| `tags[]` | `users_tags.value` | `78.3%` | `guessed` | Primitive array decomposition |
| `rating` | `reviews.rating` | `80.0%` | `guessed` | `TYPE_PURITY_LOW` (polymorphic integer / string) |
| `categories[]` | `products_categories.value` | `80.0%` | `guessed` | Primitive array decomposition |
| `address.city` | `users.address_city` | `82.5%` | `guessed` | Flattened nested object |
| `address.zip` | `users.address_zip` | `82.5%` | `guessed` | Flattened nested object |

---

## CLI Reference

SchemaShift provides a comprehensive Typer CLI:

```bash
# 1. Run full migration pipeline
uv run python -m schemashift run [OPTIONS]
  --config PATH      Path to schemashift.yaml [default: workspace/schemashift.yaml]
  --ci               Run in non-interactive CI mode
  --provider TEXT    LLM provider: none | replay | openai [default: none]
  --run-id TEXT      Custom run identifier for checkpoint tracking
  --out-dir PATH     Override artifact destination directory

# 2. Resume an interrupted run
uv run python -m schemashift resume --run-id <run-id> --action approve|reject

# 3. Seed test database
uv run python -m schemashift seed --database shop --uri mongodb://localhost:27017

# 4. Verify migrated target
uv run python -m schemashift verify --config workspace/schemashift.yaml

# 5. Inspect and profile source database
uv run python -m schemashift inspect --config workspace/schemashift.yaml

# 6. Display similarity report
uv run python -m schemashift report --config workspace/schemashift.yaml
```

---

## Configuration & Environment Variables

SchemaShift configuration is managed in `workspace/schemashift.yaml` with environment variable interpolation:

| Environment Variable | Default | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection URI |
| `PG_URI` | `postgresql://schemashift:schemashift@localhost:5432/schemashift` | PostgreSQL target connection URI |
| `SCHEMASHIFT_LLM_PROVIDER` | `none` | LLM provider (`none`, `replay`, `openai`) |
| `SCHEMASHIFT_LLM_API_BASE` | `https://api.openai.com/v1` | Base URL for OpenAI-compatible endpoint |
| `SCHEMASHIFT_LLM_API_KEY` | *(empty)* | API key for OpenAI-compatible endpoint |
| `SCHEMASHIFT_LLM_MODEL` | `gemini-2.5-flash` | Model identifier |

---

## Interactive Approval Gate & Overrides

When low-confidence mappings occur, SchemaShift halts at the approval gate and renders a rich terminal review UI. Operators can approve, reject, or supply explicit overrides.

To customize mapping decisions declaratively, create `workspace/overrides.yaml`:

```yaml
overrides:
  - target: "reviews.rating"
    set:
      pg_type: "INTEGER"
      transform: "int_coerce"
      on_error: "coerce_int"
  - target: "users.email"
    set:
      rename: "email_address"
```

Applying overrides re-enters the pipeline, increments `map_version` to `2`, recomputes the canonical SHA-256 hash, and generates updated DDL and ETL scripts.

---

## Generated Artifacts

Outputs are written into `workspace/out/`:

```
workspace/out/
├── schema_map.frozen.json    # Canonical read-only schema mapping (chmod 444, SHA-256 verified)
├── migrations/
│   ├── 001_schema.sql        # Validated PostgreSQL DDL with primary & foreign keys, unique constraints
│   ├── 001_schema.down.sql   # Rollback script dropping all target tables
│   └── NOTES.md              # Migration overview, risk assessment, and table notes
├── etl/
│   ├── etl_plan.json         # Topological execution plan with batch sizes and type transforms
│   └── etl_pipeline.md       # Human-readable pipeline documentation
├── orm/
│   ├── db.py                 # SQLAlchemy 2.0 engine and SessionLocal factory
│   ├── models.py             # SQLAlchemy Declarative Models with relationships and type hints
│   ├── repositories.py       # Entity repositories with get/list/create/delete operations
│   ├── crud_demo.py          # Validated smoke test script exercising PostgreSQL ORM CRUD
│   ├── app.env               # Application toggle (DATA_BACKEND=sql)
│   └── REFACTOR_NOTES.md     # Codebase refactoring guide for application developers
├── reports/
│   ├── profile.json          # Source database structural and type profile
│   ├── similarity.json       # Mathematical similarity scoring data
│   ├── similarity.md         # Rich similarity markdown table
│   ├── verify.json           # Dual-database verification results (counts, checksums, spot-checks, orphans)
│   ├── drift.md              # Schema and data drift analysis
│   └── CUTOVER_CHECKLIST.md  # Production cutover verification checklist
└── state/
    ├── checkpoints.sqlite    # LangGraph checkpoint database enabling process-safe resume
    └── maps/                 # Archived versioned maps (v1.json, v2.json, ...)
```

---

## Testing & Quality Verification

SchemaShift enforces strict local and CI quality gates:

- **Local Verification Fast**:
  ```bash
  make verify-fast
  ```
  Runs `ruff check .`, `ruff format --check .`, `mypy src` (0 type errors in 92 source files), fast unit tests, and validates that all source files contain valid OpenSpec spec headers.

- **Full Test Suite**:
  ```bash
  make test
  ```
  Executes unit tests with coverage, integration tests on active Docker Compose stack, and end-to-end tests (happy path, gate interrupt, refreeze, process resumption, and rollback).

- **Determinism Check**:
  ```bash
  make determinism
  ```
  Executes consecutive clean pipeline runs and asserts that the resulting archives and frozen schema map are **100% byte-identical** and match the golden reference copies in `examples/shop/golden/`.

- **Continuous Integration (CI/CD)**:
  Universal GitHub Actions workflow ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs across all commits on all branches with a two-phase architecture and a unified verification checkmark (`ci-success`).

---

## Documentation Index

- **[Hybrid Layer Details](docs/hybrid-layers.md)**: Full 22-node breakdown, prompt templates, output contracts, and fallback safety.
- **[Zero-Downtime Migration](docs/zero-downtime.md)**: Production dual-write, Change Data Capture (CDC), shadow reads, and cutover architecture.
- **[Operations & Runbook](docs/operations.md)**: Deployment runbook, environment setup, Typer CLI guide, and failure recovery.
- **[Implementation Plan](file:///home/dikshitrj/.gemini/antigravity-cli/brain/5d54c2bc-94f7-4a82-b924-b402018abfd1/IMPLEMENTATION_PLAN.md)**: Detailed phase roadmap and execution history.
