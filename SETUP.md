# FOSS Data Platform Setup Guide

This guide will walk you through setting up your FOSS data platform on a Debian 12 VPS.

## Prerequisites

- Debian 12 VPS (minimum 2 vCPU, 4GB RAM recommended)
- SSH access to your VPS
- DigitalOcean account (or other cloud provider)
- Basic knowledge of Docker, Terraform, and Linux

## Step 1: Infrastructure Setup

### 1.1 Install Terraform

```bash
# Install Terraform
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs)"
sudo apt update
sudo apt install terraform
```

### 1.2 Configure Terraform

1. Create a `terraform.tfvars` file in the `infrastructure/` directory:

```bash
cd infrastructure
cat > terraform.tfvars << EOF
do_token = "your-digitalocean-api-token"
ssh_key_id = "your-ssh-key-id"
droplet_size = "s-2vcpu-4gb"
region = "nyc1"
admin_user = "admin"
admin_ssh_key = "ssh-rsa your-public-key-here"
EOF
```

2. Initialize and apply Terraform:

```bash
terraform init
terraform plan
terraform apply
```

3. Note the public IP address from the output.

### 1.3 SSH to Your VPS

```bash
ssh admin@<your-vps-ip>
```

## Step 2: Platform Deployment

### 2.1 Clone the Repository

```bash
git clone https://github.com/yourusername/foss-dataplatform.git
cd foss-dataplatform
```

### 2.2 Run the Deployment Script

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 2.3 Verify Services

The deployment script will check all services. You can also manually verify:

```bash
docker-compose ps
```

## Step 3: Initial Configuration

### 3.1 Update Passwords

Edit the `.env` file and update all default passwords:

```bash
nano .env
```

### 3.2 Configure Trino Catalogs

Create catalog configurations for your data sources:

```bash
# Create Iceberg catalog
mkdir -p config/trino/catalog
cat > config/trino/catalog/iceberg.properties << EOF
connector.name=iceberg
iceberg.catalog.type=hive
iceberg.catalog.warehouse=/data/iceberg
iceberg.catalog.uri=thrift://localhost:9083
EOF

# Create MinIO catalog
cat > config/trino/catalog/minio.properties << EOF
connector.name=hive
hive.metastore.uri=thrift://localhost:9083
hive.s3.endpoint=localhost:9000
hive.s3.aws-access-key=minioadmin
hive.s3.aws-secret-key=minioadmin123
hive.s3.path-style-access=true
EOF
```

### 3.3 Set up DBT

```bash
cd dbt
pip install -r ../requirements.txt
dbt deps
dbt debug
```

## Step 4: First Pipeline

### 4.1 Create a Simple Dagster Pipeline

```bash
cd ../dagster
```

Edit `pipelines.py` to add your first custom pipeline.

### 4.2 Test DBT Models

```bash
cd ../dbt
dbt run --select staging
dbt test
```

## Step 5: Monitoring Setup

### 5.1 Configure Grafana

1. Access Grafana at http://your-vps-ip:3001
2. Login with admin/admin123
3. Add Prometheus as a data source
4. Import basic dashboards for:
   - System metrics
   - Docker container metrics
   - Trino query performance

### 5.2 Set up Alerts

Configure basic alerts in Prometheus for:
- Service availability
- High memory usage
- Failed queries

## Step 6: Data Ingestion

### 6.1 Create Your First Dataset

```bash
cd notebooks
python platform_demo.py
```

### 6.2 Set up Data Sources

Configure connections to your data sources:
- Databases (PostgreSQL, MySQL, etc.)
- APIs
- File systems
- Message queues

## Troubleshooting

### Common Issues

1. **Services not starting**: Check Docker logs
   ```bash
   docker-compose logs [service-name]
   ```

2. **Port conflicts**: Ensure ports are not used by other services
   ```bash
   sudo netstat -tlnp | grep :8080
   ```

3. **Permission issues**: Check file permissions
   ```bash
   sudo chown -R $USER:$USER data/ config/
   ```

4. **Memory issues**: Increase swap or reduce service memory limits

### Performance Tuning

1. **Trino**: Adjust JVM settings in `config/trino/jvm.config`
2. **PostgreSQL**: Tune `shared_buffers` and `work_mem`
3. **Docker**: Limit resource usage per container

## Security Considerations

1. **Change default passwords** immediately
2. **Use HTTPS** in production
3. **Restrict network access** to necessary ports
4. **Regular updates** of all components
5. **Backup strategies** for data and configurations

## Scaling

### Vertical Scaling
- Increase VPS resources (CPU, RAM, storage)
- Optimize JVM and service configurations

### Horizontal Scaling
- Add more Trino workers
- Implement load balancing
- Use multiple VPS instances

## Maintenance

### Regular Tasks
- Monitor disk space and logs
- Update Docker images
- Backup configurations and data
- Review and optimize queries

### Updates
```bash
# Update all services
docker-compose pull
docker-compose up -d

# Update DBT
pip install --upgrade dbt-trino

# Update Terraform
terraform init -upgrade
```

## Support

- Check service logs: `docker-compose logs -f`
- Review monitoring dashboards
- Check service documentation
- Community forums and GitHub issues

## Next Steps

1. **Data Modeling**: Design your data models in DBT
2. **Pipeline Development**: Build complex data pipelines in Dagster
3. **Monitoring**: Set up comprehensive monitoring and alerting
4. **Security**: Implement proper authentication and authorization
5. **Backup**: Set up automated backup and recovery procedures

---

Your FOSS data platform is now ready for production use! 🎉
