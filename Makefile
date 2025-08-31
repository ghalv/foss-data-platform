.PHONY: help deploy start stop restart logs status clean setup test

# Default target
help:
	@echo "FOSS Data Platform - Available Commands:"
	@echo ""
	@echo "  deploy    - Deploy the entire platform"
	@echo "  start     - Start all services"
	@echo "  stop      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - Show logs for all services"
	@echo "  status    - Show status of all services"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  setup     - Initial setup and configuration"
	@echo "  test      - Run platform tests"
	@echo "  update    - Update all services"
	@echo "  backup    - Backup configurations and data"
	@echo ""

# Deploy the platform
deploy:
	@echo "🚀 Deploying FOSS Data Platform..."
	@./scripts/deploy.sh

# Start all services
start:
	@echo "▶️  Starting data platform services..."
	@docker-compose up -d
	@echo "✅ Services started successfully"

# Stop all services
stop:
	@echo "⏹️  Stopping data platform services..."
	@docker-compose down
	@echo "✅ Services stopped successfully"

# Restart all services
restart: stop start

# Show logs for all services
logs:
	@echo "📋 Showing logs for all services..."
	@docker-compose logs -f

# Show status of all services
status:
	@echo "📊 Platform service status:"
	@docker-compose ps

# Clean up containers and volumes
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	@docker-compose down -v
	@docker system prune -f
	@echo "✅ Cleanup completed"

# Initial setup
setup:
	@echo "🔧 Setting up data platform..."
	@mkdir -p data/{iceberg,delta,logs,backups,minio,postgres,redis,prometheus,grafana}
	@mkdir -p config/{jupyter,trino,postgres,grafana}
	@mkdir -p notebooks logs
	@chmod +x scripts/deploy.sh
	@echo "✅ Setup completed"

# Run platform tests
test:
	@echo "🧪 Running platform tests..."
	@cd notebooks && python platform_demo.py
	@echo "✅ Tests completed"

# Update all services
update:
	@echo "🔄 Updating all services..."
	@docker-compose pull
	@docker-compose up -d
	@echo "✅ Update completed"

# Backup configurations and data
backup:
	@echo "💾 Creating backup..."
	@tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='data/*' \
		--exclude='*.tfstate*' \
		--exclude='.terraform' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		.
	@echo "✅ Backup created successfully"

# Install dependencies
install:
	@echo "📦 Installing Python dependencies..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed"

# Initialize DBT
dbt-init:
	@echo "🔧 Initializing DBT project..."
	@cd dbt && dbt deps
	@echo "✅ DBT initialized"

# Run DBT
dbt-run:
	@echo "▶️  Running DBT models..."
	@cd dbt && dbt run
	@echo "✅ DBT run completed"

# Test DBT
dbt-test:
	@echo "🧪 Testing DBT models..."
	@cd dbt && dbt test
	@echo "✅ DBT tests completed"

# Show platform info
info:
	@echo "ℹ️  Platform Information:"
	@echo "  • JupyterLab: http://localhost:8888"
	@echo "  • Dagster: http://localhost:3000"
	@echo "  • Grafana: http://localhost:3001"
	@echo "  • Trino: http://localhost:8080"
	@echo "  • 🚀 Platform Dashboard: http://localhost:5000"
	@echo "  • MinIO Console: http://localhost:9001"
	@echo "  • Prometheus: http://localhost:9090"
