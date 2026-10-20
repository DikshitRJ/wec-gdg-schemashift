# CODEBASE.md — repository map

Canonical file list. Every non-`__init__` source file appears here **and** as a row in exactly one `openspec/specs/<capability>/spec.md` table. Spec ID = `<capability>/<file-stem>`; each source file's module docstring carries `Spec: <id>`. `scripts/check_specs.py` enforces this in CI. Paths below are relative to `src/schemashift/` unless noted.

## 1. Top-level tree

```
schemashift/
├── PLAN.md  ARCHITECTURE.md  CODEBASE.md  AGENTS.md  ORCHESTRATION.md
├── TESTING.md  CICD.md  CODE_REVIEW.md  README.md
├── pyproject.toml  uv.lock  Dockerfile  docker-compose.yml  Makefile
├── .pre-commit-config.yaml  .gitignore  .dockerignore
├── .github/workflows/{ci.yml,release.yml}  .github/dependabot.yml
├── .agents/{STATUS.md,handoff/,requests/,reviews/}
├── openspec/{project.md,AGENTS.md,specs/<capability>/spec.md,changes/}
├── docs/{hybrid-layers.md,zero-downtime.md,operations.md}
├── examples/shop/golden/{migrations,etl,orm,reports}/
├── scripts/{wt_create.sh,wt_merge.sh,check_specs.py,check_determinism.sh,gen_file_index.py,wait_for_stack.sh}
├── workspace/{schemashift.yaml,llm_cache/,out/}          # volume; out/ is gitignored
├── src/schemashift/…                                      # §2
└── tests/{unit,integration,e2e,fixtures}/…                # §3
```

## 2. Source files (`src/schemashift/`)

