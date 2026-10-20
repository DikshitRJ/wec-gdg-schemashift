# AGENTS.md — roster, rules and briefs

Read this first if you are an agent. Then read `ARCHITECTURE.md` and the spec(s) you own.

## 1. Golden rules

1. **Hybrid rule.** Deterministic code owns truth and side effects. LLM code only suggests, ranks, explains. If in doubt, push logic to the deterministic side.
2. **Spec-first.** Implement against `openspec/specs/<capability>/spec.md`. If reality diverges, update the spec you own in the same branch.
3. **Own your paths.** Edit only files in your ownership list (§3). Need a change elsewhere? Write `.agents/requests/<from>-to-<owner>.md` and tell the lead.
4. **Contracts are frozen** after H1. Use `tests/fixtures/shop/*` as ground truth for upstream data.
5. **No raw SQL values.** Parameterize values; identifiers go through `identifiers.quote_ident`.
6. **No LLM outside `llm/` and `assist/`.** Nothing in `assist/` ever receives a DB handle or credentials.
7. **Reproducible output.** Sorted iteration, no timestamps/uuids/randomness in generated artifacts (seeded `random.Random` only where specified).
8. **Fail loudly** with a `SchemaShiftError` carrying an actionable `hint`.
9. **Every source file** starts with a module docstring containing `Spec: <capability>/<stem>`.
10. **Small commits inside your branch are fine**; the lead squash-merges into one conventional commit.

## 2. Roster (20 subagents + lead)

| ID | Slug / branch | Wave | Phase | Depends on |
|---|---|---|---|---|
| A00 | lead (orchestrator, merger) | all | all | — |
| A01 | `agent/01-scaffold` | W0 | P0 | — |
| A02 | `agent/02-contracts` | W0 | P0 | A01 (parallel; merge order A01→A02) |
| A03 | `agent/03-seed` | W1 | P1 | A02 |
| A04 | `agent/04-inspection` | W1 | P1 | A02 |
| A05 | `agent/05-infer` | W1 | P1 | A02 |
| A06 | `agent/06-similarity` | W1 | P2 | A02 |
| A07 | `agent/07-llm-core` | W1 | P2 | A02 |
| A08 | `agent/08-freeze-gate` | W1 | P2 | A02 |
| A09 | `agent/09-ddl-gen` | W1 | P3 | A02 |
| A10 | `agent/10-etl-gen` | W1 | P3 | A02 |
| A11 | `agent/11-loader` | W2 | P4 | A09, A10 |
| A12 | `agent/12-verifier` | W2 | P4 | A02, A10 (transforms) |
| A13 | `agent/13-orm-gen` | W2 | P5 | A02 |
| A14 | `agent/14-assist` | W2 | P5 | A06, A07 |
| A15 | `agent/15-graph` | W3 | P6 | A04–A14 |
| A16 | `agent/16-cli-tui` | W3 | P6 | A15 (contract of runner events from A02 `state.py`) |
| A17 | `agent/17-tests` | W2–W4 | P7 | modules as they merge |
| A18 | `agent/18-cicd` | drafts W1, merges W4 | P7 | A17 |
| A19 | `agent/19-docs` | script W1, docs W5 | P9 | all |
| A20 | `agent/20-review` | W1–W4 (RP1–RP4) | P8 | per review point |

## 3. Ownership (no overlaps)

