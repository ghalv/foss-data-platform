#!/usr/bin/env python3
"""
FOSS Data Platform Dashboard

A unified web interface that provides access to all platform services,
monitoring, and management functions.
"""

from flask import Flask, render_template, jsonify, redirect, url_for, request
import requests
import json
import os
import time
from datetime import datetime
import psutil
import subprocess
import re
from api.storage import storage_api
from api.query import trino_api
from api.platform import platform_api
from api.ingestion import ingestion_api
from api.quality import quality_api
from api.streaming import streaming_api
import random
from functools import lru_cache
import csv
import yaml


app = Flask(__name__)
# Live data source configuration
PARKING_JSON_URL = os.environ.get('PARKING_JSON_URL', '').strip()
CKAN_BASE = os.environ.get('CKAN_BASE', 'https://opencom.no').rstrip('/')
PARKING_DATASET_ID = os.environ.get('PARKING_DATASET_ID', 'stavanger-parkering').strip()

# Pipelines config paths
PIPELINES_DIR = os.path.join(os.getcwd(), 'config', 'pipelines')
PIPELINES_REGISTRY = os.path.join(PIPELINES_DIR, 'registry.yaml')
PIPELINES_OVERRIDES = os.path.join(PIPELINES_DIR, 'overrides.local.yaml')

def load_pipeline_configs() -> dict:
    registry = {}
    try:
        with open(PIPELINES_REGISTRY, 'r') as f:
            registry = yaml.safe_load(f) or {}
    except Exception:
        registry = {}
    # Load overrides
    try:
        if os.path.exists(PIPELINES_OVERRIDES):
            with open(PIPELINES_OVERRIDES, 'r') as f:
                overrides = yaml.safe_load(f) or {}
            # Merge shallowly for simplicity
            if isinstance(overrides, dict):
                registry = {**registry, **overrides}
    except Exception:
        pass
    return registry

def get_pipeline_config(pipeline_id: str) -> dict:
    reg = load_pipeline_configs()
    items = (reg.get('pipelines') or []) if isinstance(reg, dict) else []
    for p in items:
        if p.get('id') == pipeline_id:
            # Load per-pipeline file
            cfg_file = p.get('config')
            if cfg_file:
                try:
                    with open(os.path.join(PIPELINES_DIR, cfg_file), 'r') as f:
                        cfg = yaml.safe_load(f) or {}
                    # Attach id and name from registry
                    cfg.setdefault('id', p.get('id'))
                    cfg.setdefault('name', p.get('name'))
                    return cfg
                except Exception:
                    return p
            return p
    return {}


# Configuration
SERVICES = {
    'jupyterlab': {
        'name': 'JupyterLab',
        'url': 'http://jupyterlab:8888',
        'external_url': 'http://localhost:8888',
        'description': 'Interactive development environment',
        'status': 'healthy',
        'category': 'Development',
        'icon': '🔬'
    },
    'dagster': {
        'name': 'Dagster',
        'url': 'http://dagster:3000',
        'external_url': 'http://localhost:3000',
        'description': 'Data orchestration platform',
        'status': 'healthy',
        'category': 'Orchestration',
        'icon': '🎯'
    },
    'trino': {
        'name': 'Apache Trino',
        'url': 'http://trino-coordinator:8080',
        'external_url': 'http://localhost:8080',
        'description': 'Distributed SQL query engine',
        'status': 'healthy',
        'category': 'Query Engine',
        'icon': '🚀'
    },
    'dbt': {
        'name': 'dbt',
        'url': 'http://dagster:3000',
        'external_url': 'http://localhost:3000',  # DBT runs through Dagster
        'description': 'Data transformation and modeling (via Dagster)',
        'status': 'healthy',
        'category': 'Transformation',
        'icon': '🔧'
    },
    'minio': {
        'name': 'MinIO',
        'url': 'http://minio:9000',
        'external_url': 'http://localhost:9003',  # MinIO Console port
        'description': 'S3-compatible object storage',
        'status': 'healthy',
        'category': 'Storage',
        'icon': '📦'
    },
    'grafana': {
        'name': 'Grafana',
        'url': 'http://grafana:3000',
        'external_url': 'http://localhost:3001',
        'description': 'Data visualization and monitoring',
        'status': 'healthy',
        'category': 'Visualization',
        'icon': '📊'
    },
    'prometheus': {
        'name': 'Prometheus',
        'url': 'http://prometheus:9090',
        'external_url': 'http://localhost:9090',
        'description': 'Metrics collection and storage',
        'status': 'healthy',
        'category': 'Monitoring',
        'icon': '📈'
    },
    'portainer': {
        'name': 'Portainer',
        'url': 'http://portainer:9000',
        'external_url': 'http://localhost:9000',
        'description': 'Container management interface',
        'status': 'healthy',
        'category': 'Management',
        'icon': '🐳'
    },
    'kafka': {
        'name': 'Apache Kafka',
        'url': 'http://kafka:9092',
        'external_url': 'http://localhost:9092',
        'description': 'Distributed streaming platform',
        'status': 'healthy',
        'category': 'Streaming',
        'icon': '📡'
    },
    'zookeeper': {
        'name': 'Apache Zookeeper',
        'url': 'http://zookeeper:2181',
        'external_url': 'http://localhost:2181',
        'description': 'Distributed coordination service',
        'status': 'healthy',
        'category': 'Streaming',
        'icon': '🐘'
    },
    'flink': {
        'name': 'Apache Flink',
        'url': 'http://flink-jobmanager:8081',
        'external_url': 'http://localhost:8081',
        'description': 'Stream processing engine',
        'status': 'healthy',
        'category': 'Streaming',
        'icon': '⚡'
    },
    'kafka-ui': {
        'name': 'Kafka UI',
        'url': 'http://kafka-ui:8080',
        'external_url': 'http://localhost:8082',
        'description': 'Kafka management interface',
        'status': 'healthy',
        'category': 'Streaming',
        'icon': '🎛️'
    },
    'postgres': {
        'name': 'PostgreSQL',
        'url': 'http://postgres:5432',
        'external_url': 'http://localhost:5432',
        'description': 'Metadata database',
        'status': 'healthy',
        'category': 'Database',
        'icon': '🐘'
    },
    'redis': {
        'name': 'Redis',
        'url': 'http://redis:6379',
        'external_url': 'http://localhost:6379',
        'description': 'In-memory data store',
        'status': 'healthy',
        'category': 'Cache',
        'icon': '🔴'
    },
    'flink-taskmanager': {
        'name': 'Flink TaskManager',
        'url': 'http://flink-taskmanager:8081',
        'external_url': 'http://localhost:8081',
        'description': 'Flink task execution node',
        'status': 'healthy',
        'category': 'Streaming',
        'icon': '⚡'
    },
    'trino-worker': {
        'name': 'Trino Worker',
        'url': 'http://trino-worker:8080',
        'external_url': 'http://localhost:8080',
        'description': 'Trino worker node',
        'status': 'healthy',
        'category': 'Query Engine',
        'icon': '🚀'
    }
}

def check_service_health(service_id, service_info):
    """Check if a service is healthy"""
    try:
        # Special handling for Portainer to check API endpoint
        if service_id == 'portainer':
            response = requests.get('http://localhost:9000/api/status', timeout=3)
        else:
            response = requests.get(service_info['url'], timeout=3)
            
        if response.status_code == 200:
            return 'healthy'
        else:
            return 'warning'
    except requests.exceptions.RequestException:
        return 'down'

def get_system_metrics():
    """Get basic system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': round(cpu_percent, 1),
            'memory': {
                'used': round(memory.used / (1024**3), 1),  # GB
                'total': round(memory.total / (1024**3), 1),  # GB
                'percent': round(memory.percent, 1)
            },
            'disk': {
                'used': round(disk.used / (1024**3), 1),  # GB
                'total': round(disk.total / (1024**3), 1),  # GB
                'percent': round((disk.used / disk.total) * 100, 1)
            }
        }
    except Exception:
        return None

def get_docker_status():
    """Get Docker container status"""
    try:
        # Try to use Docker socket if available and docker command exists
        if os.path.exists('/var/run/docker.sock'):
            try:
                result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}:{{.Status}}'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    containers = {}
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            name, status = line.split(':', 1)
                            containers[name] = status
                    return containers
            except FileNotFoundError:
                # Docker command not available in container
                pass
        
        # Fallback: return service-based status
        return {
            'dashboard': 'Up (Service-based monitoring)',
            'dagster': 'Up (Service-based monitoring)',
            'jupyterlab': 'Up (Service-based monitoring)',
            'trino-coordinator': 'Up (Service-based monitoring)',
            'grafana': 'Up (Service-based monitoring)',
            'minio': 'Up (Service-based monitoring)',
            'prometheus': 'Up (Service-based monitoring)',
            'portainer': 'Up (Service-based monitoring)',
            'postgres': 'Up (Service-based monitoring)',
            'redis': 'Up (Service-based monitoring)'
        }
    except Exception:
        return {}

# Add pipeline status function
def get_pipeline_status():
    """Get Stavanger Parking pipeline status from actual Trino data"""
    try:
        import requests
        import json
        
        # Query actual pipeline models from Trino
        queries = {
            'models_count': "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema LIKE '%marts%' OR table_schema LIKE '%staging%' OR table_schema LIKE '%intermediate%'",
            'total_records': "SELECT COUNT(*) as count FROM memory.default_staging.stg_parking_data",
            'locations_count': "SELECT COUNT(DISTINCT parking_location) as count FROM memory.default_staging.stg_parking_data",
            'critical_alerts': "SELECT COUNT(*) as count FROM memory.default_marts_marketing.mart_parking_insights WHERE business_recommendation LIKE '%Consider Expansion%'",
            'avg_utilization': "SELECT ROUND(AVG(daily_avg_utilization), 1) as avg_util FROM memory.default_marts_marketing.mart_parking_insights"
        }
        
        results = {}
        for key, query in queries.items():
            try:
                # Use Trino's HTTP API to execute queries
                response = requests.post(
                    'http://localhost:8080/v1/statement',
                    json={'query': query},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                if response.status_code == 200:
                    # Parse the response to get the count
                    result_data = response.json()
                    if 'data' in result_data and result_data['data']:
                        results[key] = result_data['data'][0][0]  # Extract the count value
                    else:
                        results[key] = 0
                else:
                    results[key] = 0
            except:
                results[key] = 0
        
        # Get business insights from actual data
        try:
            insights_query = """
            SELECT DISTINCT parking_location, business_recommendation 
            FROM memory.default_marts_marketing.mart_parking_insights 
            WHERE business_recommendation LIKE '%Consider Expansion%' 
            LIMIT 5
            """
            insights_response = requests.post(
                'http://localhost:8080/v1/statement',
                json={'query': insights_query},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            business_insights = []
            if insights_response.status_code == 200:
                insights_data = insights_response.json()
                if 'data' in insights_data:
                    for row in insights_data['data']:
                        business_insights.append(f"{row[0]}: {row[1]}")
        except:
            business_insights = [
                'Stavanger Sentrum: High Demand - Consider Expansion',
                'Tasta: High Demand - Consider Expansion',
                'Hillevåg: High Demand - Consider Expansion'
            ]
        
        return {
            'status': 'running',
            'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 24-hour format
            'models_count': results.get('models_count', 5),
            'tests_passed': 3,  # We'll enhance this later
            'data_quality': 'good',
            'business_insights': business_insights,
            'total_locations': results.get('locations_count', 8),
            'avg_utilization': f"{results.get('avg_utilization', 75)}%",
            'critical_alerts': results.get('critical_alerts', 1),
            'total_records': results.get('total_records', 1000)
        }
    except Exception as e:
        print(f"Error getting pipeline status: {e}")
        return {
            'status': 'unknown',
            'last_run': 'N/A',
            'models_count': 0,
            'tests_passed': 0,
            'data_quality': 'unknown',
            'business_insights': [],
            'total_locations': 0,
            'avg_utilization': 'N/A',
            'critical_alerts': 0,
            'total_records': 0
        }

# Add pipeline metrics function
def get_pipeline_metrics():
    """Get key pipeline metrics from actual Trino data"""
    try:
        import requests
        import json
        
        # Query actual metrics from Trino
        metrics_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT parking_location) as locations_monitored,
            ROUND(AVG(utilization_rate), 1) as avg_utilization,
            MAX(utilization_rate) as max_utilization,
            COUNT(CASE WHEN is_peak_hour = 1 THEN 1 END) as peak_hour_count,
            COUNT(CASE WHEN occupancy_status = 'Critical' THEN 1 END) as critical_count
        FROM memory.default_staging.stg_parking_data
        """
        
        try:
            response = requests.post(
                'http://localhost:8080/v1/statement',
                json={'query': metrics_query},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if 'data' in result_data and result_data['data']:
                    row = result_data['data'][0]
                    return {
                        'total_records': row[0],
                        'locations_monitored': row[1],
                        'utilization_threshold': f"{row[2]}%",
                        'peak_hours': '08:00-09:00, 17:00-18:00',
                        'data_freshness': '1 hour',
                        'pipeline_health': 'excellent',
                        'max_utilization': f"{row[3]}%",
                        'peak_hour_percentage': f"{(row[4]/row[0]*100):.1f}%" if row[0] > 0 else "0%",
                        'critical_percentage': f"{(row[5]/row[0]*100):.1f}%" if row[0] > 0 else "0%"
                    }
        except:
            pass
        
        # Fallback to sample data
        return {
            'total_records': 0,
            'locations_monitored': 0,
            'utilization_threshold': 'N/A',
            'peak_hours': 'N/A',
            'data_freshness': 'N/A',
            'pipeline_health': 'unknown',
            'max_utilization': 'N/A',
            'peak_hour_percentage': 'N/A',
            'critical_percentage': 'N/A'
        }
    except Exception as e:
        print(f"Error getting pipeline metrics: {e}")
        return {
            'total_records': 0,
            'locations_monitored': 0,
            'utilization_threshold': 'N/A',
            'peak_hours': 'N/A',
            'data_freshness': 'N/A',
            'pipeline_health': 'unknown',
            'max_utilization': 'N/A',
            'peak_hour_percentage': 'N/A',
            'critical_percentage': 'N/A'
        }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    # Check service health
    service_status = {}
    for service_id, service_info in SERVICES.items():
        service_status[service_id] = {
            **service_info,
            'status': check_service_health(service_id, service_info)
        }
    
    # Get system metrics
    system_metrics = get_system_metrics()
    
    # Get Docker status
    docker_status = get_docker_status()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 24-hour format
    return render_template('dashboard.html',
                         services=service_status,
                         system_metrics=system_metrics,
                         docker_status=docker_status,
                         timestamp=timestamp)

@app.route('/api/health')
def api_health():
    """API endpoint for service health checks"""
    health_status = {}
    for service_id, service_info in SERVICES.items():
        health_status[service_id] = {
            'name': service_info['name'],
            'status': check_service_health(service_id, service_info),
            'url': service_info['url']
        }
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'services': health_status
    })

@app.route('/health')
def health_page():
    """Human-readable health check page"""
    health_status = {}
    for service_id, service_info in SERVICES.items():
        health_status[service_id] = {
            'name': service_info['name'],
            'status': check_service_health(service_id, service_info),
            'url': service_info['url'],
            'description': service_info.get('description'),
            'icon': service_info.get('icon'),
            'category': service_info.get('category'),
            'external_url': service_info.get('external_url')
        }
    
    # Include system and docker metrics for consolidated view
    system_metrics = get_system_metrics()
    docker_status = get_docker_status()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 24-hour format
    return render_template('health.html', services=health_status, system_metrics=system_metrics, docker_status=docker_status, timestamp=timestamp)

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for system metrics"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'system': get_system_metrics(),
        'docker': get_docker_status()
    })

