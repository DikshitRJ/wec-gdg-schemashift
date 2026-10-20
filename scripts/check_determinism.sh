#!/usr/bin/env bash
set -euo pipefail

OUT="workspace/out"
GOLD="examples/shop/golden"

echo "Checking determinism across consecutive runs..."
rm -rf "$OUT"
uv run python -m schemashift seed
uv run python -m schemashift run --ci --provider none
find "$OUT" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
tar -C "$OUT" --sort=name --format=ustar --mtime="2026-01-01 00:00:00Z" --owner=0 --group=0 --numeric-owner -cf - migrations etl orm schema_map.frozen.json | sha256sum > .det_1

rm -rf "$OUT"
uv run python -m schemashift seed
uv run python -m schemashift run --ci --provider none
find "$OUT" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
tar -C "$OUT" --sort=name --format=ustar --mtime="2026-01-01 00:00:00Z" --owner=0 --group=0 --numeric-owner -cf - migrations etl orm schema_map.frozen.json | sha256sum > .det_2

diff .det_1 .det_2 && echo "DETERMINISM CHECK PASSED: runs produce byte-identical artifacts."

if [ -d "$GOLD" ]; then
    diff -r "$OUT/migrations" "$GOLD/migrations" && \
    diff -r "$OUT/etl" "$GOLD/etl" && \
    diff -r -x "__pycache__" "$OUT/orm" "$GOLD/orm" && \
    diff "$OUT/schema_map.frozen.json" "$GOLD/schema_map.frozen.json" && \
    echo "DETERMINISM CHECK PASSED: matches golden copies."
fi

rm -f .det_1 .det_2
