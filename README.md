# FOSS Data Platform

A modern, open-source data platform built with best-in-class FOSS tools for reliable, scalable data engineering.

## Current Architecture Overview

```
🎯 LAKEHOUSE ARCHITECTURE - CURRENT STATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 WORKING PIPELINE                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                        STAVANGER PARKING PIPELINE                               │    │
│  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │    │
│  │   │   Data Source   │  │   dbt Pipeline  │  │  Iceberg Tables  │  │  Dashboard  │ │    │
│  │   │   (REST API)    │  │   (Transform)   │  │   (Storage)      │  │   (Web UI)  │ │    │
│  │   │                 │  │   ├─ Bronze     │  │   ├─ ACID        │  │   ├─ Mgmt   │ │    │
│  │   │                 │  │   ├─ Silver     │  │   ├─ Time Travel │  │   ├─ Browse │ │    │
│  │   │                 │  │   └─ Gold       │  │   └─ Schema Evol │  │   └─ Health │ │    │
│  │   └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PLATFORM INFRASTRUCTURE                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │  Flask Web App │  │   Docker Compose │  │   Python Scripts │  │   Shell Scripts │    │
│  │   (Dashboard)   │  │  (Orchestration) │  │   (Automation)   │  │   (Management)  │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Trino         │  │     MinIO       │  │    Dagster      │  │    Portainer    │    │
│  │  (Configured)   │  │  (Configured)   │  │  (Configured)   │  │  (Configured)   │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Current Status

**🟢 ACTIVE COMPONENTS:**
- **dbt Pipeline**: SQL-based data transformations with medallion architecture
- **Apache Iceberg**: Table format for lakehouse with ACID transactions
- **Flask Dashboard**: Web interface for pipeline management and data browsing
- **Docker Compose**: Container orchestration for all services

**🟡 CONFIGURED BUT NOT INTEGRATED:**
- **Trino**: Distributed SQL query engine (ready for integration)
- **MinIO**: S3-compatible object storage (ready for integration)
- **Dagster**: Pipeline orchestration (configured but dbt handles current orchestration)

**🔴 FUTURE ENHANCEMENTS:**
- Multi-pipeline support
- Advanced analytics with Trino
- Object storage integration with MinIO
- Enhanced monitoring and alerting

## Technology Stack

### 🟢 ACTIVE COMPONENTS (Currently Working)
- **Data Transformation**: dbt (SQL-based transformations with medallion architecture)
- **Storage Layer**: Apache Iceberg (ACID transactions, time travel, schema evolution)
- **Web Dashboard**: Flask + Bootstrap (Pipeline management, data browsing, health monitoring)
- **Container Orchestration**: Docker Compose (Service orchestration and deployment)

### 🟡 CONFIGURED COMPONENTS (Ready for Integration)
- **Query Engine**: Trino (Distributed SQL queries - configured in docker-compose.yml)
- **Object Storage**: MinIO (S3-compatible storage - configured in docker-compose.yml)
- **Pipeline Orchestration**: Dagster (Job scheduling - configured but not actively used)
- **Container Management**: Portainer (Docker management - configured in docker-compose.yml)

### 🔧 DEVELOPMENT & MANAGEMENT
- **Python Scripts**: Automation and utility scripts in `scripts/` and `tools/scripts/`
- **Shell Scripts**: Service management scripts in `scripts/` and `infrastructure/`
- **Version Control**: Git for code management
- **Documentation**: Markdown-based docs in `docs/` directory

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- Git for version control

### 🚀 Start the Platform
```bash
# Clone the repository
git clone <repository-url>
cd foss-dataplatform

# Start all services with Docker Compose
docker-compose up -d

# Start the dashboard (alternative method)
./scripts/start_dashboard.sh
```

### 🌐 Access the Platform
Once started, access these services:

#### 🟢 ACTIVE SERVICES:
- **Main Dashboard**: http://localhost:5000 (Pipeline management & data browsing)
- **Pipeline Management**: http://localhost:5000/pipeline-management
- **Data Browser**: http://localhost:5000/data-browser
- **Health Check**: http://localhost:5000/health
- **About Page**: http://localhost:5000/about

#### 🟡 CONFIGURED SERVICES (May require additional setup):
- **Trino Query Engine**: http://localhost:8080 (SQL analytics)
- **MinIO Object Storage**: http://localhost:9000 (S3-compatible storage)
- **Portainer**: http://localhost:9001 (Container management)
- **Dagster**: http://localhost:3000 (Pipeline orchestration UI)

### 📊 Current Pipeline
The platform comes with a working **Stavanger Parking Pipeline** that:
- Ingests real-time parking data from Stavanger municipality API
- Transforms data using dbt with medallion architecture (Bronze → Silver → Gold)
- Stores data in Apache Iceberg tables with ACID transactions
- Provides web-based monitoring and data browsing

### 🔧 Development Workflow
```bash
# View pipeline data
# Go to: http://localhost:5000/pipeline-management

