#!/usr/bin/env python3
"""
Tethys Toggle Functionality Test - February 12, 2026
Quick verification of Tethys training toggle functionality as requested in review.

Test Sequence:
1. GET /api/tethys-train/status - Check initial status (is_training should be false)
2. POST /api/tethys-train/start - Start training (should return immediately with status: training_started)
3. GET /api/tethys-train/status - Verify training started (is_training should be true)
4. POST /api/tethys-train/stop - Stop training
5. GET /api/tethys-train/status - Verify training stopped (is_training should be false)

All endpoints should respond within 5 seconds without timeout.
"""

import requests
import json
import time
from datetime import datetime

# Backend URL configuration
BASE_URL = "https://smart-trade-ai-68.preview.emergentagent.com/api"

class TethysToggleTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 5  # 5 second timeout as required
        self.results = []

    def test_endpoint(self, method: str, endpoint: str, data: dict = None, expected_field: str = None, expected_value: any = None) -> dict:
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
            
            # Check if response time is within 5 seconds
            if response_time > 5.0:
                return {
                    'endpoint': endpoint,
                    'method': method,
                    'status': 'TIMEOUT',
                    'response_time': response_time,
                    'error': f'Response time {response_time:.2f}s exceeds 5 second limit'
                }
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            # Check expected field and value if specified
            field_check_passed = True
            field_check_message = ""
            
            if expected_field and expected_value is not None:
                if expected_field in response_data:
                    actual_value = response_data[expected_field]
                    if actual_value != expected_value:
                        field_check_passed = False
                        field_check_message = f"Expected {expected_field}={expected_value}, got {actual_value}"
                else:
                    field_check_passed = False
                    field_check_message = f"Field '{expected_field}' not found in response"
            
            return {
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'response_time': response_time,
                'response_data': response_data,
                'field_check_passed': field_check_passed,
                'field_check_message': field_check_message,
                'success': response.status_code == 200 and field_check_passed
            }
            
        except requests.exceptions.Timeout:
            return {
                'endpoint': endpoint,
                'method': method,
                'status': 'TIMEOUT',
                'response_time': 5.0,
                'error': 'Request timed out after 5 seconds'
            }
        except Exception as e:
            return {
                'endpoint': endpoint,
                'method': method,
                'status': 'ERROR',
                'response_time': time.time() - start_time,
                'error': str(e)
            }

    def run_tethys_toggle_test(self):
        """Run the complete Tethys toggle test sequence"""
        print("🎯 TETHYS TOGGLE FUNCTIONALITY TEST - Starting...")
        print("=" * 60)
        
        # Step 1: Check initial status (is_training should be false)
        print("\n1️⃣ STEP 1: Check initial training status")
        result1 = self.test_endpoint('GET', '/tethys-train/status', expected_field='is_training', expected_value=False)
        self.results.append(result1)
        self.print_result(result1, "Initial status check")
        
        # Wait a moment between requests
        time.sleep(0.5)
        
        # Step 2: Start training (should return immediately with status: training_started)
        print("\n2️⃣ STEP 2: Start training")
        training_config = {
            "episodes": 10,
            "symbol": "BTC"
        }
        result2 = self.test_endpoint('POST', '/tethys-train/start', data=training_config, expected_field='status', expected_value='training_started')
        self.results.append(result2)
        self.print_result(result2, "Start training")
        
        # Wait a moment for training to initialize
        time.sleep(2.0)
        
        # Step 3: Verify training started (is_training should be true)
        # Try multiple times as training initialization may take a moment
        print("\n3️⃣ STEP 3: Verify training started (with retries)")
        training_started = False
        max_retries = 5
        
        for attempt in range(max_retries):
            result3 = self.test_endpoint('GET', '/tethys-train/status')
            if result3.get('response_data', {}).get('is_training') == True:
                training_started = True
                result3['field_check_passed'] = True
                result3['field_check_message'] = "Training started successfully"
                result3['success'] = True
                break
            else:
                print(f"   Attempt {attempt + 1}/{max_retries}: Training not started yet, waiting...")
                time.sleep(1.0)
        
        if not training_started:
            result3['field_check_passed'] = False
            result3['field_check_message'] = f"Training did not start after {max_retries} attempts"
            result3['success'] = False
        
        self.results.append(result3)
        self.print_result(result3, "Verify training started")
        
        # Wait a moment
        time.sleep(0.5)
        
        # Step 4: Stop training
        print("\n4️⃣ STEP 4: Stop training")
        result4 = self.test_endpoint('POST', '/tethys-train/stop', expected_field='status', expected_value='stop_requested')
        self.results.append(result4)
        self.print_result(result4, "Stop training")
        
        # Wait a moment for training to stop
        time.sleep(1.0)
        
        # Step 5: Verify training stopped (is_training should be false)
        print("\n5️⃣ STEP 5: Verify training stopped")
        result5 = self.test_endpoint('GET', '/tethys-train/status', expected_field='is_training', expected_value=False)
        self.results.append(result5)
        self.print_result(result5, "Verify training stopped")
        
        # Generate summary
        self.generate_summary()

    def print_result(self, result: dict, step_name: str):
        """Print formatted result for a test step"""
        if result.get('success', False):
            print(f"   ✅ {step_name}: PASSED")
            print(f"      Status Code: {result.get('status_code', 'N/A')}")
            print(f"      Response Time: {result.get('response_time', 0):.3f}s")
            if result.get('field_check_message'):
                print(f"      Field Check: {result['field_check_message']}")
        else:
            print(f"   ❌ {step_name}: FAILED")
            if 'status_code' in result:
                print(f"      Status Code: {result['status_code']}")
            print(f"      Response Time: {result.get('response_time', 0):.3f}s")
            if result.get('error'):
                print(f"      Error: {result['error']}")
            if result.get('field_check_message'):
                print(f"      Field Check: {result['field_check_message']}")
            if result.get('response_data'):
                print(f"      Response: {json.dumps(result['response_data'], indent=2)}")

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("🎯 TETHYS TOGGLE FUNCTIONALITY TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for r in self.results if r.get('success', False))
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        # Performance summary
        response_times = [r.get('response_time', 0) for r in self.results if 'response_time' in r]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"   Average Response Time: {avg_time:.3f}s")
            print(f"   Maximum Response Time: {max_time:.3f}s")
            print(f"   All responses within 5s limit: {'✅ YES' if max_time <= 5.0 else '❌ NO'}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.results, 1):
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            endpoint = result.get('endpoint', 'Unknown')
            method = result.get('method', 'Unknown')
            time_str = f"{result.get('response_time', 0):.3f}s"
            print(f"   {i}. {method} {endpoint} - {status} ({time_str})")
        
        # Final assessment
        print(f"\n🎯 TETHYS TOGGLE FUNCTIONALITY:")
        if success_rate == 100:
            print("   ✅ FULLY FUNCTIONAL - All toggle operations working correctly")
        elif success_rate >= 80:
            print("   ⚠️  MOSTLY FUNCTIONAL - Minor issues detected")
        else:
            print("   ❌ CRITICAL ISSUES - Toggle functionality not working properly")
        
        print(f"\n⏱️  PERFORMANCE:")
        if max_time <= 5.0:
            print("   ✅ EXCELLENT - All endpoints respond within 5 second requirement")
        else:
            print("   ❌ TIMEOUT ISSUES - Some endpoints exceed 5 second limit")

def main():
    """Main test execution"""
    print("🚀 Starting Tethys Toggle Functionality Test...")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BASE_URL}")
    
    tester = TethysToggleTester()
    tester.run_tethys_toggle_test()
    
    print(f"\n✅ Test completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()