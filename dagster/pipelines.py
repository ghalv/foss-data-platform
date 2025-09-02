from dagster import (
    Definitions,
    asset,
    AssetExecutionContext,
)
import pandas as pd
from datetime import datetime, timezone
import logging
import os
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stavanger Parking Assets
@asset(
    name="stavanger_parking_raw",
    description="Raw parking data from Stavanger Parking API",
    group_name="stavanger_parking",
    tags={"data_source": "stavanger_parking", "type": "raw"}
)
def fetch_stavanger_parking_raw(context: AssetExecutionContext) -> pd.DataFrame:
    """Load raw parking data from live seed written by ingestion."""

    try:
        seed_path = os.path.join(os.getcwd(), 'dbt_stavanger_parking', 'seeds', 'live_parking.csv')
        if not os.path.exists(seed_path):
            raise FileNotFoundError(f"Missing live data seed: {seed_path}")

        df = pd.read_csv(seed_path)

        # Add metadata
        df['data_source'] = 'stavanger_parking_live_seed'
        df['ingestion_timestamp'] = datetime.now(timezone.utc)
        df['pipeline_run_id'] = context.run_id

        logger.info(f"Loaded {len(df)} live records from {seed_path}")
        context.log.info(f"Loaded {len(df)} live records from seed")
        return df

    except Exception as e:
        logger.error(f"Error loading live parking data: {str(e)}")
        context.log.error(f"Failed to load live parking data: {str(e)}")
        raise

@asset
def stavanger_parking_data():
    """Process Stavanger parking data from live seed only (fail fast if missing)."""
    try:
        seed_path = os.path.join(os.getcwd(), 'dbt_stavanger_parking', 'seeds', 'live_parking.csv')
        if not os.path.exists(seed_path):
            raise FileNotFoundError(f"Missing live data seed: {seed_path}")

        df = pd.read_csv(seed_path)

        # Process the data
        df = process_parking_data(df)

        # Save processed data
        output_path = os.path.join(os.getcwd(), 'data', 'processed', 'stavanger_parking_processed.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)

        logger.info(f"Processed and saved {len(df)} parking records to {output_path}")
        return df

    except Exception as e:
        logger.error(f"Error processing live parking data: {e}")
        raise

# Removed test-data generator; pipeline must use live data seed

def process_parking_data(df):
    """Process and clean parking data"""
    # Ensure timestamp is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate occupancy percentage if not present
    if 'occupancy_percentage' not in df.columns and 'total_spaces' in df.columns and 'available_spaces' in df.columns:
        df['occupancy_percentage'] = ((df['total_spaces'] - df['available_spaces']) / df['total_spaces'] * 100).round(2)
    
    # Add data quality indicators
    df['data_quality_score'] = calculate_data_quality(df)
    
    # Sort by timestamp
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')
    
    return df

def calculate_data_quality(df):
    """Calculate data quality score based on actual data characteristics"""
    try:
        score = 100.0
        
        # Check for null values
        null_count = df.isnull().sum().sum()
        if null_count > 0:
            null_penalty = (null_count / (len(df) * len(df.columns))) * 20
            score -= null_penalty
        
        # Check for data consistency
        if 'occupancy_percentage' in df.columns:
            invalid_occupancy = len(df[df['occupancy_percentage'] < 0])
            if invalid_occupancy > 0:
                score -= (invalid_occupancy / len(df)) * 15
        
        # Check for reasonable data ranges
        if 'total_spaces' in df.columns:
            if df['total_spaces'].max() > 1000:  # Unrealistic parking lot size
                score -= 10
        
        return max(0, round(score, 1))
    except Exception as e:
        logger.error(f"Error calculating data quality: {e}")
        return 50.0  # Neutral score on error

# Combine all assets (temporarily without dbt)
all_assets = [
    fetch_stavanger_parking_raw,
    stavanger_parking_data,
]

# Define the Dagster definitions
defs = Definitions(
    assets=all_assets,
    jobs=[],
)

# Repository is defined by the defs variable
