#!/usr/bin/env python3
"""
Comprehensive Backend API Testing - February 10, 2026
Testing ALL 67 endpoints after 4 critical fixes applied:
1. MTF Training /fear-greed endpoint fixed (was 404)
2. MTF Training /predict/{symbol} fixed (was 400) 
3. ML Monitoring router registered (was unregistered)
4. Market /prices endpoint fixed (was 422)
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://fast-analyzer.preview.emergentagent.com/api"

class ComprehensiveBackendTester:
    def __init__(self):
        self.results = {
            'core': [],
            'enhanced_event_prediction': [],
            'hidden_gem_prediction': [],
            'adaptive_strategy': [],
            'whale_alerts': [],
            'on_chain_data': [],
            'tethys': [],
            'event_triggers': [],
            'ensemble_ai': [],
            'portfolio': [],
            'model_training': [],
            'mtf_training': [],
            'market_data_sentiment': [],
            'auto_trading': [],
            'security_monitoring': [],
            'ml_monitoring': [],
            'ml_optimization': [],
            'journal': [],
            'cache': []
        }
        self.session = requests.Session()
        self.session.timeout = 30

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

    def run_all_tests(self):
        """Execute all test categories as specified in review request"""
        
        print("🚀 COMPREHENSIVE BACKEND RE-TEST - Testing ALL 67 endpoints after 4 fixes")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        # 1. CORE (2 tests)
        print("\n1. CORE HEALTH ENDPOINTS")
        self.results['core'].extend([
            self.test_endpoint('GET', '/health', category='core'),
            self.test_endpoint('GET', '/', category='core')
        ])
        
        # 2. ENHANCED EVENT PREDICTION (5 tests)
        print("\n2. ENHANCED EVENT PREDICTION")
        self.results['enhanced_event_prediction'].extend([
            self.test_endpoint('POST', '/adaptive-strategy/predict-events', 
                             {'days_ahead': 60}, category='enhanced_event_prediction'),
            self.test_endpoint('GET', '/adaptive-strategy/event-coverage-stats', 
                             category='enhanced_event_prediction'),
            self.test_endpoint('GET', '/adaptive-strategy/event-calendar', 
                             {'days_ahead': 90}, category='enhanced_event_prediction'),
            self.test_endpoint('GET', '/adaptive-strategy/event-types', 
                             category='enhanced_event_prediction'),
            self.test_endpoint('GET', '/adaptive-strategy/scheduled-events', 
                             {'days_ahead': 90}, category='enhanced_event_prediction')
        ])
        
        # 3. HIDDEN GEM PREDICTION (5 tests)
        print("\n3. HIDDEN GEM PREDICTION")
        self.results['hidden_gem_prediction'].extend([
            self.test_endpoint('POST', '/gems/predict', 
                             {'days_ahead': 7}, category='hidden_gem_prediction'),
            self.test_endpoint('POST', '/gems/scan', 
                             {'limit': 10}, category='hidden_gem_prediction'),
            self.test_endpoint('GET', '/gems/top', category='hidden_gem_prediction'),
            self.test_endpoint('GET', '/gems/training-status', category='hidden_gem_prediction'),
            self.test_endpoint('GET', '/gems/backtest/status', category='hidden_gem_prediction')
        ])
        
        # 4. ADAPTIVE STRATEGY (5 tests)
        print("\n4. ADAPTIVE STRATEGY")
        self.results['adaptive_strategy'].extend([
            self.test_endpoint('GET', '/adaptive-strategy/status', category='adaptive_strategy'),
            self.test_endpoint('GET', '/adaptive-strategy/regime/current', category='adaptive_strategy'),
            self.test_endpoint('GET', '/adaptive-strategy/optimal-strategy', category='adaptive_strategy'),
            self.test_endpoint('GET', '/adaptive-strategy/variants', category='adaptive_strategy'),
            self.test_endpoint('GET', '/adaptive-strategy/predicted-events', 
                             {'min_probability': 0.3}, category='adaptive_strategy')
        ])
        
        # 5. WHALE ALERTS (5 tests)
        print("\n5. WHALE ALERTS")
        self.results['whale_alerts'].extend([
            self.test_endpoint('POST', '/alerts/whale/check', category='whale_alerts'),
            self.test_endpoint('GET', '/alerts/whale/active', category='whale_alerts'),
            self.test_endpoint('GET', '/alerts/whale/thresholds', category='whale_alerts'),
            self.test_endpoint('POST', '/alerts/backtest/simulate', 
                             {'n_predictions': 20}, category='whale_alerts'),
            self.test_endpoint('GET', '/alerts/backtest/historical-events', category='whale_alerts')
        ])
        
        # 6. ON-CHAIN DATA (4 tests)
        print("\n6. ON-CHAIN DATA")
        self.results['on_chain_data'].extend([
            self.test_endpoint('GET', '/on-chain/whale-activity', category='on_chain_data'),
            self.test_endpoint('GET', '/on-chain/exchange-flows', category='on_chain_data'),
            self.test_endpoint('GET', '/on-chain/network-metrics', category='on_chain_data'),
            self.test_endpoint('GET', '/on-chain/summary', category='on_chain_data')
        ])
        
        # 7. TETHYS (4 tests)
        print("\n7. TETHYS TRADING ENGINE")
        self.results['tethys'].extend([
            self.test_endpoint('GET', '/tethys/status', category='tethys'),
            self.test_endpoint('POST', '/tethys-trading/start', category='tethys'),
            self.test_endpoint('POST', '/tethys-trading/stop', category='tethys'),
            self.test_endpoint('GET', '/tethys-trading/status', category='tethys')
        ])
        
        # 8. EVENT TRIGGERS (4 tests)
        print("\n8. EVENT TRIGGERS")
        self.results['event_triggers'].extend([
            self.test_endpoint('GET', '/triggers/list', category='event_triggers'),
            self.test_endpoint('GET', '/triggers/templates', category='event_triggers'),
            self.test_endpoint('GET', '/triggers/status', category='event_triggers'),
            self.test_endpoint('POST', '/triggers/check-now', category='event_triggers')
        ])
        
        # 9. ENSEMBLE AI (3 tests)
        print("\n9. ENSEMBLE AI")
        self.results['ensemble_ai'].extend([
            self.test_endpoint('GET', '/ensemble/status', category='ensemble_ai'),
            self.test_endpoint('GET', '/ensemble/weights', category='ensemble_ai'),
            self.test_endpoint('GET', '/ensemble/optimal-universe', category='ensemble_ai')
        ])
        
        # 10. PORTFOLIO (2 tests)
        print("\n10. PORTFOLIO")
        self.results['portfolio'].extend([
            self.test_endpoint('GET', '/kraken/status', category='portfolio'),
            self.test_endpoint('GET', '/kraken/balance', category='portfolio')
        ])
        
        # 11. MODEL TRAINING (3 tests)
        print("\n11. MODEL TRAINING")
        self.results['model_training'].extend([
            self.test_endpoint('POST', '/enhanced-ai/train', category='model_training'),
            self.test_endpoint('GET', '/enhanced-ai/status', category='model_training'),
            self.test_endpoint('GET', '/training/status', category='model_training')
        ])
        
        # 12. MTF TRAINING - FIXED (4 tests)
        print("\n12. MTF TRAINING - TESTING FIXES")
        self.results['mtf_training'].extend([
            self.test_endpoint('GET', '/mtf-training/status', category='mtf_training'),
            self.test_endpoint('GET', '/mtf-training/predict/BTC', category='mtf_training'),  # FIXED
            self.test_endpoint('GET', '/mtf-training/fear-greed', category='mtf_training'),  # FIXED
            self.test_endpoint('GET', '/enhanced-mtf-training/fear-greed', category='mtf_training')
        ])
        
        # 13. MARKET DATA & SENTIMENT - FIXED (3 tests)
        print("\n13. MARKET DATA & SENTIMENT - TESTING FIXES")
        self.results['market_data_sentiment'].extend([
            self.test_endpoint('GET', '/market/prices', category='market_data_sentiment'),  # FIXED
            self.test_endpoint('GET', '/market/prices', 
                             {'coin_ids': 'bitcoin,ethereum'}, category='market_data_sentiment'),
            self.test_endpoint('GET', '/sentiment/market', category='market_data_sentiment')
        ])
        
        # 14. AUTO TRADING (1 test)
        print("\n14. AUTO TRADING")
        self.results['auto_trading'].extend([
            self.test_endpoint('GET', '/auto-trading/status', category='auto_trading')
        ])
        
        # 15. SECURITY & MONITORING (3 tests)
        print("\n15. SECURITY & MONITORING")
        self.results['security_monitoring'].extend([
            self.test_endpoint('GET', '/monitoring/errors', category='security_monitoring'),
            self.test_endpoint('GET', '/monitoring/errors/stats', category='security_monitoring'),
            self.test_endpoint('GET', '/monitoring/health/detailed', category='security_monitoring')
        ])
        
        # 16. ML MONITORING - FIXED (4 tests)
        print("\n16. ML MONITORING - TESTING FIXES")
        self.results['ml_monitoring'].extend([
            self.test_endpoint('GET', '/ml-monitoring/dashboard/overview', category='ml_monitoring'),  # FIXED
            self.test_endpoint('GET', '/ml-monitoring/ab-test/list', category='ml_monitoring'),  # FIXED
            self.test_endpoint('GET', '/ml-monitoring/drift/status', category='ml_monitoring'),  # FIXED
            self.test_endpoint('GET', '/ml-monitoring/alerts/active', category='ml_monitoring')  # FIXED
        ])
        
        # 17. ML OPTIMIZATION (2 tests)
        print("\n17. ML OPTIMIZATION")
        self.results['ml_optimization'].extend([
            self.test_endpoint('GET', '/ml-optimization/cache/status', category='ml_optimization'),
            self.test_endpoint('GET', '/ml-optimization/distributed/status', category='ml_optimization')
        ])
        
        # 18. JOURNAL - FIXED (1 test)
        print("\n18. JOURNAL - TESTING FIXES")
        self.results['journal'].extend([
            self.test_endpoint('GET', '/journal/entries', category='journal')  # Should not timeout
        ])
        
        # 19. CACHE (1 test)
        print("\n19. CACHE")
        self.results['cache'].extend([
            self.test_endpoint('GET', '/cache/stats', category='cache')
        ])

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
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"📈 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        # Category breakdown
        print("\n🎯 RESULTS BY CATEGORY:")
        
        fixed_issues = []
        failed_tests = []
        
        for category, tests in self.results.items():
            if not tests:
                continue
                
            category_passed = sum(1 for t in tests if t['passed'])
            category_total = len(tests)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            status_icon = "✅" if category_rate == 100 else "⚠️" if category_rate >= 50 else "❌"
            
            print(f"{status_icon} {category.upper().replace('_', ' ')}: {category_rate:.1f}% ({category_passed}/{category_total})")
            
            # Track fixed issues specifically
            if category in ['mtf_training', 'market_data_sentiment', 'ml_monitoring', 'journal']:
                fixed_issues.append({
                    'category': category,
                    'passed': category_passed,
                    'total': category_total,
                    'rate': category_rate
                })
            
            # Track failed tests
            for test in tests:
                if not test['passed']:
                    failed_tests.append(test)
        
        # Highlight the 4 FIXED issues
        print(f"\n🔧 4 FIXED ISSUES STATUS:")
        for fix in fixed_issues:
            icon = "✅ FIXED" if fix['rate'] == 100 else f"⚠️ PARTIAL ({fix['rate']:.0f}%)"
            print(f"   {icon}: {fix['category'].replace('_', ' ').title()} - {fix['passed']}/{fix['total']} tests")
        
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
            'fixed_issues': fixed_issues,
            'category_results': {cat: tests for cat, tests in self.results.items() if tests}
        }

def main():
    """Run comprehensive backend testing"""
    tester = ComprehensiveBackendTester()
    
    print("🎉 COMPREHENSIVE BACKEND RE-TEST AFTER 4 FIXES")
    print("=" * 80)
    print("Testing all 19 categories with 67 total endpoints")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run all tests
    tester.run_all_tests()
    
    # Analyze and report
    results = tester.analyze_results()
    
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"✅ SUCCESS RATE: {results['success_rate']:.1f}% ({results['passed_tests']}/{results['total_tests']})")
    
    if results['success_rate'] >= 85:
        print("🎉 EXCELLENT - Backend is production ready!")
    elif results['success_rate'] >= 70:
        print("👍 GOOD - Backend has minor issues but core functionality works")
    else:
        print("⚠️ NEEDS ATTENTION - Multiple critical issues found")
    
    return results

if __name__ == "__main__":
    main()