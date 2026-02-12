#!/usr/bin/env python3
"""
Hardened Hidden Gem Prediction Testing
=====================================
Comprehensive testing for hardened gem prediction endpoints with focus on:
- POST /api/gems/predict with new response structure (llm_enhanced, llm_status, model_version)
- POST /api/gems/scan endpoint functionality
- GET /api/gems/top endpoint with top_gems and potential_gems arrays
- GET /api/gems/history, training-status, deep-training-status, backtest/status
- Verify adaptive-strategy endpoints still work
- Test graceful handling when no market data available
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

# Use production URL from environment
BACKEND_URL = "https://filecheck-4.preview.emergentagent.com/api"
print(f"🔗 Testing Hardened Hidden Gem Prediction at: {BACKEND_URL}")

class HardenedGemTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'HardenedGemTester/1.0'
        })
        self.results = []
        self.failed_tests = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response_data': response_data
        })
        
        if not success:
            self.failed_tests.append({
                'test': test_name,
                'details': details,
                'response_data': response_data
            })
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None, timeout: int = 30) -> tuple:
        """Make HTTP request and return (success, status_code, data)"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(url, params=params, timeout=timeout)
            elif method == "POST":
                response = self.session.post(url, json=data, params=params, timeout=timeout)
            else:
                return False, 0, f"Unsupported method: {method}"
            
            if response.status_code == 200:
                try:
                    return True, response.status_code, response.json()
                except json.JSONDecodeError:
                    return True, response.status_code, response.text
            else:
                return False, response.status_code, response.text
                
        except requests.exceptions.RequestException as e:
            return False, 0, str(e)
    
    def test_gems_predict_endpoint(self):
        """Test POST /api/gems/predict with new hardened structure"""
        print("\n💎 Testing Hardened Gem Prediction (7 days)...")
        
        success, status, data = self.make_request(
            "POST", 
            "/gems/predict",
            data={"days_ahead": 7}
        )
        
        if not success:
            self.log_result("Gems Predict", False, f"HTTP {status}: {data}")
            return None
        
        # Verify NEW required fields as per review request
        required_fields = ["prediction_period", "generated_at", "predictions", "methodology", 
                          "llm_enhanced", "llm_status", "model_version"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_result("Gems Predict", False, f"Missing NEW fields: {missing_fields}")
            return None
        
        # Verify specific field values as per review request
        prediction_period = data.get("prediction_period")
        if prediction_period != "next_7_days":
            self.log_result("Gems Predict", False, f"Wrong prediction_period: {prediction_period}, expected 'next_7_days'")
            return None
        
        # Check generated_at is ISO timestamp
        generated_at = data.get("generated_at")
        try:
            datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        except:
            self.log_result("Gems Predict", False, f"Invalid generated_at timestamp: {generated_at}")
            return None
        
        # Check llm_enhanced is boolean
        llm_enhanced = data.get("llm_enhanced")
        if not isinstance(llm_enhanced, bool):
            self.log_result("Gems Predict", False, f"llm_enhanced not boolean: {llm_enhanced}")
            return None
        
        # Check llm_status is valid (per review request: "no_api_key", "skipped_no_candidates", "error: ...", or "success")
        llm_status = data.get("llm_status")
        valid_statuses = ["no_api_key", "skipped_no_candidates", "success", "attempting", "unavailable", "empty_response"]
        if not llm_status or (not llm_status.startswith("error:") and llm_status not in valid_statuses):
            self.log_result("Gems Predict", False, f"Invalid llm_status: {llm_status}")
            return None
        
        # Check model_version matches expected value
        model_version = data.get("model_version")
        if model_version != "v2.0_optimized_92pct":
            self.log_result("Gems Predict", False, f"Wrong model_version: {model_version}, expected 'v2.0_optimized_92pct'")
            return None
        
        # Check predictions array exists (can be empty in test environment)
        predictions = data.get("predictions")
        if not isinstance(predictions, list):
            self.log_result("Gems Predict", False, f"Predictions not array: {type(predictions)}")
            return None
        
        # Check methodology exists
        methodology = data.get("methodology")
        if not methodology or len(methodology) < 20:
            self.log_result("Gems Predict", False, f"Methodology too short or missing")
            return None
        
        # Review request notes: In test environment, scan may return 0 gems, llm_status may be "skipped_no_candidates" - this is CORRECT
        gems_count = len(predictions)
        
        self.log_result(
            "Gems Predict", 
            True, 
            f"✅ ALL NEW FIELDS present: {gems_count} predictions, llm_enhanced={llm_enhanced}, llm_status='{llm_status}', model='{model_version}'"
        )
        
        return data
    
    def test_gems_scan_endpoint(self):
        """Test POST /api/gems/scan with {"limit": 10}"""
        print("\n🔍 Testing Gem Scan Endpoint...")
        
        success, status, data = self.make_request(
            "POST", 
            "/gems/scan",
            data={"limit": 10}
        )
        
        if not success:
            self.log_result("Gems Scan", False, f"HTTP {status}: {data}")
            return None
        
        # Check basic response structure (actual response has different field names)
        required_fields = ["success", "gems", "scan_time"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_result("Gems Scan", False, f"Missing fields: {missing_fields}")
            return None
        
        # Check scan_time is valid timestamp
        scan_time = data.get("scan_time")
        try:
            datetime.fromisoformat(scan_time.replace("Z", "+00:00"))
        except:
            self.log_result("Gems Scan", False, f"Invalid scan_time: {scan_time}")
            return None
        
        gems = data.get("gems", [])
        gems_found = data.get("gems_found", 0)  # Use actual field name
        
        # Verify gems_found matches gems array length
        if gems_found != len(gems):
            self.log_result("Gems Scan", False, f"gems_found {gems_found} doesn't match gems array length {len(gems)}")
            return None
        
        self.log_result(
            "Gems Scan", 
            True, 
            f"Scan successful: {gems_found} gems found (expected 0 in test env with no live data)"
        )
        
        return data
    
    def test_gems_top_endpoint(self):
        """Test GET /api/gems/top - should return top_gems and potential_gems arrays"""
        print("\n🏆 Testing Top Gems Endpoint...")
        
        success, status, data = self.make_request("GET", "/gems/top")
        
        if not success:
            self.log_result("Gems Top", False, f"HTTP {status}: {data}")
            return None
        
        # Check required fields per review request
        required_fields = ["top_gems", "potential_gems", "generated_at"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_result("Gems Top", False, f"Missing fields: {missing_fields}")
            return None
        
        top_gems = data.get("top_gems", [])
        potential_gems = data.get("potential_gems", [])
        
        # Verify they are arrays (can be empty)
        if not isinstance(top_gems, list):
            self.log_result("Gems Top", False, f"top_gems not array: {type(top_gems)}")
            return None
        
        if not isinstance(potential_gems, list):
            self.log_result("Gems Top", False, f"potential_gems not array: {type(potential_gems)}")
            return None
        
        # Check generated_at timestamp
        generated_at = data.get("generated_at")
        try:
            datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        except:
            self.log_result("Gems Top", False, f"Invalid generated_at: {generated_at}")
            return None
        
        self.log_result(
            "Gems Top", 
            True, 
            f"✅ CORRECT structure: top_gems({len(top_gems)}), potential_gems({len(potential_gems)})"
        )
        
        return data
    
    def test_gems_history_endpoint(self):
        """Test GET /api/gems/history"""
        print("\n📈 Testing Gem History Endpoint...")
        
        success, status, data = self.make_request("GET", "/gems/history")
        
        if not success:
            self.log_result("Gems History", False, f"HTTP {status}: {data}")
            return None
        
        # Check response structure
        required_fields = ["count", "predictions"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_result("Gems History", False, f"Missing fields: {missing_fields}")
            return None
        
        count = data.get("count", 0)
        predictions = data.get("predictions", [])
        
        if count != len(predictions):
            self.log_result("Gems History", False, f"Count {count} doesn't match predictions length {len(predictions)}")
            return None
        
        self.log_result(
            "Gems History", 
            True, 
            f"History retrieved: {count} predictions"
        )
        
        return data
    
    def test_gems_training_status_endpoint(self):
        """Test GET /api/gems/training-status"""
        print("\n📊 Testing Gem Training Status...")
        
        success, status, data = self.make_request("GET", "/gems/training-status")
        
        if not success:
            self.log_result("Gems Training Status", False, f"HTTP {status}: {data}")
            return None
        
        # Should return training status info (structure may vary)
        self.log_result(
            "Gems Training Status", 
            True, 
            f"Training status retrieved: {list(data.keys())}"
        )
        
        return data
    
    def test_gems_deep_training_status_endpoint(self):
        """Test GET /api/gems/deep-training-status"""
        print("\n🧠 Testing Deep Training Status...")
        
        success, status, data = self.make_request("GET", "/gems/deep-training-status")
        
        if not success:
            self.log_result("Gems Deep Training Status", False, f"HTTP {status}: {data}")
            return None
        
        # Should return deep training status info
        self.log_result(
            "Gems Deep Training Status", 
            True, 
            f"Deep training status retrieved: {list(data.keys())}"
        )
        
        return data
    
    def test_gems_backtest_status_endpoint(self):
        """Test GET /api/gems/backtest/status"""
        print("\n⚡ Testing Gem Backtest Status...")
        
        success, status, data = self.make_request("GET", "/gems/backtest/status")
        
        if not success:
            self.log_result("Gems Backtest Status", False, f"HTTP {status}: {data}")
            return None
        
        # Should return backtest status info
        self.log_result(
            "Gems Backtest Status", 
            True, 
            f"Backtest status retrieved: {list(data.keys())}"
        )
        
        return data
    
    def test_adaptive_strategy_endpoints(self):
        """Test that adaptive strategy endpoints still work as requested"""
        print("\n🔄 Testing Adaptive Strategy Endpoints (Still Working)...")
        
        # Test event-coverage-stats
        success, status, data = self.make_request("GET", "/adaptive-strategy/event-coverage-stats")
        
        if success:
            self.log_result(
                "Adaptive: Event Coverage Stats", 
                True, 
                f"Coverage stats working: {data.get('coverage_percentage', 'N/A')}% coverage"
            )
        else:
            self.log_result("Adaptive: Event Coverage Stats", False, f"HTTP {status}: {data}")
        
        # Test predict-events with 60 days
        success, status, data = self.make_request(
            "POST", 
            "/adaptive-strategy/predict-events",
            data={"days_ahead": 60}
        )
        
        if success:
            events_count = len(data.get("events", []))
            self.log_result(
                "Adaptive: Predict Events", 
                True, 
                f"Event prediction working: {events_count} events for 60 days"
            )
        else:
            self.log_result("Adaptive: Predict Events", False, f"HTTP {status}: {data}")
    
    def test_error_handling(self):
        """Test graceful error handling when no market data available"""
        print("\n🛡️ Testing Error Handling & Edge Cases...")
        
        # Test predict with invalid days_ahead
        success, status, data = self.make_request(
            "POST", 
            "/gems/predict",
            data={"days_ahead": -1}
        )
        
        # Should either work gracefully or return proper error
        if success:
            self.log_result(
                "Error Handling: Invalid Days", 
                True, 
                f"Graceful handling of invalid input"
            )
        else:
            # Proper error response is also acceptable
            if status in [400, 422]:
                self.log_result(
                    "Error Handling: Invalid Days", 
                    True, 
                    f"Proper error response: {status}"
                )
            else:
                self.log_result("Error Handling: Invalid Days", False, f"Unexpected error: {status}")
        
        # Test scan with very high limit
        success, status, data = self.make_request(
            "POST", 
            "/gems/scan",
            data={"limit": 10000}
        )
        
        if success:
            self.log_result(
                "Error Handling: High Limit", 
                True, 
                f"Graceful handling of high limit"
            )
        else:
            if status in [400, 422, 429]:
                self.log_result(
                    "Error Handling: High Limit", 
                    True, 
                    f"Proper rate limiting/validation: {status}"
                )
            else:
                self.log_result("Error Handling: High Limit", False, f"Unexpected error: {status}")
    
    def run_all_tests(self):
        """Run comprehensive Hardened Hidden Gem Prediction tests"""
        print("=" * 80)
        print("🚀 HARDENED HIDDEN GEM PREDICTION TESTING")
        print("=" * 80)
        
        # Core gem prediction endpoints
        predict_data = self.test_gems_predict_endpoint()
        scan_data = self.test_gems_scan_endpoint()
        top_data = self.test_gems_top_endpoint()
        history_data = self.test_gems_history_endpoint()
        
        # Status endpoints
        training_status = self.test_gems_training_status_endpoint()
        deep_training_status = self.test_gems_deep_training_status_endpoint()
        backtest_status = self.test_gems_backtest_status_endpoint()
        
        # Verify adaptive strategy still works
        self.test_adaptive_strategy_endpoints()
        
        # Error handling
        self.test_error_handling()
        
        # Results Summary
        print("\n" + "=" * 80)
        print("📊 HARDENED HIDDEN GEM PREDICTION TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"✅ Passed Tests: {passed_tests}")
        print(f"❌ Failed Tests: {failed_tests}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS DETAILS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure['test']}: {failure['details']}")
        
        # Feature Analysis
        print("\n" + "=" * 50)
        print("💎 HARDENED GEM PREDICTION ANALYSIS")
        print("=" * 50)
        
        if predict_data:
            llm_enhanced = predict_data.get("llm_enhanced")
            llm_status = predict_data.get("llm_status")
            model_version = predict_data.get("model_version")
            predictions_count = len(predict_data.get("predictions", []))
            
            print(f"🤖 LLM Enhanced: {llm_enhanced}")
            print(f"📡 LLM Status: {llm_status}")
            print(f"🔧 Model Version: {model_version}")
            print(f"💎 Predictions Generated: {predictions_count}")
            
            # As per review request: no live market data expected, so 0 gems is correct
            if predictions_count == 0 and llm_status == "skipped_no_candidates":
                print("✅ CORRECT: No gems found due to no live market data (test environment)")
            elif predictions_count > 0:
                print("✅ EXCELLENT: Predictions generated despite test environment")
        
        if scan_data:
            gems_found = len(scan_data.get("gems", []))
            print(f"🔍 Gems Scanned: {gems_found}")
        
        if top_data:
            top_count = len(top_data.get("top_gems", []))
            potential_count = len(top_data.get("potential_gems", []))
            print(f"🏆 Top Gems: {top_count}")
            print(f"⭐ Potential Gems: {potential_count}")
        
        # Final Assessment
        critical_features_working = True
        
        # Check if new required fields are present
        if predict_data:
            required_new_fields = ["llm_enhanced", "llm_status", "model_version"]
            missing_critical = [f for f in required_new_fields if f not in predict_data]
            if missing_critical:
                critical_features_working = False
                print(f"❌ CRITICAL: Missing new fields: {missing_critical}")
        else:
            critical_features_working = False
        
        if success_rate >= 90 and critical_features_working:
            print(f"\n🎉 EXCELLENT: Hardened Hidden Gem Prediction working perfectly!")
        elif success_rate >= 80 and critical_features_working:
            print(f"\n✅ GOOD: Hardened Hidden Gem Prediction mostly working well")
        elif success_rate >= 70:
            print(f"\n⚠️  MODERATE: Hardened Hidden Gem Prediction needs some fixes")
        else:
            print(f"\n❌ POOR: Hardened Hidden Gem Prediction needs significant work")
        
        print("\n" + "=" * 80)
        return success_rate >= 80 and critical_features_working


if __name__ == "__main__":
    tester = HardenedGemTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎯 Hardened Hidden Gem Prediction testing completed successfully!")
        sys.exit(0)
    else:
        print("⚠️ Hardened Hidden Gem Prediction testing completed with issues.")
        sys.exit(1)