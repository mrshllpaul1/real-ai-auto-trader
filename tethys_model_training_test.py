#!/usr/bin/env python3
"""
Tethys Training and Model Training API Testing
==============================================
Testing specific endpoints requested in the review:

1. Tethys Training Status endpoints
2. Individual Model Training endpoints  
3. Model Status Persistence
4. Other important endpoints

Backend URL: https://fast-analyzer.preview.emergentagent.com/api
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://fast-analyzer.preview.emergentagent.com/api"

class TethysModelTrainingTester:
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
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time": f"{response_time:.3f}s",
                "expected_status": expected_status,
                "success": response.status_code == expected_status,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add response data for successful requests
            if response.status_code == 200:
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text[:500]
            else:
                result["error"] = response.text[:500]
            
            return result
            
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": "ERROR",
                "response_time": f"{time.time() - start_time:.3f}s",
                "expected_status": expected_status,
                "success": False,
                "description": description,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def test_tethys_training_status(self):
        """Test Tethys Training Status endpoints"""
        print("\n🔍 TESTING TETHYS TRAINING STATUS ENDPOINTS")
        print("=" * 60)
        
        # 1. GET /api/tethys-train/status - Should return status with is_active field
        result = self.test_endpoint(
            "GET", 
            "/tethys-train/status",
            description="Get Tethys training status - should include is_active field"
        )
        self.results.append(result)
        print(f"✓ GET /tethys-train/status: {result['status_code']} ({result['response_time']})")
        
        if result['success'] and 'response_data' in result:
            data = result['response_data']
            has_is_active = 'is_active' in data
            print(f"  - Contains is_active field: {'✓' if has_is_active else '✗'}")
            if has_is_active:
                print(f"  - is_active value: {data['is_active']}")
            
            # Check for other expected fields
            expected_fields = ['is_training', 'current_episode', 'total_episodes', 'progress_pct']
            for field in expected_fields:
                if field in data:
                    print(f"  - {field}: {data[field]}")
        
        return result

    def test_tethys_training_start_stop(self):
        """Test Tethys Training Start/Stop functionality"""
        print("\n🚀 TESTING TETHYS TRAINING START/STOP")
        print("=" * 60)
        
        # 2. POST /api/tethys-train/start - Should start Tethys training
        start_result = self.test_endpoint(
            "POST", 
            "/tethys-train/start",
            data={"episodes": 10, "symbol": "BTC/USD"},
            description="Start Tethys training with minimal episodes"
        )
        self.results.append(start_result)
        print(f"✓ POST /tethys-train/start: {start_result['status_code']} ({start_result['response_time']})")
        
        if start_result['success'] and 'response_data' in start_result:
            data = start_result['response_data']
            print(f"  - Status: {data.get('status', 'unknown')}")
            if 'config' in data:
                print(f"  - Episodes: {data['config'].get('episodes', 'unknown')}")
        
        # Wait a moment for training to potentially start
        time.sleep(2)
        
        # 3. GET /api/tethys-train/status - Should show updated status
        status_result = self.test_endpoint(
            "GET", 
            "/tethys-train/status",
            description="Check status after starting training"
        )
        self.results.append(status_result)
        print(f"✓ GET /tethys-train/status (after start): {status_result['status_code']} ({status_result['response_time']})")
        
        if status_result['success'] and 'response_data' in status_result:
            data = status_result['response_data']
            print(f"  - is_active: {data.get('is_active', 'unknown')}")
            print(f"  - is_training: {data.get('is_training', 'unknown')}")
            print(f"  - Progress: {data.get('progress_pct', 0)}%")
        
        return start_result, status_result

    def test_individual_model_training(self):
        """Test Individual Model Training endpoints"""
        print("\n🤖 TESTING INDIVIDUAL MODEL TRAINING")
        print("=" * 60)
        
        # 4. GET /api/training/models-status - Should return status for all 6 models
        models_status_result = self.test_endpoint(
            "GET", 
            "/training/models-status",
            description="Get status for all models (should show 6 models)"
        )
        self.results.append(models_status_result)
        print(f"✓ GET /training/models-status: {models_status_result['status_code']} ({models_status_result['response_time']})")
        
        if models_status_result['success'] and 'response_data' in models_status_result:
            data = models_status_result['response_data']
            model_count = len(data)
            print(f"  - Number of models: {model_count}")
            
            expected_models = ["historical", "gem_ml_dl", "mtf", "xgboost", "lstm_gru", "finrl"]
            for model in expected_models:
                if model in data:
                    model_data = data[model]
                    is_trained = model_data.get('is_trained', False)
                    status = model_data.get('status', 'unknown')
                    print(f"  - {model}: trained={is_trained}, status={status}")
        
        # 5. POST /api/training/train-model - Should start training for historical model
        train_model_result = self.test_endpoint(
            "POST", 
            "/training/train-model",
            data={"model_name": "historical", "coins": ["bitcoin"]},
            description="Start training historical model with bitcoin"
        )
        self.results.append(train_model_result)
        print(f"✓ POST /training/train-model: {train_model_result['status_code']} ({train_model_result['response_time']})")
        
        if train_model_result['success'] and 'response_data' in train_model_result:
            data = train_model_result['response_data']
            print(f"  - Status: {data.get('status', 'unknown')}")
            print(f"  - Model: {data.get('model_name', 'unknown')}")
            print(f"  - Task ID: {data.get('task_id', 'unknown')}")
        
        # Wait a moment for training to start
        time.sleep(3)
        
        # 6. GET /api/training/models-status - Should show historical model in training/completed
        updated_status_result = self.test_endpoint(
            "GET", 
            "/training/models-status",
            description="Check models status after starting historical training"
        )
        self.results.append(updated_status_result)
        print(f"✓ GET /training/models-status (after training): {updated_status_result['status_code']} ({updated_status_result['response_time']})")
        
        if updated_status_result['success'] and 'response_data' in updated_status_result:
            data = updated_status_result['response_data']
            if 'historical' in data:
                historical_data = data['historical']
                print(f"  - Historical model status: {historical_data.get('status', 'unknown')}")
                print(f"  - Historical model trained: {historical_data.get('is_trained', False)}")
        
        return models_status_result, train_model_result, updated_status_result

    def test_model_status_persistence(self):
        """Test Model Status Persistence"""
        print("\n💾 TESTING MODEL STATUS PERSISTENCE")
        print("=" * 60)
        
        # 7. GET /api/training/model-status/historical - Should show is_trained status
        historical_status_result = self.test_endpoint(
            "GET", 
            "/training/model-status/historical",
            description="Get specific status for historical model"
        )
        self.results.append(historical_status_result)
        print(f"✓ GET /training/model-status/historical: {historical_status_result['status_code']} ({historical_status_result['response_time']})")
        
        if historical_status_result['success'] and 'response_data' in historical_status_result:
            data = historical_status_result['response_data']
            is_trained = data.get('is_trained', False)
            status = data.get('status', 'unknown')
            accuracy = data.get('accuracy', 0)
            trained_at = data.get('trained_at', 'never')
            
            print(f"  - is_trained: {is_trained}")
            print(f"  - status: {status}")
            print(f"  - accuracy: {accuracy}%")
            print(f"  - trained_at: {trained_at}")
        
        return historical_status_result

    def test_other_important_endpoints(self):
        """Test Other Important Endpoints"""
        print("\n🔧 TESTING OTHER IMPORTANT ENDPOINTS")
        print("=" * 60)
        
        # 8. GET /api/training/status - General training status
        training_status_result = self.test_endpoint(
            "GET", 
            "/training/status",
            description="Get general training status"
        )
        self.results.append(training_status_result)
        print(f"✓ GET /training/status: {training_status_result['status_code']} ({training_status_result['response_time']})")
        
        if training_status_result['success'] and 'response_data' in training_status_result:
            data = training_status_result['response_data']
            print(f"  - Response keys: {list(data.keys())}")
        
        # 9. GET /api/health - Health check
        health_result = self.test_endpoint(
            "GET", 
            "/health",
            description="Health check endpoint"
        )
        self.results.append(health_result)
        print(f"✓ GET /health: {health_result['status_code']} ({health_result['response_time']})")
        
        if health_result['success'] and 'response_data' in health_result:
            data = health_result['response_data']
            print(f"  - Status: {data.get('status', 'unknown')}")
            print(f"  - Database: {data.get('database', 'unknown')}")
        
        return training_status_result, health_result

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🎯 TETHYS TRAINING AND MODEL TRAINING API TESTING")
        print("=" * 80)
        print(f"Backend URL: {BASE_URL}")
        print(f"Test started at: {datetime.now().isoformat()}")
        
        start_time = time.time()
        
        # Run all test categories
        try:
            # Test 1: Tethys Training Status
            self.test_tethys_training_status()
            
            # Test 2: Tethys Training Start/Stop
            self.test_tethys_training_start_stop()
            
            # Test 3: Individual Model Training
            self.test_individual_model_training()
            
            # Test 4: Model Status Persistence
            self.test_model_status_persistence()
            
            # Test 5: Other Important Endpoints
            self.test_other_important_endpoints()
            
        except Exception as e:
            print(f"\n❌ Test execution error: {e}")
        
        # Calculate summary
        total_time = time.time() - start_time
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Average Response Time: {sum(float(r['response_time'].replace('s', '')) for r in self.results if 'response_time' in r) / total_tests:.3f}s")
        
        # Print failed tests
        failed_tests = [r for r in self.results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['method']} {test['endpoint']}: {test['status_code']} - {test.get('error', 'Unknown error')}")
        
        # Print key findings
        print(f"\n🔍 KEY FINDINGS:")
        
        # Check Tethys training functionality
        tethys_status_tests = [r for r in self.results if 'tethys-train' in r['endpoint']]
        tethys_working = all(r['success'] for r in tethys_status_tests)
        print(f"  - Tethys Training System: {'✓ Working' if tethys_working else '✗ Issues found'}")
        
        # Check model training functionality
        model_training_tests = [r for r in self.results if '/training/' in r['endpoint']]
        model_training_working = all(r['success'] for r in model_training_tests)
        print(f"  - Model Training System: {'✓ Working' if model_training_working else '✗ Issues found'}")
        
        # Check health endpoint
        health_tests = [r for r in self.results if r['endpoint'] == '/health']
        health_working = all(r['success'] for r in health_tests)
        print(f"  - Health Check: {'✓ Working' if health_working else '✗ Issues found'}")
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "tethys_working": tethys_working,
            "model_training_working": model_training_working,
            "health_working": health_working,
            "results": self.results
        }

def main():
    """Main test execution"""
    tester = TethysModelTrainingTester()
    results = tester.run_comprehensive_test()
    
    # Save results to file
    with open('/app/tethys_model_training_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: /app/tethys_model_training_results.json")
    
    return results

if __name__ == "__main__":
    main()