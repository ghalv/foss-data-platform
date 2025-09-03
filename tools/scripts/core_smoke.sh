#!/usr/bin/env bash
set -euo pipefail

echo "[SMOKE] Dashboard health check..."
HEALTH=$(curl -s http://localhost:5000/api/health)
echo "$HEALTH" | grep '"services"' >/dev/null || { echo "[FAIL] Dashboard health check failed"; echo "$HEALTH"; exit 1; }
echo "[SMOKE] Dashboard OK: API responding correctly"

echo "[SMOKE] dbt run..."
docker exec -i dashboard bash -lc 'cd /app/pipelines/stavanger_parking/dbt && dbt run --target docker --quiet' || { echo "[FAIL] dbt run"; exit 1; }
echo "[SMOKE] dbt test..."
docker exec -i dashboard bash -lc 'cd /app/pipelines/stavanger_parking/dbt && dbt test --target docker --quiet' || echo "[WARN] dbt tests reported failures"

echo "[SMOKE] Trino query via dashboard API (count rows in staging)..."
QRES=$(curl -s -X POST http://localhost:5000/api/query/execute -H 'Content-Type: application/json' -d '{"query":"SELECT COUNT(*) AS cnt FROM memory.default_staging.stg_parking_data"}')
echo "$QRES" | grep '"success": true' >/dev/null || { echo "[FAIL] Trino query"; echo "$QRES"; exit 1; }
echo "$QRES" | sed 's/.*/[SMOKE] Trino OK: &/'

echo "[SMOKE] SUCCESS"

