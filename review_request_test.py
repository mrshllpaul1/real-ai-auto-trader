#!/usr/bin/env python3
"""
Review Request API Testing - February 11, 2026
Testing the specific 22 endpoints mentioned in the review request
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://kraken-security-scan.preview.emergentagent.com/api"

class ReviewRequestTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 30

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, description: str = "") -> Dict:
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
            
            response_time = round((time.time() - start_time) * 1000, 1)
            
            result = {
                'endpoint': endpoint,
                'method': method.upper(),
                'description': description,
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'success': response.status_code == expected_status,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add response data for analysis
            try:
                result['response_data'] = response.json()
            except:
                result['response_data'] = response.text[:200] if response.text else "No response body"
            
            return result
            
        except Exception as e:
            return {
                'endpoint': endpoint,
                'method': method.upper(),
                'description': description,
                'status_code': 0,
                'response_time_ms': round((time.time() - start_time) * 1000, 1),
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def run_core_apis_test(self):
        """Test Core APIs (1-3)"""
        print("🔍 Testing Core APIs...")
        
        # 1. Health check
        result = self.test_endpoint('GET', '/health', description="Health check")
        self.results.append(result)
        
        # 2. Tethys trading engine status
        result = self.test_endpoint('GET', '/tethys/status', description="Tethys trading engine status")
        self.results.append(result)
        
        # 3. Ensemble AI status
        result = self.test_endpoint('GET', '/ensemble/status', description="Ensemble AI status")
        self.results.append(result)

    def run_trading_apis_test(self):
        """Test Trading APIs (4-6)"""
        print("🔍 Testing Trading APIs...")
        
        # 4. Kraken coins list
        result = self.test_endpoint('GET', '/kraken-universe/coins', description="Kraken coins list")
        self.results.append(result)
        
        # 5. Portfolio data
        result = self.test_endpoint('GET', '/portfolio', description="Portfolio data")
        self.results.append(result)
        
        # 6. Paper trades
        result = self.test_endpoint('GET', '/paper-trades', description="Paper trades")
        self.results.append(result)

    def run_market_data_apis_test(self):
        """Test Market Data APIs (7-8)"""
        print("🔍 Testing Market Data APIs...")
        
        # 7. Current prices
        result = self.test_endpoint('GET', '/market/prices', description="Current prices")
        self.results.append(result)
        
        # 8. News feed
        result = self.test_endpoint('GET', '/coindesk/news', description="News feed")
        self.results.append(result)

    def run_settings_apis_test(self):
        """Test Settings APIs (9-11)"""
        print("🔍 Testing Settings APIs...")
        
        # 9. Sound settings (new)
        result = self.test_endpoint('GET', '/sound-settings/', description="Sound settings (new)")
        self.results.append(result)
        
        # 10. Email digest settings (new)
        result = self.test_endpoint('GET', '/email-digest/settings', description="Email digest settings (new)")
        self.results.append(result)
        
        # 11. Portfolio shares (new)
        result = self.test_endpoint('GET', '/portfolio-share/my-shares', description="Portfolio shares (new)")
        self.results.append(result)

    def run_social_marketplace_apis_test(self):
        """Test Social/Marketplace APIs (12-15) - Should return empty"""
        print("🔍 Testing Social/Marketplace APIs (should return empty)...")
        
        # 12. Copy trading leaderboard
        result = self.test_endpoint('GET', '/copy-trading/leaderboard', description="Copy trading leaderboard - should return empty")
        self.results.append(result)
        
        # 13. Social feed
        result = self.test_endpoint('GET', '/social/feed', description="Social feed - should return empty")
        self.results.append(result)
        
        # 14. Marketplace strategies
        result = self.test_endpoint('GET', '/marketplace/strategies', description="Marketplace strategies - should return empty")
        self.results.append(result)
        
        # 15. Paper leaderboard
        result = self.test_endpoint('GET', '/paper-leaderboard/', description="Paper leaderboard - should return empty")
        self.results.append(result)

    def run_defi_apis_test(self):
        """Test DeFi APIs (16) - Should return empty with message"""
        print("🔍 Testing DeFi APIs (should return empty with message)...")
        
        # 16. DeFi wallet balances
        result = self.test_endpoint('GET', '/defi-wallet/balances/0x123456', description="DeFi wallet balances - should return empty with message")
        self.results.append(result)

    def run_ml_apis_test(self):
        """Test ML APIs (17-18) - Should return empty/not_configured"""
        print("🔍 Testing ML APIs (should return empty/not_configured)...")
        
        # 17. ML monitoring A/B test list
        result = self.test_endpoint('GET', '/ml-monitoring/ab-test/list', description="ML monitoring A/B test list - should return empty")
        self.results.append(result)
        
        # 18. ML optimization distributed status
        result = self.test_endpoint('GET', '/ml-optimization/distributed/status', description="ML optimization distributed status - should return not_configured")
        self.results.append(result)

    def run_training_apis_test(self):
        """Test Training APIs (19-20)"""
        print("🔍 Testing Training APIs...")
        
        # 19. Training status
        result = self.test_endpoint('GET', '/training/status', description="Training status")
        self.results.append(result)
        
        # 20. Active training progress
        result = self.test_endpoint('GET', '/training-progress/active', description="Active training progress")
        self.results.append(result)

    def run_ai_analysis_apis_test(self):
        """Test AI/Analysis APIs (21-22)"""
        print("🔍 Testing AI/Analysis APIs...")
        
        # 21. AI models list
        result = self.test_endpoint('GET', '/ai-explain/models', description="AI models list")
        self.results.append(result)
        
        # 22. Achievements
        result = self.test_endpoint('GET', '/achievements/list', description="Achievements")
        self.results.append(result)

    def run_all_tests(self):
        """Run all tests in the review request"""
        print("🚀 Starting Review Request API Testing...")
        print(f"📍 Testing against: {BASE_URL}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test categories
        self.run_core_apis_test()
        self.run_trading_apis_test()
        self.run_market_data_apis_test()
        self.run_settings_apis_test()
        self.run_social_marketplace_apis_test()
        self.run_defi_apis_test()
        self.run_ml_apis_test()
        self.run_training_apis_test()
        self.run_ai_analysis_apis_test()
        
        total_time = time.time() - start_time
        
        # Generate summary
        self.generate_summary(total_time)

    def generate_summary(self, total_time: float):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 REVIEW REQUEST API TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {total_time:.2f}s")
        
        # Group results by success/failure
        successful_results = [r for r in self.results if r['success']]
        failed_results = [r for r in self.results if not r['success']]
        
        if successful_results:
            print(f"\n✅ SUCCESSFUL ENDPOINTS ({len(successful_results)}):")
            for result in successful_results:
                status_code = result['status_code']
                response_time = result['response_time_ms']
                print(f"   ✅ {result['method']} {result['endpoint']} ({status_code}) - {response_time}ms")
                
                # Show key response data for verification
                if 'response_data' in result and isinstance(result['response_data'], dict):
                    data = result['response_data']
                    if 'status' in data:
                        print(f"      Status: {data['status']}")
                    if 'message' in data:
                        print(f"      Message: {data['message']}")
                    if isinstance(data, list) and len(data) == 0:
                        print(f"      Response: Empty array (expected for some endpoints)")
                    elif isinstance(data, dict) and len(data) == 0:
                        print(f"      Response: Empty object")
        
        if failed_results:
            print(f"\n❌ FAILED ENDPOINTS ({len(failed_results)}):")
            for result in failed_results:
                status_code = result.get('status_code', 'N/A')
                error = result.get('error', 'Unknown error')
                print(f"   ❌ {result['method']} {result['endpoint']} ({status_code})")
                print(f"      Error: {error}")
                if 'response_data' in result:
                    print(f"      Response: {str(result['response_data'])[:100]}...")
        
        # Performance analysis
        response_times = [r['response_time_ms'] for r in self.results if r['success']]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"   Average Response Time: {avg_response_time:.1f}ms")
            print(f"   Fastest Response: {min_response_time:.1f}ms")
            print(f"   Slowest Response: {max_response_time:.1f}ms")
        
        # Specific verification for empty endpoints
        empty_endpoints = [
            '/copy-trading/leaderboard',
            '/social/feed', 
            '/marketplace/strategies',
            '/paper-leaderboard/',
            '/defi-wallet/balances/0x123456',
            '/ml-monitoring/ab-test/list',
            '/ml-optimization/distributed/status'
        ]
        
        print(f"\n🔍 EMPTY STATE VERIFICATION:")
        for result in self.results:
            if result['endpoint'] in empty_endpoints and result['success']:
                data = result.get('response_data', {})
                if isinstance(data, dict):
                    if 'message' in data:
                        print(f"   ✅ {result['endpoint']}: {data['message']}")
                    elif len(data) == 0 or (isinstance(data.get('data'), list) and len(data['data']) == 0):
                        print(f"   ✅ {result['endpoint']}: Returns empty as expected")
                elif isinstance(data, list) and len(data) == 0:
                    print(f"   ✅ {result['endpoint']}: Returns empty array as expected")
        
        print("\n" + "=" * 80)
        print("🎉 Review Request API Testing Complete!")
        print("=" * 80)

if __name__ == "__main__":
    tester = ReviewRequestTester()
    tester.run_all_tests()