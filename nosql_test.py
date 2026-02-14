#!/usr/bin/env python3
"""
NoSQL Injection Test - Direct Testing
"""

import httpx
import asyncio

BACKEND_URL = "https://kraken-security-scan.preview.emergentagent.com"

async def test_nosql_injection_detailed():
    """Detailed NoSQL injection testing"""
    client = httpx.AsyncClient(timeout=10.0)
    
    test_cases = [
        ("Direct $gt", "/api/market/prices?coin_ids=$gt"),
        ("URL encoded $gt", "/api/market/prices?coin_ids=%24gt"),
        ("Direct $where", "/api/market/prices?coin_ids=$where"),
        ("URL encoded $where", "/api/market/prices?coin_ids=%24where"),
        ("Normal bitcoin", "/api/market/prices?coin_ids=bitcoin"),
        ("Normal comma separated", "/api/market/prices?coin_ids=bitcoin,ethereum")
    ]
    
    for name, url in test_cases:
        try:
            response = await client.get(f"{BACKEND_URL}{url}")
            print(f"{name}: Status {response.status_code}")
            if response.status_code == 400:
                print(f"  Response: {response.text}")
            elif response.status_code == 200:
                data = response.json()
                print(f"  Success: {len(data) if isinstance(data, dict) else 'Non-dict response'}")
        except Exception as e:
            print(f"{name}: Exception {e}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_nosql_injection_detailed())