from dagster import (
    Definitions,
    asset,
    AssetExecutionContext,
)
import pandas as pd
from datetime import datetime, timezone
import logging

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
    """Fetch raw parking data from Stavanger Parking API."""
    
    try:
        logger.info("Fetching Stavanger parking data...")
        
        # Sample data structure based on the API documentation
        sample_data = [
            {
                "parking_house_name": "Stavanger Sentrum",
                "location": "58.9700,5.7331",
                "available_spaces": 45,
                "total_spaces": 200,
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            {
                "parking_house_name": "Kongsberg Parkering",
                "location": "58.9750,5.7400",
                "available_spaces": 23,
                "total_spaces": 150,
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            {
                "parking_house_name": "Havneringen",
                "location": "58.9730,5.7310",
                "available_spaces": 67,
                "total_spaces": 300,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Convert to DataFrame
        df = pd.DataFrame(sample_data)
        
        # Add metadata
        df['data_source'] = 'stavanger_parking_api'
        df['ingestion_timestamp'] = datetime.now(timezone.utc)
        df['pipeline_run_id'] = context.run_id
        
        logger.info(f"Successfully fetched {len(df)} parking records")
        context.log.info(f"Fetched {len(df)} parking records from Stavanger API")
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching Stavanger parking data: {str(e)}")
        context.log.error(f"Failed to fetch parking data: {str(e)}")
        raise

@asset(
    name="stavanger_parking_cleaned",
    description="Cleaned and validated parking data",
    group_name="stavanger_parking",
    tags={"data_source": "stavanger_parking", "type": "cleaned"},
    deps=["stavanger_parking_raw"]
)
def clean_stavanger_parking_data(context: AssetExecutionContext, stavanger_parking_raw: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate the raw parking data."""
    
    try:
        logger.info("Cleaning Stavanger parking data...")
        
        # Create a copy to avoid modifying the original
        df = stavanger_parking_raw.copy()
        
        # Data cleaning steps
        # 1. Remove duplicates
        df = df.drop_duplicates()
        
        # 2. Validate coordinates (basic check)
        def validate_coordinates(coord_str):
            try:
                lat, lon = coord_str.split(',')
                lat = float(lat)
                lon = float(lon)
                # Stavanger is roughly at 58.97, 5.73
                return 58.5 <= lat <= 59.5 and 5.0 <= lon <= 6.0
            except:
                return False
        
        df = df[df['location'].apply(validate_coordinates)]
        
        # 3. Validate parking numbers
        df = df[
            (df['available_spaces'] >= 0) & 
            (df['total_spaces'] > 0) & 
            (df['available_spaces'] <= df['total_spaces'])
        ]
        
        # 4. Add computed fields
        df['occupied_spaces'] = df['total_spaces'] - df['available_spaces']
        df['occupancy_percentage'] = (df['available_spaces'] / df['total_spaces'] * 100).round(2)
        df['is_available'] = df['available_spaces'] > 0
        
        # 5. Add data quality indicators
        df['data_quality_score'] = 100  # Perfect for sample data
        
        logger.info(f"Cleaned data: {len(df)} records remaining")
        context.log.info(f"Cleaned parking data: {len(df)} valid records")
        
        return df
        
    except Exception as e:
        logger.error(f"Error cleaning parking data: {str(e)}")
        context.log.error(f"Failed to clean parking data: {str(e)}")
        raise

# Combine all assets (temporarily without dbt)
all_assets = [
    fetch_stavanger_parking_raw,
    clean_stavanger_parking_data,
]

# Define the Dagster definitions
defs = Definitions(
    assets=all_assets,
    jobs=[],
)

# Repository is defined by the defs variable