| Agent | Owns |
|---|---|
| A01 | `pyproject.toml`, `uv.lock`, `Dockerfile`, `docker-compose.yml`, `Makefile`, `.pre-commit-config.yaml`, `.gitignore`, `.dockerignore`, `src/schemashift/__init__.py`, `tests/conftest.py` |
| A02 | `contracts/*`, `config.py`, `errors.py`, `identifiers.py`, `tests/fixtures/shop/*`, `tests/unit/test_{contracts,config,errors,identifiers}.py`, spec `foundation` |
| A03 | `seed/*`, `sample_app/*`, `tests/fixtures/seed/*`, `tests/unit/test_seed.py`, spec `sample` |
| A04 | `inspection/*`, `tests/unit/test_{sampler,typestats,redact,profile}.py`, spec `inspect` |
| A05 | `infer/*`, `tests/unit/test_infer_*.py`, spec `infer` |
| A06 | `normalize.py`, `similarity/*`, `tests/unit/test_{normalize,scoring,matcher,report}.py`, spec `similarity` |
| A07 | `llm/{__init__,client,providers,cache,guard}.py`, `tests/unit/test_llm_*.py` |
| A08 | `freeze/*`, `tests/unit/test_{canonical,gate,overrides,freezer}.py`, spec `freeze-gate` |
| A09 | `gen/{__init__,header,ddl,rollback}.py`, `gen/templates/{ddl,rollback}.sql.j2`, `migrate/ordering.py`, `tests/unit/test_{ddl,rollback,ordering}.py`, spec `scriptgen` (DDL parts) |
| A10 | `gen/etl_plan.py`, `gen/templates/etl_pipeline.md.j2`, `migrate/transforms.py`, `tests/unit/test_{etl_plan,transforms}.py`, spec `scriptgen` (ETL parts) |
| A11 | `migrate/{__init__,failures,executor,loader}.py`, `tests/unit/test_{failures,loader_unit}.py`, spec `migrate` |
| A12 | `verify/*`, `tests/unit/test_{counts,checksums,spotcheck,orphans,verifier}.py`, spec `verify` |
| A13 | `orm/*`, `tests/unit/test_orm_*.py`, spec `orm` |
| A14 | `llm/prompts/*`, `assist/*`, `tests/unit/test_assist_*.py`, spec `llm-assist` |
| A15 | `graph/*`, `tests/unit/test_graph_*.py`, spec `orchestration` |
| A16 | `cli/*`, `__main__.py`, `tests/unit/test_cli_*.py`, spec `cli-tui` |
| A17 | `tests/integration/*`, `tests/e2e/*`, `scripts/check_determinism.sh`, `scripts/wait_for_stack.sh`, `TESTING.md` |
| A18 | `.github/**`, `CICD.md` |
| A19 | `README.md`, `docs/**`, `scripts/check_specs.py`, `scripts/gen_file_index.py`, `CODEBASE.md`, `openspec/project.md`, `openspec/AGENTS.md`, spec `delivery` |
| A20 | `.agents/reviews/**`, `CODE_REVIEW.md` |
| A00 | `PLAN.md`, `ARCHITECTURE.md`, `AGENTS.md`, `ORCHESTRATION.md`, `scripts/wt_*.sh`, `.agents/STATUS.md` |

## 4. Prompt preamble (sent to every subagent)

```
You are agent {ID} ({slug}) on SchemaShift. Work ONLY inside your git worktree {path} on branch {branch}.
1. Read AGENTS.md, ARCHITECTURE.md, and the openspec spec(s) you own. Your brief is below.
2. Implement your owned files only; use tests/fixtures/shop/* as upstream truth.
3. Write unit tests as you go. Run `make verify-fast` until green.
4. Add `Spec: <capability>/<stem>` to each module docstring; keep your spec table accurate.
5. Time box: {minutes} minutes. If at risk, deliver the minimal path and list gaps in the handoff.
6. Write .agents/handoff/{NN}-{slug}.md: what exists, how to run it, known gaps, requests to other owners.
7. Do not merge. Report DONE with the branch name to the lead.
```

## 5. Briefs

**A01 scaffold-infra (10 min).** uv project (Python 3.12; deps: pymongo, psycopg[binary]≥3, SQLAlchemy≥2, langgraph, langgraph-checkpoint-sqlite, pydantic≥2, pydantic-settings, PyYAML, typer, rich, rapidfuzz, jinja2; extra `llm`: openai; dev group: pytest, pytest-cov, hypothesis, ruff, mypy, types-PyYAML). Multi-stage `Dockerfile` (`runtime`, `dev`), non-root. Compose: `mongo:7.0` and `postgres:16` with healthchecks, `schemashift` (volume `./workspace:/workspace`, env URIs), `tests` profile. `Makefile` targets per `TESTING.md` §6. Pre-commit (ruff, ruff-format). DoD: `make verify-fast` and `docker compose config` pass.

