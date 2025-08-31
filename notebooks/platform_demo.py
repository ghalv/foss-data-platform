#!/usr/bin/env python3
"""
FOSS Data Platform Demo Script

This script demonstrates the basic functionality of your FOSS data platform.
Run it to check service health and see sample data processing.
"""

import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime
import time

def print_header():
    """Print a nice header for the demo"""
    print("=" * 60)
    print("🚀 FOSS Data Platform Demo")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_service_health(service_name, url, expected_status=200):
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            return f"✅ {service_name}: Healthy"
        else:
            return f"⚠️  {service_name}: Status {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"❌ {service_name}: {str(e)}"

def platform_health_check():
    """Check the health of all platform services"""
    print("🔍 Platform Health Check:")
    print("-" * 30)
    
    services = {
        "Dagster": "http://localhost:3000",
        "Grafana": "http://localhost:3001",
        "Trino": "http://localhost:8080",
        "MinIO": "http://localhost:9000",
        "Prometheus": "http://localhost:9090"
    }
    
    for service, url in services.items():
        status = check_service_health(service, url)
        print(status)
        time.sleep(0.5)  # Small delay between checks
    
    print()

def generate_sample_data():
    """Generate and display sample data"""
    print("📊 Sample Data Generation:")
    print("-" * 30)
    
    # Generate sample time series data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # Create sample metrics
    data = {
        'date': dates,
        'metric_1': np.random.normal(100, 15, 100),
        'metric_2': np.random.exponential(50, 100),
        'metric_3': np.random.poisson(25, 100),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    }
    
    df = pd.DataFrame(data)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Columns: {list(df.columns)}")
    print()
    
    print("First 5 rows:")
    print(df.head())
    print()
    
    print("Basic statistics:")
    print(df.describe())
    print()
    
    return df

def demonstrate_data_operations(df):
    """Demonstrate various data operations"""
    print("🔧 Data Operations Demo:")
    print("-" * 30)
    
    # Group by category
    print("Group by category:")
    grouped = df.groupby('category').agg({
        'metric_1': ['mean', 'std'],
        'metric_2': ['mean', 'std'],
        'metric_3': ['mean', 'std']
    }).round(2)
    print(grouped)
    print()
    
    # Rolling statistics
    print("Rolling 7-day average for metric_1:")
    rolling_avg = df['metric_1'].rolling(window=7).mean()
    print(f"Latest 7-day avg: {rolling_avg.iloc[-1]:.2f}")
    print()
    
    # Correlation analysis
    print("Correlation between metrics:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    corr_matrix = df[numeric_cols].corr()
    print(corr_matrix.round(3))
    print()

def show_platform_info():
    """Display platform information and next steps"""
    print("📋 Platform Information:")
    print("-" * 30)
    
    print("Services available at:")
    print("  • JupyterLab: http://localhost:8888")
    print("  • Dagster: http://localhost:3000")
    print("  • Grafana: http://localhost:3001 (admin/admin123)")
    print("  • Trino: http://localhost:8080")
    print("  • MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)")
    print("  • Prometheus: http://localhost:9090")
    print()
    
    print("Next steps:")
    print("  1. Update passwords in .env file")
    print("  2. Configure your data sources in DBT")
    print("  3. Set up your first Dagster pipeline")
    print("  4. Create your first Jupyter notebook")
    print("  5. Set up monitoring dashboards in Grafana")
    print()
    
    print("Platform features:")
    print("  • Scalable: Built with distributed computing principles")
    print("  • FOSS: All components are open-source")
    print("  • Modern: Uses current best practices and tools")
    print("  • Lean: Minimal resource footprint")
    print("  • High-performing: Optimized for speed and efficiency")

def main():
    """Main demo function"""
    print_header()
    
    # Check platform health
    platform_health_check()
    
    # Generate and analyze sample data
    df = generate_sample_data()
    demonstrate_data_operations(df)
    
    # Show platform information
    show_platform_info()
    
    print("=" * 60)
    print("🎉 Demo complete! Your FOSS data platform is ready to use.")
    print("=" * 60)

if __name__ == "__main__":
    main()
