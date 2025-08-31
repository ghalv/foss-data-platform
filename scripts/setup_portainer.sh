#!/bin/bash

# Portainer Setup Script
# This script sets up Portainer CE with persistent configuration

echo "🚀 Setting up Portainer CE with persistent configuration..."

# Create Portainer data directory if it doesn't exist
mkdir -p ./data/portainer

# Set proper permissions
chmod 755 ./data/portainer

echo "📁 Portainer data directory created: ./data/portainer"

echo ""
echo "🔧 Next Steps:"
echo "1. Go to http://localhost:9000"
echo "2. Create admin user with:"
echo "   - Username: admin"
echo "   - Password: admin123456789 (12+ characters)"
echo "3. Uncheck 'Allow collection of anonymous statistics'"
echo "4. Click 'Create User'"
echo ""
echo "💡 This setup will persist across container restarts!"
echo ""
echo "🔍 To verify setup, run: ./scripts/monitor_portainer.sh"
