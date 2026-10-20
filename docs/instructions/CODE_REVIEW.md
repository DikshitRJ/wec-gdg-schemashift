# CODE_REVIEW.md

Agent A20 runs review as three lenses (three separate sub-instances so each stays focused). Reviewers read code and run tests; they **never edit code**. Findings go to the owning agent through the lead.

## 1. Review points

| RP | Trigger | Scope | Lenses |
|---|---|---|---|
| RP1 | After W1 merges | `inspection, infer, similarity, llm core, freeze, gen, seed` | R1, R2, R3 |
| RP2 | After W2 merges | `migrate, verify, orm, assist` | R1, R2, R3 |
| RP3 | After W3 merges | `graph, cli` + whole-repo determinism/security sweep | R1, R2 |
| RP4 | End of W4 | Full repo vs specs, README claims, CI | R3 (+ R1 spot checks) |

Output files: `.agents/reviews/RP<n>-R<k>-<lens>.md`. Each finding: `ID · severity · file:line · issue · evidence · suggested fix · owner`.

Severity: **BLOCKER** (violates spec/hybrid rule/safety, wrong results) · **MAJOR** (likely bug, missing test for a spec scenario) · **MINOR** (clarity, naming) · **NIT**. Blockers and majors must be fixed before the next wave merges; minors are batched.

## 2. Lens R1 — correctness and determinism

- Same inputs → same bytes? Look for unordered dict/set iteration, timestamps, uuids, locale, floating-point formatting, `hash()` use.
- Sampling: ordered by `_id`; stride logic correct at boundaries (count = size, size+1).
- Inference rules: threshold comparisons (`≥` vs `>`), empty/all-null/nested-array edge cases, deterministic collision suffixes.
- Scoring: weights sum to 1; scores bounded [0,1]; ambiguity cap applied; unmapped fields count as 0; overall weighting by field count.
- Gate: every non-`matched` band and every ambiguity requires approval; `needs_review` never auto-approved.
- Freeze: canonical JSON excludes timestamps/approvals; hash verification on **every** load; version bump only on content change.
- Loader: FK order correct for self/cyclic refs (must error clearly); transaction boundaries; retries only for transient errors; failures carry `_id`.
- Verifier: independent comparator really is independent of transform code; seeded selection reproducible.
- Graph: every edge reachable; loops bounded; re-run path always re-freezes before regenerating.

## 3. Lens R2 — security and safety

- **SQL:** no f-string/format SQL with values; identifiers only via `quote_ident`; DDL templates quote everything; check names from user data (collection/field names) containing quotes, spaces, unicode, SQL keywords, > 63 chars.
- **LLM boundary:** no DB handles/credentials in `assist/`/`llm/`; prompts built from redacted profile only; outputs parsed through pydantic; failed parse → fallback, not retry-with-more-data.
- **No LLM write path:** grep proves LLM output never reaches script bodies, loader, or ORM template inputs except through validated, provenance-tagged map decisions.
- **Secrets:** URIs/passwords never logged, never in reports/prompts/cache keys' stored prompt text (redaction test).
- **Files:** frozen map `chmod 444`; atomic writes; no path traversal via collection names in artifact paths.
- **Containers:** non-root user, no `latest` base tags, no secrets baked into the image, compose ports bound sensibly.
- **Dependencies:** pinned via lock; Trivy clean at CRITICAL/HIGH.
- **CI:** no secrets in logs; least-privilege `permissions`.

## 4. Lens R3 — spec, test and docs conformance

- Every source file has `Spec:` header and a row in a spec table (`check_specs.py` green).
- For each spec **Scenario**: a test exists and asserts the THEN clause. Missing → MAJOR.
- README table matches `ARCHITECTURE.md` §3 and reality (commands tested verbatim).
- CLI help text matches behavior and exit codes (§15).
- Generated artifact headers carry `map_hash`; golden files in `examples/shop/golden/` current.
- Commit history matches PLAN §5 (one conventional commit per agent, trailers present, docs last).

## 5. Review checklist for every PR/branch (lead, 2 minutes)

- [ ] Diff only touches the owner's paths
- [ ] `make verify-fast` green after rebase
- [ ] No `TODO`/`FIXME` without a handoff entry
- [ ] No new network calls outside `llm/providers.py`
- [ ] Tests added for each new public function
- [ ] Spec table rows updated

## 6. Human review hotspots (you, ≈ 35 min total)

Read these yourself; they decide correctness:

1. `contracts/schema_map.py` + fixtures (H1)
2. `infer/rules.py`, `infer/nesting.py`, `infer/references.py` (H2)
3. `similarity/scoring.py` (formula vs `ARCHITECTURE.md` §7) and `freeze/gate.py` (H2)
4. `gen/templates/ddl.sql.j2` and generated DDL on the seed (H3)
5. `migrate/loader.py` transaction + FK ordering, `verify/spotcheck.py` comparator (H3)
6. `graph/build.py` + `graph/routing.py`: confirm every re-run passes through freeze (H4)
7. The interactive gate in the terminal and the generated `orm/repositories.py` (H4)
