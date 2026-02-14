#!/usr/bin/env python3
"""
Optimized Backend Services Testing for Tethys AI Crypto Trading Platform
Focus: Response Time Performance, Error Management, State Persistence, Training, Core APIs
Target: All endpoints should respond in under 100ms
"""

import requests
import time
import json
from typing import Dict, List, Tuple

# Backend URL from environment
BACKEND_URL = "https://push-to-emerge.preview.emergentagent.com/api"

class OptimizedBackendTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 10
        
    def test_endpoint(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200) -> Dict:
        """Test a single endpoint and measure response time"""
        url = f"{BACKEND_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 1),
                "success": response.status_code == expected_status,
                "under_100ms": response_time < 100,
                "response_size": len(response.content) if response.content else 0
            }
            
            # Add response data for analysis
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200] if response.text else ""
                
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time_ms": round(response_time, 1),
                "success": False,
                "under_100ms": False,
                "error": str(e),
                "response_size": 0
            }
    
    def run_performance_tests(self):
        """Test Response Time Performance - Critical requirement: under 100ms"""
        print("🎯 TESTING RESPONSE TIME PERFORMANCE (Target: <100ms)")
        print("=" * 60)
        
        performance_endpoints = [
            ("GET", "/health"),
            ("GET", "/errors/stats"),
            ("GET", "/system-state/all"),
            ("GET", "/performance/summary")
        ]
        
        performance_results = []
        for method, endpoint in performance_endpoints:
            result = self.test_endpoint(method, endpoint)
            performance_results.append(result)
            
            status_icon = "✅" if result["success"] else "❌"
            speed_icon = "⚡" if result["under_100ms"] else "🐌"
            
            print(f"{status_icon} {speed_icon} {method} {endpoint}")
            print(f"   Status: {result['status_code']} | Time: {result['response_time_ms']}ms")
            
            if not result["success"]:
                print(f"   Error: {result.get('error', 'HTTP Error')}")
            
        self.results.extend(performance_results)
        
        # Performance summary
        under_100ms_count = sum(1 for r in performance_results if r["under_100ms"])
        avg_response_time = sum(r["response_time_ms"] for r in performance_results) / len(performance_results)
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Endpoints under 100ms: {under_100ms_count}/{len(performance_results)} ({under_100ms_count/len(performance_results)*100:.1f}%)")
        print(f"   Average response time: {avg_response_time:.1f}ms")
        
        return performance_results
    
    def run_error_management_tests(self):
        """Test Error Management (Lightweight) - Quick error stats and health checks"""
        print("\n🛡️ TESTING ERROR MANAGEMENT (Lightweight)")
        print("=" * 60)
        
        error_endpoints = [
            ("GET", "/errors/stats"),
            ("GET", "/errors/recent"),
            ("GET", "/errors/health-check")
        ]
        
        error_results = []
        for method, endpoint in error_endpoints:
            result = self.test_endpoint(method, endpoint)
            error_results.append(result)
            
            status_icon = "✅" if result["success"] else "❌"
            speed_icon = "⚡" if result["under_100ms"] else "🐌"
            
            print(f"{status_icon} {speed_icon} {method} {endpoint}")
            print(f"   Status: {result['status_code']} | Time: {result['response_time_ms']}ms")
            
            # Show key response data for error management
            if result["success"] and "response_data" in result:
                data = result["response_data"]
                if endpoint == "/errors/stats":
                    print(f"   Stats: {data.get('total_errors', 'N/A')} total errors")
                elif endpoint == "/errors/health-check":
                    print(f"   Health: {data.get('overall_status', 'N/A')}")
            
        self.results.extend(error_results)
        return error_results
    
    def run_state_persistence_tests(self):
        """Test State Persistence - System state management"""
        print("\n💾 TESTING STATE PERSISTENCE")
        print("=" * 60)
        
        state_endpoints = [
            ("GET", "/system-state/all"),
            ("POST", "/system-state/set", {"component": "test_component", "state": {"is_running": True}})
        ]
        
        state_results = []
        for method, endpoint, *data in state_endpoints:
            payload = data[0] if data else None
            result = self.test_endpoint(method, endpoint, payload)
            state_results.append(result)
            
            status_icon = "✅" if result["success"] else "❌"
            speed_icon = "⚡" if result["under_100ms"] else "🐌"
            
            print(f"{status_icon} {speed_icon} {method} {endpoint}")
            print(f"   Status: {result['status_code']} | Time: {result['response_time_ms']}ms")
            
            # Show key response data for state persistence
            if result["success"] and "response_data" in result:
                data = result["response_data"]
                if endpoint == "/system-state/all":
                    components = len(data) if isinstance(data, dict) else 0
                    print(f"   Components: {components} system components tracked")
            
        self.results.extend(state_results)
        return state_results
    
    def run_training_functionality_tests(self):
        """Test Training Functionality - Training operations"""
        print("\n🧠 TESTING TRAINING FUNCTIONALITY")
        print("=" * 60)
        
        training_endpoints = [
            ("POST", "/training/train-all"),
            ("GET", "/training-progress/active")
        ]
        
        training_results = []
        for method, endpoint in training_endpoints:
            result = self.test_endpoint(method, endpoint)
            training_results.append(result)
            
            status_icon = "✅" if result["success"] else "❌"
            speed_icon = "⚡" if result["under_100ms"] else "🐌"
            
            print(f"{status_icon} {speed_icon} {method} {endpoint}")
            print(f"   Status: {result['status_code']} | Time: {result['response_time_ms']}ms")
            
            # Show key response data for training
            if result["success"] and "response_data" in result:
                data = result["response_data"]
                if endpoint == "/training-progress/active":
                    active_tasks = len(data.get('active_tasks', [])) if isinstance(data, dict) else 0
                    print(f"   Active Tasks: {active_tasks} training tasks running")
                elif endpoint == "/training/train-all":
                    status = data.get('status', 'N/A') if isinstance(data, dict) else 'N/A'
                    print(f"   Training Status: {status}")
            
        self.results.extend(training_results)
        return training_results
    
    def run_core_api_regression_tests(self):
        """Test Core API Regression Tests - Basic health and status checks"""
        print("\n🔧 TESTING CORE API REGRESSION")
        print("=" * 60)
        
        core_endpoints = [
            ("GET", "/health"),
            ("GET", "/market/prices", None, [200, 422]),  # May need parameters
            ("GET", "/tethys/status")
        ]
        
        core_results = []
        for endpoint_data in core_endpoints:
            method, endpoint = endpoint_data[0], endpoint_data[1]
            expected_statuses = endpoint_data[3] if len(endpoint_data) > 3 else [200]
            
            result = self.test_endpoint(method, endpoint)
            
            # Check if status is in expected list
            result["success"] = result["status_code"] in expected_statuses
            
            core_results.append(result)
            
            status_icon = "✅" if result["success"] else "❌"
            speed_icon = "⚡" if result["under_100ms"] else "🐌"
            
            print(f"{status_icon} {speed_icon} {method} {endpoint}")
            print(f"   Status: {result['status_code']} | Time: {result['response_time_ms']}ms")
            
            # Show key response data for core APIs
            if result["success"] and "response_data" in result:
                data = result["response_data"]
                if endpoint == "/health":
                    status = data.get('status', 'N/A') if isinstance(data, dict) else 'N/A'
                    print(f"   Health Status: {status}")
                elif endpoint == "/tethys/status":
                    status = data.get('status', 'N/A') if isinstance(data, dict) else 'N/A'
                    print(f"   Tethys Status: {status}")
            
        self.results.extend(core_results)
        return core_results
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 OPTIMIZED BACKEND SERVICES TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        under_100ms_tests = sum(1 for r in self.results if r["under_100ms"])
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        performance_rate = (under_100ms_tests / total_tests * 100) if total_tests > 0 else 0
        
        avg_response_time = sum(r["response_time_ms"] for r in self.results) / total_tests if total_tests > 0 else 0
        max_response_time = max(r["response_time_ms"] for r in self.results) if self.results else 0
        min_response_time = min(r["response_time_ms"] for r in self.results) if self.results else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"   Under 100ms: {under_100ms_tests}/{total_tests} ({performance_rate:.1f}%)")
        print(f"   Average Response Time: {avg_response_time:.1f}ms")
        print(f"   Response Time Range: {min_response_time:.1f}ms - {max_response_time:.1f}ms")
        
        # Critical issues
        critical_issues = []
        failed_tests = [r for r in self.results if not r["success"]]
        slow_tests = [r for r in self.results if r["response_time_ms"] > 100]
        
        if failed_tests:
            critical_issues.append(f"❌ {len(failed_tests)} endpoints failed")
        if slow_tests:
            critical_issues.append(f"🐌 {len(slow_tests)} endpoints over 100ms")
        
        if critical_issues:
            print(f"\n⚠️ CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ NO CRITICAL ISSUES FOUND")
        
        # Performance breakdown by category
        print(f"\n📈 PERFORMANCE BREAKDOWN:")
        categories = {
            "Performance Tests": [r for r in self.results if r["endpoint"] in ["/health", "/errors/stats", "/system-state/all", "/performance/summary"]],
            "Error Management": [r for r in self.results if "/errors/" in r["endpoint"]],
            "State Persistence": [r for r in self.results if "/system-state/" in r["endpoint"]],
            "Training": [r for r in self.results if "/training" in r["endpoint"]],
            "Core APIs": [r for r in self.results if r["endpoint"] in ["/health", "/market/prices", "/tethys/status"]]
        }
        
        for category, tests in categories.items():
            if tests:
                success_count = sum(1 for t in tests if t["success"])
                under_100ms_count = sum(1 for t in tests if t["under_100ms"])
                avg_time = sum(t["response_time_ms"] for t in tests) / len(tests)
                print(f"   {category}: {success_count}/{len(tests)} success, {under_100ms_count}/{len(tests)} <100ms, avg {avg_time:.1f}ms")
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "under_100ms_tests": under_100ms_tests,
            "performance_rate": performance_rate,
            "avg_response_time": avg_response_time,
            "critical_issues": len(failed_tests) + len(slow_tests)
        }

def main():
    """Run optimized backend services testing"""
    print("🚀 STARTING OPTIMIZED BACKEND SERVICES TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    tester = OptimizedBackendTester()
    
    # Run all test categories
    tester.run_performance_tests()
    tester.run_error_management_tests()
    tester.run_state_persistence_tests()
    tester.run_training_functionality_tests()
    tester.run_core_api_regression_tests()
    
    # Generate summary
    summary = tester.generate_summary()
    
    # Return results for further analysis
    return tester.results, summary

if __name__ == "__main__":
    results, summary = main()