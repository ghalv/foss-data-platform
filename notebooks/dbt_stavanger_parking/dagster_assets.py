"""
Dagster Assets for Stavanger Parking Data Pipeline
Orchestrates the complete data pipeline from ingestion to business intelligence
"""

from dagster import (
    asset,
    AssetExecutionContext,
    AssetIn,
    AssetOut,
    multi_asset,
    Output,
    Config,
    MetadataValue,
    asset_key_from_path
)
from typing import Dict, Any, List
import subprocess
import os
import json
from datetime import datetime

class DbtConfig(Config):
    """Configuration for dbt operations"""
    project_dir: str = "dbt_stavanger_parking"
    target: str = "dev"
    select: str = "*"

@asset(
    description="Download and validate Stavanger parking data from OpenCom.no",
    tags=["ingestion", "parking", "data-quality"],
    group_name="ingestion"
)
def raw_parking_data(context: AssetExecutionContext) -> Dict[str, Any]:
    """Download raw parking data and perform initial validation"""
    
    try:
        context.log.info("Starting Stavanger parking data ingestion...")
        
        # Change to dbt project directory
        os.chdir(context.config.project_dir)
        
        # Run data ingestion script
        result = subprocess.run(
            ["python", "scripts/download_data.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("Data ingestion completed successfully")
        context.log.info(f"Script output: {result.stdout}")
        
        # Read metadata to get record count
        metadata_path = "seeds/metadata.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return {
                "status": "success",
                "record_count": metadata.get("record_count", 0),
                "columns": metadata.get("columns", []),
                "download_timestamp": metadata.get("download_timestamp"),
                "source_url": metadata.get("source_url")
            }
        else:
            return {
                "status": "success",
                "record_count": 0,
                "message": "Metadata file not found"
            }
            
    except subprocess.CalledProcessError as e:
        context.log.error(f"Data ingestion failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during ingestion: {str(e)}")
        raise

@asset(
    description="Load raw data into dbt seeds",
    tags=["dbt", "seeds", "parking"],
    group_name="dbt_processing",
    deps=[raw_parking_data]
)
def dbt_seeds(context: AssetExecutionContext) -> Dict[str, Any]:
    """Load raw data into dbt seeds"""
    
    try:
        context.log.info("Loading dbt seeds...")
        
        # Change to dbt project directory
        os.chdir(context.config.project_dir)
        
        # Run dbt seed
        result = subprocess.run(
            ["dbt", "seed", "--target", context.config.target],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("dbt seeds loaded successfully")
        
        return {
            "status": "success",
            "operation": "dbt_seed",
            "target": context.config.target,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.CalledProcessError as e:
        context.log.error(f"dbt seed failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during dbt seed: {str(e)}")
        raise

@asset(
    description="Run dbt staging models",
    tags=["dbt", "staging", "parking"],
    group_name="dbt_processing",
    deps=[dbt_seeds]
)
def dbt_staging_models(context: AssetExecutionContext) -> Dict[str, Any]:
    """Run dbt staging models"""
    
    try:
        context.log.info("Running dbt staging models...")
        
        # Change to dbt project directory
        os.chdir(context.config.project_dir)
        
        # Run dbt models with staging tag
        result = subprocess.run(
            ["dbt", "run", "--target", context.config.target, "--select", "tag:staging"],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("dbt staging models completed successfully")
        
        return {
            "status": "success",
            "operation": "dbt_staging",
            "target": context.config.target,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.CalledProcessError as e:
        context.log.error(f"dbt staging models failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during dbt staging: {str(e)}")
        raise

@asset(
    description="Run dbt intermediate models",
    tags=["dbt", "intermediate", "parking"],
    group_name="dbt_processing",
    deps=[dbt_staging_models]
)
def dbt_intermediate_models(context: AssetExecutionContext) -> Dict[str, Any]:
    """Run dbt intermediate models"""
    
    try:
        context.log.info("Running dbt intermediate models...")
        
        # Change to dbt project directory
        os.chdir(context.config.project_dir)
        
        # Run dbt models with intermediate tag
        result = subprocess.run(
            ["dbt", "run", "--target", context.config.target, "--select", "tag:intermediate"],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("dbt intermediate models completed successfully")
        
        return {
            "status": "success",
            "operation": "dbt_intermediate",
            "target": context.config.target,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.CalledProcessError as e:
        context.log.error(f"dbt intermediate models failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during dbt intermediate: {str(e)}")
        raise

@asset(
    description="Run dbt mart models",
    tags=["dbt", "marts", "parking"],
    group_name="dbt_processing",
    deps=[dbt_intermediate_models]
)
def dbt_mart_models(context: AssetExecutionContext) -> Dict[str, Any]:
    """Run dbt mart models"""
    
    try:
        context.log.info("Running dbt mart models...")
        
        # Change to dbt project directory
        os.chdir(context.config.project_dir)
        
        # Run dbt models with marts tag
        result = subprocess.run(
            ["dbt", "run", "--target", context.config.target, "--select", "tag:marts"],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("dbt mart models completed successfully")
        
        return {
            "status": "success",
            "operation": "dbt_marts",
            "target": context.config.target,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.CalledProcessError as e:
        context.log.error(f"dbt mart models failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during dbt marts: {str(e)}")
        raise

@asset(
    description="Run dbt tests for data quality validation",
    tags=["dbt", "testing", "parking", "data-quality"],
    group_name="quality_assurance",
    deps=[dbt_mart_models]
)
def dbt_tests(context: AssetExecutionContext) -> Dict[str, Any]:
    """Run dbt tests for data quality validation"""
    
    try:
        context.log.info("Running dbt tests...")
        
        # Change to dbt project directory
        os.chdir(context.config.project_dir)
        
        # Run dbt tests
        result = subprocess.run(
            ["dbt", "test", "--target", context.config.target],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("dbt tests completed successfully")
        
        return {
            "status": "success",
            "operation": "dbt_test",
            "target": context.config.target,
            "timestamp": datetime.now().isoformat(),
            "test_output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        context.log.error(f"dbt tests failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during dbt tests: {str(e)}")
        raise

@asset(
    description="Generate dbt documentation",
    tags=["dbt", "documentation", "parking"],
    group_name="documentation",
    deps=[dbt_tests]
)
def dbt_documentation(context: AssetExecutionContext) -> Dict[str, Any]:
    """Generate dbt documentation"""
    
    try:
        context.log.info("Generating dbt documentation...")
        
        # Change to dbt project directory
        os.chdir(context.config.project_dir)
        
        # Generate dbt docs
        result = subprocess.run(
            ["dbt", "docs", "generate", "--target", context.config.target],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("dbt documentation generated successfully")
        
        return {
            "status": "success",
            "operation": "dbt_docs_generate",
            "target": context.config.target,
            "timestamp": datetime.now().isoformat(),
            "docs_path": "target/index.html"
        }
        
    except subprocess.CalledProcessError as e:
        context.log.error(f"dbt documentation generation failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during documentation generation: {str(e)}")
        raise

@asset(
    description="Complete Stavanger parking data pipeline",
    tags=["pipeline", "parking", "complete"],
    group_name="pipeline_summary",
    deps=[dbt_documentation]
)
def parking_pipeline_complete(context: AssetExecutionContext) -> Dict[str, Any]:
    """Complete pipeline summary and status"""
    
    context.log.info("🎉 Stavanger Parking Data Pipeline completed successfully!")
    
    return {
        "status": "complete",
        "pipeline_name": "Stavanger Parking Data Pipeline",
        "completion_timestamp": datetime.now().isoformat(),
        "components": [
            "raw_data_ingestion",
            "dbt_seeds",
            "staging_models",
            "intermediate_models",
            "mart_models",
            "data_quality_tests",
            "documentation"
        ],
        "business_value": [
            "Real-time parking utilization insights",
            "Business recommendations for capacity planning",
            "Revenue optimization opportunities",
            "Strategic location analysis"
        ],
        "next_steps": [
            "Review business insights in marts",
            "Create Grafana dashboards",
            "Set up automated scheduling",
            "Monitor data quality metrics"
        ]
    }
