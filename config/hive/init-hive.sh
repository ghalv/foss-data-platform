#!/bin/bash
# Hive metastore initialization script
set -e

echo "Setting up Hive metastore..."

# Copy PostgreSQL JDBC driver to Hive lib directory
if [ -f /opt/hive/conf/postgresql-jdbc.jar ]; then
    echo "Copying PostgreSQL JDBC driver to Hive lib directory..."
    cp /opt/hive/conf/postgresql-jdbc.jar /opt/hive/lib/
    echo "JDBC driver copied successfully"
else
    echo "WARNING: PostgreSQL JDBC driver not found at /opt/hive/conf/postgresql-jdbc.jar"
fi

# Initialize schema with PostgreSQL if not already done
echo "Checking if schema needs initialization..."
if ! /opt/hive/bin/schematool -dbType postgres -info | grep -q "Schema version"; then
    echo "Initializing Hive metastore schema with PostgreSQL..."
    /opt/hive/bin/schematool -dbType postgres -initSchema
    echo "Schema initialization completed"
else
    echo "Schema already initialized"
fi

# Continue with normal Hive metastore startup
echo "Starting Hive metastore..."
exec /opt/hive/bin/hive --service metastore
