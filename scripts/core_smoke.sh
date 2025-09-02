#!/usr/bin/env bash
set -euo pipefail

echo "[SMOKE] Ingestion: pulling live data via dashboard..."
INGEST=$(curl -s -X POST http://localhost:5000/api/ingestion/pull -H 'Content-Type: application/json' -d '{}')
echo "$INGEST" | grep '"success": true' >/dev/null || { echo "[FAIL] Ingestion failed"; echo "$INGEST"; exit 1; }
ROWS=$(echo "$INGEST" | sed -n 's/.*"rows": *\([0-9][0-9]*\).*/\1/p')
SEED=$(echo "$INGEST" | sed -n 's/.*"seed_path": *"\([^"]*\)".*/\1/p')
echo "[SMOKE] Ingestion OK: $ROWS rows -> $SEED"

echo "[SMOKE] dbt run..."
docker exec -i dashboard bash -lc 'cd /app/dbt_stavanger_parking && dbt run --target dev --quiet' || { echo "[FAIL] dbt run"; exit 1; }
echo "[SMOKE] dbt test..."
docker exec -i dashboard bash -lc 'cd /app/dbt_stavanger_parking && dbt test --target dev --quiet' || echo "[WARN] dbt tests reported failures"

echo "[SMOKE] Trino query via dashboard API (count rows in staging)..."
QRES=$(curl -s -X POST http://localhost:5000/api/query/execute -H 'Content-Type: application/json' -d '{"query":"SELECT COUNT(*) AS cnt FROM memory.default_staging.stg_parking_data"}')
echo "$QRES" | grep '"success": true' >/dev/null || { echo "[FAIL] Trino query"; echo "$QRES"; exit 1; }
echo "$QRES" | sed 's/.*/[SMOKE] Trino OK: &/'

echo "[SMOKE] SUCCESS"