# Browse processed data
# Go to: http://localhost:5000/data-browser

# Check system health
# Go to: http://localhost:5000/health
```

## 📁 Project Structure & File Locations

```
foss-dataplatform/
├── 📊 pipelines/                          # 🎯 WHERE PIPELINES RESIDE
│   └── stavanger_parking/                 # Current working pipeline
│       ├── dbt/                           # 🏗️ WHERE TRANSFORMATIONS RESIDE
│       │   ├── models/                    # dbt SQL models (Bronze/Silver/Gold)
│       │   │   ├── bronze/                # Raw data models
│       │   │   ├── silver/                # Cleaned data models
│       │   │   └── gold/                  # Analytics-ready models
│       │   ├── tests/                     # Data quality tests
│       │   ├── macros/                    # Reusable SQL macros
│       │   ├── seeds/                     # Static data files
│       │   └── dbt_project.yml            # dbt configuration
│       ├── data/                          # 💾 WHERE PIPELINE DATA RESIDES
│       │   ├── raw/                       # Raw ingested data
│       │   ├── staging/                   # Cleaned/transformed data
│       │   └── processed/                 # Final processed datasets
│       ├── docs/                          # Pipeline documentation
│       └── scripts/                       # Pipeline-specific scripts
│
├── 🏗️ platform/                           # Platform infrastructure (future use)
│   ├── governance/                        # Data governance (placeholder)
│   ├── monitoring/                        # Monitoring configs (placeholder)
│   └── security/                          # Security policies (placeholder)
│
├── 🔧 scripts/                            # ⚙️ WHERE CORE SCRIPTS RESIDE
│   ├── start_dashboard.sh                 # Dashboard startup script
│   ├── monitor_dashboard.sh               # Dashboard monitoring script
│   └── [other automation scripts]         # Service management scripts
│
├── 📚 docs/                               # 📖 WHERE DOCUMENTATION RESIDES
│   ├── README.md                          # This main README
│   ├── DASHBOARD_README.md                # Dashboard usage guide
│   ├── ARCHITECTURE.md                    # System architecture docs
│   ├── PIPELINE_MANAGEMENT_GUIDE.md       # Pipeline development guide
│   └── [other documentation files]        # Platform documentation
│
├── 🌐 dashboard/                          # 🎛️ WHERE WEB DASHBOARD RESIDES
│   ├── app.py                             # Flask application (main core)
│   ├── templates/                         # HTML templates
│   │   ├── dashboard.html                 # Main dashboard page
│   │   ├── pipeline_management.html       # Pipeline management
│   │   ├── data_browser.html              # Data browsing interface
│   │   ├── about.html                     # About page
│   │   └── [other HTML templates]         # UI templates
│   └── static/                            # CSS/JS/images (if added later)
│
├── ⚙️ infrastructure/                     # 🏗️ WHERE INFRA CONFIGS RESIDE
│   ├── foss-dashboard.service             # Systemd service for dashboard
│   └── [other infrastructure files]       # Deployment configurations
│
├── 🛠️ tools/                              # 🔨 WHERE DEVELOPMENT TOOLS RESIDE
│   ├── scripts/                           # Additional utility scripts
│   │   ├── qa_test_suite.py               # Quality assurance tests
│   │   ├── service_validation_suite.py    # Service validation
│   │   └── [other development scripts]    # Development utilities
│   ├── cli/                               # Command-line tools
│   └── templates/                         # Code generation templates
│
├── 📦 docker-compose.yml                  # 🐳 WHERE CONTAINER CONFIGS RESIDE
├── 📋 requirements.txt                    # 📦 WHERE PYTHON DEPS RESIDE
├── 📖 README.md                           # 📚 Main documentation (this file)
└── 🔒 .venv/                              # 🐍 Python virtual environment
```

### 🎯 KEY LOCATIONS SUMMARY

| Component | Location | Purpose |
|-----------|----------|---------|
| **🧠 Core Application** | `dashboard/app.py` | Main Flask web application |
| **🔧 Pipeline Logic** | `pipelines/stavanger_parking/dbt/` | dbt transformations & models |
| **💾 Pipeline Data** | `pipelines/stavanger_parking/data/` | Raw, staging, and processed data |
| **🌐 Web Interface** | `dashboard/templates/` | HTML templates for UI |
| **⚙️ Automation Scripts** | `scripts/` | Service management & automation |
| **📚 Documentation** | `docs/` | All platform documentation |
| **🏗️ Infrastructure** | `infrastructure/` | Deployment & service configs |
| **🛠️ Development Tools** | `tools/` | QA, testing, and utilities |

### 🎯 Current Design Principles

**🏗️ Lakehouse-First Architecture:**
- Modern data lakehouse combining data lake flexibility with warehouse reliability
- ACID transactions, schema evolution, and time travel with Apache Iceberg
- Cost-effective storage with high-performance analytics

**🔧 Developer-Centric Design:**
- Clear separation between platform infrastructure and pipeline logic
- Web-based management interface for ease of use
- Docker-based deployment for consistency across environments

**📊 Production-Ready Operations:**
- Health monitoring and automated service management
- Comprehensive logging and error handling
- Scalable architecture ready for growth

## 🛠️ Development & Operations

### Platform Management
```bash
# Start the platform
docker-compose up -d

