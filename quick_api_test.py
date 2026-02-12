#!/usr/bin/env python3
"""
Simple Backend API Test - Review Request Endpoints
"""

import requests
import json
import time
from datetime import datetime

# Try both URLs
URLS = [
    "http://localhost:8001/api",
    "https://speed-optimizer-12.preview.emergentagent.com/api"
]

def test_single_endpoint(base_url, endpoint, timeout=10):
    """Test a single endpoint with timeout"""
    url = f"{base_url}{endpoint}"
    try:
        response = requests.get(url, timeout=timeout)
        return {
            'endpoint': endpoint,
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'response_size': len(response.text),
            'url': url
        }
    except Exception as e:
        return {
            'endpoint': endpoint,
            'status_code': 0,
            'success': False,
            'error': str(e),
            'url': url
        }

def main():
    print("🔍 Testing Review Request Endpoints...")
    
    # Core endpoints from review request
    endpoints = [
        '/health',
        '/tethys/status', 
        '/ensemble/status',
        '/kraken-universe/coins',
        '/portfolio',
        '/paper-trades',
        '/market/prices',
        '/coindesk/news',
        '/sound-settings/',
        '/email-digest/settings',
        '/portfolio-share/my-shares',
        '/copy-trading/leaderboard',
        '/social/feed',
        '/marketplace/strategies',
        '/paper-leaderboard/',
        '/defi-wallet/balances/0x123456',
        '/ml-monitoring/ab-test/list',
        '/ml-optimization/distributed/status',
        '/training/status',
        '/training-progress/active',
        '/ai-explain/models',
        '/achievements/list'
    ]
    
    for base_url in URLS:
        print(f"\n📍 Testing against: {base_url}")
        print("-" * 60)
        
        successful = 0
        total = len(endpoints)
        
        for endpoint in endpoints:
            result = test_single_endpoint(base_url, endpoint)
            
            if result['success']:
                print(f"✅ {endpoint} ({result['status_code']}) - {result['response_size']} bytes")
                successful += 1
            else:
                error_msg = result.get('error', f"Status {result['status_code']}")
                print(f"❌ {endpoint} - {error_msg}")
        
        success_rate = (successful / total * 100) if total > 0 else 0
        print(f"\n📊 Results: {successful}/{total} ({success_rate:.1f}% success)")
        
        # If we got good results from one URL, break
        if success_rate > 50:
            print(f"✅ Found working backend at: {base_url}")
            break
    
    print("\n🎉 Quick test complete!")

if __name__ == "__main__":
    main()