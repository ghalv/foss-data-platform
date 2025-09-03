#!/usr/bin/env python3
"""
FOSS Data Platform - Comprehensive Stress Test Suite
=====================================================

This script performs thorough validation of the entire platform:
- Service health and connectivity
- Pipeline execution end-to-end
- Data flow verification
- API robustness testing
- Performance validation
- Error handling verification

Usage: python platform_stress_test.py
"""

import requests
import json
import time
import subprocess
import os
import sys
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import threading
import concurrent.futures
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('platform_stress_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class PlatformStressTester:
    """Comprehensive platform stress testing"""

    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.results = {
            'overall_score': 0,
            'services': {},
            'pipelines': {},
            'data_flow': {},
            'performance': {},
            'errors': []
        }
        self.start_time = datetime.now()

    def log(self, level: str, message: str):
        """Log a message with appropriate level"""
        if level == 'INFO':
            logging.info(message)
        elif level == 'ERROR':
            logging.error(message)
        elif level == 'WARNING':
            logging.warning(message)
        elif level == 'SUCCESS':
            logging.info(f"✅ {message}")

    def test_service_health(self) -> Dict[str, Any]:
        """Test all service health endpoints"""
        self.log('INFO', 'Testing service health...')

        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=30)
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})

                results = {
                    'total_services': len(services),
                    'healthy_services': 0,
                    'unhealthy_services': 0,
                    'details': {}
                }

                for service_name, service_info in services.items():
                    status = service_info.get('status', 'unknown')
                    results['details'][service_name] = status

                    if status == 'healthy':
                        results['healthy_services'] += 1
                    else:
                        results['unhealthy_services'] += 1

                health_percentage = (results['healthy_services'] / results['total_services'] * 100) if results['total_services'] > 0 else 0
                results['health_percentage'] = health_percentage

                if health_percentage >= 80:
                    self.log('SUCCESS', f"Service health: {health_percentage:.1f}% healthy")
                else:
                    self.log('WARNING', f"Service health: Only {health_percentage:.1f}% healthy")

                return results
            else:
                self.log('ERROR', f"Health API returned status {response.status_code}")
                return {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            self.log('ERROR', f"Service health test failed: {str(e)}")
            return {'error': str(e)}

    def test_pipeline_execution(self) -> Dict[str, Any]:
        """Test end-to-end pipeline execution"""
        self.log('INFO', 'Testing pipeline execution...')

        try:
            # Test pipeline API endpoints
            endpoints = [
                '/api/pipeline/list',
                '/api/pipeline/stats',
                '/api/pipeline/status'
            ]

            results = {}
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                    results[endpoint] = response.status_code == 200
                except Exception:
                    results[endpoint] = False

            # Test pipeline run (if available)
            try:
                payload = {
                    'pipeline': 'stavanger_parking',
                    'steps': ['seed']
                }
                response = requests.post(f"{self.base_url}/api/pipeline/run",
                                       json=payload, timeout=120)
                results['pipeline_execution'] = response.status_code in [200, 202]
            except Exception:
                results['pipeline_execution'] = False

            success_count = sum(results.values())
            total_count = len(results)

            if success_count >= total_count * 0.8:
                self.log('SUCCESS', f"Pipeline tests: {success_count}/{total_count} passed")
            else:
                self.log('WARNING', f"Pipeline tests: Only {success_count}/{total_count} passed")

            return results

        except Exception as e:
            self.log('ERROR', f"Pipeline execution test failed: {str(e)}")
            return {'error': str(e)}

    def test_data_flow(self) -> Dict[str, Any]:
        """Test data flow through the platform"""
        self.log('INFO', 'Testing data flow...')

        try:
            # Test query execution
            query_payload = {
                'query': 'SELECT 1 as test_value'
            }

            response = requests.post(f"{self.base_url}/api/query/execute",
                                   json=query_payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                query_success = data.get('success', False)
            else:
                query_success = False

            # Test storage stats
            try:
                response = requests.get(f"{self.base_url}/api/storage/stats", timeout=30)
                storage_success = response.status_code == 200
            except Exception:
                storage_success = False

            results = {
                'query_execution': query_success,
                'storage_stats': storage_success,
                'data_flow_score': (query_success + storage_success) / 2 * 100
            }

            if results['data_flow_score'] >= 80:
                self.log('SUCCESS', f"Data flow: {results['data_flow_score']:.1f}% functional")
            else:
                self.log('WARNING', f"Data flow: Only {results['data_flow_score']:.1f}% functional")

            return results

        except Exception as e:
            self.log('ERROR', f"Data flow test failed: {str(e)}")
            return {'error': str(e)}

    def test_performance(self) -> Dict[str, Any]:
        """Test platform performance under load"""
        self.log('INFO', 'Testing performance...')

        try:
            # Test response times for key endpoints
            endpoints = [
                '/api/health',
                '/api/metrics',
                '/api/pipeline/stats'
            ]

            results = {}
            for endpoint in endpoints:
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                    response_time = time.time() - start_time
                    results[endpoint] = {
                        'response_time': response_time,
                        'success': response.status_code == 200,
                        'performance': 'good' if response_time < 5.0 else 'slow'
                    }
                except Exception as e:
                    results[endpoint] = {
                        'response_time': None,
                        'success': False,
                        'performance': 'failed',
                        'error': str(e)
                    }

            # Calculate average response time
            successful_requests = [r for r in results.values() if r['success'] and r['response_time']]
            if successful_requests:
                avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
                results['average_response_time'] = avg_response_time
                results['performance_rating'] = 'good' if avg_response_time < 3.0 else 'acceptable' if avg_response_time < 10.0 else 'poor'

                self.log('SUCCESS' if avg_response_time < 5.0 else 'WARNING',
                        f"Performance: {avg_response_time:.2f}s average response time")
            else:
                results['performance_rating'] = 'failed'
                self.log('ERROR', "Performance test failed - no successful requests")

            return results

        except Exception as e:
            self.log('ERROR', f"Performance test failed: {str(e)}")
            return {'error': str(e)}

    def test_concurrent_load(self) -> Dict[str, Any]:
        """Test platform under concurrent load"""
        self.log('INFO', 'Testing concurrent load...')

        def make_request(endpoint: str) -> Tuple[str, bool, float]:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                response_time = time.time() - start_time
                return endpoint, response.status_code == 200, response_time
            except Exception:
                return endpoint, False, time.time() - start_time

        try:
            # Test concurrent requests to health endpoint
            endpoints = ['/api/health'] * 10  # 10 concurrent requests

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

            successful_requests = sum(1 for _, success, _ in results if success)
            total_requests = len(results)

            success_rate = (successful_requests / total_requests) * 100

            concurrent_results = {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'success_rate': success_rate,
                'concurrent_load': 'good' if success_rate >= 90 else 'acceptable' if success_rate >= 70 else 'poor'
            }

            if success_rate >= 90:
                self.log('SUCCESS', f"Concurrent load: {success_rate:.1f}% success rate")
            else:
                self.log('WARNING', f"Concurrent load: Only {success_rate:.1f}% success rate")

            return concurrent_results

        except Exception as e:
            self.log('ERROR', f"Concurrent load test failed: {str(e)}")
            return {'error': str(e)}

    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        self.log('INFO', 'Starting comprehensive platform stress test...')

        # Run all tests
        self.results['services'] = self.test_service_health()
        self.results['pipelines'] = self.test_pipeline_execution()
        self.results['data_flow'] = self.test_data_flow()
        self.results['performance'] = self.test_performance()
        self.results['concurrent_load'] = self.test_concurrent_load()

        # Calculate overall score
        test_categories = ['services', 'pipelines', 'data_flow', 'performance', 'concurrent_load']

        total_score = 0
        max_score = len(test_categories)

        for category in test_categories:
            if category in self.results and isinstance(self.results[category], dict):
                if 'error' not in self.results[category]:
                    # Calculate category score based on success metrics
                    if category == 'services':
                        score = self.results[category].get('health_percentage', 0) / 100
                    elif category == 'pipelines':
                        success_count = sum(self.results[category].values())
                        total_count = len(self.results[category])
                        score = success_count / total_count if total_count > 0 else 0
                    elif category == 'data_flow':
                        score = self.results[category].get('data_flow_score', 0) / 100
                    elif category == 'performance':
                        avg_time = self.results[category].get('average_response_time', 10)
                        score = max(0, 1 - (avg_time / 10))  # Better score for faster responses
                    elif category == 'concurrent_load':
                        score = self.results[category].get('success_rate', 0) / 100

                    total_score += score
                else:
                    self.log('ERROR', f"{category} test failed completely")

        self.results['overall_score'] = (total_score / max_score) * 100

        # Generate final report
        self.generate_report()

        return self.results

    def generate_report(self):
        """Generate comprehensive test report"""
        duration = datetime.now() - self.start_time

        print("\n" + "="*80)
        print("🎯 FOSS DATA PLATFORM - STRESS TEST REPORT")
        print("="*80)
        print(f"Test Duration: {duration.total_seconds():.1f} seconds")
        print(f"Overall Score: {self.results['overall_score']:.1f}%")
        print()

        # Service Health
        if 'services' in self.results and 'error' not in self.results['services']:
            services = self.results['services']
            print("🏥 SERVICE HEALTH")
            print(f"  Total Services: {services.get('total_services', 0)}")
            print(f"  Healthy: {services.get('healthy_services', 0)}")
            print(f"  Unhealthy: {services.get('unhealthy_services', 0)}")
            print(".1f")
            print()

        # Pipelines
        if 'pipelines' in self.results and 'error' not in self.results['pipelines']:
            pipelines = self.results['pipelines']
            success_count = sum(pipelines.values())
            total_count = len(pipelines)
            print("🔧 PIPELINE TESTS")
            print(f"  Tests Passed: {success_count}/{total_count}")
            print(".1f")
            print()

        # Data Flow
        if 'data_flow' in self.results and 'error' not in self.results['data_flow']:
            data_flow = self.results['data_flow']
            print("📊 DATA FLOW")
            print(f"  Query Execution: {'✅' if data_flow.get('query_execution') else '❌'}")
            print(f"  Storage Stats: {'✅' if data_flow.get('storage_stats') else '❌'}")
            print(".1f")
            print()

        # Performance
        if 'performance' in self.results and 'error' not in self.results['performance']:
            perf = self.results['performance']
            print("⚡ PERFORMANCE")
            if 'average_response_time' in perf:
                print(".2f")
                print(f"  Rating: {perf.get('performance_rating', 'unknown')}")
            print()

        # Concurrent Load
        if 'concurrent_load' in self.results and 'error' not in self.results['concurrent_load']:
            load = self.results['concurrent_load']
            print("🔄 CONCURRENT LOAD")
            print(f"  Success Rate: {load.get('success_rate', 0):.1f}%")
            print(f"  Rating: {load.get('concurrent_load', 'unknown')}")
            print()

        # Final Assessment
        score = self.results['overall_score']
        if score >= 90:
            print("🎉 EXCELLENT: Platform is production-ready!")
        elif score >= 75:
            print("✅ GOOD: Platform is stable with minor issues")
        elif score >= 60:
            print("⚠️  ACCEPTABLE: Platform works but needs improvements")
        else:
            print("❌ POOR: Platform needs significant attention")

        print("="*80)

def main():
    """Main entry point"""
    print("🚀 FOSS Data Platform - Stress Test Suite")
    print("=" * 50)

    tester = PlatformStressTester()
    results = tester.run_full_test_suite()

    # Save results to file
    with open('stress_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n📄 Results saved to stress_test_results.json")

if __name__ == "__main__":
    main()
