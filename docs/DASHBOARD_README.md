# 🚀 FOSS Data Platform Dashboard

## Overview

The FOSS Data Platform Dashboard is a web-based interface for managing and monitoring your data platform. It provides real-time insights into pipeline operations, data flows, and system health.

## Quick Start

### Automatic Startup (Recommended)
```bash
# From the project root directory
./scripts/start_dashboard.sh
```

This script will:
- ✅ **Check for existing instances** - Avoids duplicate processes
- ✅ **Test health** - Verifies if existing dashboard is working
- ✅ **Graceful shutdown** - Properly stops unhealthy processes
- ✅ **Port management** - Ensures port 5000 is available
- ✅ **Smart startup** - Only starts if needed

### Force Restart (If Needed)
```bash
# Force restart even if dashboard appears healthy
./scripts/start_dashboard.sh --restart
```

### Manual Startup (Not Recommended)
```bash
# Only use if startup script doesn't work
source .venv/bin/activate
cd dashboard
python app.py
```

### Monitoring and Health Checks
```bash
# Check dashboard status
./scripts/monitor_dashboard.sh

# Continuous monitoring (run in background)
while true; do ./scripts/monitor_dashboard.sh; sleep 300; done &
```

## Process Management & Instance Control

### 🛡️ Preventing Multiple Instances

The system includes **intelligent process management** to prevent resource conflicts and ensure clean operation:

#### 1. Smart Instance Detection
```bash
./scripts/start_dashboard.sh
# Output:
# [INFO] Checking for existing dashboard processes...
# [SUCCESS] Existing dashboard is healthy and responding!
# [INFO] Dashboard is available at: http://localhost:5000
# [INFO] No need to start a new instance
```

#### 2. Health-Based Decisions
- ✅ **Healthy instance exists** → Skip startup
- ⚠️ **Unhealthy instance exists** → Graceful shutdown + restart
- ❌ **No instance exists** → Start fresh

#### 3. Graceful Process Management
- **SIGTERM first** (graceful shutdown, 5-second timeout)
- **SIGKILL fallback** (force kill if graceful fails)
- **Resource cleanup** (removes zombie processes)

### Port Management

#### Ensuring Port 5000 is Always Available

The dashboard **only runs on port 5000** with intelligent conflict resolution:

#### 1. Using the Startup Script (Recommended)
```bash
./scripts/start_dashboard.sh
```
This automatically:
- Detects port conflicts
- Identifies conflicting processes
- Gracefully shuts them down
- Starts dashboard on clean port 5000

#### 2. Manual Port Management
```bash
# Check what's using port 5000
lsof -i :5000

# Kill process using port 5000
fuser -k 5000/tcp

# Or more forcefully
lsof -ti:5000 | xargs kill -9
```

#### 3. Systemd Service (For Production)
```bash
# Copy service file to systemd
sudo cp infrastructure/foss-dashboard.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable foss-dashboard
sudo systemctl start foss-dashboard

# Check status
sudo systemctl status foss-dashboard

# View logs
sudo systemctl logs foss-dashboard
```

### Monitoring & Auto-Recovery

#### Health Monitoring
```bash
# Check dashboard status manually
./scripts/monitor_dashboard.sh

# Continuous monitoring (every 5 minutes)
while true; do ./scripts/monitor_dashboard.sh; sleep 300; done &
```

#### Auto-Recovery Features
- **Health checks** every monitoring cycle
- **Automatic restart** if dashboard becomes unresponsive
- **Process cleanup** removes orphaned processes
- **Notification logging** for troubleshooting

#### Systemd Integration
The systemd service provides:
- **Automatic startup** on system boot
- **Process monitoring** with restart on failure
- **Resource limits** (1GB RAM, 50% CPU)
- **Security hardening** (NoNewPrivileges, PrivateTmp)
- **Comprehensive logging** to journald

## Features

### 🏗️ Medallion Architecture Visualization
- **Real-time pipeline flow** from ingestion to analytics
- **9-step data transformation** visualization
- **Color-coded layers**: Bronze (raw), Silver (clean), Gold (analytics)
- **Status indicators** for each processing step

### 📊 Dashboard Metrics
- **Pipeline health** monitoring
- **Data quality** indicators
- **Performance metrics** and KPIs
- **System resource** usage

### 🔧 Pipeline Management
- **Pipeline operations** (start, stop, monitor)
- **Configuration management**
- **Log viewing** and troubleshooting
- **Real-time status** updates

## URLs

- **Main Dashboard**: http://localhost:5000
- **Pipeline Management**: http://localhost:5000/pipeline-management
- **Data Browser**: http://localhost:5000/data-browser
- **Health Monitoring**: http://localhost:5000/health
- **API Documentation**: http://localhost:5000/chat

## Configuration

### Environment Variables
```bash
# Set production mode
export FLASK_ENV=production
export FLASK_DEBUG=false

# Custom port (if needed)
export FLASK_RUN_PORT=5000
```

### Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Troubleshooting

### Port 5000 Already in Use
```bash
# Automatic solution
./scripts/start_dashboard.sh

# Manual solution
pkill -f "python.*app.py"
lsof -ti:5000 | xargs kill -9
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Flask Won't Start
```bash
# Check for missing dependencies
pip list | grep -E "(flask|werkzeug|jinja)"

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### JavaScript Errors
- Hard refresh the browser: `Ctrl + Shift + R`
- Clear browser cache
- Check browser console for specific errors

## Development

### Running in Debug Mode
```bash
cd dashboard
export FLASK_DEBUG=true
python app.py
```

### Code Structure
```
dashboard/
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   ├── pipeline_management.html
│   ├── dashboard.html
│   └── ...
├── static/             # CSS, JS, images
└── api/                # API modules
    ├── query.py
    ├── ingestion.py
    └── ...
```

### Adding New Features
1. Create API endpoint in `dashboard/api/`
2. Add route in `dashboard/app.py`
3. Create/update template in `dashboard/templates/`
4. Add frontend JavaScript as needed

## Performance Optimization

### For Production Deployment
1. **Use Gunicorn** instead of Flask development server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Enable caching** for static files
3. **Use a reverse proxy** (nginx) for load balancing
4. **Set up monitoring** with proper logging

### Memory and CPU Usage
- Default limits: 1GB RAM, 50% CPU
- Adjust in `infrastructure/foss-dashboard.service` for production
- Monitor with `htop` or `top`

## Security Considerations

### Production Deployment
- Change default port if exposed to internet
- Use HTTPS with proper SSL certificates
- Implement authentication and authorization
- Regular security updates for dependencies

### Network Security
- Bind to localhost only if not exposing externally
- Use firewall rules to restrict access
- Monitor for suspicious activity

## Support

### Common Issues
1. **Port conflicts**: Use `./scripts/start_dashboard.sh`
2. **Virtual environment**: Recreate with `python -m venv .venv`
3. **Dependencies**: Reinstall with `pip install -r requirements.txt`
4. **Browser cache**: Hard refresh with `Ctrl + Shift + R`

### Logs and Debugging
```bash
# Flask logs (when running)
tail -f /tmp/flask.log

# System logs
journalctl -u foss-dashboard -f

# Python errors
python -c "import traceback; traceback.print_exc()"
```

## Architecture

The dashboard follows a **medallion architecture** approach:

```
Raw Data (Bronze) → Clean Data (Silver) → Analytics (Gold)
    ↓                    ↓                    ↓
Ingestion → Validation → Transformation → Aggregation → Reporting
```

This ensures data quality and provides multiple layers of insight for different user types.

---

**🎉 Your FOSS Data Platform Dashboard is now running reliably on port 5000!**
