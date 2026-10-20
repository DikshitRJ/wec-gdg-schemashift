#!/usr/bin/env bash
set -euo pipefail
NN="$1"; SLUG="$2"; MSG="$3"; SPEC="${4:-}"
BRANCH="agent/${NN}-${SLUG}"

git checkout main
git merge --no-ff "$BRANCH" -m "$MSG" \
  -m "Agent: A${NN}" \
  ${SPEC:+-m "Spec: $SPEC"}

git branch -d "$BRANCH" || true
echo "Merged $BRANCH into main"
