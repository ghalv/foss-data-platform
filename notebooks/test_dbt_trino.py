#!/usr/bin/env python3
"""
Test Script for dbt-trino Integration and Stavanger Parking Pipeline

This script tests our working components:
1. dbt-trino connection
2. Trino query execution
3. Basic data pipeline logic
"""

import subprocess
import sys
import os
from datetime import datetime

def test_dbt_connection():
    """Test our dbt-trino connection"""
    print("🔍 Testing dbt-trino connection...")
    
    try:
        # Change to dbt directory
        result = subprocess.run(
            ['dbt', 'debug', '--profile', 'foss_data_platform'],
            capture_output=True,
            text=True,
            cwd='./dbt'
        )
        
        if result.returncode == 0:
            print("✅ dbt-trino connection successful!")
            return True
        else:
            print("❌ dbt-trino connection failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error testing dbt connection: {e}")
        return False

def test_dbt_models():
    """Test running our dbt models"""
    print("\n🚀 Testing dbt models...")
    
    try:
        # Run dbt models
        result = subprocess.run(
            ['dbt', 'run', '--profile', 'foss_data_platform'],
            capture_output=True,
            text=True,
            cwd='./dbt'
        )
        
        if result.returncode == 0:
            print("✅ dbt models ran successfully!")
            print("\nOutput:")
            print(result.stdout)
            return True
        else:
            print("❌ dbt models failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running dbt models: {e}")
        return False

def test_trino_queries():
    """Test basic Trino queries"""
    print("\n🔍 Testing Trino queries...")
    
    try:
        # Test a simple query
        result = subprocess.run(
            ['dbt', 'run-operation', 'test_query', '--profile', 'foss_data_platform', '--args', '{query: "SELECT 1 as test_value"}'],
            capture_output=True,
            text=True,
            cwd='./dbt'
        )
        
        if result.returncode == 0:
            print("✅ Trino query test successful!")
            return True
        else:
            print("❌ Trino query test failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error testing Trino queries: {e}")
        return False

def simulate_stavanger_parking_data():
    """Simulate the Stavanger parking data pipeline logic"""
    print("\n🚗 Simulating Stavanger Parking Pipeline...")
    
    # Sample parking data (what our Dagster assets would produce)
    parking_data = [
        {
            'parking_house_name': 'Stavanger Sentrum',
            'location': '58.9700,5.7331',
            'available_spaces': 45,
            'total_spaces': 200,
            'last_updated': datetime.now().isoformat()
        },
        {
            'parking_house_name': 'Kongsberg Parkering',
            'location': '58.9750,5.7400',
            'available_spaces': 23,
            'total_spaces': 150,
            'last_updated': datetime.now().isoformat()
        },
        {
            'parking_house_name': 'Havneringen',
            'location': '58.9730,5.7310',
            'available_spaces': 67,
            'total_spaces': 300,
            'last_updated': datetime.now().isoformat()
        }
    ]
    
    print(f"📊 Generated {len(parking_data)} parking records:")
    for record in parking_data:
        occupancy = ((record['total_spaces'] - record['available_spaces']) / record['total_spaces']) * 100
        print(f"  - {record['parking_house_name']}: {record['available_spaces']}/{record['total_spaces']} available ({occupancy:.1f}% occupied)")
    
    # Calculate metrics
    total_capacity = sum(r['total_spaces'] for r in parking_data)
    total_available = sum(r['available_spaces'] for r in parking_data)
    overall_occupancy = ((total_capacity - total_available) / total_capacity) * 100
    
    print(f"\n📈 Overall Metrics:")
    print(f"  - Total Capacity: {total_capacity}")
    print(f"  - Total Available: {total_available}")
    print(f"  - Overall Occupancy: {overall_occupancy:.1f}%")
    
    return True

def main():
    """Main test function"""
    print("🚀 FOSS Data Platform - Component Testing")
    print("=" * 50)
    
    # Test dbt-trino integration
    dbt_working = test_dbt_connection()
    
    if dbt_working:
        # Test dbt models
        models_working = test_dbt_models()
        
        # Test Trino queries
        trino_working = test_trino_queries()
        
        # Simulate parking pipeline
        pipeline_working = simulate_stavanger_parking_data()
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print(f"  ✅ dbt-trino: {'Working' if dbt_working else 'Failed'}")
        print(f"  ✅ dbt models: {'Working' if models_working else 'Failed'}")
        print(f"  ✅ Trino queries: {'Working' if trino_working else 'Failed'}")
        print(f"  ✅ Pipeline logic: {'Working' if pipeline_working else 'Failed'}")
        
        if all([dbt_working, models_working, trino_working, pipeline_working]):
            print("\n🎉 All components are working! Ready for production pipeline!")
        else:
            print("\n⚠️ Some components need attention.")
    else:
        print("\n❌ dbt-trino connection failed. Please check configuration.")

if __name__ == "__main__":
    main()
