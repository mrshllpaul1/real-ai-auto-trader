#!/usr/bin/env python3
"""
Mock Data Removal Verification Test - February 11, 2026
Testing specific endpoints to verify mock/simulated data has been removed.
These endpoints should return empty arrays or "not_configured" status, not fake data.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL configuration
BASE_URL = "https://filecheck-4.preview.emergentagent.com/api"

class MockDataRemovalTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 30

    def test_endpoint(self, method: str, endpoint: str, expected_behavior: str) -> Dict:
        """Test individual endpoint and verify no mock data"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json={})
            else:
                return {
                    'endpoint': endpoint,
                    'method': method,
                    'status': 'ERROR',
                    'message': f'Unsupported method: {method}',
                    'response_time': 0,
                    'mock_data_removed': False
                }
            
            response_time = round((time.time() - start_time) * 1000, 1)
            
            # Parse response
            try:
                data = response.json()
            except:
                data = response.text
            
            # Check for mock data removal
            mock_data_removed = self.verify_no_mock_data(data, expected_behavior)
            
            return {
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'status': 'PASS' if mock_data_removed else 'FAIL',
                'response_time': response_time,
                'data': data,
                'expected_behavior': expected_behavior,
                'mock_data_removed': mock_data_removed,
                'verification_details': self.get_verification_details(data, expected_behavior)
            }
            
        except requests.exceptions.Timeout:
            return {
                'endpoint': endpoint,
                'method': method,
                'status': 'TIMEOUT',
                'message': 'Request timed out after 30 seconds',
                'response_time': 30000,
                'mock_data_removed': False
            }
        except Exception as e:
            return {
                'endpoint': endpoint,
                'method': method,
                'status': 'ERROR',
                'message': str(e),
                'response_time': round((time.time() - start_time) * 1000, 1),
                'mock_data_removed': False
            }

    def verify_no_mock_data(self, data: Any, expected_behavior: str) -> bool:
        """Verify that the response contains no mock/simulated data"""
        if not isinstance(data, dict):
            return False
            
        if expected_behavior == "empty_array":
            # Should return empty array or empty data structure
            if isinstance(data, dict):
                # Look for array fields that should be empty
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        # Check if the list contains mock data indicators
                        if self.contains_mock_data(value):
                            return False
                return True
            return False
            
        elif expected_behavior == "not_configured":
            # Should return status indicating not configured
            if isinstance(data, dict):
                status = data.get('status', '').lower()
                return status in ['not_configured', 'disabled', 'unavailable']
            return False
            
        elif expected_behavior == "empty_with_message":
            # Should return empty data with helpful message
            if isinstance(data, dict):
                # Check for empty arrays/objects and presence of message
                has_message = any(key in data for key in ['message', 'info', 'note', 'description'])
                has_empty_data = True
                
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        if self.contains_mock_data(value):
                            has_empty_data = False
                            break
                            
                return has_empty_data and (has_message or len(data) == 0)
            return False
            
        elif expected_behavior == "config_only":
            # Should return configuration without sample data
            if isinstance(data, dict):
                # Check that it's configuration data, not sample/mock data
                return not self.contains_mock_data_indicators(data)
            return False
            
        return False

    def contains_mock_data(self, data: Any) -> bool:
        """Check if data contains mock/simulated indicators"""
        if isinstance(data, list):
            for item in data:
                if self.contains_mock_data_indicators(item):
                    return True
        elif isinstance(data, dict):
            return self.contains_mock_data_indicators(data)
        return False

    def contains_mock_data_indicators(self, item: Any) -> bool:
        """Check for common mock data indicators"""
        if not isinstance(item, dict):
            return False
            
        # Convert to string for pattern matching
        item_str = json.dumps(item).lower()
        
        # Common mock data indicators
        mock_indicators = [
            'sample', 'test', 'mock', 'fake', 'dummy', 'example',
            'simulated', 'generated', 'placeholder', 'demo'
        ]
        
        # Check for mock patterns in values
        for indicator in mock_indicators:
            if indicator in item_str:
                return True
                
        # Check for obviously fake data patterns
        fake_patterns = [
            'user123', 'testuser', 'sample_', 'test_', 'mock_',
            'example.com', 'test@', 'fake@', 'sample@'
        ]
        
        for pattern in fake_patterns:
            if pattern in item_str:
                return True
                
        return False

    def get_verification_details(self, data: Any, expected_behavior: str) -> str:
        """Get detailed verification information"""
        if not isinstance(data, dict):
            return f"Response is not a dict: {type(data)}"
            
        details = []
        
        if expected_behavior == "empty_array":
            for key, value in data.items():
                if isinstance(value, list):
                    if len(value) == 0:
                        details.append(f"✅ {key}: empty array (correct)")
                    else:
                        mock_found = self.contains_mock_data(value)
                        if mock_found:
                            details.append(f"❌ {key}: contains {len(value)} items with mock data")
                        else:
                            details.append(f"✅ {key}: contains {len(value)} items (no mock data detected)")
                            
        elif expected_behavior == "not_configured":
            status = data.get('status', 'unknown')
            details.append(f"Status: {status}")
            
        elif expected_behavior == "empty_with_message":
            has_message = any(key in data for key in ['message', 'info', 'note', 'description'])
            details.append(f"Has message: {has_message}")
            
            for key, value in data.items():
                if isinstance(value, list):
                    details.append(f"{key}: {len(value)} items")
                    
        elif expected_behavior == "config_only":
            mock_found = self.contains_mock_data_indicators(data)
            details.append(f"Mock data indicators found: {mock_found}")
            
        return "; ".join(details) if details else "No specific details"

    def run_mock_data_removal_tests(self):
        """Run all mock data removal verification tests"""
        print("🧪 MOCK DATA REMOVAL VERIFICATION TEST")
        print("=" * 60)
        print(f"Testing {BASE_URL}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Define test cases with expected behaviors
        test_cases = [
            {
                'method': 'GET',
                'endpoint': '/sound-settings/',
                'expected_behavior': 'config_only',
                'description': 'Should return sound settings config (no mock data)'
            },
            {
                'method': 'GET', 
                'endpoint': '/email-digest/settings',
                'expected_behavior': 'config_only',
                'description': 'Should return email settings (no mock data)'
            },
            {
                'method': 'GET',
                'endpoint': '/portfolio-share/my-shares',
                'expected_behavior': 'empty_array',
                'description': 'Should return empty shares array'
            },
            {
                'method': 'GET',
                'endpoint': '/copy-trading/leaderboard',
                'expected_behavior': 'empty_array',
                'description': 'Should return empty leaderboard (no sample traders)'
            },
            {
                'method': 'GET',
                'endpoint': '/social-trading/feed',
                'expected_behavior': 'empty_array',
                'description': 'Should return empty feed (no sample trades)'
            },
            {
                'method': 'GET',
                'endpoint': '/strategy-marketplace/strategies',
                'expected_behavior': 'empty_array',
                'description': 'Should return empty strategies (no sample strategies)'
            },
            {
                'method': 'GET',
                'endpoint': '/paper-leaderboard/',
                'expected_behavior': 'empty_array',
                'description': 'Should return empty leaderboard (no generated sample data)'
            },
            {
                'method': 'GET',
                'endpoint': '/defi-wallet/balances/0x123',
                'expected_behavior': 'empty_with_message',
                'description': 'Should return empty balances with message about requiring API key'
            },
            {
                'method': 'GET',
                'endpoint': '/ml-monitoring/ab-test/list',
                'expected_behavior': 'empty_array',
                'description': 'Should return empty tests array (no simulated tests)'
            },
            {
                'method': 'GET',
                'endpoint': '/ml-optimization/distributed/cluster',
                'expected_behavior': 'not_configured',
                'description': 'Should return "not_configured" status (no fake workers)'
            }
        ]

        # Run tests
        passed = 0
        failed = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i}/10: {test_case['method']} {test_case['endpoint']}")
            print(f"Expected: {test_case['description']}")
            
            result = self.test_endpoint(
                test_case['method'],
                test_case['endpoint'],
                test_case['expected_behavior']
            )
            
            self.results.append(result)
            
            if result['status'] == 'PASS':
                print(f"✅ PASS - Mock data removed successfully")
                print(f"   Details: {result['verification_details']}")
                passed += 1
            else:
                print(f"❌ FAIL - {result.get('message', 'Mock data still present')}")
                if 'verification_details' in result:
                    print(f"   Details: {result['verification_details']}")
                failed += 1
                
            print(f"   Response time: {result['response_time']}ms")
            print()

        # Summary
        print("=" * 60)
        print("🎯 MOCK DATA REMOVAL VERIFICATION SUMMARY")
        print(f"Total tests: {len(test_cases)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success rate: {(passed/len(test_cases)*100):.1f}%")
        print()

        if failed > 0:
            print("❌ FAILED TESTS:")
            for result in self.results:
                if result['status'] != 'PASS':
                    print(f"- {result['method']} {result['endpoint']}: {result.get('message', 'Mock data detected')}")
            print()

        print("✅ PASSED TESTS:")
        for result in self.results:
            if result['status'] == 'PASS':
                print(f"- {result['method']} {result['endpoint']}: Mock data successfully removed")
        
        return passed, failed, self.results

if __name__ == "__main__":
    tester = MockDataRemovalTester()
    passed, failed, results = tester.run_mock_data_removal_tests()