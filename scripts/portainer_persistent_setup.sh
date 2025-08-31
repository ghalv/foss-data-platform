#!/bin/bash

# Portainer Persistent Setup Script
# This script ensures Portainer CE maintains its configuration

echo "🔧 Portainer CE Persistent Setup"
echo "================================"

# Check if Portainer is running
if ! docker-compose ps portainer | grep -q "Up"; then
    echo "❌ Portainer is not running. Starting it..."
    docker-compose up -d portainer
    sleep 15
fi

# Check if Portainer is accessible
if curl -s "http://localhost:9000/api/status" > /dev/null 2>&1; then
    echo "✅ Portainer is running and accessible"
    
    # Check if setup is still required
    if curl -s "http://localhost:9000" | grep -q "portainer.init.admin"; then
        echo "⚠️  Portainer still needs initial setup"
        echo ""
        echo "🔧 SETUP REQUIRED:"
        echo "1. Go to: http://localhost:9000"
        echo "2. Create admin user:"
        echo "   - Username: admin"
        echo "   - Password: admin123456789 (12+ characters)"
        echo "3. Uncheck 'Allow collection of anonymous statistics'"
        echo "4. Click 'Create User'"
        echo ""
        echo "💡 After setup, Portainer will never ask again!"
    else
        echo "✅ Portainer is already configured!"
        echo "🔗 Access at: http://localhost:9000"
    fi
else
    echo "❌ Portainer is not responding"
    echo "🔄 Restarting Portainer..."
    docker-compose restart portainer
    sleep 20
    
    if curl -s "http://localhost:9000/api/status" > /dev/null 2>&1; then
        echo "✅ Portainer restarted successfully"
    else
        echo "❌ Portainer restart failed"
        exit 1
    fi
fi

echo ""
echo "🔍 To monitor Portainer health: ./scripts/monitor_portainer.sh"
echo "📋 To check service status: docker-compose ps portainer"
