#!/usr/bin/env python3
"""
Training Endpoints Testing - Specific Review Request
Testing 5 training-related endpoints to verify they work without timeout:

1. POST /api/training/train-model with {"model_name": "finrl", "coins": ["bitcoin"]}
2. POST /api/enhanced-mtf-training/train-all-kraken  
3. GET /api/training-progress/active
4. POST /api/tethys-train/start
5. GET /api/tethys-train/status

All endpoints should respond within 5 seconds and training should run in background.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://cryptoai-enhance.preview.emergentagent.com/api"

class TrainingEndpointsTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout to be safe

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, description: str = "") -> Dict:
        """Test individual endpoint and return result"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                headers = {'Content-Type': 'application/json'}
                response = self.session.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            # Check if response time is within 5 seconds as required
            within_timeout = response_time <= 5.0
            
            result = {
                'endpoint': endpoint,
                'method': method,
                'description': description,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'within_5s_timeout': within_timeout,
                'success': response.status_code == expected_status and within_timeout,
                'timestamp': datetime.now().isoformat()
            }
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                result['response_data'] = response_data
                
                # Check for specific response patterns
                if 'status' in response_data:
                    result['status_field'] = response_data['status']
                if 'message' in response_data:
                    result['message'] = response_data['message']
                    
            except json.JSONDecodeError:
                result['response_text'] = response.text[:200]  # First 200 chars
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                'endpoint': endpoint,
                'method': method,
                'description': description,
                'status_code': 'TIMEOUT',
                'response_time': 'TIMEOUT (>10s)',
                'within_5s_timeout': False,
                'success': False,
                'error': 'Request timed out',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'endpoint': endpoint,
                'method': method,
                'description': description,
                'status_code': 'ERROR',
                'response_time': time.time() - start_time,
                'within_5s_timeout': False,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def run_training_tests(self):
        """Run all 5 training endpoint tests as specified in review request"""
        
        print("🎯 TRAINING ENDPOINTS TESTING - Review Request Verification")
        print("=" * 70)
        print(f"Testing 5 specific training endpoints at: {BASE_URL}")
        print(f"Requirement: All endpoints must respond within 5 seconds")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test 1: POST /api/training/train-model with finrl model
        print("1️⃣ Testing Individual Model Training (FinRL)...")
        result1 = self.test_endpoint(
            'POST', 
            '/training/train-model',
            data={"model_name": "finrl", "coins": ["bitcoin"]},
            expected_status=200,
            description="Train FinRL model with Bitcoin - should return immediately with training_started status"
        )
        self.results.append(result1)
        self._print_result(result1)
        
        # Test 2: POST /api/enhanced-mtf-training/train-all-kraken
        print("\n2️⃣ Testing Enhanced MTF Training (All Kraken)...")
        result2 = self.test_endpoint(
            'POST',
            '/enhanced-mtf-training/train-all-kraken',
            data={},  # Empty body as per typical usage
            expected_status=200,
            description="Start enhanced MTF training for all Kraken pairs - should return immediately with started status"
        )
        self.results.append(result2)
        self._print_result(result2)
        
        # Test 3: GET /api/training-progress/active
        print("\n3️⃣ Testing Active Training Progress...")
        result3 = self.test_endpoint(
            'GET',
            '/training-progress/active',
            expected_status=200,
            description="Get active training tasks - should show current training status"
        )
        self.results.append(result3)
        self._print_result(result3)
        
        # Test 4: POST /api/tethys-train/start
        print("\n4️⃣ Testing Tethys Training Start...")
        result4 = self.test_endpoint(
            'POST',
            '/tethys-train/start',
            data={},  # Default parameters
            expected_status=200,
            description="Start Tethys training - should return immediately with training_started status"
        )
        self.results.append(result4)
        self._print_result(result4)
        
        # Test 5: GET /api/tethys-train/status
        print("\n5️⃣ Testing Tethys Training Status...")
        result5 = self.test_endpoint(
            'GET',
            '/tethys-train/status',
            expected_status=200,
            description="Get Tethys training status - should show current training state"
        )
        self.results.append(result5)
        self._print_result(result5)
        
        # Summary
        self._print_summary()

    def _print_result(self, result: Dict):
        """Print individual test result"""
        status_icon = "✅" if result['success'] else "❌"
        timeout_icon = "⚡" if result['within_5s_timeout'] else "⏰"
        
        print(f"   {status_icon} {result['method']} {result['endpoint']}")
        print(f"      Status: {result['status_code']} | Time: {result['response_time']}s {timeout_icon}")
        
        if 'status_field' in result:
            print(f"      Response Status: {result['status_field']}")
        if 'message' in result:
            print(f"      Message: {result['message']}")
        if 'error' in result:
            print(f"      Error: {result['error']}")

    def _print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("🎯 TRAINING ENDPOINTS TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        within_timeout = sum(1 for r in self.results if r['within_5s_timeout'])
        
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        timeout_compliance = (within_timeout / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   • Total Tests: {total_tests}")
        print(f"   • Successful: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"   • Within 5s Timeout: {within_timeout}/{total_tests} ({timeout_compliance:.1f}%)")
        
        # Average response time
        valid_times = [r['response_time'] for r in self.results if isinstance(r['response_time'], (int, float))]
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            max_time = max(valid_times)
            min_time = min(valid_times)
            print(f"   • Response Times: Avg {avg_time:.3f}s | Min {min_time:.3f}s | Max {max_time:.3f}s")
        
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result['success'] else "❌"
            timeout_icon = "⚡" if result['within_5s_timeout'] else "⏰"
            print(f"   {i}. {status_icon} {result['method']} {result['endpoint']} - {result['status_code']} ({result['response_time']}s) {timeout_icon}")
        
        # Critical Issues
        failed_tests = [r for r in self.results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for result in failed_tests:
                print(f"   • {result['method']} {result['endpoint']}: {result.get('error', 'Status ' + str(result['status_code']))}")
        
        # Timeout Issues
        timeout_issues = [r for r in self.results if not r['within_5s_timeout']]
        if timeout_issues:
            print(f"\n⏰ TIMEOUT ISSUES ({len(timeout_issues)}):")
            for result in timeout_issues:
                print(f"   • {result['method']} {result['endpoint']}: {result['response_time']}s (>5s requirement)")
        
        # Success Cases
        successful_cases = [r for r in self.results if r['success']]
        if successful_cases:
            print(f"\n✅ SUCCESSFUL TESTS ({len(successful_cases)}):")
            for result in successful_cases:
                status_msg = result.get('status_field', 'OK')
                print(f"   • {result['method']} {result['endpoint']}: {status_msg} ({result['response_time']}s)")
        
        print(f"\n🎯 REVIEW REQUEST COMPLIANCE:")
        if success_rate == 100 and timeout_compliance == 100:
            print("   ✅ PERFECT: All training endpoints working within 5s timeout")
        elif timeout_compliance == 100:
            print("   ⚡ GOOD: All endpoints respond within 5s (some may have errors)")
        elif success_rate >= 80:
            print("   ⚠️  MOSTLY WORKING: Most endpoints functional but some timeout issues")
        else:
            print("   ❌ ISSUES: Multiple endpoints failing or timing out")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main test execution"""
    tester = TrainingEndpointsTester()
    tester.run_training_tests()

if __name__ == "__main__":
    main()