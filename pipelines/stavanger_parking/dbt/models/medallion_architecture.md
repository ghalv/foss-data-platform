# 🏗️ Medallion Architecture for Stavanger Parking Pipeline

## Overview

This document describes the **Medallion Architecture** implementation for the Stavanger Parking data platform, built on **Apache Iceberg** and orchestrated with **dbt**. The architecture follows modern data lakehouse patterns with clear separation of concerns across Bronze, Silver, and Gold layers.

## 🥉 Bronze Layer (Raw Data)

### Purpose
- **Raw data ingestion** with minimal transformation
- **Data preservation** in original format
- **Time travel capabilities** for audit and debugging
- **Incremental loading** with Iceberg MERGE operations

### Key Models

#### `brz_raw_parking_data` (Landing Zone)
- **Source**: Delta load from Stavanger API
- **Materialization**: Incremental with MERGE strategy
- **Partitioning**: By `recorded_date`
- **Purpose**: Store raw API data as-is
- **Quality Gates**: Basic validation only

**Features:**
- Preserves original data structure
- Adds minimal type casting for partitioning
- Generates merge keys for incremental loading
- Tracks data quality indicators

#### `brz_data_quality_audit` (Audit Zone)
- **Purpose**: Monitor data quality and pipeline health
- **Materialization**: Incremental with APPEND strategy
- **Metrics**: Completeness, validity, anomaly detection

### Data Flow
```
API Data → Delta Load → Bronze Landing → Quality Audit → Silver Layer
```

---

## 🥈 Silver Layer (Cleaned & Enriched Data)

### Purpose
- **Data cleaning** and validation
- **Business entity standardization**
- **Referential integrity** establishment
- **Slowly changing dimensions** support

### Key Models

#### `slv_parking_locations` (Master Data Entity)
- **Type**: Slowly Changing Dimension
- **Purpose**: Standardized parking location master data
- **Materialization**: Incremental with MERGE strategy

**Business Logic:**
- Location categorization (transport_hub, city_center, residential)
- Capacity estimation and validation
- Geographic zone classification
- Business segment assignment

#### `slv_parking_occupancy_facts` (Transactional Facts)
- **Type**: Fact table with measures
- **Purpose**: Cleaned occupancy measurements
- **Materialization**: Incremental with MERGE strategy
- **Partitioning**: By `recorded_date`

**Calculations:**
- Utilization percentage computation
- Peak hour identification
- Time period categorization
- Business rule validation

#### `slv_date_dimension` (Conformed Dimension)
- **Type**: Standard calendar dimension
- **Purpose**: Consistent date/time analytics
- **Materialization**: Table (pre-computed)

**Attributes:**
- Business calendar logic
- Holiday identification
- Seasonal categorization
- Fiscal period calculations

### Data Flow
```
Bronze Raw Data → Cleaning & Validation → Business Rules → Silver Entities/Facts
```

---

## 🥇 Gold Layer (Business Analytics)

### Purpose
- **Business-ready aggregations**
- **Executive KPIs** and metrics
- **Real-time dashboards**
- **Predictive analytics features**

### Key Models

#### `gld_parking_performance_report` (Business Intelligence)
- **Type**: Aggregated business report
- **Purpose**: Daily performance analytics
- **Materialization**: Table

**Business Metrics:**
- Utilization KPIs and trends
- Peak hour performance analysis
- Capacity optimization recommendations
- Revenue potential calculations

#### `gld_dashboard_metrics` (Real-time Dashboard)
- **Type**: Live dashboard view
- **Purpose**: Current state monitoring
- **Materialization**: View

**Real-time Features:**
- Latest occupancy readings
- System-wide KPIs
- Freshness indicators
- Capacity status alerts

#### `gld_parking_predictive_features` (Machine Learning)
- **Type**: Feature engineering dataset
- **Purpose**: ML model training and prediction
- **Materialization**: Table

**Predictive Features:**
- Time series patterns
- Trend analysis (rolling averages)
- Seasonal components
- Anomaly detection indicators

### Data Flow
```
Silver Entities + Facts → Aggregation → Business Logic → Gold Analytics
```

---

## 🏛️ Architecture Principles

### 1. **Data Quality Gates**
Each layer implements quality gates:
- **Bronze**: Basic validation and audit
- **Silver**: Business rule validation
- **Gold**: Business logic consistency checks

### 2. **Incremental Processing**
- **Bronze**: MERGE operations for delta loads
- **Silver**: Incremental updates for dimensions and facts
- **Gold**: Full refresh for business aggregations

### 3. **Iceberg Partitioning Strategy**
```yaml
# Bronze Layer
partition_by: {"field": "recorded_date", "data_type": "date"}

# Silver Layer (Facts)
partition_by: {"field": "recorded_date", "data_type": "date"}

# Gold Layer (Analytics)
# No partitioning - optimized for complex queries
```

