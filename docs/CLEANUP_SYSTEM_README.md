# 🧹 FOSS Data Platform - Cleanup System

Automated garbage collection and retention management for pipeline operations, logs, and temporary files.

## 🎯 Overview

The cleanup system automatically manages the lifecycle of pipeline operations data to:
- **Reduce storage costs** by removing old operation files
- **Improve performance** by reducing database and filesystem clutter
- **Maintain compliance** with configurable data retention policies
- **Provide safety** with backups and dry-run capabilities

## 📋 Features

### ✅ Automated Cleanup
- **Scheduled execution** (runs daily at 2 AM)
- **Configurable retention periods** per data type
- **Safe deletion** with automatic backups
- **Comprehensive logging** and audit trails

### ✅ Manual Control
- **Dry-run mode** to preview cleanup actions
- **Web UI integration** in Pipeline Management page
- **Command-line interface** for scripting
- **Emergency cleanup** capabilities

### ✅ Safety Features
- **Automatic backups** before deletion
- **Audit logging** of all cleanup actions
- **Rollback capability** via backup files
- **Dry-run validation** before live execution

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │   Cleanup Script │    │   PostgreSQL    │
│                 │    │                  │    │   Database      │
│ • Manual cleanup│───▶│ • File scanning  │───▶│ • Retention     │
│ • Policy config │    │ • Safe deletion  │    │   policies      │
│ • Statistics    │    │ • Backup creation│    │ • Audit logs    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────┐
                    │   Operation Files   │
                    │   (/tmp/*.json)     │
                    │                     │
                    │ • Pipeline runs     │
                    │ • Progress data     │
                    │ • Temporary files   │
                    └─────────────────────┘
```

## 📊 Default Retention Policies

| Data Type | Retention Period | Purpose |
|-----------|------------------|---------|
| Pipeline Operations | 30 days | Execution records and progress files |
| DBT Logs | 7 days | Transformation logs and artifacts |
| Failed Operations | 14 days | Failed pipeline operations (kept longer for debugging) |
| Completed Operations | 90 days | Successfully completed operations |
| System Logs | 30 days | Application and system logs |
| Temp Files | 1 day | Temporary files and cache |

## 🚀 Quick Start

### 1. Test the System
```bash
# Test all cleanup components
python scripts/test_cleanup_system.py

# Expected output: All tests passed ✅
```

### 2. Dry Run (Safe Preview)
```bash
# See what would be cleaned without actually deleting
python scripts/cleanup_operations.py --dry-run

# Or via Docker
docker-compose exec cleanup-scheduler \
  python /scripts/cleanup_operations.py --dry-run --db-host postgres
```

### 3. Live Cleanup
```bash
# Actually perform cleanup (with confirmation prompts)
python scripts/cleanup_operations.py --run

# Or emergency cleanup (bypasses some safety checks)
python scripts/cleanup_operations.py --run --type emergency
```

### 4. Check Statistics
```bash
# View cleanup statistics and history
python scripts/cleanup_operations.py --stats

# View current retention policies
python scripts/cleanup_operations.py --config
```

## 🖥️ Web Interface

### Pipeline Management Page
Access the cleanup system through the Pipeline Management page (`/pipeline-management`):

1. **Cleanup Overview Cards**
   - Files to clean count
   - Space saved metrics
   - Last cleanup timestamp

2. **Retention Policies**
   - View current policies
   - Enable/disable policies
   - Modify retention periods

3. **Manual Cleanup**
   - **Dry Run**: Preview what will be cleaned
   - **Run Cleanup**: Execute cleanup with confirmation

4. **Cleanup History**
   - Recent cleanup actions
   - Files deleted count
   - Space freed metrics

### Configuration Modal
Click the ⚙️ settings button to configure retention policies:

- **Pipeline Operations**: How long to keep operation files
- **Failed Operations**: Extended retention for debugging
- **System Logs**: Application log retention
- **Temp Files**: Very short retention for cache files

## ⚙️ Configuration

### Database Configuration
The system uses PostgreSQL tables:
- `cleanup_policies`: Retention policy definitions
- `cleanup_audit`: Cleanup action history

### File Locations
- **Scripts**: `scripts/cleanup_operations.py`
- **Database Schema**: `config/postgres/init_cleanup.sql`
- **Backups**: `/tmp/cleanup_backups/` (auto-created)
- **Operation Files**: `/tmp/operation_*.json`

### Docker Integration
The cleanup scheduler runs automatically in Docker:

```yaml
cleanup-scheduler:
  image: alpine:latest
  command: >
    sh -c "
      echo '0 2 * * * /scripts/cleanup_operations.py --run --type automatic' > /etc/crontabs/root &&
      crond -f -l 8
    "
```

## 📈 Monitoring & Maintenance

### Health Checks
```bash
# Check cleanup system status
python scripts/test_cleanup_system.py

# View recent cleanup activity
python scripts/cleanup_operations.py --stats
```

### Log Locations
- **Application Logs**: `/tmp/cleanup_backups/cleanup_*.log`
- **Database Audit**: PostgreSQL `cleanup_audit` table
- **Docker Logs**: `docker-compose logs cleanup-scheduler`

### Backup Management
- **Automatic Backups**: Created in `/tmp/cleanup_backups/`
- **Backup Retention**: Backups are kept for 7 days
- **Manual Cleanup**: `rm -rf /tmp/cleanup_backups/` (use with caution)

## 🔧 Troubleshooting

### Common Issues

**❌ Database Connection Failed**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

**❌ No Operation Files Found**
```bash
# Check if files exist
ls -la /tmp/operation_*.json

# Run pipeline to generate test files
# Then check again
ls -la /tmp/operation_*.json
```

**❌ Permission Denied**
```bash
# Make scripts executable
chmod +x scripts/cleanup_operations.py
chmod +x scripts/test_cleanup_system.py

# Check Docker volume permissions
docker-compose exec cleanup-scheduler ls -la /scripts/
```

**❌ Cleanup Not Running**
```bash
# Check cron status
docker-compose exec cleanup-scheduler crontab -l

# Manual trigger
docker-compose exec cleanup-scheduler \
  python /scripts/cleanup_operations.py --run --type manual
```

### Recovery Procedures

**Restore from Backup**
```bash
# List available backups
ls -la /tmp/cleanup_backups/

# Restore specific file
cp /tmp/cleanup_backups/operation_xyz.json.backup /tmp/operation_xyz.json
```

**Reset Retention Policies**
```sql
-- Connect to PostgreSQL
psql -h localhost -p 5433 -U dagster -d dagster

-- Reset to defaults
TRUNCATE cleanup_policies;
-- Then re-run init_cleanup.sql
```

## 🔐 Security Considerations

- **Database Access**: Uses existing PostgreSQL credentials
- **File Permissions**: Scripts require execute permissions
- **Backup Security**: Backups contain sensitive operation data
- **Audit Logging**: All cleanup actions are logged
- **Dry-run Safety**: Always test with `--dry-run` first

## 📚 API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cleanup/stats` | GET | Get cleanup statistics |
| `/api/cleanup/policies` | GET | Get retention policies |
| `/api/cleanup/policies` | POST | Update retention policy |
| `/api/cleanup/run` | POST | Trigger manual cleanup |
| `/api/cleanup/files` | GET | List operation files |

### Command Line Options

```bash
cleanup_operations.py [OPTIONS]

Options:
  --dry-run          Show what would be cleaned
  --run              Actually perform cleanup
  --type TYPE        Cleanup type (automatic, manual, emergency)
  --stats            Show cleanup statistics
  --config           Show retention policies
  --db-host HOST     Database host (default: localhost)
  --db-port PORT     Database port (default: 5433)
  --db-name NAME     Database name (default: dagster)
  --db-user USER     Database user (default: dagster)
  --db-password PASS Database password
```

## 🎯 Best Practices

### Operational Guidelines
1. **Always run dry-run first** before live cleanup
2. **Monitor cleanup logs** regularly for issues
3. **Review retention policies** quarterly
4. **Backup important data** before major cleanup operations
5. **Test recovery procedures** annually

### Performance Optimization
- **Schedule during off-hours** (default: 2 AM)
- **Monitor disk space** before and after cleanup
- **Adjust retention periods** based on business needs
- **Archive old data** if historical analysis is needed

### Compliance Considerations
- **Data Retention Laws**: Adjust policies per jurisdiction
- **Audit Requirements**: Enable comprehensive logging
- **Backup Policies**: Align with organizational standards
- **Access Controls**: Limit cleanup permissions appropriately

---

## 🚨 Emergency Procedures

### Immediate Shutdown
```bash
# Stop cleanup scheduler
docker-compose stop cleanup-scheduler

# Disable automatic cleanup
docker-compose exec postgres psql -U dagster -d dagster \
  -c "UPDATE cleanup_policies SET enabled = false;"
```

### Data Recovery
```bash
# Restore from backups
cp /tmp/cleanup_backups/*.backup /tmp/

# Re-enable policies
docker-compose exec postgres psql -U dagster -d dagster \
  -c "UPDATE cleanup_policies SET enabled = true WHERE data_type = 'pipeline_operations';"
```

---

**🧹 Keep your data platform clean and efficient with automated cleanup!**
