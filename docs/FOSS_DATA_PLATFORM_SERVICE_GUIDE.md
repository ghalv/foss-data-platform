# 🚀 FOSS Data Platform Service Access Guide

## **Overview**

This guide explains when and how to access each service in your FOSS data platform. Each service has a specific purpose and is accessed at different stages of your data engineering workflow.

---

## **🌐 Web-Based Services (Browser Access)**

### **1. 🏠 Platform Dashboard** - `http://localhost:5000`
**When to Use:**
- **Monitoring platform health** and service status
- **Viewing pipeline execution results** and metrics
- **Quick overview** of all platform services
- **Running pipeline operations** (seed, run, test)
- **Accessing the Data Browser** for interactive queries

**What You Can Do:**
- Check service health status
- View real-time system metrics
- Execute dbt pipeline commands
- Monitor pipeline performance
- Access business intelligence dashboards
- Navigate to all platform services

**Access Method:** Open in browser, no authentication required

---

### **2. 🔍 Data Browser** - `http://localhost:5000/data-browser`
**When to Use:**
- **Interactive SQL queries** and data exploration
- **Browsing table schemas** and metadata
- **Testing queries** before implementing in dbt
- **Quick data analysis** and validation
- **Exporting query results** to CSV

**What You Can Do:**
- Write and execute SQL queries
- Browse Iceberg and memory catalogs
- View table schemas and data previews
- Export results for further analysis
- Test complex joins and aggregations

**Access Method:** Integrated in dashboard, no authentication required

---

### **3. ❤️ Health Dashboard** - `http://localhost:5000/health`
**When to Use:**
- **Monitoring service health** and platform status
- **Viewing system performance** (CPU, memory, disk) at-a-glance
- **Quick access** to external service UIs

**What You Can Do:**
- See consolidated service status grid
- View compact system metrics
- Navigate to service UIs (Grafana, Trino, etc.)

**Access Method:** Integrated in dashboard, no authentication required

---

### **4. 📊 Grafana** - `http://localhost:3001`
**When to Use:**
- **Creating custom dashboards** and visualizations
- **Monitoring system performance** over time
- **Setting up alerts** for critical metrics
- **Business intelligence reporting**

**What You Can Do:**
- Build custom dashboards
- Create time-series charts
- Set up monitoring alerts
- Export reports
- Share dashboards with stakeholders

**Access Method:** 
- Username: `admin`
- Password: `admin123`

---

### **5. 🐳 Portainer** - `http://localhost:9000`
**When to Use:**
- **Managing Docker containers** and services
- **Monitoring container performance** and logs
- **Restarting services** when needed
- **Viewing container resource usage**

**What You Can Do:**
- View all running containers
- Access container logs
- Restart/stop services
- Monitor resource usage
- Manage container networks

**Access Method:** 
- Username: `admin`
- Password: `admin123`

---

### **6. 🔬 JupyterLab** - `http://localhost:8888`
**When to Use:**
- **Interactive data exploration** and analysis
- **Developing and testing** dbt models
- **Creating data notebooks** and documentation
- **Running ad-hoc queries** and experiments
- **Editing pipeline files** directly

**What You Can Do:**
- Edit dbt SQL models directly
- Run dbt commands interactively
- Create data analysis notebooks
- Test pipeline changes
- Debug data issues
- Access all pipeline files

**Access Method:** No authentication required (development mode)

---

## **🗄️ Data & Processing Services**

### **7. 🚀 Apache Trino** - `http://localhost:8080`
**When to Use:**
- **Running SQL queries** against your data
- **Data exploration** and ad-hoc analysis
- **Testing dbt models** and transformations
- **Performance tuning** queries
- **Accessing Iceberg tables** with ACID capabilities

**What You Can Do:**
- Execute SQL queries
- View query execution plans
- Monitor query performance
- Access multiple data sources
- Run complex analytical queries
- Use Iceberg time travel features

**Access Method:** 
- HTTP API endpoints
- SQL client connections
- Username: `trino` (no password)

---

### **8. 🧊 Apache Iceberg**
**When to Use:**
- **ACID transactions** for data consistency
- **Schema evolution** without breaking changes
- **Time travel** and point-in-time queries
- **Partition management** for performance
- **Metadata management** and versioning

**What You Can Do:**
- Create transactional tables
- Evolve schemas safely
- Query data at specific points in time
- Optimize partition strategies
- Manage table metadata

**Access Method:** Via Trino SQL interface

---

### **9. 🔧 dbt (Data Build Tool)**
**When to Use:**
- **Building data models** and transformations
- **Running data pipelines** (seed, run, test)
- **Managing data quality** and testing
- **Documenting data lineage**

**What You Can Do:**
- Transform raw data into analytics-ready models
- Run data quality tests
- Generate data documentation
- Manage data dependencies
- Version control data transformations

**Access Methods:**
- **CLI**: From JupyterLab terminal or system terminal
- **Dashboard**: Via the platform dashboard
- **JupyterLab**: Interactive development and testing

---

