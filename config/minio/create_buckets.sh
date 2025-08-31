#!/bin/bash

# Create MinIO buckets for FOSS Data Platform
echo "Creating MinIO buckets..."

# Configure MinIO client with admin credentials
mc alias set minio http://localhost:9000 admin admin123

# Create main data buckets
mc mb minio/raw-data
mc mb minio/processed-data
mc mb minio/analytics
mc mb minio/backups

# Set bucket policies
mc policy set download minio/raw-data
mc policy set download minio/processed-data
mc policy set download minio/analytics
mc policy set download minio/backups

# Create a user for dbt and applications
mc admin user add minio dbt-user dbt-secret-key
mc admin policy set minio readwrite dbt-user

echo "MinIO buckets and users configured successfully!"
