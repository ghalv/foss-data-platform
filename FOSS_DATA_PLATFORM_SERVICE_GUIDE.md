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

**What You Can Do:**
- Check service health status
- View real-time system metrics
- Execute dbt pipeline commands
- Monitor pipeline performance
- Access business intelligence dashboards

**Access Method:** Open in browser, no authentication required

---

### **2. 📊 Grafana** - `http://localhost:3001`
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

### **3. 🐳 Portainer** - `http://localhost:9000`
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

### **4. 🔍 JupyterLab** - `http://localhost:8888`
**When to Use:**
- **Interactive data exploration** and analysis
- **Developing and testing** dbt models
- **Creating data notebooks** and documentation
- **Running ad-hoc queries** and experiments

**What You Can Do:**
- Edit dbt SQL models directly
- Run dbt commands interactively
- Create data analysis notebooks
- Test pipeline changes
- Debug data issues

**Access Method:** No authentication required (development mode)

---

## **🗄️ Data & Processing Services**

### **5. 🚀 Apache Trino** - `http://localhost:8080`
**When to Use:**
- **Running SQL queries** against your data
- **Data exploration** and ad-hoc analysis
- **Testing dbt models** and transformations
- **Performance tuning** queries

**What You Can Do:**
- Execute SQL queries
- View query execution plans
- Monitor query performance
- Access multiple data sources
- Run complex analytical queries

**Access Method:** 
- HTTP API endpoints
- SQL client connections
- Username: `trino` (no password)

---

### **6. 🔧 dbt (Data Build Tool)**
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

### **7. 📦 MinIO (Object Storage)** - `http://localhost:9002`
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

### **8. 🎯 Dagster** - `http://localhost:3000`
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

### **9. 📈 Prometheus** - `http://localhost:9090`
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
3. **Grafana** - Create visualizations and dashboards
4. **Trino** - Query and validate results

### **📊 Daily Operations**
1. **Dashboard** - Check platform health and pipeline status
2. **Grafana** - Review business metrics and KPIs
3. **Portainer** - Monitor container health and performance
4. **JupyterLab** - Debug issues and make improvements

### **🔧 Troubleshooting**
1. **Dashboard** - Identify which service has issues
2. **Portainer** - Check container logs and status
3. **JupyterLab** - Test fixes and validate solutions
4. **Trino** - Verify data quality and consistency

### **📈 Performance Optimization**
1. **Prometheus** - Identify performance bottlenecks
2. **Grafana** - Visualize performance trends
3. **JupyterLab** - Optimize dbt models and queries
4. **Trino** - Test query performance improvements

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
2. Use **JupyterLab** to explore data and run simple queries
3. Learn basic **dbt commands** and model development

### **Intermediate Level**
1. Create custom **Grafana dashboards**
2. Develop complex **dbt transformations**
3. Use **Trino** for advanced analytics

### **Advanced Level**
1. **Orchestrate pipelines** with Dagster
2. **Optimize performance** using Prometheus metrics
3. **Implement data governance** and quality frameworks

---

## **🎯 Quick Reference**

| Service | Port | Purpose | Access Method |
|---------|------|---------|---------------|
| Dashboard | 5000 | Platform monitoring & control | Browser |
| JupyterLab | 8888 | Interactive development | Browser |
| Grafana | 3001 | Visualization & BI | Browser + auth |
| Portainer | 9000 | Container management | Browser + auth |
| Trino | 8080 | SQL queries & analytics | HTTP API |
| MinIO | 9002 | Object storage | Browser + auth |
| Dagster | 3000 | Pipeline orchestration | Browser |
| Prometheus | 9090 | Metrics collection | Browser |

---

## **🚀 Getting Started Checklist**

- [ ] **Dashboard**: Verify all services are healthy
- [ ] **JupyterLab**: Open and explore your pipeline files
- [ ] **dbt**: Run a simple pipeline (seed → run → test)
- [ ] **Trino**: Execute a test query
- [ ] **Grafana**: Create your first dashboard
- [ ] **Portainer**: Familiarize yourself with container management

---

**🎉 Congratulations! You now have a complete, professional-grade data platform that rivals commercial solutions!**

**Your FOSS data platform provides enterprise-level capabilities with open-source tools, giving you full control over your data infrastructure while maintaining cost-effectiveness and flexibility.**
