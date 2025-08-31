# DBT Project for FOSS Data Platform

This directory contains the dbt project configuration for our FOSS data platform, using the dbt-trino adapter to connect to Apache Trino.

## 🎯 **What is dbt-trino?**

[dbt-trino](https://github.com/starburstdata/dbt-trino) is the official Trino adapter for dbt, allowing us to:
- Transform data using SQL models
- Execute transformations on Apache Trino
- Leverage Trino's distributed query engine
- Connect to multiple data sources through Trino

## 🏗️ **Project Structure**

```
dbt/
├── models/
│   ├── staging/          # Raw data models
│   ├── intermediate/     # Intermediate transformations
│   └── marts/           # Final business-ready models
├── dbt_project.yml       # Project configuration
├── profiles.yml          # Connection profiles
└── README.md            # This file
```

## 🔧 **Configuration**

### **Profiles**
- **dev**: Development environment (localhost:8080)
- **prod**: Production environment (localhost:8080)
- **minio**: MinIO storage catalog (localhost:8080)

### **Catalogs**
- **iceberg**: Apache Iceberg format for ACID compliance
- **minio**: S3-compatible object storage

## 🚀 **Getting Started**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Test Connection**
```bash
dbt debug --profile foss_data_platform
```

### **3. Run Models**
```bash
dbt run --profile foss_data_platform
```

### **4. Test Models**
```bash
dbt test --profile foss_data_platform
```

## 📊 **Current Models**

### **Staging Models**
- `stg_example.sql`: Simple test model
- `stg_stavanger_parking.sql`: Stavanger parking data staging

### **Future Models**
- Intermediate transformations for parking data
- Mart models for business analytics
- Data quality tests and monitoring

## 🔗 **Integration with Platform**

This dbt project integrates with:
- **Dagster**: For orchestration and scheduling
- **Trino**: For query execution
- **MinIO**: For data storage
- **Iceberg**: For table format

## 📚 **Resources**

- [dbt-trino Documentation](https://github.com/starburstdata/dbt-trino)
- [dbt Core Documentation](https://docs.getdbt.com/)
- [Trino Documentation](https://trino.io/docs/)
- [Apache Iceberg](https://iceberg.apache.org/)
