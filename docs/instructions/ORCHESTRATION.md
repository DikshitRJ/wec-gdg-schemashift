# ORCHESTRATION.md — worktree and merge runbook (lead A00)

## 1. Layout

```
~/work/
├── schemashift/            # main checkout (lead only; only place that merges)
└── ss-wt/
    ├── 01-scaffold/   ├── 02-contracts/   ├── 03-seed/        ├── 04-inspection/
    ├── 05-infer/      ├── 06-similarity/  ├── 07-llm-core/    ├── 08-freeze-gate/
    ├── 09-ddl-gen/    ├── 10-etl-gen/     ├── 11-loader/      ├── 12-verifier/
    ├── 13-orm-gen/    ├── 14-assist/      ├── 15-graph/       ├── 16-cli-tui/
    ├── 17-tests/      ├── 18-cicd/        ├── 19-docs/        └── 20-review/
```

One worktree = one branch `agent/<NN>-<slug>` = one subagent. Agents never touch the main checkout.

## 2. One-time bootstrap (lead)

```bash
mkdir -p ~/work && cd ~/work
git init schemashift && cd schemashift
git checkout -b main
# copy PLAN.md ARCHITECTURE.md CODEBASE.md AGENTS.md ORCHESTRATION.md TESTING.md CICD.md CODE_REVIEW.md README.md openspec/ into repo
mkdir -p scripts .agents/{handoff,requests,reviews}
# add scripts/wt_create.sh and scripts/wt_merge.sh from section 3, then:
chmod +x scripts/*.sh
git add -A && git commit -m "docs: add plan, architecture, agent roster and openspec baseline" -m "Agent: A00"
```

## 3. Scripts

`scripts/wt_create.sh <NN> <slug>`
```bash
#!/usr/bin/env bash
set -euo pipefail
NN="$1"; SLUG="$2"
ROOT="$(git rev-parse --show-toplevel)"
WT="$ROOT/../ss-wt/${NN}-${SLUG}"
git -C "$ROOT" worktree add -b "agent/${NN}-${SLUG}" "$WT" main
echo "worktree ready: $WT"
```

`scripts/wt_merge.sh <NN> <slug> "<conventional message>" [Spec-capability]`
```bash
#!/usr/bin/env bash
set -euo pipefail
NN="$1"; SLUG="$2"; MSG="$3"; SPEC="${4:-}"
ROOT="$(git rev-parse --show-toplevel)"
WT="$ROOT/../ss-wt/${NN}-${SLUG}"
BR="agent/${NN}-${SLUG}"
# 1. rebase the agent branch on the latest main and gate on fast checks
( cd "$WT" && git rebase main && make verify-fast )
# 2. squash-merge into main as ONE conventional commit
cd "$ROOT"
git checkout main
git merge --squash "$BR"
if [ -n "$SPEC" ]; then
  git commit -m "$MSG" -m "Agent: A${NN}" -m "Spec: ${SPEC}"
else
  git commit -m "$MSG" -m "Agent: A${NN}"
fi
# 3. clean up
git worktree remove "$WT"
git branch -D "$BR"
```

Squash merges leave the branch unmerged by ancestry, hence `-D`. If the rebase conflicts, stop: the agent resolves it in its worktree (conflicts mean an ownership violation; see §6).

## 4. Wave procedure

For each wave:
1. `for each agent in wave: scripts/wt_create.sh NN slug` (all from the same `main` commit).
2. Dispatch each subagent with the preamble + brief from `AGENTS.md` §4–§5, pointing it at its worktree path. Dispatch the whole wave at once.
3. Update `.agents/STATUS.md` as agents report `DONE`.
4. **Merge in dependency order**, one at a time (below). After each merge, the *remaining* branches of the wave need no action: ownership is disjoint, so rebases are trivial.
5. Run `make test` on `main` at the end of the wave. Red → dispatch fix to the owner before the next wave.

### Merge order

| Wave | Order | Commit message (as in PLAN §5) |
|---|---|---|
| W0 | A01, A02 | C01, C02 |
| W1 | A03, A04, A05, A06, A07, A08, A09, A10 | C03 … C10 |
| W2 | A11, A12, A13, A14 (A17 integration tests ride along in C17) | C11 … C14 |
| W3 | A15, A16 | C15, C16 |
| W4 | A17, A18, then review fixes | C17, C18, C19.. |
| W5 | A19 | C20 |

## 5. Review points (see `CODE_REVIEW.md`)

| RP | After | Reviewers run on | Gate |
|---|---|---|---|
| RP1 | W1 merges | A04–A10 diffs | blockers fixed before W2 merges |
| RP2 | W2 merges | A11–A14 diffs | blockers fixed before W3 merges |
| RP3 | W3 merges | A15–A16 + whole-repo determinism/security | blockers fixed before W4 tests finalize |
| RP4 | W4 end | full repo vs specs and README | blockers fixed before docs commit |

## 6. Conflict avoidance

- Ownership table in `AGENTS.md` §3 is exclusive. `check_ownership.sh` (optional, 10 lines) can fail a branch whose diff touches paths outside its owner list:
  ```bash
  git diff --name-only main...HEAD | grep -Ev "$(cat .agents/owners/$AGENT.regex)" && exit 1 || true
  ```
- Shared files (`pyproject.toml`, compose, Makefile) change only through A01 via a request ticket.
- Spec files: each capability spec has one owner (the agent who owns its code), so spec edits never collide. `scriptgen` has two owners (A09, A10) but edits disjoint sections (DDL vs ETL tables).
- `migrate/` is split across A09 (`ordering.py`), A10 (`transforms.py`), A11 (rest). `migrate/__init__.py` belongs to A11 and is merged after A09/A10, so it can re-export all three.

## 7. `.agents/STATUS.md` template

```markdown
| Agent | Branch | State | Note |
|---|---|---|---|
| A01 | agent/01-scaffold | todo | |
| A02 | agent/02-contracts | todo | |
| … | … | … | … |
```

## 8. Handoff note template (`.agents/handoff/<NN>-<slug>.md`)

```markdown
# Handoff A<NN> <slug>
## What exists
## How to run / test
## Spec rows added or changed
## Known gaps / cuts taken
## Requests to other owners
```

## 9. Lead checklist per merge

1. Branch reports DONE; handoff note present.
2. `wt_merge.sh` passes (`make verify-fast` green after rebase).
3. Skim the diff for ownership violations and for any LLM/DB boundary breach.
4. Update `STATUS.md`; start dependents if unblocked.
5. At wave end: `make test`, then the human gate (H1–H5).
