#!/usr/bin/env python3
"""
AICryptoTrade Platform - Accurate Backend API Testing
====================================================
Testing the actual implemented API endpoints based on route analysis.

Backend URL: https://enhance-test.preview.emergentagent.com
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://enhance-test.preview.emergentagent.com/api"
print(f"🔗 Testing AICryptoTrade Backend API at: {BACKEND_URL}")

class AccurateAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AccurateAPITester/1.0'
        })
        self.results = []
        self.failed_endpoints = []
        self.category_stats = {}
        
    def test_endpoint(self, category: str, method: str, endpoint: str, 
                     expected_codes: List[int] = None, data: Dict = None, 
                     params: Dict = None, timeout: int = 15) -> Dict:
        """Test individual endpoint"""
        if expected_codes is None:
            expected_codes = [200, 201, 404]  # 404 can be expected for some endpoints
            
        try:
            url = f"{self.base_url}{endpoint}"
            start_time = time.time()
            
            if method == "GET":
                response = self.session.get(url, params=params, timeout=timeout)
            elif method == "POST":
                response = self.session.post(url, json=data, params=params, timeout=timeout)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            response_time = round((time.time() - start_time) * 1000, 1)
            
            # Check if response is valid JSON
            try:
                json_data = response.json()
                has_valid_json = True
            except:
                json_data = response.text
                has_valid_json = False
            
            # Determine success (200/201 are success, 404 may be expected)
            is_success = response.status_code in [200, 201]
            is_expected_404 = response.status_code == 404 and 404 in expected_codes
            
            result = {
                "category": category,
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": is_success,
                "expected_404": is_expected_404,
                "has_valid_json": has_valid_json,
                "response_time_ms": response_time,
                "data": json_data if has_valid_json else str(json_data)[:200]
            }
            
            # Track category stats
            if category not in self.category_stats:
                self.category_stats[category] = {"total": 0, "passed": 0, "failed": 0, "expected_404": 0}
            
            self.category_stats[category]["total"] += 1
            if is_success:
                self.category_stats[category]["passed"] += 1
                status = "✅ PASS"
            elif is_expected_404:
                self.category_stats[category]["expected_404"] += 1
                status = "⚠️ 404 (expected)"
            else:
                self.category_stats[category]["failed"] += 1
                self.failed_endpoints.append(result)
                status = "❌ FAIL"
            
            print(f"{status} [{category}] {method} {endpoint} - {response.status_code} ({response_time}ms)")
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                "category": category,
                "method": method, 
                "endpoint": endpoint,
                "status_code": 0,
                "success": False,
                "has_valid_json": False,
                "response_time_ms": 0,
                "error": str(e)
            }
            
            if category not in self.category_stats:
                self.category_stats[category] = {"total": 0, "passed": 0, "failed": 0, "expected_404": 0}
            
            self.category_stats[category]["total"] += 1
            self.category_stats[category]["failed"] += 1
            self.failed_endpoints.append(result)
            
            print(f"❌ FAIL [{category}] {method} {endpoint} - ERROR: {str(e)}")
            self.results.append(result)
            return result

    def run_all_tests(self):
        """Run comprehensive tests on actually implemented endpoints"""
        print("🚀 Starting Accurate AICryptoTrade Backend API Testing...\n")
        
        # CATEGORY 1: Core Health & System
        print("=" * 60)
        print("CATEGORY 1: Core Health & System")
        print("=" * 60)
        
        self.test_endpoint("Core Health", "GET", "/health")
        self.test_endpoint("Core Health", "GET", "/")
        
        # CATEGORY 2: Kraken Trading Integration
        print("\n" + "=" * 60)
        print("CATEGORY 2: Kraken Trading Integration")
        print("=" * 60)
        
        self.test_endpoint("Kraken Trading", "GET", "/kraken/status")
        self.test_endpoint("Kraken Trading", "GET", "/kraken/balance")
        self.test_endpoint("Kraken Trading", "GET", "/kraken/ticker/XXBTZUSD")
        self.test_endpoint("Kraken Trading", "GET", "/kraken/open-orders")
        self.test_endpoint("Kraken Trading", "GET", "/kraken/trade-history")
        self.test_endpoint("Kraken Trading", "GET", "/kraken/supported-pairs")
        self.test_endpoint("Kraken Trading", "GET", "/kraken/auto-trader/status")
        self.test_endpoint("Kraken Trading", "GET", "/kraken/auto-trader/positions")
        
        # CATEGORY 3: Ensemble AI System
        print("\n" + "=" * 60)
        print("CATEGORY 3: Ensemble AI System")
        print("=" * 60)
        
        self.test_endpoint("Ensemble AI", "GET", "/ensemble/status")
        self.test_endpoint("Ensemble AI", "GET", "/ensemble/weights")
        self.test_endpoint("Ensemble AI", "GET", "/ensemble/build-status")
        self.test_endpoint("Ensemble AI", "GET", "/ensemble/optimal-universe")
        self.test_endpoint("Ensemble AI", "GET", "/ensemble/comparison")
        self.test_endpoint("Ensemble AI", "GET", "/ensemble/hidden-gems")
        self.test_endpoint("Ensemble AI", "GET", "/ensemble/top-predictions")
        
        # CATEGORY 4: Tethys Safety System  
        print("\n" + "=" * 60)
        print("CATEGORY 4: Tethys Safety System")
        print("=" * 60)
        
        self.test_endpoint("Tethys Safety", "GET", "/tethys/status")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/identity")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/risk/limits")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/audit/summary")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/audit/recent")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/uncertainty/report")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/dashboard")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/sentiment")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/fear-greed")
        self.test_endpoint("Tethys Safety", "GET", "/tethys/news")
        
        # CATEGORY 5: Market Data Services
        print("\n" + "=" * 60)
        print("CATEGORY 5: Market Data Services")  
        print("=" * 60)
        
        self.test_endpoint("Market Data", "GET", "/market/prices")
        self.test_endpoint("Market Data", "GET", "/market/prices", params={"coin_ids": "bitcoin,ethereum"})
        self.test_endpoint("Market Data", "GET", "/market/global")
        self.test_endpoint("Market Data", "GET", "/market/trending")
        self.test_endpoint("Market Data", "GET", "/market/historical/bitcoin")
        self.test_endpoint("Market Data", "GET", "/market/news")
        
        # CATEGORY 6: Trading Journal
        print("\n" + "=" * 60)
        print("CATEGORY 6: Trading Journal")
        print("=" * 60)
        
        self.test_endpoint("Trading Journal", "GET", "/journal/entries")
        self.test_endpoint("Trading Journal", "GET", "/journal/daily")
        self.test_endpoint("Trading Journal", "GET", "/journal/stats")
        self.test_endpoint("Trading Journal", "GET", "/journal/ai-insights")
        
        # Test POST endpoints with valid data
        journal_data = {
            "trade_type": "spot",
            "coin_id": "bitcoin", 
            "symbol": "BTC",
            "action": "buy",
            "amount_usd": 100.0,
            "price": 50000.0,
            "quantity": 0.002,
            "is_paper": True
        }
        self.test_endpoint("Trading Journal", "POST", "/journal/record", data=journal_data)
        self.test_endpoint("Trading Journal", "POST", "/journal/add", data=journal_data)
        
        # CATEGORY 7: Auto Trading & Strategy
        print("\n" + "=" * 60)
        print("CATEGORY 7: Auto Trading & Strategy")
        print("=" * 60)
        
        self.test_endpoint("Auto Trading", "GET", "/auto-trading/status")
        self.test_endpoint("Auto Trading", "GET", "/auto-exec/status") 
        self.test_endpoint("Auto Trading", "GET", "/master/status")
        self.test_endpoint("Auto Trading", "GET", "/growth/status")
        self.test_endpoint("Auto Trading", "GET", "/scheduler/status")
        self.test_endpoint("Auto Trading", "GET", "/weekly-scheduler/status")
        
        # CATEGORY 8: AI & Strategy Services
        print("\n" + "=" * 60)
        print("CATEGORY 8: AI & Strategy Services")
        print("=" * 60)
        
        self.test_endpoint("AI Strategy", "GET", "/adaptive-strategy/status")
        self.test_endpoint("AI Strategy", "GET", "/ai-decisions/recent")
        self.test_endpoint("AI Strategy", "GET", "/confidence-explain/summary")
        
        # CATEGORY 9: Portfolio & Visualization
        print("\n" + "=" * 60)
        print("CATEGORY 9: Portfolio & Visualization")
        print("=" * 60)
        
        self.test_endpoint("Portfolio", "GET", "/portfolio/visualization/summary")
        self.test_endpoint("Portfolio", "GET", "/paper-trading/portfolio")
        
        # CATEGORY 10: Training & ML
        print("\n" + "=" * 60)
        print("CATEGORY 10: Training & ML") 
        print("=" * 60)
        
        self.test_endpoint("Training ML", "GET", "/training/status")
        self.test_endpoint("Training ML", "GET", "/training-progress/active")
        self.test_endpoint("Training ML", "GET", "/training-history/recent")
        self.test_endpoint("Training ML", "GET", "/model-benchmark/results")
        
        # CATEGORY 11: Social & News
        print("\n" + "=" * 60)
        print("CATEGORY 11: Social & News")
        print("=" * 60)
        
        self.test_endpoint("Social News", "GET", "/sentiment/market")
        self.test_endpoint("Social News", "GET", "/social/feed")
        
        # CATEGORY 12: DeFi & Web3
        print("\n" + "=" * 60)
        print("CATEGORY 12: DeFi & Web3")
        print("=" * 60)
        
        self.test_endpoint("DeFi Web3", "GET", "/yield-farming/opportunities")
        
        # CATEGORY 13: Settings & Configuration
        print("\n" + "=" * 60)
        print("CATEGORY 13: Settings & Configuration")
        print("=" * 60)
        
        self.test_endpoint("Settings Config", "GET", "/dashboard/layouts")
        self.test_endpoint("Settings Config", "GET", "/telegram/status")
        
        # CATEGORY 14: Features & Extensions  
        print("\n" + "=" * 60)
        print("CATEGORY 14: Features & Extensions")
        print("=" * 60)
        
        self.test_endpoint("Features Extensions", "GET", "/marketplace/strategies")
        self.test_endpoint("Features Extensions", "GET", "/tax/summary")
        
        # CATEGORY 15: System Monitoring
        print("\n" + "=" * 60)
        print("CATEGORY 15: System Monitoring")
        print("=" * 60)
        
        self.test_endpoint("System Monitoring", "GET", "/performance/summary")
        self.test_endpoint("System Monitoring", "GET", "/error-alerting/status")
        
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 AICryptoTrade Backend API Testing Summary")
        print("=" * 80)
        
        total_tests = len(self.results)
        total_passed = sum(1 for r in self.results if r["success"])
        total_expected_404 = sum(1 for r in self.results if r.get("expected_404", False))
        total_failed = total_tests - total_passed - total_expected_404
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Endpoints Tested: {total_tests}")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ⚠️ Expected 404s: {total_expected_404}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, stats in self.category_stats.items():
            cat_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {category}: {stats['passed']}/{stats['total']} ({cat_rate:.1f}%) [404s: {stats.get('expected_404', 0)}]")
        
        if self.failed_endpoints:
            print(f"\n❌ CRITICAL FAILURES ({len(self.failed_endpoints)}):")
            for failed in self.failed_endpoints:
                if not failed.get("expected_404", False):
                    endpoint = failed['endpoint']
                    status = failed.get('status_code', 'ERROR')
                    error = failed.get('error', 'HTTP Error')
                    print(f"   - {failed['method']} {endpoint} - {status}")
        
        # Working endpoints summary
        working_endpoints = [r for r in self.results if r["success"]]
        print(f"\n✅ WORKING ENDPOINTS ({len(working_endpoints)}):")
        for endpoint in working_endpoints[:10]:  # Show first 10
            print(f"   - {endpoint['method']} {endpoint['endpoint']} ({endpoint['response_time_ms']}ms)")
        if len(working_endpoints) > 10:
            print(f"   ... and {len(working_endpoints) - 10} more")
        
        # Average response time
        response_times = [r.get("response_time_ms", 0) for r in self.results if r.get("response_time_ms")]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Average Response Time: {avg_time:.1f}ms")
            print(f"   Fastest Response: {min(response_times)}ms")
            print(f"   Slowest Response: {max(response_times)}ms")
        
        print("\n" + "=" * 80)
        if success_rate >= 80:
            print("🎉 EXCELLENT: Backend APIs are highly functional!")
        elif success_rate >= 60:
            print("✅ GOOD: Most backend APIs are working correctly.")  
        elif success_rate >= 40:
            print("⚠️  MODERATE: Many backend APIs are working but some need attention.")
        else:
            print("🚨 CRITICAL: Many backend APIs require immediate fixes.")
        print("=" * 80)

def main():
    """Run accurate AICryptoTrade backend testing"""
    tester = AccurateAPITester()
    
    print("🔍 AICryptoTrade Platform - Accurate Backend API Testing")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📝 Testing implemented API endpoints based on route analysis\n")
    
    # Run all tests
    try:
        tester.run_all_tests()
        tester.print_summary()
        
        # Save results
        with open('/app/accurate_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_endpoints': len(tester.results),
                'success_rate': (sum(1 for r in tester.results if r["success"]) / len(tester.results) * 100) if tester.results else 0,
                'category_stats': tester.category_stats,
                'results': tester.results,
                'failed_endpoints': tester.failed_endpoints
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: /app/accurate_test_results.json")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()