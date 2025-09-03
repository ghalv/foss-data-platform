FROM python:3.11-slim

# Set working directory
WORKDIR /opt/dagster

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    dagster==1.6.0 \
    dagster-webserver==1.6.0 \
    dagster-dbt==0.22.0 \
    dagster-postgres==0.22.0 \
    pandas \
    requests

# Create dagster home directory
RUN mkdir -p /opt/dagster/dagster_home && chmod 755 /opt/dagster/dagster_home

# Set environment variables
ENV DAGSTER_HOME=/opt/dagster/dagster_home

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Default command
CMD ["dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]
