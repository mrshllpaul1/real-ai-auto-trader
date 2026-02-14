#!/usr/bin/env python3
"""
Focused Performance Test for Tethys AI Crypto Trading Platform
Testing specific endpoints mentioned in review request for <100ms response time
"""

import requests
import time
import json
from typing import Dict, List

# Backend URL from environment
BACKEND_URL = "https://push-to-emerge.preview.emergentagent.com/api"

class FocusedPerformanceTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 5  # Shorter timeout for performance testing
        
    def test_endpoint_performance(self, method: str, endpoint: str, data: dict = None) -> Dict:
        """Test endpoint with focus on performance metrics"""
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
                "success": response.status_code in [200, 201, 202],
                "meets_performance": response_time < 100,
                "response_size": len(response.content) if response.content else 0
            }
            
            # Add key response data
            try:
                response_data = response.json()
                result["has_data"] = bool(response_data)
                
                # Extract key fields based on endpoint
                if endpoint == "/health":
                    result["health_status"] = response_data.get("status")
                elif endpoint == "/errors/stats":
                    result["total_errors"] = response_data.get("total_errors", 0)
                elif endpoint == "/system-state/all":
                    result["components_count"] = len(response_data) if isinstance(response_data, dict) else 0
                elif endpoint == "/performance/summary":
                    result["cache_hit_rate"] = response_data.get("cache", {}).get("hit_rate", 0)
                elif endpoint == "/training-progress/active":
                    result["active_tasks"] = len(response_data.get("active_tasks", [])) if isinstance(response_data, dict) else 0
                elif endpoint == "/tethys/status":
                    result["tethys_status"] = response_data.get("status")
                    
            except Exception as e:
                result["has_data"] = False
                result["parse_error"] = str(e)
                
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time_ms": round(response_time, 1),
                "success": False,
                "meets_performance": False,
                "error": str(e),
                "response_size": 0
            }

def main():
    """Run focused performance testing on review request endpoints"""
    print("🎯 FOCUSED PERFORMANCE TEST - TETHYS AI CRYPTO TRADING PLATFORM")
    print(f"Backend URL: {BACKEND_URL}")
    print("Target: All endpoints should respond in under 100ms")
    print("=" * 80)
    
    tester = FocusedPerformanceTester()
    
    # Test endpoints from review request
    test_endpoints = [
        # 1. Response Time Performance (Critical)
        ("GET", "/health"),
        ("GET", "/errors/stats"),
        ("GET", "/system-state/all"),
        ("GET", "/performance/summary"),
        
        # 2. Error Management (Lightweight)
        ("GET", "/errors/recent"),
        ("GET", "/errors/health-check"),
        
        # 3. Training Functionality
        ("POST", "/training/train-all"),
        ("GET", "/training-progress/active"),
        
        # 4. Core API Regression Tests
        ("GET", "/market/prices"),
        ("GET", "/tethys/status")
    ]
    
    print("🚀 TESTING ENDPOINTS...")
    print("-" * 80)
    
    results = []
    for method, endpoint, *data in test_endpoints:
        payload = data[0] if data else None
        
        print(f"Testing {method} {endpoint}...", end=" ")
        result = tester.test_endpoint_performance(method, endpoint, payload)
        results.append(result)
        
        # Status indicators
        if result["success"]:
            status_icon = "✅"
        else:
            status_icon = "❌"
            
        if result["meets_performance"]:
            perf_icon = "⚡"
        else:
            perf_icon = "🐌"
            
        print(f"{status_icon} {perf_icon} {result['response_time_ms']}ms")
        
        # Show additional info for failed or slow requests
        if not result["success"]:
            error_msg = result.get('error', f'HTTP {result["status_code"]}')
            print(f"   ❌ Error: {error_msg}")
        elif not result["meets_performance"]:
            print(f"   🐌 Slow response: {result['response_time_ms']}ms (target: <100ms)")
    
    # Generate summary
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    performance_tests = sum(1 for r in results if r["meets_performance"])
    
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    performance_rate = (performance_tests / total_tests * 100) if total_tests > 0 else 0
    
    avg_response_time = sum(r["response_time_ms"] for r in results) / total_tests if total_tests > 0 else 0
    
    print(f"Total Endpoints Tested: {total_tests}")
    print(f"Successful Responses: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"Meeting Performance Target (<100ms): {performance_tests}/{total_tests} ({performance_rate:.1f}%)")
    print(f"Average Response Time: {avg_response_time:.1f}ms")
    
    # Critical findings
    failed_endpoints = [r for r in results if not r["success"]]
    slow_endpoints = [r for r in results if r["success"] and not r["meets_performance"]]
    
    if failed_endpoints:
        print(f"\n❌ FAILED ENDPOINTS ({len(failed_endpoints)}):")
        for result in failed_endpoints:
            error_msg = result.get('error', f'HTTP {result["status_code"]}')
            print(f"   • {result['method']} {result['endpoint']} - {error_msg}")
    
    if slow_endpoints:
        print(f"\n🐌 SLOW ENDPOINTS ({len(slow_endpoints)}) - Over 100ms:")
        for result in slow_endpoints:
            print(f"   • {result['method']} {result['endpoint']} - {result['response_time_ms']}ms")
    
    # Performance breakdown by category
    print(f"\n📈 PERFORMANCE BY CATEGORY:")
    
    categories = {
        "Response Time Performance": ["/health", "/errors/stats", "/system-state/all", "/performance/summary"],
        "Error Management": ["/errors/recent", "/errors/health-check"],
        "Training Functionality": ["/training/train-all", "/training-progress/active"],
        "Core API Regression": ["/market/prices", "/tethys/status"]
    }
    
    for category, endpoints in categories.items():
        category_results = [r for r in results if r["endpoint"] in endpoints]
        if category_results:
            success_count = sum(1 for r in category_results if r["success"])
            perf_count = sum(1 for r in category_results if r["meets_performance"])
            avg_time = sum(r["response_time_ms"] for r in category_results) / len(category_results)
            
            print(f"   {category}:")
            print(f"     Success: {success_count}/{len(category_results)} | Performance: {perf_count}/{len(category_results)} | Avg: {avg_time:.1f}ms")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if performance_rate >= 80:
        print("   ✅ EXCELLENT - Most endpoints meet performance requirements")
    elif performance_rate >= 60:
        print("   ⚠️ GOOD - Majority of endpoints meet performance requirements")
    elif performance_rate >= 40:
        print("   ⚠️ NEEDS IMPROVEMENT - Some performance issues detected")
    else:
        print("   ❌ CRITICAL - Significant performance issues require attention")
    
    return results

if __name__ == "__main__":
    results = main()