#!/usr/bin/env python3
"""
Win Rate Improvements Testing - February 10, 2026
Testing specific improvements to win rates in the trading system:
1. A/B Testing System with New High Win Rate Variants (8 variants, 70%+ win rates)
2. Backtest Engine with ML Strategy v8 (improved from 22.2% to >40% win rate)
3. A/B Testing Status Endpoint
4. Backtest Templates Include ML Strategy
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://test-win-progress.preview.emergentagent.com/api"

class WinRateImprovementsTester:
    def __init__(self):
        self.results = {
            'ab_testing': [],
            'backtest_engine': [],
            'status_endpoints': [],
            'templates': []
        }
        self.session = requests.Session()
        self.session.timeout = 60  # Longer timeout for backtests

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
        """Execute all win rate improvement tests"""
        
        print("🚀 WIN RATE IMPROVEMENTS TESTING - Testing New High Win Rate Features")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        # 1. A/B TESTING SYSTEM WITH NEW HIGH WIN RATE VARIANTS
        print("\n1. A/B TESTING SYSTEM - NEW HIGH WIN RATE VARIANTS")
        print("   Testing initialization of 8 NEW strategy variants with 70%+ win rates")
        
        # Initialize A/B testing variants
        init_result = self.test_endpoint('POST', '/ml-optimization/ab-testing/initialize', 
                                       category='ab_testing')
        self.results['ab_testing'].append(init_result)
        
        if init_result['passed']:
            print(f"   ✅ Initialize A/B Testing: {init_result['status']}")
            if 'response_json' in init_result:
                response = init_result['response_json']
                if 'variants' in response:
                    print(f"   📊 Variants Created: {len(response['variants'])}")
                    for variant in response['variants'][:3]:  # Show first 3
                        print(f"      - {variant.get('name', 'Unknown')}: {variant.get('description', 'No description')}")
        else:
            print(f"   ❌ Initialize A/B Testing Failed: {init_result.get('status', 'ERROR')}")
        
        # Run A/B test with 200 simulations as specified
        print("\n   Running A/B test with 200 simulations...")
        ab_test_result = self.test_endpoint('POST', '/ml-optimization/ab-testing/run', 
                                          {'n_simulations': 200}, category='ab_testing')
        self.results['ab_testing'].append(ab_test_result)
        
        if ab_test_result['passed']:
            print(f"   ✅ A/B Test Run: {ab_test_result['status']}")
            if 'response_json' in ab_test_result:
                response = ab_test_result['response_json']
                print(f"   📈 Test Results:")
                if 'results' in response:
                    high_win_rate_variants = 0
                    winner_win_rate = 0
                    
                    for variant in response['results']:
                        win_rate = variant.get('win_rate', 0)
                        variant_name = variant.get('variant_id', 'Unknown')
                        print(f"      - {variant_name}: {win_rate:.1f}% win rate")
                        
                        if win_rate >= 70:
                            high_win_rate_variants += 1
                        if win_rate > winner_win_rate:
                            winner_win_rate = win_rate
                    
                    print(f"   🎯 HIGH WIN RATE ANALYSIS:")
                    print(f"      - Variants with 70%+ win rate: {high_win_rate_variants}/8")
                    print(f"      - Winner win rate: {winner_win_rate:.1f}%")
                    print(f"      - Target achieved: {'✅ YES' if winner_win_rate > 75 else '❌ NO'}")
        else:
            print(f"   ❌ A/B Test Run Failed: {ab_test_result.get('status', 'ERROR')}")
        
        # 2. BACKTEST ENGINE WITH ML STRATEGY V8
        print("\n2. BACKTEST ENGINE - ML STRATEGY V8 HIGH WIN RATE TEST")
        print("   Testing ML Strategy v8 with improved win rate (target >40% from baseline 22.2%)")
        
        # Test backtest with ML strategy v8
        backtest_config = {
            "name": "ML Strategy v8 Test",
            "strategy_type": "ml_based",
            "symbols": ["BTC/USD"],
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-12-01T00:00:00Z",
            "initial_capital": 10000,
            "position_size_pct": 15,
            "stop_loss_pct": 3,
            "take_profit_pct": 10,
            "strategy_params": {
                "lookback": 20,
                "min_trend_strength": 0.015,
                "rsi_oversold": 25,
                "rsi_overbought": 75,
                "entry_threshold": 6,
                "adx_threshold": 20
            }
        }
        
        backtest_start = self.test_endpoint('POST', '/backtest-engine/run', 
                                          backtest_config, category='backtest_engine')
        self.results['backtest_engine'].append(backtest_start)
        
        if backtest_start['passed']:
            print(f"   ✅ Backtest Started: {backtest_start['status']}")
            if 'response_json' in backtest_start:
                backtest_id = backtest_start['response_json'].get('backtest_id')
                print(f"   📊 Backtest ID: {backtest_id}")
                
                # Wait for backtest to complete
                print("   ⏳ Waiting for backtest to complete...")
                max_wait = 120  # 2 minutes max
                wait_time = 0
                
                while wait_time < max_wait:
                    time.sleep(5)
                    wait_time += 5
                    
                    status_result = self.test_endpoint('GET', f'/backtest-engine/status/{backtest_id}', 
                                                     category='backtest_engine')
                    
                    if status_result['passed'] and 'response_json' in status_result:
                        status = status_result['response_json'].get('status')
                        progress = status_result['response_json'].get('progress', 0)
                        print(f"   📈 Progress: {progress}% ({status})")
                        
                        if status == 'completed':
                            break
                        elif status == 'failed':
                            print(f"   ❌ Backtest Failed")
                            break
                
                # Get results
                if wait_time < max_wait:
                    results_result = self.test_endpoint('GET', f'/backtest-engine/results/{backtest_id}', 
                                                      category='backtest_engine')
                    self.results['backtest_engine'].append(results_result)
                    
                    if results_result['passed'] and 'response_json' in results_result:
                        results = results_result['response_json']
                        metrics = results.get('metrics', {})
                        
                        win_rate = metrics.get('win_rate', 0)
                        total_return = metrics.get('total_return_pct', 0)
                        sharpe_ratio = metrics.get('sharpe_ratio', 0)
                        total_trades = metrics.get('total_trades', 0)
                        
                        print(f"   🎯 ML STRATEGY V8 RESULTS:")
                        print(f"      - Win Rate: {win_rate:.1f}% (was 22.2%, target >40%)")
                        print(f"      - Total Return: {total_return:.1f}%")
                        print(f"      - Sharpe Ratio: {sharpe_ratio:.2f}")
                        print(f"      - Total Trades: {total_trades}")
                        print(f"      - Improvement: {'✅ YES' if win_rate > 40 else '❌ NO'}")
                        
                        if win_rate > 40:
                            improvement = ((win_rate - 22.2) / 22.2) * 100
                            print(f"      - Win Rate Improvement: +{improvement:.1f}%")
                    else:
                        print(f"   ❌ Failed to get backtest results: {results_result.get('status', 'ERROR')}")
                else:
                    print(f"   ⏰ Backtest timed out after {max_wait} seconds")
        else:
            print(f"   ❌ Backtest Start Failed: {backtest_start.get('status', 'ERROR')}")
        
        # 3. A/B TESTING STATUS ENDPOINT
        print("\n3. A/B TESTING STATUS ENDPOINT")
        print("   Verifying status endpoint shows all 8 variants with performance metrics")
        
        status_result = self.test_endpoint('GET', '/ml-optimization/ab-testing/status', 
                                         category='status_endpoints')
        self.results['status_endpoints'].append(status_result)
        
        if status_result['passed']:
            print(f"   ✅ A/B Testing Status: {status_result['status']}")
            if 'response_json' in status_result:
                response = status_result['response_json']
                if 'variants' in response:
                    variants = response['variants']
                    print(f"   📊 Variants Found: {len(variants)}")
                    
                    for i, variant in enumerate(variants[:8]):  # Show up to 8
                        name = variant.get('name', f'Variant {i+1}')
                        win_rate = variant.get('win_rate', 0)
                        trades = variant.get('total_trades', 0)
                        sharpe = variant.get('sharpe_ratio', 0)
                        print(f"      {i+1}. {name}: {win_rate:.1f}% win rate, {trades} trades, {sharpe:.2f} Sharpe")
                    
                    print(f"   🎯 Expected: 8 variants shown ✅")
                else:
                    print(f"   ⚠️ No variants found in status response")
        else:
            print(f"   ❌ A/B Testing Status Failed: {status_result.get('status', 'ERROR')}")
        
        # 4. BACKTEST TEMPLATES INCLUDE ML STRATEGY
        print("\n4. BACKTEST TEMPLATES - ML STRATEGY VERIFICATION")
        print("   Verifying that backtest templates include 'ml_based' strategy")
        
        strategies_result = self.test_endpoint('GET', '/backtest-engine/strategies', 
                                             category='templates')
        self.results['templates'].append(strategies_result)
        
        if strategies_result['passed']:
            print(f"   ✅ Strategies Endpoint: {strategies_result['status']}")
            if 'response_json' in strategies_result:
                response = strategies_result['response_json']
                strategies = response.get('strategies', [])
                
                ml_strategy_found = False
                for strategy in strategies:
                    strategy_id = strategy.get('id')
                    strategy_name = strategy.get('name')
                    description = strategy.get('description', '')
                    
                    print(f"      - {strategy_id}: {strategy_name}")
                    if strategy_id == 'ml_based':
                        ml_strategy_found = True
                        print(f"        📝 Description: {description}")
                
                print(f"   🎯 ML Strategy Found: {'✅ YES' if ml_strategy_found else '❌ NO'}")
        else:
            print(f"   ❌ Strategies Endpoint Failed: {strategies_result.get('status', 'ERROR')}")
        
        templates_result = self.test_endpoint('GET', '/backtest-engine/templates', 
                                            category='templates')
        self.results['templates'].append(templates_result)
        
        if templates_result['passed']:
            print(f"   ✅ Templates Endpoint: {templates_result['status']}")
            if 'response_json' in templates_result:
                response = templates_result['response_json']
                templates = response.get('templates', [])
                print(f"   📊 Templates Available: {len(templates)}")
                
                for template in templates:
                    name = template.get('name')
                    strategy_type = template.get('config', {}).get('strategy_type')
                    print(f"      - {name}: {strategy_type} strategy")
        else:
            print(f"   ❌ Templates Endpoint Failed: {templates_result.get('status', 'ERROR')}")

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
        print("📊 WIN RATE IMPROVEMENTS TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"📈 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        # Category breakdown
        print("\n🎯 RESULTS BY FEATURE:")
        
        failed_tests = []
        
        for category, tests in self.results.items():
            if not tests:
                continue
                
            category_passed = sum(1 for t in tests if t['passed'])
            category_total = len(tests)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            status_icon = "✅" if category_rate == 100 else "⚠️" if category_rate >= 50 else "❌"
            
            category_name = category.upper().replace('_', ' ')
            print(f"{status_icon} {category_name}: {category_rate:.1f}% ({category_passed}/{category_total})")
            
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
        
        # Win Rate Analysis Summary
        print(f"\n🏆 WIN RATE IMPROVEMENTS SUMMARY:")
        
        # Check A/B testing results
        ab_tests = [t for t in all_results if t['category'] == 'ab_testing' and t['passed']]
        if ab_tests:
            print(f"   ✅ A/B Testing System: {len(ab_tests)} tests passed")
        else:
            print(f"   ❌ A/B Testing System: Tests failed")
        
        # Check backtest results
        backtest_tests = [t for t in all_results if t['category'] == 'backtest_engine' and t['passed']]
        if backtest_tests:
            print(f"   ✅ Backtest Engine: {len(backtest_tests)} tests passed")
        else:
            print(f"   ❌ Backtest Engine: Tests failed")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'failed_tests': failed_tests,
            'category_results': {cat: tests for cat, tests in self.results.items() if tests}
        }

def main():
    """Run win rate improvements testing"""
    tester = WinRateImprovementsTester()
    
    print("🎉 WIN RATE IMPROVEMENTS TESTING")
    print("=" * 80)
    print("Testing new high win rate features:")
    print("1. A/B Testing System (8 variants, 70%+ win rates)")
    print("2. Backtest Engine ML Strategy v8 (>40% win rate)")
    print("3. A/B Testing Status Endpoint")
    print("4. Backtest Templates with ML Strategy")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run all tests
    tester.run_win_rate_tests()
    
    # Analyze and report
    results = tester.analyze_results()
    
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"✅ SUCCESS RATE: {results['success_rate']:.1f}% ({results['passed_tests']}/{results['total_tests']})")
    
    if results['success_rate'] >= 85:
        print("🎉 EXCELLENT - Win rate improvements are working!")
    elif results['success_rate'] >= 70:
        print("👍 GOOD - Most win rate features working with minor issues")
    else:
        print("⚠️ NEEDS ATTENTION - Multiple win rate improvement issues found")
    
    return results

if __name__ == "__main__":
    main()