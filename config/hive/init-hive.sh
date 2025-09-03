#!/bin/bash
# Hive metastore initialization script
set -e

echo "Setting up Hive metastore..."

# Copy PostgreSQL JDBC driver to Hive lib directory
echo "Looking for PostgreSQL JDBC driver..."
if [ -f /opt/hive/conf/postgresql-jdbc.jar ]; then
    echo "Found JDBC driver at /opt/hive/conf/postgresql-jdbc.jar"
    cp /opt/hive/conf/postgresql-jdbc.jar /opt/hive/lib/
    echo "JDBC driver copied successfully"
elif [ -f /opt/hive/lib/postgresql-jdbc.jar ]; then
    echo "JDBC driver already exists in lib directory"
else
    echo "WARNING: PostgreSQL JDBC driver not found. Downloading..."
    wget -O /opt/hive/lib/postgresql-jdbc.jar https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar
    echo "JDBC driver downloaded and copied"
fi

# Initialize schema with PostgreSQL if not already done
echo "Checking if schema needs initialization..."
echo "Running schematool info..."
/opt/hive/bin/schematool -dbType postgres -info
echo "Info command completed"

echo "Initializing Hive metastore schema with PostgreSQL..."
/opt/hive/bin/schematool -dbType postgres -initSchema -verbose
echo "Schema initialization completed"

# Continue with normal Hive metastore startup
echo "Starting Hive metastore..."
exec /opt/hive/bin/hive --service metastore
