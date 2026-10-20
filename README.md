# SchemaShift

Migrate an application from **MongoDB** to **PostgreSQL**: inspect the source, infer a relational schema, report how well the two align (match %), gate low-confidence mappings behind a human, freeze a schema map, generate DDL/ETL/rollback, load and verify the data, and generate the SQLAlchemy data-access layer. Orchestrated as an explicit **LangGraph**; terminal UI only; everything runs in **Docker Compose**.

Every layer is **hybrid**: deterministic code owns truth and side effects; an optional LLM only suggests, ranks and explains. The pipeline works end to end with the LLM turned off.

---

## Quickstart

```bash
git clone <repo> && cd schemashift
docker compose up -d --wait mongo postgres
docker compose run --rm schemashift seed                          # nested sample data in MongoDB
docker compose run --rm schemashift run --ci --provider replay    # full pipeline, non-interactive
docker compose run --rm schemashift run                           # full pipeline, interactive approval gate
docker compose run --rm tests pytest                              # unit + integration + e2e
```

Make shortcuts: `make demo`, `make demo-interactive`, `make test`, `make determinism`, `make check-specs`.

Outputs land in `workspace/out/`: `migrations/`, `etl/`, `orm/`, `reports/`, `schema_map.frozen.json`.

---

## Pipeline Architecture

The migration is orchestrated by an explicit 22-node LangGraph state machine:

```mermaid
flowchart TD
    START --> load_config[load_config (D)]
    load_config --> sample_source[sample_source (D)]
    sample_source --> infer_candidates[infer_candidates (D)]
    infer_candidates --> suggest_schema[suggest_schema (ND)]
    suggest_schema --> merge_proposals[merge_proposals (D)]
    merge_proposals --> similarity_report[similarity_report (D)]
    similarity_report --> explain_similarity[explain_similarity (ND)]
    explain_similarity --> approval_gate{approval_gate (D)}
    approval_gate -->|Approved| freeze_map[freeze_map (D)]
    approval_gate -->|Rejected / Overrides| merge_proposals
    freeze_map --> generate_scripts[generate_scripts (D)]
    generate_scripts --> annotate_scripts[annotate_scripts (ND)]
    annotate_scripts --> apply_ddl[apply_ddl (D)]
    apply_ddl --> migrate_data[migrate_data (D)]
    migrate_data -->|Success| verify[verify (D)]
    migrate_data -->|Failed| diagnose_failures[diagnose_failures (ND)]
    diagnose_failures --> remap_gate{remap_gate (D)}
    remap_gate -->|Attempts Left| merge_proposals
    remap_gate -->|Max Exceeded| rollback[rollback (D)]
    verify --> drift_summary[drift_summary (ND)]
    drift_summary -->|Passed| generate_orm[generate_orm (D)]
    drift_summary -->|Failed| rollback
    generate_orm --> refactor_notes[refactor_notes (ND)]
    refactor_notes --> orm_smoke[orm_smoke (D)]
    orm_smoke --> cutover[cutover (D)]
    cutover --> END
    rollback --> END
```

---

## Hybrid Design: Layer Justification

| Layer | Deterministic ($D$) | Non-deterministic Assist ($ND$) | Why | Safety Gate | Match-% |
|---|---|---|---|---|---|
| **Inspect / Infer** | Systematic sampling, type stats, rule-based nesting/reference/key/type decisions | LLM proposes names, relations, embed-vs-table | Structure is computable and reproducible; naming is judgment | Proposals validated by rules; structural proposals need approval; freeze only after gate | Candidate coverage feeds the report |
| **Similarity / Match %** | Normalization + token/fuzzy/type/structure scoring | LLM explains ambiguous pairs; optional embeddings only flag | A % must be recomputable | < 0.85 or ambiguity → approval | Produced here: overall, per entity, per field |
| **Script Generation** | Jinja templates from the frozen map | Risk notes in sidecar `NOTES.md` | Scripts are production side effects | Hash-verified map required; ND text never in script bodies | Report header in notes |
| **Data Migration** | FK-ordered batched loader, retries, typed transforms | Failure diagnosis, remap suggestion | Safe, repeatable loading | Patch applies only after approval + re-freeze + re-run | Per-table load stats |
| **Verify / Rollback** | Counts, checksums, seeded spot-checks, orphan scan, rollback SQL | Drift summary and likely causes | Objective pass/fail | Pass/fail by code only | — |
| **ORM Migration** | SQLAlchemy models/repositories from the frozen map | Refactor notes, query idioms | Runtime code must match schema | `py_compile` + import + CRUD smoke; notes are review-only | — |
| **Orchestration** | Execute/verify/cutover nodes, routing, bounded loops | suggest/explain nodes, interrupts | Explicit, auditable control flow | Interrupts at approval and remap | Report before approval |

