#!/usr/bin/env python3
"""
FOSS Data Platform - Automated QA Test Suite
Tests all platform functionality for consistency and correctness
"""

import requests
import json
import time
import subprocess
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

class PlatformQATester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log a test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': timestamp
        }
        self.test_results.append(result)
        print(f"[{timestamp}] {status} {test_name}")
        if details and not success:
            print(f"    Details: {details}")
    
    def test_dashboard_loading(self) -> bool:
        """Test if dashboard loads correctly"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                # Check for key elements
                content = response.text
                if "FOSS Data Platform" in content and "Dashboard" in content:
                    return True
                else:
                    return False
            return False
        except Exception as e:
            return False
    
    def test_api_endpoints(self) -> Dict[str, bool]:
        """Test all API endpoints"""
        endpoints = [
            "/api/health",
            "/api/metrics", 
            "/api/pipeline/list",
            "/api/pipeline/stats",
            "/api/quality/metrics",
            "/api/platform/parking-metrics",
            "/api/storage/stats"
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                results[endpoint] = response.status_code == 200
            except Exception:
                results[endpoint] = False
        
        return results
    
    def test_pipeline_functionality(self) -> Dict[str, bool]:
        """Test pipeline management functionality"""
        results = {}
        
        # Test pipeline list
        try:
            response = requests.get(f"{self.base_url}/api/pipeline/list", timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['pipeline_list'] = data.get('success', False)
                results['pipeline_count'] = len(data.get('pipelines', [])) > 0
            else:
                results['pipeline_list'] = False
                results['pipeline_count'] = False
        except Exception:
            results['pipeline_list'] = False
            results['pipeline_count'] = False
        
        # Test pipeline stats
        try:
            response = requests.get(f"{self.base_url}/api/pipeline/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['pipeline_stats'] = data.get('success', False)
            else:
                results['pipeline_stats'] = False
        except Exception:
            results['pipeline_stats'] = False
        
        return results
    
    def test_service_health(self) -> Dict[str, Any]:
        """Test service health monitoring"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                total_services = len(services)
                healthy_services = sum(1 for s in services.values() if s.get('status') == 'healthy')
                
                return {
                    'total': total_services,
                    'healthy': healthy_services,
                    'unhealthy': total_services - healthy_services,
                    'health_percentage': (healthy_services / total_services * 100) if total_services > 0 else 0
                }
            else:
                return {'error': 'Health API failed'}
        except Exception as e:
            return {'error': str(e)}
    
    def test_page_consistency(self):
        """Test basic page consistency and layout"""
        print("Testing page consistency...")
        
        pages = [
            '/', '/pipeline-management', '/pipeline-control', '/data-browser',
            '/storage-management', '/bi-dashboard', '/health', '/metrics',
            '/streaming'
        ]
        
        results = {}
        for page in pages:
            try:
                response = requests.get(f"{self.base_url}{page}", timeout=10)
                if response.status_code == 200:
                    # Check for layout issues
                    html = response.text
                    
                    # Check for container-fluid (too wide) vs container
                    has_container_fluid = 'container-fluid' in html
                    has_container = 'container' in html
                    
                    # Check for proper Bootstrap structure
                    has_bootstrap = 'bootstrap' in html.lower()
                    has_responsive_meta = 'viewport' in html
                    
                    # Check for proper navigation structure
                    has_navbar = 'navbar' in html
                    has_nav_links = 'nav-link' in html
                    
                    # Check for proper card structure
                    has_cards = 'card' in html
                    has_card_headers = 'card-header' in html
                    
                    # Score the page layout
                    score = 0
                    if has_container and not has_container_fluid:
                        score += 1  # Good: using container not container-fluid
                    if has_bootstrap:
                        score += 1
                    if has_responsive_meta:
                        score += 1
                    if has_navbar and has_nav_links:
                        score += 1
                    if has_cards and has_card_headers:
                        score += 1
                    
                    results[page] = {
                        'status': 'loaded',
                        'score': score,
                        'issues': []
                    }
                    
                    # Flag specific issues
                    if has_container_fluid:
                        results[page]['issues'].append('Uses container-fluid (too wide)')
                    if not has_container:
                        results[page]['issues'].append('Missing container class')
                    if not has_responsive_meta:
                        results[page]['issues'].append('Missing responsive viewport meta')
                        
                else:
                    results[page] = {'status': 'failed', 'score': 0, 'issues': [f'HTTP {response.status_code}']}
                    
            except Exception as e:
                results[page] = {'status': 'error', 'score': 0, 'issues': [str(e)]}
        
        return results

    def test_pipeline_execution(self):
        """Test actual pipeline execution, not just API endpoints"""
        print("Testing pipeline execution...")
        
        results = {}
        
        # Test pipeline list
        try:
            response = requests.get(f"{self.base_url}/api/pipeline/list", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'stavanger_parking' in str(data):
                    results['pipeline_list'] = True
                else:
                    results['pipeline_list'] = False
                    results['pipeline_list_issue'] = 'Stavanger parking pipeline not found'
            else:
                results['pipeline_list'] = False
                results['pipeline_list_issue'] = f'HTTP {response.status_code}'
        except Exception as e:
            results['pipeline_list'] = False
            results['pipeline_list_issue'] = str(e)
        
        # Test actual pipeline execution
        try:
            response = requests.post(
                f"{self.base_url}/api/pipeline/run",
                json={'pipeline': 'stavanger_parking'},
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results['pipeline_execution'] = True
                    results['execution_details'] = {
                        'status': data.get('pipeline_status'),
                        'tests_passed': data.get('tests_passed'),
                        'message': data.get('message')
                    }
                else:
                    results['pipeline_execution'] = False
                    results['execution_issue'] = data.get('message', 'Unknown error')
                    
                    # Check for specific failure reasons
                    if 'dbt' in str(data).lower() and 'not found' in str(data).lower():
                        results['execution_issue'] = 'DBT not installed or not in PATH'
                    elif 'catalog' in str(data).lower() and 'not found' in str(data).lower():
                        results['execution_issue'] = 'Trino catalog configuration issue'
                        
            else:
                results['pipeline_execution'] = False
                results['execution_issue'] = f'HTTP {response.status_code}'
                
        except Exception as e:
            results['pipeline_execution'] = False
            results['execution_issue'] = str(e)
        
        return results
    
    def test_data_quality(self) -> Dict[str, Any]:
        """Test data quality metrics"""
        try:
            response = requests.get(f"{self.base_url}/api/quality/metrics", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'overall_score': data.get('overall_score', 0),
                    'checks_performed': data.get('checks_performed', 0),
                    'has_parking_data': 'parking_data' in data,
                    'has_platform_data': 'platform_data' in data
                }
            else:
                return {'error': 'Quality API failed'}
        except Exception as e:
            return {'error': str(e)}
    
    def test_storage_functionality(self) -> Dict[str, bool]:
        """Test storage management functionality"""
        try:
            response = requests.get(f"{self.base_url}/api/storage/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'has_stats': 'total_objects' in data,
                    'has_buckets': 'buckets' in data,
                    'has_upload_count': 'upload_count' in data
                }
            else:
                return {'error': 'Storage API failed'}
        except Exception as e:
            return {'error': str(e)}
    
    def run_comprehensive_tests(self):
        """Run all QA tests"""
        print("🚀 Starting FOSS Data Platform QA Test Suite")
        print("=" * 60)
        
        # Test 1: Dashboard Loading
        self.log_test("Dashboard Loading", self.test_dashboard_loading())
        
        # Test 2: API Endpoints
        api_results = self.test_api_endpoints()
        for endpoint, success in api_results.items():
            self.log_test(f"API Endpoint: {endpoint}", success)
        
        # Test 3: Pipeline Functionality
        pipeline_results = self.test_pipeline_functionality()
        for test, success in pipeline_results.items():
            self.log_test(f"Pipeline: {test}", success)
        
        # Test 3.5: Pipeline Execution (Enhanced)
        pipeline_execution_results = self.test_pipeline_execution()
        for test, success in pipeline_execution_results.items():
            if isinstance(success, bool):
                self.log_test(f"Pipeline Execution: {test}", success)
            else:
                self.log_test(f"Pipeline Execution: {test}", False, str(success))
        
        # Test 4: Service Health
        health_results = self.test_service_health()
        if 'error' not in health_results:
            self.log_test("Service Health Monitoring", True, 
                         f"Total: {health_results['total']}, Healthy: {health_results['healthy']}, "
                         f"Health: {health_results['health_percentage']:.1f}%")
        else:
            self.log_test("Service Health Monitoring", False, health_results['error'])
        
        # Test 5: Page Consistency
        consistency_results = self.test_page_consistency()
        consistent_pages = sum(1 for page_data in consistency_results.values() 
                             if page_data.get('status') == 'loaded')
        total_pages = len(consistency_results)
        self.log_test("Page Consistency", consistent_pages == total_pages,
                     f"{consistent_pages}/{total_pages} pages consistent")
        
        # Test 6: Data Quality
        quality_results = self.test_data_quality()
        if 'error' not in quality_results:
            self.log_test("Data Quality Metrics", True,
                         f"Score: {quality_results['overall_score']:.1%}, "
                         f"Checks: {quality_results['checks_performed']}")
        else:
            self.log_test("Data Quality Metrics", False, quality_results['error'])
        
        # Test 7: Storage Functionality
        storage_results = self.test_storage_functionality()
        if 'error' not in storage_results:
            self.log_test("Storage Management", True,
                         f"Stats: {storage_results['has_stats']}, "
                         f"Buckets: {storage_results['has_buckets']}")
        else:
            self.log_test("Storage Management", False, storage_results['error'])
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 QA TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        duration = datetime.now() - self.start_time
        print(f"Duration: {duration.total_seconds():.1f} seconds")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 60)

def main():
    """Main test runner"""
    tester = PlatformQATester()
    
    try:
        tester.run_comprehensive_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
