from dagster import (
    Definitions,
    asset,
    AssetExecutionContext,
    ScheduleDefinition,
    define_asset_job,
)
import pandas as pd
from datetime import datetime, timezone
import logging
import os
import numpy as np
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stavanger Parking API Configuration
STAVANGER_PARKING_API_URL = "https://opencom.no/dataset/36ceda99-bbc3-4909-bc52-b05a6d634b3f/resource/d1bdc6eb-9b49-4f24-89c2-ab9f5ce2acce/download/parking.json"

# Stavanger Parking Assets
@asset(
    name="stavanger_parking_raw",
    description="Raw parking data from Stavanger Parking API",
    group_name="stavanger_parking",
    compute_kind="python"
)
def fetch_stavanger_parking_raw() -> pd.DataFrame:
    """Fetch raw parking data from Stavanger Parking API."""

    try:
        logger.info(f"Fetching data from Stavanger Parking API: {STAVANGER_PARKING_API_URL}")

        # Fetch data from API
        response = requests.get(STAVANGER_PARKING_API_URL, timeout=30)
        response.raise_for_status()

        # Parse JSON data
        raw_data = response.json()
        logger.info(f"Received {len(raw_data)} records from API")

        # Define seed directory for delta comparison
        seed_dir = os.path.join(os.getcwd(), 'dbt_stavanger_parking', 'seeds')

        # Load previous data for delta comparison (if exists)
        previous_data_path = os.path.join(seed_dir, 'raw_parking_data.csv')
        has_previous_data = os.path.exists(previous_data_path)

        if has_previous_data:
            previous_df = pd.read_csv(previous_data_path)
            logger.info(f"Loaded {len(previous_df)} previous records for comparison")
        else:
            previous_df = pd.DataFrame()
            logger.info("No previous data found - this will be the baseline")

        # Convert to DataFrame
        df = pd.DataFrame(raw_data)

        # Rename columns to English and standardize format
        column_mapping = {
            'Dato': 'date',
            'Klokkeslett': 'time',
            'Sted': 'location',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Antall_ledige_plasser': 'available_spaces'
        }
        df = df.rename(columns=column_mapping)

        # Create timestamp from date and time
        df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%d.%m.%Y %H:%M')

        # Convert numeric fields
        df['available_spaces'] = pd.to_numeric(df['available_spaces'], errors='coerce')
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

        # Delta Detection Logic
        if has_previous_data and not previous_df.empty:
            # Compare current data with previous data
            changes_detected = detect_parking_changes(df, previous_df)
            logger.info(f"Delta analysis: {changes_detected}")

            # Store change summary for monitoring
            change_summary = {
                'total_locations': len(df),
                'previous_locations': len(previous_df),
                'locations_changed': changes_detected['locations_changed'],
                'avg_occupancy_change': changes_detected['avg_occupancy_change'],
                'timestamp': datetime.now(timezone.utc)
            }

            # Save change summary
            changes_dir = os.path.join(os.getcwd(), 'data', 'changes')
            os.makedirs(changes_dir, exist_ok=True)
            changes_file = os.path.join(changes_dir, f'changes_{timestamp}.json')
            with open(changes_file, 'w') as f:
                json.dump(change_summary, f, default=str, indent=2)

            logger.info(f"Detected changes: {changes_detected}")
        else:
            changes_detected = {'locations_changed': len(df), 'avg_occupancy_change': 0.0}

        # Add metadata
        df['data_source'] = 'stavanger_parking_api'
        df['ingestion_timestamp'] = datetime.now(timezone.utc)
        df['pipeline_run_id'] = f"pipeline_run_{int(datetime.now(timezone.utc).timestamp())}"

        # Save raw data for dbt seed with incremental approach
        os.makedirs(seed_dir, exist_ok=True)

        # For delta loads, save with timestamp partitioning
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        seed_path = os.path.join(seed_dir, f'raw_parking_data_{timestamp}.csv')

        # Save the full processed dataframe for dbt
        df.to_csv(seed_path, index=False)

        # Also maintain a latest snapshot for compatibility
        latest_path = os.path.join(seed_dir, 'raw_parking_data.csv')
        df.to_csv(latest_path, index=False)

        logger.info(f"Processed and saved {len(df)} records to {seed_path}")

        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error processing parking data: {str(e)}")
        raise

@asset(
    name="stavanger_parking_processed",
    description="Processed and cleaned Stavanger parking data",
    group_name="stavanger_parking"
)
def stavanger_parking_processed(stavanger_parking_raw: pd.DataFrame) -> pd.DataFrame:
    """Process and clean Stavanger parking data from raw API data."""

    try:
        logger.info("Processing raw parking data")

        # Start with the raw data
        df = stavanger_parking_raw.copy()

        # Process the data
        df = process_parking_data(df)

        # Save processed data
        output_dir = os.path.join(os.getcwd(), 'data', 'processed')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'stavanger_parking_processed.csv')
        df.to_csv(output_path, index=False)

        logger.info(f"Processed and saved {len(df)} parking records to {output_path}")
        return df

    except Exception as e:
        logger.error(f"Error processing parking data: {str(e)}")
        raise

# Removed test-data generator; pipeline must use live data seed

