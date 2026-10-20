# SchemaShift Hybrid Layer Architecture

SchemaShift implements a **deterministic core with non-deterministic assistance**. This document details the architectural boundaries, security guards, prompts, fallback mechanisms, and cost-latency trade-offs of every node in the pipeline.

---

## 1. Design Philosophy

The cardinal rule of schema migration is: **a non-deterministic model must never write directly to production database schema or data without validation and human oversight**.

Therefore, SchemaShift strictly separates operations into two classes:
1. **Deterministic Core ($D$)**: Rule-based, repeatable algorithms whose outputs are guaranteed to be byte-identical given identical inputs. This includes data profiling, relational schema synthesis, similarity scoring, checksum computation, DDL generation, streaming ETL execution, and data verification.
2. **Non-Deterministic Assist ($ND$)**: Generative LLM capabilities that advise, explain, annotate, and suggest improvements. Assist nodes enhance developer experience without ever possessing authority over the migration boundary.

---

## 2. Comprehensive Node Classification

The LangGraph migration workflow executes across 22 interconnected nodes:

| # | Node Name | Layer | Primary Responsibility | Fallback when LLM Unavailable |
|---|---|---|---|---|
| 1 | `load_config` | **Deterministic ($D$)** | Reads `schemashift.yaml`, resolves paths & env vars | N/A (raises `ConfigurationError`) |
| 2 | `sample_source` | **Deterministic ($D$)** | Deterministic systematic sampling by `_id` stride | N/A |
| 3 | `infer_candidates` | **Deterministic ($D$)** | Heuristic rules for normalization, nesting, and keys | N/A |
| 4 | `suggest_schema` | **Assist ($ND$)** | Proposes idiomatic SQL table/column naming | Returns empty proposal list (`[]`) |
| 5 | `merge_proposals` | **Deterministic ($D$)** | Validates & merges LLM proposals against rules | Ignores invalid suggestions |
| 6 | `similarity_report` | **Deterministic ($D$)** | Computes Levenshtein, type match & coverage scores | N/A (pure algorithmic scoring) |
| 7 | `explain_similarity` | **Assist ($ND$)** | Synthesizes plain-English explanations of divergent fields | Formats rule-based reason codes |
| 8 | `approval_gate` | **Deterministic ($D$)** | Evaluates bands (`matched`, `guessed`, `needs_review`) | CI auto-approves `guessed`; halts interactive |
| 9 | `freeze_map` | **Deterministic ($D$)** | Computes SHA-256 canonical hash, sets `chmod 444` | N/A |
| 10 | `generate_scripts` | **Deterministic ($D$)** | Generates DDL (`001_schema.sql`) and ETL plan | N/A |
| 11 | `annotate_scripts` | **Assist ($ND$)** | Annotates scripts with risk level and review notes | Generates default deterministic notes |
| 12 | `apply_ddl` | **Deterministic ($D$)** | Applies DDL in transaction on PostgreSQL target | N/A (rolls back on failure) |
| 13 | `migrate_data` | **Deterministic ($D$)** | Cursor-based streaming batch loader with type coercion | N/A |
| 14 | `diagnose_failures` | **Assist ($ND$)** | Analyzes migration errors to suggest remap patches | Produces empty patch; routes to remap gate |
| 15 | `remap_gate` | **Deterministic ($D$)** | Evaluates retry count and decides loop vs rollback | Enforces `max_remap_attempts=2` |
| 16 | `verify` | **Deterministic ($D$)** | Dual-DB verification (counts, checksums, spot checks) | N/A |
| 17 | `drift_summary` | **Assist ($ND$)** | Summarizes schema drift or spot-check results | Uses raw verification status counts |
| 18 | `rollback` | **Deterministic ($D$)** | Executes `001_schema.down.sql` dropping migrated tables | N/A |
| 19 | `generate_orm` | **Deterministic ($D$)** | Generates SQLAlchemy 2.0 declarative models & repos | N/A |
| 20 | `refactor_notes` | **Assist ($ND$)** | Suggests ORM refactoring considerations | Generates static review checklist |
| 21 | `orm_smoke` | **Deterministic ($D$)** | Executes `crud_demo.py` against migrated PostgreSQL | N/A |
| 22 | `cutover` | **Deterministic ($D$)** | Generates cutover checklist and switch configuration | N/A |

---

## 3. Assist Guardrails & Contract Enforcement

All assist nodes communicate via strict Pydantic v2 schemas configured with `extra="forbid"`. The prompt sent to the LLM is first redacted to scrub any sensitive customer credentials, emails, or PII.

```
+-------------------------------------------------------------------+
|                        Assist Invocation                          |
|                                                                   |
|   1. Redact Prompt  --> 2. Complete Request --> 3. Schema Validate|
|      (Mask emails,         (OpenAI-compatible      (Pydantic v2   |
|       passwords,            endpoint or cache)      extra='forbid')|
|       API keys)                                                   |
+-------------------------------------------------------------------+
```

### Replay Cache
Every prompt and response is cached locally under `workspace/llm_cache/` keyed by `sha256(provider | model | redacted_prompt)`. When running with `--provider replay` or in CI pipelines:
- Zero external network requests are made.
- Execution is completely deterministic and reproducible.
- If a new prompt is encountered without a cache entry, `LLMCacheMiss` is raised.

---

## 4. Cost, Latency, and Safety Trade-Offs

| Approach | Latency Impact | Financial Cost | Safety Risk | SchemaShift Strategy |
|---|---|---|---|---|
| **Raw End-to-End LLM Migration** | High (5–10 min) | High ($$$ per schema iteration) | Extreme (hallucinated DDL, silent data drop) | **Rejected** |
| **Pure Rule-Based Pipeline** | Very Low (< 1 s) | Zero ($0) | Moderate (inflexible names, cryptic errors) | **Used as deterministic baseline** |
| **SchemaShift Hybrid (D + ND)** | Low (~2–3 s with cache) | Minimal (< $0.001 per run) | None (validated contracts + approval gate) | **Adopted** |
