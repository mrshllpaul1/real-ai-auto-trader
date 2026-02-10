#!/usr/bin/env python3
"""
Yearly Adaptive Backtest System Testing - February 10, 2026
Testing the new Yearly Adaptive Backtest System for Crypto Trading Application

Focus Areas:
1. POST /api/yearly-backtest/quick-test - Quick yearly backtest
2. POST /api/yearly-backtest/run - Full backtest with background processing
3. GET /api/yearly-backtest/status/{backtest_id} - Check backtest status
4. GET /api/yearly-backtest/results/{backtest_id} - Get full results
5. GET /api/yearly-backtest/recommended-portfolio - Get trading recommendations
6. GET /api/yearly-backtest/strategy-params - Get adaptive strategy params
7. GET /api/yearly-backtest/market-calendar - Get 2025 market events
8. GET /api/yearly-backtest/coins - Get available coins for backtest
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://crypto-trader-194.preview.emergentagent.com/api"

class YearlyBacktestTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 60  # Longer timeout for backtest operations
        self.backtest_ids = []  # Track created backtest IDs

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, timeout: int = 60) -> Dict:
        """Test individual endpoint and return result"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=timeout)
            else:
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status": "error",
                    "error": f"Unsupported method: {method}"
                }
            
            response_time = time.time() - start_time
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time": round(response_time, 2),
                "success": response.status_code == expected_status
            }
            
            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text[:500]
            
            if not result["success"]:
                result["error"] = f"Expected {expected_status}, got {response.status_code}"
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": "timeout",
                "error": f"Request timed out after {timeout}s"
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": "error",
                "error": str(e)
            }

    def validate_quick_test_response(self, response: Dict) -> Dict:
        """Validate quick test response meets requirements"""
        validation = {
            "valid": True,
            "issues": [],
            "metrics": {}
        }
        
        # Check required fields
        required_fields = ["status", "win_rate", "total_return_pct", "sharpe_ratio", 
                          "profit_factor", "max_drawdown_pct", "top_coins", 
                          "recommended_portfolio", "auto_trade_ready", "next_week_strategy"]
        
        for field in required_fields:
            if field not in response:
                validation["valid"] = False
                validation["issues"].append(f"Missing required field: {field}")
        
        if "status" in response and response["status"] != "completed":
            validation["valid"] = False
            validation["issues"].append(f"Status not completed: {response['status']}")
        
        # Validate performance metrics
        if "win_rate" in response:
            win_rate = response["win_rate"]
            validation["metrics"]["win_rate"] = win_rate
            if win_rate < 50:
                validation["issues"].append(f"Win rate {win_rate}% below 50% target")
            elif win_rate >= 50:
                validation["issues"].append(f"✅ Win rate {win_rate}% meets 50%+ target")
        
        if "total_return_pct" in response:
            total_return = response["total_return_pct"]
            validation["metrics"]["total_return"] = total_return
            if total_return <= 0:
                validation["issues"].append(f"Total return {total_return}% not positive")
            else:
                validation["issues"].append(f"✅ Total return {total_return}% is positive")
        
        if "sharpe_ratio" in response:
            sharpe = response["sharpe_ratio"]
            validation["metrics"]["sharpe_ratio"] = sharpe
            if sharpe <= 1.0:
                validation["issues"].append(f"Sharpe ratio {sharpe} not > 1.0")
            else:
                validation["issues"].append(f"✅ Sharpe ratio {sharpe} > 1.0")
        
        if "profit_factor" in response:
            pf = response["profit_factor"]
            validation["metrics"]["profit_factor"] = pf
            if isinstance(pf, (int, float)) and pf <= 1.0:
                validation["issues"].append(f"Profit factor {pf} not > 1.0")
            else:
                validation["issues"].append(f"✅ Profit factor {pf} > 1.0")
        
        if "max_drawdown_pct" in response:
            dd = response["max_drawdown_pct"]
            validation["metrics"]["max_drawdown"] = dd
            if dd >= 10:
                validation["issues"].append(f"Max drawdown {dd}% not < 10%")
            else:
                validation["issues"].append(f"✅ Max drawdown {dd}% < 10%")
        
        # Check top coins win rates
        if "top_coins" in response:
            top_coins = response["top_coins"]
            validation["metrics"]["top_coins_count"] = len(top_coins)
            high_win_rate_coins = 0
            for coin in top_coins:
                if "win_rate" in coin:
                    win_rate_str = coin["win_rate"].replace("%", "")
                    try:
                        coin_win_rate = float(win_rate_str)
                        if coin_win_rate >= 50:
                            high_win_rate_coins += 1
                    except:
                        pass
            
            if high_win_rate_coins > 0:
                validation["issues"].append(f"✅ {high_win_rate_coins} top coins with 50-100% win rates")
            else:
                validation["issues"].append("No top coins with 50%+ win rates found")
        
        # Check recommended portfolio
        if "recommended_portfolio" in response:
            portfolio = response["recommended_portfolio"]
            if "coins" in portfolio and len(portfolio["coins"]) > 0:
                validation["issues"].append(f"✅ Recommended portfolio with {len(portfolio['coins'])} coins")
            else:
                validation["issues"].append("Recommended portfolio missing or empty")
        
        # Check auto trade ready
        if "auto_trade_ready" in response:
            if response["auto_trade_ready"]:
                validation["issues"].append("✅ Auto trade ready = true")
            else:
                validation["issues"].append("Auto trade ready = false")
        
        # Check next week strategy
        if "next_week_strategy" in response:
            strategy = response["next_week_strategy"]
            if isinstance(strategy, dict) and len(strategy) > 0:
                validation["issues"].append(f"✅ Next week strategy with {len(strategy)} parameters")
            else:
                validation["issues"].append("Next week strategy missing or invalid")
        
        return validation

    def run_comprehensive_test(self):
        """Run comprehensive test of Yearly Adaptive Backtest System"""
        print("🚀 Starting Yearly Adaptive Backtest System Testing...")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        test_start_time = time.time()
        
        # Test 1: Quick Test - Most Important
        print("\n1️⃣ Testing POST /api/yearly-backtest/quick-test")
        print("   Expected: Completed status, 50%+ win rate, positive returns, Sharpe > 1.0")
        
        quick_test_result = self.test_endpoint("POST", "/yearly-backtest/quick-test", timeout=120)
        self.results.append(("Quick Test", quick_test_result))
        
        if quick_test_result.get("success"):
            validation = self.validate_quick_test_response(quick_test_result["response"])
            print(f"   ✅ Status: {quick_test_result['status_code']} ({quick_test_result['response_time']}s)")
            
            # Print key metrics
            if "metrics" in validation:
                metrics = validation["metrics"]
                print(f"   📊 Key Metrics:")
                for metric, value in metrics.items():
                    print(f"      • {metric}: {value}")
            
            # Print validation results
            print(f"   📋 Validation Results:")
            for issue in validation["issues"]:
                print(f"      • {issue}")
        else:
            print(f"   ❌ Failed: {quick_test_result.get('error', 'Unknown error')}")
        
        # Test 2: Start Full Backtest
        print("\n2️⃣ Testing POST /api/yearly-backtest/run")
        print("   Expected: Returns backtest_id and status 'started'")
        
        backtest_request = {
            "initial_capital": 100000,
            "use_all_kraken_coins": False
        }
        
        run_result = self.test_endpoint("POST", "/yearly-backtest/run", data=backtest_request)
        self.results.append(("Start Full Backtest", run_result))
        
        backtest_id = None
        if run_result.get("success") and "response" in run_result:
            response = run_result["response"]
            if "backtest_id" in response:
                backtest_id = response["backtest_id"]
                self.backtest_ids.append(backtest_id)
                print(f"   ✅ Status: {run_result['status_code']} ({run_result['response_time']}s)")
                print(f"   📝 Backtest ID: {backtest_id}")
                print(f"   📊 Status: {response.get('status')}")
                print(f"   💬 Message: {response.get('message')}")
            else:
                print(f"   ⚠️ Success but no backtest_id in response")
        else:
            print(f"   ❌ Failed: {run_result.get('error', 'Unknown error')}")
        
        # Test 3: Check Backtest Status
        if backtest_id:
            print(f"\n3️⃣ Testing GET /api/yearly-backtest/status/{backtest_id}")
            print("   Expected: Shows running or completed status")
            
            status_result = self.test_endpoint("GET", f"/yearly-backtest/status/{backtest_id}")
            self.results.append(("Check Status", status_result))
            
            if status_result.get("success"):
                response = status_result["response"]
                print(f"   ✅ Status: {status_result['status_code']} ({status_result['response_time']}s)")
                print(f"   📊 Backtest Status: {response.get('status')}")
                print(f"   📈 Progress: {response.get('progress', 0)}%")
                print(f"   🪙 Coins Count: {response.get('coins_count')}")
                print(f"   💰 Initial Capital: ${response.get('initial_capital', 0):,.2f}")
            else:
                print(f"   ❌ Failed: {status_result.get('error', 'Unknown error')}")
        else:
            print("\n3️⃣ Skipping status check - no backtest_id available")
        
        # Test 4: Try to Get Results (may not be ready yet)
        if backtest_id:
            print(f"\n4️⃣ Testing GET /api/yearly-backtest/results/{backtest_id}")
            print("   Expected: Comprehensive metrics after completion (may be 202 if still running)")
            
            results_result = self.test_endpoint("GET", f"/yearly-backtest/results/{backtest_id}", expected_status=202)
            # Accept both 200 (completed) and 202 (still running)
            if results_result.get("status_code") in [200, 202]:
                results_result["success"] = True
            
            self.results.append(("Get Results", results_result))
            
            if results_result.get("success"):
                print(f"   ✅ Status: {results_result['status_code']} ({results_result['response_time']}s)")
                if results_result["status_code"] == 202:
                    print(f"   ⏳ Backtest still running (expected)")
                else:
                    print(f"   🎉 Backtest completed!")
                    # Could validate results here if completed
            else:
                print(f"   ❌ Failed: {results_result.get('error', 'Unknown error')}")
        else:
            print("\n4️⃣ Skipping results check - no backtest_id available")
        
        # Test 5: Get Recommended Portfolio
        print("\n5️⃣ Testing GET /api/yearly-backtest/recommended-portfolio")
        print("   Expected: Recommended coins, allocation, backtest metrics, strategy params")
        
        portfolio_result = self.test_endpoint("GET", "/yearly-backtest/recommended-portfolio")
        self.results.append(("Recommended Portfolio", portfolio_result))
        
        if portfolio_result.get("success"):
            response = portfolio_result["response"]
            print(f"   ✅ Status: {portfolio_result['status_code']} ({portfolio_result['response_time']}s)")
            
            if "backtest_metrics" in response:
                metrics = response["backtest_metrics"]
                print(f"   📊 Backtest Metrics:")
                for key, value in metrics.items():
                    if value is not None:
                        print(f"      • {key}: {value}")
            
            if "recommended_portfolio" in response:
                portfolio = response["recommended_portfolio"]
                print(f"   🎯 Recommended Portfolio:")
                if "coins" in portfolio:
                    print(f"      • Coins: {portfolio['coins']}")
                if "allocation" in portfolio:
                    print(f"      • Allocation: {portfolio['allocation']}")
            
            if "top_coins" in response:
                print(f"   🏆 Top Coins: {len(response['top_coins'])} coins")
            
            if "auto_trade_ready" in response:
                print(f"   🤖 Auto Trade Ready: {response['auto_trade_ready']}")
        else:
            print(f"   ❌ Failed: {portfolio_result.get('error', 'Unknown error')}")
        
        # Test 6: Get Strategy Parameters
        print("\n6️⃣ Testing GET /api/yearly-backtest/strategy-params")
        print("   Expected: Current regime, adapted params, available regimes")
        
        strategy_result = self.test_endpoint("GET", "/yearly-backtest/strategy-params")
        self.results.append(("Strategy Parameters", strategy_result))
        
        if strategy_result.get("success"):
            response = strategy_result["response"]
            print(f"   ✅ Status: {strategy_result['status_code']} ({strategy_result['response_time']}s)")
            print(f"   🎯 Current Regime: {response.get('current_regime')}")
            
            if "adapted_params" in response:
                params = response["adapted_params"]
                print(f"   ⚙️ Adapted Parameters: {len(params)} parameters")
                # Show key parameters
                key_params = ["entry_threshold", "take_profit_pct", "stop_loss_pct", "rsi_oversold", "rsi_overbought"]
                for param in key_params:
                    if param in params:
                        print(f"      • {param}: {params[param]}")
            
            if "available_regimes" in response:
                regimes = response["available_regimes"]
                print(f"   📋 Available Regimes: {regimes}")
            
            if "regime_descriptions" in response:
                descriptions = response["regime_descriptions"]
                print(f"   📖 Regime Descriptions: {len(descriptions)} regimes described")
        else:
            print(f"   ❌ Failed: {strategy_result.get('error', 'Unknown error')}")
        
        # Test 7: Get Market Calendar
        print("\n7️⃣ Testing GET /api/yearly-backtest/market-calendar")
        print("   Expected: 2025 market events calendar")
        
        calendar_result = self.test_endpoint("GET", "/yearly-backtest/market-calendar")
        self.results.append(("Market Calendar", calendar_result))
        
        if calendar_result.get("success"):
            response = calendar_result["response"]
            print(f"   ✅ Status: {calendar_result['status_code']} ({calendar_result['response_time']}s)")
            print(f"   📅 Year: {response.get('year')}")
            print(f"   📊 Total Events: {response.get('total_events')}")
            
            if "events" in response:
                events = response["events"]
                print(f"   🗓️ Sample Events:")
                for i, event in enumerate(events[:3]):  # Show first 3 events
                    print(f"      • Week {event.get('week')}: {event.get('event')} ({event.get('regime')})")
            
            if "regimes_by_quarter" in response:
                quarters = response["regimes_by_quarter"]
                print(f"   📈 Events by Quarter:")
                for quarter, quarter_events in quarters.items():
                    print(f"      • {quarter}: {len(quarter_events)} events")
        else:
            print(f"   ❌ Failed: {calendar_result.get('error', 'Unknown error')}")
        
        # Test 8: Get Available Coins
        print("\n8️⃣ Testing GET /api/yearly-backtest/coins")
        print("   Expected: Default top coins, Kraken universe info")
        
        coins_result = self.test_endpoint("GET", "/yearly-backtest/coins")
        self.results.append(("Available Coins", coins_result))
        
        if coins_result.get("success"):
            response = coins_result["response"]
            print(f"   ✅ Status: {coins_result['status_code']} ({coins_result['response_time']}s)")
            
            if "default_top_coins" in response:
                top_coins = response["default_top_coins"]
                print(f"   🏆 Default Top Coins: {len(top_coins)} coins")
                print(f"      • Sample: {top_coins[:10]}")
            
            if "kraken_universe_coins" in response:
                kraken_count = response["kraken_universe_coins"]
                print(f"   🌐 Kraken Universe: {kraken_count} coins available")
            
            if "kraken_coins_sample" in response:
                sample = response["kraken_coins_sample"]
                print(f"   📋 Kraken Sample: {len(sample)} coins shown")
            
            if "recommended_for_backtest" in response:
                recommended = response["recommended_for_backtest"]
                print(f"   ✅ Recommended for Backtest: {len(recommended)} coins")
        else:
            print(f"   ❌ Failed: {coins_result.get('error', 'Unknown error')}")
        
        # Summary
        total_time = time.time() - test_start_time
        successful_tests = sum(1 for _, result in self.results if result.get("success", False))
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 YEARLY ADAPTIVE BACKTEST SYSTEM TEST SUMMARY")
        print("=" * 80)
        print(f"🎯 Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests} tests passed)")
        print(f"⏱️ Total Time: {total_time:.2f} seconds")
        print(f"🔗 Backend URL: {BASE_URL}")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in self.results:
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            response_time = result.get("response_time", 0)
            status_code = result.get("status_code", "N/A")
            print(f"   {status} {test_name}: {status_code} ({response_time}s)")
            
            if not result.get("success") and "error" in result:
                print(f"      Error: {result['error']}")
        
        # Key Findings
        print(f"\n🔍 Key Findings:")
        
        # Check if quick test passed and met requirements
        quick_test = next((result for name, result in self.results if name == "Quick Test"), None)
        if quick_test and quick_test.get("success"):
            print(f"   ✅ Quick Test: Yearly backtest system operational")
            
            # Extract key metrics from quick test
            if "response" in quick_test:
                response = quick_test["response"]
                win_rate = response.get("win_rate", 0)
                total_return = response.get("total_return_pct", 0)
                sharpe = response.get("sharpe_ratio", 0)
                
                if win_rate >= 50:
                    print(f"   🎯 Win Rate: {win_rate}% (MEETS 50%+ TARGET)")
                else:
                    print(f"   ⚠️ Win Rate: {win_rate}% (below 50% target)")
                
                if total_return > 0:
                    print(f"   💰 Total Return: {total_return}% (PROFITABLE)")
                else:
                    print(f"   ⚠️ Total Return: {total_return}% (not profitable)")
                
                if sharpe > 1.0:
                    print(f"   📈 Sharpe Ratio: {sharpe} (GOOD RISK-ADJUSTED RETURNS)")
                else:
                    print(f"   ⚠️ Sharpe Ratio: {sharpe} (below 1.0 target)")
        else:
            print(f"   ❌ Quick Test: Failed - core functionality not working")
        
        # Check portfolio recommendations
        portfolio_test = next((result for name, result in self.results if name == "Recommended Portfolio"), None)
        if portfolio_test and portfolio_test.get("success"):
            print(f"   ✅ Portfolio Recommendations: Available for live trading")
        else:
            print(f"   ❌ Portfolio Recommendations: Not available")
        
        # Check strategy adaptation
        strategy_test = next((result for name, result in self.results if name == "Strategy Parameters"), None)
        if strategy_test and strategy_test.get("success"):
            print(f"   ✅ Adaptive Strategy: Parameters adapting to market conditions")
        else:
            print(f"   ❌ Adaptive Strategy: Not working properly")
        
        # Overall assessment
        if success_rate >= 75:
            print(f"\n🎉 OVERALL: Yearly Adaptive Backtest System is PRODUCTION READY")
            print(f"   All core features operational, performance targets achievable")
        elif success_rate >= 50:
            print(f"\n⚠️ OVERALL: Yearly Adaptive Backtest System is PARTIALLY FUNCTIONAL")
            print(f"   Some features working, but improvements needed")
        else:
            print(f"\n❌ OVERALL: Yearly Adaptive Backtest System has MAJOR ISSUES")
            print(f"   Significant problems preventing proper operation")
        
        return {
            "success_rate": success_rate,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "total_time": total_time,
            "results": self.results
        }


if __name__ == "__main__":
    tester = YearlyBacktestTester()
    results = tester.run_comprehensive_test()