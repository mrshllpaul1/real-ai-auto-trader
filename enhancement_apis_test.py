#!/usr/bin/env python3
"""
Enhancement APIs Testing - Natural Language Strategy, AI Copilot, ML Analytics
Tests the NEW enhancement APIs that were just implemented
"""

import requests
import json
import sys
from typing import Dict, Any
import time

# Backend URL from frontend/.env
BACKEND_URL = "https://feature-enhancer-7.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def make_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Make HTTP request with error handling"""
    try:
        start_time = time.time()
        
        # Add X-API-Key header for POST requests to bypass CSRF
        if method.upper() == 'POST' and 'headers' not in kwargs:
            kwargs['headers'] = {}
        if method.upper() == 'POST':
            kwargs['headers']['X-API-Key'] = 'test-key-bypass-csrf'
        
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
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON response",
            "status_code": response.status_code if 'response' in locals() else None,
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": None,
            "url": url
        }

def test_natural_language_strategy_api():
    """Test Natural Language Strategy Builder API endpoints"""
    print("\n🎯 TESTING NATURAL LANGUAGE STRATEGY BUILDER API")
    print("=" * 60)
    
    results = []
    
    # 1. GET /api/nl-strategy/examples
    print("\n1. Testing GET /api/nl-strategy/examples")
    result = make_request('GET', f"{API_BASE}/nl-strategy/examples")
    results.append(("GET /api/nl-strategy/examples", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "examples" in response and "tips" in response and "available_indicators" in response:
            print(f"   ✅ SUCCESS: {len(response['examples'])} examples, {len(response['tips'])} tips, {len(response['available_indicators'])} indicators")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 2. POST /api/nl-strategy/parse
    print("\n2. Testing POST /api/nl-strategy/parse")
    parse_payload = {
        "input": "Buy BTC when RSI drops below 30 with 5% stop loss",
        "coins": ["BTC"],
        "backtest": False
    }
    result = make_request('POST', f"{API_BASE}/nl-strategy/parse", 
                         json=parse_payload,
                         headers={'Content-Type': 'application/json'})
    results.append(("POST /api/nl-strategy/parse", result))
    
    strategy_id = None
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "strategy_id" in response and "status" in response:
            strategy_id = response["strategy_id"]
            print(f"   ✅ SUCCESS: Strategy parsed with ID {strategy_id}, status: {response['status']}")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 3. GET /api/nl-strategy/list
    print("\n3. Testing GET /api/nl-strategy/list")
    result = make_request('GET', f"{API_BASE}/nl-strategy/list")
    results.append(("GET /api/nl-strategy/list", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "strategies" in response and "total" in response:
            print(f"   ✅ SUCCESS: {response['total']} strategies listed")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 4. POST /api/nl-strategy/{strategy_id}/activate (if we have a strategy_id)
    if strategy_id:
        print(f"\n4. Testing POST /api/nl-strategy/{strategy_id}/activate")
        result = make_request('POST', f"{API_BASE}/nl-strategy/{strategy_id}/activate")
        results.append(("POST /api/nl-strategy/{strategy_id}/activate", result))
        
        if result["success"] and result["status_code"] == 200:
            response = result["response"]
            if "message" in response and "strategy" in response:
                print(f"   ✅ SUCCESS: {response['message']}")
            else:
                print(f"   ⚠️  Missing expected fields in response")
        else:
            print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    else:
        print("\n4. Skipping activate test - no strategy_id available")
        results.append(("POST /api/nl-strategy/{strategy_id}/activate", {"success": False, "error": "No strategy_id", "status_code": None}))
    
    # 5. POST /api/nl-strategy/validate
    print("\n5. Testing POST /api/nl-strategy/validate")
    validate_payload = {
        "entry_conditions": [
            {"indicator": "RSI", "operator": "<", "value": 30}
        ],
        "exit_conditions": [
            {"indicator": "RSI", "operator": ">", "value": 70}
        ],
        "risk_management": {
            "stop_loss_percent": 5,
            "take_profit_percent": 15,
            "position_size_percent": 10
        },
        "coins": ["BTC"]
    }
    result = make_request('POST', f"{API_BASE}/nl-strategy/validate", 
                         json=validate_payload,
                         headers={'Content-Type': 'application/json'})
    results.append(("POST /api/nl-strategy/validate", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "valid" in response and "errors" in response and "warnings" in response:
            print(f"   ✅ SUCCESS: Valid: {response['valid']}, Errors: {len(response['errors'])}, Warnings: {len(response['warnings'])}")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    return results

def test_ai_copilot_api():
    """Test AI Trading Copilot API endpoints"""
    print("\n🤖 TESTING AI TRADING COPILOT API")
    print("=" * 60)
    
    results = []
    
    # 1. POST /api/ai-copilot/chat
    print("\n1. Testing POST /api/ai-copilot/chat")
    chat_payload = {
        "message": "What is the current market sentiment?",
        "include_market_context": True
    }
    result = make_request('POST', f"{API_BASE}/ai-copilot/chat", 
                         json=chat_payload,
                         headers={'Content-Type': 'application/json'})
    results.append(("POST /api/ai-copilot/chat", result))
    
    session_id = None
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "session_id" in response and "response" in response and "timestamp" in response:
            session_id = response["session_id"]
            print(f"   ✅ SUCCESS: Chat response received, session: {session_id}")
            print(f"   📝 Response preview: {response['response'][:100]}...")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 2. GET /api/ai-copilot/quick-insights
    print("\n2. Testing GET /api/ai-copilot/quick-insights")
    result = make_request('GET', f"{API_BASE}/ai-copilot/quick-insights")
    results.append(("GET /api/ai-copilot/quick-insights", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "insights" in response and "market_context" in response:
            print(f"   ✅ SUCCESS: {len(response['insights'])} insights generated")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 3. GET /api/ai-copilot/sessions
    print("\n3. Testing GET /api/ai-copilot/sessions")
    result = make_request('GET', f"{API_BASE}/ai-copilot/sessions")
    results.append(("GET /api/ai-copilot/sessions", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "sessions" in response and "total" in response:
            print(f"   ✅ SUCCESS: {response['total']} sessions found")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 4. POST /api/ai-copilot/session/{session_id}/clear (if we have a session_id)
    if session_id:
        print(f"\n4. Testing POST /api/ai-copilot/session/{session_id}/clear")
        result = make_request('POST', f"{API_BASE}/ai-copilot/session/{session_id}/clear")
        results.append(("POST /api/ai-copilot/session/{session_id}/clear", result))
        
        if result["success"] and result["status_code"] == 200:
            response = result["response"]
            if "message" in response and "session_id" in response:
                print(f"   ✅ SUCCESS: {response['message']}")
            else:
                print(f"   ⚠️  Missing expected fields in response")
        else:
            print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    else:
        print("\n4. Skipping clear session test - no session_id available")
        results.append(("POST /api/ai-copilot/session/{session_id}/clear", {"success": False, "error": "No session_id", "status_code": None}))
    
    return results

def test_ml_analytics_api():
    """Test ML Analytics API endpoints"""
    print("\n📊 TESTING ML ANALYTICS API")
    print("=" * 60)
    
    results = []
    
    # 1. GET /api/ml-analytics/dashboard
    print("\n1. Testing GET /api/ml-analytics/dashboard")
    result = make_request('GET', f"{API_BASE}/ml-analytics/dashboard")
    results.append(("GET /api/ml-analytics/dashboard", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "calibration" in response and "drift" in response and "ab_testing" in response and "infrastructure" in response:
            print(f"   ✅ SUCCESS: Dashboard data retrieved with all sections")
        else:
            print(f"   ⚠️  Missing expected sections in dashboard")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 2. GET /api/ml-analytics/calibration/accuracy-by-level
    print("\n2. Testing GET /api/ml-analytics/calibration/accuracy-by-level")
    result = make_request('GET', f"{API_BASE}/ml-analytics/calibration/accuracy-by-level")
    results.append(("GET /api/ml-analytics/calibration/accuracy-by-level", result))
    
    if result["success"] and result["status_code"] == 200:
        print(f"   ✅ SUCCESS: Accuracy by confidence level retrieved")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 3. GET /api/ml-analytics/calibration/curve
    print("\n3. Testing GET /api/ml-analytics/calibration/curve")
    result = make_request('GET', f"{API_BASE}/ml-analytics/calibration/curve")
    results.append(("GET /api/ml-analytics/calibration/curve", result))
    
    if result["success"] and result["status_code"] == 200:
        print(f"   ✅ SUCCESS: Calibration curve retrieved")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 4. GET /api/ml-analytics/drift/status
    print("\n4. Testing GET /api/ml-analytics/drift/status")
    result = make_request('GET', f"{API_BASE}/ml-analytics/drift/status")
    results.append(("GET /api/ml-analytics/drift/status", result))
    
    if result["success"] and result["status_code"] == 200:
        print(f"   ✅ SUCCESS: Model drift status retrieved")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 5. GET /api/ml-analytics/drift/alerts
    print("\n5. Testing GET /api/ml-analytics/drift/alerts")
    result = make_request('GET', f"{API_BASE}/ml-analytics/drift/alerts")
    results.append(("GET /api/ml-analytics/drift/alerts", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "alerts" in response and "total" in response:
            print(f"   ✅ SUCCESS: {response['total']} drift alerts retrieved")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 6. GET /api/ml-analytics/ab-test/list
    print("\n6. Testing GET /api/ml-analytics/ab-test/list")
    result = make_request('GET', f"{API_BASE}/ml-analytics/ab-test/list")
    results.append(("GET /api/ml-analytics/ab-test/list", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "tests" in response and "total" in response:
            print(f"   ✅ SUCCESS: {response['total']} A/B tests listed")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 7. GET /api/ml-analytics/cache/stats
    print("\n7. Testing GET /api/ml-analytics/cache/stats")
    result = make_request('GET', f"{API_BASE}/ml-analytics/cache/stats")
    results.append(("GET /api/ml-analytics/cache/stats", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "cache" in response and "deduplication" in response:
            print(f"   ✅ SUCCESS: Cache and deduplication stats retrieved")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    # 8. POST /api/ml-analytics/ab-test/create
    print("\n8. Testing POST /api/ml-analytics/ab-test/create")
    ab_test_payload = {
        "test_id": "test_strategy_comparison",
        "test_name": "RSI vs MACD Strategy Comparison",
        "variants": [
            {"id": "rsi_strategy", "name": "RSI Strategy", "config": {"indicator": "RSI", "threshold": 30}},
            {"id": "macd_strategy", "name": "MACD Strategy", "config": {"indicator": "MACD", "crossover": True}}
        ],
        "traffic_split": [0.5, 0.5],
        "metric": "win_rate"
    }
    result = make_request('POST', f"{API_BASE}/ml-analytics/ab-test/create", 
                         json=ab_test_payload,
                         headers={'Content-Type': 'application/json'})
    results.append(("POST /api/ml-analytics/ab-test/create", result))
    
    if result["success"] and result["status_code"] == 200:
        response = result["response"]
        if "test_id" in response and "status" in response:
            print(f"   ✅ SUCCESS: A/B test created with ID {response['test_id']}")
        else:
            print(f"   ⚠️  Missing expected fields in response")
    else:
        print(f"   ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
    
    return results

def main():
    """Run all enhancement API tests"""
    print("🚀 ENHANCEMENT APIS TESTING - Natural Language Strategy, AI Copilot, ML Analytics")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    
    all_results = []
    
    # Test Natural Language Strategy API
    nl_results = test_natural_language_strategy_api()
    all_results.extend(nl_results)
    
    # Test AI Copilot API
    copilot_results = test_ai_copilot_api()
    all_results.extend(copilot_results)
    
    # Test ML Analytics API
    ml_results = test_ml_analytics_api()
    all_results.extend(ml_results)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 ENHANCEMENT APIS TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(all_results)
    successful_tests = len([r for r in all_results if r[1]["success"] and r[1]["status_code"] == 200])
    failed_tests = total_tests - successful_tests
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Successful: {successful_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Detailed results by category
    print(f"\n📋 DETAILED RESULTS:")
    
    # Natural Language Strategy API
    nl_success = len([r for r in nl_results if r[1]["success"] and r[1]["status_code"] == 200])
    print(f"   🎯 Natural Language Strategy API: {nl_success}/{len(nl_results)} ({(nl_success/len(nl_results))*100:.1f}%)")
    
    # AI Copilot API
    copilot_success = len([r for r in copilot_results if r[1]["success"] and r[1]["status_code"] == 200])
    print(f"   🤖 AI Copilot API: {copilot_success}/{len(copilot_results)} ({(copilot_success/len(copilot_results))*100:.1f}%)")
    
    # ML Analytics API
    ml_success = len([r for r in ml_results if r[1]["success"] and r[1]["status_code"] == 200])
    print(f"   📊 ML Analytics API: {ml_success}/{len(ml_results)} ({(ml_success/len(ml_results))*100:.1f}%)")
    
    # Failed tests details
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS:")
        for endpoint, result in all_results:
            if not (result["success"] and result["status_code"] == 200):
                status = result.get("status_code", "N/A")
                error = result.get("error", "Unknown error")
                print(f"   • {endpoint}: {status} - {error}")
    
    # Performance summary
    response_times = [r[1]["response_time"] for r in all_results if r[1].get("response_time")]
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        print(f"\n⚡ PERFORMANCE:")
        print(f"   Average Response Time: {avg_time:.3f}s")
        print(f"   Maximum Response Time: {max_time:.3f}s")
    
    print(f"\n🎉 Enhancement APIs testing completed!")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)