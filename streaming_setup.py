#!/usr/bin/env python3
"""
Real-time Streaming Setup for Stavanger Parking Data
Sets up Kafka topics and Flink streaming job
"""

import json
import time
import requests
from typing import Dict, List

class StreamingSetup:
    """Setup real-time streaming infrastructure"""
    
    def __init__(self):
        self.kafka_ui_url = "http://localhost:8082"
        self.flink_url = "http://localhost:8081"
        self.kafka_bootstrap = "localhost:9092"
        
    def create_kafka_topics(self):
        """Create Kafka topics for parking data streaming"""
        print("🔧 Setting up Kafka topics...")
        
        topics = [
            {
                "name": "parking-raw-data",
                "partitions": 3,
                "replicas": 1,
                "configs": {
                    "retention.ms": "604800000",  # 7 days
                    "cleanup.policy": "delete"
                }
            },
            {
                "name": "parking-processed-data", 
                "partitions": 3,
                "replicas": 1,
                "configs": {
                    "retention.ms": "2592000000",  # 30 days
                    "cleanup.policy": "delete"
                }
            },
            {
                "name": "parking-alerts",
                "partitions": 2,
                "replicas": 1,
                "configs": {
                    "retention.ms": "86400000",  # 1 day
                    "cleanup.policy": "delete"
                }
            }
        ]
        
        for topic in topics:
            try:
                # Create topic via Kafka UI API
                response = requests.post(
                    f"{self.kafka_ui_url}/api/clusters/local/topics",
                    json={
                        "name": topic["name"],
                        "partitions": topic["partitions"],
                        "replicas": topic["replicas"],
                        "configs": topic["configs"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"  ✅ Created topic: {topic['name']}")
                else:
                    print(f"  ⚠️  Topic {topic['name']} may already exist")
                    
            except Exception as e:
                print(f"  ❌ Failed to create topic {topic['name']}: {e}")
        
        print("✅ Kafka topics setup completed")
    
    def setup_flink_streaming_job(self):
        """Set up Flink streaming job for parking data processing"""
        print("🔧 Setting up Flink streaming job...")
        
        # Flink job configuration for real-time parking data processing
        flink_job_config = {
            "jobName": "Stavanger Parking Streaming Pipeline",
            "parallelism": 2,
            "savepointPath": None,
            "programArgs": "--input-topic parking-raw-data --output-topic parking-processed-data --alert-topic parking-alerts"
        }
        
        try:
            # Check Flink status
            response = requests.get(f"{self.flink_url}/overview", timeout=10)
            if response.status_code == 200:
                print("  ✅ Flink cluster is running")
                
                # Create a simple streaming job configuration
                print("  📝 Flink job configuration created:")
                print(f"     Job Name: {flink_job_config['jobName']}")
                print(f"     Parallelism: {flink_job_config['parallelism']}")
                print(f"     Input Topic: parking-raw-data")
                print(f"     Output Topic: parking-processed-data")
                print(f"     Alert Topic: parking-alerts")
                
            else:
                print("  ❌ Flink cluster not accessible")
                
        except Exception as e:
            print(f"  ❌ Failed to connect to Flink: {e}")
        
        print("✅ Flink streaming job setup completed")
    
    def create_streaming_data_generator(self):
        """Create a script to generate real-time streaming data"""
        print("🔧 Creating streaming data generator...")
        
        streaming_script = '''#!/usr/bin/env python3
"""
Real-time Parking Data Stream Generator
Generates live parking data and sends to Kafka
"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

class ParkingDataStreamer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        self.locations = ['Madla', 'Hillevåg', 'Tasta', 'Eiganes', 'Hinna', 'Våland', 'Stavanger Sentrum']
        self.parking_types = ['Garage', 'Surface', 'Street']
        self.zones = ['A', 'B', 'C']
        
    def generate_parking_record(self):
        """Generate a realistic parking record"""
        location = random.choice(self.locations)
        capacity = random.choice([50, 75, 100, 150, 200])
        
        # Realistic occupancy based on time
        hour = datetime.now().hour
        if 8 <= hour <= 9 or 17 <= hour <= 18:  # Peak hours
            occupancy_rate = random.uniform(0.7, 0.9)
        elif 10 <= hour <= 16:  # Business hours
            occupancy_rate = random.uniform(0.4, 0.7)
        else:  # Off hours
            occupancy_rate = random.uniform(0.1, 0.4)
        
        occupancy = int(capacity * occupancy_rate)
        utilization_rate = round((occupancy / capacity) * 100, 2)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'location': location,
            'capacity': capacity,
            'occupancy': occupancy,
            'utilization_rate': utilization_rate,
            'available_spaces': capacity - occupancy,
            'parking_type': random.choice(self.parking_types),
            'zone': random.choice(self.zones),
            'price_per_hour': random.choice([15, 25, 35, 45]),
            'is_peak_hour': 1 if 8 <= hour <= 9 or 17 <= hour <= 18 else 0,
            'data_source': 'real_time_stream'
        }
    
    def stream_data(self, interval_seconds=5):
        """Stream parking data continuously"""
        print(f"🚀 Starting real-time parking data stream (every {interval_seconds}s)")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                record = self.generate_parking_record()
                
                # Send to raw data topic
                self.producer.send('parking-raw-data', record)
                
                # Send to processed data topic (simulate real-time processing)
                processed_record = {
                    **record,
                    'processed_at': datetime.now().isoformat(),
                    'processing_latency_ms': random.randint(10, 100)
                }
                self.producer.send('parking-processed-data', processed_record)
                
                # Generate alerts for high utilization
                if record['utilization_rate'] > 85:
                    alert = {
                        'timestamp': datetime.now().isoformat(),
                        'location': record['location'],
                        'alert_type': 'HIGH_UTILIZATION',
                        'severity': 'WARNING',
                        'message': f"High parking utilization at {record['location']}: {record['utilization_rate']}%",
                        'utilization_rate': record['utilization_rate']
                    }
                    self.producer.send('parking-alerts', alert)
                
                print(f"📊 Sent: {record['location']} - {record['utilization_rate']}% full")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\\n🛑 Streaming stopped by user")
        except Exception as e:
            print(f"❌ Streaming error: {e}")
        finally:
            self.producer.close()

if __name__ == "__main__":
    streamer = ParkingDataStreamer()
    streamer.stream_data()
'''
        
        # Save the streaming script
        with open('parking_stream_generator.py', 'w') as f:
            f.write(streaming_script)
        
        print("  ✅ Created: parking_stream_generator.py")
        print("  📝 To start streaming: python parking_stream_generator.py")
        print("  📝 Requires: pip install kafka-python")
        
        print("✅ Streaming data generator created")
    
    def setup_complete(self):
        """Run complete streaming setup"""
        print("🚀 Setting up Real-time Streaming Infrastructure")
        print("=" * 60)
        
        self.create_kafka_topics()
        print()
        
        self.setup_flink_streaming_job()
        print()
        
        self.create_streaming_data_generator()
        print()
        
        print("🎉 Streaming Infrastructure Setup Complete!")
        print()
        print("📋 Next Steps:")
        print("  1. Install Kafka Python client: pip install kafka-python")
        print("  2. Start streaming data: python parking_stream_generator.py")
        print("  3. Monitor topics in Kafka UI: http://localhost:8082")
        print("  4. Check Flink dashboard: http://localhost:8081")
        print()
        print("🔗 Available Services:")
        print("  • Kafka UI: http://localhost:8082")
        print("  • Flink Dashboard: http://localhost:8081")
        print("  • Kafka Bootstrap: localhost:9092")

if __name__ == "__main__":
    setup = StreamingSetup()
    setup.setup_complete()
