# ---- Stage 1: base ----
FROM python:3.15-slim AS base
RUN groupadd -r schemashift && useradd -r -g schemashift -m schemashift
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
COPY pyproject.toml ./
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev
COPY src/ src/

# ---- Stage 2: runtime ----
FROM base AS runtime
USER schemashift
VOLUME ["/workspace"]
ENV PYTHONPATH=/app/src
ENTRYPOINT ["uv", "run", "python", "-m", "schemashift"]

# ---- Stage 3: dev ----
FROM base AS dev
RUN uv sync --frozen 2>/dev/null || uv sync
COPY tests/ tests/
COPY scripts/ scripts/
COPY examples/ examples/
COPY workspace/ workspace/
USER schemashift
ENV PYTHONPATH=/app/src
ENTRYPOINT ["uv", "run"]
