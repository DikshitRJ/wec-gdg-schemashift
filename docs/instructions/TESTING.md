# TESTING.md

## 1. Pyramid

| Level | Location | Needs | Runs in | Purpose |
|---|---|---|---|---|
| Unit | `tests/unit/` | nothing | `make test-unit`, `verify-fast` | Pure functions: inference rules, scoring, gate, canonical hash, generators, transforms, guard, fallbacks |
| Property | inside unit (hypothesis) | nothing | unit | `quote_ident`, canonical JSON, normalization, score bounds, freeze idempotence |
| Contract | `unit/test_contracts.py` | nothing | unit | Fixtures round-trip through models; JSON-schema snapshot catches contract drift |
| Integration | `tests/integration/` | mongo + postgres (compose) | `make test-int` | Module ↔ real DB: sampler, DDL apply, loader, verifier, ORM CRUD, LLM replay |
| End-to-end | `tests/e2e/` | mongo + postgres | `make test-e2e` | Whole LangGraph pipeline via the CLI |

Markers: `unit`, `integration`, `e2e`. Coverage gate: ≥ 85 % on `inspection, infer, similarity, freeze, gen, migrate, verify` (unit + integration combined in CI).

## 2. Fixtures as truth

`tests/fixtures/shop/`: `profile.json`, `draft_map.json`, `similarity.json`, `schema_map.frozen.json`, `etl_plan.json`, `ddl.expected.sql`, `rollback.expected.sql`. Unit tests of each stage consume the previous stage's fixture and compare to the next stage's fixture. If an intentional rule change alters a fixture, the change goes through a request ticket and H1/H2 review.

## 3. Integration suites (A17)

| File | Asserts |
|---|---|
| `test_sampler_mongo.py` | Seeded Mongo → `SourceProfile` equals fixture; sampling is stable across runs |
| `test_ddl_apply.py` | Generated DDL applies to fresh Postgres; down script leaves an empty schema; idempotent re-apply after down |
| `test_loader.py` | Full seed loads; counts as expected; `--inject orphan_review`, `bad_date`, `uncoercible_rating` each fail loudly with the documented hint; failed load leaves tables empty (all-or-nothing) |
| `test_verifier.py` | Clean load passes; tamper cases each fail the *specific* check: delete a row (counts), mutate a value (checksum/spot-check), insert an orphan (orphans) |
| `test_orm_crud.py` | Generated ORM imports; `crud_demo.py` exits 0; repositories create order with items atomically |
| `test_llm_replay.py` | Replay provider serves cached outputs; cache miss raises; no network used |

`integration/conftest.py` provides a connection-retry fixture and a per-test schema reset (`DROP SCHEMA public CASCADE; CREATE SCHEMA public;`) plus Mongo re-seed.

## 4. End-to-end suites (A17)

| File | Scenario |
|---|---|
| `test_happy_path.py` | `run --ci --provider replay` exits 0; all artifacts exist; `verify.json.passed == true`; `reports/similarity.json` has overall + per-entity + per-field; `orm/` imports |
| `test_gate_interrupt.py` | Without `--ci`, run stops at `approval_gate` with a payload listing `reviews.rating`; `resume` with an `edit` override re-scores, re-freezes (`map_version == 2`), completes |
| `test_remap_refreeze.py` | Seed with `uncoercible_rating`; load fails (exit 4 first attempt); `diagnose_failures` proposal approved → override → re-freeze → re-run succeeds; asserts new `map_hash` ≠ old and that no script was regenerated before re-freeze |
| `test_verify_fail_rollback.py` | Tamper hook between load and verify; verify fails (exit 3); `rollback` node drops target tables; run ends `failed` |
| `test_llm_off_equivalence.py` | Runs with `provider=none` and `provider=replay`; frozen map, `migrations/`, `etl/`, `orm/` byte-equal; only sidecars differ |
| `test_determinism.py` | Two full runs → identical `map_hash` and artifacts; compare with `examples/shop/golden/` |
| `test_resume_across_processes.py` | Start run in process A, kill at gate, `resume --run-id` in process B completes |

## 5. Determinism script

`scripts/check_determinism.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
OUT=workspace/out; GOLD=examples/shop/golden
for i in 1 2; do
  rm -rf "$OUT"; make demo >/dev/null
  tar -C "$OUT" -cf - migrations etl orm schema_map.frozen.json | sha256sum > ".det_$i"
done
diff .det_1 .det_2 && echo "determinism: runs identical"
diff -r "$OUT/migrations" "$GOLD/migrations" && diff -r "$OUT/etl" "$GOLD/etl" && diff -r "$OUT/orm" "$GOLD/orm" \
  && echo "determinism: matches golden"
rm -f .det_1 .det_2
```

## 6. Make targets

| Target | Does |
|---|---|
| `make up` | `docker compose up -d --wait mongo postgres` |
| `make down` | `docker compose down -v` |
| `make seed` | `docker compose run --rm schemashift seed` |
| `make demo` | up + seed + `schemashift run --ci --provider replay` |
| `make demo-interactive` | up + seed + `schemashift run` (real prompts) |
| `make lint` | `ruff check . && ruff format --check . && mypy src` |
| `make verify-fast` | lint + `pytest tests/unit -x -q` + `python scripts/check_specs.py` |
| `make test-unit` | unit with coverage |
| `make test-int` | up + `docker compose run --rm tests pytest tests/integration` |
| `make test-e2e` | up + `docker compose run --rm tests pytest tests/e2e` |
| `make test` | unit + int + e2e |
| `make check-specs` | `python scripts/check_specs.py` |
| `make determinism` | `bash scripts/check_determinism.sh` |
| `make clean` | remove `workspace/out`, caches |

## 7. Reviewer-facing demo script (goes in README)

```bash
git clone <repo> && cd schemashift
docker compose up -d --wait mongo postgres
docker compose run --rm schemashift seed
docker compose run --rm schemashift run --ci --provider replay    # non-interactive
docker compose run --rm schemashift run                           # interactive gate
docker compose run --rm tests pytest                              # all tests
```
