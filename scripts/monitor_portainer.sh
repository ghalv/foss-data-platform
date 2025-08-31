#!/bin/bash

# Portainer Health Monitor Script
# This script checks if Portainer is responding and restarts it if needed

echo "🔍 Monitoring Portainer health..."

# Check if Portainer is responding
if curl -s "http://localhost:9000/api/status" > /dev/null 2>&1; then
    echo "✅ Portainer is healthy and responding"
    exit 0
else
    echo "❌ Portainer is not responding - restarting..."
    
    # Restart Portainer
    docker-compose restart portainer
    
    # Wait for it to start
    echo "⏳ Waiting for Portainer to start..."
    sleep 20
    
    # Check if it's working now
    if curl -s "http://localhost:9000/api/status" > /dev/null 2>&1; then
        echo "✅ Portainer restarted successfully"
        exit 0
    else
        echo "❌ Portainer restart failed"
        exit 1
    fi
fi
