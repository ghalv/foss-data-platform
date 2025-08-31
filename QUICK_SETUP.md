# 🚀 FOSS Data Platform - Quick Setup Guide

## ⚡ **Skip the Setup Wizards - Everything is Preconfigured!**

### **🎯 What's Already Set Up:**
- ✅ **Grafana**: Pre-configured dashboards and data sources
- ✅ **MinIO**: Pre-created buckets and users
- ✅ **Portainer**: Pre-configured admin user
- ✅ **JupyterLab**: Ready with authentication token
- ✅ **dbt-trino**: Fully integrated and tested
- ✅ **All Services**: Health checks and monitoring

### **🔑 Default Credentials:**

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| **Grafana** | http://localhost:3001 | `admin` | `admin123` |
| **MinIO** | http://localhost:9002 | `minioadmin` | `minioadmin123` |
| **Portainer** | http://localhost:9000 | `admin` | `admin123` |
| **JupyterLab** | http://localhost:8888/lab | Token: `fossdata123` | - |
| **Dashboard** | http://localhost:5000 | - | - |

### **🚀 Quick Start:**

1. **Start the Platform:**
   ```bash
   docker-compose up -d
   ```

2. **Initialize Services (One-time setup):**
   ```bash
   chmod +x scripts/init_services.sh
   ./scripts/init_services.sh
   ```

3. **Access Services:**
   - **Main Dashboard**: http://localhost:5000
   - **Grafana**: http://localhost:3001
   - **JupyterLab**: http://localhost:8888/lab?token=fossdata123

### **🔧 What's Preconfigured:**

#### **Grafana:**
- ✅ Prometheus data source
- ✅ Trino data source  
- ✅ FOSS Platform dashboard
- ✅ System metrics panels
- ✅ Container monitoring

#### **MinIO:**
- ✅ `raw-data` bucket
- ✅ `processed-data` bucket
- ✅ `analytics` bucket
- ✅ `backups` bucket
- ✅ `dbt-user` with read/write access

#### **Portainer:**
- ✅ Admin user ready
- ✅ Container management access
- ✅ No first-time setup required

#### **JupyterLab:**
- ✅ Authentication token configured
- ✅ Python environment ready
- ✅ dbt-trino integration tested

### **📊 Test Your Setup:**

```bash
# Test dbt-trino integration
python notebooks/test_dbt_trino.py

# Check service health
docker-compose ps
```

### **🎉 You're Ready!**

**No setup wizards, no configuration screens, no point-and-click setup required!**

All services are preconfigured and ready for:
- 📊 **Data Analysis** via JupyterLab
- 🔄 **Data Pipelines** via dbt-trino  
- 📈 **Monitoring** via Grafana
- 🗄️ **Storage** via MinIO
- 🐳 **Management** via Portainer

**Start building your data platform immediately!** 🚀
