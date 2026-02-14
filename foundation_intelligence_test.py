#!/usr/bin/env python3
"""
Foundation and Intelligence Features Testing
===========================================
Tests the newly implemented AI Explanation and WebSocket Status endpoints.

Test Coverage:
1. AI Explanation Endpoints:
   - GET /api/ai-explain/signal/{coin_id} - Get explanation for a coin's signal
   - GET /api/ai-explain/factors - Get list of all factors
   - GET /api/ai-explain/confidence-levels - Get confidence level explanations

2. WebSocket Status:
   - GET /api/ws/status - Check WebSocket connection status

Expected Response Fields:
- AI explanation: signal, confidence, summary, primary_factors, risk_factors, recommendation
- WebSocket status: connection counts per channel
"""

import requests
import json
import time
from datetime import datetime
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://kraken-security-scan.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

class FoundationIntelligenceTest:
    def __init__(self):
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'test_details': []
        }
        self.start_time = time.time()
    
    def log_test(self, test_name: str, status: str, details: str, response_time: float = 0):
        """Log test result"""
        self.results['total_tests'] += 1
        if status == 'PASS':
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
        
        self.results['test_details'].append({
            'test': test_name,
            'status': status,
            'details': details,
            'response_time': f"{response_time:.3f}s"
        })
        
        status_icon = "✅" if status == 'PASS' else "❌"
        print(f"{status_icon} {test_name}: {details} ({response_time:.3f}s)")
    
    def test_endpoint(self, method: str, endpoint: str, expected_fields: list = None, test_name: str = None):
        """Test a single endpoint"""
        if not test_name:
            test_name = f"{method} {endpoint}"
        
        start_time = time.time()
        
        try:
            url = f"{BASE_URL}{endpoint}"
            
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json={}, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check expected fields if provided
                    if expected_fields:
                        missing_fields = []
                        for field in expected_fields:
                            if field not in data:
                                missing_fields.append(field)
                        
                        if missing_fields:
                            self.log_test(test_name, 'FAIL', 
                                        f"Missing fields: {missing_fields}. Got: {list(data.keys())}", 
                                        response_time)
                            return False
                    
                    self.log_test(test_name, 'PASS', 
                                f"Status 200, fields: {list(data.keys())[:5]}{'...' if len(data.keys()) > 5 else ''}", 
                                response_time)
                    return True
                    
                except json.JSONDecodeError:
                    self.log_test(test_name, 'FAIL', 
                                f"Status {response.status_code}, invalid JSON response", 
                                response_time)
                    return False
            else:
                self.log_test(test_name, 'FAIL', 
                            f"Status {response.status_code}: {response.text[:100]}", 
                            response_time)
                return False
                
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            self.log_test(test_name, 'FAIL', f"Request error: {str(e)}", response_time)
            return False
    
    def test_ai_explanation_signal(self):
        """Test AI explanation for specific coin signal"""
        print("\n🧠 Testing AI Explanation Signal Endpoint...")
        
        # Test with BTC
        expected_fields = ['signal', 'confidence', 'summary', 'primary_factors', 'risk_factors', 'recommendation']
        success = self.test_endpoint('GET', '/ai-explain/signal/BTC', expected_fields, 
                                   'AI Explanation Signal (BTC)')
        
        if success:
            # Test response structure in detail
            try:
                response = requests.get(f"{BASE_URL}/ai-explain/signal/BTC", timeout=10)
                data = response.json()
                
                # Verify signal is valid
                if data.get('signal') in ['BUY', 'SELL', 'HOLD']:
                    print(f"  ✅ Signal: {data.get('signal')}")
                else:
                    print(f"  ❌ Invalid signal: {data.get('signal')}")
                
                # Verify confidence is numeric
                confidence = data.get('confidence')
                if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                    print(f"  ✅ Confidence: {confidence:.2%}")
                else:
                    print(f"  ❌ Invalid confidence: {confidence}")
                
                # Verify arrays exist
                if isinstance(data.get('primary_factors'), list):
                    print(f"  ✅ Primary factors: {len(data.get('primary_factors', []))} items")
                else:
                    print(f"  ❌ Primary factors not a list")
                
                if isinstance(data.get('risk_factors'), list):
                    print(f"  ✅ Risk factors: {len(data.get('risk_factors', []))} items")
                else:
                    print(f"  ❌ Risk factors not a list")
                
                # Verify recommendation structure
                recommendation = data.get('recommendation')
                if isinstance(recommendation, dict) and 'action' in recommendation:
                    print(f"  ✅ Recommendation: {recommendation.get('action')}")
                else:
                    print(f"  ❌ Invalid recommendation structure")
                    
            except Exception as e:
                print(f"  ❌ Error verifying response structure: {e}")
        
        # Test with ETH
        self.test_endpoint('GET', '/ai-explain/signal/ETH', expected_fields, 
                          'AI Explanation Signal (ETH)')
        
        return success
    
    def test_ai_explanation_factors(self):
        """Test AI factors list endpoint"""
        print("\n📊 Testing AI Factors Endpoint...")
        
        expected_fields = ['technical_factors', 'sentiment_factors', 'on_chain_factors', 'pattern_factors']
        success = self.test_endpoint('GET', '/ai-explain/factors', expected_fields, 
                                   'AI Factors List')
        
        if success:
            # Verify factor structure
            try:
                response = requests.get(f"{BASE_URL}/ai-explain/factors", timeout=10)
                data = response.json()
                
                for category in expected_fields:
                    factors = data.get(category, [])
                    if isinstance(factors, list) and len(factors) > 0:
                        print(f"  ✅ {category}: {len(factors)} factors")
                        
                        # Check first factor structure
                        first_factor = factors[0]
                        if all(key in first_factor for key in ['name', 'weight', 'description']):
                            print(f"    ✅ Factor structure valid: {first_factor.get('name')}")
                        else:
                            print(f"    ❌ Invalid factor structure: {list(first_factor.keys())}")
                    else:
                        print(f"  ❌ {category}: Invalid or empty")
                        
            except Exception as e:
                print(f"  ❌ Error verifying factors structure: {e}")
        
        return success
    
    def test_ai_explanation_confidence_levels(self):
        """Test AI confidence levels endpoint"""
        print("\n🎯 Testing AI Confidence Levels Endpoint...")
        
        expected_fields = ['levels', 'note']
        success = self.test_endpoint('GET', '/ai-explain/confidence-levels', expected_fields, 
                                   'AI Confidence Levels')
        
        if success:
            # Verify confidence levels structure
            try:
                response = requests.get(f"{BASE_URL}/ai-explain/confidence-levels", timeout=10)
                data = response.json()
                
                levels = data.get('levels', [])
                if isinstance(levels, list) and len(levels) >= 3:
                    print(f"  ✅ Confidence levels: {len(levels)} levels defined")
                    
                    # Check level structure
                    for level in levels:
                        if all(key in level for key in ['level', 'range', 'meaning', 'action']):
                            print(f"    ✅ {level.get('level')}: {level.get('range')}")
                        else:
                            print(f"    ❌ Invalid level structure: {list(level.keys())}")
                else:
                    print(f"  ❌ Invalid levels structure")
                
                if data.get('note'):
                    print(f"  ✅ Note provided: {data.get('note')[:50]}...")
                else:
                    print(f"  ❌ No explanatory note")
                    
            except Exception as e:
                print(f"  ❌ Error verifying confidence levels structure: {e}")
        
        return success
    
    def test_websocket_status(self):
        """Test WebSocket status endpoint"""
        print("\n🔌 Testing WebSocket Status Endpoint...")
        
        expected_fields = ['status', 'connections']
        success = self.test_endpoint('GET', '/ws/status', expected_fields, 
                                   'WebSocket Status')
        
        if success:
            # Verify WebSocket status structure
            try:
                response = requests.get(f"{BASE_URL}/ws/status", timeout=10)
                data = response.json()
                
                status = data.get('status')
                if status == 'ok':
                    print(f"  ✅ WebSocket status: {status}")
                else:
                    print(f"  ❌ Unexpected status: {status}")
                
                connections = data.get('connections')
                if isinstance(connections, dict):
                    print(f"  ✅ Connection counts per channel:")
                    total_connections = 0
                    for channel, count in connections.items():
                        print(f"    - {channel}: {count} connections")
                        total_connections += count
                    print(f"  ✅ Total connections: {total_connections}")
                else:
                    print(f"  ❌ Invalid connections structure: {type(connections)}")
                    
            except Exception as e:
                print(f"  ❌ Error verifying WebSocket status structure: {e}")
        
        return success
    
    def run_all_tests(self):
        """Run all Foundation and Intelligence tests"""
        print("🚀 FOUNDATION AND INTELLIGENCE FEATURES TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test AI Explanation endpoints
        self.test_ai_explanation_signal()
        self.test_ai_explanation_factors()
        self.test_ai_explanation_confidence_levels()
        
        # Test WebSocket status
        self.test_websocket_status()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎯 FOUNDATION AND INTELLIGENCE TESTING SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        if self.results['failed'] > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.results['test_details']:
                if test['status'] == 'FAIL':
                    print(f"  - {test['test']}: {test['details']}")
        
        print("\n✅ PASSED TESTS:")
        for test in self.results['test_details']:
            if test['status'] == 'PASS':
                print(f"  - {test['test']}: {test['details']}")
        
        # Overall status
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: {success_rate:.1f}% success rate - Foundation and Intelligence features are working perfectly!")
        elif success_rate >= 75:
            print(f"\n✅ GOOD: {success_rate:.1f}% success rate - Most features working, minor issues to address")
        elif success_rate >= 50:
            print(f"\n⚠️ MODERATE: {success_rate:.1f}% success rate - Several issues need attention")
        else:
            print(f"\n❌ CRITICAL: {success_rate:.1f}% success rate - Major issues require immediate attention")


if __name__ == "__main__":
    tester = FoundationIntelligenceTest()
    tester.run_all_tests()