#!/usr/bin/env python3
"""
Web3 Wallet & AI Explainability API Testing - February 11, 2026
Testing newly implemented APIs from ENHANCEMENT_RECOMMENDATIONS.md:
1. Web3 Wallet API (/api/web3-wallet/*)
2. AI Explainability API (/api/ai-explainability/*)
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://crypto-pulse-dash.preview.emergentagent.com/api"

class Web3AIExplainabilityTester:
    def __init__(self):
        self.results = {
            'web3_wallet': [],
            'ai_explainability': []
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

    def run_web3_wallet_tests(self):
        """Test Web3 Wallet API endpoints"""
        print("\n🔗 WEB3 WALLET API TESTING")
        print("=" * 50)
        
        # Test sample wallet address for testing (proper 42-character Ethereum address)
        test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f3e6E6"
        
        # 1. GET /api/web3-wallet/chains - Get supported blockchain networks
        print("1. Testing supported chains...")
        self.results['web3_wallet'].append(
            self.test_endpoint('GET', '/web3-wallet/chains', category='web3_wallet')
        )
        
        # 2. GET /api/web3-wallet/protocols - Get supported DeFi protocols
        print("2. Testing supported protocols...")
        self.results['web3_wallet'].append(
            self.test_endpoint('GET', '/web3-wallet/protocols', category='web3_wallet')
        )
        
        # 3. POST /api/web3-wallet/connect - Connect a wallet
        print("3. Testing wallet connection...")
        connect_data = {
            "address": test_address,
            "chain_id": 1,
            "wallet_type": "metamask"
        }
        self.results['web3_wallet'].append(
            self.test_endpoint('POST', '/web3-wallet/connect', connect_data, category='web3_wallet')
        )
        
        # 4. GET /api/web3-wallet/wallets - Get connected wallets
        print("4. Testing connected wallets...")
        self.results['web3_wallet'].append(
            self.test_endpoint('GET', '/web3-wallet/wallets', category='web3_wallet')
        )
        
        # 5. GET /api/web3-wallet/balances/{address} - Get token balances
        print("5. Testing wallet balances...")
        self.results['web3_wallet'].append(
            self.test_endpoint('GET', f'/web3-wallet/balances/{test_address}', category='web3_wallet')
        )
        
        # 6. GET /api/web3-wallet/defi-positions/{address} - Get DeFi positions
        print("6. Testing DeFi positions...")
        self.results['web3_wallet'].append(
            self.test_endpoint('GET', f'/web3-wallet/defi-positions/{test_address}', category='web3_wallet')
        )
        
        # 7. GET /api/web3-wallet/nfts/{address} - Get NFT holdings
        print("7. Testing NFT holdings...")
        self.results['web3_wallet'].append(
            self.test_endpoint('GET', f'/web3-wallet/nfts/{test_address}', category='web3_wallet')
        )
        
        # 8. GET /api/web3-wallet/portfolio-summary/{address} - Get portfolio summary
        print("8. Testing portfolio summary...")
        self.results['web3_wallet'].append(
            self.test_endpoint('GET', f'/web3-wallet/portfolio-summary/{test_address}', category='web3_wallet')
        )

    def run_ai_explainability_tests(self):
        """Test AI Explainability API endpoints"""
        print("\n🧠 AI EXPLAINABILITY API TESTING")
        print("=" * 50)
        
        # 1. GET /api/ai-explainability/explain/BTC - Explain prediction for BTC
        print("1. Testing BTC prediction explanation...")
        self.results['ai_explainability'].append(
            self.test_endpoint('GET', '/ai-explainability/explain/BTC', category='ai_explainability')
        )
        
        # 2. GET /api/ai-explainability/historical-accuracy/BTC - Get historical accuracy
        print("2. Testing historical accuracy...")
        self.results['ai_explainability'].append(
            self.test_endpoint('GET', '/ai-explainability/historical-accuracy/BTC', category='ai_explainability')
        )
        
        # 3. GET /api/ai-explainability/what-if/BTC?scenario=price_up_10 - What-if analysis
        print("3. Testing what-if analysis...")
        self.results['ai_explainability'].append(
            self.test_endpoint('GET', '/ai-explainability/what-if/BTC', 
                             {'scenario': 'price_up_10'}, category='ai_explainability')
        )
        
        # 4. GET /api/ai-explainability/model-performance - Get model performance metrics
        print("4. Testing model performance...")
        self.results['ai_explainability'].append(
            self.test_endpoint('GET', '/ai-explainability/model-performance', category='ai_explainability')
        )
        
        # 5. GET /api/ai-explainability/feature-definitions - Get feature definitions
        print("5. Testing feature definitions...")
        self.results['ai_explainability'].append(
            self.test_endpoint('GET', '/ai-explainability/feature-definitions', category='ai_explainability')
        )

    def run_all_tests(self):
        """Execute all test categories"""
        print("🚀 WEB3 WALLET & AI EXPLAINABILITY API TESTING")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        # Run Web3 Wallet tests
        self.run_web3_wallet_tests()
        
        # Run AI Explainability tests
        self.run_ai_explainability_tests()

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
        print("📊 WEB3 & AI EXPLAINABILITY TEST RESULTS")
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
        
        # Detailed results for each category
        print(f"\n📋 DETAILED RESULTS:")
        
        # Web3 Wallet Results
        web3_tests = self.results.get('web3_wallet', [])
        if web3_tests:
            print(f"\n🔗 WEB3 WALLET API ({len([t for t in web3_tests if t['passed']])}/{len(web3_tests)} passed):")
            for test in web3_tests:
                status = "✅" if test['passed'] else "❌"
                print(f"   {status} {test['method']} {test['endpoint']} → {test['status']} ({test['duration']}s)")
                
                # Show key response data for successful tests
                if test['passed'] and 'response_json' in test:
                    response = test['response_json']
                    if 'chains' in test['endpoint']:
                        chains_count = len(response.get('chains', []))
                        print(f"      → {chains_count} supported chains found")
                    elif 'protocols' in test['endpoint']:
                        protocols_count = len(response.get('protocols', []))
                        print(f"      → {protocols_count} DeFi protocols supported")
                    elif 'connect' in test['endpoint']:
                        status = response.get('status', 'unknown')
                        print(f"      → Connection status: {status}")
                    elif 'balances' in test['endpoint']:
                        balances = response.get('balances', [])
                        total_value = response.get('total_value_usd', 0)
                        print(f"      → {len(balances)} tokens, ${total_value:,.2f} total value")
                    elif 'defi-positions' in test['endpoint']:
                        positions = response.get('positions', [])
                        total_value = response.get('total_value_usd', 0)
                        print(f"      → {len(positions)} DeFi positions, ${total_value:,.2f} total value")
                    elif 'nfts' in test['endpoint']:
                        nfts = response.get('nfts', [])
                        total_value = response.get('total_floor_value_usd', 0)
                        print(f"      → {len(nfts)} NFTs, ${total_value:,.2f} floor value")
                    elif 'portfolio-summary' in test['endpoint']:
                        total_value = response.get('total_value_usd', 0)
                        print(f"      → Portfolio total: ${total_value:,.2f}")
        
        # AI Explainability Results
        ai_tests = self.results.get('ai_explainability', [])
        if ai_tests:
            print(f"\n🧠 AI EXPLAINABILITY API ({len([t for t in ai_tests if t['passed']])}/{len(ai_tests)} passed):")
            for test in ai_tests:
                status = "✅" if test['passed'] else "❌"
                print(f"   {status} {test['method']} {test['endpoint']} → {test['status']} ({test['duration']}s)")
                
                # Show key response data for successful tests
                if test['passed'] and 'response_json' in test:
                    response = test['response_json']
                    if 'explain' in test['endpoint']:
                        prediction = response.get('prediction', {})
                        action = prediction.get('action', 'N/A')
                        confidence = prediction.get('confidence', 0)
                        print(f"      → Prediction: {action} (confidence: {confidence:.1%})")
                    elif 'historical-accuracy' in test['endpoint']:
                        accuracy = response.get('overall_accuracy', 0)
                        print(f"      → Overall accuracy: {accuracy}%")
                    elif 'what-if' in test['endpoint']:
                        scenario_name = response.get('name', 'N/A')
                        new_prediction = response.get('new_prediction', 'N/A')
                        print(f"      → Scenario: {scenario_name} → {new_prediction}")
                    elif 'model-performance' in test['endpoint']:
                        overall = response.get('overall', {})
                        accuracy = overall.get('accuracy', 0)
                        print(f"      → Model accuracy: {accuracy}%")
                    elif 'feature-definitions' in test['endpoint']:
                        features = response.get('features', [])
                        print(f"      → {len(features)} feature definitions")
        
        # Failed test details
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['method']} {test['endpoint']} → {test['status']} (expected {test['expected']})")
                if 'error' in test:
                    print(f"     Error: {test['error']}")
                elif 'response_text' in test:
                    print(f"     Response: {test['response_text'][:200]}...")
        
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
    """Run Web3 Wallet & AI Explainability API testing"""
    tester = Web3AIExplainabilityTester()
    
    print("🎉 WEB3 WALLET & AI EXPLAINABILITY API TESTING")
    print("=" * 80)
    print("Testing newly implemented APIs from ENHANCEMENT_RECOMMENDATIONS.md")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run all tests
    tester.run_all_tests()
    
    # Analyze and report
    results = tester.analyze_results()
    
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"✅ SUCCESS RATE: {results['success_rate']:.1f}% ({results['passed_tests']}/{results['total_tests']})")
    
    if results['success_rate'] >= 90:
        print("🎉 EXCELLENT - New APIs are production ready!")
    elif results['success_rate'] >= 75:
        print("👍 GOOD - APIs working well with minor issues")
    elif results['success_rate'] >= 50:
        print("⚠️ PARTIAL - Some APIs need attention")
    else:
        print("❌ CRITICAL - Major issues found, APIs need fixes")
    
    return results

if __name__ == "__main__":
    main()