**A02 contracts (10 min).** Pydantic v2 models (`extra="forbid"`, stable JSON) per `ARCHITECTURE.md` §5–§9; `Settings` per §14; error taxonomy with `exit_code` per §15; `quote_ident` / `snake_case` / `safe_name`. Hand-author the seven fixtures in `tests/fixtures/shop/` for the sample schema in §10 (expected DDL/rollback text, ETL plan, frozen map with a correct `map_hash`). DoD: fixtures validate; JSON-schema snapshot test; identifiers property tests.

**A03 seed (25 min).** `random.Random(42)` generators for users/products/orders/reviews with the nesting and messy `rating` field from §10; `--inject orphan_review|bad_date|uncoercible_rating`; idempotent (`drop`+recreate collections). `mongo_app.py` and `sql_app.py` expose the same small interface (create/get/list/update/delete user, place order). DoD: seed twice → identical snapshot; counts as specified.

**A04 inspection (25 min).** Deterministic systematic sampler ordered by `_id`; type-stats walker (paths with `[]` for arrays; BSON type counts, presence rate, string length, numeric range, Decimal128 digits, distinct estimate capped at 1000, array length min/max/mean, key-set signatures for objects); redactor (≤ 3 examples, hash or truncate); `profile.py` builds `SourceProfile` and writes `reports/profile.json`. DoD: output equals `profile.json` fixture on the seed (integration) and on a mocked cursor (unit).

**A05 infer (30 min).** Implement every rule in `ARCHITECTURE.md` §5 as registered rules emitting `Decision`s; `build.py` assembles the draft `SchemaMap` with deterministic ordering; type map §6. Handle mixed types with the ambiguity flag. DoD: draft map equals `draft_map.json` fixture from the fixture profile; unit tests per rule including edge cases (empty arrays, nested arrays, all-null fields, name collisions → deterministic suffixes).

**A06 similarity (30 min).** `normalize.py`, matcher, scoring per §7 including ambiguity cap, bands, reason codes, drag list, JSON + Markdown render; weights from `Settings`. DoD: report equals `similarity.json` fixture to 4 decimals; property tests: scores in [0,1], monotonic with coverage, recomputation stable.

**A07 llm-core (25 min).** `LLMClient` protocol (`complete(task, prompt, schema) -> BaseModel | None`), providers `none` (returns `None`), `replay` (cache-only, error on miss), `openai` (optional import, timeout 30 s, 2 retries, JSON-only); cache keyed `sha256(provider|model|prompt)` stored as files; `guard.py` extracts/validates JSON into a pydantic model, rejects extra keys, redacts secrets/URIs from prompts. DoD: no network in tests; replay miss raises `LLMCacheMiss`.

**A08 freeze-gate (30 min).** Canonical JSON + hash (§8), gate policy producing a `GateReport` (required approvals list with reasons), overrides parser/applier (ordered, validated against the map), freezer (atomic write, chmod 444, `load_frozen_map` verifying hash, version bump, `approvals.jsonl` ledger, CI auto-approve rules). DoD: freeze is idempotent; tampering fails verification; `needs_review` cannot be auto-approved.

**A09 ddl-gen (25 min).** `header.py`; DDL template (tables in FK order, quoted identifiers, PK/FK/UNIQUE/indexes, `CHECK` for position ≥ 0); rollback template (reverse order `DROP TABLE IF EXISTS … CASCADE`); `ordering.py` toposort with cycle error. DoD: byte-equal to expected fixtures; applies to a fresh Postgres (integration, via A17).

**A10 etl-gen (25 min).** Declarative `etl_plan.json` (per table: source collection, iteration path, columns with `source_path` + `transform` + `on_error`, parent key propagation, `position` rule), ETL doc template, `transforms.py` (`objectid_hex`, `date_utc`, `decimal_numeric`, `int_coerce`, `json_dump`, `null_if_missing`, `identity`) with explicit `TransformError`. DoD: plan equals fixture; transform tests incl. edge values (`"5"`, `"N/A"`, `None`, naive datetimes, Decimal128 scale).

