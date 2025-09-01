"""
Unified Query API Client for Trino Operations
Provides programmatic access to query execution and schema management
"""

import requests
import json
import time
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TrinoAPI:
    """Unified API for Trino query operations"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        
    def execute_query(self, query: str, catalog: str = "iceberg", 
                     schema: str = "default") -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        try:
            # Start query execution
            response = self.session.post(
                f"{self.base_url}/v1/statement",
                data=query,
                headers={'Content-Type': 'text/plain'},
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Query execution failed: {response.status_code}',
                    'details': response.text
                }
            
            # Get query ID and next URI
            query_data = response.json()
            query_id = query_data.get('id')
            next_uri = query_data.get('nextUri')
            
            if not next_uri:
                return {
                    'success': False,
                    'error': 'No next URI received from Trino'
                }
            
            # Poll for results
            max_attempts = 200
            poll_interval = 0.5
            
            for attempt in range(max_attempts):
                result_response = self.session.get(next_uri, timeout=10)
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    current_state = result_data.get('stats', {}).get('state')
                    new_next_uri = result_data.get('nextUri')
                    
                    if new_next_uri:
                        next_uri = new_next_uri
                    
                    if current_state == 'FINISHED':
                        # Query completed successfully
                        columns = result_data.get('columns', [])
                        data = result_data.get('data', [])
                        
                        return {
                            'success': True,
                            'query_id': query_id,
                            'columns': columns,
                            'data': data,
                            'row_count': len(data),
                            'execution_time': result_data.get('stats', {}).get('elapsedTime', 0)
                        }
                        
                    elif current_state == 'FAILED':
                        # Query failed
                        error = result_data.get('error', {})
                        return {
                            'success': False,
                            'error': error.get('message', 'Query execution failed'),
                            'query_id': query_id
                        }
                        
                    elif current_state in ['RUNNING', 'QUEUED']:
                        # Query still running, continue polling
                        time.sleep(poll_interval)
                        continue
                        
                elif result_response.status_code == 410:
                    # Query ID expired, try to get final results
                    try:
                        final_response = self.session.get(
                            f"{self.base_url}/v1/query/{query_id}",
                            timeout=10
                        )
                        if final_response.status_code == 200:
                            final_data = final_response.json()
                            if final_data.get('stats', {}).get('state') == 'FINISHED':
                                columns = final_data.get('columns', [])
                                data = final_data.get('data', [])
                                return {
                                    'success': True,
                                    'query_id': query_id,
                                    'columns': columns,
                                    'data': data,
                                    'row_count': len(data),
                                    'execution_time': final_data.get('stats', {}).get('elapsedTime', 0)
                                }
                    except:
                        pass
                    
                    return {
                        'success': False,
                        'error': 'Query execution timed out or failed',
                        'query_id': query_id
                    }
                    
                else:
                    return {
                        'success': False,
                        'error': f'Unexpected response: {result_response.status_code}',
                        'query_id': query_id
                    }
            
            # Timeout
            return {
                'success': False,
                'error': 'Query execution timed out',
                'query_id': query_id
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_catalogs(self) -> List[str]:
        """Get list of available catalogs"""
        try:
            result = self.execute_query("SHOW CATALOGS")
            if result['success']:
                return [row[0] for row in result['data']]
            return []
        except:
            return []
    
    def get_schemas(self, catalog: str = None) -> List[str]:
        """Get list of schemas in a catalog"""
        try:
            if catalog:
                query = f"SHOW SCHEMAS FROM {catalog}"
            else:
                query = "SHOW SCHEMAS"
            
            result = self.execute_query(query)
            if result['success']:
                return [row[0] for row in result['data']]
            return []
        except:
            return []
    
    def get_tables(self, catalog: str, schema: str) -> List[Dict]:
        """Get list of tables in a schema"""
        try:
            query = f"SHOW TABLES FROM {catalog}.{schema}"
            result = self.execute_query(query)
            
            if result['success']:
                tables = []
                for row in result['data']:
                    table_name = row[0]
                    # Get table info
                    table_info = self.get_table_info(catalog, schema, table_name)
                    tables.append(table_info)
                return tables
            return []
        except:
            return []
    
    def get_table_info(self, catalog: str, schema: str, table: str) -> Dict:
        """Get detailed information about a table"""
        try:
            # Get table schema
            schema_query = f"DESCRIBE {catalog}.{schema}.{table}"
            schema_result = self.execute_query(schema_query)
            
            columns = []
            if schema_result['success']:
                columns = [
                    {
                        'name': row[0],
                        'type': row[1],
                        'extra': row[2] if len(row) > 2 else '',
                        'comment': row[3] if len(row) > 3 else ''
                    }
                    for row in schema_result['data']
                ]
            
            # Get table stats
            stats_query = f"SELECT COUNT(*) as row_count FROM {catalog}.{schema}.{table}"
            stats_result = self.execute_query(stats_query)
            
            row_count = 0
            if stats_result['success'] and stats_result['data']:
                row_count = stats_result['data'][0][0]
            
            return {
                'catalog': catalog,
                'schema': schema,
                'table': table,
                'columns': columns,
                'row_count': row_count,
                'full_name': f"{catalog}.{schema}.{table}"
            }
            
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {
                'catalog': catalog,
                'schema': schema,
                'table': table,
                'columns': [],
                'row_count': 0,
                'full_name': f"{catalog}.{schema}.{table}",
                'error': str(e)
            }
    
    def test_connection(self) -> bool:
        """Test connection to Trino"""
        try:
            result = self.execute_query("SELECT 1 as test")
            return result['success']
        except:
            return False

# Global Trino API instance
trino_api = TrinoAPI()
