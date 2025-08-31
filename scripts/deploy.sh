#!/bin/bash

set -e

echo "🚀 Deploying FOSS Data Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Create necessary directories
print_status "Creating project directories..."
mkdir -p data/{iceberg,delta,logs,backups,minio,postgres,redis,prometheus,grafana}
mkdir -p config/{jupyter,trino,postgres,grafana}
mkdir -p notebooks
mkdir -p logs

# Set proper permissions
print_status "Setting directory permissions..."
chmod 755 data config notebooks logs
chmod 777 data/minio data/postgres data/redis data/prometheus data/grafana

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file..."
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
    print_warning "Please update the .env file with your desired passwords and tokens!"
fi

# Pull latest images
print_status "Pulling Docker images..."
docker-compose pull

# Start services
print_status "Starting data platform services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."
docker-compose ps

# Initialize DBT project
if [ -d "dbt" ]; then
    print_status "Initializing DBT project..."
    cd dbt
    if [ ! -f "dbt_packages.yml" ]; then
        echo "Installing DBT packages..."
        # dbt deps
    fi
    cd ..
fi

print_status "🎉 FOSS Data Platform deployment complete!"
echo ""
echo "Services are available at:"
echo "  • JupyterLab: http://localhost:8888"
echo "  • Dagster: http://localhost:3000"
echo "  • Grafana: http://localhost:3001 (admin/admin123)"
echo "  • Trino: http://localhost:8080"
echo "  • MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)"
echo "  • Prometheus: http://localhost:9090"
echo ""
echo "Next steps:"
echo "  1. Update passwords in .env file"
echo "  2. Configure your data sources in DBT"
echo "  3. Set up your first Dagster pipeline"
echo "  4. Create your first Jupyter notebook"
echo ""
echo "To view logs: docker-compose logs -f [service_name]"
echo "To stop services: docker-compose down"
