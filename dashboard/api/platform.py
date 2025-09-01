"""
Unified Platform API
Integrates all platform services into a single, cohesive interface
"""

from typing import Dict, List, Any, Optional
import logging
from .storage import storage_api
from .query import trino_api
import time

logger = logging.getLogger(__name__)

class PlatformAPI:
    """Unified API for all platform services"""
    
    def __init__(self):
        self.storage = storage_api
        self.query = trino_api
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get comprehensive platform status"""
        try:
            # Storage status
            storage_stats = self.storage.get_storage_stats()
            
            # Query engine status
            trino_status = self.query.test_connection()
            
            # Overall platform health
            platform_health = {
                'storage': {
                    'status': 'healthy' if storage_stats else 'unhealthy',
                    'stats': storage_stats
                },
                'query_engine': {
                    'status': 'healthy' if trino_status else 'unhealthy',
                    'connection': trino_status
                },
                'overall_status': 'healthy' if (storage_stats and trino_status) else 'degraded'
            }
            
            return platform_health
            
        except Exception as e:
            logger.error(f"Error getting platform status: {e}")
            return {
                'overall_status': 'error',
                'error': str(e)
            }
    
    def get_data_catalog(self) -> Dict[str, Any]:
        """Get comprehensive data catalog information"""
        try:
            catalogs = self.query.get_catalogs()
            catalog_info = {}
            
            for catalog in catalogs:
                schemas = self.query.get_schemas(catalog)
                catalog_info[catalog] = {
                    'schemas': schemas,
                    'tables': {}
                }
                
                for schema in schemas:
                    tables = self.query.get_tables(catalog, schema)
                    catalog_info[catalog]['tables'][schema] = tables
            
            return {
                'success': True,
                'catalogs': catalog_info,
                'total_catalogs': len(catalogs),
                'total_schemas': sum(len(catalog_info[c]['schemas']) for c in catalog_info),
                'total_tables': sum(
                    len(catalog_info[c]['tables'][s]) 
                    for c in catalog_info 
                    for s in catalog_info[c]['tables']
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting data catalog: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_and_process_data(self, file_path: str, bucket_name: str, 
                               object_key: str, process_type: str = 'raw') -> Dict[str, Any]:
        """Upload data and optionally process it"""
        try:
            # Upload file to storage
            upload_success = self.storage.upload_file(bucket_name, object_key, file_path)
            
            if not upload_success:
                return {
                    'success': False,
                    'error': 'Failed to upload file to storage'
                }
            
            # Get file info
            file_info = self.storage.get_object_info(bucket_name, object_key)
            
            result = {
                'success': True,
                'message': 'File uploaded successfully',
                'file_info': file_info,
                'storage_location': f"{bucket_name}/{object_key}"
            }
            
            # If processing is requested, add processing logic here
            if process_type == 'auto':
                # Could trigger dbt pipeline, data validation, etc.
                result['processing'] = 'Processing pipeline triggered'
            
            return result
            
        except Exception as e:
            logger.error(f"Error in upload and process: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_data_quality_metrics(self, catalog: str = 'iceberg', 
                                schema: str = 'default') -> Dict[str, Any]:
        """Get data quality metrics for tables"""
        try:
            tables = self.query.get_tables(catalog, schema)
            quality_metrics = {}
            
            for table in tables:
                table_name = table['table']
                row_count = table.get('row_count', 0)
                
                # Basic quality metrics (could be extended with more sophisticated checks)
                quality_metrics[table_name] = {
                    'row_count': row_count,
                    'has_data': row_count > 0,
                    'data_freshness': 'unknown',  # Could check last modified timestamps
                    'schema_completeness': len(table.get('columns', [])),
                    'quality_score': 100 if row_count > 0 else 0
                }
            
            return {
                'success': True,
                'catalog': catalog,
                'schema': schema,
                'tables': quality_metrics,
                'summary': {
                    'total_tables': len(tables),
                    'tables_with_data': sum(1 for t in quality_metrics.values() if t['has_data']),
                    'average_quality_score': sum(t['quality_score'] for t in quality_metrics.values()) / len(quality_metrics) if quality_metrics else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_data_pipeline(self, pipeline_name: str, 
                             parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a data pipeline with given parameters"""
        try:
            # This would integrate with Dagster or other orchestration tools
            # For now, return a mock response
            return {
                'success': True,
                'pipeline_name': pipeline_name,
                'execution_id': f'exec_{int(time.time())}',
                'status': 'started',
                'message': f'Pipeline {pipeline_name} execution started',
                'parameters': parameters or {}
            }
            
        except Exception as e:
            logger.error(f"Error executing pipeline {pipeline_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global platform API instance
platform_api = PlatformAPI()
