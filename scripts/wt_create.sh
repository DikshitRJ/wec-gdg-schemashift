#!/usr/bin/env bash
set -euo pipefail
NN="$1"; SLUG="$2"
BRANCH="agent/${NN}-${SLUG}"
git checkout -b "$BRANCH"
echo "Switched to branch: $BRANCH"
