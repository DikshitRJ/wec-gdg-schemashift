# SchemaShift

Migrate an application from **MongoDB** to **PostgreSQL**: inspect the source, infer a relational schema, report how well the two align (match %), gate low-confidence mappings behind a human, freeze a schema map, generate DDL/ETL/rollback, load and verify the data, and generate the SQLAlchemy data-access layer. Orchestrated as an explicit **LangGraph**; terminal UI only; everything runs in **Docker Compose**.

Every layer is **hybrid**: deterministic code owns truth and side effects; an optional LLM only suggests, ranks and explains. The pipeline works end to end with the LLM turned off.

> _Skeleton owned by A19. Sections marked `TODO(A19)` are filled in the final docs commit from a real run._

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

## Pipeline

`TODO(A19)`: embed the mermaid graph from `ARCHITECTURE.md` §2 and a captured terminal screenshot/transcript of the similarity table and the approval gate.

## Hybrid design: layer → deterministic → non-deterministic → why → gate → match-%

| Layer | Deterministic | Non-deterministic | Why | Safety gate | Match-% |
|---|---|---|---|---|---|
| Inspect / Infer | Systematic sampling, type stats, rule-based nesting/reference/key/type decisions | LLM proposes names, relations, embed-vs-table | Structure is computable and reproducible; naming is judgment | Proposals validated by rules; structural proposals need approval; freeze only after gate | Candidate coverage feeds the report |
| Similarity / Match % | Normalization + token/fuzzy/type/structure scoring | LLM explains ambiguous pairs; optional embeddings only flag | A % must be recomputable | < 0.85 or ambiguity → approval | Produced here: overall, per entity, per field |
| Script generation | Jinja templates from the frozen map | Risk notes in sidecar `NOTES.md` | Scripts are production side effects | Hash-verified map required; ND text never in script bodies | Report header in notes |
| Data migration | FK-ordered batched loader, retries, typed transforms | Failure diagnosis, remap suggestion | Safe, repeatable loading | Patch applies only after approval + re-freeze + re-run | Per-table load stats |
| Verify / rollback | Counts, checksums, seeded spot-checks, orphan scan, rollback SQL | Drift summary and likely causes | Objective pass/fail | Pass/fail by code only | — |
| ORM migration | SQLAlchemy models/repositories from the frozen map | Refactor notes, query idioms | Runtime code must match schema | `py_compile` + import + CRUD smoke; notes are review-only | — |
| Orchestration | Execute/verify/cutover nodes, routing, bounded loops | suggest/explain nodes, interrupts | Explicit, auditable control flow | Interrupts at approval and remap | Report before approval |

Full per-layer justification: `docs/hybrid-layers.md` (`TODO(A19)`).

## Match percentage

Normalize names/types, then score each source field against the column it maps to:
`field = 0.35·name + 0.35·type + 0.20·structure + 0.10·constraints`, with an ambiguity cap of 0.80. Entity and overall scores aggregate field scores (unmapped fields count as 0). Bands: matched ≥ 0.85 · guessed 0.60–0.85 · needs_review < 0.60. The LLM never touches the number. Details: `ARCHITECTURE.md` §7.

`TODO(A19)`: paste the real sample report (overall %, per-entity %, drag list).

## Configuration

`workspace/schemashift.yaml` (source/target URIs via env, sampling, inference thresholds, scoring weights, migration options, LLM provider, overrides file). See `ARCHITECTURE.md` §14.

## Interactive schema review

At the gate you can approve, reject (fall back to the rule default) or edit a mapping; edits become entries in `overrides.yaml`, the map is re-scored and re-frozen (`map_version` + 1).

## Testing and CI

Unit, property, contract, integration and end-to-end suites with failure injection, LLM-off equivalence and byte-for-byte determinism checks. See `TESTING.md` and `CICD.md`.

## Orchestration and agent-built history

Built spec-first with OpenSpec (`openspec/`), by parallel agents on git worktrees. See `PLAN.md`, `AGENTS.md`, `ORCHESTRATION.md`, `CODE_REVIEW.md`.

## Limitations and future work

- ORM path implemented: native `pymongo` → SQLAlchemy 2.0 (Prisma/Drizzle/TypeORM/Sequelize templates are not included).
- Verifier checksums reuse transform code; the independent spot-check and golden transform tests cover this.
- Zero-downtime migration is a written design (`docs/zero-downtime.md`, `TODO(A19)`); SQL→NoSQL is not implemented.