**A11 loader (25 min).** `executor.py` runs down/up scripts via psycopg (statement-by-statement, fail with statement context); `loader.py` reads Mongo (cursor sorted by `_id`), expands nested paths per plan, applies transforms, loads in `ordering` with batches, all-or-nothing transaction, bounded transient retry, `ProgressSink` callbacks, `--truncate`; `failures.py` `RowFailure` + `failures.json`. DoD: seed loads; each `--inject` flag yields a specific, actionable error.

**A12 verifier (25 min).** Counts, checksums, seeded spot-check with an independent comparator, orphan scan, `verifier.py` aggregating to `VerifyReport` (JSON). DoD: passes on clean load; each check individually fails on a targeted tamper (integration).

**A13 orm-gen (25 min).** Templates + generator per §13; `naming.py` (table → class, column → attribute, relationship names); `# REVIEW:` markers; `app.env`. DoD: generated package compiles/imports; CRUD demo passes on migrated DB; output byte-stable.

**A14 assist (25 min).** Prompts (JSON-only, schema in prompt, redacted inputs); `suggest_schema`, `merge` (validators per §4 rule 2), `explain_similarity`, `annotate_scripts`, `diagnose_failures`, `drift_summary`, `refactor_notes`, and `fallbacks.py` so every function works with provider `none`. DoD: with `none`, all functions return deterministic narratives; with `replay` fixtures, proposals are validated and tagged; invalid proposals are rejected with recorded reasons.

**A15 graph (20 min).** Nodes per `ARCHITECTURE.md` §2 (node files per `CODEBASE.md`), `StateGraph` with conditional routing, `interrupt()` at `approval_gate` and `remap_gate`, SQLite checkpointer, runner exposing `run()`, `resume()`, event stream (node start/end, progress, gate payloads) for the TUI; bounded loops. DoD: graph test with stubbed nodes covers every edge; real run works via `make demo`.

**A16 cli-tui (20 min).** Typer commands: `seed`, `inspect`, `report`, `freeze`, `generate`, `migrate`, `verify`, `rollback`, `orm`, `run`, `resume`, `status`, `demo`, global `--config`, `--ci`, `--run-id`, `--provider`. Rich: pipeline progress with D/ND badges, similarity table (overall %, per-entity, per-field with band colors, drag list), gate panel (approve / reject / edit-to-overrides), migration progress bars, final summary with exit-code mapping §15. Non-TTY degrades to plain text. DoD: CLI tests with `CliRunner`; `make demo-interactive` works.

**A17 tests (parallel W2–W4).** Integration suites per module as they merge; e2e suites per `TESTING.md` incl. failure injection, gate interrupt/resume across processes, LLM-off equivalence, determinism diff vs `examples/shop/golden/`. DoD: `make test-int` and `make test-e2e` green on a clean compose stack.

**A18 cicd (drafts W1, merges W4).** Workflows in `CICD.md`; pin actions by tag; cache uv; compose-based integration job; image build + Trivy; release on tag. DoD: workflow YAML lints (`actionlint` if available) and mirrors `make` targets.

**A19 docs (script W1, docs W5).** W1: `scripts/check_specs.py` and `scripts/gen_file_index.py`. W5: README with layer table and commands, `docs/hybrid-layers.md`, `docs/zero-downtime.md`, `docs/operations.md`, spec reconciliation, regenerate `CODEBASE.md` index. DoD: `check_specs` green; commands in README executed verbatim on a clean clone.

**A20 review (RP1–RP4).** Lenses and checklists in `CODE_REVIEW.md`; output `.agents/reviews/RPn-<lens>.md` with severities; never edits code (findings go to owners via lead).

## 6. Status and handoff protocol

- `.agents/STATUS.md` (lead-owned) table: agent · branch · state (`todo|running|done|merged|blocked`) · note.
- Agents report `DONE <branch>`; lead runs `scripts/wt_merge.sh` (see `ORCHESTRATION.md`).
- Blockers: `.agents/requests/<from>-to-<owner>.md` with the exact change wanted and why.