def process_parking_data(df):
    """Process and clean parking data from Stavanger API"""

    # Ensure timestamp is properly formatted
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Add additional derived fields for analysis
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['month'] = df['timestamp'].dt.month
    df['year'] = df['timestamp'].dt.year

    # Add location type classification
    df['location_type'] = df['location'].apply(classify_location_type)

    # Calculate basic occupancy metrics (we only have available spaces, not total)
    # For now, we'll use reasonable estimates for total capacity based on location
    df['estimated_total_capacity'] = df.apply(lambda row: estimate_total_capacity(row['location']), axis=1)
    df['estimated_occupied_spaces'] = df['estimated_total_capacity'] - df['available_spaces']
    df['estimated_occupancy_rate'] = (df['estimated_occupied_spaces'] / df['estimated_total_capacity'] * 100).round(2)

    # Add data quality indicators
    df['data_quality_score'] = calculate_data_quality(df)

    # Sort by timestamp
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')

    return df

def classify_location_type(location_name):
    """Classify parking location type based on name"""
    location_lower = str(location_name).lower()

    if any(keyword in location_lower for keyword in ['jernbanen', 'stasjon', 'station']):
        return 'transport_hub'
    elif any(keyword in location_lower for keyword in ['sentrum', 'center', 'forum']):
        return 'city_center'
    elif any(keyword in location_lower for keyword in ['shopping', 'handel']):
        return 'shopping'
    elif any(keyword in location_lower for keyword in ['park', 'green']):
        return 'recreational'
    else:
        return 'residential'

def estimate_total_capacity(location_name):
    """Estimate total parking capacity based on location characteristics"""
    # This is a rough estimation based on typical parking lot sizes
    # In a real implementation, this would come from a reference table
    location_lower = str(location_name).lower()

    if any(keyword in location_lower for keyword in ['jernbanen', 'stasjon']):
        return 400  # Train station - large capacity
    elif any(keyword in location_lower for keyword in ['forum', 'sentrum']):
        return 350  # City center - high capacity
    elif any(keyword in location_lower for keyword in ['shopping']):
        return 300  # Shopping center
    else:
        return 250  # Standard parking lot

def detect_parking_changes(current_df, previous_df):
    """Detect changes between current and previous parking data"""
    try:
        changes = {
            'locations_changed': 0,
            'occupancy_changes': [],
            'avg_occupancy_change': 0.0,
            'new_locations': [],
            'removed_locations': []
        }

        # Ensure both dataframes have the same structure for comparison
        if 'location' not in current_df.columns or 'location' not in previous_df.columns:
            return changes

        # Create lookup dictionaries for comparison
        current_lookup = {row['location']: row for _, row in current_df.iterrows()}
        previous_lookup = {row['location']: row for _, row in previous_df.iterrows()}

        # Find locations in current but not in previous (new locations)
        new_locations = set(current_lookup.keys()) - set(previous_lookup.keys())
        changes['new_locations'] = list(new_locations)

        # Find locations in previous but not in current (removed locations)
        removed_locations = set(previous_lookup.keys()) - set(current_lookup.keys())
        changes['removed_locations'] = list(removed_locations)

        # Compare occupancy changes for common locations
        common_locations = set(current_lookup.keys()) & set(previous_lookup.keys())
        occupancy_changes = []

        for location in common_locations:
            current_spaces = current_lookup[location].get('available_spaces', 0)
            previous_spaces = previous_lookup[location].get('available_spaces', 0)

            if current_spaces != previous_spaces:
                change = {
                    'location': location,
                    'previous_spaces': previous_spaces,
                    'current_spaces': current_spaces,
                    'change': current_spaces - previous_spaces
                }
                occupancy_changes.append(change)

        changes['locations_changed'] = len(occupancy_changes)
        changes['occupancy_changes'] = occupancy_changes

        # Calculate average occupancy change
        if occupancy_changes:
            total_change = sum(abs(change['change']) for change in occupancy_changes)
            changes['avg_occupancy_change'] = total_change / len(occupancy_changes)
        else:
            changes['avg_occupancy_change'] = 0.0

        return changes

    except Exception as e:
        logger.error(f"Error detecting parking changes: {str(e)}")
        return {
            'locations_changed': 0,
            'occupancy_changes': [],
            'avg_occupancy_change': 0.0,
            'new_locations': [],
            'removed_locations': [],
            'error': str(e)
        }

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

# Define job for periodic execution
stavanger_parking_job = define_asset_job(
    name="stavanger_parking_pipeline",
    selection=["stavanger_parking_raw", "stavanger_parking_processed"],
    description="Periodic pipeline to fetch and process Stavanger parking data"
)

# Define schedule to run every 15 minutes
stavanger_parking_schedule = ScheduleDefinition(
    job=stavanger_parking_job,
    cron_schedule="*/15 * * * *",  # Every 15 minutes
    name="stavanger_parking_schedule",
    description="Fetch Stavanger parking data every 15 minutes"
)

# Combine all assets
all_assets = [
    fetch_stavanger_parking_raw,
    stavanger_parking_processed,
]

# Define the Dagster definitions
defs = Definitions(
    assets=all_assets,
    jobs=[stavanger_parking_job],
    schedules=[stavanger_parking_schedule],
)

# Repository is defined by the defs variable
