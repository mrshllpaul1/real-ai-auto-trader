#!/usr/bin/env python3
"""
Backend API Testing for Review Request - Journal Add Endpoint and Core APIs
Tests the new journal/add endpoint and core API regression after enhancements
"""

import requests
import json
import sys
from typing import Dict, Any
import time

# Backend URL from review request
BACKEND_URL = "https://feature-enhancer-7.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def make_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Make HTTP request with error handling"""
    try:
        start_time = time.time()
        if method.upper() == 'GET':
            response = requests.get(url, timeout=30, **kwargs)
        elif method.upper() == 'POST':
            response = requests.post(url, timeout=30, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        response_time = time.time() - start_time
        
        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "response_time": response_time,
            "url": url
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout (>30s)",
            "status_code": None,
            "url": url
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') and e.response else None,
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": None,
            "url": url
        }

def test_core_health_check():
    """Test 1: Core Health Check - GET /api/health should return 200"""
    print("🔍 Testing Core Health Check...")
    result = make_request('GET', f"{API_BASE}/health")
    
    if result["success"] and result["status_code"] == 200:
        print(f"✅ GET /api/health: {result['status_code']} ({result['response_time']:.3f}s)")
        return True, f"Health check working - {result['response']}"
    else:
        print(f"❌ GET /api/health: {result.get('status_code', 'ERROR')} - {result.get('error', 'Unknown error')}")
        return False, f"Health check failed - Status: {result.get('status_code')}, Error: {result.get('error')}"

def test_journal_add_endpoint():
    """Test 2: Journal Add Endpoint (NEW) - POST /api/journal/add"""
    print("🔍 Testing NEW Journal Add Endpoint...")
    
    # Test data from review request
    test_payload = {
        "coin_id": "bitcoin",
        "action": "buy",
        "amount": 100,
        "price": 50000,
        "trade_type": "spot",
        "symbol": "BTC/USD",
        "amount_usd": 100.0,
        "quantity": 0.002,
        "is_paper": True,
        "notes": "Test trade via new journal/add endpoint"
    }
    
    headers = {"Content-Type": "application/json"}
    result = make_request('POST', f"{API_BASE}/journal/add", 
                         json=test_payload, headers=headers)
    
    if result["success"] and result["status_code"] == 200:
        print(f"✅ POST /api/journal/add: {result['status_code']} ({result['response_time']:.3f}s)")
        return True, f"New journal/add endpoint working - Trade recorded successfully"
    else:
        print(f"❌ POST /api/journal/add: {result.get('status_code', 'ERROR')} - {result.get('error', 'Unknown error')}")
        if result.get('response'):
            print(f"   Response: {result['response']}")
        return False, f"Journal/add endpoint failed - Status: {result.get('status_code')}, Error: {result.get('error')}"

def test_journal_record_endpoint():
    """Test 3: Journal Record Endpoint - POST /api/journal/record (should still work)"""
    print("🔍 Testing Original Journal Record Endpoint...")
    
    # Same test data to verify compatibility
    test_payload = {
        "coin_id": "bitcoin", 
        "action": "sell",
        "amount": 50,
        "price": 51000,
        "trade_type": "spot",
        "symbol": "BTC/USD", 
        "amount_usd": 50.0,
        "quantity": 0.001,
        "is_paper": True,
        "notes": "Test trade via original journal/record endpoint"
    }
    
    headers = {"Content-Type": "application/json"}
    result = make_request('POST', f"{API_BASE}/journal/record",
                         json=test_payload, headers=headers)
    
    if result["success"] and result["status_code"] == 200:
        print(f"✅ POST /api/journal/record: {result['status_code']} ({result['response_time']:.3f}s)")
        return True, f"Journal/record endpoint still working - Trade recorded successfully"
    else:
        print(f"❌ POST /api/journal/record: {result.get('status_code', 'ERROR')} - {result.get('error', 'Unknown error')}")
        if result.get('response'):
            print(f"   Response: {result['response']}")
        return False, f"Journal/record endpoint failed - Status: {result.get('status_code')}, Error: {result.get('error')}"

def test_key_apis_quick_check():
    """Test 4: Key APIs Quick Check - All should return 200"""
    print("🔍 Testing Key APIs Quick Check...")
    
    endpoints = [
        f"{API_BASE}/tethys/status",
        f"{API_BASE}/ensemble/status", 
        f"{API_BASE}/market/prices?coin_ids=bitcoin,ethereum",
        f"{API_BASE}/kraken/status",
        f"{API_BASE}/performance/summary"
    ]
    
    results = []
    all_passed = True
    
    for endpoint in endpoints:
        endpoint_name = endpoint.split("/api/")[-1]
        result = make_request('GET', endpoint)
        
        if result["success"] and result["status_code"] == 200:
            print(f"✅ GET /api/{endpoint_name}: {result['status_code']} ({result['response_time']:.3f}s)")
            results.append(f"{endpoint_name}: ✅ Working")
        else:
            print(f"❌ GET /api/{endpoint_name}: {result.get('status_code', 'ERROR')} - {result.get('error', 'Unknown error')}")
            results.append(f"{endpoint_name}: ❌ Failed - {result.get('status_code')} {result.get('error', '')}")
            all_passed = False
    
    return all_passed, "\n".join(results)

def run_all_tests():
    """Run all backend tests for the review request"""
    print("🚀 Starting Backend API Testing for Review Request")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 70)
    
    test_results = []
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Core Health Check
    total_tests += 1
    success, message = test_core_health_check()
    if success:
        passed_tests += 1
    test_results.append(("Core Health Check", success, message))
    
    print()
    
    # Test 2: Journal Add Endpoint (NEW)
    total_tests += 1
    success, message = test_journal_add_endpoint()
    if success:
        passed_tests += 1
    test_results.append(("Journal Add Endpoint (NEW)", success, message))
    
    print()
    
    # Test 3: Journal Record Endpoint
    total_tests += 1
    success, message = test_journal_record_endpoint()
    if success:
        passed_tests += 1
    test_results.append(("Journal Record Endpoint", success, message))
    
    print()
    
    # Test 4: Key APIs Quick Check (counts as 1 test group)
    total_tests += 1
    success, message = test_key_apis_quick_check()
    if success:
        passed_tests += 1
    test_results.append(("Key APIs Quick Check", success, message))
    
    # Summary
    print()
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} test groups passed)")
    print()
    
    for test_name, success, message in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success or "❌" in message:
            # Show details for failed tests or tests with issues
            print(f"     Details: {message}")
        print()
    
    return success_rate, test_results

if __name__ == "__main__":
    success_rate, results = run_all_tests()
    
    # Exit with error code if critical tests fail
    if success_rate < 75:
        print("❌ CRITICAL: Success rate below 75% - backend has issues")
        sys.exit(1)
    elif success_rate < 100:
        print("⚠️  WARNING: Some tests failed - see details above")
        sys.exit(0)
    else:
        print("🎉 SUCCESS: All tests passed!")
        sys.exit(0)