Full per-layer justification: [docs/hybrid-layers.md](docs/hybrid-layers.md).

---

## Match Percentage (Live Run Output)

Normalize names and types, then score each source field against the column it maps to:
$$\text{field} = 0.35 \cdot \text{name} + 0.35 \cdot \text{type} + 0.20 \cdot \text{structure} + 0.10 \cdot \text{constraints}$$
with an ambiguity cap of 0.80. Entity and overall scores aggregate field scores (unmapped fields count as 0). Bands: **matched** $\ge 0.85$ · **guessed** $0.60 - 0.85$ · **needs_review** $< 0.60$. The LLM never touches the number.

### Real Sample Report from `shop` Dataset

**Overall Match:** `93.5%` (MATCHED)
- Matched: `31` fields
- Guessed: `7` fields
- Needs Review: `0` fields

#### Per-Entity Alignment

| Collection | Target Tables | Match % | Fields | Matched | Guessed | Needs Review |
|---|---|---|---|---|---|---|
| `orders` | `orders, orders_items` | `94.5%` | 13 | 12 | 1 | 0 |
| `products` | `products, products_categories` | `96.3%` | 7 | 6 | 1 | 0 |
| `reviews` | `reviews` | `92.6%` | 6 | 4 | 2 | 0 |
| `users` | `users, users_tags` | `91.3%` | 12 | 9 | 3 | 0 |

#### Top Score Drags (Ambiguous / Divergent Fields)

| Source Field | Target Column | Score | Band | Reasons |
|---|---|---|---|---|
| `userId` | `orders.user_id` | `75.5%` | `guessed` | Foreign key convention |
| `userId` | `reviews.user_id` | `75.5%` | `guessed` | Foreign key convention |
| `tags[]` | `users_tags.value` | `78.3%` | `guessed` | Primitive array decomposition |
| `rating` | `reviews.rating` | `80.0%` | `guessed` | `TYPE_PURITY_LOW` (polymorphic int/string) |
| `categories[]` | `products_categories.value` | `80.0%` | `guessed` | Primitive array decomposition |
| `address.city` | `users.address_city` | `82.5%` | `guessed` | Flattened sub-object |
| `address.zip` | `users.address_zip` | `82.5%` | `guessed` | Flattened sub-object |

---

## Configuration

Configured in `workspace/schemashift.yaml` (source/target URIs via env, sampling, inference thresholds, scoring weights, migration options, LLM provider, overrides file). See [docs/operations.md](docs/operations.md).

---

## Interactive Schema Review

At the gate you can approve, reject (fall back to the rule default), or edit a mapping; edits become entries in `workspace/overrides.yaml`, and the map is re-scored and re-frozen (`map_version` + 1) with an immutable SHA-256 hash.

---

## Testing & Verification

Comprehensive test suites covering unit, property, contract, integration, and end-to-end verification:
- `make verify-fast`: Ruff lint + format check, fast unit tests, OpenSpec spec checker.
- `make test`: Full unit, integration, and e2e suites with coverage report.
- `make determinism`: Runs consecutive pipeline runs from scratch, verifying byte-for-byte identical output against `examples/shop/golden/`.

---

## Architectural Documentation

- **[Hybrid Layer Details](docs/hybrid-layers.md)**: Deep dive into deterministic vs non-deterministic separation, Pydantic contracts, and fallback safety.
- **[Zero-Downtime Migration](docs/zero-downtime.md)**: Production dual-write, CDC change data capture, shadow reads, and cutover architecture.
- **[Operations & Runbook](docs/operations.md)**: Deployment, environment configuration, Typer CLI reference, and failure recovery.
