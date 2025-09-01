#!/usr/bin/env python3
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
            print("\n🛑 Streaming stopped by user")
        except Exception as e:
            print(f"❌ Streaming error: {e}")
        finally:
            self.producer.close()

if __name__ == "__main__":
    streamer = ParkingDataStreamer()
    streamer.stream_data()
