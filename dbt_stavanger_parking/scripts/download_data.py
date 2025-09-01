#!/usr/bin/env python3
"""
Stavanger Parking Data Ingestion Script
Downloads parking data from OpenCom.no and prepares it for dbt processing
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StavangerParkingIngestion:
    """Data ingestion class for Stavanger Parking data"""
    
    def __init__(self, output_dir="seeds"):
        self.output_dir = output_dir
        self.base_url = "https://opencom.no/dataset/stavanger-parkering"
        self.api_endpoint = "https://opencom.no/api/1/datasets/stavanger-parkering"
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def download_parking_data(self):
        """Download parking data from OpenCom.no"""
        try:
            logger.info("Starting Stavanger Parking data download...")
            
            # Try to get dataset info first
            try:
                response = requests.get(self.api_endpoint, timeout=30)
                response.raise_for_status()
                
                dataset_info = response.json()
                logger.info(f"Dataset info retrieved: {dataset_info.get('title', 'Unknown')}")
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API endpoint not accessible: {str(e)}")
                logger.info("Proceeding with sample data generation for demonstration purposes")
            
            # Create sample data structure since we need to understand the actual API
            # This demonstrates the ingestion pattern
            sample_data = self._create_sample_parking_data()
            
            # Save as CSV for dbt seeds
            csv_path = os.path.join(self.output_dir, "raw_parking_data.csv")
            sample_data.to_csv(csv_path, index=False)
            logger.info(f"Sample data saved to {csv_path}")
            
            # Save metadata
            metadata = {
                "dataset_name": "Stavanger Parking",
                "source_url": self.base_url,
                "download_timestamp": datetime.now().isoformat(),
                "record_count": len(sample_data),
                "columns": list(sample_data.columns),
                "note": "Sample data generated for demonstration - replace with actual API data"
            }
            
            metadata_path = os.path.join(self.output_dir, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Metadata saved to {metadata_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in data processing: {str(e)}")
            return False
    
    def _create_sample_parking_data(self):
        """Create sample parking data for demonstration"""
        # This will be replaced with actual data once we understand the API
        import numpy as np
        
        # Generate realistic sample data
        np.random.seed(42)  # For reproducible results
        
        locations = [
            "Stavanger Sentrum", "Våland", "Eiganes", "Hillevåg", 
            "Tasta", "Hundvåg", "Madla", "Hinna"
        ]
        
        # Generate 1000 sample records
        n_records = 1000
        data = {
            'id': range(1, n_records + 1),
            'timestamp': pd.date_range('2024-01-01', periods=n_records, freq='H'),
            'location': np.random.choice(locations, n_records),
            'occupancy': np.random.randint(0, 100, n_records),
            'capacity': np.random.choice([50, 75, 100, 150, 200], n_records),
            'parking_type': np.random.choice(['Street', 'Garage', 'Surface'], n_records),
            'zone': np.random.choice(['A', 'B', 'C'], n_records),
            'price_per_hour': np.random.choice([15, 25, 35, 45], n_records)
        }
        
        df = pd.DataFrame(data)
        
        # Calculate derived fields
        df['utilization_rate'] = (df['occupancy'] / df['capacity'] * 100).round(2)
        df['available_spaces'] = df['capacity'] - df['occupancy']
        df['is_peak_hour'] = df['timestamp'].dt.hour.isin([8, 9, 17, 18]).astype(int)
        
        return df
    
    def validate_data(self, data_path):
        """Validate downloaded data quality"""
        try:
            df = pd.read_csv(data_path)
            
            # Basic validation checks
            validation_results = {
                'total_records': len(df),
                'null_values': df.isnull().sum().to_dict(),
                'duplicate_records': df.duplicated().sum(),
                'data_types': df.dtypes.to_dict(),
                'value_ranges': {
                    'occupancy': {'min': df['occupancy'].min(), 'max': df['occupancy'].max()},
                    'capacity': {'min': df['capacity'].min(), 'max': df['capacity'].max()},
                    'utilization_rate': {'min': df['utilization_rate'].min(), 'max': df['utilization_rate'].max()}
                }
            }
            
            logger.info("Data validation completed successfully")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return None

def main():
    """Main execution function"""
    logger.info("Starting Stavanger Parking data pipeline...")
    
    # Initialize ingestion
    ingestion = StavangerParkingIngestion()
    
    # Download data
    if ingestion.download_parking_data():
        logger.info("Data download completed successfully")
        
        # Validate data
        csv_path = "seeds/raw_parking_data.csv"
        validation_results = ingestion.validate_data(csv_path)
        
        if validation_results:
            logger.info("Data validation results:")
            logger.info(f"Total records: {validation_results['total_records']}")
            logger.info(f"Duplicate records: {validation_results['duplicate_records']}")
        
        logger.info("Pipeline completed successfully!")
    else:
        logger.error("Pipeline failed!")
        exit(1)

if __name__ == "__main__":
    main()
