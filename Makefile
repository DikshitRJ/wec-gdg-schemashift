.PHONY: up down seed demo demo-interactive lint verify-fast test-unit test-int test-e2e test check-specs determinism clean

COMPOSE := docker compose
RUN := $(COMPOSE) run --rm schemashift
TEST := $(COMPOSE) run --rm --profile test tests

up:
	$(COMPOSE) up -d --wait mongo postgres

down:
	$(COMPOSE) down -v

seed: up
	$(RUN) seed

demo: up seed
	$(RUN) run --ci --provider replay

demo-interactive: up seed
	$(RUN) run

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src

verify-fast: lint
	uv run pytest tests/unit -x -q
	uv run python scripts/check_specs.py

test-unit:
	uv run pytest tests/unit -q --cov=src/schemashift --cov-report=xml

test-int: up
	uv run pytest tests/integration -m integration -q

test-e2e: up
	uv run pytest tests/e2e -m e2e -q

test: test-unit test-int test-e2e

check-specs:
	uv run python scripts/check_specs.py

determinism:
	bash scripts/check_determinism.sh

clean:
	rm -rf workspace/out .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
