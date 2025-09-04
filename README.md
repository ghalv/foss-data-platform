# FOSS Data Platform

A modern, lean, and high-performing open-source data platform built with best-in-class FOSS tools.

## Architecture Overview

```
🎯 PIPELINE-CENTRIC ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  PIPELINES LAYER                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ Sales Pipeline  │  │Marketing Pipeline│  │  User Pipeline │  │  ...Pipeline   │    │
│  │   ├─ DBT        │  │   ├─ DBT        │  │   ├─ DBT        │  │   ├─ DBT        │    │
│  │   ├─ Dagster    │  │   ├─ Dagster    │  │   ├─ Dagster    │  │   ├─ Dagster    │    │
│  │   ├─ Notebooks  │  │   ├─ Notebooks  │  │   ├─ Notebooks  │  │   ├─ Notebooks  │    │
│  │   └─ Data       │  │   └─ Data       │  │   └─ Data       │  │   └─ Data       │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               PLATFORM LAYER                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   JupyterLab   │  │     Dagster     │  │      DBT        │  │   Apache Trino  │    │
│  │  (Interactive) │  │  (Orchestration)│  │(Transformation) │  │ (Query Engine)  │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                        │
│  │    Grafana     │  │   Prometheus    │  │    Portainer    │                        │
│  │  (Visualization)│  │  (Monitoring)  │  │(Container Mgmt) │                        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               STORAGE LAYER                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ PostgreSQL DB  │  │     MinIO       │  │   Iceberg       │  │     Kafka       │    │
│  │  (Metadata)    │  │   (Object Store)│  │ (Data Lake)     │  │  (Streaming)    │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Benefits

**🎯 Pipeline Autonomy:**
- Each pipeline operates independently
- Isolated data, code, and configurations
- Team-specific ownership and deployment

**🔄 Platform Services:**
- Shared infrastructure for all pipelines
- Centralized monitoring and orchestration
- Consistent tooling and governance

**📊 Scalable Storage:**
- Multi-format data lake support
- Streaming and batch processing
- Metadata-driven data management

## Technology Stack

### Core Data Platform
- **Interactive Development**: JupyterLab (Interactive notebooks & analysis)
- **Pipeline Orchestration**: Dagster (Job scheduling & dependency management)
- **Data Transformation**: DBT (SQL-based data modeling & testing)
- **Query Engine**: Apache Trino (Distributed SQL queries)
- **Storage Layer**: Apache Iceberg / Delta Lake (Data lake formats)

### Infrastructure & DevOps
- **Container Orchestration**: Docker & Docker Compose
- **Infrastructure as Code**: Terraform
- **Container Management**: Portainer
- **Monitoring**: Prometheus + Grafana
- **Version Control**: Git
- **Secrets Management**: SOPS + Age

### Development Tools
- **CLI Tools**: Custom pipeline creation scripts
- **Testing Framework**: Python-based QA test suite
- **Code Quality**: Automated formatting & linting
- **Documentation**: Markdown-based docs with templates
- **Cleanup System**: Automated data lifecycle management

## Quick Start

### Prerequisites
- Debian 12 VPS
- Docker and Docker Compose
- Terraform
- SOPS + Age for secrets management

### Setup Infrastructure
```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

### Deploy Platform
```bash
docker-compose up -d
```

### Create Your First Pipeline
```bash
# Create a new pipeline in seconds
./tools/cli/create-pipeline.sh my_first_pipeline "My First Data Pipeline"

# This creates a complete pipeline structure with:
# - DBT models, tests, and seeds
# - Dagster orchestration code
# - Jupyter notebooks for analysis
# - Proper data directory structure
# - Documentation templates
```

### Access Services
- **Platform Dashboard**: http://your-vps:5000 (Main entry point)
- **Pipeline Management**: http://your-vps:5000/pipeline-management
- **Health Check**: http://your-vps:5000/health (Service status)
- **System Metrics**: http://your-vps:5000/metrics (Performance monitoring)
- **JupyterLab**: http://your-vps:8888 (Interactive development)
- **Dagster**: http://your-vps:3000 (Pipeline orchestration)
- **Grafana**: http://your-vps:3001 (Monitoring & visualization)
- **Trino**: http://your-vps:8080 (SQL query engine)
- **Portainer**: http://your-vps:9000 (Container management)

## Project Structure

