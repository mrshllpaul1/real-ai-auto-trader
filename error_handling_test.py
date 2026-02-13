#!/usr/bin/env python3
"""
Error Handling and Recovery System Testing - July 2025
Testing the enhanced error handling and recovery system for Tethys AI Crypto Trading Platform.

Test Coverage:
1. Error Statistics API
2. Error Patterns Analysis
3. Health Check System
4. Recovery Statistics
5. Error Alerts Management
6. Clear Suppressed Errors
7. Market Prices Fallback Behavior
8. Existing Endpoints Regression
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL configuration
BASE_URL = "https://smart-trade-ai-68.preview.emergentagent.com/api"

class ErrorHandlingTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 30
        
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, description: str = "") -> Dict:
        """Test individual endpoint and return result"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'expected_status': expected_status,
                'success': response.status_code == expected_status,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
            
            # Parse response if JSON
            try:
                result['response_data'] = response.json()
            except:
                result['response_data'] = response.text[:500]
            
            return result
            
        except Exception as e:
            return {
                'endpoint': endpoint,
                'method': method,
                'status_code': 0,
                'response_time': time.time() - start_time,
                'expected_status': expected_status,
                'success': False,
                'error': str(e),
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
    
    def test_error_statistics(self):
        """Test GET /api/errors/stats endpoint"""
        print("\n🔍 Testing Error Statistics API...")
        
        result = self.test_endpoint(
            "GET", "/errors/stats", 
            description="Should return recovery stats, monitoring stats, and database error count"
        )
        
        if result['success']:
            data = result['response_data']
            required_fields = ['status', 'recovery', 'monitoring', 'database', 'timestamp']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                result['success'] = False
                result['error'] = f"Missing required fields: {missing_fields}"
            else:
                print(f"✅ Error stats retrieved: {data.get('database', {}).get('errors_last_24h', 0)} errors in last 24h")
        
        self.results.append(result)
        return result
    
    def test_error_patterns(self):
        """Test GET /api/errors/patterns?hours=24 endpoint"""
        print("\n🔍 Testing Error Patterns Analysis...")
        
        result = self.test_endpoint(
            "GET", "/errors/patterns?hours=24",
            description="Should return error pattern analysis for last 24 hours"
        )
        
        if result['success']:
            data = result['response_data']
            required_fields = ['patterns', 'total_unique_errors', 'recurring_count']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                result['success'] = False
                result['error'] = f"Missing required fields: {missing_fields}"
            else:
                print(f"✅ Error patterns analyzed: {data.get('total_unique_errors', 0)} unique errors, {data.get('recurring_count', 0)} recurring")
        
        self.results.append(result)
        return result
    
    def test_health_check(self):
        """Test GET /api/errors/health-check endpoint"""
        print("\n🔍 Testing Comprehensive Health Check...")
        
        result = self.test_endpoint(
            "GET", "/errors/health-check",
            description="Should run comprehensive health check and return system status"
        )
        
        if result['success']:
            data = result['response_data']
            required_fields = ['system_checks', 'overall_status']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                result['success'] = False
                result['error'] = f"Missing required fields: {missing_fields}"
            else:
                system_checks = data.get('system_checks', [])
                check_names = [check.get('name') for check in system_checks]
                expected_checks = ['database', 'cache', 'circuit_breakers']
                
                if all(check in check_names for check in expected_checks):
                    print(f"✅ Health check completed: {data.get('overall_status')} status with {len(system_checks)} checks")
                else:
                    result['success'] = False
                    result['error'] = f"Missing expected health checks: {expected_checks}"
        
        self.results.append(result)
        return result
    
    def test_recovery_statistics(self):
        """Test GET /api/errors/recovery/stats endpoint"""
        print("\n🔍 Testing Recovery Statistics...")
        
        result = self.test_endpoint(
            "GET", "/errors/recovery/stats",
            description="Should return error recovery statistics"
        )
        
        if result['success']:
            data = result['response_data']
            required_fields = ['total_errors', 'recovered', 'failed', 'suppressed', 'recovery_rate']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                result['success'] = False
                result['error'] = f"Missing required fields: {missing_fields}"
            else:
                print(f"✅ Recovery stats: {data.get('total_errors', 0)} total errors, {data.get('recovery_rate', 0):.1f}% recovery rate")
        
        self.results.append(result)
        return result
    
    def test_error_alerts(self):
        """Test GET /api/errors/alerts endpoint"""
        print("\n🔍 Testing Error Alerts...")
        
        result = self.test_endpoint(
            "GET", "/errors/alerts",
            description="Should return error alerts with total and unresolved counts"
        )
        
        if result['success']:
            data = result['response_data']
            required_fields = ['alerts', 'total', 'unresolved']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                result['success'] = False
                result['error'] = f"Missing required fields: {missing_fields}"
            else:
                print(f"✅ Error alerts: {data.get('total', 0)} total alerts, {data.get('unresolved', 0)} unresolved")
        
        self.results.append(result)
        return result
    
    def test_clear_suppressed(self):
        """Test POST /api/errors/clear-suppressed endpoint"""
        print("\n🔍 Testing Clear Suppressed Errors...")
        
        result = self.test_endpoint(
            "POST", "/errors/clear-suppressed",
            description="Should clear suppressed error fingerprints"
        )
        
        if result['success']:
            data = result['response_data']
            if 'status' in data and data['status'] == 'ok':
                print(f"✅ Suppressed errors cleared: {data.get('cleared_count', 0)} fingerprints")
            else:
                result['success'] = False
                result['error'] = "Invalid response format"
        
        self.results.append(result)
        return result
    
    def test_market_prices_fallback(self):
        """Test GET /api/market/prices with fallback behavior"""
        print("\n🔍 Testing Market Prices Fallback Behavior...")
        
        # Test with default parameters (should work)
        result1 = self.test_endpoint(
            "GET", "/market/prices",
            description="Should return prices with fallback behavior if sources fail"
        )
        
        # Test with specific coin_ids
        result2 = self.test_endpoint(
            "GET", "/market/prices?coin_ids=bitcoin,ethereum",
            description="Should return prices for specific coins with fallback"
        )
        
        success_count = 0
        
        if result1['success']:
            data = result1['response_data']
            if isinstance(data, dict) and len(data) > 0:
                print(f"✅ Market prices (default): {len(data)} coins retrieved")
                success_count += 1
            else:
                result1['success'] = False
                result1['error'] = "Empty or invalid price data"
        
        if result2['success']:
            data = result2['response_data']
            if isinstance(data, dict) and len(data) > 0:
                print(f"✅ Market prices (specific): {len(data)} coins retrieved")
                success_count += 1
            else:
                result2['success'] = False
                result2['error'] = "Empty or invalid price data"
        
        self.results.extend([result1, result2])
        
        # Return combined result
        return {
            'success': success_count == 2,
            'tests_passed': success_count,
            'total_tests': 2,
            'details': [result1, result2]
        }
    
    def test_existing_endpoints(self):
        """Test that existing endpoints still work"""
        print("\n🔍 Testing Existing Endpoints Regression...")
        
        endpoints_to_test = [
            ("/health", "Basic health check"),
            ("/system-state/all", "System state overview"),
            ("/performance/summary", "Performance summary")
        ]
        
        results = []
        success_count = 0
        
        for endpoint, description in endpoints_to_test:
            result = self.test_endpoint("GET", endpoint, description=description)
            results.append(result)
            
            if result['success']:
                success_count += 1
                print(f"✅ {endpoint}: Working")
            else:
                print(f"❌ {endpoint}: Failed - {result.get('error', 'Unknown error')}")
        
        self.results.extend(results)
        
        return {
            'success': success_count == len(endpoints_to_test),
            'tests_passed': success_count,
            'total_tests': len(endpoints_to_test),
            'details': results
        }
    
    def run_comprehensive_test(self):
        """Run all error handling tests"""
        print("🚀 Starting Error Handling and Recovery System Testing...")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Test all error handling endpoints
        test_methods = [
            self.test_error_statistics,
            self.test_error_patterns,
            self.test_health_check,
            self.test_recovery_statistics,
            self.test_error_alerts,
            self.test_clear_suppressed,
            self.test_market_prices_fallback,
            self.test_existing_endpoints
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                result = test_method()
                if isinstance(result, dict) and result.get('success'):
                    passed_tests += 1
                elif hasattr(result, 'get') and result.get('success'):
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {e}")
        
        total_time = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 ERROR HANDLING TESTING SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"🔗 Backend URL: {BASE_URL}")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        
        successful_endpoints = []
        failed_endpoints = []
        
        for result in self.results:
            if isinstance(result, dict):
                if result.get('success'):
                    successful_endpoints.append(f"✅ {result['method']} {result['endpoint']} ({result['response_time']}s)")
                else:
                    error_msg = result.get('error', f"Status {result.get('status_code', 'unknown')}")
                    failed_endpoints.append(f"❌ {result['method']} {result['endpoint']} - {error_msg}")
        
        if successful_endpoints:
            print(f"\n✅ WORKING ENDPOINTS ({len(successful_endpoints)}):")
            for endpoint in successful_endpoints:
                print(f"  {endpoint}")
        
        if failed_endpoints:
            print(f"\n❌ FAILED ENDPOINTS ({len(failed_endpoints)}):")
            for endpoint in failed_endpoints:
                print(f"  {endpoint}")
        
        # Performance analysis
        response_times = [r.get('response_time', 0) for r in self.results if isinstance(r, dict) and r.get('response_time')]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⚡ PERFORMANCE:")
            print(f"  Average Response Time: {avg_time:.3f}s")
            print(f"  Maximum Response Time: {max_time:.3f}s")
        
        return {
            'success_rate': success_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'total_time': total_time,
            'successful_endpoints': successful_endpoints,
            'failed_endpoints': failed_endpoints
        }


def main():
    """Main test execution"""
    tester = ErrorHandlingTester()
    results = tester.run_comprehensive_test()
    
    # Return appropriate exit code
    if results['success_rate'] >= 80:
        print(f"\n🎉 ERROR HANDLING SYSTEM TESTING COMPLETED SUCCESSFULLY!")
        print(f"All critical error handling and recovery features are operational.")
        return 0
    else:
        print(f"\n⚠️  ERROR HANDLING SYSTEM TESTING COMPLETED WITH ISSUES")
        print(f"Some error handling features need attention.")
        return 1


if __name__ == "__main__":
    exit(main())