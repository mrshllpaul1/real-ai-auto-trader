"""
AI Universe API Tests
Tests for the dynamic coin universe management endpoints.
Features tested:
- GET /api/ai-universe/stats - Universe statistics
- GET /api/ai-universe/coins - All active coins
- GET /api/ai-universe/coins/gems - Gem candidates
- GET /api/ai-universe/coins/discovered - AI discovered coins
- POST /api/ai-universe/coins/ai-discover - Add new coin via AI discovery
- DELETE /api/ai-universe/coin/{coin_id} - Deactivate a coin
- GET /api/scheduler/coin-universe - Scheduler coin universe endpoint
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment - DO NOT add default
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')


class TestAIUniverseStats:
    """Test /api/ai-universe/stats endpoint"""
    
    def test_get_universe_stats_success(self):
        """GET /api/ai-universe/stats should return universe statistics"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/stats", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert 'total_coins' in data, "Response should contain 'total_coins'"
        assert 'ai_discovered' in data, "Response should contain 'ai_discovered'"
        assert 'by_category' in data, "Response should contain 'by_category'"
        assert 'categories' in data, "Response should contain 'categories'"
        
        # Validate data types
        assert isinstance(data['total_coins'], int), "total_coins should be an integer"
        assert isinstance(data['ai_discovered'], int), "ai_discovered should be an integer"
        assert isinstance(data['by_category'], dict), "by_category should be a dict"
        assert isinstance(data['categories'], list), "categories should be a list"
        
        # Validate expected categories exist
        expected_categories = ['major', 'large', 'mid', 'defi', 'gaming', 'ai', 'meme', 'new', 'discovered']
        for cat in expected_categories:
            assert cat in data['categories'], f"Category '{cat}' should be in categories list"
        
        print(f"✅ Universe stats: {data['total_coins']} total coins, {data['ai_discovered']} AI discovered")


class TestAIUniverseCoins:
    """Test /api/ai-universe/coins endpoint"""
    
    def test_get_all_coins_success(self):
        """GET /api/ai-universe/coins should return all active coins"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'count' in data, "Response should contain 'count'"
        
        # Validate data types
        assert isinstance(data['coins'], list), "coins should be a list"
        assert isinstance(data['count'], int), "count should be an integer"
        assert data['count'] == len(data['coins']), "count should match coins list length"
        
        # Validate we have base coins (77 base coins expected)
        assert data['count'] >= 70, f"Expected at least 70 coins, got {data['count']}"
        
        # Validate some expected coins exist
        expected_coins = ['bitcoin', 'ethereum', 'solana', 'cardano']
        for coin in expected_coins:
            assert coin in data['coins'], f"Expected coin '{coin}' to be in universe"
        
        print(f"✅ All coins: {data['count']} active coins in universe")


class TestAIUniverseGems:
    """Test /api/ai-universe/coins/gems endpoint"""
    
    def test_get_gem_candidates_success(self):
        """GET /api/ai-universe/coins/gems should return gem candidates"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/gems", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'count' in data, "Response should contain 'count'"
        
        # Validate data types
        assert isinstance(data['coins'], list), "coins should be a list"
        assert isinstance(data['count'], int), "count should be an integer"
        
        # Gem candidates should include meme, ai, new, gaming, discovered categories
        # We expect at least some gems from base universe
        assert data['count'] >= 10, f"Expected at least 10 gem candidates, got {data['count']}"
        
        # Validate some expected gem coins exist (meme/ai/new categories)
        expected_gems = ['pepe', 'fetch-ai', 'jupiter']
        found_gems = [g for g in expected_gems if g in data['coins']]
        assert len(found_gems) >= 1, f"Expected at least one of {expected_gems} in gems"
        
        print(f"✅ Gem candidates: {data['count']} coins")


