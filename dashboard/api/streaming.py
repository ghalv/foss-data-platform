"""
Real-time Data Streaming API Client
Handles Kafka operations, stream processing, and real-time data ingestion
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

class StreamingAPI:
    """Real-time data streaming operations using Kafka and Flink"""
    
    def __init__(self):
        self.kafka_bootstrap_servers = "kafka:9092"
        self.kafka_ui_url = "http://kafka-ui:8080"
        self.flink_url = "http://flink-jobmanager:8081"
        self.logger = logging.getLogger(__name__)
        
        # Stream processing configurations
        self.stream_configs = {
            "stavanger_parking_realtime": {
                "topic": "stavanger_parking_events",
                "partitions": 3,
                "replication_factor": 1,
                "retention_hours": 168,  # 7 days
                "cleanup_policy": "delete"
            },
            "data_quality_alerts": {
                "topic": "data_quality_alerts",
                "partitions": 1,
                "replication_factor": 1,
                "retention_hours": 8760,  # 1 year
                "cleanup_policy": "compact"
            },
            "system_metrics": {
                "topic": "system_metrics",
                "partitions": 2,
                "replication_factor": 1,
                "retention_hours": 720,  # 30 days
                "cleanup_policy": "delete"
            }
        }
    
    def get_streaming_status(self) -> Dict[str, Any]:
        """Get overall streaming platform status"""
        try:
            status = {
                "kafka": self._check_kafka_status(),
                "flink": self._check_flink_status(),
                "topics": self._get_kafka_topics(),
                "streams": self._get_flink_jobs(),
                "overall_status": "healthy"
            }
            
            # Determine overall status
            if not status["kafka"]["healthy"] or not status["flink"]["healthy"]:
                status["overall_status"] = "degraded"
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting streaming status: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "kafka": {"healthy": False, "error": str(e)},
                "flink": {"healthy": False, "error": str(e)},
                "topics": [],
                "streams": []
            }
    
    def _check_kafka_status(self) -> Dict[str, Any]:
        """Check Kafka cluster health"""
        try:
            # Try to connect to Kafka UI API
            response = requests.get(f"{self.kafka_ui_url}/api/clusters", timeout=5)
            if response.status_code == 200:
                return {"healthy": True, "message": "Kafka cluster is running"}
            else:
                return {"healthy": False, "message": f"Kafka UI returned {response.status_code}"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _check_flink_status(self) -> Dict[str, Any]:
        """Check Flink cluster health"""
        try:
            response = requests.get(f"{self.flink_url}/overview", timeout=5)
            if response.status_code == 200:
                return {"healthy": True, "message": "Flink cluster is running"}
            else:
                return {"healthy": False, "message": f"Flink returned {response.status_code}"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _get_kafka_topics(self) -> List[Dict[str, Any]]:
        """Get list of Kafka topics"""
        try:
            response = requests.get(f"{self.kafka_ui_url}/api/clusters/local/topics", timeout=5)
            if response.status_code == 200:
                topics = response.json()
                return [
                    {
                        "name": topic["name"],
                        "partitions": topic["partitions"],
                        "replicas": topic["replicas"],
                        "size": topic.get("size", 0),
                        "messages": topic.get("messages", 0)
                    }
                    for topic in topics
                ]
            return []
        except Exception as e:
            self.logger.error(f"Error getting Kafka topics: {e}")
            return []
    
    def _get_flink_jobs(self) -> List[Dict[str, Any]]:
        """Get list of Flink jobs"""
        try:
            response = requests.get(f"{self.flink_url}/jobs", timeout=5)
            if response.status_code == 200:
                jobs = response.json()
                return [
                    {
                        "id": job["id"],
                        "name": job["name"],
                        "status": job["status"],
                        "start_time": job.get("start-time", 0),
                        "end_time": job.get("end-time", 0),
                        "duration": job.get("duration", 0)
                    }
                    for job in jobs.get("jobs", [])
                ]
            return []
        except Exception as e:
            self.logger.error(f"Error getting Flink jobs: {e}")
            return []
    
    def create_streaming_topic(self, topic_name: str, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new Kafka topic for streaming"""
        try:
            if not config:
                config = self.stream_configs.get(topic_name, {
                    "partitions": 1,
                    "replication_factor": 1,
                    "retention_hours": 24,
                    "cleanup_policy": "delete"
                })
            
            topic_config = {
                "name": topic_name,
                "partitions": config["partitions"],
                "replicas": config["replication_factor"],
                "configs": {
                    "retention.ms": config["retention_hours"] * 3600000,
                    "cleanup.policy": config["cleanup_policy"]
                }
            }
            
            # This would typically use the Kafka Admin API
            # For now, we'll simulate topic creation
            self.logger.info(f"Creating topic {topic_name} with config: {topic_config}")
            
            return {
                "success": True,
                "topic": topic_name,
                "message": f"Topic {topic_name} created successfully",
                "config": topic_config
            }
            
        except Exception as e:
            self.logger.error(f"Error creating topic {topic_name}: {e}")
            return {
                "success": False,
                "topic": topic_name,
                "error": str(e)
            }
    
    def start_streaming_pipeline(self, pipeline_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a real-time streaming pipeline"""
        try:
            # This would typically submit a Flink job
            # For now, we'll simulate pipeline startup
            self.logger.info(f"Starting streaming pipeline {pipeline_name} with config: {config}")
            
            return {
                "success": True,
                "pipeline": pipeline_name,
                "job_id": f"flink_job_{int(time.time())}",
                "status": "RUNNING",
                "message": f"Streaming pipeline {pipeline_name} started successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error starting streaming pipeline {pipeline_name}: {e}")
            return {
                "success": False,
                "pipeline": pipeline_name,
                "error": str(e)
            }
    
    def get_streaming_metrics(self, topic_name: str, time_range: str = "1h") -> Dict[str, Any]:
        """Get real-time streaming metrics for a topic"""
        try:
            # This would typically query Kafka metrics
            # For now, we'll return simulated metrics
            current_time = datetime.now()
            
            metrics = {
                "topic": topic_name,
                "timestamp": current_time.isoformat(),
                "time_range": time_range,
                "messages_per_second": 150.5,
                "total_messages": 54200,
                "active_consumers": 3,
                "lag": 0,
                "throughput_mb_s": 2.1,
                "error_rate": 0.001,
                "partition_info": [
                    {"partition": 0, "messages": 18000, "lag": 0},
                    {"partition": 1, "messages": 18100, "lag": 0},
                    {"partition": 2, "messages": 18100, "lag": 0}
                ]
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting streaming metrics for {topic_name}: {e}")
            return {
                "topic": topic_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def ingest_streaming_data(self, topic_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest data into a streaming topic"""
        try:
            # This would typically use Kafka Producer API
            # For now, we'll simulate data ingestion
            self.logger.info(f"Ingesting data into topic {topic_name}: {data}")
            
            return {
                "success": True,
                "topic": topic_name,
                "timestamp": datetime.now().isoformat(),
                "message": f"Data ingested into {topic_name} successfully",
                "data_size": len(json.dumps(data))
            }
            
        except Exception as e:
            self.logger.error(f"Error ingesting data into {topic_name}: {e}")
            return {
                "success": False,
                "topic": topic_name,
                "error": str(e)
            }

# Global streaming API instance
streaming_api = StreamingAPI()
