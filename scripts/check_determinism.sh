#!/usr/bin/env bash
set -euo pipefail

OUT="workspace/out"

echo "Checking determinism across consecutive runs..."
rm -rf "$OUT"
uv run python -m schemashift seed
uv run python -m schemashift run --ci --provider none
tar -C "$OUT" -cf - migrations etl orm schema_map.frozen.json | sha256sum > .det_1

rm -rf "$OUT"
uv run python -m schemashift seed
uv run python -m schemashift run --ci --provider none
tar -C "$OUT" -cf - migrations etl orm schema_map.frozen.json | sha256sum > .det_2

diff .det_1 .det_2 && echo "DETERMINISM CHECK PASSED: runs produce byte-identical artifacts."
rm -f .det_1 .det_2
