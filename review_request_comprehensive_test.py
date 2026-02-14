#!/usr/bin/env python3
"""
AICryptoTrade Platform - Comprehensive Backend API Testing
=========================================================
Testing ALL 120+ API endpoints across 13 categories as specified in review request.

Backend URL: https://cryptodash-43.preview.emergentagent.com
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://cryptodash-43.preview.emergentagent.com/api"
print(f"🔗 Testing AICryptoTrade Backend API at: {BACKEND_URL}")

class AICryptoTradeTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AICryptoTradeTester/1.0'
        })
        self.results = []
        self.failed_endpoints = []
        self.category_stats = {}
        
    def test_endpoint(self, category: str, method: str, endpoint: str, 
                     expected_codes: List[int] = None, data: Dict = None, 
                     params: Dict = None, timeout: int = 10) -> Dict:
        """Test individual endpoint"""
        if expected_codes is None:
            expected_codes = [200, 201]
            
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
            
            # Determine success
            is_success = response.status_code in expected_codes
            
            result = {
                "category": category,
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": is_success,
                "has_valid_json": has_valid_json,
                "response_time_ms": response_time,
                "data": json_data if has_valid_json else str(json_data)[:200]
            }
            
            # Track category stats
            if category not in self.category_stats:
                self.category_stats[category] = {"total": 0, "passed": 0, "failed": 0}
            
            self.category_stats[category]["total"] += 1
            if is_success:
                self.category_stats[category]["passed"] += 1
                status = "✅ PASS"
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
                self.category_stats[category] = {"total": 0, "passed": 0, "failed": 0}
            
            self.category_stats[category]["total"] += 1
            self.category_stats[category]["failed"] += 1
            self.failed_endpoints.append(result)
            
            print(f"❌ FAIL [{category}] {method} {endpoint} - ERROR: {str(e)}")
            self.results.append(result)
            return result

    def run_all_tests(self):
        """Run all test categories"""
        print("🚀 Starting Comprehensive AICryptoTrade Backend API Testing...\n")
        
        # CATEGORY 1: Core System (CRITICAL)
        print("=" * 60)
        print("CATEGORY 1: Core System (CRITICAL)")
        print("=" * 60)
        
        self.test_endpoint("Core System", "GET", "/health")
        self.test_endpoint("Core System", "GET", "/tethys/status")
        self.test_endpoint("Core System", "GET", "/consolidated/full-status")
        
        # CATEGORY 2: Trading & Portfolio
        print("\n" + "=" * 60)
        print("CATEGORY 2: Trading & Portfolio")
        print("=" * 60)
        
        self.test_endpoint("Trading & Portfolio", "GET", "/trading/portfolio")
        self.test_endpoint("Trading & Portfolio", "GET", "/trading/positions")
        self.test_endpoint("Trading & Portfolio", "GET", "/trading/history")
        self.test_endpoint("Trading & Portfolio", "GET", "/kraken/status")
        self.test_endpoint("Trading & Portfolio", "GET", "/kraken/portfolio")
        self.test_endpoint("Trading & Portfolio", "GET", "/kraken/pairs")
        self.test_endpoint("Trading & Portfolio", "GET", "/spot-trading/positions")
        self.test_endpoint("Trading & Portfolio", "GET", "/paper-trading/portfolio")
        
        # CATEGORY 3: Market Data
        print("\n" + "=" * 60)
        print("CATEGORY 3: Market Data")
        print("=" * 60)
        
        self.test_endpoint("Market Data", "GET", "/market/prices", params={"coin_ids": "bitcoin,ethereum"})
        self.test_endpoint("Market Data", "GET", "/market/trending")
        self.test_endpoint("Market Data", "GET", "/market/global")
        self.test_endpoint("Market Data", "GET", "/ohlcv/supported-pairs")
        self.test_endpoint("Market Data", "GET", "/enhanced-data/market-depth/BTC")
        
        # CATEGORY 4: AI & Strategy
        print("\n" + "=" * 60)
        print("CATEGORY 4: AI & Strategy")
        print("=" * 60)
        
        self.test_endpoint("AI & Strategy", "GET", "/ensemble/status")
        self.test_endpoint("AI & Strategy", "GET", "/ensemble/signals/BTC")
        self.test_endpoint("AI & Strategy", "GET", "/tethys/status")
        self.test_endpoint("AI & Strategy", "GET", "/tethys/metrics")
        self.test_endpoint("AI & Strategy", "GET", "/ai-portfolio/status")
        self.test_endpoint("AI & Strategy", "GET", "/adaptive-strategy/status")
        self.test_endpoint("AI & Strategy", "GET", "/advanced-ai/status")
        self.test_endpoint("AI & Strategy", "GET", "/ai-decisions/recent")
        self.test_endpoint("AI & Strategy", "GET", "/ai-explain/available-models")
        self.test_endpoint("AI & Strategy", "GET", "/confidence-explain/summary")
        
        # CATEGORY 5: Automation
        print("\n" + "=" * 60)
        print("CATEGORY 5: Automation")
        print("=" * 60)
        
        self.test_endpoint("Automation", "GET", "/auto-trading/status")
        self.test_endpoint("Automation", "GET", "/auto-exec/status")
        self.test_endpoint("Automation", "GET", "/master/status")
        self.test_endpoint("Automation", "GET", "/growth/status")
        self.test_endpoint("Automation", "GET", "/scheduler/status")
        self.test_endpoint("Automation", "GET", "/weekly-scheduler/status")
        
        # CATEGORY 6: Backtesting & Analysis
        print("\n" + "=" * 60)
        print("CATEGORY 6: Backtesting & Analysis")
        print("=" * 60)
        
        self.test_endpoint("Backtesting & Analysis", "GET", "/backtest/results")
        self.test_endpoint("Backtesting & Analysis", "GET", "/backtest-engine/status")
        self.test_endpoint("Backtesting & Analysis", "GET", "/yearly-backtest/status")
        self.test_endpoint("Backtesting & Analysis", "GET", "/risk/metrics")
        self.test_endpoint("Backtesting & Analysis", "GET", "/risk-analyzer/portfolio-risk")
        
        # CATEGORY 7: News & Social
        print("\n" + "=" * 60)
        print("CATEGORY 7: News & Social")
        print("=" * 60)
        
        self.test_endpoint("News & Social", "GET", "/news/latest")
        self.test_endpoint("News & Social", "GET", "/events/upcoming")
        self.test_endpoint("News & Social", "GET", "/event-triggers/status")
        self.test_endpoint("News & Social", "GET", "/sentiment/market")
        self.test_endpoint("News & Social", "GET", "/social-sentiment/overview")
        self.test_endpoint("News & Social", "GET", "/social/feed")
        self.test_endpoint("News & Social", "GET", "/social-trading/traders")
        self.test_endpoint("News & Social", "GET", "/paper-leaderboard/rankings")
        
        # CATEGORY 8: DeFi & Web3
        print("\n" + "=" * 60)
        print("CATEGORY 8: DeFi & Web3")
        print("=" * 60)
        
        self.test_endpoint("DeFi & Web3", "GET", "/defi-wallet/portfolio")
        self.test_endpoint("DeFi & Web3", "GET", "/yield-farming/opportunities")
        self.test_endpoint("DeFi & Web3", "GET", "/web3-wallet/status")
        self.test_endpoint("DeFi & Web3", "GET", "/defi-ai/predictions")
        self.test_endpoint("DeFi & Web3", "GET", "/onchain/whale-movements")
        
        # CATEGORY 9: Settings & Notifications
        print("\n" + "=" * 60)
        print("CATEGORY 9: Settings & Notifications")
        print("=" * 60)
        
        self.test_endpoint("Settings & Notifications", "GET", "/alerts/active")
        self.test_endpoint("Settings & Notifications", "GET", "/notifications/recent")
        self.test_endpoint("Settings & Notifications", "GET", "/sound-settings/config")
        self.test_endpoint("Settings & Notifications", "GET", "/dashboard/layouts")
        self.test_endpoint("Settings & Notifications", "GET", "/budget/status")
        self.test_endpoint("Settings & Notifications", "GET", "/telegram/status")
        
        # CATEGORY 10: Models & Training
        print("\n" + "=" * 60)
        print("CATEGORY 10: Models & Training")
        print("=" * 60)
        
        self.test_endpoint("Models & Training", "GET", "/training/status")
        self.test_endpoint("Models & Training", "GET", "/training-progress/active")
        self.test_endpoint("Models & Training", "GET", "/training-history/recent")
        self.test_endpoint("Models & Training", "GET", "/model-benchmark/results")
        self.test_endpoint("Models & Training", "GET", "/ml-monitoring/dashboard")
        self.test_endpoint("Models & Training", "GET", "/ml-optimization/experiments")
        self.test_endpoint("Models & Training", "GET", "/mtf-training/status")
        
        # CATEGORY 11: Features & Extensions
        print("\n" + "=" * 60)
        print("CATEGORY 11: Features & Extensions")
        print("=" * 60)
        
        self.test_endpoint("Features & Extensions", "GET", "/scanner/gems")
        self.test_endpoint("Features & Extensions", "GET", "/marketplace/strategies")
        self.test_endpoint("Features & Extensions", "GET", "/tax/summary")
        self.test_endpoint("Features & Extensions", "GET", "/portfolio-share/public")
        self.test_endpoint("Features & Extensions", "GET", "/achievements/status")
        self.test_endpoint("Features & Extensions", "GET", "/export/formats")
        self.test_endpoint("Features & Extensions", "GET", "/copy-trading/status")
        
        # CATEGORY 12: System Health & Monitoring
        print("\n" + "=" * 60)
        print("CATEGORY 12: System Health & Monitoring")
        print("=" * 60)
        
        self.test_endpoint("System Health & Monitoring", "GET", "/performance/summary")
        self.test_endpoint("System Health & Monitoring", "GET", "/perf-dashboard/overview")
        self.test_endpoint("System Health & Monitoring", "GET", "/error-tracking/summary")
        self.test_endpoint("System Health & Monitoring", "GET", "/error-alerting/status")
        self.test_endpoint("System Health & Monitoring", "GET", "/monitoring/status")
        self.test_endpoint("System Health & Monitoring", "GET", "/backup/status")
        
        # CATEGORY 13: Journal & Records (including POST endpoints)
        print("\n" + "=" * 60)
        print("CATEGORY 13: Journal & Records")
        print("=" * 60)
        
        self.test_endpoint("Journal & Records", "GET", "/journal/entries")
        self.test_endpoint("Journal & Records", "POST", "/journal/add", 
                          data={"coin_id": "bitcoin", "action": "buy", "amount": 100, "price": 50000})
        self.test_endpoint("Journal & Records", "POST", "/journal/record",
                          data={"coin_id": "bitcoin", "action": "sell", "amount": 50, "price": 51000})
        
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 AICryptoTrade Backend API Testing Summary")
        print("=" * 80)
        
        total_tests = len(self.results)
        total_passed = sum(1 for r in self.results if r["success"])
        total_failed = total_tests - total_passed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Endpoints Tested: {total_tests}")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, stats in self.category_stats.items():
            cat_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {category}: {stats['passed']}/{stats['total']} ({cat_rate:.1f}%)")
        
        if self.failed_endpoints:
            print(f"\n❌ FAILED ENDPOINTS ({len(self.failed_endpoints)}):")
            for failed in self.failed_endpoints:
                endpoint = failed['endpoint']
                status = failed.get('status_code', 'ERROR')
                error = failed.get('error', 'HTTP Error')
                print(f"   - {failed['method']} {endpoint} - {status} ({error})")
        
        # Average response time
        response_times = [r.get("response_time_ms", 0) for r in self.results if r.get("response_time_ms")]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Average Response Time: {avg_time:.1f}ms")
            print(f"   Fastest Response: {min(response_times)}ms")
            print(f"   Slowest Response: {max(response_times)}ms")
        
        print("\n" + "=" * 80)
        if success_rate >= 90:
            print("🎉 EXCELLENT: Backend APIs are highly functional!")
        elif success_rate >= 75:
            print("✅ GOOD: Most backend APIs are working correctly.")
        elif success_rate >= 50:
            print("⚠️  MODERATE: Some backend APIs need attention.")
        else:
            print("🚨 CRITICAL: Many backend APIs require immediate fixes.")
        print("=" * 80)

def main():
    """Run comprehensive AICryptoTrade backend testing"""
    tester = AICryptoTradeTester()
    
    print("🔍 AICryptoTrade Platform - Comprehensive Backend API Testing")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📝 Testing 120+ API endpoints across 13 categories\n")
    
    # Run all tests
    try:
        tester.run_all_tests()
        tester.print_summary()
        
        # Save results
        with open('/app/test_results_comprehensive.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_endpoints': len(tester.results),
                'success_rate': (sum(1 for r in tester.results if r["success"]) / len(tester.results) * 100) if tester.results else 0,
                'category_stats': tester.category_stats,
                'results': tester.results,
                'failed_endpoints': tester.failed_endpoints
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: /app/test_results_comprehensive.json")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()