```
├── pipelines/                    # 🎯 Pipeline Projects (Scalable)
│   ├── stavanger_parking/        # Example pipeline
│   │   ├── dbt/                  # DBT models, tests, seeds
│   │   ├── orchestration/        # Dagster assets & jobs
│   │   ├── notebooks/            # Analysis & exploration
│   │   ├── scripts/              # Pipeline utilities
│   │   ├── config/               # Pipeline configuration
│   │   ├── docs/                 # Pipeline documentation
│   │   └── data/                 # Pipeline data (raw/staging/processed)
│   │       ├── raw/              # Raw ingested data
│   │       ├── staging/          # Cleaned data
│   │       ├── processed/        # Final datasets
│   │       └── temp/             # Temporary files
│   ├── shared/                   # Shared components across pipelines
│   │   ├── macros/               # Reusable DBT macros
│   │   ├── tests/                # Shared test utilities
│   │   ├── schemas/              # Common data schemas
│   │   └── utilities/            # Shared utilities
│   └── _templates/               # Pipeline creation templates
│       └── pipeline_template/    # Complete pipeline template
│
├── platform/                     # 🏗️ Platform Infrastructure
│   ├── orchestration/            # Dagster workspace & jobs
│   ├── monitoring/               # Monitoring configurations
│   ├── security/                 # Security policies
│   └── governance/               # Data governance rules
│
├── data/                         # 💾 Data Management
│   ├── services/                 # Service-specific data
│   └── pipelines/                # Pipeline-specific data
│
├── tools/                        # 🔧 Development Tools
│   ├── cli/                      # Command-line utilities
│   │   └── create-pipeline.sh    # Pipeline creation tool
│   ├── scripts/                  # Utility scripts
│   │   ├── core_smoke.sh         # Smoke tests
│   │   ├── cleanup_operations.py # Data cleanup
│   │   └── test_cleanup_system.py # Cleanup tests
│   ├── templates/                # Code templates
│   └── testing/                  # Testing framework
│
├── infrastructure/               # ☁️ Infrastructure as Code
├── dashboard/                    # 🌐 Web Dashboard
└── docs/                         # 📚 Documentation
```

### Key Design Principles

**🎯 Pipeline-Centric Organization:**
- Each pipeline is self-contained with all dependencies
- Clear separation between pipeline logic and platform infrastructure
- Easy to add new pipelines without affecting existing ones

**🔧 Developer Experience:**
- Template-based pipeline creation (seconds, not hours)
- Shared components reduce duplication
- Clear boundaries for team collaboration

**📈 Scalability:**
- Supports 50+ pipelines without root-level clutter
- Independent deployment and scaling per pipeline
- Consistent structure across all pipelines

## Pipeline Development

### Creating New Pipelines
```bash
# Fast pipeline creation
./tools/cli/create-pipeline.sh sales_analytics "Sales Analytics Pipeline"
./tools/cli/create-pipeline.sh customer_insights "Customer Insights Pipeline"
./tools/cli/create-pipeline.sh inventory_forecast "Inventory Forecasting Pipeline"
```

### Pipeline Structure
Each pipeline follows a consistent structure:
```
pipelines/your_pipeline/
├── dbt/              # Data transformation models
├── orchestration/    # Dagster jobs and assets
├── notebooks/        # Analysis and exploration
├── scripts/          # Pipeline utilities
├── config/           # Pipeline configuration
├── docs/             # Documentation
└── data/             # Data lifecycle management
    ├── raw/          # Raw ingested data
    ├── staging/      # Cleaned and validated data
    ├── processed/    # Final transformed datasets
    └── temp/         # Temporary files (auto-cleaned)
```

### Testing & Validation
```bash
# Run comprehensive QA tests
python scripts/qa_test_suite.py

# Run smoke tests
./tools/scripts/core_smoke.sh

# Test specific pipeline
python scripts/test_formatting.py
```

### Data Cleanup & Maintenance
```bash
# Manual cleanup
python tools/scripts/cleanup_operations.py --dry-run

# Automated cleanup (runs daily via cron)
# Configured in docker-compose.yml

## Documentation

All project documentation is organized in the `docs/` directory:

- **ARCHITECTURE.md** - System architecture and design
- **PIPELINE_MANAGEMENT_GUIDE.md** - Pipeline development guide
- **PLATFORM_QUALITY_ASSURANCE.md** - Testing and QA procedures
- **CLEANUP_SYSTEM_README.md** - Data cleanup system documentation
- **SECURITY_AUDIT_REPORT.md** - Security assessment results
- **MIGRATION_GUIDE.md** - Migration from legacy structure

## Scripts & Tools

All utility scripts are organized in the `scripts/` directory:

- **qa_test_suite.py** - Comprehensive QA test suite
- **service_validation_suite.py** - Service validation tests
- **test_formatting.py** - Code formatting validation
- **quickstart.sh** - Platform quickstart script
- **restructure_repo.sh** - Repository restructuring utility
```

## Migration Guide

### From Legacy Structure
This platform has been restructured for better scalability:

**Old Structure → New Structure:**
```
dbt_stavanger_parking/     → pipelines/stavanger_parking/dbt/
dagster/                   → platform/orchestration/
scripts/                   → tools/scripts/
CLEANUP_SYSTEM_README.md   → docs/CLEANUP_SYSTEM_README.md
migration_plan.md          → docs/migration_plan.md
```

**Migration Benefits:**
- ✅ **Scalable**: Support for 50+ pipelines without root clutter
- ✅ **Organized**: Clear separation of concerns
- ✅ **Automated**: Template-based pipeline creation
- ✅ **Maintainable**: Consistent structure across all pipelines

**Repository Organization:**
- 📁 **Root Directory**: Clean with only essential files
- 📁 **docs/**: All documentation (except master README.md)
- 📁 **scripts/**: All utility scripts and test suites
- 📁 **pipelines/**: Pipeline projects with self-contained structure
- 📁 **platform/**: Platform infrastructure and services
- 📁 **tools/**: Development tools and CLI utilities

**Backward Compatibility:**
- All existing functionality preserved
- API endpoints remain the same
- Docker services continue to work
- No breaking changes for users

## Development

This platform is designed to be:
- **FOSS**: All components are open-source
- **Modern**: Uses current best practices and tools
- **Lean**: Minimal resource footprint
- **High-performing**: Optimized for speed and efficiency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details
