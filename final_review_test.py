#!/usr/bin/env python3
"""
Final Review Request API Testing - February 12, 2026
Testing the specific 22 endpoints with CORRECT paths
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001/api"

def test_endpoint_detailed(endpoint, description=""):
    """Test endpoint and return detailed results"""
    url = f"{BASE_URL}{endpoint}"
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=15)
        response_time = round((time.time() - start_time) * 1000, 1)
        
        # Try to parse JSON
        try:
            data = response.json()
        except:
            data = response.text[:200]
        
        return {
            'endpoint': endpoint,
            'description': description,
            'status_code': response.status_code,
            'response_time_ms': response_time,
            'success': response.status_code == 200,
            'data': data,
            'size_bytes': len(response.text)
        }
    except Exception as e:
        return {
            'endpoint': endpoint,
            'description': description,
            'status_code': 0,
            'response_time_ms': round((time.time() - start_time) * 1000, 1),
            'success': False,
            'error': str(e),
            'data': None
        }

def main():
    print("🚀 FINAL REVIEW REQUEST API TESTING - CORRECTED ENDPOINTS")
    print("=" * 80)
    print(f"📍 Testing against: {BASE_URL}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test all endpoints from review request with CORRECT paths
    endpoints = [
        # Core APIs (1-3)
        ('/health', 'Health check'),
        ('/tethys/status', 'Tethys trading engine status'),
        ('/ensemble/status', 'Ensemble AI status'),
        
        # Trading APIs (4-6) - CORRECTED PATHS
        ('/kraken-universe/coins', 'Kraken coins list'),
        ('/portfolio/visualization/summary', 'Portfolio data - CORRECTED PATH'),
        ('/paper-trading/portfolio', 'Paper trades - CORRECTED PATH'),
        
        # Market Data APIs (7-8)
        ('/market/prices', 'Current prices'),
        ('/coindesk/news', 'News feed'),
        
        # Settings APIs (9-11)
        ('/sound-settings/', 'Sound settings (new)'),
        ('/email-digest/settings', 'Email digest settings (new)'),
        ('/portfolio-share/my-shares', 'Portfolio shares (new)'),
        
        # Social/Marketplace APIs (12-15) - Should return empty
        ('/copy-trading/leaderboard', 'Copy trading leaderboard - should return empty'),
        ('/social/feed', 'Social feed - should return empty'),
        ('/marketplace/strategies', 'Marketplace strategies - should return empty'),
        ('/paper-leaderboard/top', 'Paper leaderboard - CORRECTED PATH'),
        
        # DeFi APIs (16) - Should return empty with message
        ('/defi-wallet/balances/0x123456', 'DeFi wallet balances - should return empty with message'),
        
        # ML APIs (17-18) - Should return empty/not_configured
        ('/ml-monitoring/ab-test/list', 'ML monitoring A/B test list - should return empty'),
        ('/ml-optimization/distributed/status', 'ML optimization distributed status - should return not_configured'),
        
        # Training APIs (19-20)
        ('/training/status', 'Training status'),
        ('/training-progress/active', 'Active training progress'),
        
        # AI/Analysis APIs (21-22) - CORRECTED PATHS
        ('/ai-explainability/feature-definitions', 'AI models list - CORRECTED PATH'),
        ('/achievements/list', 'Achievements')
    ]
    
    results = []
    successful = 0
    
    for endpoint, description in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        result = test_endpoint_detailed(endpoint, description)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ SUCCESS ({result['status_code']}) - {result['response_time_ms']}ms - {result['size_bytes']} bytes")
            successful += 1
            
            # Show key response data
            if isinstance(result['data'], dict):
                if 'status' in result['data']:
                    print(f"      Status: {result['data']['status']}")
                if 'message' in result['data']:
                    print(f"      Message: {result['data']['message']}")
                if 'data' in result['data'] and isinstance(result['data']['data'], list):
                    print(f"      Data items: {len(result['data']['data'])}")
                elif isinstance(result['data'], list):
                    print(f"      Array items: {len(result['data'])}")
        else:
            print(f"   ❌ FAILED ({result['status_code']}) - {result.get('error', 'Unknown error')}")
    
    # Summary
    total = len(results)
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 80)
    print("📊 FINAL TEST SUMMARY - CORRECTED ENDPOINTS")
    print("=" * 80)
    print(f"🎯 OVERALL RESULTS:")
    print(f"   Total Tests: {total}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {total - successful}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    # Performance metrics
    response_times = [r['response_time_ms'] for r in results if r['success']]
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"   Average Response Time: {avg_time:.1f}ms")
        print(f"   Fastest: {min(response_times):.1f}ms")
        print(f"   Slowest: {max(response_times):.1f}ms")
    
    # Successful endpoints
    successful_results = [r for r in results if r['success']]
    if successful_results:
        print(f"\n✅ WORKING ENDPOINTS ({len(successful_results)}):")
        for result in successful_results:
            print(f"   ✅ {result['endpoint']} - {result['description']}")
    
    # Failed endpoints
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print(f"\n❌ FAILED ENDPOINTS ({len(failed_results)}):")
        for result in failed_results:
            error_info = result.get('error', f"Status {result['status_code']}")
            print(f"   ❌ {result['endpoint']} - {error_info}")
    
    # Verify empty state endpoints
    empty_endpoints = [
        '/copy-trading/leaderboard',
        '/social/feed',
        '/marketplace/strategies', 
        '/paper-leaderboard/top',
        '/defi-wallet/balances/0x123456',
        '/ml-monitoring/ab-test/list',
        '/ml-optimization/distributed/status'
    ]
    
    print(f"\n🔍 EMPTY STATE VERIFICATION:")
    for result in results:
        if result['endpoint'] in empty_endpoints and result['success']:
            data = result['data']
            if isinstance(data, dict):
                if 'message' in data:
                    print(f"   ✅ {result['endpoint']}: {data['message']}")
                elif 'data' in data and isinstance(data['data'], list) and len(data['data']) == 0:
                    print(f"   ✅ {result['endpoint']}: Returns empty array as expected")
                elif len(data) == 0:
                    print(f"   ✅ {result['endpoint']}: Returns empty object as expected")
                else:
                    print(f"   ⚠️  {result['endpoint']}: Contains data (may not be empty as expected)")
            elif isinstance(data, list) and len(data) == 0:
                print(f"   ✅ {result['endpoint']}: Returns empty array as expected")
    
    print("\n" + "=" * 80)
    print("🎉 FINAL REVIEW REQUEST API TESTING COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    main()