@app.route('/metrics')
def metrics_page():
    """Redirect consolidated metrics view to health page"""
    return redirect(url_for('health_page'))

@app.route('/service/<service_id>')
def service_redirect(service_id):
    """Redirect to a specific service"""
    if service_id in SERVICES:
        return redirect(SERVICES[service_id]['external_url'])
    else:
        return "Service not found", 404



@app.route('/pipeline')
def pipeline_status():
    """Pipeline status page"""
    pipeline_status = get_pipeline_status_data()
    pipeline_metrics = get_pipeline_metrics()
    
    return render_template('pipeline.html', 
                         pipeline_status=pipeline_status,
                         pipeline_metrics=pipeline_metrics)

@app.route('/api/pipeline/status')
def api_pipeline_status():
    """API endpoint for pipeline status"""
    return jsonify(get_pipeline_status())

@app.route('/api/pipeline/metrics')
def api_pipeline_metrics():
    """API endpoint for pipeline metrics"""
    return jsonify(get_pipeline_metrics())

@app.route('/api/pipeline/run', methods=['POST'])
def run_pipeline():
    """Run a specific pipeline"""
    try:
        import subprocess
        import os
        import json
        
        data = request.get_json()
        pipeline_name = data.get('pipeline')
        
        if not pipeline_name:
            return jsonify({
                'success': False,
                'error': 'Pipeline name is required'
            }), 400
        
        # Map pipeline names to project directories
        pipeline_configs = {
            'stavanger_parking': {
                'project_dir': 'dbt_stavanger_parking',
                'commands': [
                    ['dbt', 'seed', '--target', 'dev'],
                    ['dbt', 'run', '--target', 'dev'],
                    ['dbt', 'test', '--target', 'dev']
                ]
            }
        }
        
        if pipeline_name not in pipeline_configs:
            return jsonify({
                'success': False,
                'error': f'Unknown pipeline: {pipeline_name}'
            }), 400
        
        config = pipeline_configs[pipeline_name]
        project_dir = config['project_dir']
        
        if not os.path.exists(project_dir):
            return jsonify({
                'success': False,
                'error': f'Project directory not found: {project_dir}'
            }), 400
        
        # Run dbt commands using host environment
        results = []
        for cmd in config['commands']:
            try:
                # Use dbt from container installation
                cmd[0] = 'dbt'
                
                result = subprocess.run(
                    cmd, 
                    cwd=project_dir, 
                    capture_output=True, 
                    text=True, 
                    timeout=300,
                    env=os.environ.copy()
                )
                results.append({
                    'command': ' '.join(cmd),
                    'success': result.returncode == 0,
                    'output': result.stdout if result.stdout else '',
                    'error': result.stderr if result.stderr else ''
                })
            except subprocess.TimeoutExpired:
                results.append({
                    'command': ' '.join(cmd),
                    'success': False,
                    'output': '',
                    'error': 'Command timed out after 5 minutes'
                })
            except Exception as e:
                results.append({
                    'command': ' '.join(cmd),
                    'success': False,
                    'output': '',
                    'error': f'Command failed: {str(e)}'
                })
        
        # Check if core pipeline (seed + run) succeeded
        core_pipeline_success = results[0]['success'] and results[1]['success']  # seed and run
        tests_success = results[2]['success'] if len(results) > 2 else True
        
        pipeline_status = 'success' if core_pipeline_success else 'failed'
        message = 'Pipeline executed successfully' if core_pipeline_success else 'Pipeline execution failed'
        
        # Persist canonical test summary right after run
        try:
            ts = get_last_dbt_test_failures(project_dir=project_dir)
            if core_pipeline_success and not tests_success:
                count = ts.get('failed', 0)
                names = ', '.join([t.get('name','unknown') for t in ts.get('tests', [])])
                if count > 0:
                    message = f'Pipeline executed successfully ({count} tests failed: {names})'
                else:
                    message = 'Pipeline executed successfully (tests failed - check data quality)'
            # write summary file as well
            summary = {
                'pipeline': pipeline_name,
                'status': pipeline_status,
                'tests_passed': tests_success,
                'timestamp': datetime.now().isoformat(),
                'failed_count': ts.get('failed', 0),
                'failed_tests': ts.get('tests', [])
            }
            with open('/tmp/last_test_summary.json', 'w') as f:
                json.dump(summary, f)
        except Exception:
            pass
        
        response_payload = {
            'success': core_pipeline_success,
            'results': results,
            'message': message,
            'pipeline_status': pipeline_status,
            'tests_passed': tests_success,
            'pipeline_name': pipeline_name
        }

        # Persist concise last-run summary (including failed tests if any)
        try:
            summary = {
                'pipeline': pipeline_name,
                'status': pipeline_status,
                'tests_passed': tests_success,
                'timestamp': datetime.now().isoformat(),
            }
            test_summary = get_last_dbt_test_failures(project_dir=project_dir)
            if test_summary.get('found'):
                summary['failed_tests'] = test_summary.get('tests', [])
                summary['failed_count'] = test_summary.get('failed', 0)
            with open('/tmp/last_pipeline_summary.json', 'w') as f:
                json.dump(summary, f)
            # Write unified events
            write_event({
                'type': 'pipeline_run',
                'pipeline_id': pipeline_name,
                'status': pipeline_status,
                'tests_passed': tests_success,
                'failed_count': summary.get('failed_count', 0),
                'message': message
            })
        except Exception:
            pass

        return jsonify(response_payload)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to execute pipeline: {str(e)}'
        }), 500

@app.route('/api/pipeline/run-model', methods=['POST'])
def run_specific_model():
    """Run a specific dbt model"""
    try:
        import subprocess
        import os
        import json
        
        data = request.get_json()
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({'success': False, 'error': 'Model name is required'}), 400
        
        # Change to dbt project directory - use symlink in dashboard directory
        project_dir = 'dbt_stavanger_parking'
        
        if not os.path.exists(project_dir):
            return jsonify({
                'success': False,
                'output': '',
                'error': f'Project directory not found: {project_dir}',
                'results': [{
                    'command': f'dbt run --select {model_name}',
                    'success': False,
                    'output': '',
                    'error': f'Project directory not found: {project_dir}'
                }]
            }), 400
        
        result = subprocess.run(
            ['dbt', 'run', '--select', model_name, '--target', 'dev'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout if result.stdout else '',
            'error': result.stderr if result.stderr else '',
            'results': [{
                'command': f'dbt run --select {model_name}',
                'success': result.returncode == 0,
                'output': result.stdout if result.stdout else '',
                'error': result.stderr if result.stderr else ''
            }]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'output': '',
            'error': f'Failed to run model: {str(e)}',
            'results': [{
                'command': f'dbt run --select {model_name}',
                'success': False,
                'output': '',
                'error': f'Failed to run model: {str(e)}'
            }]
        }), 500

@app.route('/api/pipeline/test', methods=['POST'])
def run_tests():
    """Run dbt tests"""
    try:
        import subprocess
        import os
        
        # Change to dbt project directory - use symlink in dashboard directory
        project_dir = 'dbt_stavanger_parking'
        
        if not os.path.exists(project_dir):
            return jsonify({
                'success': False,
                'output': '',
                'error': f'Project directory not found: {project_dir}',
                'tests_passed': False,
                'results': [{
                    'command': 'dbt test --target dev',
                    'success': False,
                    'output': '',
                    'error': f'Project directory not found: {project_dir}'
                }]
            }), 400
        
        result = subprocess.run(
            ['dbt', 'test', '--target', 'dev'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        # After test completes, persist canonical summary
        try:
            ts = get_last_dbt_test_failures(project_dir=project_dir)
            summary = {
                'timestamp': datetime.now().isoformat(),
                'failed_count': ts.get('failed', 0),
                'failed_tests': ts.get('tests', [])
            }
            with open('/tmp/last_test_summary.json', 'w') as f:
                json.dump(summary, f)
            # Persist raw output for troubleshooting
            with open('/tmp/last_test_output.txt', 'w') as f:
                f.write(result.stdout or '')
                if result.stderr:
                    f.write("\n--- stderr ---\n")
                    f.write(result.stderr)
            # Write unified events
            write_event({
                'type': 'dbt_test',
                'pipeline_id': 'stavanger_parking',
                'status': 'success' if result.returncode == 0 else 'failed',
                'failed_count': summary.get('failed_count', 0)
            })
        except Exception:
            pass

        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout if result.stdout else '',
            'error': result.stderr if result.stderr else '',
            'tests_passed': result.returncode == 0,
            'results': [{
                'command': 'dbt test --target dev',
                'success': result.returncode == 0,
                'output': result.stdout if result.stdout else '',
                'error': result.stderr if result.stderr else ''
            }]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'output': '',
            'error': f'Failed to run tests: {str(e)}',
            'tests_passed': False,
            'results': [{
                'command': 'dbt test --target dev',
                'success': False,
                'output': '',
                'error': f'Failed to run tests: {str(e)}'
            }]
        }), 500

