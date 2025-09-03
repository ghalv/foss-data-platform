#!/bin/bash
# FOSS Data Platform - Cleanup Schema Initialization
# This script initializes the cleanup schema in PostgreSQL

set -e

echo "Initializing cleanup schema..."

# Wait for PostgreSQL to be ready
until psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready. Running cleanup schema initialization..."

# Run the cleanup schema
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /config/postgres/init_cleanup.sql

echo "Cleanup schema initialization completed successfully!"
echo "Retention policies have been set up with the following defaults:"
echo "  - Pipeline operations: 30 days retention"
echo "  - DBT logs: 7 days retention"
echo "  - Failed operations: 14 days retention"
echo "  - Completed operations: 90 days retention"
echo "  - System logs: 30 days retention"
echo "  - Temp files: 1 day retention"
