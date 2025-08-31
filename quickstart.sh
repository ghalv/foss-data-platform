#!/bin/bash

echo "🚀 FOSS Data Platform - Quick Start"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Create necessary directories
echo "📁 Setting up project structure..."
mkdir -p data/{iceberg,delta,logs,backups,minio,postgres,redis,prometheus,grafana}
mkdir -p config/{jupyter,trino,postgres,grafana}
mkdir -p notebooks logs

# Set permissions
chmod 755 data config notebooks logs
chmod 777 data/minio data/postgres data/redis data/prometheus data/grafana

echo "✅ Project structure created"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating environment file..."
    cat > .env << EOF
# FOSS Data Platform Environment Variables
COMPOSE_PROJECT_NAME=foss-dataplatform

# JupyterLab
JUPYTER_TOKEN=your-secret-token-here

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# PostgreSQL
POSTGRES_DB=dagster
POSTGRES_USER=dagster
POSTGRES_PASSWORD=dagster123

# Grafana
GRAFANA_ADMIN_PASSWORD=admin123

# Trino
TRINO_USER=admin
TRINO_PASSWORD=admin
EOF
    echo "⚠️  Please update the .env file with your desired passwords!"
    echo ""
fi

# Start services
echo "🚀 Starting data platform services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "🎉 FOSS Data Platform is starting up!"
echo ""
echo "Services will be available at:"
echo "  • 🚀 Platform Dashboard: http://localhost:5000 (Main entry point)"
echo "  • JupyterLab: http://localhost:8888"
echo "  • Dagster: http://localhost:3000"
echo "  • Grafana: http://localhost:3001 (admin/admin123)"
echo "  • Trino: http://localhost:8080"
echo "  • MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)"
echo "  • Prometheus: http://localhost:9090"
echo ""
echo "Next steps:"
echo "  1. Wait a few minutes for all services to fully start"
echo "  2. Update passwords in the .env file"
echo "  3. Run: make test (to test the platform)"
echo "  4. Visit the service URLs above"
echo ""
echo "Useful commands:"
echo "  make status    - Check service status"
echo "  make logs      - View service logs"
echo "  make stop      - Stop all services"
echo "  make start     - Start all services"
echo "  make restart   - Restart all services"
echo ""
echo "For full setup instructions, see SETUP.md"