### **10. 📦 MinIO (Object Storage)** - `http://localhost:9003`
**When to Use:**
- **Storing raw data files** (CSV, JSON, Parquet)
- **Backing up pipeline artifacts**
- **Storing model outputs** and results
- **Data lake functionality**

**What You Can Do:**
- Upload/download data files
- Organize data by folders
- Set up data lifecycle policies
- Access data via S3-compatible API
- Manage data access permissions

**Access Method:** 
- Username: `admin`
- Password: `admin123`

---

### **11. 🎯 Dagster** - `http://localhost:3000`
**When to Use:**
- **Orchestrating complex data pipelines**
- **Scheduling automated jobs**
- **Monitoring pipeline dependencies**
- **Managing data assets** and lineage

**What You Can Do:**
- Define pipeline workflows
- Schedule automated executions
- Monitor pipeline dependencies
- Track data asset lineage
- Set up alerts and notifications

**Access Method:** Web interface, no authentication required

---

### **12. 📈 Prometheus** - `http://localhost:9090`
**When to Use:**
- **Collecting system metrics** and performance data
- **Setting up monitoring** and alerting
- **Performance analysis** and optimization
- **Capacity planning**

**What You Can Do:**
- View system metrics
- Create custom queries
- Set up alerting rules
- Export metrics data
- Monitor service performance

**Access Method:** Web interface, no authentication required

---

## **🔄 Workflow Patterns**

### **🆕 New Data Pipeline Development**
1. **JupyterLab** - Develop and test dbt models
2. **Dashboard** - Run pipeline and monitor execution
3. **Data Browser** - Test queries and validate data
4. **Grafana** - Create visualizations and dashboards
5. **Trino** - Query and validate results

### **📊 Daily Operations**
1. **Dashboard** - Check platform health and pipeline status
2. **Data Browser** - Run ad-hoc queries and explore data
3. **Grafana** - Review business metrics and KPIs
4. **Portainer** - Monitor container health and performance
5. **JupyterLab** - Debug issues and make improvements

### **🔧 Troubleshooting**
1. **Dashboard** - Identify which service has issues
2. **Portainer** - Check container logs and status
3. **JupyterLab** - Test fixes and validate solutions
4. **Data Browser** - Verify data quality and consistency
5. **Trino** - Test query performance

### **📈 Performance Optimization**
1. **Prometheus** - Identify performance bottlenecks
2. **Grafana** - Visualize performance trends
3. **JupyterLab** - Optimize dbt models and queries
4. **Data Browser** - Test query variations
5. **Trino** - Analyze query execution plans

---

## **🔐 Security & Best Practices**

### **Development Environment**
- **No authentication** required for most services
- **Local access only** (localhost)
- **Suitable for development** and testing

### **Production Considerations**
- **Enable authentication** for all services
- **Use environment variables** for secrets
- **Implement network security** and firewalls
- **Regular security updates** and patches

---

## **📚 Learning Path**

### **Beginner Level**
1. Start with the **Dashboard** to understand platform status
2. Use **Data Browser** to explore data with simple queries
3. Use **JupyterLab** to explore data and run simple queries
4. Learn basic **dbt commands** and model development

### **Intermediate Level**
1. Create custom **Grafana dashboards**
2. Develop complex **dbt transformations**
3. Use **Trino** for advanced analytics
4. Explore **Iceberg** features and capabilities

### **Advanced Level**
1. **Orchestrate pipelines** with Dagster
2. **Optimize performance** using Prometheus metrics
3. **Implement data governance** and quality frameworks
4. **Design Iceberg table strategies** for performance

---

## **🎯 Quick Reference**

| Service | Port | Purpose | Access Method |
|---------|------|---------|---------------|
| Dashboard | 5000 | Platform monitoring & control | Browser |
| Data Browser | 5000 | Interactive SQL queries | Browser (integrated) |
| JupyterLab | 8888 | Interactive development | Browser |
| Grafana | 3000 | Visualization & BI | Browser + auth |
| Portainer | 9000 | Container management | Browser + auth |
| Trino | 8080 | SQL queries & analytics | HTTP API |
| MinIO | 9001 | Object storage | Browser + auth |
| Dagster | 3001 | Pipeline orchestration | Browser |
| Prometheus | 9090 | Metrics collection | Browser |
| Iceberg | - | Table format & metadata | Via Trino |

---

## **🚀 Getting Started Checklist**

- [ ] **Dashboard**: Verify all services are healthy
- [ ] **Data Browser**: Run a simple query to explore data
- [ ] **JupyterLab**: Open and explore your pipeline files
- [ ] **dbt**: Run a simple pipeline (seed → run → test)
- [ ] **Trino**: Execute a test query
- [ ] **Grafana**: Create your first dashboard
- [ ] **Portainer**: Familiarize yourself with container management
- [ ] **Iceberg**: Create your first Iceberg table

---

**🎉 Congratulations! You now have a complete, professional-grade data platform that rivals commercial solutions!**

**Your FOSS data platform provides enterprise-level capabilities with open-source tools, giving you full control over your data infrastructure while maintaining cost-effectiveness and flexibility.**
