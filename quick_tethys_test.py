#!/usr/bin/env python3
"""
Quick Tethys Training and Model Training Test
============================================
Testing specific endpoints with shorter timeouts
"""

import requests
import json
import time
from datetime import datetime

# Backend URL configuration
BASE_URL = "https://filecheck-4.preview.emergentagent.com/api"

def test_endpoint(method, endpoint, data=None, timeout=10):
    """Test individual endpoint with short timeout"""
    url = f"{BASE_URL}{endpoint}"
    start_time = time.time()
    
    try:
        session = requests.Session()
        session.timeout = timeout
        
        if method.upper() == "GET":
            response = session.get(url)
        elif method.upper() == "POST":
            response = session.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response_time = time.time() - start_time
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "response_time": f"{response_time:.3f}s",
            "success": response.status_code == 200,
            "timestamp": datetime.now().isoformat()
        }
        
        if response.status_code == 200:
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200]
        else:
            result["error"] = response.text[:200]
        
        return result
        
    except Exception as e:
        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": "ERROR",
            "response_time": f"{time.time() - start_time:.3f}s",
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Run quick tests"""
    print("🎯 QUICK TETHYS TRAINING AND MODEL TRAINING TEST")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    tests = [
        # Basic health check
        ("GET", "/health", None, "Health check"),
        
        # Tethys Training Status
        ("GET", "/tethys-train/status", None, "Tethys training status - should include is_active field"),
        
        # Individual Model Training Status
        ("GET", "/training/models-status", None, "Get status for all 6 models"),
        
        # General training status
        ("GET", "/training/status", None, "General training status"),
        
        # Try to start Tethys training (with minimal episodes)
        ("POST", "/tethys-train/start", {"episodes": 3, "symbol": "BTC/USD"}, "Start Tethys training"),
        
        # Try to train a model
        ("POST", "/training/train-model", {"model_name": "historical", "coins": ["bitcoin"]}, "Train historical model"),
        
        # Check model status persistence
        ("GET", "/training/model-status/historical", None, "Historical model status persistence"),
    ]
    
    results = []
    successful = 0
    
    for method, endpoint, data, description in tests:
        print(f"\n🔍 Testing: {description}")
        result = test_endpoint(method, endpoint, data)
        results.append(result)
        
        if result['success']:
            successful += 1
            print(f"✅ {method} {endpoint}: {result['status_code']} ({result['response_time']})")
            
            # Print key response data
            if 'response_data' in result and isinstance(result['response_data'], dict):
                data = result['response_data']
                
                # For Tethys status
                if 'tethys-train/status' in endpoint:
                    print(f"   - is_active: {data.get('is_active', 'N/A')}")
                    print(f"   - is_training: {data.get('is_training', 'N/A')}")
                
                # For models status
                elif 'models-status' in endpoint:
                    model_count = len(data)
                    print(f"   - Number of models: {model_count}")
                    for model_name, model_data in data.items():
                        if isinstance(model_data, dict):
                            is_trained = model_data.get('is_trained', False)
                            print(f"   - {model_name}: trained={is_trained}")
                
                # For health check
                elif endpoint == "/health":
                    print(f"   - Status: {data.get('status', 'N/A')}")
                    print(f"   - Database: {data.get('database', 'N/A')}")
                
                # For training start
                elif 'train' in endpoint and method == "POST":
                    print(f"   - Status: {data.get('status', 'N/A')}")
                    if 'task_id' in data:
                        print(f"   - Task ID: {data['task_id']}")
        else:
            print(f"❌ {method} {endpoint}: {result['status_code']} - {result.get('error', 'Unknown error')}")
    
    # Summary
    total_tests = len(results)
    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 QUICK TEST SUMMARY")
    print("=" * 40)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful}")
    print(f"Failed: {total_tests - successful}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    # Check specific functionality
    tethys_tests = [r for r in results if 'tethys-train' in r['endpoint']]
    tethys_working = all(r['success'] for r in tethys_tests)
    print(f"  - Tethys Training System: {'✅ Working' if tethys_working else '❌ Issues found'}")
    
    model_tests = [r for r in results if '/training/' in r['endpoint']]
    model_working = all(r['success'] for r in model_tests)
    print(f"  - Model Training System: {'✅ Working' if model_working else '❌ Issues found'}")
    
    health_tests = [r for r in results if r['endpoint'] == '/health']
    health_working = all(r['success'] for r in health_tests)
    print(f"  - Health Check: {'✅ Working' if health_working else '❌ Issues found'}")
    
    # Save results
    with open('/app/quick_tethys_test_results.json', 'w') as f:
        json.dump({
            "total_tests": total_tests,
            "successful_tests": successful,
            "success_rate": success_rate,
            "tethys_working": tethys_working,
            "model_training_working": model_working,
            "health_working": health_working,
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: /app/quick_tethys_test_results.json")
    
    return results

if __name__ == "__main__":
    main()