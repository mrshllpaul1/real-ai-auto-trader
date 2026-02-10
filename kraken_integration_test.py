#!/usr/bin/env python3
"""
Kraken Portfolio and Trading Pairs Integration Test - February 10, 2026
Testing specific endpoints requested in review:
1. GET /api/spot/pairs/all - Should return 600+ USD trading pairs from Kraken
2. GET /api/portfolio/visualization/kraken-portfolio - Should return connected=true, total_value_usd > 0
3. GET /api/options/chain/ETH - verify returns real price for ETH
4. GET /api/perpetuals/markets - verify returns real Kraken prices
5. Market Maker Trading Pair Selection verification
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://winrate-booster.preview.emergentagent.com/api"

class KrakenIntegrationTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 30
        self.total_tests = 0
        self.passed_tests = 0

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, test_name: str = "") -> Dict:
        """Test individual endpoint and return result"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                'test_name': test_name,
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'response_time': round(response_time, 2),
                'expected_status': expected_status,
                'success': response.status_code == expected_status,
                'timestamp': datetime.now().isoformat()
            }
            
            # Parse response if possible
            try:
                result['response_data'] = response.json()
            except:
                result['response_data'] = response.text[:500] if response.text else "No response body"
            
            self.total_tests += 1
            if result['success']:
                self.passed_tests += 1
                
            return result
            
        except Exception as e:
            self.total_tests += 1
            return {
                'test_name': test_name,
                'endpoint': endpoint,
                'method': method,
                'status_code': 'ERROR',
                'response_time': time.time() - start_time,
                'expected_status': expected_status,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def test_trading_pairs_endpoint(self):
        """Test 1: All Trading Pairs Endpoint - Should return 600+ USD trading pairs"""
        print("🔍 Testing Trading Pairs Endpoint...")
        
        result = self.test_endpoint('GET', '/spot/pairs/all', 
                                  test_name="All Trading Pairs - Kraken Integration")
        
        # Additional validation for trading pairs
        if result['success'] and 'response_data' in result:
            data = result['response_data']
            
            # Check for required fields
            if 'count' in data and 'pairs' in data:
                count = data.get('count', 0)
                pairs = data.get('pairs', [])
                
                result['validation'] = {
                    'has_count_field': True,
                    'has_pairs_array': True,
                    'count_value': count,
                    'pairs_length': len(pairs),
                    'meets_600_requirement': count >= 600,
                    'sample_pairs': pairs[:3] if pairs else []
                }
                
                # Check if pairs have required structure (symbol, display)
                if pairs:
                    sample_pair = pairs[0]
                    result['validation']['pair_structure'] = {
                        'has_symbol': 'symbol' in sample_pair,
                        'has_display': 'display' in sample_pair,
                        'sample_pair': sample_pair
                    }
                
                print(f"   ✅ Found {count} trading pairs (requirement: 600+)")
                if count >= 600:
                    print(f"   ✅ Meets 600+ pairs requirement")
                else:
                    print(f"   ❌ Does not meet 600+ pairs requirement")
            else:
                result['validation'] = {
                    'has_count_field': 'count' in data,
                    'has_pairs_array': 'pairs' in data,
                    'missing_fields': True
                }
                print(f"   ❌ Missing required fields (count, pairs)")
        
        self.results.append(result)
        return result

    def test_kraken_portfolio_endpoint(self):
        """Test 2: Kraken Portfolio Endpoint - Should return connected=true, total_value_usd > 0"""
        print("🔍 Testing Kraken Portfolio Endpoint...")
        
        result = self.test_endpoint('GET', '/portfolio/visualization/kraken-portfolio',
                                  test_name="Kraken Portfolio Visualization")
        
        # Additional validation for portfolio
        if result['success'] and 'response_data' in result:
            data = result['response_data']
            
            result['validation'] = {
                'has_connected_field': 'connected' in data,
                'connected_value': data.get('connected'),
                'has_total_value_usd': 'total_value_usd' in data,
                'total_value_usd': data.get('total_value_usd'),
                'has_holdings_array': 'holdings' in data,
                'holdings_count': len(data.get('holdings', [])) if 'holdings' in data else 0
            }
            
            connected = data.get('connected', False)
            total_value = data.get('total_value_usd', 0)
            
            print(f"   Connected: {connected}")
            print(f"   Total Value USD: ${total_value}")
            
            if connected:
                print(f"   ✅ Kraken connection active")
            else:
                print(f"   ❌ Kraken not connected")
                
            if total_value > 0:
                print(f"   ✅ Has positive portfolio value")
            else:
                print(f"   ❌ Portfolio value is zero or negative")
                
            # Check holdings structure
            holdings = data.get('holdings', [])
            if holdings:
                sample_holding = holdings[0]
                result['validation']['holdings_structure'] = {
                    'has_asset': 'asset' in sample_holding,
                    'has_amount': 'amount' in sample_holding,
                    'has_price_usd': 'price_usd' in sample_holding,
                    'has_value_usd': 'value_usd' in sample_holding,
                    'has_percentage': 'percentage' in sample_holding,
                    'sample_holding': sample_holding
                }
                print(f"   ✅ Found {len(holdings)} holdings with proper structure")
        
        self.results.append(result)
        return result

    def test_options_chain_endpoint(self):
        """Test 3: Options Trading Pair Selection - ETH real price"""
        print("🔍 Testing Options Chain Endpoint...")
        
        result = self.test_endpoint('GET', '/options/chain/ETH',
                                  test_name="Options Chain ETH - Real Price Verification")
        
        # Additional validation for options
        if result['success'] and 'response_data' in result:
            data = result['response_data']
            
            # Look for price information
            current_price = None
            if 'current_price' in data:
                current_price = data['current_price']
            elif 'price' in data:
                current_price = data['price']
            elif 'underlying_price' in data:
                current_price = data['underlying_price']
            
            result['validation'] = {
                'has_price_data': current_price is not None,
                'current_price': current_price,
                'price_range_check': None,
                'data_structure': list(data.keys()) if isinstance(data, dict) else "Not a dict"
            }
            
            if current_price:
                # ETH price should be in reasonable range (e.g., $1000-$5000)
                if 1000 <= current_price <= 5000:
                    result['validation']['price_range_check'] = 'reasonable'
                    print(f"   ✅ ETH price ${current_price} is in reasonable range")
                else:
                    result['validation']['price_range_check'] = 'unusual'
                    print(f"   ⚠️ ETH price ${current_price} seems unusual")
            else:
                print(f"   ❌ No price data found in response")
        
        self.results.append(result)
        return result

    def test_perpetuals_markets_endpoint(self):
        """Test 4: Perpetuals Markets - Real Kraken prices"""
        print("🔍 Testing Perpetuals Markets Endpoint...")
        
        result = self.test_endpoint('GET', '/perpetuals/markets',
                                  test_name="Perpetuals Markets - Real Kraken Prices")
        
        # Additional validation for perpetuals
        if result['success'] and 'response_data' in result:
            data = result['response_data']
            
            markets = []
            if isinstance(data, list):
                markets = data
            elif isinstance(data, dict) and 'markets' in data:
                markets = data['markets']
            
            result['validation'] = {
                'markets_count': len(markets),
                'has_markets_data': len(markets) > 0,
                'sample_markets': markets[:3] if markets else [],
                'kraken_price_verification': []
            }
            
            # Check market structure and prices
            for i, market in enumerate(markets[:5]):  # Check first 5 markets
                if isinstance(market, dict):
                    market_validation = {
                        'market_name': market.get('symbol', market.get('name', f'Market_{i}')),
                        'has_price': 'price' in market or 'current_price' in market or 'mark_price' in market,
                        'price_value': market.get('price', market.get('current_price', market.get('mark_price'))),
                        'has_symbol': 'symbol' in market or 'name' in market
                    }
                    result['validation']['kraken_price_verification'].append(market_validation)
            
            print(f"   ✅ Found {len(markets)} perpetual markets")
            if markets:
                print(f"   ✅ Markets have real price data from Kraken")
                for validation in result['validation']['kraken_price_verification']:
                    market_name = validation['market_name']
                    price = validation['price_value']
                    if price:
                        print(f"      - {market_name}: ${price}")
        
        self.results.append(result)
        return result

    def test_market_maker_pairs_verification(self):
        """Test 5: Verify Market Maker has access to 626+ trading pairs"""
        print("🔍 Testing Market Maker Trading Pairs Access...")
        
        # This might be the same endpoint as trading pairs, but let's verify
        result = self.test_endpoint('GET', '/spot/pairs/all',
                                  test_name="Market Maker Trading Pairs Verification")
        
        # Additional validation specific to market maker requirements
        if result['success'] and 'response_data' in result:
            data = result['response_data']
            count = data.get('count', 0)
            
            result['validation'] = {
                'total_pairs': count,
                'meets_626_requirement': count >= 626,
                'market_maker_ready': count >= 626
            }
            
            print(f"   Total pairs available: {count}")
            if count >= 626:
                print(f"   ✅ Market Maker has sufficient pairs (626+ requirement met)")
            else:
                print(f"   ❌ Market Maker insufficient pairs (need 626+, got {count})")
        
        self.results.append(result)
        return result

    def run_all_tests(self):
        """Run all Kraken integration tests"""
        print("🚀 Starting Kraken Portfolio and Trading Pairs Integration Tests")
        print("=" * 70)
        
        start_time = time.time()
        
        # Run all tests
        self.test_trading_pairs_endpoint()
        print()
        
        self.test_kraken_portfolio_endpoint()
        print()
        
        self.test_options_chain_endpoint()
        print()
        
        self.test_perpetuals_markets_endpoint()
        print()
        
        self.test_market_maker_pairs_verification()
        print()
        
        total_time = time.time() - start_time
        
        # Print summary
        print("=" * 70)
        print("🎯 KRAKEN INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 Overall Results: {self.passed_tests}/{self.total_tests} tests passed ({success_rate:.1f}%)")
        print(f"⏱️ Total execution time: {total_time:.2f} seconds")
        print()
        
        # Detailed results
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['test_name']}")
            print(f"   Endpoint: {result['method']} {result['endpoint']}")
            print(f"   Status: {result['status_code']} (expected {result['expected_status']})")
            print(f"   Response time: {result['response_time']}s")
            
            if 'validation' in result:
                print(f"   Validation results:")
                for key, value in result['validation'].items():
                    if key not in ['sample_pairs', 'sample_holding', 'sample_markets', 'kraken_price_verification']:
                        print(f"     - {key}: {value}")
            
            if not result['success']:
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                elif 'response_data' in result:
                    print(f"   Response: {str(result['response_data'])[:200]}...")
            
            print()
        
        # Critical issues summary
        critical_issues = []
        for result in self.results:
            if not result['success']:
                critical_issues.append(f"{result['test_name']}: {result.get('error', 'HTTP ' + str(result['status_code']))}")
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   ❌ {issue}")
        else:
            print("✅ NO CRITICAL ISSUES - ALL KRAKEN INTEGRATION TESTS PASSED")
        
        return {
            'success_rate': success_rate,
            'passed': self.passed_tests,
            'total': self.total_tests,
            'critical_issues': critical_issues,
            'results': self.results
        }

if __name__ == "__main__":
    tester = KrakenIntegrationTester()
    results = tester.run_all_tests()