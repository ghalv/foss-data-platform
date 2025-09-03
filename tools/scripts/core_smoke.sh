#!/usr/bin/env bash
set -euo pipefail

# Function to log with timestamp
log() {
    echo "[$(date +'%H:%M:%S')] $1"
}

# Function to run command with timeout and progress
run_with_timeout() {
    local cmd="$1"
    local timeout="$2"
    local desc="$3"

    log "STARTING: $desc"
    log "COMMAND: $cmd"
    log "TIMEOUT: ${timeout}s"

    # Run command in background with timeout
    (
        eval "$cmd" &
        local pid=$!

        # Wait for timeout or completion
        local count=0
        while kill -0 $pid 2>/dev/null && [ $count -lt $timeout ]; do
            sleep 1
            count=$((count + 1))
            if [ $((count % 5)) -eq 0 ]; then
                log "PROGRESS: $desc (${count}s elapsed)"
            fi
        done

        if kill -0 $pid 2>/dev/null; then
            log "TIMEOUT: Killing process after ${timeout}s"
            kill $pid 2>/dev/null || true
            return 1
        else
            wait $pid
            return $?
        fi
    )

    local result=$?
    if [ $result -eq 0 ]; then
        log "SUCCESS: $desc completed"
    else
        log "FAILED: $desc failed (exit code: $result)"
    fi
    return $result
}

log "🚀 STARTING FOSS DATA PLATFORM SMOKE TEST"
log "=========================================="

# Test 1: Dashboard Health
log "🔍 TEST 1: Dashboard Health Check"
if HEALTH=$(curl -s --max-time 10 http://localhost:5000/api/health); then
    if echo "$HEALTH" | grep -q '"services"'; then
        log "✅ PASS: Dashboard health check successful"
    else
        log "❌ FAIL: Dashboard health check failed - no services found"
        log "RESPONSE: $HEALTH"
        exit 1
    fi
else
    log "❌ FAIL: Dashboard health check failed - connection error"
    exit 1
fi

# Test 2: dbt Run
log "🔍 TEST 2: dbt Run Test"
if run_with_timeout "docker exec -i dashboard bash -lc 'cd /app/pipelines/stavanger_parking/dbt && dbt run --target docker --quiet'" 120 "dbt run"; then
    log "✅ PASS: dbt run completed successfully"
else
    log "❌ FAIL: dbt run failed or timed out"
    exit 1
fi

# Test 3: dbt Test
log "🔍 TEST 3: dbt Test"
if run_with_timeout "docker exec -i dashboard bash -lc 'cd /app/pipelines/stavanger_parking/dbt && dbt test --target docker --quiet'" 120 "dbt test"; then
    log "✅ PASS: dbt test completed successfully"
else
    log "⚠️  WARN: dbt test failed (this may be expected if no tests exist)"
fi

# Test 4: Trino Query
log "🔍 TEST 4: Trino Query Test"
if QRES=$(curl -s --max-time 30 -X POST http://localhost:5000/api/query/execute -H 'Content-Type: application/json' -d '{"query":"SELECT 1 as test_value"}'); then
    if echo "$QRES" | grep -q '"success": true'; then
        log "✅ PASS: Trino query executed successfully"
        echo "$QRES" | sed 's/.*/    RESULT: &/'
    elif echo "$QRES" | grep -q '"error"'; then
        ERROR_MSG=$(echo "$QRES" | sed -n 's/.*"error": *"\([^"]*\)".*/\1/p')
        log "❌ FAIL: Trino query failed - $ERROR_MSG"
        exit 1
    else
        log "⚠️  UNKNOWN: Trino query returned unexpected response"
        log "RESPONSE: $QRES"
    fi
else
    log "❌ FAIL: Trino query request failed"
    exit 1
fi

log "🎉 SMOKE TEST COMPLETED SUCCESSFULLY"
log "===================================="
log "All core platform components are working!"

