"""
Data Quality Monitoring API
Comprehensive data quality checks, monitoring, and alerting
"""

import time
from typing import Dict, List, Any, Optional
import logging
from .query import trino_api

logger = logging.getLogger(__name__)

class DataQualityAPI:
    """Data quality monitoring and validation"""
    
    def __init__(self):
        self.quality_checks = {
            'completeness': self._check_completeness,
            'freshness': self._check_freshness,
            'validity': self._check_validity,
            'consistency': self._check_consistency,
            'uniqueness': self._check_uniqueness
        }
        
        self.alert_thresholds = {
            'completeness': 0.95,  # 95% completeness required
            'freshness_hours': 24,  # Data should be less than 24 hours old
            'validity': 0.98,      # 98% valid records required
            'consistency': 0.90,   # 90% consistency required
            'uniqueness': 0.99     # 99% unique records required
        }
    
    def run_quality_checks(self, catalog: str = 'iceberg', 
                          schema: str = 'default') -> Dict[str, Any]:
        """Run comprehensive quality checks on all tables"""
        try:
            # Get all tables in the schema
            tables = trino_api.get_tables(catalog, schema)
            
            if not tables:
                return {
                    'success': False,
                    'error': 'No tables found in schema'
                }
            
            quality_results = {}
            overall_score = 0
            total_checks = 0
            
            for table in tables:
                table_name = table['table']
                table_quality = self._check_table_quality(catalog, schema, table_name)
                quality_results[table_name] = table_quality
                
                if table_quality['overall_score'] > 0:
                    overall_score += table_quality['overall_score']
                    total_checks += 1
            
            # Calculate overall quality score
            overall_quality_score = overall_score / total_checks if total_checks > 0 else 0
            
            # Generate alerts for quality issues
            alerts = self._generate_quality_alerts(quality_results)
            
            return {
                'success': True,
                'catalog': catalog,
                'schema': schema,
                'overall_score': round(overall_quality_score, 2),
                'total_tables': len(tables),
                'quality_results': quality_results,
                'alerts': alerts,
                'check_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error running quality checks: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_table_quality(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """Run quality checks on a specific table"""
        try:
            quality_metrics = {}
            
            # Run each quality check
            for check_name, check_function in self.quality_checks.items():
                try:
                    result = check_function(catalog, schema, table)
                    quality_metrics[check_name] = result
                except Exception as e:
                    logger.error(f"Error in {check_name} check for {table}: {e}")
                    quality_metrics[check_name] = {
                        'score': 0,
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Calculate overall table score
            scores = [m.get('score', 0) for m in quality_metrics.values() if m.get('score') is not None]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            # Determine overall status
            if overall_score >= 0.9:
                overall_status = 'excellent'
            elif overall_score >= 0.8:
                overall_status = 'good'
            elif overall_score >= 0.7:
                overall_status = 'fair'
            else:
                overall_status = 'poor'
            
            return {
                'table_name': table,
                'overall_score': round(overall_score, 3),
                'overall_status': overall_status,
                'quality_metrics': quality_metrics,
                'check_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error checking table quality for {table}: {e}")
            return {
                'table_name': table,
                'overall_score': 0,
                'overall_status': 'error',
                'error': str(e),
                'check_timestamp': time.time()
            }
    
    def _check_completeness(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """Check data completeness (non-null values)"""
        try:
            # Get table schema to identify columns
            table_info = trino_api.get_table_info(catalog, schema, table)
            columns = table_info.get('columns', [])
            
            if not columns:
                return {'score': 0, 'status': 'error', 'error': 'No columns found'}
            
            # Check each column for null values
            completeness_scores = []
            column_details = {}
            
            for column in columns:
                column_name = column['name']
                
                # Count null values
                null_query = f"SELECT COUNT(*) as null_count FROM {catalog}.{schema}.{table} WHERE {column_name} IS NULL"
                null_result = trino_api.execute_query(null_query)
                
                if null_result['success'] and null_result['data']:
                    null_count = null_result['data'][0][0]
                    total_count = table_info.get('row_count', 0)
                    
                    if total_count > 0:
                        completeness = 1 - (null_count / total_count)
                        completeness_scores.append(completeness)
                        column_details[column_name] = {
                            'null_count': null_count,
                            'total_count': total_count,
                            'completeness': round(completeness, 3)
                        }
            
            if not completeness_scores:
                return {'score': 0, 'status': 'error', 'error': 'No completeness data'}
            
            overall_completeness = sum(completeness_scores) / len(completeness_scores)
            
            return {
                'score': round(overall_completeness, 3),
                'status': 'pass' if overall_completeness >= self.alert_thresholds['completeness'] else 'fail',
                'details': column_details,
                'threshold': self.alert_thresholds['completeness']
            }
            
        except Exception as e:
            logger.error(f"Error checking completeness for {table}: {e}")
            return {'score': 0, 'status': 'error', 'error': str(e)}
    
    def _check_freshness(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """Check data freshness (how recent the data is)"""
        try:
            # Look for timestamp columns
            table_info = trino_api.get_table_info(catalog, schema, table)
            columns = table_info.get('columns', [])
            
            timestamp_columns = [col for col in columns if 'timestamp' in col['name'].lower() or 'date' in col['name'].lower()]
            
            if not timestamp_columns:
                return {
                    'score': 0.5,  # Neutral score if no timestamp columns
                    'status': 'unknown',
                    'reason': 'No timestamp columns found'
                }
            
            # Check the most recent timestamp
            latest_query = f"""
                SELECT MAX({timestamp_columns[0]['name']}) as latest_timestamp 
                FROM {catalog}.{schema}.{table}
            """
            
            latest_result = trino_api.execute_query(latest_query)
            
            if latest_result['success'] and latest_result['data']:
                latest_timestamp = latest_result['data'][0][0]
                
                if latest_timestamp:
                    # Calculate hours since last update
                    current_time = time.time()
                    if isinstance(latest_timestamp, str):
                        # Parse timestamp string
                        import datetime
                        try:
                            latest_time = datetime.datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                            latest_unix = latest_time.timestamp()
                        except:
                            latest_unix = current_time
                    else:
                        latest_unix = latest_timestamp
                    
                    hours_old = (current_time - latest_unix) / 3600
                    
                    # Calculate freshness score (1.0 = very fresh, 0.0 = very old)
                    if hours_old <= 1:
                        freshness_score = 1.0
                    elif hours_old <= 24:
                        freshness_score = 1.0 - (hours_old / 24) * 0.3  # 0.7 to 1.0
                    elif hours_old <= 168:  # 1 week
                        freshness_score = 0.7 - ((hours_old - 24) / 144) * 0.4  # 0.3 to 0.7
                    else:
                        freshness_score = 0.3 - min((hours_old - 168) / 168, 0.3)  # 0.0 to 0.3
                    
                    return {
                        'score': round(freshness_score, 3),
                        'status': 'pass' if hours_old <= self.alert_thresholds['freshness_hours'] else 'fail',
                        'latest_timestamp': latest_timestamp,
                        'hours_old': round(hours_old, 1),
                        'threshold_hours': self.alert_thresholds['freshness_hours']
                    }
            
            return {
                'score': 0.5,
                'status': 'unknown',
                'reason': 'Could not determine data freshness'
            }
            
        except Exception as e:
            logger.error(f"Error checking freshness for {table}: {e}")
            return {'score': 0, 'status': 'error', 'error': str(e)}
    
    def _check_validity(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """Check data validity (data types, ranges, formats)"""
        try:
            # For now, return a basic validity check
            # In a real implementation, this would check:
            # - Data type compliance
            # - Value ranges
            # - Format validation
            # - Business rules
            
            # Calculate actual validity score based on data
            try:
                # Check for null values in critical columns
                null_check_query = f"""
                    SELECT 
                        COUNT(*) as total_rows,
                        COUNT(CASE WHEN timestamp IS NULL THEN 1 END) as null_timestamps,
                        COUNT(CASE WHEN parking_zone IS NULL THEN 1 END) as null_zones,
                        COUNT(CASE WHEN occupancy_rate IS NULL THEN 1 END) as null_occupancy
                    FROM {catalog}.{schema}.{table}
                """
                
                null_result = trino_api.execute_query(null_check_query)
                if null_result['success'] and null_result['data']:
                    row = null_result['data'][0]
                    total_rows = row[0] or 0
                    null_timestamps = row[1] or 0
                    null_zones = row[2] or 0
                    null_occupancy = row[3] or 0
                    
                    if total_rows > 0:
                        # Calculate validity score (lower null rates = higher score)
                        null_rate = (null_timestamps + null_zones + null_occupancy) / (total_rows * 3)
                        validity_score = max(0.0, 1.0 - null_rate)
                        
                        return {
                            'score': round(validity_score, 3),
                            'status': 'pass' if validity_score >= 0.9 else 'warning',
                            'details': f'Validity check: {total_rows} rows, {null_timestamps + null_zones + null_occupancy} null values',
                            'null_timestamps': null_timestamps,
                            'null_zones': null_zones,
                            'null_occupancy': null_occupancy
                        }
                
                return {
                    'score': 0.5,
                    'status': 'unknown',
                    'details': 'Unable to calculate validity score',
                    'note': 'Data validation incomplete'
                }
            except Exception as e:
                return {
                    'score': 0.0,
                    'status': 'error',
                    'details': f'Validity check error: {str(e)}'
                }
            
        except Exception as e:
            logger.error(f"Error checking validity for {table}: {e}")
            return {'score': 0, 'status': 'error', 'error': str(e)}
    
    def _check_consistency(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """Check data consistency (cross-field validation, business rules)"""
        try:
            # For now, return a basic consistency check
            # In a real implementation, this would check:
            # - Cross-field relationships
            # - Business rule compliance
            # - Referential integrity
            
            # Calculate actual consistency score based on data
            try:
                # Check for data consistency across related fields
                consistency_query = f"""
                    SELECT 
                        COUNT(*) as total_rows,
                        COUNT(CASE WHEN occupancy_rate < 0 OR occupancy_rate > 100 THEN 1 END) as invalid_occupancy,
                        COUNT(CASE WHEN timestamp > NOW() THEN 1 END) as future_timestamps,
                        COUNT(CASE WHEN parking_zone = '' THEN 1 END) as empty_zones
                    FROM {catalog}.{schema}.{table}
                """
                
                consistency_result = trino_api.execute_query(consistency_query)
                if consistency_result['success'] and consistency_result['data']:
                    row = consistency_result['data'][0]
                    total_rows = row[0] or 0
                    invalid_occupancy = row[1] or 0
                    future_timestamps = row[2] or 0
                    empty_zones = row[3] or 0
                    
                    if total_rows > 0:
                        # Calculate consistency score (fewer inconsistencies = higher score)
                        inconsistency_rate = (invalid_occupancy + future_timestamps + empty_zones) / total_rows
                        consistency_score = max(0.0, 1.0 - inconsistency_rate)
                        
                        return {
                            'score': round(consistency_score, 3),
                            'status': 'pass' if consistency_score >= 0.9 else 'warning',
                            'details': f'Consistency check: {total_rows} rows, {invalid_occupancy + future_timestamps + empty_zones} inconsistencies',
                            'invalid_occupancy': invalid_occupancy,
                            'future_timestamps': future_timestamps,
                            'empty_zones': empty_zones
                        }
                
                return {
                    'score': 0.5,
                    'status': 'unknown',
                    'details': 'Unable to calculate consistency score',
                    'note': 'Consistency validation incomplete'
                }
            except Exception as e:
                return {
                    'score': 0.0,
                    'status': 'error',
                    'details': f'Consistency check error: {str(e)}'
                }
            
        except Exception as e:
            logger.error(f"Error checking consistency for {table}: {e}")
            return {'score': 0, 'status': 'error', 'error': str(e)}
    
    def _check_uniqueness(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """Check data uniqueness (duplicate detection)"""
        try:
            # Get table schema to identify potential key columns
            table_info = trino_api.get_table_info(catalog, schema, table)
            columns = table_info.get('columns', [])
            total_rows = table_info.get('row_count', 0)
            
            if total_rows == 0:
                return {
                    'score': 1.0,
                    'status': 'pass',
                    'reason': 'Empty table'
                }
            
            # Check for common ID columns
            id_columns = [col for col in columns if 'id' in col['name'].lower() or 'key' in col['name'].lower()]
            
            if id_columns:
                # Check uniqueness of ID column
                id_column = id_columns[0]['name']
                uniqueness_query = f"""
                    SELECT COUNT(DISTINCT {id_column}) as unique_count, COUNT(*) as total_count
                    FROM {catalog}.{schema}.{table}
                """
                
                uniqueness_result = trino_api.execute_query(uniqueness_query)
                
                if uniqueness_result['success'] and uniqueness_result['data']:
                    unique_count = uniqueness_result['data'][0][0]
                    total_count = uniqueness_result['data'][0][1]
                    
                    if total_count > 0:
                        uniqueness_score = unique_count / total_count
                        
                        return {
                            'score': round(uniqueness_score, 3),
                            'status': 'pass' if uniqueness_score >= self.alert_thresholds['uniqueness'] else 'fail',
                            'unique_count': unique_count,
                            'total_count': total_count,
                            'duplicate_count': total_count - unique_count,
                            'threshold': self.alert_thresholds['uniqueness']
                        }
            
            # If no ID columns found, return neutral score
            return {
                'score': 0.5,
                'status': 'unknown',
                'reason': 'No ID columns found for uniqueness check'
            }
            
        except Exception as e:
            logger.error(f"Error checking uniqueness for {table}: {e}")
            return {'score': 0, 'status': 'error', 'error': str(e)}
    
    def _generate_quality_alerts(self, quality_results: Dict) -> List[Dict]:
        """Generate alerts for quality issues"""
        alerts = []
        
        for table_name, table_quality in quality_results.items():
            if table_quality.get('overall_status') == 'error':
                alerts.append({
                    'level': 'error',
                    'table': table_name,
                    'message': f'Quality check failed for {table_name}: {table_quality.get("error", "Unknown error")}',
                    'timestamp': time.time()
                })
                continue
            
            overall_score = table_quality.get('overall_score', 0)
            
            if overall_score < 0.7:
                alerts.append({
                    'level': 'critical',
                    'table': table_name,
                    'message': f'Critical quality issues in {table_name}: Score {overall_score}',
                    'timestamp': time.time()
                })
            elif overall_score < 0.8:
                alerts.append({
                    'level': 'warning',
                    'table': table_name,
                    'message': f'Quality warning for {table_name}: Score {overall_score}',
                    'timestamp': time.time()
                })
            
            # Check individual metrics
            metrics = table_quality.get('quality_metrics', {})
            for metric_name, metric_result in metrics.items():
                if metric_result.get('status') == 'fail':
                    alerts.append({
                        'level': 'warning',
                        'table': table_name,
                        'metric': metric_name,
                        'message': f'{metric_name} check failed for {table_name}',
                        'timestamp': time.time()
                    })
        
        return alerts

# Global data quality API instance
quality_api = DataQualityAPI()
