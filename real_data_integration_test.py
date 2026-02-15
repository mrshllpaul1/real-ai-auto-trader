#!/usr/bin/env python3
"""
Real Data Integration Testing - February 10, 2026
Testing specific endpoints for real data integration changes as requested in review.

Review Request Focus:
1. Options Trading with Real Prices (GET /api/options/chain/BTC)
2. Perpetual Futures with Real Prices (GET /api/perpetuals/markets) 
3. Perpetuals Account with Real Balance (GET /api/perpetuals/account)
4. Position Manager Endpoint (GET /api/isolated-portfolio/positions)
5. Triggers Endpoint (GET /api/triggers/list)
6. News Sentiment (GET /api/sentiment/market)
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL configuration
BASE_URL = "https://feature-enhancer-7.preview.emergentagent.com/api"

class RealDataIntegrationTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 30

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, description: str = "") -> Dict:
        """Test individual endpoint and return detailed result"""
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
                'description': description,
                'status': response.status_code,
                'expected': expected_status,
                'passed': response.status_code == expected_status,
                'duration': round(duration, 3),
                'response_size': len(response.content),
                'timestamp': datetime.now().isoformat()
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
                'description': description,
                'status': 'ERROR',
                'expected': expected_status,
                'passed': False,
                'duration': round(duration, 3),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def analyze_real_data_response(self, result: Dict, expected_real_data_indicators: List[str]) -> Dict:
        """Analyze if response contains real data vs simulated/hardcoded data"""
        analysis = {
            'has_real_data': False,
            'real_data_indicators': [],
            'simulated_data_indicators': [],
            'price_analysis': {},
            'data_source_analysis': {}
        }
        
        if not result.get('response_json'):
            analysis['error'] = "No JSON response to analyze"
            return analysis
        
        response_data = result['response_json']
        response_str = json.dumps(response_data).lower()
        
        # Check for real data indicators
        real_indicators_found = []
        for indicator in expected_real_data_indicators:
            if indicator.lower() in response_str:
                real_indicators_found.append(indicator)
        
        analysis['real_data_indicators'] = real_indicators_found
        
        # Check for simulated/hardcoded data indicators
        simulated_indicators = ['simulated', 'mock', 'fake', 'test', 'hardcoded', '45000', 'demo']
        simulated_found = []
        for indicator in simulated_indicators:
            if indicator in response_str:
                simulated_found.append(indicator)
        
        analysis['simulated_data_indicators'] = simulated_found
        
        # Analyze prices (look for realistic BTC/ETH prices)
        if 'current_price' in response_str or 'price' in response_str:
            # Look for BTC prices around 68000-70000
            if any(str(price) in response_str for price in range(68000, 71000)):
                analysis['price_analysis']['btc_realistic'] = True
            elif '45000' in response_str:
                analysis['price_analysis']['btc_old_simulated'] = True
            
            # Look for ETH prices around 2000-2200  
            if any(str(price) in response_str for price in range(2000, 2300)):
                analysis['price_analysis']['eth_realistic'] = True
        
        # Check data source
        if 'data_source' in response_data:
            analysis['data_source_analysis']['source'] = response_data['data_source']
            analysis['data_source_analysis']['is_kraken_live'] = response_data['data_source'] == 'kraken_live'
        
        # Determine if has real data
        analysis['has_real_data'] = (
            len(real_indicators_found) > 0 and 
            len(simulated_found) == 0 and
            not analysis['price_analysis'].get('btc_old_simulated', False)
        )
        
        return analysis

    def run_real_data_integration_tests(self):
        """Execute all real data integration tests as specified in review request"""
        
        print("🚀 REAL DATA INTEGRATION TESTING")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        # 1. OPTIONS TRADING WITH REAL PRICES
        print("\n1. 📊 OPTIONS TRADING - Real BTC Prices")
        result1 = self.test_endpoint(
            'GET', '/options/chain/BTC', 
            description="Options chain for BTC - should show real price ~$68,000-70,000"
        )
        self.results.append(result1)
        
        if result1['passed']:
            analysis1 = self.analyze_real_data_response(
                result1, 
                ['kraken', 'real', 'live', 'current_price']
            )
            result1['real_data_analysis'] = analysis1
            
            if analysis1.get('price_analysis', {}).get('btc_realistic'):
                print("   ✅ BTC price appears realistic ($68k-$70k range)")
            elif analysis1.get('price_analysis', {}).get('btc_old_simulated'):
                print("   ❌ BTC price shows old simulated value ($45k)")
            else:
                print("   ⚠️ BTC price analysis inconclusive")
        
        # 2. PERPETUAL FUTURES WITH REAL PRICES
        print("\n2. 📈 PERPETUAL FUTURES - Real Kraken Prices")
        result2 = self.test_endpoint(
            'GET', '/perpetuals/markets',
            description="Perpetual futures markets - should show real Kraken prices"
        )
        self.results.append(result2)
        
        if result2['passed']:
            analysis2 = self.analyze_real_data_response(
                result2,
                ['kraken', 'BTC-PERP', 'ETH-PERP', 'real', 'live']
            )
            result2['real_data_analysis'] = analysis2
            
            if analysis2.get('price_analysis', {}).get('btc_realistic'):
                print("   ✅ BTC-PERP price appears realistic")
            if analysis2.get('price_analysis', {}).get('eth_realistic'):
                print("   ✅ ETH-PERP price appears realistic")
        
        # 3. PERPETUALS ACCOUNT WITH REAL BALANCE
        print("\n3. 💰 PERPETUALS ACCOUNT - Real Kraken Balance")
        result3 = self.test_endpoint(
            'GET', '/perpetuals/account',
            description="Perpetuals account - should show data_source='kraken_live'"
        )
        self.results.append(result3)
        
        if result3['passed']:
            analysis3 = self.analyze_real_data_response(
                result3,
                ['kraken_live', 'kraken', 'real', 'live']
            )
            result3['real_data_analysis'] = analysis3
            
            if analysis3.get('data_source_analysis', {}).get('is_kraken_live'):
                print("   ✅ Data source confirmed as 'kraken_live'")
            else:
                print(f"   ⚠️ Data source: {analysis3.get('data_source_analysis', {}).get('source', 'unknown')}")
        
        # 4. POSITION MANAGER ENDPOINT
        print("\n4. 📋 POSITION MANAGER - Positions Array")
        result4 = self.test_endpoint(
            'GET', '/isolated-portfolio/positions',
            description="Position manager - should return positions array"
        )
        self.results.append(result4)
        
        if result4['passed'] and result4.get('response_json'):
            if isinstance(result4['response_json'], list) or 'positions' in result4['response_json']:
                print("   ✅ Returns positions array structure")
            else:
                print("   ⚠️ Response structure unclear")
        
        # 5. TRIGGERS ENDPOINT
        print("\n5. 🔔 TRIGGERS - Triggers Array")
        result5 = self.test_endpoint(
            'GET', '/triggers/list',
            description="Triggers list - should return triggers array"
        )
        self.results.append(result5)
        
        if result5['passed'] and result5.get('response_json'):
            response_data = result5['response_json']
            if isinstance(response_data, list) or 'triggers' in response_data:
                print("   ✅ Returns triggers array structure")
            else:
                print("   ⚠️ Response structure unclear")
        
        # 6. NEWS SENTIMENT
        print("\n6. 📰 NEWS SENTIMENT - Market Score & Label")
        result6 = self.test_endpoint(
            'GET', '/sentiment/market',
            description="Market sentiment - should return market_score and market_label"
        )
        self.results.append(result6)
        
        if result6['passed'] and result6.get('response_json'):
            response_data = result6['response_json']
            has_score = 'market_score' in response_data
            has_label = 'market_label' in response_data
            
            if has_score and has_label:
                print(f"   ✅ Has market_score and market_label")
                if 'market_score' in response_data:
                    print(f"   📊 Market Score: {response_data.get('market_score')}")
                if 'market_label' in response_data:
                    print(f"   🏷️ Market Label: {response_data.get('market_label')}")
            else:
                missing = []
                if not has_score: missing.append('market_score')
                if not has_label: missing.append('market_label')
                print(f"   ⚠️ Missing: {', '.join(missing)}")

    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 REAL DATA INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"📈 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        print(f"\n🎯 DETAILED RESULTS:")
        
        real_data_endpoints = 0
        simulated_data_endpoints = 0
        
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result['passed'] else "❌"
            print(f"\n{i}. {status_icon} {result['method']} {result['endpoint']}")
            print(f"   📝 {result['description']}")
            print(f"   📊 Status: {result['status']} (expected {result['expected']})")
            
            if result['passed']:
                print(f"   ⏱️ Duration: {result['duration']}s")
                
                # Real data analysis
                if 'real_data_analysis' in result:
                    analysis = result['real_data_analysis']
                    
                    if analysis['has_real_data']:
                        print(f"   ✅ REAL DATA CONFIRMED")
                        real_data_endpoints += 1
                    else:
                        print(f"   ⚠️ DATA SOURCE UNCLEAR")
                    
                    if analysis['real_data_indicators']:
                        print(f"   🔍 Real data indicators: {', '.join(analysis['real_data_indicators'])}")
                    
                    if analysis['simulated_data_indicators']:
                        print(f"   ⚠️ Simulated indicators: {', '.join(analysis['simulated_data_indicators'])}")
                        simulated_data_endpoints += 1
                    
                    if analysis['price_analysis']:
                        print(f"   💰 Price analysis: {analysis['price_analysis']}")
                    
                    if analysis['data_source_analysis']:
                        print(f"   📡 Data source: {analysis['data_source_analysis']}")
            else:
                if 'error' in result:
                    print(f"   ❌ Error: {result['error']}")
        
        # Final assessment
        print(f"\n🎯 REAL DATA INTEGRATION ASSESSMENT:")
        print(f"   ✅ Endpoints with confirmed real data: {real_data_endpoints}")
        print(f"   ⚠️ Endpoints with simulated data indicators: {simulated_data_endpoints}")
        print(f"   📊 Working endpoints: {passed_tests}/{total_tests}")
        
        if success_rate >= 80 and real_data_endpoints >= 3:
            print(f"\n🎉 EXCELLENT: Real data integration is working well!")
        elif success_rate >= 60:
            print(f"\n👍 GOOD: Most endpoints working, some real data integration issues")
        else:
            print(f"\n⚠️ NEEDS ATTENTION: Multiple integration issues found")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'real_data_endpoints': real_data_endpoints,
            'simulated_data_endpoints': simulated_data_endpoints,
            'results': self.results
        }

def main():
    """Run real data integration testing"""
    tester = RealDataIntegrationTester()
    
    print("🎉 REAL DATA INTEGRATION TESTING")
    print("=" * 80)
    print("Testing 6 specific endpoints for real data integration changes")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run all tests
    tester.run_real_data_integration_tests()
    
    # Generate report
    results = tester.generate_summary_report()
    
    return results

if __name__ == "__main__":
    main()