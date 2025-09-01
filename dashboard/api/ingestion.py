"""
Smart Data Ingestion API
Automatically detects file types and triggers appropriate processing pipelines
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
import logging
from .storage import storage_api
from .query import trino_api

logger = logging.getLogger(__name__)

class DataIngestionAPI:
    """Smart data ingestion with automatic pipeline triggering"""
    
    def __init__(self):
        self.supported_formats = {
            'csv': {'mime_type': 'text/csv', 'extensions': ['.csv']},
            'json': {'mime_type': 'application/json', 'extensions': ['.json']},
            'parquet': {'mime_type': 'application/octet-stream', 'extensions': ['.parquet', '.parq']},
            'avro': {'mime_type': 'application/avro', 'extensions': ['.avro']},
            'excel': {'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'extensions': ['.xlsx', '.xls']}
        }
        
        self.pipeline_triggers = {
            'parking_data': {
                'patterns': ['parking', 'stavanger', 'occupancy'],
                'pipeline': 'stavanger_parking',
                'target_schema': 'raw_data'
            },
            'weather_data': {
                'patterns': ['weather', 'temperature', 'precipitation'],
                'pipeline': 'weather_processing',
                'target_schema': 'raw_data'
            },
            'traffic_data': {
                'patterns': ['traffic', 'congestion', 'flow'],
                'pipeline': 'traffic_analysis',
                'target_schema': 'raw_data'
            }
        }
    
    def ingest_file(self, file_path: str, bucket_name: str, object_key: str, 
                    auto_process: bool = True) -> Dict[str, Any]:
        """Ingest a file with smart processing"""
        try:
            # Detect file type and content
            file_info = self._analyze_file(file_path, object_key)
            
            # Upload to storage
            upload_success = storage_api.upload_file(bucket_name, object_key, file_path)
            
            if not upload_success:
                return {
                    'success': False,
                    'error': 'Failed to upload file to storage'
                }
            
            # Get storage info
            storage_info = storage_api.get_object_info(bucket_name, object_key)
            
            result = {
                'success': True,
                'message': 'File ingested successfully',
                'file_info': file_info,
                'storage_info': storage_info,
                'ingestion_timestamp': time.time()
            }
            
            # Auto-process if enabled
            if auto_process:
                processing_result = self._auto_process_file(bucket_name, object_key, file_info)
                result['processing'] = processing_result
            
            # Log ingestion
            self._log_ingestion(bucket_name, object_key, file_info, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_file(self, file_path: str, object_key: str) -> Dict[str, Any]:
        """Analyze file to determine type and content"""
        file_info = {
            'filename': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'detected_format': None,
            'estimated_rows': 0,
            'schema_hint': None,
            'content_preview': None
        }
        
        # Detect format
        for format_name, format_info in self.supported_formats.items():
            if file_info['extension'] in format_info['extensions']:
                file_info['detected_format'] = format_name
                break
        
        # Analyze content for pipeline detection
        pipeline_hint = self._detect_pipeline_hint(object_key, file_info)
        if pipeline_hint:
            file_info['pipeline_hint'] = pipeline_hint
        
        # Get content preview (first few lines/records)
        try:
            file_info['content_preview'] = self._get_content_preview(file_path, file_info['detected_format'])
        except:
            file_info['content_preview'] = "Unable to read content preview"
        
        return file_info
    
    def _detect_pipeline_hint(self, object_key: str, file_info: Dict) -> Optional[str]:
        """Detect which pipeline should process this file"""
        object_key_lower = object_key.lower()
        
        for pipeline_name, trigger_info in self.pipeline_triggers.items():
            for pattern in trigger_info['patterns']:
                if pattern.lower() in object_key_lower:
                    return pipeline_name
        
        return None
    
    def _get_content_preview(self, file_path: str, format_type: str) -> str:
        """Get a preview of file content"""
        try:
            if format_type == 'csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [f.readline().strip() for _ in range(3)]
                    return '\n'.join(lines)
            elif format_type == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # First 500 chars
                    return content + ('...' if len(content) >= 500 else '')
            else:
                return f"Binary file ({format_type})"
        except:
            return "Unable to read content"
    
    def _auto_process_file(self, bucket_name: str, object_key: str, 
                          file_info: Dict) -> Dict[str, Any]:
        """Automatically trigger processing pipeline"""
        try:
            pipeline_name = file_info.get('pipeline_hint')
            
            if not pipeline_name:
                return {
                    'triggered': False,
                    'reason': 'No pipeline detected for this file type'
                }
            
            # Trigger pipeline execution
            pipeline_result = self._trigger_pipeline(pipeline_name, {
                'source_bucket': bucket_name,
                'source_key': object_key,
                'file_info': file_info,
                'ingestion_timestamp': time.time()
            })
            
            return {
                'triggered': True,
                'pipeline': pipeline_name,
                'result': pipeline_result
            }
            
        except Exception as e:
            logger.error(f"Error in auto-processing: {e}")
            return {
                'triggered': False,
                'error': str(e)
            }
    
    def _trigger_pipeline(self, pipeline_name: str, parameters: Dict) -> Dict[str, Any]:
        """Trigger a data processing pipeline"""
        try:
            # This would integrate with Dagster or other orchestration tools
            # For now, we'll simulate pipeline triggering
            
            if pipeline_name == 'stavanger_parking':
                # Trigger the existing dbt pipeline
                return self._trigger_dbt_pipeline('stavanger_parking', parameters)
            else:
                # Placeholder for other pipelines
                return {
                    'success': True,
                    'pipeline': pipeline_name,
                    'status': 'triggered',
                    'execution_id': f'exec_{int(time.time())}',
                    'message': f'Pipeline {pipeline_name} triggered successfully'
                }
                
        except Exception as e:
            logger.error(f"Error triggering pipeline {pipeline_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _trigger_dbt_pipeline(self, pipeline_name: str, parameters: Dict) -> Dict[str, Any]:
        """Trigger a dbt pipeline"""
        try:
            # This would call the existing pipeline execution endpoint
            # For now, return a mock response
            return {
                'success': True,
                'pipeline': pipeline_name,
                'type': 'dbt',
                'status': 'triggered',
                'execution_id': f'dbt_{int(time.time())}',
                'message': f'DBT pipeline {pipeline_name} triggered for new data',
                'parameters': parameters
            }
            
        except Exception as e:
            logger.error(f"Error triggering DBT pipeline: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _log_ingestion(self, bucket_name: str, object_key: str, 
                       file_info: Dict, result: Dict):
        """Log ingestion activity"""
        log_entry = {
            'timestamp': time.time(),
            'bucket': bucket_name,
            'key': object_key,
            'file_info': file_info,
            'result': result
        }
        
        # Store in a log file or database
        log_file = '/tmp/data_ingestion_log.jsonl'
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except:
            pass  # Logging failure shouldn't break ingestion
    
    def get_ingestion_history(self, limit: int = 100) -> List[Dict]:
        """Get ingestion history"""
        try:
            log_file = '/tmp/data_ingestion_log.jsonl'
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Parse last N entries
            history = []
            for line in lines[-limit:]:
                try:
                    entry = json.loads(line.strip())
                    history.append(entry)
                except:
                    continue
            
            return history[::-1]  # Reverse to show newest first
            
        except Exception as e:
            logger.error(f"Error reading ingestion history: {e}")
            return []
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        try:
            history = self.get_ingestion_history(1000)
            
            if not history:
                return {
                    'total_files': 0,
                    'successful_ingestions': 0,
                    'failed_ingestions': 0,
                    'formats': {},
                    'pipelines_triggered': {}
                }
            
            stats = {
                'total_files': len(history),
                'successful_ingestions': sum(1 for h in history if h['result']['success']),
                'failed_ingestions': sum(1 for h in history if not h['result']['success']),
                'formats': {},
                'pipelines_triggered': {}
            }
            
            # Count formats
            for entry in history:
                format_type = entry['file_info'].get('detected_format', 'unknown')
                stats['formats'][format_type] = stats['formats'].get(format_type, 0) + 1
                
                # Count pipeline triggers
                if 'processing' in entry['result'] and entry['result']['processing']['triggered']:
                    pipeline = entry['result']['processing']['pipeline']
                    stats['pipelines_triggered'][pipeline] = stats['pipelines_triggered'].get(pipeline, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating ingestion stats: {e}")
            return {}

# Global ingestion API instance
ingestion_api = DataIngestionAPI()
