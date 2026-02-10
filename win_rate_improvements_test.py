#!/usr/bin/env python3
"""
Win Rate Improvements Testing - February 10, 2026
Testing A/B Testing System, ML Strategy Backtesting, and Overfitting Detection
Focus on verifying high win rates (70%+) and positive Sharpe ratios
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Backend URL configuration
BASE_URL = "https://trade-sentinel-27.preview.emergentagent.com/api"

class WinRateImprovementsTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 60  # Longer timeout for ML operations
        self.results = {
            'ab_testing': [],
            'backtest_engine': [],
            'overfitting_detection': []
        }

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, category: str = 'unknown') -> Dict:
        """Test individual endpoint and return result"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                response = self.session.request(method, url, json=data)
                
            duration = time.time() - start_time
            
            result = {
                'endpoint': endpoint,
                'method': method,
                'status': response.status_code,
                'expected': expected_status,
                'passed': response.status_code == expected_status,
                'duration': round(duration, 3),
                'response_size': len(response.content),
                'category': category
            }
            
            # Add response details for analysis
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    result['response_json'] = response.json()
                else:
                    result['response_text'] = response.text[:500]
            except:
                result['response_text'] = response.text[:500] if hasattr(response, 'text') else 'No response body'
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'endpoint': endpoint,
                'method': method,
                'status': 'ERROR',
                'expected': expected_status,
                'passed': False,
                'duration': round(duration, 3),
                'error': str(e),
                'category': category
            }

    def run_win_rate_tests(self):
        """Execute all Win Rate Improvements tests"""
        
        print("🚀 WIN RATE IMPROVEMENTS TESTING - A/B Testing & ML Strategy")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        # 1. A/B TESTING SYSTEM
        print("\n1. A/B TESTING SYSTEM - Testing Strategy Variants")
        
        # Initialize variants first
        print("   Initializing strategy variants...")
        init_result = self.test_endpoint('POST', '/ml-optimization/ab-testing/initialize', 
                                       category='ab_testing')
        self.results['ab_testing'].append(init_result)
        
        if init_result['passed']:
            print("   ✅ Variants initialized successfully")
        else:
            print(f"   ❌ Failed to initialize variants: {init_result.get('status', 'Unknown error')}")
        
        # Run A/B test with n_simulations=200 as requested
        print("   Running A/B test simulation with 200 iterations...")
        ab_test_result = self.test_endpoint('POST', '/ml-optimization/ab-testing/run', 
                                          {'n_simulations': 200}, category='ab_testing')
        self.results['ab_testing'].append(ab_test_result)
        
        if ab_test_result['passed']:
            response_data = ab_test_result.get('response_json', {})
            winner = response_data.get('winner', {})
            results = response_data.get('results', [])
            
            print(f"   ✅ A/B test completed with {len(results)} variants")
            if winner:
                win_rate = winner.get('win_rate', 0)
                sharpe = winner.get('sharpe_ratio', 0)
                print(f"   🏆 Winner: {winner.get('name', 'Unknown')} - Win Rate: {win_rate}% | Sharpe: {sharpe}")
                
                # Check if winner achieves target win rate (70%+)
                if win_rate >= 70:
                    print(f"   🎯 EXCELLENT: Winner achieves {win_rate}% win rate (target: 70%+)")
                else:
                    print(f"   ⚠️  Winner win rate {win_rate}% below target 70%")
            
            # Verify all 8 strategy variants are present
            expected_variants = [
                "Ultra Conservative", "RSI Extreme Hunter", "Quality Momentum", 
                "Trend Precision", "Smart Breakout", "Momentum Precision", 
                "Mean Reversion Pro", "Divergence Master"
            ]
            
            found_variants = [r.get('name', '') for r in results]
            print(f"   📊 Strategy variants found: {len(found_variants)}/8")
            
            for variant_name in expected_variants:
                if variant_name in found_variants:
                    variant_data = next((r for r in results if r.get('name') == variant_name), {})
                    win_rate = variant_data.get('win_rate', 0)
                    sharpe = variant_data.get('sharpe_ratio', 0)
                    print(f"      ✅ {variant_name}: {win_rate}% win rate, {sharpe} Sharpe")
                else:
                    print(f"      ❌ Missing variant: {variant_name}")
        else:
            print(f"   ❌ A/B test failed: {ab_test_result.get('status', 'Unknown error')}")
        
        # Get A/B testing status
        print("   Checking A/B testing status...")
        status_result = self.test_endpoint('GET', '/ml-optimization/ab-testing/status', 
                                         category='ab_testing')
        self.results['ab_testing'].append(status_result)
        
        if status_result['passed']:
            status_data = status_result.get('response_json', {})
            variants = status_data.get('variants', [])
            print(f"   ✅ Status retrieved: {len(variants)} variants with metrics")
            
            # Show top performers
            for i, variant in enumerate(variants[:3]):
                name = variant.get('name', 'Unknown')
                win_rate = variant.get('win_rate', 0)
                sharpe = variant.get('sharpe_ratio', 0)
                print(f"      #{i+1} {name}: {win_rate}% win rate, {sharpe} Sharpe")
        else:
            print(f"   ❌ Status check failed: {status_result.get('status', 'Unknown error')}")
        
        # 2. BACKTEST ENGINE WITH ML STRATEGY
        print("\n2. BACKTEST ENGINE - ML Strategy Testing")
        
        # Get available strategies first
        print("   Checking available strategies...")
        strategies_result = self.test_endpoint('GET', '/backtest-engine/strategies', 
                                             category='backtest_engine')
        self.results['backtest_engine'].append(strategies_result)
        
        if strategies_result['passed']:
            strategies_data = strategies_result.get('response_json', {})
            strategies = strategies_data.get('strategies', [])
            ml_strategy_found = any(s.get('id') == 'ml_based' for s in strategies)
            
            print(f"   ✅ Found {len(strategies)} strategies")
            if ml_strategy_found:
                print("   ✅ ML-based strategy available in templates")
            else:
                print("   ⚠️  ML-based strategy not found in templates")
            
            # Show available strategies
            for strategy in strategies:
                print(f"      • {strategy.get('name', 'Unknown')}: {strategy.get('description', 'No description')}")
        else:
            print(f"   ❌ Failed to get strategies: {strategies_result.get('status', 'Unknown error')}")
        
        # Run ML strategy backtest
        print("   Running ML strategy backtest...")
        
        # Calculate date range (last 90 days for realistic test)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        backtest_config = {
            "name": "ML Strategy Win Rate Test",
            "strategy_type": "ml_strategy",
            "symbols": ["BTC/USD", "ETH/USD"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "initial_capital": 10000,
            "position_size_pct": 15,
            "stop_loss_pct": 3,
            "take_profit_pct": 12,
            "strategy_params": {
                "lookback": 20,
                "min_trend_strength": 0.02,
                "entry_threshold": 8,
                "rsi_oversold": 20,
                "rsi_overbought": 80
            }
        }
        
        backtest_result = self.test_endpoint('POST', '/backtest-engine/run', 
                                           backtest_config, category='backtest_engine')
        self.results['backtest_engine'].append(backtest_result)
        
        if backtest_result['passed']:
            backtest_data = backtest_result.get('response_json', {})
            backtest_id = backtest_data.get('backtest_id')
            print(f"   ✅ Backtest started: {backtest_id}")
            
            # Wait for backtest to complete and check results
            print("   Waiting for backtest completion...")
            max_wait = 120  # 2 minutes max wait
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(10)
                wait_time += 10
                
                status_check = self.test_endpoint('GET', f'/backtest-engine/status/{backtest_id}', 
                                                category='backtest_engine')
                
                if status_check['passed']:
                    status_info = status_check.get('response_json', {})
                    status = status_info.get('status', 'unknown')
                    progress = status_info.get('progress', 0)
                    
                    print(f"      Status: {status} ({progress}%)")
                    
                    if status == 'completed':
                        # Get results
                        results_check = self.test_endpoint('GET', f'/backtest-engine/results/{backtest_id}', 
                                                         category='backtest_engine')
                        self.results['backtest_engine'].append(results_check)
                        
                        if results_check['passed']:
                            results_data = results_check.get('response_json', {})
                            metrics = results_data.get('metrics', {})
                            
                            win_rate = metrics.get('win_rate', 0)
                            sharpe_ratio = metrics.get('sharpe_ratio', 0)
                            total_return = metrics.get('total_return_pct', 0)
                            total_trades = metrics.get('total_trades', 0)
                            
                            print(f"   🎯 BACKTEST RESULTS:")
                            print(f"      Win Rate: {win_rate}% (target: 40%+ improvement from ~22% baseline)")
                            print(f"      Sharpe Ratio: {sharpe_ratio}")
                            print(f"      Total Return: {total_return}%")
                            print(f"      Total Trades: {total_trades}")
                            
                            # Check if win rate shows improvement
                            baseline_win_rate = 22  # Mentioned in review request
                            improvement = ((win_rate - baseline_win_rate) / baseline_win_rate) * 100
                            
                            if improvement >= 40:
                                print(f"   ✅ EXCELLENT: {improvement:.1f}% improvement over baseline (target: 40%+)")
                            elif win_rate > baseline_win_rate:
                                print(f"   ⚠️  {improvement:.1f}% improvement (below 40% target)")
                            else:
                                print(f"   ❌ Win rate {win_rate}% not improved from baseline {baseline_win_rate}%")
                        
                        break
                    elif status == 'failed':
                        print(f"   ❌ Backtest failed")
                        break
                else:
                    print(f"      ❌ Status check failed")
                    break
            
            if wait_time >= max_wait:
                print(f"   ⚠️  Backtest timeout after {max_wait} seconds")
        else:
            print(f"   ❌ Failed to start backtest: {backtest_result.get('status', 'Unknown error')}")
        
        # 3. OVERFITTING DETECTION
        print("\n3. OVERFITTING DETECTION")
        
        # Test overfitting detection with provided parameters
        print("   Testing overfitting detection...")
        
        # Try the direct approach with train_accuracy and validation_accuracy as specified in review
        simple_overfitting_request = {
            "train_accuracy": 0.85,
            "validation_accuracy": 0.55
        }
        
        overfitting_result = self.test_endpoint('POST', '/ml-optimization/overfitting/detect', 
                                              simple_overfitting_request, category='overfitting_detection')
        self.results['overfitting_detection'].append(overfitting_result)
        
        if overfitting_result['passed']:
            overfitting_data = overfitting_result.get('response_json', {})
            is_overfit = overfitting_data.get('is_overfit', False)
            overfit_score = overfitting_data.get('overfit_score', 0)
            
            print(f"   ✅ Overfitting detection completed")
            print(f"      Train Accuracy: 85%")
            print(f"      Validation Accuracy: 55%")
            print(f"      Overfitting Detected: {is_overfit}")
            print(f"      Overfit Score: {overfit_score}")
            
            if is_overfit:
                print("   ✅ CORRECT: Overfitting scenario properly detected (85% vs 55%)")
            else:
                print("   ⚠️  Expected overfitting detection for 85% vs 55% accuracy gap")
        else:
            # Try the more complex endpoint structure that the service expects
            overfitting_request = {
                "variant_id": "test_variant",
                "train_results": {
                    "win_rate": 85,
                    "sharpe_ratio": 2.5
                },
                "validation_results": {
                    "win_rate": 55,
                    "sharpe_ratio": 0.8
                }
            }
            
            overfitting_result2 = self.test_endpoint('POST', '/ml-optimization/overfitting/detect', 
                                                   overfitting_request, category='overfitting_detection')
            self.results['overfitting_detection'].append(overfitting_result2)
            
            if overfitting_result2['passed']:
                overfitting_data = overfitting_result2.get('response_json', {})
                is_overfit = overfitting_data.get('is_overfit', False)
                
                print(f"   ✅ Overfitting detection completed (complex format)")
                print(f"      Overfitting Detected: {is_overfit}")
                
                if is_overfit:
                    print("   ✅ CORRECT: Overfitting scenario properly detected")
                else:
                    print("   ⚠️  Expected overfitting detection for large accuracy gap")
            else:
                print(f"   ❌ Overfitting detection failed: {overfitting_result.get('status', 'Unknown error')}")

    def analyze_results(self):
        """Analyze test results and generate comprehensive report"""
        
        # Calculate totals
        all_results = []
        for category_results in self.results.values():
            all_results.extend(category_results)
        
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r['passed'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 WIN RATE IMPROVEMENTS TEST RESULTS")
        print("=" * 80)
        print(f"📈 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        # Category breakdown
        print("\n🎯 RESULTS BY CATEGORY:")
        
        failed_tests = []
        
        for category, tests in self.results.items():
            if not tests:
                continue
                
            category_passed = sum(1 for t in tests if t['passed'])
            category_total = len(tests)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            status_icon = "✅" if category_rate == 100 else "⚠️" if category_rate >= 50 else "❌"
            
            print(f"{status_icon} {category.upper().replace('_', ' ')}: {category_rate:.1f}% ({category_passed}/{category_total})")
            
            # Track failed tests
            for test in tests:
                if not test['passed']:
                    failed_tests.append(test)
        
        # Failed test details
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['method']} {test['endpoint']} → {test['status']} (expected {test['expected']})")
                if 'error' in test:
                    print(f"     Error: {test['error']}")
        
        # Performance stats
        avg_duration = sum(t.get('duration', 0) for t in all_results) / len(all_results) if all_results else 0
        print(f"\n⚡ PERFORMANCE: Average response time {avg_duration:.2f}s")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'failed_tests': failed_tests,
            'category_results': {cat: tests for cat, tests in self.results.items() if tests}
        }

def main():
    """Run Win Rate Improvements testing"""
    tester = WinRateImprovementsTester()
    
    print("🎯 WIN RATE IMPROVEMENTS TESTING")
    print("=" * 80)
    print("Testing A/B Testing System, ML Strategy Backtesting, and Overfitting Detection")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run all tests
    tester.run_win_rate_tests()
    
    # Analyze and report
    results = tester.analyze_results()
    
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"✅ SUCCESS RATE: {results['success_rate']:.1f}% ({results['passed_tests']}/{results['total_tests']})")
    
    if results['success_rate'] >= 85:
        print("🎉 EXCELLENT - Win Rate Improvements features working perfectly!")
    elif results['success_rate'] >= 70:
        print("👍 GOOD - Win Rate Improvements mostly functional with minor issues")
    else:
        print("⚠️ NEEDS ATTENTION - Multiple issues found in Win Rate Improvements")
    
    return results

if __name__ == "__main__":
    main()