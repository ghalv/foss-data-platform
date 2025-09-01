# Data Pipeline Management Guide
## FOSS Data Platform

This guide covers how to add, edit, remove, and manage data pipelines on our platform.

---

## 📋 **Table of Contents**

1. [Pipeline Architecture Overview](#pipeline-architecture-overview)
2. [Adding New Pipelines](#adding-new-pipelines)
3. [Editing Existing Pipelines](#editing-existing-pipelines)
4. [Removing Pipelines](#removing-pipelines)
5. [Pipeline Lifecycle Management](#pipeline-lifecycle-management)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🏗️ **Pipeline Architecture Overview**

### **Platform Components:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  dbt Pipeline   │───▶│  Business      │
│   (APIs, Files) │    │   (Trino)       │    │  Intelligence   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MinIO Storage │    │  Dagster        │    │  Grafana       │
│   (Raw Data)    │    │  (Orchestration)│    │  (Dashboards)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Pipeline Layers:**
1. **Staging**: Raw data validation and basic transformations
2. **Intermediate**: Business logic and aggregations
3. **Marts**: Business-ready datasets
4. **Business Intelligence**: Insights and recommendations

---

## ➕ **Adding New Pipelines**

### **Step 1: Project Structure**
```bash
# Create new pipeline directory
mkdir dbt_new_pipeline
cd dbt_new_pipeline

# Create standard structure
mkdir -p {models/{staging,intermediate,marts/{core,marketing}},seeds,tests,scripts,docs,macros}
```

### **Step 2: Configuration Files**

#### **dbt_project.yml**
```yaml
name: 'new_pipeline'
version: '1.0.0'
config-version: 2

profile: 'new_pipeline'

model-paths: ["models"]
analysis-paths: ["analysis"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

models:
  new_pipeline:
    staging:
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: view
      +schema: intermediate
    marts:
      +materialized: table
      +schema: marts
      core:
        +materialized: table
        +schema: marts_core
      marketing:
        +materialized: table
        +schema: marts_marketing
```

#### **profiles.yml**
```yaml
new_pipeline:
  target: dev
  outputs:
    dev:
      type: trino
      host: localhost
      port: 8080
      user: trino
      password: ""
      catalog: memory  # or iceberg for production
      schema: default
      threads: 4
      http_scheme: http
      use_ssl: false
      verify: false
```

#### **requirements.txt**
```txt
dbt-trino==1.7.0
dbt-core==1.7.0
pandas==2.0.3
requests==2.31.0
python-dotenv==1.0.0
```

### **Step 3: Data Models**

#### **Staging Model Example**
```sql
-- models/staging/stg_new_data.sql
{{
  config(
    materialized='view',
    schema='staging',
    tags=['staging', 'new_pipeline', 'daily']
  )
}}

with source as (
    select * from {{ ref('raw_new_data') }}
),

staged as (
    select
        id,
        timestamp,
        value,
        category,
        current_timestamp as _loaded_at
    from source
)

select * from staged
```

#### **Intermediate Model Example**
```sql
-- models/intermediate/int_daily_metrics.sql
{{
  config(
    materialized='view',
    schema='intermediate',
    tags=['intermediate', 'new_pipeline', 'daily']
  )
}}

with staging as (
    select * from {{ ref('stg_new_data') }}
),

daily_metrics as (
    select
        date(timestamp) as metric_date,
        category,
        count(*) as record_count,
        avg(value) as avg_value
    from staging
    group by 1, 2
)

select * from daily_metrics
```

#### **Mart Model Example**
```sql
-- models/marts/core/fct_new_facts.sql
{{
  config(
    materialized='table',
    schema='marts_core',
    tags=['marts', 'core', 'new_pipeline']
  )
}}

with intermediate as (
    select * from {{ ref('int_daily_metrics') }}
),

final as (
    select
        *,
        case 
            when avg_value > 100 then 'High'
            when avg_value > 50 then 'Medium'
            else 'Low'
        end as performance_category
    from intermediate
)

select * from final
```

### **Step 4: Data Ingestion Script**
```python
# scripts/download_data.py
#!/usr/bin/env python3
"""
Data Ingestion Script for New Pipeline
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime

class NewDataIngestion:
    def __init__(self, output_dir="seeds"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download_data(self):
        # Implement data download logic
        pass
    
    def create_sample_data(self):
        # Create sample data for development
        pass

def main():
    ingestion = NewDataIngestion()
    if ingestion.download_data():
        print("Data ingestion completed successfully!")
    else:
        print("Data ingestion failed!")

if __name__ == "__main__":
    main()
```

### **Step 5: Data Quality Tests**
```sql
-- tests/test_data_quality.sql
-- Test for null values in critical fields
select 
    count(*) as null_count
from {{ ref('stg_new_data') }}
where id is null 
   or timestamp is null 
   or value is null
```

### **Step 6: Dagster Assets**
```python
# dagster_assets.py
from dagster import asset, AssetExecutionContext

@asset(
    description="Download and validate new data",
    tags=["ingestion", "new_pipeline"],
    group_name="ingestion"
)
def raw_new_data(context: AssetExecutionContext):
    # Implement data ingestion
    pass

@asset(
    description="Run dbt pipeline",
    tags=["dbt", "new_pipeline"],
    group_name="dbt_processing",
    deps=[raw_new_data]
)
def dbt_pipeline(context: AssetExecutionContext):
    # Run dbt models
    pass
```

### **Step 7: Testing the Pipeline**
```bash
# Install dependencies
pip install -r requirements.txt

# Test connection
dbt debug

# Load seeds
dbt seed

# Run models
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
```

---

## ✏️ **Editing Existing Pipelines**

### **Adding New Models**
```bash
# Create new model file
touch models/staging/stg_new_feature.sql

# Edit the model with proper configuration
# Add tests
touch tests/test_new_feature.sql

# Update dbt_project.yml if needed
# Run the new model
dbt run --select stg_new_feature
```

### **Modifying Existing Models**
```bash
# Edit the model file
vim models/staging/stg_parking_data.sql

# Test the changes
dbt run --select stg_parking_data

# Run downstream models
dbt run --select +stg_parking_data
```

### **Adding New Tests**
```bash
# Create new test file
touch tests/test_new_business_rule.sql

# Run specific test
dbt test --select test_new_business_rule
```

### **Updating Dependencies**
```bash
# Update requirements.txt
pip install new_package

# Update dbt_project.yml
# Run dbt deps
dbt deps
```

---

## 🗑️ **Removing Pipelines**

### **Step 1: Stop Pipeline Execution**
```bash
# Stop Dagster if running
docker-compose stop dagster

# Or stop specific assets
# (Remove from Dagster UI or code)
```

### **Step 2: Remove dbt Models**
```bash
# Remove model files
rm -rf models/staging/stg_parking_data.sql
rm -rf models/intermediate/int_daily_parking_metrics.sql
rm -rf models/marts/core/dim_parking_locations.sql
rm -rf models/marts/core/fct_parking_utilization.sql
rm -rf models/marts/marketing/mart_parking_insights.sql

# Remove test files
rm -rf tests/test_*.sql

# Remove scripts
rm -rf scripts/download_data.py
```

### **Step 3: Clean Database**
```bash
# Drop schemas (if using persistent catalog)
docker exec -it trino-coordinator trino --execute "
DROP SCHEMA IF EXISTS memory.default_staging CASCADE;
DROP SCHEMA IF EXISTS memory.default_intermediate CASCADE;
DROP SCHEMA IF EXISTS memory.default_marts_core CASCADE;
DROP SCHEMA IF EXISTS memory.default_marts_marketing CASCADE;
"
```

### **Step 4: Remove Project Files**
```bash
# Remove entire project directory
cd ..
rm -rf dbt_stavanger_parking

# Remove from git (if committed)
git rm -r dbt_stavanger_pipeline
git commit -m "Remove Stavanger Parking pipeline"
```

### **Step 5: Update Platform Configuration**
```bash
# Remove from docker-compose.yml if needed
# Remove from Dagster workspace if needed
# Update documentation
```

---

## 🔄 **Pipeline Lifecycle Management**

### **Development Phase**
```bash
# 1. Create project structure
mkdir dbt_new_pipeline

# 2. Develop models incrementally
dbt run --select staging
dbt run --select intermediate
dbt run --select marts

# 3. Test continuously
dbt test

# 4. Generate documentation
dbt docs generate
```

### **Testing Phase**
```bash
# 1. Run full pipeline
dbt run

# 2. Validate data quality
dbt test

# 3. Performance testing
dbt run --profiles-dir profiles_prod

# 4. Integration testing
# Test with real data sources
```

### **Production Phase**
```bash
# 1. Deploy to production
dbt run --target prod

# 2. Set up monitoring
# Configure alerts and dashboards

# 3. Schedule execution
# Set up Dagster schedules

# 4. Monitor performance
# Track execution times and failures
```

### **Maintenance Phase**
```bash
# 1. Regular testing
dbt test --target prod

# 2. Performance optimization
# Analyze slow queries
# Optimize model materializations

# 3. Documentation updates
dbt docs generate

# 4. Dependency updates
dbt deps
```

---

## ✅ **Best Practices**

### **Project Structure**
- Use consistent naming conventions
- Separate concerns (staging, intermediate, marts)
- Group related models with tags
- Maintain clear dependencies

### **Data Quality**
- Test critical business rules
- Validate data types and ranges
- Check for duplicates and nulls
- Monitor data freshness

### **Performance**
- Use appropriate materializations
- Optimize query patterns
- Monitor execution times
- Use incremental models where possible

### **Documentation**
- Document business logic
- Maintain data lineage
- Update README files
- Generate dbt documentation

### **Version Control**
- Commit pipeline changes
- Use meaningful commit messages
- Tag releases
- Maintain change logs

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Connection Problems**
```bash
# Test Trino connection
dbt debug

# Check service status
docker-compose ps

# Verify network connectivity
docker exec -it trino-coordinator trino --execute "SELECT 1"
```

#### **Model Failures**
```bash
# Check model compilation
dbt compile --select failing_model

# View compiled SQL
cat target/compiled/stavanger_parking/models/staging/stg_parking_data.sql

# Check dependencies
dbt list --select +failing_model
```

#### **Test Failures**
```bash
# Run specific test
dbt test --select test_name

# Store failures for analysis
dbt test --store-failures

# Check failure details
docker exec -it trino-coordinator trino --execute "
SELECT * FROM memory.default_dbt_test__audit.test_name
"
```

#### **Performance Issues**
```bash
# Profile model execution
dbt run --select slow_model --profile

# Check model materializations
dbt run --select slow_model --full-refresh

# Analyze query plans
# Use Trino EXPLAIN for complex queries
```

### **Debugging Commands**
```bash
# List all models
dbt list

# Show model dependencies
dbt list --select +model_name

# Check model status
dbt run --select model_name --dry-run

# View model lineage
dbt ls --select +model_name
```

---

## 📚 **Additional Resources**

### **Documentation**
- [dbt Documentation](https://docs.getdbt.com/)
- [Trino Documentation](https://trino.io/docs/)
- [Dagster Documentation](https://docs.dagster.io/)

### **Templates and Examples**
- Check `dbt_stavanger_parking/` for working examples
- Use `dbt init` for new project templates
- Reference existing models for patterns

### **Support**
- Platform logs: `docker-compose logs service_name`
- dbt logs: `target/logs/`
- Trino logs: `docker-compose logs trino-coordinator`

---

## 🎯 **Quick Reference**

### **Essential Commands**
```bash
# New pipeline
dbt init new_pipeline
dbt run --select staging
dbt test
dbt docs generate

# Edit pipeline
dbt run --select model_name
dbt test --select test_name
dbt run --select +model_name

# Remove pipeline
dbt run --select model_name --full-refresh
# Then delete files and clean database
```

### **File Structure**
```
dbt_pipeline/
├── dbt_project.yml      # Project configuration
├── profiles.yml         # Database connections
├── requirements.txt     # Python dependencies
├── models/             # Data models
│   ├── staging/        # Raw data validation
│   ├── intermediate/   # Business logic
│   └── marts/         # Business datasets
├── tests/              # Data quality tests
├── scripts/            # Data ingestion
├── docs/               # Documentation
└── macros/             # Reusable logic
```

---

**This guide covers the complete lifecycle of data pipelines on our FOSS data platform. For specific questions or advanced scenarios, refer to the individual tool documentation or platform logs.**
