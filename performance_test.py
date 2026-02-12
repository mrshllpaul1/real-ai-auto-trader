#!/usr/bin/env python3
"""
Performance Verification Test - AI Crypto Trading Platform Backend
Focus: Response time verification for critical endpoints (target <100ms for internal endpoints)
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple
import statistics

# Backend URL from environment configuration
BASE_URL = "https://crypto-ai-fixes.preview.emergentagent.com/api"

class PerformanceTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout for performance testing
        
    def test_endpoint_performance(self, endpoint: str, method: str = "GET", 
                                data: Dict = None, runs: int = 3) -> Dict:
        """Test endpoint performance with multiple runs"""
        url = f"{BASE_URL}{endpoint}"
        response_times = []
        statuses = []
        
        print(f"Testing {method} {endpoint}...")
        
        for run in range(runs):
            try:
                start_time = time.time()
                
                if method.upper() == "GET":
                    response = self.session.get(url)
                elif method.upper() == "POST":
                    response = self.session.post(url, json=data or {})
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                response_times.append(response_time_ms)
                statuses.append(response.status_code)
                
                # Small delay between runs
                if run < runs - 1:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"  ❌ Run {run + 1} failed: {str(e)}")
                response_times.append(float('inf'))
                statuses.append(0)
        
        # Calculate statistics
        valid_times = [t for t in response_times if t != float('inf')]
        
        result = {
            'endpoint': endpoint,
            'method': method,
            'runs': runs,
            'successful_runs': len(valid_times),
            'avg_response_time_ms': statistics.mean(valid_times) if valid_times else float('inf'),
            'min_response_time_ms': min(valid_times) if valid_times else float('inf'),
            'max_response_time_ms': max(valid_times) if valid_times else float('inf'),
            'status_codes': statuses,
            'success_rate': len(valid_times) / runs * 100,
            'meets_target': statistics.mean(valid_times) < 100 if valid_times else False
        }
        
        # Print result
        if result['successful_runs'] > 0:
            avg_time = result['avg_response_time_ms']
            status = "✅" if result['meets_target'] else "⚠️" if avg_time < 500 else "❌"
            print(f"  {status} Avg: {avg_time:.1f}ms (min: {result['min_response_time_ms']:.1f}ms, max: {result['max_response_time_ms']:.1f}ms)")
            print(f"     Status codes: {set(statuses)}, Success rate: {result['success_rate']:.1f}%")
        else:
            print(f"  ❌ All runs failed")
        
        self.results.append(result)
        return result

    def run_critical_endpoints_test(self):
        """Test the critical endpoints mentioned in the review request"""
        print("🚀 PERFORMANCE VERIFICATION TEST - AI CRYPTO TRADING PLATFORM")
        print("=" * 70)
        print(f"Target: <100ms for internal endpoints")
        print(f"Backend URL: {BASE_URL}")
        print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Critical API endpoints from review request
        critical_endpoints = [
            "/health",
            "/kraken/status", 
            "/ensemble/status",
            "/tethys/status",
            "/auto-trading/status",
            "/triggers/list"
        ]
        
        print("1. TESTING CRITICAL API ENDPOINTS")
        print("-" * 40)
        
        for endpoint in critical_endpoints:
            self.test_endpoint_performance(endpoint, runs=3)
        
        print()
        print("2. TESTING DATABASE POOL STATS")
        print("-" * 40)
        
        # Database monitoring endpoint
        self.test_endpoint_performance("/monitoring/health/detailed", runs=3)
        
        print()
        print("3. TESTING CRITICAL TRADING ENDPOINTS")
        print("-" * 40)
        
        # Critical trading endpoints
        trading_endpoints = [
            ("/market/prices?coin_ids=bitcoin,ethereum", "GET"),
            ("/sentiment/market", "GET")
        ]
        
        for endpoint, method in trading_endpoints:
            self.test_endpoint_performance(endpoint, method=method, runs=3)
        
        print()
        self.generate_performance_report()

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("📊 PERFORMANCE REPORT")
        print("=" * 70)
        
        # Overall statistics
        successful_tests = [r for r in self.results if r['successful_runs'] > 0]
        total_tests = len(self.results)
        success_rate = len(successful_tests) / total_tests * 100 if total_tests > 0 else 0
        
        print(f"Total endpoints tested: {total_tests}")
        print(f"Successful tests: {len(successful_tests)} ({success_rate:.1f}%)")
        
        if successful_tests:
            all_response_times = [r['avg_response_time_ms'] for r in successful_tests]
            avg_response_time = statistics.mean(all_response_times)
            
            print(f"Average response time: {avg_response_time:.1f}ms")
            print(f"Fastest endpoint: {min(all_response_times):.1f}ms")
            print(f"Slowest endpoint: {max(all_response_times):.1f}ms")
            
            # Performance categories
            fast_endpoints = [r for r in successful_tests if r['avg_response_time_ms'] < 100]
            medium_endpoints = [r for r in successful_tests if 100 <= r['avg_response_time_ms'] < 500]
            slow_endpoints = [r for r in successful_tests if r['avg_response_time_ms'] >= 500]
            
            print()
            print("PERFORMANCE BREAKDOWN:")
            print(f"✅ Fast (<100ms): {len(fast_endpoints)} endpoints")
            print(f"⚠️  Medium (100-500ms): {len(medium_endpoints)} endpoints") 
            print(f"❌ Slow (>500ms): {len(slow_endpoints)} endpoints")
            
            if fast_endpoints:
                print()
                print("FAST ENDPOINTS (<100ms):")
                for result in fast_endpoints:
                    print(f"  ✅ {result['endpoint']}: {result['avg_response_time_ms']:.1f}ms")
            
            if medium_endpoints:
                print()
                print("MEDIUM ENDPOINTS (100-500ms):")
                for result in medium_endpoints:
                    print(f"  ⚠️  {result['endpoint']}: {result['avg_response_time_ms']:.1f}ms")
            
            if slow_endpoints:
                print()
                print("SLOW ENDPOINTS (>500ms):")
                for result in slow_endpoints:
                    print(f"  ❌ {result['endpoint']}: {result['avg_response_time_ms']:.1f}ms")
        
        # Failed endpoints
        failed_tests = [r for r in self.results if r['successful_runs'] == 0]
        if failed_tests:
            print()
            print("FAILED ENDPOINTS:")
            for result in failed_tests:
                print(f"  ❌ {result['endpoint']}: All runs failed")
        
        print()
        print("🎯 PERFORMANCE ASSESSMENT:")
        
        if successful_tests:
            meets_target_count = len([r for r in successful_tests if r['meets_target']])
            target_percentage = meets_target_count / len(successful_tests) * 100
            
            if target_percentage >= 80:
                print(f"✅ EXCELLENT: {target_percentage:.1f}% of endpoints meet <100ms target")
            elif target_percentage >= 60:
                print(f"⚠️  GOOD: {target_percentage:.1f}% of endpoints meet <100ms target")
            else:
                print(f"❌ NEEDS IMPROVEMENT: Only {target_percentage:.1f}% of endpoints meet <100ms target")
        
        # Service status summary
        print()
        print("SERVICE STATUS SUMMARY:")
        critical_services = ["/health", "/kraken/status", "/ensemble/status", "/tethys/status"]
        critical_results = [r for r in self.results if r['endpoint'] in critical_services and r['successful_runs'] > 0]
        
        if len(critical_results) == len(critical_services):
            print("✅ All critical services operational")
        else:
            print(f"⚠️  {len(critical_results)}/{len(critical_services)} critical services operational")

def main():
    """Run performance verification test"""
    tester = PerformanceTester()
    tester.run_critical_endpoints_test()

if __name__ == "__main__":
    main()