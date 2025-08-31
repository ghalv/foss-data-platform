#!/bin/bash

set -e

echo "💾 FOSS Data Platform Backup Script"
echo "===================================="

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="foss-dataplatform-backup-${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

print_status "Starting backup: ${BACKUP_NAME}"

# 1. Backup Docker volumes
print_status "Backing up Docker volumes..."
docker run --rm -v foss-dataplatform_data:/data -v $(pwd)/${BACKUP_DIR}:/backup alpine tar czf /backup/volumes-${TIMESTAMP}.tar.gz -C /data .

# 2. Backup configuration files
print_status "Backing up configuration files..."
tar -czf "${BACKUP_DIR}/config-${TIMESTAMP}.tar.gz" \
    --exclude='data/*' \
    --exclude='*.tfstate*' \
    --exclude='.terraform' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='backups/*' \
    --exclude='logs/*' \
    .

# 3. Backup PostgreSQL database
print_status "Backing up PostgreSQL database..."
docker exec foss-dataplatform-postgres-1 pg_dump -U dagster dagster > "${BACKUP_DIR}/postgres-${TIMESTAMP}.sql"

# 4. Create backup manifest
print_status "Creating backup manifest..."
cat > "${BACKUP_DIR}/backup-manifest-${TIMESTAMP}.txt" << EOF
FOSS Data Platform Backup Manifest
==================================
Backup Date: $(date)
Backup Name: ${BACKUP_NAME}
Platform Version: $(git describe --tags --always 2>/dev/null || echo "Unknown")

Contents:
- Docker volumes: volumes-${TIMESTAMP}.tar.gz
- Configuration: config-${TIMESTAMP}.tar.gz
- PostgreSQL: postgres-${TIMESTAMP}.sql

Services Status:
$(docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}")

System Info:
- OS: $(uname -a)
- Docker: $(docker --version)
- Docker Compose: $(docker-compose --version)
EOF

# 5. Create final backup archive
print_status "Creating final backup archive..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" \
    "volumes-${TIMESTAMP}.tar.gz" \
    "config-${TIMESTAMP}.tar.gz" \
    "postgres-${TIMESTAMP}.sql" \
    "backup-manifest-${TIMESTAMP}.txt"

# Clean up individual files
rm "volumes-${TIMESTAMP}.tar.gz" "config-${TIMESTAMP}.tar.gz" "postgres-${TIMESTAMP}.sql" "backup-manifest-${TIMESTAMP}.txt"

cd ..

# 6. Show backup summary
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
print_status "Backup completed successfully!"
echo ""
echo "Backup Details:"
echo "  Name: ${BACKUP_NAME}.tar.gz"
echo "  Location: ${BACKUP_DIR}/"
echo "  Size: ${BACKUP_SIZE}"
echo "  Timestamp: ${TIMESTAMP}"
echo ""

# 7. Cleanup old backups (keep last 5)
print_status "Cleaning up old backups (keeping last 5)..."
cd "${BACKUP_DIR}"
ls -t *.tar.gz | tail -n +6 | xargs -r rm -f
cd ..

print_status "Backup process completed! 🎉"
