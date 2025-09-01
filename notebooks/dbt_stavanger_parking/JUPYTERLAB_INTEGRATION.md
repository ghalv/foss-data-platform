# 🚀 **JupyterLab Integration for Pipeline Management**

## **Overview**

This integration provides **seamless pipeline management directly from JupyterLab** using dbt magic commands and interactive tools. No more switching between terminals and notebooks!

## **🎯 What You Can Do**

### **✅ Full Pipeline Management**
- **Run Models**: Execute dbt models directly from notebooks
- **Run Tests**: Execute data quality tests
- **Load Data**: Seed raw data into the pipeline
- **Generate Docs**: Create documentation automatically
- **Monitor Status**: Track pipeline health and performance

### **✅ Interactive Data Analysis**
- **Query Trino**: Execute SQL queries against your pipeline data
- **Data Visualization**: Create charts and insights
- **Real-time Monitoring**: Check pipeline status and metrics
- **Custom Analysis**: Build custom data quality checks

## **🔧 Setup Instructions**

### **1. Load Magic Commands**
```python
# In any JupyterLab notebook
exec(open('jupyter_setup.py').read())
print("✅ dbt Magic Commands loaded successfully!")
```

### **2. Verify Setup**
```python
%dbt_help
```

## **🚀 Available Magic Commands**

### **Basic Commands**
| Command | Description | Example |
|---------|-------------|---------|
| `%dbt run` | Run all models | `%dbt run` |
| `%dbt test` | Run all tests | `%dbt test` |
| `%dbt seed` | Load seeds | `%dbt seed` |
| `%dbt docs` | Generate docs | `%dbt docs generate` |
| `%dbt list` | List models | `%dbt list` |

### **Advanced Commands**
| Command | Description | Example |
|---------|-------------|---------|
| `%dbt run --select tag:staging` | Run specific models | `%dbt run --select tag:staging` |
| `%dbt test --select test_name` | Run specific tests | `%dbt test --select test_critical_fields_not_null` |
| `%dbt_status` | Show project status | `%dbt_status` |
| `%dbt_help` | Show help | `%dbt_help` |

### **Cell Magic Commands**
| Command | Description | Example |
|---------|-------------|---------|
| `%%dbt_run` | Run models with custom logic | See notebook examples |
| `%%dbt_test` | Run tests with custom logic | See notebook examples |

## **📊 Utility Functions**

### **Pipeline Information**
```python
# Show pipeline structure
show_pipeline_structure()

# Check current status
get_pipeline_info()
```

### **Data Querying**
```python
# Query Trino directly
df = query_trino("SELECT * FROM memory.default_staging.stg_parking_data LIMIT 10")
```

## **🎨 Example Workflows**

### **Complete Pipeline Run**
```python
# 1. Load data
%dbt seed

# 2. Run all models
%dbt run

# 3. Run all tests
%dbt test

# 4. Generate documentation
%dbt docs generate
```

### **Selective Model Execution**
```python
# Run only staging models
%dbt run --select tag:staging

# Run specific model
%dbt run --select staging.stg_parking_data

# Run models with dependencies
%dbt run --select +mart_parking_insights
```

### **Data Quality Testing**
```python
# Run all tests
%dbt test

# Run specific test
%dbt test --select test_critical_fields_not_null

# Run tests for specific model
%dbt test --select staging.stg_parking_data
```

## **🔍 Monitoring & Debugging**

### **Check Pipeline Status**
```python
# Show available models
%dbt_status

# Check pipeline info
get_pipeline_info()

# List all models
%dbt list
```

### **Error Handling**
- All commands provide detailed output and error messages
- Failed commands show exit codes and error details
- Timeout protection for long-running operations

## **📈 Interactive Analysis Examples**

### **Basic Data Exploration**
```python
# Query staging data
df = query_trino("""
SELECT 
    parking_location,
    AVG(utilization_rate) as avg_utilization,
    COUNT(*) as readings
FROM memory.default_staging.stg_parking_data 
GROUP BY parking_location
ORDER BY avg_utilization DESC
""")

# Display results
display(df.head())
```

### **Data Quality Monitoring**
```python
# Check for data quality issues
quality_query = """
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN current_occupancy > total_capacity THEN 1 END) as invalid_records,
    ROUND(COUNT(CASE WHEN current_occupancy > total_capacity THEN 1 END) * 100.0 / COUNT(*), 2) as error_rate
FROM memory.default_staging.stg_parking_data
"""

quality_df = query_trino(quality_query)
display(quality_df)
```

## **🚀 Advanced Features**

### **Custom Model Execution**
```python
%%dbt_run
# This cell will run dbt run with any custom logic
# You can add Python code here before the dbt execution
print("Preparing to run models...")
# The dbt command will execute automatically
```

### **Automated Testing**
```python
%%dbt_test
# Run tests with custom validation logic
import pandas as pd

# Custom validation
df = query_trino("SELECT * FROM memory.default_staging.stg_parking_data")
print(f"Testing {len(df)} records...")

# The dbt test command will execute automatically
```

## **🔧 Troubleshooting**

### **Common Issues**

**1. Magic Commands Not Working**
```python
# Ensure setup script is loaded
exec(open('jupyter_setup.py').read())
```

**2. dbt Not Found**
- Ensure dbt is installed in your JupyterLab environment
- Check that `dbt-trino` is available

**3. Connection Issues**
- Verify Trino is running on `localhost:8080`
- Check network connectivity

### **Debug Mode**
```python
# Enable verbose output
import logging
logging.basicConfig(level=logging.DEBUG)
```

## **🎉 Benefits**

### **✅ Developer Experience**
- **No Context Switching**: Manage pipelines from notebooks
- **Interactive Development**: Test and validate changes immediately
- **Version Control**: Track pipeline changes with notebook changes
- **Collaboration**: Share pipeline logic and analysis

### **✅ Operational Efficiency**
- **Faster Iteration**: Immediate feedback on pipeline changes
- **Better Debugging**: Interactive error investigation
- **Automated Workflows**: Build custom pipeline management scripts
- **Real-time Monitoring**: Track pipeline health during development

## **🚀 Next Steps**

1. **Load the setup script** in your JupyterLab environment
2. **Explore the magic commands** with `%dbt_help`
3. **Run your first pipeline** with `%dbt run`
4. **Build custom analysis** using the utility functions
5. **Create automated workflows** for your specific needs

---

**🎯 You now have enterprise-grade pipeline management directly from JupyterLab!** 

No more terminal switching, no more manual command execution. Everything you need is available through intuitive magic commands and interactive tools.
