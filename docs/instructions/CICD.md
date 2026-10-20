# CICD.md

## 1. Pipeline

```
push / PR ──► lint ──► unit ──► integration ──► e2e ──► image (build + scan) ──► [tag] release
               │        │          │              │
               │        │          │              └─ make demo, determinism diff, upload workspace/out
               │        │          └─ compose mongo+postgres, pytest tests/integration
               │        └─ pytest tests/unit --cov (≥85 % core)
               └─ ruff, ruff format --check, mypy, check_specs
```

Local mirror: every CI step is a `make` target, so `make verify-fast` and `make test` reproduce CI. During the 2-hour build, `make verify-fast` inside each worktree is the merge gate; the workflow file is drafted in W1 and merged in W4 (C18).

## 2. `.github/workflows/ci.yml`

```yaml
name: ci
on:
  push: { branches: [main] }
  pull_request: {}
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
env:
  MONGO_URI: mongodb://localhost:27017
  PG_URI: postgresql://schemashift:schemashift@localhost:5432/schemashift
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with: { enable-cache: true }
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy src
      - run: uv run python scripts/check_specs.py

  unit:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with: { enable-cache: true }
      - run: uv sync --frozen
      - run: uv run pytest tests/unit -q --cov=src/schemashift --cov-report=xml
      - uses: actions/upload-artifact@v4
        with: { name: coverage-unit, path: coverage.xml }

  integration:
    needs: unit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with: { enable-cache: true }
      - run: uv sync --frozen
      - run: docker compose up -d --wait mongo postgres
      - run: uv run pytest tests/integration -q
      - if: failure()
        run: docker compose logs --no-color
      - if: always()
        run: docker compose down -v

  e2e:
    needs: integration
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with: { enable-cache: true }
      - run: uv sync --frozen
      - run: docker compose build schemashift
      - run: uv run pytest tests/e2e -q
      - run: make determinism
      - if: always()
        uses: actions/upload-artifact@v4
        with: { name: workspace-out, path: workspace/out, if-no-files-found: ignore }
      - if: always()
        run: docker compose down -v

  image:
    needs: e2e
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with: { context: ., target: runtime, load: true, tags: schemashift:ci }
      - uses: aquasecurity/trivy-action@0.28.0
        with: { image-ref: schemashift:ci, severity: CRITICAL,HIGH, exit-code: '1', ignore-unfixed: true }
```

## 3. `.github/workflows/release.yml`

```yaml
name: release
on:
  push: { tags: ['v*'] }
permissions: { contents: write, packages: write }
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: '${{ github.actor }}', password: '${{ secrets.GITHUB_TOKEN }}' }
      - uses: docker/build-push-action@v6
        with:
          context: .
          target: runtime
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }},ghcr.io/${{ github.repository }}:latest
      - uses: softprops/action-gh-release@v2
        with: { generate_release_notes: true }
```

## 4. `.github/dependabot.yml`

```yaml
version: 2
updates:
  - { package-ecosystem: pip, directory: /, schedule: { interval: weekly } }
  - { package-ecosystem: github-actions, directory: /, schedule: { interval: weekly } }
  - { package-ecosystem: docker, directory: /, schedule: { interval: weekly } }
```

## 5. Policy

- `main` protected: required checks = `lint`, `unit`, `integration`, `e2e`; linear history (squash only).
- CI never needs LLM credentials: provider is `none` or `replay`.
- Secrets: none required for CI; `release` uses `GITHUB_TOKEN` only.
- Compose image tags and Python deps pinned (`uv.lock`); Dependabot proposes bumps.
- Artifacts: `workspace/out` uploaded on every e2e run so reviewers can read generated scripts, reports and ORM straight from CI.