### 4. **Schema Evolution**
- **Bronze**: Schema-on-read flexibility
- **Silver**: Controlled schema evolution
- **Gold**: Stable business schemas

---

## 🔧 Technical Implementation

### dbt Model Organization
```
models/
├── bronze/
│   ├── landing/
│   │   └── brz_raw_parking_data.sql
│   └── audit/
│       └── brz_data_quality_audit.sql
├── silver/
│   ├── entities/
│   │   └── slv_parking_locations.sql
│   ├── facts/
│   │   └── slv_parking_occupancy_facts.sql
│   └── conformed/
│       └── slv_date_dimension.sql
└── gold/
    ├── reports/
    │   └── gld_parking_performance_report.sql
    ├── dashboards/
    │   └── gld_dashboard_metrics.sql
    └── analytics/
        └── gld_parking_predictive_features.sql
```

### Data Quality Testing
```
tests/
├── bronze/
│   └── test_brz_raw_parking_data_quality.sql
├── silver/
│   ├── test_slv_parking_locations_quality.sql
│   └── test_slv_occupancy_facts_quality.sql
└── gold/
    └── test_gld_performance_report_quality.sql
```

---

## 📊 Business Value

### Operational Benefits
- **🔍 Data Discovery**: Easy exploration from Bronze to Gold
- **⚡ Performance**: Optimized queries at each layer
- **🔄 Flexibility**: Schema evolution without breaking changes
- **🎯 Analytics**: Purpose-built datasets for different use cases

### Use Cases Enabled

#### Real-time Dashboards
```sql
SELECT * FROM gld_dashboard_metrics
WHERE data_freshness = 'current'
ORDER BY utilization_percentage DESC
```

#### Business Intelligence Reports
```sql
SELECT
    recorded_date,
    location_name,
    utilization_status,
    business_recommendation
FROM gld_parking_performance_report
WHERE recorded_date >= current_date - interval '30 days'
```

#### Predictive Analytics
```sql
SELECT * FROM gld_parking_predictive_features
WHERE target_next_hour_utilization IS NOT NULL
-- Use for ML model training
```

---

## 🚀 Scaling & Performance

### Iceberg Optimizations
- **Partitioning**: Date-based partitioning for time-series data
- **Z-ordering**: Optimized for common query patterns
- **Compaction**: Automatic file optimization
- **Caching**: Query result caching in Trino

### Query Performance
- **Bronze**: Fast raw data access for exploration
- **Silver**: Optimized joins with conformed dimensions
- **Gold**: Pre-aggregated metrics for dashboard performance

### Incremental Loading
- **Micro-batch processing** every 15 minutes
- **MERGE operations** for efficient updates
- **Change data capture** via merge keys
- **Time travel** for point-in-time analysis

---

## 🔍 Monitoring & Observability

### Data Quality Metrics
- **Completeness**: Percentage of valid records
- **Accuracy**: Business rule compliance
- **Freshness**: Data currency indicators
- **Consistency**: Cross-table validation

### Pipeline Health
- **Success rates** for each layer
- **Processing latency** monitoring
- **Error categorization** and alerting
- **Volume tracking** for capacity planning

---

## 🛠️ Development Workflow

### Adding New Features
1. **Bronze**: Add raw data fields with minimal transformation
2. **Silver**: Implement business logic and validation rules
3. **Gold**: Create business aggregations and KPIs

### Testing Strategy
1. **Unit Tests**: Individual model validation
2. **Integration Tests**: Cross-layer consistency
3. **Business Tests**: KPI and metric accuracy

### Deployment Process
1. **Bronze First**: Deploy raw data models
2. **Silver Next**: Deploy cleaned data models
3. **Gold Last**: Deploy business analytics models

---

## 📈 Future Enhancements

### Advanced Analytics
- **Machine Learning**: Predictive occupancy models
- **Anomaly Detection**: Automated outlier identification
- **Trend Analysis**: Advanced time series forecasting

### Performance Optimizations
- **Materialized Views**: Pre-computed complex aggregations
- **Query Caching**: Intelligent result caching
- **Columnar Storage**: Optimized for analytical queries

### Governance Features
- **Data Lineage**: End-to-end data flow tracking
- **Access Control**: Role-based data access
- **Audit Trails**: Comprehensive change logging

---

## 🎯 Key Success Metrics

### Technical Metrics
- **Query Performance**: < 5 second response times for dashboards
- **Data Freshness**: < 15 minute data latency
- **Pipeline Reliability**: > 99.9% uptime
- **Storage Efficiency**: < 30% data duplication across layers

### Business Metrics
- **User Adoption**: Active dashboard users
- **Decision Velocity**: Time to insights
- **Data Quality Score**: > 95% accuracy
- **ROI**: Cost savings from data-driven decisions

---

*This medallion architecture provides a robust, scalable foundation for Stavanger Parking analytics while maintaining data quality, performance, and business value throughout the data lifecycle.*