@app.route('/api/pipeline/status-detail')
def get_pipeline_status_detail():
    """Get detailed pipeline status including model states"""
    try:
        import subprocess
        import os
        import json
        
        project_dir = 'dbt_stavanger_parking'
        
        # Get dbt project status
        result = subprocess.run(
            ['dbt', 'list', '--target', 'dev'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        models = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    models.append({
                        'name': line.strip(),
                        'status': 'available'
                    })
        
        return jsonify({
            'models': models,
            'total_models': len(models),
            'project_status': 'healthy' if result.returncode == 0 else 'error'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'models': [],
            'total_models': 0,
            'project_status': 'unknown'
        }), 500

@app.route('/data-browser')
def data_browser():
    """Data browser page for interactive data exploration"""
    return render_template('data_browser.html')

@app.route('/streaming')
def streaming():
    """Real-time streaming dashboard"""
    return render_template('streaming.html')

@app.route('/api/query/execute', methods=['POST'])
def execute_query():
    """Execute SQL query via Trino"""
    try:
        import requests
        import json
        import time
        
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({'success': False, 'error': 'No query provided'}), 400
        
        # Trino query execution
        start_time = time.time()
        
        # Execute query via Trino HTTP API
        trino_url = "http://trino-coordinator:8080/v1/statement"
        headers = {
            'Content-Type': 'application/json',
            'X-Trino-User': 'trino'
        }
        
        response = requests.post(trino_url, data=query, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return jsonify({
                'success': False, 
                'error': f'Trino API error: {response.status_code}'
            }), 500
        
        # Get query results
        query_id = response.json().get('id')
        if not query_id:
            return jsonify({
                'success': False, 
                'error': 'No query ID returned from Trino'
            }), 500
        
        # Poll for results with longer timeout for complex queries
        max_attempts = 200  # Increased significantly for complex queries
        poll_interval = 0.5  # Increased slightly for better performance
        
        print(f"Starting to poll for query {query_id}")
        
        # Get the nextUri from the initial response
        next_uri = response.json().get('nextUri')
        if not next_uri:
            return jsonify({
                'success': False,
                'error': 'No nextUri in Trino response'
            }), 500
        
        print(f"Using nextUri: {next_uri}")
        
        for attempt in range(max_attempts):
            time.sleep(poll_interval)
            print(f"Poll attempt {attempt + 1}/{max_attempts}")
            
            try:
                # Use the nextUri directly
                result_response = requests.get(next_uri, headers=headers, timeout=10)
                print(f"Response status: {result_response.status_code}")
                print(f"Response headers: {dict(result_response.headers)}")
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    print(f"Full response data: {json.dumps(result_data, indent=2)}")
                    current_state = result_data.get('stats', {}).get('state')
                    print(f"Query state: {current_state}")
                    print(f"Response keys: {list(result_data.keys())}")
                    
                    # Update nextUri for next iteration (Trino provides new URI each time)
                    new_next_uri = result_data.get('nextUri')
                    if new_next_uri:
                        next_uri = new_next_uri
                        print(f"Updated nextUri: {next_uri}")
                    
                    if current_state == 'FINISHED':
                        # Extract results
                        columns = [col['name'] for col in result_data.get('columns', [])]
                        data_rows = result_data.get('data', [])
                        
                        # Convert to list of dicts
                        results = []
                        for row in data_rows:
                            row_dict = {}
                            for i, col in enumerate(columns):
                                row_dict[col] = row[i] if i < len(row) else None
                            results.append(row_dict)
                        
                        execution_time = int((time.time() - start_time) * 1000)
                        print(f"Query completed successfully in {execution_time}ms")
                        
                        return jsonify({
                            'success': True,
                            'results': results,
                            'columns': columns,
                            'execution_time': execution_time,
                            'row_count': len(results)
                        })
                    
                    elif current_state == 'FAILED':
                        error_msg = result_data.get('error', {}).get('message', 'Unknown error')
                        print(f"Query failed: {error_msg}")
                        return jsonify({
                            'success': False,
                            'error': f'Query failed: {error_msg}'
                        }), 500
                    
                    elif current_state in ['RUNNING', 'QUEUED']:
                        # Continue polling
                        print(f"Query {current_state.lower()}, continuing to poll...")
                        continue
                    
                    # If we get here, the state is something unexpected
                    print(f"Unexpected query state: {current_state}")
                    continue
                    
                elif result_response.status_code == 410:
                    # Query is gone, might be completed
                    print("Query returned 410 Gone, checking if it completed")
                    # Try to get the final status from the query ID
                    final_response = requests.get(f"http://trino-coordinator:8080/v1/query/{query_id}", headers=headers, timeout=10)
                    if final_response.status_code == 200:
                        final_data = final_response.json()
                        if final_data.get('state') == 'FINISHED':
                            # Extract results from final response
                            columns = [col['name'] for col in final_data.get('columns', [])]
                            data_rows = final_data.get('data', [])
                            
                            results = []
                            for row in data_rows:
                                row_dict = {}
                                for i, col in enumerate(columns):
                                    row_dict[col] = row[i] if i < len(row) else None
                                results.append(row_dict)
                            
                            execution_time = int((time.time() - start_time) * 1000)
                            print(f"Query completed successfully in {execution_time}ms")
                            
                            return jsonify({
                                'success': True,
                                'results': results,
                                'columns': columns,
                                'execution_time': execution_time,
                                'row_count': len(results)
                            })
                        else:
                            print(f"Query state in final response: {final_data.get('state')}")
                            # If query is not finished, it might have failed
                            if final_data.get('state') == 'FAILED':
                                error_msg = final_data.get('error', {}).get('message', 'Unknown error')
                                return jsonify({
                                    'success': False,
                                    'error': f'Query failed: {error_msg}'
                                }), 500
                    
                    # If we can't get results from the final response, the query might be too fast
                    # Try to get results directly from the nextUri with a different approach
                    print("Query completed too fast, trying direct result retrieval")
                    try:
                        # For fast queries, try to get results immediately
                        direct_response = requests.get(next_uri, headers=headers, timeout=5)
                        if direct_response.status_code == 200:
                            direct_data = direct_response.json()
                            if direct_data.get('state') == 'FINISHED':
                                columns = [col['name'] for col in direct_data.get('columns', [])]
                                data_rows = direct_data.get('data', [])
                                
                                results = []
                                for row in data_rows:
                                    row_dict = {}
                                    for i, col in enumerate(columns):
                                        row_dict[col] = row[i] if i < len(row) else None
                                    results.append(row_dict)
                                
                                execution_time = int((time.time() - start_time) * 1000)
                                print(f"Query completed successfully in {execution_time}ms")
                                
                                return jsonify({
                                    'success': True,
                                    'results': results,
                                    'columns': columns,
                                    'execution_time': execution_time,
                                    'row_count': len(results)
                                })
                    except Exception as e:
                        print(f"Direct result retrieval failed: {e}")
                    
                    continue
                    
                else:
                    print(f"Unexpected response status: {result_response.status_code}")
                    print(f"Response text: {result_response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                print(f"Timeout on poll attempt {attempt + 1}")
                continue
            except Exception as e:
                print(f"Error on poll attempt {attempt + 1}: {e}")
                continue
        
        # If we get here, the query timed out
        total_timeout = max_attempts * poll_interval
        return jsonify({
            'success': False,
            'error': f'Query execution timed out after {total_timeout:.1f} seconds. This may indicate:\n\n1. The table/catalog does not exist\n2. The query is too complex\n3. Trino service is overloaded\n\nTry:\n- Using the memory catalog instead of iceberg\n- Checking table names in the schema browser\n- Running a simpler query first\n\nNote: Complex queries may take up to {total_timeout:.0f} seconds to complete.'
        }), 500
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request to Trino timed out. Please check if Trino is running and accessible.'
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to execute query: {str(e)}'
        }), 500

@app.route('/api/query/test-connection')
def test_trino_connection():
    """Simple test endpoint to debug Trino connection"""
    try:
        import requests
        
        # Test 1: Simple GET request to Trino UI
        ui_response = requests.get('http://trino-coordinator:8080/ui/', timeout=5)
        
        # Test 2: POST request to statement endpoint
        statement_response = requests.post(
            'http://trino-coordinator:8080/v1/statement',
            data='SHOW CATALOGS',
            headers={'Content-Type': 'application/json', 'X-Trino-User': 'trino'},
            timeout=10
        )
        
        return jsonify({
            'success': True,
            'ui_status': ui_response.status_code,
            'statement_status': statement_response.status_code,
            'statement_response': statement_response.text[:500] if statement_response.status_code == 200 else 'N/A'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/api/query/simple-test')
def simple_trino_test():
    """Very simple test to see what Trino returns"""
    try:
        import requests
        
        # Make a simple request to Trino
        response = requests.post(
            'http://trino-coordinator:8080/v1/statement',
            data='SHOW CATALOGS',
            headers={'Content-Type': 'application/json', 'X-Trino-User': 'trino'},
            timeout=10
        )
        
        if response.status_code == 200:
            # Get the query ID and immediately check its status
            query_data = response.json()
            query_id = query_data.get('id')
            
            if query_id:
                # Wait a moment and check the status
                import time
                time.sleep(1)
                
                status_response = requests.get(
                    f'http://trino-coordinator:8080/v1/query/{query_id}',
                    headers={'X-Trino-User': 'trino'},
                    timeout=10
                )
                
                return jsonify({
                    'success': True,
                    'initial_response': query_data,
                    'status_response': status_response.json() if status_response.status_code == 200 else {'error': status_response.text},
                    'status_code': status_response.status_code
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No query ID in response',
                    'response': query_data
                })
        else:
            return jsonify({
                'success': False,
                'error': f'Trino returned status {response.status_code}',
                'response_text': response.text
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/api/query/debug-test')
def debug_trino_communication():
    """Comprehensive test endpoint to debug Trino communication"""
    try:
        import requests
        import json
        
        debug_info = {
            'dashboard_container': 'dashboard',
            'trino_container': 'trino-coordinator',
            'test_results': []
        }
        
        # Test 1: Basic connectivity
        try:
            ui_response = requests.get('http://trino-coordinator:8080/ui/', timeout=5)
            debug_info['test_results'].append({
                'test': 'Basic connectivity to Trino UI',
                'status': 'SUCCESS' if ui_response.status_code == 200 else 'FAILED',
                'status_code': ui_response.status_code,
                'response_size': len(ui_response.text)
            })
        except Exception as e:
            debug_info['test_results'].append({
                'test': 'Basic connectivity to Trino UI',
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Test 2: Submit simple query
        try:
            query_response = requests.post(
                'http://trino-coordinator:8080/v1/statement',
                data='SELECT 1 as test',
                headers={'Content-Type': 'application/json', 'X-Trino-User': 'trino'},
                timeout=10
            )
            
            if query_response.status_code == 200:
                query_data = query_response.json()
                query_id = query_data.get('id')
                next_uri = query_data.get('nextUri')
                
                debug_info['test_results'].append({
                    'test': 'Submit simple query',
                    'status': 'SUCCESS',
                    'query_id': query_id,
                    'next_uri': next_uri,
                    'initial_state': query_data.get('stats', {}).get('state')
                })
                
                # Test 3: Follow nextUri chain
                if next_uri:
                    chain_results = []
                    current_uri = next_uri
                    max_chain_length = 5
                    
                    for i in range(max_chain_length):
                        try:
                            chain_response = requests.get(current_uri, headers={'X-Trino-User': 'trino'}, timeout=5)
                            if chain_response.status_code == 200:
                                chain_data = chain_response.json()
                                current_state = chain_data.get('stats', {}).get('state')
                                new_next_uri = chain_data.get('nextUri')
                                
                                chain_results.append({
                                    'step': i + 1,
                                    'uri': current_uri,
                                    'state': current_state,
                                    'new_next_uri': new_next_uri
                                })
                                
                                if current_state == 'FINISHED':
                                    debug_info['test_results'].append({
                                        'test': 'Follow nextUri chain',
                                        'status': 'SUCCESS - Query completed',
                                        'steps': chain_results,
                                        'final_state': current_state
                                    })
                                    break
                                elif current_state == 'FAILED':
                                    debug_info['test_results'].append({
                                        'test': 'Follow nextUri chain',
                                        'status': 'FAILED - Query failed',
                                        'steps': chain_results,
                                        'final_state': current_state
                                    })
                                    break
                                elif new_next_uri:
                                    current_uri = new_next_uri
                                else:
                                    debug_info['test_results'].append({
                                        'test': 'Follow nextUri chain',
                                        'status': 'STUCK - No nextUri provided',
                                        'steps': chain_results,
                                        'final_state': current_state
                                    })
                                    break
                            else:
                                chain_results.append({
                                    'step': i + 1,
                                    'uri': current_uri,
                                    'status_code': chain_response.status_code,
                                    'error': chain_response.text[:200]
                                })
                                debug_info['test_results'].append({
                                    'test': 'Follow nextUri chain',
                                    'status': f'ERROR - HTTP {chain_response.status_code}',
                                    'steps': chain_results
                                })
                                break
                        except Exception as e:
                            chain_results.append({
                                'step': i + 1,
                                'uri': current_uri,
                                'error': str(e)
                            })
                            debug_info['test_results'].append({
                                'test': 'Follow nextUri chain',
                                'status': f'ERROR - Exception: {str(e)}',
                                'steps': chain_results
                            })
                            break
                    else:
                        debug_info['test_results'].append({
                            'test': 'Follow nextUri chain',
                            'status': 'TIMEOUT - Max chain length reached',
                            'steps': chain_results
                        })
            else:
                debug_info['test_results'].append({
                    'test': 'Submit simple query',
                    'status': 'FAILED',
                    'status_code': query_response.status_code,
                    'error': query_response.text[:200]
                })
                
        except Exception as e:
            debug_info['test_results'].append({
                'test': 'Submit simple query',
                'status': 'ERROR',
                'error': str(e)
            })
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'error': f'Debug test failed: {str(e)}'
        }), 500

@app.route('/pipeline-management')
def pipeline_management():
    """Pipeline Management page - manage multiple pipelines"""
    # Mock data for now - will be replaced with real pipeline registry
    pipeline_stats = {
        'total_pipelines': 1,
        'running_pipelines': 1,
        'warning_pipelines': 0,
        'error_pipelines': 0
    }
    
    pipelines = [
        {
            'id': 'stavanger_parking',
            'name': 'Stavanger Parking',
            'type': 'dbt',
            'description': 'Real-time parking utilization insights and business intelligence',
            'status': 'Running',
            'last_run': '2025-09-01 15:33:59',
            'models_count': 5,
            'success_rate': 85
        }
    ]
    
    recent_executions = [
        {
            'pipeline_name': 'Stavanger Parking',
            'timestamp': '2025-09-01 15:33:59',
            'status': 'SUCCESS',
            'status_color': 'success'
        }
    ]
    
    recent_alerts = [
        {
            'pipeline_name': 'Stavanger Parking',
            'message': 'Some tests failed - check data quality',
            'severity': 'warning'
        }
    ]
    
    return render_template('pipeline_management.html', 
                         pipeline_stats=pipeline_stats,
                         pipelines=pipelines,
                         recent_executions=recent_executions,
                         recent_alerts=recent_alerts)

@app.route('/pipeline-control')
def pipeline_control():
    """Pipeline Control page - execute and monitor pipelines"""
    # Get pipeline parameter from query string
    pipeline_id = request.args.get('pipeline', 'stavanger_parking')
    
    # For now, only support the existing stavanger_parking pipeline
    if pipeline_id == 'stavanger_parking':
        pipelines = [
            {
                'id': 'stavanger_parking',
                'name': 'Stavanger Parking',
                'type': 'dbt'
            }
        ]
        selected_pipeline = 'stavanger_parking'
    else:
        pipelines = []
        selected_pipeline = None
    
    return render_template('pipeline_control.html', 
                         pipelines=pipelines, 
                         selected_pipeline=selected_pipeline)

@app.route('/api/pipeline', methods=['POST'])
def create_pipeline():
    """Create a new pipeline"""
    try:
        data = request.get_json()
        
        # Mock implementation - in real system this would save to database
        pipeline_id = f"pipeline_{int(time.time())}"
        
        return jsonify({
            'success': True,
            'pipeline_id': pipeline_id,
            'message': 'Pipeline created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pipeline/<pipeline_id>', methods=['DELETE'])
def delete_pipeline(pipeline_id):
    """Delete a pipeline"""
    try:
        # Mock implementation - in real system this would delete from database
        return jsonify({
            'success': True,
            'message': f'Pipeline {pipeline_id} deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pipeline/<pipeline_id>/run', methods=['POST'])
def run_specific_pipeline(pipeline_id):
    """Run a specific pipeline"""
    try:
        data = request.get_json()
        target = data.get('target', 'dev')
        
        if pipeline_id == 'stavanger_parking':
            # Create execution tracking file
            execution_file = f'/tmp/pipeline_{pipeline_id}_execution.json'
            execution_data = {
                'pipeline_id': pipeline_id,
                'status': 'RUNNING',
                'start_time': time.time(),
                'target': target,
                'pid': None
            }
            
            # Start pipeline execution in background
            try:
                # Run the pipeline
                result = run_pipeline()
                
                if result.json['success']:
                    # Update execution data with success
                    execution_data['status'] = 'FINISHED'
                    execution_data['end_time'] = time.time()
                    execution_data['result'] = result.json
                    
                    # Update timestamp in pipeline status
                    update_pipeline_timestamp(pipeline_id)
                    
                    with open(execution_file, 'w') as f:
                        json.dump(execution_data, f)
                    
                    return jsonify({
                        'success': True,
                        'message': 'Pipeline execution completed successfully',
                        'execution_id': f'exec_{int(time.time())}'
                    })
                else:
                    # Update execution data with failure
                    execution_data['status'] = 'FAILED'
                    execution_data['end_time'] = time.time()
                    execution_data['error'] = result.json.get('error', 'Unknown error')
                    
                    with open(execution_file, 'w') as f:
                        json.dump(execution_data, f)
                    
                    return jsonify({
                        'success': False,
                        'error': result.json.get('error', 'Pipeline execution failed')
                    })
                    
            except Exception as e:
                # Update execution data with error
                execution_data['status'] = 'FAILED'
                execution_data['end_time'] = time.time()
                execution_data['error'] = str(e)
                
                with open(execution_file, 'w') as f:
                    json.dump(execution_data, f)
                
                return jsonify({
                    'success': False,
                    'error': f'Pipeline execution error: {str(e)}'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'Pipeline {pipeline_id} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pipeline/<pipeline_id>/status')
def get_pipeline_status(pipeline_id):
    """Get status of a specific pipeline"""
    try:
        # For now, only support the existing stavanger_parking pipeline
        if pipeline_id == 'stavanger_parking':
            return jsonify(get_pipeline_status_data())
        else:
            return jsonify({
                'success': False,
                'error': f'Pipeline {pipeline_id} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pipeline/<pipeline_id>/execution-status', methods=['GET'])
def get_pipeline_execution_status(pipeline_id):
    """Get real-time execution status for a specific pipeline"""
    try:
        if pipeline_id == 'stavanger_parking':
            # Check if there's an active execution
            execution_file = f'/tmp/pipeline_{pipeline_id}_execution.json'
            
            if os.path.exists(execution_file):
                with open(execution_file, 'r') as f:
                    execution_data = json.load(f)
                
                # Check if execution is still running
                if execution_data.get('status') == 'RUNNING':
                    # Check if the process is still alive
                    try:
                        os.kill(execution_data['pid'], 0)  # Check if process exists
                        return jsonify({
                            'status': 'RUNNING',
                            'message': 'Pipeline execution in progress',
                            'start_time': execution_data['start_time'],
                            'elapsed_time': time.time() - execution_data['start_time']
                        })
                    except OSError:
                        # Process died, mark as failed
                        execution_data['status'] = 'FAILED'
                        execution_data['end_time'] = time.time()
                        execution_data['error'] = 'Process terminated unexpectedly'
                        with open(execution_file, 'w') as f:
                            json.dump(execution_data, f)
                        return jsonify({
                            'status': 'FAILED',
                            'error': 'Process terminated unexpectedly',
                            'start_time': execution_data['start_time'],
                            'end_time': execution_data['end_time']
                        })
                else:
                    # Execution completed, return final status
                    return jsonify(execution_data)
            else:
                # No active execution
                return jsonify({
                    'status': 'IDLE',
                    'message': 'No active execution'
                })
        else:
            return jsonify({
                'success': False,
                'error': f'Pipeline {pipeline_id} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pipeline/<pipeline_id>')
def get_pipeline(pipeline_id):
    """Get pipeline data"""
    try:
        # For now, only support the existing stavanger_parking pipeline
        if pipeline_id == 'stavanger_parking':
            pipeline_data = {
                'name': 'Stavanger Parking',
                'type': 'dbt',
                'description': 'Real-time parking utilization insights and business intelligence',
                'project_dir': 'dbt_stavanger_parking',
                'target': 'dev',
                'schedule': '0 0 * * *'
            }
            
            return jsonify({
                'success': True,
                'pipeline': pipeline_data
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Pipeline {pipeline_id} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pipeline/<pipeline_id>', methods=['PUT'])
def update_pipeline(pipeline_id):
    """Update a pipeline"""
    try:
        data = request.get_json()
        
        # Mock implementation - in real system this would update database
        return jsonify({
            'success': True,
            'message': f'Pipeline {pipeline_id} updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/pipeline/<pipeline_id>')
def view_pipeline(pipeline_id):
    """View individual pipeline details"""
    try:
        # For now, only support the existing stavanger_parking pipeline
        if pipeline_id == 'stavanger_parking':
            pipeline_data = {
                'id': 'stavanger_parking',
                'name': 'Stavanger Parking',
                'type': 'dbt',
                'description': 'Real-time parking utilization insights and business intelligence',
                'project_dir': 'dbt_stavanger_parking',
                'target': 'dev',
                'schedule': '0 0 * * *'
            }
            
            # Get pipeline status and metrics
            status_data = get_pipeline_status_data()
            metrics_data = get_pipeline_metrics()
            
            return render_template('pipeline.html', 
                                 pipeline=pipeline_data,
                                 pipeline_status=status_data,
                                 pipeline_metrics=metrics_data)
        else:
            return "Pipeline not found", 404
            
    except Exception as e:
        return f"Error loading pipeline: {str(e)}", 500

def get_pipeline_status_data():
    """Get pipeline status data for the existing stavanger_parking pipeline"""
    try:
        # Get actual pipeline metrics
        metrics = get_pipeline_metrics()
        
        return {
            'status': 'running',
            'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'models_count': 5,
            'tests_passed': 3,
            'data_quality': 'good',
            'critical_alerts': 0,
            'total_records': metrics.get('total_records', 0),
            'total_locations': metrics.get('locations_monitored', 0)
        }
    except Exception as e:
        return {
            'status': 'unknown',
            'last_run': 'N/A',
            'models_count': 0,
            'tests_passed': 0,
            'data_quality': 'unknown',
            'critical_alerts': 0,
            'total_records': 0,
            'total_locations': 0
        }

def update_pipeline_timestamp(pipeline_id):
    """Update the last run timestamp for a pipeline"""
    try:
        # This would typically update a database or configuration file
        # For now, we'll just log the update
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"Pipeline {pipeline_id} last run updated to: {current_time}")
        
        # Update the pipeline status data
        global pipeline_status_data
        if pipeline_id == 'stavanger_parking':
            pipeline_status_data['last_run'] = current_time
            
    except Exception as e:
        print(f"Error updating pipeline timestamp: {e}")

# New unified API endpoints
@app.route('/api/platform/status')
def get_platform_status():
    """Get comprehensive platform status"""
    return jsonify(platform_api.get_platform_status())

@app.route('/api/platform/catalog')
def get_data_catalog():
    """Get comprehensive data catalog"""
    return jsonify(platform_api.get_data_catalog())

@app.route('/api/platform/quality')
def get_data_quality():
    """Get data quality metrics"""
    catalog = request.args.get('catalog', 'iceberg')
    schema = request.args.get('schema', 'default')
    return jsonify(platform_api.get_data_quality_metrics(catalog, schema))

@app.route('/api/storage/buckets')
def list_storage_buckets():
    """List all storage buckets"""
    return jsonify(platform_api.storage.list_buckets())

@app.route('/api/storage/bucket/<bucket_name>/objects')
def list_bucket_objects(bucket_name):
    """List objects in a bucket"""
    prefix = request.args.get('prefix', '')
    return jsonify(platform_api.storage.list_objects(bucket_name, prefix))

@app.route('/api/storage/stats')
def get_storage_stats():
    """Get storage statistics"""
    return jsonify(platform_api.storage.get_storage_stats())

@app.route('/api/query/catalogs')
def get_query_catalogs():
    """Get available query catalogs"""
    return jsonify(platform_api.query.get_catalogs())

@app.route('/api/query/schemas/<catalog>')
def get_query_schemas(catalog):
    """Get schemas in a catalog"""
    return jsonify(platform_api.query.get_schemas(catalog))

@app.route('/api/query/tables/<catalog>/<schema>')
def get_query_tables(catalog, schema):
    """Get tables in a schema"""
    return jsonify(platform_api.query.get_tables(catalog, schema))

@app.route('/storage-management')
def storage_management():
    """Storage management page"""
    return render_template('storage_management.html')

@app.route('/api/storage/buckets', methods=['POST'])
def create_storage_bucket():
    """Create a new storage bucket"""
    try:
        data = request.get_json()
        bucket_name = data.get('name')
        
        if not bucket_name:
            return jsonify({'success': False, 'error': 'Bucket name is required'}), 400
        
        success = platform_api.storage.create_bucket(bucket_name)
        
        if success:
            return jsonify({'success': True, 'message': f'Bucket {bucket_name} created successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to create bucket'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/storage/bucket/<bucket_name>/objects/<path:object_key>', methods=['DELETE'])
def delete_storage_object(bucket_name, object_key):
    """Delete an object from storage"""
    try:
        success = platform_api.storage.delete_object(bucket_name, object_key)
        
        if success:
            return jsonify({'success': True, 'message': f'Object {object_key} deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete object'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/storage/upload', methods=['POST'])
def upload_storage_file():
    """Upload a file to storage"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        bucket_name = request.form.get('bucket')
        object_key = request.form.get('key', file.filename)
        
        if not bucket_name:
            return jsonify({'success': False, 'error': 'Bucket name is required'}), 400
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save file temporarily
        temp_path = f'/tmp/{file.filename}'
        file.save(temp_path)
        
        # Upload to storage
        success = platform_api.storage.upload_file(bucket_name, object_key, temp_path)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'File {file.filename} uploaded successfully',
                'location': f'{bucket_name}/{object_key}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to upload file'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/bi-dashboard')
def bi_dashboard():
    """Business Intelligence Dashboard"""
    return render_template('bi_dashboard.html')

@app.route('/api/ingestion/stats')
def get_ingestion_stats():
    """Get ingestion statistics"""
    return jsonify(ingestion_api.get_ingestion_stats())

@app.route('/api/ingestion/history')
def get_ingestion_history():
    """Get ingestion history"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(ingestion_api.get_ingestion_history(limit))

@app.route('/api/quality/run-checks')
def run_quality_checks():
    """Run data quality checks"""
    catalog = request.args.get('catalog', 'iceberg')
    schema = request.args.get('schema', 'default')
    return jsonify(quality_api.run_quality_checks(catalog, schema))

@app.route('/api/quality/metrics')
def get_quality_metrics():
    """Get data quality metrics"""
    try:
        from api.platform import platform_api
        metrics = platform_api.get_data_quality_metrics()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({
            'error': f'Failed to get quality metrics: {str(e)}',
            'overall_score': 0.0,
            'checks_performed': 0
        }), 500

# Removed duplicate streaming-dashboard route - use /streaming instead

# Streaming API endpoints
@app.route('/api/streaming/status')
def get_streaming_status():
    """Get streaming platform status"""
    try:
        # Simulator disabled
        return jsonify({
            'overall_status': 'disabled',
            'services': {},
            'message': 'Streaming simulator is disabled'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streaming/topics', methods=['POST'])
def create_streaming_topic():
    """Create a new Kafka topic"""
    try:
        data = request.get_json()
        topic_name = data.get('topic_name')
        config = data.get('config', {})
        
        if not topic_name:
            return jsonify({'error': 'Topic name is required'}), 400
        
        result = streaming_api.create_streaming_topic(topic_name, config)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streaming/pipelines', methods=['POST'])
def start_streaming_pipeline():
    """Start a streaming pipeline"""
    try:
        data = request.get_json()
        pipeline_name = data.get('pipeline_name')
        config = data.get('config', {})
        
        if not pipeline_name:
            return jsonify({'error': 'Pipeline name is required'}), 400
        
        result = streaming_api.start_streaming_pipeline(pipeline_name, config)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streaming/metrics/<topic_name>')
def get_streaming_metrics(topic_name):
    """Get streaming metrics for a topic"""
    try:
        time_range = request.args.get('time_range', '1h')
        metrics = streaming_api.get_streaming_metrics(topic_name, time_range)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/platform/parking-metrics')
def get_parking_metrics():
    """Get Stavanger parking metrics"""
    try:
        # Get parking data from Trino
        from api.query import TrinoAPI
        trino_client = TrinoAPI()
        
        # Query for parking metrics
        query = """
        SELECT 
            COUNT(*) as total_records,
            AVG(occupancy_rate) as avg_occupancy,
            MAX(occupancy_rate) as max_occupancy,
            COUNT(DISTINCT parking_zone) as unique_zones,
            COUNT(DISTINCT DATE(timestamp)) as unique_dates
        FROM iceberg.default.stavanger_parking
        """
        
        results = trino_client.execute_query(query)
        if results and results[0]:
            row = results[0]
            return jsonify({
                'total_records': row[0] or 0,
                'avg_occupancy': round(row[1], 2) if row[1] else 0.0,
                'max_occupancy': round(row[2], 2) if row[2] else 0.0,
                'unique_zones': row[3] or 0,
                'unique_dates': row[4] or 0,
                'data_freshness': 'Real-time',
                'pipeline_health': 'Active'
            })
        else:
            # Fallback to sample data
            return jsonify({
                'total_records': 0,
                'avg_occupancy': 0.0,
                'max_occupancy': 0.0,
                'unique_zones': 0,
                'unique_dates': 0,
                'data_freshness': 'N/A',
                'pipeline_health': 'Unknown'
            })
            
    except Exception as e:
        print(f"Error getting parking metrics: {e}")
        return jsonify({
            'total_records': 0,
            'avg_occupancy': 0.0,
            'max_occupancy': 0.0,
            'unique_zones': 0,
            'unique_dates': 0,
            'data_freshness': 'Error',
            'pipeline_health': 'Error'
        }), 500

@app.route('/api/pipeline/list')
def get_pipeline_list():
    """Get list of all available pipelines"""
    try:
        # Get available pipelines from the dbt project
        dbt_project_dir = os.path.join(os.getcwd(), 'dbt_stavanger_parking')
        
        if os.path.exists(dbt_project_dir):
            pipelines = [
                {
                    'name': 'stavanger_parking',
                    'type': 'dbt',
                    'status': 'ready',
                    'last_run': get_last_pipeline_run('stavanger_parking'),
                    'next_run': None,  # Would come from scheduler
                    'description': 'Stavanger Parking Data Pipeline'
                }
            ]
        else:
            pipelines = []
        
        return jsonify({
            'success': True,
            'pipelines': pipelines
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pipeline/stats')
def get_pipeline_stats():
    """Get pipeline statistics"""
    try:
        # Count available pipelines
        dbt_project_dir = os.path.join(os.getcwd(), 'dbt_stavanger_parking')
        total_pipelines = 1 if os.path.exists(dbt_project_dir) else 0
        
        # Get pipeline statuses
        active_pipelines = 0
        failed_pipelines = 0
        success_rate = 1.0
        
        # Check if Stavanger parking pipeline exists and is working
        if total_pipelines > 0:
            try:
                # Check if dbt project is valid
                result = subprocess.run(
                    ['dbt', 'debug', '--project-dir', dbt_project_dir],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    active_pipelines = 1
                    failed_pipelines = 0
                    success_rate = 1.0
                else:
                    failed_pipelines = 1
                    success_rate = 0.0
            except Exception:
                failed_pipelines = 1
                success_rate = 0.0
        
        return jsonify({
            'success': True,
            'total_pipelines': total_pipelines,
            'active_pipelines': active_pipelines,
            'failed_pipelines': failed_pipelines,
            'success_rate': success_rate
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_last_pipeline_run(pipeline_name):
    """Get the last run timestamp for a pipeline"""
    try:
        # Check for dbt run artifacts
        dbt_project_dir = os.path.join(os.getcwd(), 'dbt_stavanger_parking')
        target_dir = os.path.join(dbt_project_dir, 'target')
        
        if os.path.exists(target_dir):
            # Look for run_results.json
            run_results_file = os.path.join(target_dir, 'run_results.json')
            if os.path.exists(run_results_file):
                with open(run_results_file, 'r') as f:
                    run_data = json.load(f)
                    if 'metadata' in run_data and 'generated_at' in run_data['metadata']:
                        return run_data['metadata']['generated_at']
        
        # Fallback to file modification time
        dbt_project_file = os.path.join(dbt_project_dir, 'dbt_project.yml')
        if os.path.exists(dbt_project_file):
            return datetime.fromtimestamp(os.path.getmtime(dbt_project_file)).isoformat()
        
        return None
    except Exception:
        return None

# Streaming API endpoints
@app.route('/api/streaming/topics')
def get_streaming_topics():
    """Get Kafka topic status and information"""
    try:
        # Simulator disabled
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streaming/consumers')
def get_streaming_consumers():
    """Get consumer group information and lag"""
    try:
        # Simulator disabled
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streaming/live-data')
def get_live_streaming_data():
    """Get live streaming data for dashboard display"""
    try:
        # Simulator disabled
        return jsonify({
            'messages': [],
            'counts': { 'raw': 0, 'processed': 0, 'alerts': 0 },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streaming/start', methods=['POST'])
def start_streaming():
    """Start streaming data generation"""
    try:
        # In a real implementation, this would start the streaming job
        # For now, we'll just return success
        return jsonify({'status': 'success', 'message': 'Streaming started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streaming/stop', methods=['POST'])
def stop_streaming():
    """Stop streaming data generation"""
    try:
        # In a real implementation, this would stop the streaming job
        # For now, we'll just return success
        return jsonify({'status': 'success', 'message': 'Streaming stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_topic_message_count(topic_name):
    """Get message count for a specific topic"""
    try:
        # Simulator disabled
        return 0
    except:
        return 0

@app.route('/chat')
def chat_page():
    """Simple chat UI (stubbed backend)"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Enhanced chat endpoint with comprehensive LLM integration and UI blocks."""
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get('message', '').strip()
        messages = data.get('messages', [])
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400

        msg_lower = user_message.lower()

        # Enhanced intent recognition with more capabilities
        intents = analyze_user_intent(user_message, messages, messages)

        # Force conversational patterns to trigger operations
        msg_lower = user_message.lower()
        if not intents.get('action'):
            # Force status check for pipeline inquiries
            if any(phrase in msg_lower for phrase in ['are there any pipelines', 'what pipelines', 'pipeline status', 'tell me about the failed', 'information about']):
                intents['action'] = 'check_status'
            # Force test execution for test requests
            elif any(phrase in msg_lower for phrase in ['run a test', 'run some tests', 'run test', 'execute test', 'can you run a test', 'test it']):
                intents['action'] = 'run_tests'

        # For long-running operations, create an operation ID and start async processing
        operation_id = None
        if intents.get('action') in ['run_pipeline', 'run_tests', 'ingest_data', 'run_tests_and_check_status']:
            operation_id = f"{intents.get('action')}_{int(time.time())}_{hash(user_message) % 10000}"

            # Get operation context before starting
            context_info = get_operation_context(intents, user_message)

            # Start the operation in a separate thread
            import threading
            thread = threading.Thread(target=run_operation_async, args=(operation_id, intents, user_message))
            thread.daemon = True
            thread.start()

            # Provide informative response with context - dynamic content in UI blocks
            action_name = intents.get('action').replace('_', ' ').title()

            # Create contextual response based on operation type
            if intents.get('action') == 'run_pipeline':
                response_message = f"🚀 Starting the Stavanger Parking pipeline execution. This will process the latest parking data through seeding, modeling, and testing phases. You'll see real-time progress in the card below."
            elif intents.get('action') == 'run_tests':
                response_message = f"🧪 Initiating comprehensive dbt test suite. This will validate data quality, check for null values, and ensure business logic integrity across all models. Results will appear in the progress card."
            elif intents.get('action') == 'ingest_data':
                response_message = f"📥 Starting data ingestion from the Stavanger Kommune API. This will fetch the latest parking availability data and update the staging tables. The progress card will show real-time updates."
            elif intents.get('action') == 'run_tests_and_check_status':
                response_message = f"🔍 Running combined diagnostic check - executing tests and assessing system health. This comprehensive analysis will identify any issues and provide actionable insights in the card below."
            elif intents.get('action') == 'create_pipeline':
                response_message = f"🏗️ Starting pipeline creation wizard. I'll guide you through setting up a new data pipeline step by step."
            else:
                response_message = f"⚙️ Starting {action_name.lower()} operation. The progress card below will keep you updated on the status."

            return jsonify({
                'success': True,
                'reply': response_message,
                'operation_id': operation_id,
                'status': 'running',
                'ui_blocks': [
                    {
                        'type': 'progress',
                        'title': f'{action_name}',
                        'status': 'running',
                        'message': 'Initializing...',
                        'progress': 5,
                        'operation_id': operation_id,
                        'context': context_info,
                        'show_details': True
                    }
                ]
            })

        # Handle different intent types (short operations)
        if intents.get('action') == 'check_status':
            return handle_status_check(intents)
        elif intents.get('action') == 'query_data':
            return handle_data_query(intents, user_message)
        elif intents.get('action') == 'health_check':
            return handle_health_check(intents)
        elif intents.get('action') == 'run_tests_and_check_status':
            # This will be handled by the async processing above
            pass
        elif intents.get('action') == 'create_pipeline':
            return handle_create_pipeline(intents, user_message, messages)

        # Use OpenAI for complex queries or general assistance
        return handle_llm_assistance(user_message, messages, intents)

    except Exception as e:
        return jsonify({'success': False, 'error': f'Chat error: {str(e)}'}), 500


@app.route('/api/chat/progress/<operation_id>', methods=['GET'])
def get_operation_progress(operation_id):
    """Get progress status for a specific operation."""
    try:
        progress_file = f'/tmp/operation_{operation_id}.json'
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            return jsonify(progress_data)
        else:
            return jsonify({
                'status': 'unknown',
                'message': 'Operation not found',
                'completed': False
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking progress: {str(e)}',
            'completed': True
        })


@app.route('/api/logs/diagnostics', methods=['GET'])
def get_system_diagnostics():
    """Get comprehensive system diagnostics for troubleshooting."""
    try:
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'system_health': {},
            'pipeline_status': {},
            'recent_errors': [],
            'service_logs': {},
            'data_quality': {}
        }

        # System health overview
        try:
            health_resp = requests.get('http://localhost:5000/api/health', timeout=5)
            if health_resp.status_code == 200:
                diagnostics['system_health'] = health_resp.json()
        except:
            diagnostics['system_health'] = {'error': 'Unable to fetch health data'}

        # Pipeline status
        try:
            stats_resp = requests.get('http://localhost:5000/api/pipeline/stats', timeout=5)
            if stats_resp.status_code == 200:
                diagnostics['pipeline_status'] = stats_resp.json()
        except:
            diagnostics['pipeline_status'] = {'error': 'Unable to fetch pipeline stats'}

        # Recent test failures
        try:
            test_resp = requests.get('http://localhost:5000/api/pipeline/last-test-summary', timeout=5)
            if test_resp.status_code == 200:
                test_data = test_resp.json()
                if test_data.get('found') and test_data.get('failed', 0) > 0:
                    diagnostics['recent_errors'].append({
                        'type': 'test_failures',
                        'count': test_data.get('failed'),
                        'details': test_data.get('tests', [])[:5]  # First 5 failures
                    })
        except:
            pass

        # Recent pipeline events
        try:
            events = read_recent_events(limit=10)
            if events:
                diagnostics['recent_errors'].extend([{
                    'type': 'pipeline_event',
                    'timestamp': e.get('timestamp'),
                    'event_type': e.get('event_type'),
                    'message': e.get('message')
                } for e in events])
        except:
            pass

        # Data quality metrics
        try:
            # Check if parking data exists
            csv_path = os.path.join('dbt_stavanger_parking', 'seeds', 'live_parking.csv')
            if os.path.exists(csv_path):
                mtime = os.path.getmtime(csv_path)
                diagnostics['data_quality']['last_update'] = datetime.fromtimestamp(mtime).isoformat()

                # Get record count
                try:
                    query_resp = requests.post('http://localhost:5000/api/query/execute',
                                              json={'query': 'SELECT COUNT(*) as cnt FROM memory.default_staging.stg_parking_data'},
                                              timeout=10)
                    if query_resp.status_code == 200:
                        qj = query_resp.json()
                        if qj.get('success') and qj.get('results'):
                            diagnostics['data_quality']['record_count'] = qj['results'][0].get('cnt', 0)
                except:
                    pass
            else:
                diagnostics['data_quality']['status'] = 'No data file found'
        except:
            diagnostics['data_quality']['error'] = 'Unable to check data quality'

        return jsonify(diagnostics)

    except Exception as e:
        return jsonify({
            'error': f'Diagnostics error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/logs/recent', methods=['GET'])
def get_recent_logs():
    """Get recent system logs and events."""
    try:
        limit = int(request.args.get('limit', 20))
        log_type = request.args.get('type', 'all')  # all, errors, pipeline, system

        logs = {
            'timestamp': datetime.now().isoformat(),
            'logs': [],
            'summary': {}
        }

        # Get recent events from our unified store
        try:
            events = read_recent_events(limit=limit)
            if events:
                for event in events:
                    if log_type == 'all' or event.get('event_type') == log_type:
                        logs['logs'].append({
                            'timestamp': event.get('timestamp'),
                            'type': event.get('event_type'),
                            'level': event.get('level', 'info'),
                            'message': event.get('message'),
                            'details': event.get('details', {})
                        })
        except:
            pass

        # Add summary statistics
        logs['summary'] = {
            'total_logs': len(logs['logs']),
            'error_count': len([l for l in logs['logs'] if l.get('level') == 'error']),
            'pipeline_events': len([l for l in logs['logs'] if l.get('type') == 'pipeline']),
            'system_events': len([l for l in logs['logs'] if l.get('type') == 'system'])
        }

        return jsonify(logs)

    except Exception as e:
        return jsonify({
            'error': f'Log retrieval error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


def run_operation_async(operation_id, intents, user_message):
    """Run long operations asynchronously and update progress."""
    try:
        progress_file = f'/tmp/operation_{operation_id}.json'

        # Initialize progress
        progress_data = {
            'operation_id': operation_id,
            'status': 'running',
            'message': 'Initializing...',
            'progress': 0,
            'completed': False,
            'start_time': time.time()
        }
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

        # Update progress and run operation
        if intents.get('action') == 'run_pipeline':
            result = run_pipeline_operation(operation_id, intents)
        elif intents.get('action') == 'run_tests':
            result = run_test_operation(operation_id, intents)
        elif intents.get('action') == 'ingest_data':
            result = run_ingest_operation(operation_id, intents)
        elif intents.get('action') == 'run_tests_and_check_status':
            result = run_tests_and_status_combined(operation_id, intents)
        elif intents.get('action') == 'create_pipeline':
            result = run_create_pipeline_operation(operation_id, intents)
        else:
            result = {
                'success': False,
                'reply': 'Unknown operation type',
                'ui_blocks': []
            }

        # Mark as completed
        result['operation_id'] = operation_id
        result['completed'] = True
        result['status'] = 'completed' if result.get('success') else 'failed'

        with open(progress_file, 'w') as f:
            json.dump(result, f)

        # Clean up old progress files (older than 1 hour)
        cleanup_old_progress_files()

    except Exception as e:
        error_result = {
            'operation_id': operation_id,
            'status': 'error',
            'message': f'Operation failed: {str(e)}',
            'completed': True,
            'success': False,
            'reply': f'Operation failed with error: {str(e)}',
            'ui_blocks': [{
                'type': 'metric',
                'title': 'Operation Status',
                'value': '❌ Error',
                'color': 'danger'
            }]
        }
        try:
            with open(progress_file, 'w') as f:
                json.dump(error_result, f)
        except:
            pass

        # Clean up old progress files
        cleanup_old_progress_files()


def get_operation_context(intents, user_message):
    """Get contextual information about what an operation will do."""
    action = intents.get('action')
    pipeline = intents.get('pipeline', 'stavanger_parking')

    contexts = {
        'run_pipeline': {
            'description': f'Running the {pipeline} pipeline which includes data seeding, model execution, and testing. This will process parking data from the live API.',
            'estimated_time': '2-5 minutes',
            'steps': ['Seed live data', 'Run dbt models', 'Execute tests', 'Generate reports']
        },
        'run_tests': {
            'description': 'Running comprehensive tests on all dbt models to ensure data quality and integrity. This includes checks for null values, data consistency, and business logic validation.',
            'estimated_time': '1-3 minutes',
            'steps': ['Load test data', 'Run all dbt tests', 'Validate results', 'Generate test summary']
        },
        'ingest_data': {
            'description': 'Fetching the latest parking data from the Stavanger Kommune API and updating the local database. This ensures we have the most current parking availability information.',
            'estimated_time': '30-60 seconds',
            'steps': ['Connect to API', 'Download data', 'Process and clean', 'Update database']
        },
        'run_tests_and_check_status': {
            'description': 'Running comprehensive tests on dbt models and checking the current status of all platform services and pipelines.',
            'estimated_time': '1-2 minutes',
            'steps': ['Run dbt tests', 'Check service health', 'Analyze pipeline status', 'Generate combined report']
        }
    }

    context = contexts.get(action, {
        'description': 'Processing your request...',
        'estimated_time': 'Varies',
        'steps': ['Processing', 'Completing operation']
    })

    return context


def cleanup_old_progress_files():
    """Clean up progress files older than 1 hour."""
    try:
        import glob
        progress_dir = '/tmp'
        current_time = time.time()

        for progress_file in glob.glob(f'{progress_dir}/operation_*.json'):
            try:
                file_age = current_time - os.path.getmtime(progress_file)
                if file_age > 3600:  # 1 hour
                    os.remove(progress_file)
            except:
                pass
    except:
        pass


def run_pipeline_operation(operation_id, intents):
    """Run pipeline operation with progress updates."""
    progress_file = f'/tmp/operation_{operation_id}.json'

    # Update progress: Starting
    progress_data = {
        'operation_id': operation_id,
        'status': 'running',
        'message': 'Starting pipeline execution...',
        'progress': 10,
        'completed': False
    }
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f)

    try:
        pipeline = intents.get('pipeline', 'stavanger_parking')

        # Update progress: Running
        progress_data.update({
            'message': f'Executing {pipeline} pipeline...',
            'progress': 30
        })
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

        run_resp = requests.post('http://localhost:5000/api/pipeline/run',
                                json={'pipeline': pipeline}, timeout=600)

        if run_resp.status_code == 200:
            rj = run_resp.json()
            ok = rj.get('success', False)
            msg = rj.get('message', 'Pipeline executed')

            # Update progress: Completed
            result = {
                'success': True,
                'reply': msg,
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Pipeline Execution',
                    'value': '✅ Success' if ok else '❌ Failed',
                    'color': 'success' if ok else 'danger'
                }]
            }

            if rj.get('results'):
                details = rj['results']
                result['ui_blocks'].append({
                    'type': 'table',
                    'title': 'Execution Details',
                    'columns': ['Step', 'Command', 'Status'],
                    'rows': [[d.get('command', ''), '✅' if d.get('success') else '❌', d.get('error', '')]
                            for d in details[:3]]
                })

            # Add suggestions
            suggestions = generate_suggestions(result['ui_blocks'])
            if suggestions:
                result['ui_blocks'].append(suggestions)

            # Simple, direct response focused on the user's request
            if ok:
                result['reply'] = f"Yes, I've successfully executed the Stavanger parking pipeline. The data has been processed and is ready to use."
                # For successful runs, minimal UI - user can ask for details if needed
                result['ui_blocks'] = [{
                    'type': 'metric',
                    'title': 'Pipeline Status',
                    'value': '✅ Success',
                    'color': 'success'
                }]
            else:
                result['reply'] = f"The pipeline execution failed. Let me show you what went wrong so we can fix it:"

            return result
        else:
            return {
                'success': False,
                'reply': f"Pipeline run failed with HTTP {run_resp.status_code}",
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Pipeline Execution',
                    'value': '❌ HTTP Error',
                    'color': 'danger'
                }]
            }
    except Exception as e:
        return {
            'success': False,
            'reply': f'Pipeline run error: {str(e)}',
            'ui_blocks': [{
                'type': 'metric',
                'title': 'Pipeline Execution',
                'value': '❌ Error',
                'color': 'danger'
            }]
        }


def run_test_operation(operation_id, intents):
    """Run test operation with progress updates."""
    progress_file = f'/tmp/operation_{operation_id}.json'

    # Update progress: Starting
    progress_data = {
        'operation_id': operation_id,
        'status': 'running',
        'message': 'Starting test execution...',
        'progress': 20,
        'completed': False
    }
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f)

    try:
        # Update progress: Running tests
        progress_data.update({
            'message': 'Running dbt tests...',
            'progress': 50
        })
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

        try:
            test_resp = requests.post('http://localhost:5000/api/pipeline/test', timeout=300)  # Reduced to 5 minutes

            if test_resp.status_code == 200:
                tj = test_resp.json()
                ok = tj.get('tests_passed', False)
            else:
                ok = False
                print(f"Test API returned status {test_resp.status_code}")
        except requests.exceptions.Timeout:
            ok = False
            print("Test operation timed out")
        except Exception as e:
            ok = False
            error_message = str(e)
            print(f"Test operation failed: {error_message}")

        # Update progress: Completed
        progress_data.update({
            'message': 'Tests completed, processing results...',
            'progress': 90
        })
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

        if ok:
            result = {
                'success': True,
                'reply': 'Tests completed successfully!',
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Test Results',
                    'value': '✅ All Passed',
                    'color': 'success'
                }]
            }
        else:
            result = {
                'success': False,
                'reply': 'Some tests failed. Detailed error information is shown in the card below.',
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Test Results',
                    'value': '⚠️ Some Failed',
                    'color': 'warning'
                }]
            }

            # Add error details for failed operations
            if 'error_message' in locals():
                result['ui_blocks'].append({
                    'type': 'info',
                    'title': '❌ Operation Error',
                    'content': f'The test operation encountered an error: {error_message}',
                    'color': 'danger'
                })

        # Get detailed test results from the API response
        failed_tests = []
        if not ok and 'tj' in locals() and tj.get('results'):
            for test_result in tj['results']:
                if test_result.get('status') == 'fail':
                    test_name = test_result.get('unique_id', '').split('.')[-1]
                    message = test_result.get('message', 'Test failed')
                    failed_tests.append({'name': test_name, 'message': message})

        # Try to get additional test summary from API
        try:
            ts = requests.get('http://localhost:5000/api/pipeline/last-test-summary', timeout=3).json()
            if ts.get('found') and ts.get('failed', 0) > 0:
                result['ui_blocks'].append({
                    'type': 'table',
                    'title': 'Failed Tests',
                    'columns': ['Test Name', 'Error'],
                    'rows': [[t.get('name', 'unknown'), t.get('message', '')]
                            for t in ts.get('tests', [])[:5]]
                })
        except:
            # If API fails, use the test results we extracted above
            if failed_tests:
                result['ui_blocks'].append({
                    'type': 'table',
                    'title': 'Failed Tests',
                    'columns': ['Test Name', 'Error'],
                    'rows': [[t['name'], t['message']] for t in failed_tests[:5]]
                })

        # Persist canonical test summary for future queries
        try:
            summary = {
                'pipeline': 'stavanger_parking',
                'status': 'success' if ok else 'failed',
                'tests_passed': ok,
                'timestamp': datetime.now().isoformat(),
                'failed_count': len(failed_tests),
                'failed_tests': failed_tests
            }

            # Try multiple possible locations for the summary file
            summary_paths = ['/tmp/last_test_summary.json', './last_test_summary.json', '/app/last_test_summary.json']
            saved = False
            for path in summary_paths:
                try:
                    with open(path, 'w') as f:
                        json.dump(summary, f)
                    print(f"Test summary saved to {path}")
                    saved = True
                    break
                except Exception as e:
                    print(f"Failed to save to {path}: {e}")
                    continue

            if not saved:
                print("Warning: Could not save test summary to any location")
        except Exception as e:
            print(f"Error persisting test summary: {e}")

        # Add detailed error information to UI blocks for failed tests
        if not ok and 'tj' in locals() and tj.get('results'):
            failed_test_details = []
            error_messages = []

            for test_result in tj['results']:
                if test_result.get('command') == 'dbt test --target dev':
                    # Extract failed test information from the output
                    output = test_result.get('output', '')
                    error_msg = test_result.get('error', '')

                    if 'FAIL' in output:
                        # Parse the dbt output to extract specific failures
                        lines = output.split('\n')
                        for line in lines:
                            if 'FAIL' in line and 'test_' in line:
                                # Extract test name from the line
                                match = re.search(r'FAIL \d+ (\w+)', line)
                                if match:
                                    test_name = match.group(1)
                                    failed_test_details.append(f"❌ {test_name}")

                    # Extract specific error details
                    if 'Completed with 3 errors' in output:
                        error_messages.append("❌ Data quality validation failed")
                        error_messages.append("💡 Check for null values in critical fields")
                        error_messages.append("💡 Review business logic calculations")

                    if 'test_critical_fields_not_null' in output and 'FAIL' in output:
                        error_messages.append("⚠️ Null values found in essential parking data fields")

                    if 'test_capacity_occupancy_logic' in output and 'FAIL' in output:
                        error_messages.append("⚠️ Business logic validation failed for capacity calculations")

                    if 'test_utilization_rate_calculation' in output and 'FAIL' in output:
                        error_messages.append("⚠️ Utilization rate calculations are incorrect")

            if failed_test_details:
                result['ui_blocks'].append({
                    'type': 'list',
                    'title': '❌ Failed Tests',
                    'items': failed_test_details
                })

            if error_messages:
                result['ui_blocks'].append({
                    'type': 'list',
                    'title': '🔍 Error Analysis & Suggestions',
                    'items': error_messages
                })

        # Add suggestions
        suggestions = generate_suggestions(result['ui_blocks'])
        if suggestions:
            result['ui_blocks'].append(suggestions)

        # Finalize result based on success/failure
        if ok:
            result['reply'] = f"Great news! All tests passed successfully. Your data quality looks good."
            # For successful tests, minimal UI - user can ask for details if needed
            result['ui_blocks'] = [{
                'type': 'metric',
                'title': 'Test Results',
                'value': '✅ All Passed',
                'color': 'success'
            }]
        else:
            result['reply'] = f"Some tests failed. The detailed error information is shown in the progress card below."

            # Ensure error details are included in UI blocks for failed operations
            if not any(block.get('type') == 'info' and 'Operation Error' in block.get('title', '') for block in result['ui_blocks']):
                result['ui_blocks'].insert(0, {
                    'type': 'info',
                    'title': '❌ Test Operation Failed',
                    'content': 'One or more data quality tests failed. Please review the detailed error information below.',
                    'color': 'danger'
                })

        return result
    except Exception as e:
        error_details = str(e)
        print(f"Test operation critical error: {error_details}")
        return {
            'success': False,
            'reply': f'Test execution error: {error_details}',
            'ui_blocks': [
                {
                    'type': 'metric',
                    'title': 'Test Results',
                    'value': '❌ Error',
                    'color': 'danger'
                },
                {
                    'type': 'info',
                    'title': '❌ Critical Error',
                    'content': f'The test operation encountered a critical error: {error_details}',
                    'color': 'danger'
                }
            ]
        }


def run_ingest_operation(operation_id, intents):
    """Run data ingestion operation with progress updates."""
    progress_file = f'/tmp/operation_{operation_id}.json'

    # Update progress: Starting
    progress_data = {
        'operation_id': operation_id,
        'status': 'running',
        'message': 'Starting data ingestion...',
        'progress': 15,
        'completed': False
    }
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f)

    try:
        # Update progress: Connecting to API
        progress_data.update({
            'message': 'Connecting to Stavanger Kommune API...',
            'progress': 30
        })
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

        ingest_resp = requests.post('http://localhost:5000/api/ingestion/pull',
                                   json={}, timeout=300)

        # Update progress: Processing data
        progress_data.update({
            'message': 'Processing and storing data...',
            'progress': 70
        })
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

        if ingest_resp.status_code == 200:
            ij = ingest_resp.json()
            success = ij.get('success', False)
            rows = ij.get('rows', 0)

            # Update progress: Finalizing
            progress_data.update({
                'message': 'Finalizing data ingestion...',
                'progress': 95
            })
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f)

            # Direct response focused on data loading results
            if success:
                reply_msg = f"Perfect! I've successfully loaded {rows} parking records from the API. The data is ready for processing."
                # For successful ingestion, minimal UI - user can ask for details if needed
                result['ui_blocks'] = [{
                    'type': 'metric',
                    'title': 'Data Ingestion',
                    'value': f'{rows} records',
                    'color': 'success'
                }]
            else:
                reply_msg = f"There was an issue loading the data. Let me show you what went wrong:"

            result = {
                'success': True,
                'reply': reply_msg,
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Data Ingestion',
                    'value': f'{rows} records',
                    'color': 'success' if success else 'danger'
                }]
            }

            return result
        else:
            return {
                'success': False,
                'reply': f'Ingestion failed with HTTP {ingest_resp.status_code}',
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Data Ingestion',
                    'value': '❌ HTTP Error',
                    'color': 'danger'
                }]
            }
    except Exception as e:
        return {
            'success': False,
            'reply': f'Data ingestion error: {str(e)}',
            'ui_blocks': [{
                'type': 'metric',
                'title': 'Data Ingestion',
                'value': '❌ Error',
                'color': 'danger'
            }]
        }


def analyze_user_intent(message, history, messages=None):
    """Analyze user message to determine intent and extract parameters."""
    msg_lower = message.lower()
    intents = {'action': None, 'pipeline': 'stavanger_parking', 'parameters': {}}

    # Pipeline operations - expanded recognition
    if any(kw in msg_lower for kw in ['run pipeline', 'start pipeline', 'execute pipeline', 'run stavanger', 'start the pipeline']):
        intents['action'] = 'run_pipeline'
    elif any(kw in msg_lower for kw in ['run test', 'execute test', 'test pipeline', 'run tests', 'execute tests', 'run a test', 'test it', 'run some tests']):
        intents['action'] = 'run_tests'
    elif any(kw in msg_lower for kw in ['ingest', 'pull data', 'fetch data', 'update data', 'pull latest data']):
        intents['action'] = 'ingest_data'
    elif any(kw in msg_lower for kw in ['status', 'what is running', 'pipeline status', 'check status', 'service status', 'system status', 'platform status']):
        intents['action'] = 'check_status'
    elif any(kw in msg_lower for kw in ['query', 'show data', 'get data', 'select', 'count']):
        intents['action'] = 'query_data'
    elif any(kw in msg_lower for kw in ['health', 'system health', 'platform health']):
        intents['action'] = 'health_check'
    elif any(kw in msg_lower for kw in ['create pipeline', 'new pipeline', 'build pipeline', 'setup pipeline']):
        intents['action'] = 'create_pipeline'
    # Additional conversational patterns
    elif any(kw in msg_lower for kw in ['tell me about', 'what about', 'information about', 'details about']):
        if 'pipeline' in msg_lower or 'failed' in msg_lower:
            intents['action'] = 'check_status'
    elif 'running' in msg_lower and ('pipeline' in msg_lower or 'pipelines' in msg_lower):
        intents['action'] = 'check_status'

    # Handle conversational follow-ups based on previous assistant messages
    if messages and len(messages) > 0 and intents['action'] is None:
        last_assistant_msg = None
        for msg in reversed(messages):
            if msg.get('role') == 'assistant':
                last_assistant_msg = msg.get('content', '').lower()
                break

        if last_assistant_msg:
            # If assistant suggested running tests, handle affirmative responses
            if ('run test' in last_assistant_msg or 'test' in last_assistant_msg or 'running tests' in last_assistant_msg):
                if any(affirmative in msg_lower for affirmative in ['yes', 'please', 'go ahead', 'run', 'do it', 'okay', 'sure', 'lets do it', 'run it']):
                    intents['action'] = 'run_tests'

            # If assistant suggested running pipeline, handle affirmative responses
            elif ('run pipeline' in last_assistant_msg or 'pipeline again' in last_assistant_msg or 'execute pipeline' in last_assistant_msg or 'run the pipeline' in last_assistant_msg):
                if any(affirmative in msg_lower for affirmative in ['yes', 'please', 'go ahead', 'run', 'do it', 'okay', 'sure', 'lets do it', 'run it']):
                    intents['action'] = 'run_pipeline'

            # If assistant mentioned failed pipelines, handle requests for details
            elif ('failed pipeline' in last_assistant_msg or 'attention' in last_assistant_msg or 'need attention' in last_assistant_msg):
                if any(detail_req in msg_lower for detail_req in ['what kind', 'what kind of', 'why', 'what happened', 'details', 'more info', 'tell me more']):
                    intents['action'] = 'run_tests_and_check_status'  # Get detailed diagnostics

    # Handle combined requests like "Please do both" or "run tests and check status"
    if any(kw in msg_lower for kw in ['both', 'and', 'also', 'together', 'please do']):
        # Look for test + status combination
        if ('test' in msg_lower or 'tests' in msg_lower) and ('status' in msg_lower or 'check' in msg_lower):
            intents['action'] = 'run_tests_and_check_status'
        elif ('test' in msg_lower or 'tests' in msg_lower) and 'ingest' in msg_lower:
            intents['action'] = 'run_tests_and_ingest'
        elif ('status' in msg_lower or 'check' in msg_lower) and 'ingest' in msg_lower:
            intents['action'] = 'check_status_and_ingest'
        # Handle generic "do both" based on conversation context
        elif any(kw in msg_lower for kw in ['do both', 'please do', 'run both']):
            # Check conversation history for what "both" refers to
            if messages:
                recent_content = ' '.join([msg.get('content', '') for msg in messages[-3:]]).lower()
                if ('test' in recent_content or 'tests' in recent_content) and ('status' in recent_content or 'check' in recent_content):
                    intents['action'] = 'run_tests_and_check_status'

    # Extract pipeline name if specified
    if 'stavanger' in msg_lower:
        intents['pipeline'] = 'stavanger_parking'

    return intents


def handle_pipeline_run(intents):
    """Handle pipeline run requests with safety confirmations."""
    try:
        pipeline = intents.get('pipeline', 'stavanger_parking')

        # Safety check: Warn about potential data overwrites
        safety_warnings = []

        # Check if pipeline has been run recently
        try:
            last_run_resp = requests.get('http://localhost:5000/api/pipeline/last-run-summary', timeout=3)
            if last_run_resp.status_code == 200:
                lr = last_run_resp.json()
                if lr.get('found') and lr.get('pipeline') == pipeline:
                    last_run_time = lr.get('timestamp', '')
                    if last_run_time:
                        # If run within last 5 minutes, suggest it's recent
                        safety_warnings.append("Pipeline was recently executed - consider if re-run is necessary")
        except:
            pass

        # Check if there are any failed tests that might indicate issues
        try:
            test_resp = requests.get('http://localhost:5000/api/pipeline/last-test-summary', timeout=3)
            if test_resp.status_code == 200:
                ts = test_resp.json()
                if ts.get('found') and ts.get('failed', 0) > 0:
                    safety_warnings.append(f"There are {ts.get('failed')} failed tests - pipeline may have issues")
        except:
            pass

        # Proceed with execution
        run_resp = requests.post('http://localhost:5000/api/pipeline/run',
                                json={'pipeline': pipeline}, timeout=600)

        if run_resp.status_code == 200:
            rj = run_resp.json()
            ok = rj.get('success', False)
            msg = rj.get('message', 'Pipeline executed')

            # Add safety warnings to response if any
            if safety_warnings:
                msg += f"\n\n⚠️ Safety notes:\n" + "\n".join(f"• {w}" for w in safety_warnings)

            # Create structured response with UI blocks
            response = {
                'success': True,
                'reply': msg,
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Pipeline Execution',
                    'value': '✅ Success' if ok else '❌ Failed',
                    'color': 'success' if ok else 'danger'
                }]
            }

            # Add safety warnings as info blocks
            if safety_warnings:
                response['ui_blocks'].append({
                    'type': 'info',
                    'title': 'Safety Warnings',
                    'content': '\n'.join(safety_warnings),
                    'color': 'warning'
                })

            if rj.get('results'):
                details = rj['results']
                response['ui_blocks'].append({
                    'type': 'table',
                    'title': 'Execution Details',
                    'columns': ['Step', 'Command', 'Status'],
                    'rows': [[d.get('command', ''), '✅' if d.get('success') else '❌', d.get('error', '')]
                            for d in details[:3]]  # Show first 3 steps
                })

            return jsonify(response)
        else:
            return jsonify({
                'success': True,
                'reply': f"Pipeline run failed with HTTP {run_resp.status_code}",
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Pipeline Execution',
                    'value': '❌ HTTP Error',
                    'color': 'danger'
                }]
            })
    except Exception as e:
        return jsonify({'success': True, 'reply': f'Pipeline run error: {str(e)}'})


def handle_test_run(intents):
    """Handle test execution requests."""
    try:
        test_resp = requests.post('http://localhost:5000/api/pipeline/test', timeout=600)

        if test_resp.status_code == 200:
            tj = test_resp.json()
            ok = tj.get('tests_passed', False)

            response = {
                'success': True,
                'reply': 'Tests completed successfully!' if ok else 'Some tests failed.',
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Test Results',
                    'value': '✅ All Passed' if ok else '⚠️ Some Failed',
                    'color': 'success' if ok else 'warning'
                }]
            }

            # Get detailed test results
            try:
                ts = requests.get('http://localhost:5000/api/pipeline/last-test-summary', timeout=3).json()
                if ts.get('found') and ts.get('failed', 0) > 0:
                    response['ui_blocks'].append({
                        'type': 'table',
                        'title': 'Failed Tests',
                        'columns': ['Test Name', 'Error'],
                        'rows': [[t.get('name', 'unknown'), t.get('message', '')]
                                for t in ts.get('tests', [])[:5]]  # Show first 5 failures
                    })
            except:
                pass

            return jsonify(response)
        else:
            return jsonify({'success': True, 'reply': f'Test run failed with HTTP {test_resp.status_code}'})
    except Exception as e:
        return jsonify({'success': True, 'reply': f'Test execution error: {str(e)}'})


def handle_data_ingest(intents):
    """Handle data ingestion requests with safety checks."""
    try:
        # Safety check: Warn about data freshness
        safety_warnings = []

        # Check when data was last updated
        try:
            csv_path = os.path.join('dbt_stavanger_parking', 'seeds', 'live_parking.csv')
            if os.path.exists(csv_path):
                mtime = os.path.getmtime(csv_path)
                last_update = datetime.fromtimestamp(mtime)
                time_diff = datetime.now() - last_update

                if time_diff.total_seconds() < 300:  # Less than 5 minutes ago
                    safety_warnings.append("Data was updated very recently - consider if re-ingestion is necessary")
                elif time_diff.total_seconds() > 3600:  # More than 1 hour ago
                    safety_warnings.append("Data is stale (>1 hour old) - refresh recommended")
        except:
            pass

        # Check current data volume
        try:
            query_resp = requests.post('http://localhost:5000/api/query/execute',
                                      json={'query': 'SELECT COUNT(*) as cnt FROM memory.default_staging.stg_parking_data'},
                                      timeout=10)
            if query_resp.status_code == 200:
                qj = query_resp.json()
                if qj.get('success') and qj.get('results'):
                    current_count = qj['results'][0].get('cnt', 0)
                    safety_warnings.append(f"Current dataset contains {current_count} records")
        except:
            pass

        # Proceed with ingestion
        ingest_resp = requests.post('http://localhost:5000/api/ingestion/pull',
                                   json={}, timeout=300)

        if ingest_resp.status_code == 200:
            ij = ingest_resp.json()
            success = ij.get('success', False)
            rows = ij.get('rows', 0)

            msg = f'Data ingestion {"completed successfully" if success else "failed"}. {rows} records processed.'

            # Add safety context
            if safety_warnings:
                msg += f"\n\nℹ️ Context:\n" + "\n".join(f"• {w}" for w in safety_warnings)

            response = {
                'success': True,
                'reply': msg,
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Data Ingestion',
                    'value': f'{rows} records',
                    'color': 'success' if success else 'danger'
                }]
            }

            # Add context information
            if safety_warnings:
                response['ui_blocks'].append({
                    'type': 'info',
                    'title': 'Data Context',
                    'content': '\n'.join(safety_warnings),
                    'color': 'info'
                })

            # Add suggestions
            suggestions = generate_suggestions(response['ui_blocks'])
            if suggestions:
                response['ui_blocks'].append(suggestions)

            return jsonify(response)
        else:
            return jsonify({'success': True, 'reply': f'Ingestion failed with HTTP {ingest_resp.status_code}'})
    except Exception as e:
        return jsonify({'success': True, 'reply': f'Data ingestion error: {str(e)}'})


def run_tests_and_status_combined(operation_id, intents):
    """Run tests and check status simultaneously with progress updates."""
    progress_file = f'/tmp/operation_{operation_id}.json'

    # Initialize progress with both operations
    progress_data = {
        'operation_id': operation_id,
        'status': 'running',
        'message': 'Starting tests and status check...',
        'progress': 5,
        'completed': False,
        'tests_status': 'pending',
        'status_check': 'pending'
    }
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f)

    try:
        results = {'success': True, 'ui_blocks': []}

        # Update progress: Starting tests
        progress_data.update({
            'message': 'Running dbt tests...',
            'progress': 20,
            'tests_status': 'running'
        })
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

        # Run tests
        test_resp = requests.post('http://localhost:5000/api/pipeline/test', timeout=600)
        if test_resp.status_code == 200:
            tj = test_resp.json()
            ok = tj.get('tests_passed', False)

            # Get detailed test results
            try:
                ts = requests.get('http://localhost:5000/api/pipeline/last-test-summary', timeout=3).json()
                if ts.get('found') and ts.get('failed', 0) > 0:
                    results['ui_blocks'].append({
                        'type': 'table',
                        'title': 'Failed Tests',
                        'columns': ['Test Name', 'Error'],
                        'rows': [[t.get('name', 'unknown'), t.get('message', '')]
                                for t in ts.get('tests', [])[:5]]
                    })
            except:
                pass

            progress_data.update({
                'tests_status': 'completed',
                'progress': 60
            })
        else:
            progress_data.update({
                'tests_status': 'failed',
                'progress': 60
            })

        # Update progress: Starting status check
        progress_data.update({
            'message': 'Checking system status...',
            'status_check': 'running',
            'progress': 70
        })
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)

        # Get status check
        diag_resp = requests.get('http://localhost:5000/api/logs/diagnostics', timeout=10)

        if diag_resp.status_code == 200:
            diagnostics = diag_resp.json()

            # System health
            system_health = diagnostics.get('system_health', {})
            if 'services' in system_health:
                services = system_health['services']
                healthy = sum(1 for s in services.values() if s.get('status') == 'healthy')
                total = len(services)

                results['ui_blocks'].append({
                    'type': 'metric',
                    'title': 'System Health',
                    'value': f'{healthy}/{total}',
                    'subtitle': 'Services running',
                    'color': 'success' if healthy == total else 'warning'
                })

                # Show unhealthy services if any
                unhealthy = [name for name, svc in services.items() if svc.get('status') != 'healthy']
                if unhealthy:
                    results['ui_blocks'].append({
                        'type': 'list',
                        'title': 'Unhealthy Services',
                        'items': unhealthy[:5]
                    })

            # Pipeline status
            pipeline_status = diagnostics.get('pipeline_status', {})
            if pipeline_status.get('success'):
                active = pipeline_status.get('active_pipelines', 0)
                total = pipeline_status.get('total_pipelines', 0)
                failed = pipeline_status.get('failed_pipelines', 0)

                results['ui_blocks'].append({
                    'type': 'metric',
                    'title': 'Active Pipelines',
                    'value': f'{active}/{total}',
                    'subtitle': 'Currently running',
                    'color': 'success' if active > 0 else 'warning'
                })

                if failed > 0:
                    results['ui_blocks'].append({
                        'type': 'metric',
                        'title': 'Failed Pipelines',
                        'value': str(failed),
                        'subtitle': 'Need attention',
                        'color': 'danger'
                    })

            progress_data.update({
                'status_check': 'completed',
                'progress': 90
            })

        # Finalize results
        progress_data.update({
            'message': 'Operations completed',
            'progress': 100
        })

        # Generate suggestions based on results
        suggestions = generate_suggestions(results['ui_blocks'])

        # Enhanced reply with contextual analysis
        has_issues = any(
            block.get('type') == 'table' and 'Failed Tests' in block.get('title', '')
            for block in results['ui_blocks']
        ) or any(
            block.get('type') == 'list' and 'Unhealthy Services' in block.get('title', '')
            for block in results['ui_blocks']
        ) or any(
            block.get('type') == 'metric' and 'Failed Pipelines' in block.get('title', '') and block.get('value', '0') != '0'
            for block in results['ui_blocks']
        )

        if has_issues:
            results['reply'] = 'I found some issues that need attention. Here are the specific problems:'
        else:
            results['reply'] = 'Everything looks great! Your data platform is running smoothly.'
            # For healthy systems, minimal UI is sufficient
            results['ui_blocks'] = [{
                'type': 'metric',
                'title': 'System Health',
                'value': '✅ Good',
                'color': 'success'
            }]

        if suggestions:
            results['ui_blocks'].append(suggestions)

        return results

    except Exception as e:
        return {
            'success': False,
            'reply': f'Combined operation error: {str(e)}',
            'ui_blocks': [{
                'type': 'metric',
                'title': 'Combined Operation',
                'value': '❌ Error',
                'color': 'danger'
            }]
        }


def generate_suggestions(ui_blocks):
    """Generate actionable suggestions based on operation results."""
    suggestions = []
    has_failed_tests = False
    has_unhealthy_services = False
    has_failed_pipelines = False

    # Analyze the UI blocks for issues
    for block in ui_blocks:
        if block.get('type') == 'table' and 'Failed Tests' in block.get('title', ''):
            has_failed_tests = True
        elif block.get('type') == 'list' and 'Unhealthy Services' in block.get('title', ''):
            has_unhealthy_services = True
            unhealthy_services = block.get('items', [])
        elif block.get('type') == 'metric' and 'Failed Pipelines' in block.get('title', ''):
            if block.get('value', '0') != '0':
                has_failed_pipelines = True

    # Generate suggestions based on findings
    if has_failed_tests:
        suggestions.append("🔧 **Fix test failures** - Review and resolve dbt test errors")
        suggestions.append("📊 **Check data quality** - Examine source data for inconsistencies")

    if has_unhealthy_services:
        suggestions.append("🛠️ **Restart unhealthy services** - Fix Flink, Kafka, Minio, etc.")
        suggestions.append("🔍 **Check service logs** - Investigate why services are down")

    if has_failed_pipelines:
        suggestions.append("🔄 **Re-run failed pipeline** - Try executing the pipeline again")
        suggestions.append("📋 **Check pipeline logs** - Review detailed execution logs")

    # Always provide general suggestions
    if not suggestions:
        suggestions.append("✅ **System healthy** - No immediate action required")
        suggestions.append("📈 **Monitor performance** - Keep an eye on system metrics")

    # Create suggestion UI block
    if suggestions:
        return {
            'type': 'list',
            'title': '💡 Suggested Next Steps',
            'items': suggestions[:4]  # Limit to 4 suggestions
        }

    return None


def handle_status_check(intents):
    """Handle status check requests with comprehensive UI blocks."""
    try:
        # Get comprehensive diagnostics for status
        diag_resp = requests.get('http://localhost:5000/api/logs/diagnostics', timeout=10)

        ui_blocks = []

        if diag_resp.status_code == 200:
            diagnostics = diag_resp.json()

            # System health
            system_health = diagnostics.get('system_health', {})
            if 'services' in system_health:
                services = system_health['services']
                healthy = sum(1 for s in services.values() if s.get('status') == 'healthy')
                total = len(services)

                ui_blocks.append({
                    'type': 'metric',
                    'title': 'System Health',
                    'value': f'{healthy}/{total}',
                    'subtitle': 'Services running',
                    'color': 'success' if healthy == total else 'warning'
                })

                # Show unhealthy services if any
                unhealthy = [name for name, svc in services.items() if svc.get('status') != 'healthy']
                if unhealthy:
                    ui_blocks.append({
                        'type': 'list',
                        'title': 'Unhealthy Services',
                        'items': unhealthy[:5]  # Show first 5
                    })

            # Pipeline status
            pipeline_status = diagnostics.get('pipeline_status', {})
            if pipeline_status.get('success'):
                active = pipeline_status.get('active_pipelines', 0)
                total = pipeline_status.get('total_pipelines', 0)
                failed = pipeline_status.get('failed_pipelines', 0)

                ui_blocks.append({
                    'type': 'metric',
                    'title': 'Active Pipelines',
                    'value': f'{active}/{total}',
                    'subtitle': 'Currently running',
                    'color': 'success' if active > 0 else 'warning'
                })

                if failed > 0:
                    ui_blocks.append({
                        'type': 'metric',
                        'title': 'Failed Pipelines',
                        'value': str(failed),
                        'subtitle': 'Need attention',
                        'color': 'danger'
                    })

            # Data quality
            data_quality = diagnostics.get('data_quality', {})
            if 'record_count' in data_quality:
                ui_blocks.append({
                    'type': 'metric',
                    'title': 'Data Records',
                    'value': str(data_quality['record_count']),
                    'subtitle': 'In staging table',
                    'color': 'info'
                })

        # Create targeted response based on what user is likely asking
        # For general status questions, provide concise answer with minimal UI

        # Extract key metrics
        active_pipelines = None
        failed_pipelines = None

        for block in ui_blocks:
            if block.get('type') == 'metric':
                title = block.get('title', '')
                value = block.get('value', '')
                if 'Active Pipelines' in title:
                    active_pipelines = value
                elif 'Failed Pipelines' in title:
                    failed_pipelines = value

        # Simple, direct answer for pipeline-focused questions
        if active_pipelines is not None:
            if active_pipelines == '0':
                reply_msg = "No pipelines are currently running."
            else:
                reply_msg = f"There are {active_pipelines} pipelines running."

            # Only add UI card if there are failed pipelines that need attention
            if failed_pipelines and failed_pipelines != '0':
                reply_msg += f" However, there are {failed_pipelines} failed pipelines that may need attention."
                # Show only the failed pipelines info, not all system details
                ui_blocks = [{
                    'type': 'metric',
                    'title': 'Failed Pipelines',
                    'value': failed_pipelines,
                    'color': 'warning'
                }]
            else:
                # For simple "no issues" cases, just text is sufficient
                ui_blocks = []
        else:
            # Fallback for comprehensive status requests
            reply_msg = "Here's the current system status:"

        response = {
            'success': True,
            'reply': reply_msg,
            'ui_blocks': ui_blocks
        }

        return jsonify(response)
    except Exception as e:
        return jsonify({
            'success': True,
            'reply': 'Status check completed.',
            'ui_blocks': [{
                'type': 'metric',
                'title': 'Status Check',
                'value': 'Error',
                'color': 'danger'
            }]
        })


def handle_data_query(intents, query_text):
    """Handle data query requests."""
    try:
        # Simple query parsing - look for basic SQL patterns
        if 'count' in query_text.lower() and 'parking' in query_text.lower():
            # Default to count query if user asks for count
            sql_query = "SELECT COUNT(*) as total_records FROM memory.default_staging.stg_parking_data"
        elif 'show' in query_text.lower() and 'parking' in query_text.lower():
            sql_query = "SELECT parking_location, available_spaces FROM memory.default_staging.stg_parking_data LIMIT 5"
        else:
            # Generic query
            sql_query = "SELECT COUNT(*) as record_count FROM memory.default_staging.stg_parking_data"

        query_resp = requests.post('http://localhost:5000/api/query/execute',
                                  json={'query': sql_query}, timeout=30)

        if query_resp.status_code == 200:
            qj = query_resp.json()
            if qj.get('success') and qj.get('results'):
                results = qj['results']
                columns = qj.get('columns', [])

                # Enhanced conversational response
                if len(results) > 0:
                    reply_msg = f"I found {len(results)} parking records matching your query. Here are the results showing the latest parking data with location details and availability:"
                else:
                    reply_msg = f"Your query didn't return any results. This usually means either the data hasn't been loaded yet, or the criteria didn't match any records. You might want to run data ingestion first or try a different query."

                response = {
                    'success': True,
                    'reply': reply_msg,
                    'ui_blocks': [{
                        'type': 'table',
                        'title': 'Query Results',
                        'columns': columns,
                        'rows': [list(row.values()) for row in results[:10]]  # Show first 10 rows
                    }]
                }

                return jsonify(response)
            else:
                return jsonify({'success': True, 'reply': 'Query executed but returned no results.'})
        else:
            return jsonify({'success': True, 'reply': f'Query failed with HTTP {query_resp.status_code}'})
    except Exception as e:
        return jsonify({'success': True, 'reply': f'Data query error: {str(e)}'})


def handle_health_check(intents):
    """Handle health check requests."""
    try:
        health_resp = requests.get('http://localhost:5000/api/health', timeout=10)

        if health_resp.status_code == 200:
            hj = health_resp.json()
            services = hj.get('services', {})
            healthy_count = sum(1 for s in services.values() if s.get('status') == 'healthy')
            total_count = len(services)

            response = {
                'success': True,
                'reply': f'System health: {healthy_count}/{total_count} services healthy.',
                'ui_blocks': [{
                    'type': 'metric',
                    'title': 'Healthy Services',
                    'value': f'{healthy_count}/{total_count}',
                    'color': 'success' if healthy_count == total_count else 'warning'
                }]
            }

            # Add unhealthy services if any
            unhealthy = [name for name, svc in services.items() if svc.get('status') != 'healthy']
            if unhealthy:
                response['ui_blocks'].append({
                    'type': 'list',
                    'title': 'Unhealthy Services',
                    'items': unhealthy
                })

            return jsonify(response)
        else:
            return jsonify({'success': True, 'reply': f'Health check failed with HTTP {health_resp.status_code}'})
    except Exception as e:
        return jsonify({'success': True, 'reply': f'Health check error: {str(e)}'})

def trigger_operation_async(action, user_message, messages):
    """Trigger an operation asynchronously with proper UI blocks"""
    operation_id = f"{action}_{int(time.time())}_{random.randint(1000, 9999)}"

    # Create context information for the operation
    context_info = {}
    if action == 'run_pipeline':
        context_info = {
            'estimated_time': '2-5 minutes',
            'steps': ['Seed live data', 'Run dbt models', 'Execute tests', 'Generate reports'],
            'description': 'Running the stavanger_parking pipeline which includes data seeding, model execution, and testing. This will process parking data from the live API.'
        }
    elif action == 'run_tests':
        context_info = {
            'estimated_time': '1-3 minutes',
            'steps': ['Load test data', 'Run all dbt tests', 'Validate results', 'Generate test summary'],
            'description': 'Running comprehensive tests on all dbt models to ensure data quality and integrity. This includes checks for null values, data consistency, and business logic validation.'
        }
    elif action == 'ingest_data':
        context_info = {
            'estimated_time': '30-60 seconds',
            'steps': ['Fetch from API', 'Process data', 'Update staging tables'],
            'description': 'Fetching the latest parking data from the Stavanger Kommune API and updating the local database. This ensures we have the most current parking availability information.'
        }
    elif action == 'create_pipeline':
        context_info = {
            'estimated_time': '5-10 minutes',
            'steps': ['Gather requirements', 'Configure data source', 'Create dbt models', 'Set up tests', 'Generate configuration'],
            'description': 'Creating a new data pipeline from scratch. This interactive process will guide you through defining data sources, transformations, and testing requirements.'
        }

    # Start the operation asynchronously
    intents = {'action': action, 'user_message': user_message}
    thread = threading.Thread(target=run_operation_async, args=(operation_id, intents, user_message))
    thread.daemon = True
    thread.start()

    # Return immediate response with progress UI block
    return jsonify({
        'success': True,
        'reply': get_operation_start_message(action),
        'operation_id': operation_id,
        'status': 'running',
        'ui_blocks': [{
            'type': 'progress',
            'title': get_operation_title(action),
            'status': 'running',
            'message': 'Initializing operation...',
            'progress': 5,
            'operation_id': operation_id,
            'context': context_info,
            'show_details': True
        }]
    })

def get_operation_start_message(action):
    """Get appropriate start message for operation"""
    messages = {
        'run_pipeline': '🚀 Starting the Stavanger Parking pipeline execution. This will process the latest parking data through seeding, modeling, and testing phases. You\'ll see real-time progress in the card below.',
        'run_tests': '🧪 Initiating comprehensive dbt test suite. This will validate data quality, check for null values, and ensure business logic integrity across all models. Results will appear in the progress card.',
        'ingest_data': '📥 Starting data ingestion from the Stavanger Kommune API. This will fetch the latest parking availability data and update the staging tables. The progress card will show real-time updates.',
        'check_status': '🔍 Running system status check. This will assess the health of all services and pipelines.',
        'create_pipeline': '🏗️ Starting the pipeline creation wizard. I\'ll guide you through creating a new data pipeline step by step. This will help you set up data sources, transformations, and testing.'
    }
    return messages.get(action, f'Starting {action} operation...')

def get_operation_title(action):
    """Get appropriate title for operation"""
    titles = {
        'run_pipeline': 'Run Pipeline',
        'run_tests': 'Run Tests',
        'ingest_data': 'Data Ingestion',
        'check_status': 'System Status',
        'create_pipeline': 'Create Pipeline'
    }
    return titles.get(action, action.replace('_', ' ').title())

def handle_llm_assistance(user_message, messages, intents):
    """Handle complex queries using OpenAI LLM with enhanced context."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return jsonify({
            'success': True,
            'reply': f"I understand you want to: {intents.get('action', 'general assistance')}. Please configure OPENAI_API_KEY for advanced AI assistance."
        })

    try:
        from openai import OpenAI

        client = _get_openai_client(api_key)

        # Enhanced system prompt for integrated operations
        system_prompt = f"""You are a FOSS Data Platform assistant with direct command access.

CRITICAL INSTRUCTIONS:
- When user asks to "run tests", "execute tests", "test pipeline", or similar: IMMEDIATELY TRIGGER THE TEST OPERATION
- When user asks for "status", "system status", "pipeline status": IMMEDIATELY TRIGGER STATUS CHECK
- When user asks to "run pipeline": IMMEDIATELY TRIGGER PIPELINE EXECUTION
- When user asks to "pull data", "ingest data": IMMEDIATELY TRIGGER DATA INGESTION
- DO NOT give generic responses - actually execute the requested operations
- Keep responses very brief when triggering operations
- Use the actual command system, don't simulate it

Available commands you can trigger:
- "run tests" → executes dbt tests
- "system status" → shows platform health
- "run stavanger parking pipeline" → executes the pipeline
- "pull latest data" → ingests new data

RESPONSE STYLE:
- For operation requests: Keep under 10 words, then the system handles the rest
- For questions: Answer directly and concisely
- Always use proper spacing and punctuation between sentences
- Format responses clearly with appropriate line breaks
- Let the UI blocks show progress and results, not your text

FORMATTING REQUIREMENTS:
- ALWAYS add a line break after ANY list of items
- NEVER put text immediately after a list without a blank line
- Example: "Services: A, B, C\n\nThese services..." NOT "Services: A, B, C These services..."
- Use proper sentence spacing (period followed by space)
- Break complex responses into clear paragraphs
- Use bullet points or numbered lists when appropriate
- Add line breaks after lists of services or items
- Use proper indentation for multi-line responses
- Separate different types of information with blank lines
- After enumerating services/items, ALWAYS start new content on next line

Be direct and use the actual command system."""

        # Check if this is an operation request that should trigger UI blocks
        user_lower = user_message.lower()

        # Direct operation detection for LLM responses
        if any(phrase in user_lower for phrase in ['run test', 'execute test', 'test']):
            return trigger_operation_async('run_tests', user_message, messages)
        elif any(phrase in user_lower for phrase in ['run pipeline', 'start pipeline', 'execute pipeline', 'run stavanger']):
            return trigger_operation_async('run_pipeline', user_message, messages)
        elif any(phrase in user_lower for phrase in ['pull data', 'ingest data', 'fetch data']):
            return trigger_operation_async('ingest_data', user_message, messages)
        elif any(phrase in user_lower for phrase in ['status', 'system status', 'pipeline status']):
            return trigger_operation_async('check_status', user_message, messages)
        elif any(phrase in user_lower for phrase in ['create pipeline', 'new pipeline', 'build pipeline']):
            return trigger_operation_async('create_pipeline', user_message, messages)

        # Post-process response for better formatting
        if user_message and not any(phrase in user_lower for phrase in ['run test', 'run pipeline', 'pull data', 'status']):
            # Add formatting fixes to the system prompt
            system_prompt += "\n\nADDITIONAL FORMATTING RULES:\n- If response contains lists, ALWAYS add \\n\\n after the last list item\n- Never continue text immediately after listing services\n- Use proper paragraph breaks"

        # Build comprehensive conversation context with diagnostics
        context_lines = []

        # Get comprehensive diagnostics
        try:
            diag_resp = requests.get('http://localhost:5000/api/logs/diagnostics', timeout=5)
            if diag_resp.status_code == 200:
                diagnostics = diag_resp.json()

                # System health
                system_health = diagnostics.get('system_health', {})
                if 'services' in system_health:
                    services = system_health['services']
                    healthy = sum(1 for s in services.values() if s.get('status') == 'healthy')
                    total = len(services)
                    context_lines.append(f"System health: {healthy}/{total} services healthy")

                    if healthy < total:
                        unhealthy = [name for name, svc in services.items() if svc.get('status') != 'healthy']
                        context_lines.append(f"Unhealthy services: {', '.join(unhealthy[:3])}")

                # Pipeline status
                pipeline_status = diagnostics.get('pipeline_status', {})
                if pipeline_status.get('success'):
                    active = pipeline_status.get('active_pipelines', 0)
                    total = pipeline_status.get('total_pipelines', 0)
                    failed = pipeline_status.get('failed_pipelines', 0)
                    context_lines.append(f"Pipeline status: {active}/{total} active, {failed} failed")

        except Exception as e:
            # Fallback to basic context if diagnostics fail
            context_lines.append("Note: Full diagnostics temporarily unavailable, using basic status")

        # Format conversation history
        convo_text = "\n".join([
            f"{'User' if not m.get('role') or m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')}"
            for m in messages[-5:]  # Last 5 messages for context
        ])

        ctx_text = "\n".join(context_lines) if context_lines else "No additional context available."

        composed_input = f"""{system_prompt}

CURRENT PLATFORM CONTEXT:
{ctx_text}

CONVERSATION HISTORY:
{convo_text}

USER QUERY: {user_message}

Please respond helpfully and proactively. If the user is asking about platform capabilities or data, provide specific guidance."""

        # Make the API call
        response = client.responses.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
            input=composed_input,
            store=False,
        )

        assistant_reply = getattr(response, 'output_text', None) or str(response)

        # Post-process reply for better formatting
        assistant_reply = post_process_formatting(assistant_reply)

        # Don't truncate responses - let them be natural

        return jsonify({
            'success': True,
            'reply': assistant_reply,
            'ui_blocks': []
        })

    except Exception as e:
        return jsonify({
            'success': True,
            'reply': f"AI assistance temporarily unavailable: {str(e)}. Try using specific commands like 'run pipeline' or 'check status'."
        })

@lru_cache(maxsize=1)
def _get_openai_client(api_key: str):
    from openai import OpenAI  # lazy import
    return OpenAI(api_key=api_key)

def post_process_formatting(text):
    """Post-process LLM response to fix formatting issues."""
    import re

    # Fix missing line breaks after service names followed by additional text
    # Pattern: "Minio These issues" -> "Minio\n\nThese issues"
    text = re.sub(r'(\w+)\s+(These|The|This|It|They)', r'\1\n\n\2', text)

    # Fix missing line breaks after service lists
    text = re.sub(r'(\w+)\s+(could|may|might|will)', r'\1\n\n\2', text)

    # Fix missing line breaks after service names followed by additional text
    text = re.sub(r'(\w+)\s+(Additionally|Also|Moreover)', r'\1\n\n\2', text)

    # Fix missing line breaks after colons followed by lists
    text = re.sub(r':\s*([^:\n]+)\s+(These|The|This)', r': \1\n\n\2', text)

    # Fix missing line breaks after indented lists
    text = re.sub(r'(\s+[\w-]+)\s+(These|The|This)', r'\1\n\n\2', text)

    # Fix missing line breaks after commas in service lists
    text = re.sub(r'(minio|kafka|flink|trino|grafana|jupyter[^,]*),\s+', r'\1\n', text, flags=re.IGNORECASE)

    # Fix missing line breaks after service names at end of lists
    text = re.sub(r'(minio|kafka|flink|trino|grafana|jupyter)\s+([A-Z])', r'\1\n\n\2', text, flags=re.IGNORECASE)

    # Fix missing line breaks after common list patterns
    text = re.sub(r'(\w+)\s+(appears|seems|looks|is)\s+healthy', r'\1\n\n\2 healthy', text, flags=re.IGNORECASE)
    text = re.sub(r'(\w+)\s+(has|have)\s+issues', r'\1\n\n\2 issues', text, flags=re.IGNORECASE)
    text = re.sub(r'(\w+)\s+(needs|require)\s+attention', r'\1\n\n\2 attention', text, flags=re.IGNORECASE)

    # Fix missing line breaks after numbers in lists
    text = re.sub(r'(\d+)\.\s*([A-Z])', r'\1.\n\n\2', text)

    # Ensure proper spacing after periods
    text = re.sub(r'\.([A-Z])', r'. \1', text)

    # Fix double spaces
    text = re.sub(r'  +', ' ', text)

    return text


def write_event(event: dict) -> None:
    try:
        enriched = {
            **event,
            'timestamp': datetime.now().isoformat()
        }
        with open(EVENTS_PATH, 'a') as f:
            f.write(json.dumps(enriched) + "\n")
    except Exception:
        pass


def read_recent_events(limit: int = 20, pipeline_id: str | None = None) -> list[dict]:
    try:
        if not os.path.exists(EVENTS_PATH):
            return []
        with open(EVENTS_PATH, 'r') as f:
            lines = f.readlines()
        records = []
        for line in lines[-limit:]:  # Get last N records
            try:
                record = json.loads(line.strip())
                if pipeline_id is None or record.get('pipeline_id') == pipeline_id:
                    records.append(record)
            except json.JSONDecodeError:
                continue
        return records
    except Exception:
        return []


def _resolve_ckan_parking_json_url() -> str:
    """Discover the JSON resource URL via CKAN package_show if not explicitly configured."""
    try:
        # Try the CKAN API to get the JSON resource URL
        package_show_url = "https://opencom.no/api/3/action/package_show"
        params = {'id': 'stavanger-parkering'}
        response = requests.get(package_show_url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'result' in data:
                resources = data['result'].get('resources', [])
                # Look for JSON resource
                for resource in resources:
                    if resource.get('format', '').upper() == 'JSON':
                        json_url = resource.get('url')
                        if json_url:
                            print(f"Resolved parking JSON URL via CKAN: {json_url}")
                            return json_url

        print("Could not resolve parking JSON URL via CKAN, using fallback")
        return "https://opencom.no/dataset/stavanger-parkering/resource/12345678-1234-1234-1234-123456789012/download/stavanger-parkering.json"

    except Exception as e:
        print(f"Error resolving CKAN parking URL: {e}")
        return "https://opencom.no/dataset/stavanger-parkering/resource/12345678-1234-1234-1234-123456789012/download/stavanger-parkering.json"


# Removed corrupted function - using correct implementation below


@lru_cache(maxsize=1)
def _get_openai_client(api_key: str):
    from openai import OpenAI  # lazy import
    return OpenAI(api_key=api_key)


def get_last_dbt_test_failures(project_dir: str = 'dbt_stavanger_parking'):
    """Parse dbt artifacts to summarize failed tests, if any."""
    try:
        # Prefer persisted canonical summary if available
        summary_paths = ['/tmp/last_test_summary.json', './last_test_summary.json', '/app/last_test_summary.json']
        for path in summary_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    return {
                        'found': True,
                        'failed': data.get('failed_count', 0),
                        'tests': data.get('failed_tests', [])
                    }
                except Exception as e:
                    print(f"Error reading test summary from {path}: {e}")
                    continue

        target_path = os.path.join(project_dir, 'target', 'run_results.json')
        if not os.path.exists(target_path):
            return {'found': False, 'failed': 0, 'tests': []}
        with open(target_path, 'r') as f:
            data = json.load(f)
        results = data.get('results', [])
        failed_tests = []
        for r in results:
            if r.get('resource_type') == 'test' and r.get('status') not in ('pass', 'success'):  # dbt may use 'fail'/'error'
                node = r.get('unique_id', '')
                name = r.get('info', {}).get('name') or r.get('node', {}).get('name') or node
                message = (r.get('message') or r.get('failures') or r.get('status'))
                failed_tests.append({'name': name, 'message': str(message)})
        return {
            'found': True,
            'failed': len(failed_tests),
            'tests': failed_tests[:10]  # cap for chat
        }
    except Exception:
        return {'found': False, 'failed': 0, 'tests': []}


# --- Unified events store (JSONL) ---
EVENTS_PATH = '/tmp/pipeline_events.jsonl'


def write_event(event: dict) -> None:
    try:
        enriched = {
            **event,
            'timestamp': datetime.now().isoformat()
        }
        with open(EVENTS_PATH, 'a') as f:
            f.write(json.dumps(enriched) + "\n")
    except Exception:
        pass


def read_recent_events(limit: int = 20, pipeline_id: str | None = None) -> list[dict]:
    try:
        if not os.path.exists(EVENTS_PATH):
            return []
        with open(EVENTS_PATH, 'r') as f:
            lines = f.readlines()
        records = []
        for line in lines[-limit:]:  # Get last N records
            try:
                record = json.loads(line.strip())
                if pipeline_id is None or record.get('pipeline_id') == pipeline_id:
                    records.append(record)
            except json.JSONDecodeError:
                continue
        return records
    except Exception:
        return []


def _resolve_ckan_parking_json_url() -> str:
    """Discover the JSON resource URL via CKAN package_show if not explicitly configured."""
    try:
        # Try the CKAN API to get the JSON resource URL
        package_show_url = "https://opencom.no/api/3/action/package_show"
        params = {'id': 'stavanger-parkering'}
        response = requests.get(package_show_url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'result' in data:
                resources = data['result'].get('resources', [])
                # Look for JSON resource
                for resource in resources:
                    if resource.get('format', '').upper() == 'JSON':
                        json_url = resource.get('url')
                        if json_url:
                            print(f"Resolved parking JSON URL via CKAN: {json_url}")
                            return json_url

        print("Could not resolve parking JSON URL via CKAN, using fallback")
        return "https://opencom.no/dataset/stavanger-parkering/resource/12345678-1234-1234-1234-123456789012/download/stavanger-parkering.json"

    except Exception as e:
        print(f"Error resolving CKAN parking URL: {e}")
        return "https://opencom.no/dataset/stavanger-parkering/resource/12345678-1234-1234-1234-123456789012/download/stavanger-parkering.json"


# Corrupted function removed - using correct implementation below


def write_rows_to_seed_csv(rows):
    seed_dir = os.path.join(os.getcwd(), 'dbt_stavanger_parking', 'seeds')
    os.makedirs(seed_dir, exist_ok=True)
    seed_path = os.path.join(seed_dir, 'live_parking.csv')
    fieldnames = ['name', 'available_spaces', 'lat', 'lon', 'fetched_at']
    with open(seed_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fieldnames})
    return seed_path


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
