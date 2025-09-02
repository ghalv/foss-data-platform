# FOSS Data PlatformExce

A modern, lean, and high-performing open-source data platform built with best-in-class FOSS tools.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   JupyterLab   │    │     Dagster     │    │      DBT        │
│  (Interactive) │    │  (Orchestration)│    │(Transformation) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Apache Trino  │
                    │ (Query Engine)  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Iceberg/Delta  │
                    │   (Storage)     │
                    └─────────────────┘
```

## Technology Stack

- **Interactive Layer**: JupyterLab
- **Data Ingestion**: Dagster
- **Storage**: Apache Iceberg / Delta Lake
- **Transformation**: DBT (Data Build Tool)
- **Query Engine**: Apache Trino
- **Key Management**: DBT + Custom Python Scripts
- **Infrastructure**: Terraform
- **Monitoring**: Prometheus + Grafana
- **Version Control**: Git
- **Secrets**: SOPS + Age

## Quick Start

1. **Prerequisites**
   - Debian 12 VPS
   - Docker and Docker Compose
   - Terraform
   - SOPS + Age for secrets management

2. **Setup Infrastructure**
   ```bash
   cd infrastructure
   terraform init
   terraform plan
   terraform apply
   ```

3. **Deploy Platform**
   ```bash
   docker-compose up -d
   ```

4. **Access Services**
   - **Platform Dashboard**: http://your-vps:5000 (Main entry point)
   - **Health Check**: http://your-vps:5000/health (Service status)
   - **System Metrics**: http://your-vps:5000/metrics (Performance monitoring)
   - JupyterLab: http://your-vps:8888
   - Dagster: http://your-vps:3000
   - Grafana: http://your-vps:3001
   - Trino: http://your-vps:8080
   - **Portainer**: http://your-vps:9000 (Container management)

## Project Structure

```
├── infrastructure/          # Terraform configurations
├── docker/                 # Docker configurations
├── dbt/                   # DBT project
├── dagster/               # Dagster pipelines
├── monitoring/            # Prometheus + Grafana configs
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

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