| Path | Owner | Spec ID | Purpose |
|---|---|---|---|
| `__init__.py` | A01 | foundation/init | `__version__` |
| `__main__.py` | A16 | cli-tui/main | `python -m schemashift` → CLI |
| `config.py` | A02 | foundation/config | YAML + env interpolation → typed `Settings` |
| `errors.py` | A02 | foundation/errors | Error taxonomy with `hint` + exit code |
| `identifiers.py` | A02 | foundation/identifiers | `quote_ident`, snake-casing, 63-char safe names |
| `normalize.py` | A06 | similarity/normalize | Name/type normalization used by scoring |
| **contracts/** | A02 | | |
| `contracts/__init__.py` | A02 | foundation/contracts-init | Re-exports |
| `contracts/schema_map.py` | A02 | foundation/schema-map | `SchemaMap`, `Table`, `Column`, `ForeignKey`, `Index`, `Decision`, `ApprovalRecord` |
| `contracts/profile.py` | A02 | foundation/profile | `SourceProfile`, `CollectionProfile`, `FieldProfile` |
| `contracts/similarity.py` | A02 | foundation/similarity-models | `SimilarityReport`, `EntityScore`, `FieldScore`, `Band` |
| `contracts/verify.py` | A02 | foundation/verify-models | `VerifyReport`, `CheckResult` |
| `contracts/llm.py` | A02 | foundation/llm-models | `SchemaProposal`, `ExplanationNote`, `RemapPatch`, … |
| `contracts/state.py` | A02 | foundation/state | `GraphState` TypedDict |
| **inspection/** | A04 | | |
| `inspection/__init__.py` | A04 | inspect/init | Re-exports |
| `inspection/sampler.py` | A04 | inspect/sampler | Deterministic systematic sampling |
| `inspection/typestats.py` | A04 | inspect/typestats | Per-path type frequency/length/range stats |
| `inspection/redact.py` | A04 | inspect/redact | Example-value redaction |
| `inspection/profile.py` | A04 | inspect/profile | Builds and writes `SourceProfile` |
| **infer/** | A05 | | |
| `infer/__init__.py` | A05 | infer/init | Re-exports |
| `infer/typemap.py` | A05 | infer/typemap | BSON → PG type + transform |
| `infer/nesting.py` | A05 | infer/nesting | Flatten / child table / JSONB rules |
| `infer/references.py` | A05 | infer/references | FK detection by name + value overlap |
| `infer/keys.py` | A05 | infer/keys | PK, unique, index candidates |
| `infer/rules.py` | A05 | infer/rules | Rule registry, `Decision` recording |
| `infer/build.py` | A05 | infer/build | Profile → draft `SchemaMap` |
| **similarity/** | A06 | | |
| `similarity/__init__.py` | A06 | similarity/init | Re-exports |
| `similarity/scoring.py` | A06 | similarity/scoring | Field/entity/overall scoring |
| `similarity/matcher.py` | A06 | similarity/matcher | Source field ↔ target column pairing |
| `similarity/report.py` | A06 | similarity/report | Build + render report JSON/MD, drag list |
| **freeze/** | A08 | | |
| `freeze/__init__.py` | A08 | freeze-gate/init | Re-exports |
| `freeze/canonical.py` | A08 | freeze-gate/canonical | Canonical JSON + sha256 |
| `freeze/gate.py` | A08 | freeze-gate/gate | Approval policy, required-approval list |
| `freeze/overrides.py` | A08 | freeze-gate/overrides | Parse/apply `overrides.yaml` |
| `freeze/freezer.py` | A08 | freeze-gate/freezer | Freeze, verify, re-freeze, ledger |
| **gen/** | A09/A10 | | |
| `gen/__init__.py` | A09 | scriptgen/init | Re-exports |
| `gen/header.py` | A09 | scriptgen/header | Hash header for generated files |
| `gen/ddl.py` | A09 | scriptgen/ddl | DDL renderer |
| `gen/rollback.py` | A09 | scriptgen/rollback | Down/cleanup renderer |
| `gen/etl_plan.py` | A10 | scriptgen/etl-plan | Declarative ETL plan + docs |
| `gen/templates/ddl.sql.j2` | A09 | scriptgen/ddl-template | DDL template |
| `gen/templates/rollback.sql.j2` | A09 | scriptgen/rollback-template | Rollback template |
| `gen/templates/etl_pipeline.md.j2` | A10 | scriptgen/etl-template | ETL documentation template |
| **migrate/** | A09/A10/A11 | | |
| `migrate/__init__.py` | A11 | migrate/init | Re-exports |
| `migrate/ordering.py` | A09 | migrate/ordering | FK topological order |
| `migrate/transforms.py` | A10 | migrate/transforms | Named typed transforms |
| `migrate/failures.py` | A11 | migrate/failures | `RowFailure`, failure report |
| `migrate/executor.py` | A11 | migrate/executor | Apply DDL/down scripts safely |
| `migrate/loader.py` | A11 | migrate/loader | Batched loader + progress |
| **verify/** | A12 | | |
| `verify/__init__.py` | A12 | verify/init | Re-exports |
| `verify/counts.py` | A12 | verify/counts | Expected vs actual counts |
| `verify/checksums.py` | A12 | verify/checksums | Column checksums |
| `verify/spotcheck.py` | A12 | verify/spotcheck | Seeded independent comparison |
| `verify/orphans.py` | A12 | verify/orphans | FK orphan scan |
| `verify/verifier.py` | A12 | verify/verifier | Runs all checks → `VerifyReport` |
| **orm/** | A13 | | |
| `orm/__init__.py` | A13 | orm/init | Re-exports |
| `orm/naming.py` | A13 | orm/naming | Class/attribute naming |
| `orm/generator.py` | A13 | orm/generator | Renders ORM package |
| `orm/templates/models.py.j2` | A13 | orm/models-template | Models |
| `orm/templates/repositories.py.j2` | A13 | orm/repositories-template | Repositories |
| `orm/templates/db.py.j2` | A13 | orm/db-template | Engine/session |
| `orm/templates/crud_demo.py.j2` | A13 | orm/crud-demo-template | CRUD smoke script |
| **llm/** | A07/A14 | | |
| `llm/__init__.py` | A07 | llm-assist/llm-init | Re-exports |
| `llm/client.py` | A07 | llm-assist/client | `LLMClient` protocol + factory |
| `llm/providers.py` | A07 | llm-assist/providers | `none`, `replay`, `openai` |
| `llm/cache.py` | A07 | llm-assist/cache | Record/replay store |
| `llm/guard.py` | A07 | llm-assist/guard | Parse/validate/redact |
| `llm/prompts/suggest_schema.md` | A14 | llm-assist/prompt-suggest | Prompt |
| `llm/prompts/explain_similarity.md` | A14 | llm-assist/prompt-explain | Prompt |
| `llm/prompts/annotate_scripts.md` | A14 | llm-assist/prompt-annotate | Prompt |
| `llm/prompts/diagnose_failures.md` | A14 | llm-assist/prompt-diagnose | Prompt |
| `llm/prompts/drift_summary.md` | A14 | llm-assist/prompt-drift | Prompt |
| `llm/prompts/refactor_notes.md` | A14 | llm-assist/prompt-refactor | Prompt |
| **assist/** | A14 | | |
| `assist/__init__.py` | A14 | llm-assist/assist-init | Re-exports |
| `assist/suggest_schema.py` | A14 | llm-assist/suggest-schema | Proposals from redacted profile |
| `assist/merge.py` | A14 | llm-assist/merge | Validate/accept proposals |
| `assist/explain_similarity.py` | A14 | llm-assist/explain-similarity | Narrative + ambiguous-pair flags |
| `assist/annotate_scripts.py` | A14 | llm-assist/annotate-scripts | `NOTES.md` sidecar |
| `assist/diagnose_failures.py` | A14 | llm-assist/diagnose-failures | `RemapPatch` suggestions |
| `assist/drift_summary.py` | A14 | llm-assist/drift-summary | Verification narrative |
| `assist/refactor_notes.py` | A14 | llm-assist/refactor-notes | `REFACTOR_NOTES.md` sidecar |
| `assist/fallbacks.py` | A14 | llm-assist/fallbacks | Deterministic templated narratives |
| **graph/** | A15 | | |
| `graph/__init__.py` | A15 | orchestration/init | Re-exports |
| `graph/build.py` | A15 | orchestration/build | Assemble `StateGraph` |
| `graph/routing.py` | A15 | orchestration/routing | Conditional edges, loop bounds |
| `graph/checkpoint.py` | A15 | orchestration/checkpoint | SQLite saver factory |
| `graph/runner.py` | A15 | orchestration/runner | Run/resume/stream events |
| `graph/nodes/__init__.py` | A15 | orchestration/nodes-init | Node registry |
| `graph/nodes/source.py` | A15 | orchestration/node-source | `load_config`, `sample_source`, `infer_candidates` |
| `graph/nodes/suggest.py` | A15 | orchestration/node-suggest | `suggest_schema`, `merge_proposals` |
| `graph/nodes/similarity.py` | A15 | orchestration/node-similarity | `similarity_report`, `explain_similarity` |
| `graph/nodes/gate.py` | A15 | orchestration/node-gate | `approval_gate`, `remap_gate` (interrupts) |
| `graph/nodes/freeze_gen.py` | A15 | orchestration/node-freeze-gen | `freeze_map`, `generate_scripts`, `annotate_scripts` |
| `graph/nodes/migrate.py` | A15 | orchestration/node-migrate | `apply_ddl`, `migrate_data`, `diagnose_failures` |
| `graph/nodes/verify.py` | A15 | orchestration/node-verify | `verify`, `drift_summary`, `rollback` |
| `graph/nodes/orm_final.py` | A15 | orchestration/node-orm-final | `generate_orm`, `refactor_notes`, `orm_smoke`, `cutover` |
| **cli/** | A16 | | |
| `cli/__init__.py` | A16 | cli-tui/init | Re-exports |
| `cli/app.py` | A16 | cli-tui/app | Typer commands |
| `cli/tui.py` | A16 | cli-tui/tui | Rich rendering (tables, panels, progress) |
| `cli/prompts.py` | A16 | cli-tui/prompts | Approval / remap prompts |
| **seed/, sample_app/** | A03 | | |
| `seed/__init__.py` | A03 | sample/seed-init | Re-exports |
| `seed/__main__.py` | A03 | sample/seed-main | `python -m schemashift.seed` |
| `seed/shop.py` | A03 | sample/shop | Deterministic dataset + injections |
| `sample_app/__init__.py` | A03 | sample/app-init | Re-exports |
| `sample_app/mongo_app.py` | A03 | sample/mongo-app | Thin pymongo CRUD ("before") |
| `sample_app/sql_app.py` | A03 | sample/sql-app | Thin CRUD using generated ORM ("after") |

## 3. Tests (`tests/`)

| Path | Owner | Covers |
|---|---|---|
| `conftest.py` | A01 | Shared fixtures, markers (`unit`, `integration`, `e2e`) |
| `fixtures/shop/{profile.json,draft_map.json,similarity.json,schema_map.frozen.json,etl_plan.json,ddl.expected.sql,rollback.expected.sql}` | A02 | Contract fixtures |
| `fixtures/seed/…` | A03 | Seed snapshot |
| `unit/test_<module>.py` (one per module) | module owner | Pure-function behavior |
| `integration/conftest.py` | A17 | DB connection retry, per-test schema reset |
| `integration/test_sampler_mongo.py` `test_ddl_apply.py` `test_loader.py` `test_verifier.py` `test_orm_crud.py` `test_llm_replay.py` | A17 | Module ↔ real DB |
| `e2e/test_happy_path.py` `test_gate_interrupt.py` `test_remap_refreeze.py` `test_verify_fail_rollback.py` `test_llm_off_equivalence.py` `test_determinism.py` `test_resume_across_processes.py` | A17 | Whole graph |

## 4. Non-source file ownership

| File(s) | Owner |
|---|---|
| `pyproject.toml`, `uv.lock`, `Dockerfile`, `docker-compose.yml`, `Makefile`, pre-commit, ignore files | A01 |
| `scripts/wt_*.sh` | lead (A00) |
| `scripts/check_specs.py`, `scripts/gen_file_index.py` | A19 |
| `scripts/check_determinism.sh`, `scripts/wait_for_stack.sh` | A17 |
| `.github/**` | A18 |
| `openspec/specs/<cap>/spec.md` | capability owner (see `AGENTS.md`), reconciled by A19 |
| `README.md`, `docs/**` | A19 |
| `.agents/reviews/**` | A20 |
