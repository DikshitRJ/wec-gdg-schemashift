#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for PostgreSQL and MongoDB..."

until pg_isready -h localhost -p 5432 -U schemashift 2>/dev/null || docker compose exec -T postgres pg_isready -U schemashift 2>/dev/null; do
  echo "Waiting for postgres..."
  sleep 1
done

echo "Stack is ready!"
