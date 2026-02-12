#!/usr/bin/env python3
"""
Multi-Year Adaptive Backtest System Testing (2020-2024)
=======================================================
Comprehensive testing of the yearly backtest system as requested in review.

Test Requirements:
1. POST /api/yearly-backtest/multi-year - Run multi-year backtest (2020-2024)
2. POST /api/yearly-backtest/quick-test?year=2022 - Test 2022 crypto winter
3. POST /api/yearly-backtest/quick-test?year=2020 - Test 2020 COVID crash and DeFi summer
4. POST /api/yearly-backtest/quick-test?year=2024 - Test 2024 Bitcoin halving year
5. GET /api/yearly-backtest/market-calendar - Verify 2020-2025 events are available
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL configuration
BASE_URL = "https://crypto-ai-fixes.preview.emergentagent.com/api"

class MultiYearBacktestTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 60  # Longer timeout for backtest operations
        self.results = []
        
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     params: Dict = None, expected_status: int = 200) -> Dict:
        """Test individual endpoint and return detailed result"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            else:
                response = self.session.request(method, url, json=data, params=params)
                
            duration = time.time() - start_time
            
            result = {
                'endpoint': endpoint,
                'method': method,
                'status': response.status_code,
                'expected': expected_status,
                'passed': response.status_code == expected_status,
                'duration': round(duration, 3),
                'response_size': len(response.content),
                'url': url
            }
            
            # Add response details for analysis
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    result['response_json'] = response.json()
                else:
                    result['response_text'] = response.text[:1000]
            except:
                result['response_text'] = response.text[:1000] if hasattr(response, 'text') else 'No response body'
            
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
                'url': url
            }

    def run_multi_year_backtest_tests(self):
        """Execute all multi-year backtest tests as specified in review request"""
        
        print("🚀 MULTI-YEAR ADAPTIVE BACKTEST SYSTEM TESTING (2020-2024)")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        # Test 1: POST /api/yearly-backtest/multi-year - Run multi-year backtest (2020-2024)
        print("\n1. 🎯 MULTI-YEAR BACKTEST (2020-2024)")
        print("   Testing: POST /api/yearly-backtest/multi-year")
        
        multi_year_data = {
            "years": [2020, 2021, 2022, 2023, 2024],
            "initial_capital": 100000
        }
        
        multi_year_result = self.test_endpoint(
            'POST', 
            '/yearly-backtest/multi-year', 
            data=multi_year_data
        )
        self.results.append(multi_year_result)
        
        if multi_year_result['passed']:
            response = multi_year_result.get('response_json', {})
            print(f"   ✅ Status: {response.get('status', 'N/A')}")
            
            # Verify requirements from review request
            if response.get('status') == 'completed':
                print("   ✅ Returns status 'completed'")
                
                # Check if all 5 years have results
                yearly_results = response.get('yearly_results', {})
                if len(yearly_results) == 5:
                    print("   ✅ All 5 years have results")
                else:
                    print(f"   ⚠️ Only {len(yearly_results)} years have results (expected 5)")
                
                # Check CAGR is positive (strategy is profitable long-term)
                cagr_pct = response.get('cagr_pct', 0)
                if cagr_pct > 0:
                    print(f"   ✅ CAGR is positive: {cagr_pct:.2f}% (strategy is profitable long-term)")
                else:
                    print(f"   ❌ CAGR is not positive: {cagr_pct:.2f}%")
                
                # Check overall win rate is around 50%
                overall_win_rate = response.get('overall_win_rate', 0)
                if 45 <= overall_win_rate <= 55:
                    print(f"   ✅ Overall win rate is around 50%: {overall_win_rate:.2f}%")
                else:
                    print(f"   ⚠️ Overall win rate: {overall_win_rate:.2f}% (expected ~50%)")
                
                # Check final capital > initial capital
                final_capital = response.get('final_capital', 0)
                initial_capital = response.get('initial_capital', 100000)
                if final_capital > initial_capital:
                    print(f"   ✅ Final capital (${final_capital:,.2f}) > Initial capital (${initial_capital:,.2f})")
                else:
                    print(f"   ❌ Final capital (${final_capital:,.2f}) <= Initial capital (${initial_capital:,.2f})")
                    
            else:
                print(f"   ⚠️ Status: {response.get('status', 'N/A')} (expected 'completed')")
        else:
            print(f"   ❌ Failed: {multi_year_result.get('status', 'ERROR')}")
        
        # Test 2: POST /api/yearly-backtest/quick-test?year=2022 - Test 2022 crypto winter
        print("\n2. 🐻 2022 CRYPTO WINTER TEST")
        print("   Testing: POST /api/yearly-backtest/quick-test?year=2022")
        
        test_2022_result = self.test_endpoint(
            'POST', 
            '/yearly-backtest/quick-test', 
            params={'year': 2022}
        )
        self.results.append(test_2022_result)
        
        if test_2022_result['passed']:
            response = test_2022_result.get('response_json', {})
            
            # Verify profit factor > 1 (profitable even in bear market)
            profit_factor = response.get('profit_factor', 0)
            if profit_factor > 1:
                print(f"   ✅ Profit factor > 1: {profit_factor:.2f} (profitable even in bear market)")
            else:
                print(f"   ❌ Profit factor <= 1: {profit_factor:.2f}")
            
            # Verify win rate > 40%
            win_rate = response.get('win_rate', 0)
            if win_rate > 40:
                print(f"   ✅ Win rate > 40%: {win_rate:.2f}%")
            else:
                print(f"   ❌ Win rate <= 40%: {win_rate:.2f}%")
            
            # Verify total return > 0 (strategy survived 2022 crash)
            total_return = response.get('total_return_pct', 0)
            if total_return > 0:
                print(f"   ✅ Total return > 0: {total_return:.2f}% (strategy survived 2022 crash)")
            else:
                print(f"   ❌ Total return <= 0: {total_return:.2f}%")
                
        else:
            print(f"   ❌ Failed: {test_2022_result.get('status', 'ERROR')}")
        
        # Test 3: POST /api/yearly-backtest/quick-test?year=2020 - Test 2020 COVID crash and DeFi summer
        print("\n3. 📈 2020 COVID CRASH AND DEFI SUMMER TEST")
        print("   Testing: POST /api/yearly-backtest/quick-test?year=2020")
        
        test_2020_result = self.test_endpoint(
            'POST', 
            '/yearly-backtest/quick-test', 
            params={'year': 2020}
        )
        self.results.append(test_2020_result)
        
        if test_2020_result['passed']:
            response = test_2020_result.get('response_json', {})
            
            # Verify strategy adapts through crash and recovery regimes
            regimes = response.get('regimes_detected', [])
            if regimes:
                print(f"   ✅ Strategy adapts through regimes: {regimes}")
            else:
                print("   ⚠️ No regime information available")
            
            # Verify win rate > 50%
            win_rate = response.get('win_rate', 0)
            if win_rate > 50:
                print(f"   ✅ Win rate > 50%: {win_rate:.2f}%")
            else:
                print(f"   ❌ Win rate <= 50%: {win_rate:.2f}%")
                
        else:
            print(f"   ❌ Failed: {test_2020_result.get('status', 'ERROR')}")
        
        # Test 4: POST /api/yearly-backtest/quick-test?year=2024 - Test 2024 Bitcoin halving year
        print("\n4. ⚡ 2024 BITCOIN HALVING YEAR TEST")
        print("   Testing: POST /api/yearly-backtest/quick-test?year=2024")
        
        test_2024_result = self.test_endpoint(
            'POST', 
            '/yearly-backtest/quick-test', 
            params={'year': 2024}
        )
        self.results.append(test_2024_result)
        
        if test_2024_result['passed']:
            response = test_2024_result.get('response_json', {})
            
            # Verify win rate > 50%
            win_rate = response.get('win_rate', 0)
            if win_rate > 50:
                print(f"   ✅ Win rate > 50%: {win_rate:.2f}%")
            else:
                print(f"   ❌ Win rate <= 50%: {win_rate:.2f}%")
            
            # Verify Sharpe ratio > 1.0
            sharpe_ratio = response.get('sharpe_ratio', 0)
            if sharpe_ratio > 1.0:
                print(f"   ✅ Sharpe ratio > 1.0: {sharpe_ratio:.2f}")
            else:
                print(f"   ❌ Sharpe ratio <= 1.0: {sharpe_ratio:.2f}")
            
            # Verify regimes include "euphoria" and "bull_strong"
            regimes = response.get('regimes_detected', [])
            has_euphoria = any('euphoria' in str(regime).lower() for regime in regimes)
            has_bull_strong = any('bull_strong' in str(regime).lower() for regime in regimes)
            
            if has_euphoria:
                print("   ✅ Regimes include 'euphoria'")
            else:
                print("   ⚠️ Regimes do not include 'euphoria'")
                
            if has_bull_strong:
                print("   ✅ Regimes include 'bull_strong'")
            else:
                print("   ⚠️ Regimes do not include 'bull_strong'")
                
        else:
            print(f"   ❌ Failed: {test_2024_result.get('status', 'ERROR')}")
        
        # Test 5: GET /api/yearly-backtest/market-calendar - Verify 2020-2025 events are available
        print("\n5. 📅 MARKET CALENDAR (2020-2025 EVENTS)")
        print("   Testing: GET /api/yearly-backtest/market-calendar")
        
        calendar_result = self.test_endpoint(
            'GET', 
            '/yearly-backtest/market-calendar'
        )
        self.results.append(calendar_result)
        
        if calendar_result['passed']:
            response = calendar_result.get('response_json', {})
            
            # Verify 2020-2025 events are available
            events = response.get('events', [])
            total_events = response.get('total_events', 0)
            
            if total_events > 0:
                print(f"   ✅ Market calendar has {total_events} events")
                
                # Check for events across different years (if available in response)
                year_coverage = response.get('year', 2025)
                print(f"   📅 Calendar covers year: {year_coverage}")
                
                # Check quarterly breakdown
                quarters = response.get('regimes_by_quarter', {})
                if quarters:
                    for quarter, quarter_events in quarters.items():
                        print(f"   📊 {quarter}: {len(quarter_events)} events")
                        
            else:
                print("   ❌ No events found in market calendar")
                
        else:
            print(f"   ❌ Failed: {calendar_result.get('status', 'ERROR')}")

    def analyze_results(self):
        """Analyze test results and generate comprehensive report"""
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 MULTI-YEAR ADAPTIVE BACKTEST SYSTEM TEST RESULTS")
        print("=" * 80)
        print(f"📈 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        # Detailed results
        print("\n🎯 DETAILED TEST RESULTS:")
        
        test_names = [
            "Multi-Year Backtest (2020-2024)",
            "2022 Crypto Winter Test", 
            "2020 COVID Crash and DeFi Summer Test",
            "2024 Bitcoin Halving Year Test",
            "Market Calendar (2020-2025 Events)"
        ]
        
        failed_tests = []
        
        for i, result in enumerate(self.results):
            test_name = test_names[i] if i < len(test_names) else f"Test {i+1}"
            status_icon = "✅" if result['passed'] else "❌"
            
            print(f"{status_icon} {test_name}: {result['status']} (expected {result['expected']}) - {result['duration']}s")
            
            if not result['passed']:
                failed_tests.append({
                    'name': test_name,
                    'result': result
                })
                if 'error' in result:
                    print(f"   Error: {result['error']}")
        
        # Performance stats
        if self.results:
            avg_duration = sum(r.get('duration', 0) for r in self.results) / len(self.results)
            print(f"\n⚡ PERFORMANCE: Average response time {avg_duration:.2f}s")
        
        # Key metrics summary
        print(f"\n📋 KEY METRICS VERIFICATION:")
        
        # Extract key metrics from multi-year backtest if available
        if self.results and self.results[0]['passed']:
            multi_year_response = self.results[0].get('response_json', {})
            
            if multi_year_response.get('status') == 'completed':
                print(f"   📊 CAGR: {multi_year_response.get('cagr_pct', 'N/A')}%")
                print(f"   📊 Overall Win Rate: {multi_year_response.get('overall_win_rate', 'N/A')}%")
                print(f"   📊 Final Capital: ${multi_year_response.get('final_capital', 'N/A'):,.2f}")
                print(f"   📊 Initial Capital: ${multi_year_response.get('initial_capital', 'N/A'):,.2f}")
        
        # Extract 2022 metrics if available
        if len(self.results) > 1 and self.results[1]['passed']:
            test_2022_response = self.results[1].get('response_json', {})
            print(f"   🐻 2022 Profit Factor: {test_2022_response.get('profit_factor', 'N/A')}")
            print(f"   🐻 2022 Win Rate: {test_2022_response.get('win_rate', 'N/A')}%")
            print(f"   🐻 2022 Total Return: {test_2022_response.get('total_return_pct', 'N/A')}%")
        
        # Extract 2024 metrics if available
        if len(self.results) > 3 and self.results[3]['passed']:
            test_2024_response = self.results[3].get('response_json', {})
            print(f"   ⚡ 2024 Win Rate: {test_2024_response.get('win_rate', 'N/A')}%")
            print(f"   ⚡ 2024 Sharpe Ratio: {test_2024_response.get('sharpe_ratio', 'N/A')}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'failed_tests': failed_tests,
            'results': self.results
        }

def main():
    """Run Multi-Year Adaptive Backtest System testing"""
    tester = MultiYearBacktestTester()
    
    print("🎉 MULTI-YEAR ADAPTIVE BACKTEST SYSTEM TESTING")
    print("=" * 80)
    print("Testing the Multi-Year Adaptive Backtest System (2020-2024)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run all tests
    tester.run_multi_year_backtest_tests()
    
    # Analyze and report
    results = tester.analyze_results()
    
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"✅ SUCCESS RATE: {results['success_rate']:.1f}% ({results['passed_tests']}/{results['total_tests']})")
    
    if results['success_rate'] >= 80:
        print("🎉 EXCELLENT - Multi-Year Adaptive Backtest System is working well!")
    elif results['success_rate'] >= 60:
        print("👍 GOOD - System has minor issues but core functionality works")
    else:
        print("⚠️ NEEDS ATTENTION - Multiple issues found with the backtest system")
    
    return results

if __name__ == "__main__":
    main()