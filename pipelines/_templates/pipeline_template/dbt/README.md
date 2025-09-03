# Stavanger Parking Data Pipeline

A modern, production-ready data pipeline for Stavanger parking data analysis, built with dbt, Trino, and following data engineering best practices.

## 🎯 **Project Overview**

This project demonstrates a complete data pipeline from raw data ingestion to business intelligence insights, showcasing modern data engineering practices and our FOSS data platform's capabilities.

## 🏗️ **Architecture**

### **Data Flow**
```
Raw Data (OpenCom.no) → Staging → Intermediate → Marts → Business Intelligence
```

### **Layers**
- **Staging**: Raw data validation and basic transformations
- **Intermediate**: Business logic and aggregations
- **Marts**: Business-ready datasets for analytics
  - **Core**: Dimension and fact tables
  - **Marketing**: Business insights and recommendations

## 📊 **Data Models**

### **Staging Models**
- `stg_parking_data`: Raw data with business logic and metadata

### **Intermediate Models**
- `int_daily_parking_metrics`: Daily aggregations and KPIs

### **Core Marts**
- `dim_parking_locations`: Location dimension table
- `fct_parking_utilization`: Utilization fact table

### **Marketing Marts**
- `mart_parking_insights`: Business intelligence and recommendations

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.8+
- dbt-core 1.7.0+
- dbt-trino 1.7.0+
- Access to Trino database

### **Installation**
```bash
# Activate virtual environment
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dbt dependencies
dbt deps
```

### **Configuration**
1. Update `profiles.yml` with your Trino connection details
2. Ensure Trino is running and accessible
3. Verify database permissions

### **Running the Pipeline**
```bash
# Run all models
dbt run

# Run specific models
dbt run --select staging
dbt run --select marts

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

## 🔍 **Data Quality & Testing**

### **Automated Tests**
- **Data Integrity**: Null checks, duplicate detection
- **Business Logic**: Capacity vs occupancy validation
- **Calculations**: Utilization rate accuracy
- **Range Validation**: Price and capacity bounds

### **Test Commands**
```bash
# Run all tests
dbt test

# Run specific test categories
dbt test --select test_type:generic
dbt test --select test_type:singular
```

## 📈 **Key Metrics & KPIs**

### **Operational Metrics**
- **Utilization Rate**: Current occupancy vs capacity
- **Peak Hour Analysis**: Morning/evening rush patterns
- **Capacity Health**: Critical status frequency

### **Business Metrics**
- **Revenue Potential**: Estimated daily revenue
- **Location Performance**: Category-based analysis
- **Optimization Score**: Revenue optimization potential

### **Strategic Insights**
- **Business Recommendations**: Demand-based suggestions
- **Location Strategy**: Category-specific optimization
- **Capacity Planning**: Expansion and development guidance

## 🎨 **Data Visualization**

### **Grafana Dashboards**
- **Real-time Monitoring**: Live parking utilization
- **Trend Analysis**: Historical patterns and forecasts
- **Business Intelligence**: Strategic insights and recommendations

### **Sample Queries**
```sql
-- Daily utilization by location
SELECT 
    recorded_date,
    parking_location,
    avg_utilization_rate_rounded,
    business_recommendation
FROM marts_marketing.mart_parking_insights
ORDER BY recorded_date DESC, avg_utilization_rate_rounded DESC;

-- Peak hour analysis
SELECT 
    parking_location,
    peak_hour_percentage,
    peak_hour_avg_utilization
FROM intermediate.int_daily_parking_metrics
WHERE peak_hour_percentage > 20;
```

## 🔧 **Development Workflow**

### **Model Development**
1. **Create staging models** for raw data validation
2. **Build intermediate models** for business logic
3. **Design mart models** for business consumption
4. **Add tests** for data quality assurance
5. **Update documentation** for maintainability

### **Testing Strategy**
- **Unit Tests**: Individual model validation
- **Integration Tests**: Cross-model dependencies
- **Data Quality Tests**: Business rule validation
- **Performance Tests**: Query optimization

### **Deployment**
- **Development**: Local testing and validation
- **Staging**: Integration testing
- **Production**: Automated deployment with CI/CD

## 📚 **Documentation**

### **Model Documentation**
Each model includes:
- **Purpose**: Business objective and use case
- **Dependencies**: Upstream and downstream models
- **Business Logic**: Key calculations and transformations
- **Usage Examples**: Sample queries and insights

### **Generated Documentation**
```bash
dbt docs generate
dbt docs serve
```

## 🚀 **Platform Integration**

### **Dagster Orchestration**
- **Asset Dependencies**: Automated pipeline execution
- **Monitoring**: Success/failure tracking
- **Scheduling**: Automated data updates

### **MinIO Storage**
- **Raw Data**: Original datasets
- **Processed Data**: Cleaned and transformed data
- **Metadata**: Pipeline documentation and lineage

### **Trino Query Engine**
- **SQL Processing**: Complex analytical queries
- **Performance**: Optimized query execution
- **Scalability**: Distributed query processing

## 🔮 **Future Enhancements**

### **Advanced Analytics**
- **Machine Learning**: Predictive capacity modeling
- **Real-time Processing**: Streaming data ingestion
- **Advanced Metrics**: Customer behavior analysis

### **Integration**
- **External APIs**: Weather, events, traffic data
- **Mobile Apps**: Real-time parking availability
- **Payment Systems**: Revenue optimization

## 🤝 **Contributing**

### **Development Guidelines**
1. **Follow dbt best practices** for model design
2. **Add comprehensive tests** for data quality
3. **Document all models** with clear descriptions
4. **Use consistent naming conventions**
5. **Implement incremental processing** where appropriate

### **Code Review Process**
1. **Model validation** with dbt test
2. **Documentation updates** for new models
3. **Performance review** for query optimization
4. **Business logic validation** with stakeholders

## 📞 **Support & Contact**

For questions or support:
- **Documentation**: Run `dbt docs serve`
- **Issues**: Check test results with `dbt test`
- **Performance**: Monitor query execution times
- **Business Logic**: Review model documentation

---

**Built with ❤️ using modern data engineering best practices and our FOSS data platform.**