class TestAIUniverseDiscovered:
    """Test /api/ai-universe/coins/discovered endpoint"""
    
    def test_get_ai_discovered_coins_success(self):
        """GET /api/ai-universe/coins/discovered should return AI discovered coins"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/discovered", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'count' in data, "Response should contain 'count'"
        
        # Validate data types
        assert isinstance(data['coins'], list), "coins should be a list"
        assert isinstance(data['count'], int), "count should be an integer"
        
        # If there are discovered coins, validate their structure
        if data['count'] > 0:
            coin = data['coins'][0]
            assert 'coin_id' in coin, "Discovered coin should have 'coin_id'"
            assert 'symbol' in coin, "Discovered coin should have 'symbol'"
            assert 'ai_discovered' in coin, "Discovered coin should have 'ai_discovered'"
            assert coin['ai_discovered'] == True, "ai_discovered should be True"
        
        print(f"✅ AI discovered coins: {data['count']} coins")


class TestAIUniverseAIDiscover:
    """Test /api/ai-universe/coins/ai-discover endpoint"""
    
    def test_ai_discover_new_coin_success(self):
        """POST /api/ai-universe/coins/ai-discover should add a new coin"""
        # Generate unique coin ID to avoid duplicates
        unique_id = f"test-coin-{uuid.uuid4().hex[:8]}"
        
        payload = {
            "coin_id": unique_id,
            "symbol": "TEST",
            "reason": "Automated test - AI discovered coin",
            "potential_score": 0.75,
            "market_cap": 1000000,
            "volume_24h": 50000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-universe/coins/ai-discover",
            json=payload,
            timeout=30
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data.get('success') == True, f"Expected success=True, got {data}"
        assert data.get('coin_id') == unique_id, f"Expected coin_id={unique_id}"
        assert data.get('symbol') == "TEST", "Expected symbol=TEST"
        assert data.get('category') == "discovered", "Expected category=discovered"
        
        print(f"✅ AI discovered coin added: {unique_id}")
        
        # Verify coin was added by fetching it
        verify_response = requests.get(f"{BASE_URL}/api/ai-universe/coin/{unique_id}", timeout=30)
        assert verify_response.status_code == 200, f"Coin should exist after creation"
        
        verify_data = verify_response.json()
        assert verify_data['coin_id'] == unique_id
        assert verify_data['ai_discovered'] == True
        
        print(f"✅ Verified coin exists in universe")
        
        # Cleanup - deactivate the test coin
        cleanup_response = requests.delete(
            f"{BASE_URL}/api/ai-universe/coin/{unique_id}",
            params={"reason": "Test cleanup"},
            timeout=30
        )
        assert cleanup_response.status_code == 200, "Cleanup should succeed"
        print(f"✅ Test coin cleaned up")
    
    def test_ai_discover_duplicate_coin_fails(self):
        """POST /api/ai-universe/coins/ai-discover should fail for existing coin"""
        # Try to add bitcoin which already exists
        payload = {
            "coin_id": "bitcoin",
            "symbol": "BTC",
            "reason": "Test duplicate",
            "potential_score": 0.5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-universe/coins/ai-discover",
            json=payload,
            timeout=30
        )
        
        # Should return 400 for duplicate
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        
        # Verify error message
        data = response.json()
        assert 'detail' in data, "Error response should have 'detail'"
        assert 'already exists' in data['detail'].lower(), f"Error should mention 'already exists': {data['detail']}"
        
        print(f"✅ Duplicate coin correctly rejected")


class TestAIUniverseDeactivate:
    """Test DELETE /api/ai-universe/coin/{coin_id} endpoint"""
    
    def test_deactivate_coin_success(self):
        """DELETE /api/ai-universe/coin/{coin_id} should deactivate a coin"""
        # First create a test coin to deactivate
        unique_id = f"test-deactivate-{uuid.uuid4().hex[:8]}"
        
        create_payload = {
            "coin_id": unique_id,
            "symbol": "DEACT",
            "reason": "Test coin for deactivation",
            "potential_score": 0.5
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/ai-universe/coins/ai-discover",
            json=create_payload,
            timeout=30
        )
        assert create_response.status_code == 200, f"Failed to create test coin: {create_response.text}"
        print(f"✅ Created test coin: {unique_id}")
        
        # Now deactivate it
        deactivate_response = requests.delete(
            f"{BASE_URL}/api/ai-universe/coin/{unique_id}",
            params={"reason": "Test deactivation"},
            timeout=30
        )
        
        # Status code assertion
        assert deactivate_response.status_code == 200, f"Expected 200, got {deactivate_response.status_code}: {deactivate_response.text}"
        
        # Data assertions
        data = deactivate_response.json()
        assert data.get('success') == True, f"Expected success=True, got {data}"
        
        print(f"✅ Coin deactivated successfully")
        
        # Verify coin is no longer in active coins list
        all_coins_response = requests.get(f"{BASE_URL}/api/ai-universe/coins", timeout=30)
        all_coins = all_coins_response.json()['coins']
        assert unique_id not in all_coins, "Deactivated coin should not be in active coins list"
        
        print(f"✅ Verified coin is no longer active")
    
    def test_deactivate_nonexistent_coin_fails(self):
        """DELETE /api/ai-universe/coin/{coin_id} should fail for non-existent coin"""
        response = requests.delete(
            f"{BASE_URL}/api/ai-universe/coin/nonexistent-coin-xyz123",
            params={"reason": "Test"},
            timeout=30
        )
        
        # Should return 404 for non-existent coin
        assert response.status_code == 404, f"Expected 404 for non-existent coin, got {response.status_code}"
        
        print(f"✅ Non-existent coin correctly returns 404")


class TestSchedulerCoinUniverse:
    """Test /api/scheduler/coin-universe endpoint"""
    
    def test_scheduler_coin_universe_success(self):
        """GET /api/scheduler/coin-universe should return dynamic universe"""
        response = requests.get(f"{BASE_URL}/api/scheduler/coin-universe", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'total_coins' in data, "Response should contain 'total_coins'"
        assert 'gem_candidates' in data, "Response should contain 'gem_candidates'"
        assert 'categories' in data, "Response should contain 'categories'"
        
        # Validate data types
        assert isinstance(data['coins'], list), "coins should be a list"
        assert isinstance(data['total_coins'], int), "total_coins should be an integer"
        assert isinstance(data['gem_candidates'], int), "gem_candidates should be an integer"
        
        # Should have same coins as ai-universe/coins
        ai_universe_response = requests.get(f"{BASE_URL}/api/ai-universe/coins", timeout=30)
        ai_universe_data = ai_universe_response.json()
        
        # Counts should match (scheduler uses dynamic universe)
        assert data['total_coins'] == ai_universe_data['count'], \
            f"Scheduler total_coins ({data['total_coins']}) should match AI universe count ({ai_universe_data['count']})"
        
        print(f"✅ Scheduler coin universe: {data['total_coins']} coins (matches AI universe)")


class TestAIUniverseCategories:
    """Test /api/ai-universe/categories endpoint"""
    
    def test_get_categories_success(self):
        """GET /api/ai-universe/categories should return all categories"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/categories", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert 'categories' in data, "Response should contain 'categories'"
        
        # Validate expected categories
        expected_categories = ['major', 'large', 'mid', 'defi', 'gaming', 'ai', 'meme', 'new', 'discovered']
        for cat in expected_categories:
            assert cat in data['categories'], f"Category '{cat}' should exist"
        
        print(f"✅ Categories: {len(data['categories'])} categories available")


