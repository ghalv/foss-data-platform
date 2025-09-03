#!/bin/bash

echo "🚀 Initializing FOSS Data Platform Services..."
echo "================================================"

# Create necessary directories
echo "📁 Creating configuration directories..."
mkdir -p config/grafana/provisioning/{datasources,dashboards}
mkdir -p config/minio
mkdir -p config/portainer
mkdir -p data/{grafana,minio,portainer,postgres,redis,trino}

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 config/minio/create_buckets.sh

# Initialize MinIO buckets
echo "🪣 Initializing MinIO buckets..."
docker-compose exec minio /scripts/create_buckets.sh

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Test service connectivity
echo "🔍 Testing service connectivity..."

# Test Grafana
if curl -s "http://localhost:3001/api/health" | grep -q "ok"; then
    echo "✅ Grafana is ready"
else
    echo "❌ Grafana is not ready yet"
fi

# Test MinIO
if curl -s "http://localhost:9002/minio/health/live" | grep -q "ok"; then
    echo "✅ MinIO is ready"
else
    echo "❌ MinIO is not ready yet"
fi

# Test Portainer
if curl -s "http://localhost:9000/api/status" | grep -q "ok"; then
    echo "✅ Portainer is ready"
else
    echo "❌ Portainer is not ready yet"
fi

echo ""
echo "🎉 Service initialization complete!"
echo ""
echo "📋 Service Access Information:"
echo "  • Grafana:     http://localhost:3001 (admin/admin123)"
echo "  • MinIO:       http://localhost:9002 (minioadmin/minioadmin123)"
echo "  • Portainer:   http://localhost:9000 (admin/admin123)"
echo "  • JupyterLab:  http://localhost:8888/lab?token=fossdata123"
echo "  • Dashboard:   http://localhost:5000"
echo ""
echo "🔧 All services are preconfigured and ready to use!"
