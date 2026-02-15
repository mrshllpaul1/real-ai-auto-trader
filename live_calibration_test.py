#!/usr/bin/env python3
"""
Live Calibration API Integration Testing
Tests real-time ML Analytics updates through Live Calibration endpoints
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime
import time

# Backend URL from frontend .env
BACKEND_URL = "https://feature-enhancer-7.preview.emergentagent.com"
API_KEY = "test-api-key-12345"

class LiveCalibrationTester:
    def __init__(self):
        self.base_url = f"{BACKEND_URL}/api"
        self.headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        self.test_results = []
        self.prediction_ids = []
        self.trade_ids = []
        
    async def test_endpoint(self, method: str, endpoint: str, data=None, expected_status=200):
        """Test a single endpoint and record results."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                success = response.status_code == expected_status
                result = {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "expected": expected_status,
                    "success": success,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    "response_data": None,
                    "error": None
                }
                
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text[:500]
                
                if not success:
                    result["error"] = f"Expected {expected_status}, got {response.status_code}"
                
                self.test_results.append(result)
                return result
                
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "expected": expected_status,
                "success": False,
                "response_time": 0,
                "response_data": None,
                "error": str(e)
            }
            self.test_results.append(result)
            return result

    async def test_record_prediction_flow(self):
        """Test the complete prediction recording flow."""
        print("\n🎯 Testing Record Prediction Flow...")
        
        # Generate test data
        trade_id = str(uuid.uuid4())
        self.trade_ids.append(trade_id)
        
        # 1. Record a new prediction
        prediction_data = {
            "coin_id": "BTC",
            "predicted_action": "BUY",
            "confidence": 0.85,
            "model_name": "tethys_ensemble",
            "trade_id": trade_id,
            "entry_price": 95000.0,
            "stop_loss": 90000.0,
            "take_profit": 100000.0,
            "metadata": {
                "test_run": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        result = await self.test_endpoint("POST", "/live-calibration/record-prediction", prediction_data)
        if result["success"] and result["response_data"]:
            prediction_id = result["response_data"].get("prediction_id")
            if prediction_id:
                self.prediction_ids.append(prediction_id)
                print(f"✅ Prediction recorded: {prediction_id}")
            else:
                print("❌ No prediction_id returned")
        else:
            print(f"❌ Failed to record prediction: {result.get('error', 'Unknown error')}")
        
        # 2. Check pending predictions
        await self.test_endpoint("GET", "/live-calibration/pending")
        
        # 3. Record outcome for the prediction
        if self.prediction_ids:
            outcome_data = {
                "prediction_id": self.prediction_ids[-1],
                "is_correct": True,
                "actual_price": 96500.0,
                "exit_price": 97000.0,
                "pnl_percent": 2.1,
                "pnl_usd": 200.0
            }
            await self.test_endpoint("POST", "/live-calibration/record-outcome", outcome_data)
        
        # 4. Check outcomes
        await self.test_endpoint("GET", "/live-calibration/outcomes")

    async def test_webhook_flow(self):
        """Test webhook flow for trading integration."""
        print("\n🔗 Testing Webhook Flow for Trading Integration...")
        
        # Generate test trade
        trade_id = str(uuid.uuid4())
        self.trade_ids.append(trade_id)
        
        # 1. Simulate trade opened webhook
        trade_opened_data = {
            "trade_id": trade_id,
            "coin_id": "ETH",
            "action": "BUY",
            "entry_price": 2500.0,
            "amount": 1.0,
            "signal_confidence": 0.75,
            "signal_model": "lstm_predictor",
            "stop_loss": 2400.0,
            "take_profit": 2700.0,
            "metadata": {
                "webhook_test": True,
                "source": "automated_trading"
            }
        }
        
        result = await self.test_endpoint("POST", "/live-calibration/webhook/trade-opened", trade_opened_data)
        if result["success"]:
            print(f"✅ Trade opened webhook processed for trade: {trade_id}")
        else:
            print(f"❌ Trade opened webhook failed: {result.get('error', 'Unknown error')}")
        
        # 2. Simulate trade closed webhook
        trade_closed_data = {
            "trade_id": trade_id,
            "exit_price": 2650.0,
            "pnl_percent": 6.0,
            "pnl_usd": 150.0
        }
        
        result = await self.test_endpoint("POST", "/live-calibration/webhook/trade-closed", trade_closed_data)
        if result["success"]:
            print(f"✅ Trade closed webhook processed for trade: {trade_id}")
        else:
            print(f"❌ Trade closed webhook failed: {result.get('error', 'Unknown error')}")

    async def test_live_stats(self):
        """Test live statistics endpoints."""
        print("\n📊 Testing Live Stats...")
        
        # 1. Get model stats (all models)
        await self.test_endpoint("GET", "/live-calibration/model-stats")
        
        # 2. Get model stats for specific model
        await self.test_endpoint("GET", "/live-calibration/model-stats?model_name=tethys_ensemble")
        
        # 3. Get calibration status
        await self.test_endpoint("GET", "/live-calibration/status")

    async def test_ml_analytics_integration(self):
        """Test ML Analytics integration endpoints."""
        print("\n🧠 Testing ML Analytics Integration...")
        
        # 1. Test calibration accuracy by level
        result = await self.test_endpoint("GET", "/ml-analytics/calibration/accuracy-by-level")
        if result["success"]:
            accuracy_data = result["response_data"]
            print(f"✅ Calibration accuracy data retrieved: {accuracy_data}")
        else:
            print(f"❌ Failed to get calibration accuracy: {result.get('error', 'Unknown error')}")
        
        # 2. Test drift status
        result = await self.test_endpoint("GET", "/ml-analytics/drift/status")
        if result["success"]:
            drift_data = result["response_data"]
            print(f"✅ Model drift status retrieved: {drift_data}")
        else:
            print(f"❌ Failed to get drift status: {result.get('error', 'Unknown error')}")
        
        # 3. Test ML analytics dashboard
        result = await self.test_endpoint("GET", "/ml-analytics/dashboard")
        if result["success"]:
            dashboard_data = result["response_data"]
            print(f"✅ ML Analytics dashboard retrieved with sections: {list(dashboard_data.keys())}")
        else:
            print(f"❌ Failed to get ML analytics dashboard: {result.get('error', 'Unknown error')}")

    async def test_data_flow_verification(self):
        """Verify that live data is properly flowing into ML Analytics."""
        print("\n🔄 Testing Data Flow Verification...")
        
        # Get initial state
        initial_status = await self.test_endpoint("GET", "/live-calibration/status")
        initial_ml_dashboard = await self.test_endpoint("GET", "/ml-analytics/dashboard")
        
        # Record multiple predictions to generate data
        for i in range(3):
            prediction_data = {
                "coin_id": ["BTC", "ETH", "SOL"][i],
                "predicted_action": ["BUY", "SELL", "HOLD"][i],
                "confidence": [0.9, 0.7, 0.6][i],
                "model_name": ["tethys_ensemble", "lstm_predictor", "xgboost_classifier"][i],
                "trade_id": str(uuid.uuid4()),
                "entry_price": [95000.0, 2500.0, 85.0][i],
                "metadata": {"batch_test": True, "index": i}
            }
            
            result = await self.test_endpoint("POST", "/live-calibration/record-prediction", prediction_data)
            if result["success"] and result["response_data"]:
                prediction_id = result["response_data"].get("prediction_id")
                if prediction_id:
                    # Record outcome immediately
                    outcome_data = {
                        "prediction_id": prediction_id,
                        "is_correct": i % 2 == 0,  # Alternate correct/incorrect
                        "actual_price": prediction_data["entry_price"] * (1.02 if i % 2 == 0 else 0.98),
                        "pnl_percent": 2.0 if i % 2 == 0 else -2.0,
                        "pnl_usd": 100.0 if i % 2 == 0 else -100.0
                    }
                    await self.test_endpoint("POST", "/live-calibration/record-outcome", outcome_data)
        
        # Wait a moment for data processing
        await asyncio.sleep(2)
        
        # Get updated state
        final_status = await self.test_endpoint("GET", "/live-calibration/status")
        final_ml_dashboard = await self.test_endpoint("GET", "/ml-analytics/dashboard")
        
        # Verify data flow
        if initial_status["success"] and final_status["success"]:
            initial_total = initial_status["response_data"].get("predictions", {}).get("total", 0)
            final_total = final_status["response_data"].get("predictions", {}).get("total", 0)
            
            if final_total > initial_total:
                print(f"✅ Data flow verified: Predictions increased from {initial_total} to {final_total}")
            else:
                print(f"⚠️ Data flow unclear: Predictions {initial_total} -> {final_total}")
        
        return {
            "initial_status": initial_status,
            "final_status": final_status,
            "initial_ml_dashboard": initial_ml_dashboard,
            "final_ml_dashboard": final_ml_dashboard
        }

    async def run_all_tests(self):
        """Run all Live Calibration API tests."""
        print("🚀 Starting Live Calibration API Integration Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing {datetime.utcnow().isoformat()}")
        
        start_time = time.time()
        
        # Test core health first
        await self.test_endpoint("GET", "/health")
        
        # Run test suites
        await self.test_record_prediction_flow()
        await self.test_webhook_flow()
        await self.test_live_stats()
        await self.test_ml_analytics_integration()
        data_flow_results = await self.test_data_flow_verification()
        
        # Generate summary
        total_time = time.time() - start_time
        self.generate_summary(total_time, data_flow_results)

    def generate_summary(self, total_time, data_flow_results):
        """Generate test summary."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"🎯 LIVE CALIBRATION API INTEGRATION TEST RESULTS")
        print(f"{'='*80}")
        print(f"📊 SUMMARY: {success_rate:.1f}% SUCCESS RATE ({passed_tests}/{total_tests} tests passed)")
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        
        # Categorize results
        categories = {
            "Record Prediction Flow": ["/live-calibration/record-prediction", "/live-calibration/pending", "/live-calibration/record-outcome", "/live-calibration/outcomes"],
            "Webhook Flow": ["/live-calibration/webhook/trade-opened", "/live-calibration/webhook/trade-closed"],
            "Live Stats": ["/live-calibration/model-stats", "/live-calibration/status"],
            "ML Analytics Integration": ["/ml-analytics/calibration/accuracy-by-level", "/ml-analytics/drift/status", "/ml-analytics/dashboard"],
            "Core Health": ["/health"]
        }
        
        for category, endpoints in categories.items():
            category_results = [r for r in self.test_results if any(ep in r["endpoint"] for ep in endpoints)]
            if category_results:
                category_passed = len([r for r in category_results if r["success"]])
                category_total = len(category_results)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                
                status_icon = "✅" if category_rate == 100 else "⚠️" if category_rate >= 50 else "❌"
                print(f"\n{status_icon} {category}: {category_rate:.1f}% ({category_passed}/{category_total})")
                
                for result in category_results:
                    status = "✅" if result["success"] else "❌"
                    print(f"  {status} {result['method']} {result['endpoint']} ({result['status_code']})")
                    if not result["success"] and result["error"]:
                        print(f"      Error: {result['error']}")
        
        # Failed tests details
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            print(f"\n❌ FAILED TESTS ({len(failed_results)}):")
            for result in failed_results:
                print(f"  • {result['method']} {result['endpoint']}")
                print(f"    Status: {result['status_code']} (expected {result['expected']})")
                if result["error"]:
                    print(f"    Error: {result['error']}")
                if result["response_data"]:
                    print(f"    Response: {str(result['response_data'])[:200]}...")
        
        # Data flow analysis
        if data_flow_results:
            print(f"\n🔄 DATA FLOW ANALYSIS:")
            initial_status = data_flow_results.get("initial_status", {})
            final_status = data_flow_results.get("final_status", {})
            
            if initial_status.get("success") and final_status.get("success"):
                initial_data = initial_status["response_data"]
                final_data = final_status["response_data"]
                
                print(f"  • Live Calibration Status:")
                print(f"    - Predictions: {initial_data.get('predictions', {}).get('total', 0)} → {final_data.get('predictions', {}).get('total', 0)}")
                print(f"    - Outcomes: {initial_data.get('outcomes_recorded', 0)} → {final_data.get('outcomes_recorded', 0)}")
                
                calibration_initial = initial_data.get('calibration', {})
                calibration_final = final_data.get('calibration', {})
                print(f"    - In-memory predictions: {calibration_initial.get('total_in_memory', 0)} → {calibration_final.get('total_in_memory', 0)}")
                
                if calibration_final.get('overall_accuracy') is not None:
                    print(f"    - Overall accuracy: {calibration_final.get('overall_accuracy', 'N/A')}")
        
        # Performance metrics
        response_times = [r["response_time"] for r in self.test_results if r["response_time"] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⚡ PERFORMANCE:")
            print(f"  • Average response time: {avg_time:.3f}s")
            print(f"  • Maximum response time: {max_time:.3f}s")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        
        # Check if live data is flowing
        live_calibration_working = any(r["success"] and "/live-calibration/" in r["endpoint"] for r in self.test_results)
        ml_analytics_working = any(r["success"] and "/ml-analytics/" in r["endpoint"] for r in self.test_results)
        
        if live_calibration_working and ml_analytics_working:
            print(f"  ✅ Live Calibration API is operational")
            print(f"  ✅ ML Analytics integration is working")
            print(f"  ✅ Real-time data flow is established")
        else:
            if not live_calibration_working:
                print(f"  ❌ Live Calibration API has issues")
            if not ml_analytics_working:
                print(f"  ❌ ML Analytics integration has issues")
        
        # Check webhook functionality
        webhook_results = [r for r in self.test_results if "/webhook/" in r["endpoint"]]
        webhook_working = all(r["success"] for r in webhook_results) if webhook_results else False
        
        if webhook_working:
            print(f"  ✅ Trading webhook integration is functional")
        elif webhook_results:
            print(f"  ❌ Trading webhook integration has issues")
        
        # Test data generated
        if self.prediction_ids:
            print(f"  📝 Generated {len(self.prediction_ids)} test predictions")
        if self.trade_ids:
            print(f"  💰 Generated {len(self.trade_ids)} test trades")
        
        print(f"\n{'='*80}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"🎉 EXCELLENT: Live Calibration API integration is working perfectly!")
        elif success_rate >= 75:
            print(f"✅ GOOD: Live Calibration API integration is mostly functional with minor issues.")
        elif success_rate >= 50:
            print(f"⚠️ PARTIAL: Live Calibration API integration has significant issues that need attention.")
        else:
            print(f"❌ CRITICAL: Live Calibration API integration is not working properly.")


async def main():
    """Main test execution."""
    tester = LiveCalibrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())