class TestAIUniverseCoinsByCategory:
    """Test /api/ai-universe/coins/category/{category} endpoint"""
    
    def test_get_coins_by_category_major(self):
        """GET /api/ai-universe/coins/category/major should return major coins"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/category/major", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert 'category' in data, "Response should contain 'category'"
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'count' in data, "Response should contain 'count'"
        
        assert data['category'] == 'major', "Category should be 'major'"
        assert data['count'] >= 5, f"Expected at least 5 major coins, got {data['count']}"
        
        # Validate coin structure
        if data['count'] > 0:
            coin = data['coins'][0]
            assert 'coin_id' in coin, "Coin should have 'coin_id'"
            assert 'symbol' in coin, "Coin should have 'symbol'"
            assert 'category' in coin, "Coin should have 'category'"
            assert coin['category'] == 'major', "Coin category should be 'major'"
        
        print(f"✅ Major coins: {data['count']} coins")
    
    def test_get_coins_by_category_defi(self):
        """GET /api/ai-universe/coins/category/defi should return DeFi coins"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/category/defi", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data['category'] == 'defi', "Category should be 'defi'"
        assert data['count'] >= 5, f"Expected at least 5 DeFi coins, got {data['count']}"
        
        # Validate expected DeFi coins
        coin_ids = [c['coin_id'] for c in data['coins']]
        expected_defi = ['aave', 'uniswap', 'maker']
        found_defi = [d for d in expected_defi if d in coin_ids]
        assert len(found_defi) >= 1, f"Expected at least one of {expected_defi} in DeFi coins"
        
        print(f"✅ DeFi coins: {data['count']} coins")


class TestAIUniverseGetCoin:
    """Test /api/ai-universe/coin/{coin_id} endpoint"""
    
    def test_get_coin_bitcoin_success(self):
        """GET /api/ai-universe/coin/bitcoin should return bitcoin details"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coin/bitcoin", timeout=30)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data['coin_id'] == 'bitcoin', "coin_id should be 'bitcoin'"
        assert data['symbol'] == 'BTC', "symbol should be 'BTC'"
        assert data['category'] == 'major', "category should be 'major'"
        assert data['active'] == True, "active should be True"
        
        print(f"✅ Bitcoin details: {data['symbol']} - {data['category']}")
    
    def test_get_coin_nonexistent_fails(self):
        """GET /api/ai-universe/coin/{coin_id} should return 404 for non-existent coin"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coin/nonexistent-xyz123", timeout=30)
        
        # Should return 404
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print(f"✅ Non-existent coin correctly returns 404")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
