#!/usr/bin/env python3
"""
Delta Loading Implementation for Stavanger Parking Data Platform

This script demonstrates how to implement intelligent delta loading
that leverages the full power of the Dagster + dbt + Trino + Iceberg stack.
"""

import pandas as pd
import requests
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import os

# Configuration
STAVANGER_API_URL = "https://opencom.no/dataset/36ceda99-bbc3-4909-bc52-b05a6d634b3f/resource/d1bdc6eb-9b49-4f24-89c2-ab9f5ce2acce/download/parking.json"
DATA_DIR = Path(__file__).parent.parent / "data"
SEEDS_DIR = Path(__file__).parent.parent / "dbt_stavanger_parking" / "seeds"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeltaLoadingEngine:
    """Intelligent delta loading engine for parking data"""

    def __init__(self):
        self.api_url = STAVANGER_API_URL
        self.data_dir = DATA_DIR
        self.seeds_dir = SEEDS_DIR
        self.setup_directories()

    def setup_directories(self):
        """Create necessary directories"""
        self.data_dir.mkdir(exist_ok=True)
        self.seeds_dir.mkdir(exist_ok=True)
        (self.data_dir / "changes").mkdir(exist_ok=True)
        (self.data_dir / "partitions").mkdir(exist_ok=True)

    def fetch_current_data(self):
        """Fetch current parking data from API"""
        logger.info(f"Fetching data from {self.api_url}")
        response = requests.get(self.api_url, timeout=30)
        response.raise_for_status()
        return response.json()

    def load_previous_data(self):
        """Load previous dataset for comparison"""
        latest_file = self.seeds_dir / "raw_parking_data.csv"
        if latest_file.exists():
            return pd.read_csv(latest_file)
        return pd.DataFrame()

    def detect_changes(self, current_df, previous_df):
        """Detect changes between datasets"""
        if previous_df.empty:
            return {
                'has_changes': True,
                'change_type': 'baseline',
                'changed_locations': len(current_df),
                'new_locations': list(current_df['location']),
                'removed_locations': [],
                'occupancy_changes': []
            }

        # Create lookup dictionaries
        current_lookup = {row['location']: row for _, row in current_df.iterrows()}
        previous_lookup = {row['location']: row for _, row in previous_df.iterrows()}

        # Find changes
        new_locations = set(current_lookup.keys()) - set(previous_lookup.keys())
        removed_locations = set(previous_lookup.keys()) - set(current_lookup.keys())
        common_locations = set(current_lookup.keys()) & set(previous_lookup.keys())

        occupancy_changes = []
        for location in common_locations:
            current_spaces = current_lookup[location].get('available_spaces', 0)
            previous_spaces = previous_lookup[location].get('available_spaces', 0)

            if abs(current_spaces - previous_spaces) > 0:  # Any change
                occupancy_changes.append({
                    'location': location,
                    'change': current_spaces - previous_spaces,
                    'current': current_spaces,
                    'previous': previous_spaces
                })

        return {
            'has_changes': len(occupancy_changes) > 0 or len(new_locations) > 0 or len(removed_locations) > 0,
            'change_type': 'delta',
            'changed_locations': len(occupancy_changes),
            'new_locations': list(new_locations),
            'removed_locations': list(removed_locations),
            'occupancy_changes': occupancy_changes,
            'total_change_magnitude': sum(abs(change['change']) for change in occupancy_changes)
        }

    def should_process_delta(self, changes):
        """Determine if changes warrant processing"""
        # Process if:
        # 1. New locations added/removed
        # 2. Significant occupancy changes (>5% of locations)
        # 3. Large magnitude changes (total change > 20 spaces)

        significant_threshold = max(3, len(changes.get('new_locations', [])) * 2)  # At least 3 changes or 2x new locations
        large_magnitude = changes.get('total_change_magnitude', 0) > 20

        return (
            len(changes.get('new_locations', [])) > 0 or
            len(changes.get('removed_locations', [])) > 0 or
            changes.get('changed_locations', 0) >= significant_threshold or
            large_magnitude
        )

    def create_partitioned_files(self, df, timestamp):
        """Create time-based partitioned files for Iceberg loading"""
        # Partition by date and hour for optimal Iceberg performance
        df['partition_date'] = pd.to_datetime(df['timestamp']).dt.date
        df['partition_hour'] = pd.to_datetime(df['timestamp']).dt.hour

        # Group by partitions
        partitions = {}
        for (date, hour), group in df.groupby(['partition_date', 'partition_hour']):
            partition_key = f"{date}_{hour:02d}"
            partitions[partition_key] = group.drop(['partition_date', 'partition_hour'], axis=1)

        # Save partitioned files
        for partition_key, partition_df in partitions.items():
            partition_file = self.data_dir / "partitions" / f"parking_data_{partition_key}_{timestamp}.parquet"
            partition_df.to_parquet(partition_file, index=False)
            logger.info(f"Created partition: {partition_file.name} ({len(partition_df)} records)")

        return list(partitions.keys())

    def save_change_summary(self, changes, timestamp):
        """Save change summary for monitoring"""
        summary = {
            'timestamp': timestamp,
            'change_analysis': changes,
            'processing_decision': 'processed' if changes.get('has_changes') else 'skipped',
            'recommendations': self.generate_recommendations(changes)
        }

        summary_file = self.data_dir / "changes" / f"changes_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, default=str, indent=2)

        return summary

    def generate_recommendations(self, changes):
        """Generate recommendations based on change analysis"""
        recommendations = []

        if changes.get('changed_locations', 0) > 10:
            recommendations.append("High activity detected - consider increasing monitoring frequency")

        if len(changes.get('new_locations', [])) > 0:
            recommendations.append(f"New locations detected: {changes['new_locations']}")

        if changes.get('total_change_magnitude', 0) > 50:
            recommendations.append("Large occupancy changes detected - investigate peak hours")

        if not changes.get('has_changes'):
            recommendations.append("No significant changes - consider reducing processing frequency")

        return recommendations

    def execute_delta_load(self):
        """Execute the complete delta loading process"""
        logger.info("Starting delta loading process...")

        # 1. Fetch current data
        raw_data = self.fetch_current_data()
        current_df = pd.DataFrame(raw_data)

        # Transform data (same as current pipeline)
        current_df = self.transform_data(current_df)

        # 2. Load previous data for comparison
        previous_df = self.load_previous_data()

        # 3. Detect changes
        changes = self.detect_changes(current_df, previous_df)

        # 4. Determine if processing is needed
        should_process = self.should_process_delta(changes)

        if not should_process:
            logger.info("No significant changes detected - skipping processing")
            return {
                'status': 'skipped',
                'reason': 'no_significant_changes',
                'changes': changes
            }

        # 5. Process the delta
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

        # Create partitioned files for Iceberg
        partitions = self.create_partitioned_files(current_df, timestamp)

        # Save main dataset
        main_file = self.seeds_dir / "raw_parking_data.csv"
        current_df.to_csv(main_file, index=False)

        # Save change summary
        summary = self.save_change_summary(changes, timestamp)

        logger.info(f"Delta loading completed - processed {len(partitions)} partitions")

        return {
            'status': 'processed',
            'partitions_created': len(partitions),
            'records_processed': len(current_df),
            'changes_detected': changes,
            'summary': summary
        }

    def transform_data(self, df):
        """Transform raw API data to match pipeline format"""
        # Rename columns
        column_mapping = {
            'Dato': 'date',
            'Klokkeslett': 'time',
            'Sted': 'location',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Antall_ledige_plasser': 'available_spaces'
        }
        df = df.rename(columns=column_mapping)

        # Create timestamp
        df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%d.%m.%Y %H:%M')

        # Convert numeric fields
        df['available_spaces'] = pd.to_numeric(df['available_spaces'], errors='coerce')
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

        # Add metadata
        df['data_source'] = 'stavanger_parking_api'
        df['ingestion_timestamp'] = datetime.now(timezone.utc)
        df['pipeline_run_id'] = f"delta_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        return df


def main():
    """Main execution function"""
    engine = DeltaLoadingEngine()

    try:
        result = engine.execute_delta_load()

        print(f"\n{'='*50}")
        print("DELTA LOADING RESULTS")
        print(f"{'='*50}")

        print(f"Status: {result['status']}")

        if result['status'] == 'processed':
            print(f"Partitions Created: {result.get('partitions_created', 0)}")
            print(f"Records Processed: {result.get('records_processed', 0)}")

            changes = result.get('changes', {})
            print(f"Locations Changed: {changes.get('changed_locations', 0)}")
            print(f"New Locations: {len(changes.get('new_locations', []))}")
            print(f"Removed Locations: {len(changes.get('removed_locations', []))}")

            # Show top changes
            occupancy_changes = changes.get('occupancy_changes', [])
            if occupancy_changes:
                print("
Top Occupancy Changes:")
                for change in sorted(occupancy_changes, key=lambda x: abs(x['change']), reverse=True)[:5]:
                    print(f"  {change['location']}: {change['change']:+d} spaces")

        elif result['status'] == 'skipped':
            print("Reason: No significant changes detected")

        print(f"\n{'='*50}")

    except Exception as e:
        logger.error(f"Delta loading failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