# Start dashboard with monitoring
./scripts/start_dashboard.sh

# Monitor dashboard health
./scripts/monitor_dashboard.sh

# Stop all services
docker-compose down
```

### Current Pipeline Operations
The **Stavanger Parking Pipeline** demonstrates:
- **Real-time Data Ingestion**: REST API data collection from municipality
- **Medallion Architecture**: Bronze (raw) → Silver (clean) → Gold (analytics) layers
- **Quality Assurance**: Automated dbt tests and data validation
- **Web Monitoring**: Real-time status, metrics, and data browsing

### Quality Assurance
```bash
# Run QA test suite
python tools/scripts/qa_test_suite.py

# Run service validation
python tools/scripts/service_validation_suite.py

# Manual data cleanup
python tools/scripts/cleanup_operations.py --dry-run
```

## 📚 Documentation Structure

Documentation is organized in the `docs/` directory:

- **`README.md`** - Main project overview (this file)
- **`DASHBOARD_README.md`** - Dashboard usage and management guide
- **`ARCHITECTURE.md`** - Detailed system architecture
- **`PIPELINE_MANAGEMENT_GUIDE.md`** - Pipeline development workflows
- **Other docs** - Feature-specific documentation and guides

## 🚀 Future Roadmap

### Phase 2: Analytics Engine Integration
- **Trino Integration**: Distributed SQL queries across data sources
- **Advanced Analytics**: Complex analytical queries and reporting
- **Multi-Source Queries**: Query across different data formats

### Phase 3: Object Storage Layer
- **MinIO Integration**: S3-compatible object storage for data lake
- **Storage Optimization**: Cost-effective, scalable data storage
- **Data Lifecycle**: Automated data tiering and archival

### Phase 4: Multi-Pipeline Orchestration
- **Pipeline Templates**: Automated pipeline creation from templates
- **Orchestration Engine**: Advanced workflow management
- **Monitoring Dashboard**: Comprehensive pipeline monitoring

### Phase 5: Enterprise Features
- **Security**: Authentication, authorization, and audit trails
- **Governance**: Data lineage, quality monitoring, and compliance
- **Scalability**: Support for 50+ concurrent pipelines

## 🤝 Contributing

### Getting Started
1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/your-username/foss-dataplatform.git`
3. **Create** a feature branch: `git checkout -b feature/your-feature`
4. **Make** your changes
5. **Test** thoroughly: `docker-compose up -d && ./scripts/start_dashboard.sh`
6. **Submit** a pull request

### Development Guidelines
- **Code Quality**: Run QA tests before submitting
- **Documentation**: Update docs for any new features
- **Testing**: Ensure all existing functionality works
- **Docker**: Test changes with Docker Compose

### Areas for Contribution
- **New Pipeline Templates**: Create templates for common use cases
- **Enhanced Monitoring**: Improve dashboard features and metrics
- **Documentation**: Improve guides and examples
- **Testing**: Add more comprehensive test coverage
- **Performance**: Optimize query performance and resource usage

## 📄 License

**MIT License** - This project is open-source and free to use, modify, and distribute.

See LICENSE file for full license details.

---

## 🎯 Quick Reference

| What | Where | Why |
|------|-------|-----|
| **Start Platform** | `docker-compose up -d` | Launch all services |
| **View Dashboard** | `http://localhost:5000` | Main management interface |
| **Pipeline Code** | `pipelines/stavanger_parking/dbt/` | dbt transformations |
| **Pipeline Data** | `pipelines/stavanger_parking/data/` | Raw, staging, processed data |
| **Core App** | `dashboard/app.py` | Flask web application |
| **Scripts** | `scripts/` | Automation and management |
| **Docs** | `docs/` | All documentation |

**Ready to explore? Start with:** `docker-compose up -d && ./scripts/start_dashboard.sh`
