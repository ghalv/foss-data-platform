#!/usr/bin/env python3
"""
JupyterLab Setup for dbt Integration
Adds magic commands for seamless pipeline management
"""

import os
import subprocess
from IPython import get_ipython
from IPython.core.magic import register_line_magic, register_cell_magic

def setup_dbt_magic():
    """Setup dbt magic commands in JupyterLab"""
    
    @register_line_magic
    def dbt(line):
        """Execute dbt commands from JupyterLab"""
        if not line.strip():
            print("Available dbt commands:")
            print("  %dbt run          - Run all models")
            print("  %dbt test         - Run all tests")
            print("  %dbt seed         - Load seeds")
            print("  %dbt docs         - Generate docs")
            print("  %dbt list         - List models")
            return
        
        try:
            # Change to dbt project directory
            project_dir = os.path.join(os.getcwd(), 'pipelines.stavanger_parking.dbt')
            if not os.path.exists(project_dir):
                project_dir = 'pipelines.stavanger_parking.dbt'
            
            # Execute dbt command
            result = subprocess.run(
                ['dbt'] + line.split(),
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                print("✅ Output:")
                print(result.stdout)
            
            if result.stderr:
                print("⚠️  Warnings/Errors:")
                print(result.stderr)
                
            if result.returncode == 0:
                print(f"✅ dbt {line} completed successfully")
            else:
                print(f"❌ dbt {line} failed with exit code {result.returncode}")
                
        except Exception as e:
            print(f"❌ Error executing dbt {line}: {e}")
    
    @register_cell_magic
    def dbt_run(line, cell):
        """Run dbt models with custom logic"""
        if line.strip():
            # Run specific model
            dbt(f"run --select {line}")
        else:
            # Run all models
            dbt("run")
    
    @register_cell_magic
    def dbt_test(line, cell):
        """Run dbt tests with custom logic"""
        if line.strip():
            # Run specific test
            dbt(f"test --select {line}")
        else:
            # Run all tests
            dbt("test")
    
    @register_line_magic
    def dbt_status(line):
        """Show dbt project status"""
        try:
            project_dir = os.path.join(os.getcwd(), 'pipelines.stavanger_parking.dbt')
            if not os.path.exists(project_dir):
                project_dir = 'pipelines.stavanger_parking.dbt'
            
            # List models
            result = subprocess.run(
                ['dbt', 'list'],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("📊 Available Models:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"  • {line.strip()}")
            else:
                print("❌ Failed to list models")
                
        except Exception as e:
            print(f"❌ Error getting dbt status: {e}")
    
    @register_line_magic
    def dbt_help(line):
        """Show dbt magic commands help"""
        help_text = """
🚀 **dbt Magic Commands for JupyterLab**

**Basic Commands:**
  %dbt run          - Run all models
  %dbt test         - Run all tests  
  %dbt seed         - Load seeds
  %dbt docs         - Generate docs
  %dbt list         - List models
  %dbt status       - Show project status

**Advanced Commands:**
  %%dbt_run         - Run models with custom logic
  %%dbt_test        - Run tests with custom logic

**Examples:**
  %dbt run --select tag:staging
  %dbt test --select test_critical_fields_not_null
  %dbt seed --select raw_parking_data

**Project Info:**
  %dbt_status       - List all available models
  %dbt_help         - Show this help
        """
        print(help_text)

def setup_pipeline_utilities():
    """Setup utility functions for pipeline management"""
    
    def get_pipeline_info():
        """Get current pipeline information"""
        try:
            import pandas as pd
            import requests
            
            # Try to get data from Trino
            query = "SELECT COUNT(*) as count FROM memory.default_staging.stg_parking_data"
            response = requests.post(
                'http://localhost:8080/v1/statement',
                json={'query': query},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if 'data' in result_data and result_data['data']:
                    record_count = result_data['data'][0][0]
                    print(f"📊 Pipeline Status: {record_count} records in staging")
                else:
                    print("📊 Pipeline Status: No data available")
            else:
                print("📊 Pipeline Status: Unable to connect to Trino")
                
        except Exception as e:
            print(f"📊 Pipeline Status: Error - {e}")
    
    # Add to global namespace
    globals()['get_pipeline_info'] = get_pipeline_info
    
    def show_pipeline_structure():
        """Show the pipeline structure"""
        structure = """
🏗️ **Stavanger Parking Pipeline Structure**

**Data Flow:**
  Raw Data → Staging → Intermediate → Marts → Business Intelligence

**Models:**
  📁 staging/
    └── stg_parking_data.sql
  📁 intermediate/
    └── int_daily_parking_metrics.sql
  📁 marts/
    ├── core/
    │   ├── dim_parking_locations.sql
    │   └── fct_parking_utilization.sql
    └── marketing/
        └── mart_parking_insights.sql

**Tests:**
  ✅ test_critical_fields_not_null
  ✅ test_capacity_occupancy_logic  
  ✅ test_utilization_rate_calculation

**Quick Start:**
  %dbt seed          # Load sample data
  %dbt run           # Run all models
  %dbt test          # Run all tests
  %dbt docs          # Generate documentation
        """
        print(structure)
    
    # Add to global namespace
    globals()['show_pipeline_structure'] = show_pipeline_structure

if __name__ == "__main__":
    # Setup magic commands
    setup_dbt_magic()
    setup_pipeline_utilities()
    
    print("🚀 dbt Magic Commands loaded successfully!")
    print("💡 Use %dbt_help to see available commands")
    print("📊 Use show_pipeline_structure() to see pipeline info")
    print("🔍 Use get_pipeline_info() to check current status")
else:
    # Auto-setup when imported
    setup_dbt_magic()
    setup_pipeline_utilities()
