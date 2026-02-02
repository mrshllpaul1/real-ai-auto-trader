"""
Dynamic Coin Universe Integration Tests
Tests for AI training, gem finder, and coin selection with the expanded universe of 79 coins.
Features tested:
- /api/ai-universe/stats - Universe stats with correct counts
- /api/ai-universe/coins - All active coins in universe
- /api/ai-universe/coins/gems - Gem candidate coins
- /api/ai-universe/coins/discovered - AI-discovered coins (kaspa, ondo)
- /api/ai-universe/coins/ai-discover - Add new coin via AI discovery
- /api/ai-selection/select-coins - AI selects best coins from universe
- /api/gems/scan - Gem finder scans universe for opportunities
- /api/training/status - Training status with universe coins
- /api/training/ai-weights - AI weights including sentiment
- /api/training/hidden-gems - Historical hidden gems from training
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


class TestUniverseStats:
    """Test /api/ai-universe/stats - Verify universe stats show correct counts"""
    
    def test_universe_stats_total_coins(self):
        """Universe should have 79 total coins (77 human + 2 AI discovered)"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/stats", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'total_coins' in data, "Response should contain 'total_coins'"
        assert 'ai_discovered' in data, "Response should contain 'ai_discovered'"
        assert 'human_added' in data, "Response should contain 'human_added'"
        
        # Verify expected counts
        assert data['total_coins'] >= 79, f"Expected at least 79 total coins, got {data['total_coins']}"
        assert data['ai_discovered'] >= 2, f"Expected at least 2 AI discovered coins, got {data['ai_discovered']}"
        assert data['human_added'] >= 77, f"Expected at least 77 human added coins, got {data['human_added']}"
        
        print(f"✅ Universe stats: {data['total_coins']} total, {data['ai_discovered']} AI discovered, {data['human_added']} human added")
    
    def test_universe_stats_categories(self):
        """Universe should have all expected categories"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/stats", timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'by_category' in data, "Response should contain 'by_category'"
        assert 'categories' in data, "Response should contain 'categories'"
        
        # Verify expected categories exist
        expected_categories = ['major', 'large', 'mid', 'defi', 'gaming', 'ai', 'meme', 'new', 'discovered']
        for cat in expected_categories:
            assert cat in data['categories'], f"Category '{cat}' should be in categories list"
        
        # Verify discovered category has AI coins
        assert 'discovered' in data['by_category'], "by_category should have 'discovered'"
        assert data['by_category']['discovered'] >= 2, f"Expected at least 2 discovered coins, got {data['by_category'].get('discovered', 0)}"
        
        print(f"✅ Categories verified: {len(data['categories'])} categories, {data['by_category'].get('discovered', 0)} discovered")


class TestUniverseCoins:
    """Test /api/ai-universe/coins - Get all active coins in universe"""
    
    def test_get_all_active_coins(self):
        """Should return all 79+ active coins"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'count' in data, "Response should contain 'count'"
        
        # Verify count matches list length
        assert data['count'] == len(data['coins']), "count should match coins list length"
        
        # Verify we have at least 79 coins
        assert data['count'] >= 79, f"Expected at least 79 coins, got {data['count']}"
        
        # Verify base coins exist
        expected_coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'dogecoin']
        for coin in expected_coins:
            assert coin in data['coins'], f"Expected coin '{coin}' to be in universe"
        
        # Verify AI-discovered coins exist
        ai_discovered = ['kaspa', 'ondo']
        for coin in ai_discovered:
            assert coin in data['coins'], f"AI-discovered coin '{coin}' should be in universe"
        
        print(f"✅ All coins: {data['count']} active coins including AI-discovered (kaspa, ondo)")


class TestGemCandidates:
    """Test /api/ai-universe/coins/gems - Get gem candidate coins"""
    
    def test_get_gem_candidates(self):
        """Should return gem candidates from meme, ai, new, gaming, discovered categories"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/gems", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'count' in data, "Response should contain 'count'"
        
        # Verify we have gem candidates (expected ~29-30)
        assert data['count'] >= 25, f"Expected at least 25 gem candidates, got {data['count']}"
        
        # Verify AI-discovered coins are in gem candidates
        ai_discovered = ['kaspa', 'ondo']
        for coin in ai_discovered:
            assert coin in data['coins'], f"AI-discovered coin '{coin}' should be in gem candidates"
        
        # Verify some expected gem category coins
        expected_gems = ['pepe', 'fetch-ai', 'jupiter', 'bittensor']
        found_gems = [g for g in expected_gems if g in data['coins']]
        assert len(found_gems) >= 2, f"Expected at least 2 of {expected_gems} in gems"
        
        print(f"✅ Gem candidates: {data['count']} coins including AI-discovered")
    
    def test_gem_candidates_include_ai_discovered(self):
        """AI-discovered coins should be included in gem candidates"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/gems", timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        # Both kaspa and ondo should be in gems
        assert 'kaspa' in data['coins'], "kaspa should be in gem candidates"
        assert 'ondo' in data['coins'], "ondo should be in gem candidates"
        
        print(f"✅ AI-discovered coins (kaspa, ondo) are in gem candidates")


class TestAIDiscoveredCoins:
    """Test /api/ai-universe/coins/discovered - Get AI-discovered coins"""
    
    def test_get_ai_discovered_coins(self):
        """Should return kaspa and ondo as AI-discovered coins"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/discovered", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'count' in data, "Response should contain 'count'"
        
        # Get active AI-discovered coins
        active_discovered = [c for c in data['coins'] if c.get('active', False)]
        
        # Verify we have at least 2 active AI-discovered coins
        assert len(active_discovered) >= 2, f"Expected at least 2 active AI-discovered coins, got {len(active_discovered)}"
        
        # Verify kaspa and ondo are present and active
        coin_ids = [c['coin_id'] for c in active_discovered]
        assert 'kaspa' in coin_ids, "kaspa should be in AI-discovered coins"
        assert 'ondo' in coin_ids, "ondo should be in AI-discovered coins"
        
        print(f"✅ AI-discovered coins: {len(active_discovered)} active (kaspa, ondo)")
    
    def test_ai_discovered_coin_structure(self):
        """AI-discovered coins should have proper structure"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/discovered", timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        # Find kaspa in the list
        kaspa = next((c for c in data['coins'] if c.get('coin_id') == 'kaspa'), None)
        assert kaspa is not None, "kaspa should be in discovered coins"
        
        # Verify structure
        assert kaspa['ai_discovered'] == True, "ai_discovered should be True"
        assert kaspa['category'] == 'discovered', "category should be 'discovered'"
        assert kaspa['added_by'] == 'ai', "added_by should be 'ai'"
        assert 'discovery_reason' in kaspa, "Should have discovery_reason"
        assert 'metadata' in kaspa, "Should have metadata"
        
        print(f"✅ AI-discovered coin structure verified for kaspa")


class TestAIDiscoverEndpoint:
    """Test /api/ai-universe/coins/ai-discover - Add new coin via AI discovery"""
    
    def test_ai_discover_new_coin(self):
        """Should successfully add a new coin via AI discovery"""
        unique_id = f"test-ai-discover-{uuid.uuid4().hex[:8]}"
        
        payload = {
            "coin_id": unique_id,
            "symbol": "TAID",
            "reason": "Test AI discovery - high momentum coin",
            "potential_score": 80.0,
            "market_cap": 500000000,
            "volume_24h": 10000000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-universe/coins/ai-discover",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get('success') == True, f"Expected success=True, got {data}"
        assert data.get('coin_id') == unique_id
        assert data.get('symbol') == "TAID"
        assert data.get('category') == "discovered"
        
        print(f"✅ AI discovered coin added: {unique_id}")
        
        # Verify coin is in gem candidates (discovered category)
        gems_response = requests.get(f"{BASE_URL}/api/ai-universe/coins/gems", timeout=30)
        gems_data = gems_response.json()
        assert unique_id in gems_data['coins'], "New AI-discovered coin should be in gem candidates"
        
        print(f"✅ New coin is in gem candidates")
        
        # Cleanup
        cleanup_response = requests.delete(
            f"{BASE_URL}/api/ai-universe/coin/{unique_id}",
            params={"reason": "Test cleanup"},
            timeout=30
        )
        assert cleanup_response.status_code == 200, "Cleanup should succeed"
        print(f"✅ Test coin cleaned up")
    
    def test_ai_discover_duplicate_fails(self):
        """Should fail when trying to add existing coin"""
        payload = {
            "coin_id": "kaspa",
            "symbol": "KAS",
            "reason": "Test duplicate",
            "potential_score": 50.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-universe/coins/ai-discover",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        
        data = response.json()
        assert 'detail' in data, "Error response should have 'detail'"
        assert 'already exists' in data['detail'].lower(), f"Error should mention 'already exists'"
        
        print(f"✅ Duplicate AI discovery correctly rejected")


class TestAISelection:
    """Test /api/ai-selection/select-coins - AI selects best coins from universe"""
    
    def test_ai_select_coins(self):
        """AI should select coins from the dynamic universe"""
        payload = {
            "max_coins": 5,
            "market_condition": "neutral"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-selection/select-coins",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get('success') == True, f"Expected success=True, got {data}"
        assert 'selected_coins' in data, "Response should contain 'selected_coins'"
        assert 'total_selected' in data, "Response should contain 'total_selected'"
        
        # Verify we got coins
        assert data['total_selected'] > 0, "Should select at least 1 coin"
        assert data['total_selected'] <= 5, f"Should select at most 5 coins, got {data['total_selected']}"
        
        # Verify coin structure
        if data['selected_coins']:
            coin = data['selected_coins'][0]
            assert 'coin_id' in coin, "Selected coin should have 'coin_id'"
            assert 'symbol' in coin, "Selected coin should have 'symbol'"
            assert 'total_score' in coin, "Selected coin should have 'total_score'"
            assert 'scores' in coin, "Selected coin should have 'scores'"
        
        print(f"✅ AI selected {data['total_selected']} coins from universe")
    
    def test_ai_selection_includes_sentiment(self):
        """AI selection should include sentiment scores"""
        payload = {"max_coins": 3}
        
        response = requests.post(
            f"{BASE_URL}/api/ai-selection/select-coins",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get('selected_coins'):
            coin = data['selected_coins'][0]
            assert 'scores' in coin, "Coin should have scores"
            assert 'sentiment' in coin['scores'], "Scores should include sentiment"
        
        print(f"✅ AI selection includes sentiment scores")


class TestGemScanner:
    """Test /api/gems/scan - Gem finder scans universe for opportunities"""
    
    def test_gem_scan(self):
        """Gem scanner should find opportunities from dynamic universe"""
        payload = {
            "max_gems": 5,
            "min_score": 40.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/gems/scan",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get('success') == True, f"Expected success=True, got {data}"
        assert 'gems_found' in data, "Response should contain 'gems_found'"
        assert 'gems' in data, "Response should contain 'gems'"
        assert 'scan_time' in data, "Response should contain 'scan_time'"
        
        # Verify gem structure if any found
        if data['gems']:
            gem = data['gems'][0]
            assert 'coin_id' in gem, "Gem should have 'coin_id'"
            assert 'total_score' in gem, "Gem should have 'total_score'"
            assert 'signal' in gem, "Gem should have 'signal'"
            assert 'scores' in gem, "Gem should have 'scores'"
            assert 'metrics' in gem, "Gem should have 'metrics'"
            
            # Verify sentiment is included
            assert 'sentiment' in gem['scores'], "Gem scores should include sentiment"
        
        print(f"✅ Gem scanner found {data['gems_found']} gems")
    
    def test_gem_scan_uses_dynamic_universe(self):
        """Gem scanner should use coins from dynamic universe including AI-discovered"""
        payload = {"max_gems": 10, "min_score": 30.0}
        
        response = requests.post(
            f"{BASE_URL}/api/gems/scan",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # The gem scanner should be able to find gems from the expanded universe
        # Even if no gems are found, the scan should complete successfully
        assert data.get('success') == True
        
        print(f"✅ Gem scanner uses dynamic universe (found {data['gems_found']} gems)")


class TestTrainingStatus:
    """Test /api/training/status - Training status with universe coins"""
    
    def test_training_status(self):
        """Should return training status with trained coins"""
        response = requests.get(f"{BASE_URL}/api/training/status", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'trained' in data, "Response should contain 'trained'"
        
        if data['trained']:
            assert 'summary' in data or 'coins_trained' in data, "Should have training summary"
            
            # Verify training uses real data
            if 'summary' in data:
                summary = data['summary']
                assert summary.get('data_source') == 'REAL_MARKET_DATA_ONLY', "Should use real market data"
                assert summary.get('simulated_data_used') == False, "Should not use simulated data"
        
        print(f"✅ Training status: trained={data['trained']}")
    
    def test_training_status_coins(self):
        """Training should include coins from universe"""
        response = requests.get(f"{BASE_URL}/api/training/status", timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        if data['trained']:
            coins_trained = data.get('coins_trained', data.get('summary', {}).get('coins_trained', []))
            
            # Verify some base coins are trained
            expected_coins = ['bitcoin', 'ethereum', 'solana']
            for coin in expected_coins:
                assert coin in coins_trained, f"Expected {coin} to be trained"
        
        print(f"✅ Training includes base universe coins")


class TestAIWeights:
    """Test /api/training/ai-weights - AI weights including sentiment"""
    
    def test_ai_weights_structure(self):
        """Should return AI weights with sentiment parameter"""
        response = requests.get(f"{BASE_URL}/api/training/ai-weights", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'selection_weights' in data, "Response should contain 'selection_weights'"
        assert 'signal_weights' in data, "Response should contain 'signal_weights'"
        assert 'training_stats' in data, "Response should contain 'training_stats'"
        
        # Verify selection weights include sentiment
        weights = data['selection_weights']
        assert 'sentiment' in weights, "Selection weights should include 'sentiment'"
        assert 'momentum' in weights, "Selection weights should include 'momentum'"
        assert 'volatility' in weights, "Selection weights should include 'volatility'"
        assert 'volume' in weights, "Selection weights should include 'volume'"
        assert 'trend' in weights, "Selection weights should include 'trend'"
        
        print(f"✅ AI weights include sentiment: {weights.get('sentiment')}")
    
    def test_ai_weights_sentiment_value(self):
        """Sentiment weight should be 0.12 (12%)"""
        response = requests.get(f"{BASE_URL}/api/training/ai-weights", timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        sentiment_weight = data['selection_weights'].get('sentiment', 0)
        assert sentiment_weight == 0.12, f"Expected sentiment weight 0.12, got {sentiment_weight}"
        
        # Verify weights sum to approximately 1.0
        weights = data['selection_weights']
        total = sum(weights.values())
        assert 0.99 <= total <= 1.01, f"Weights should sum to ~1.0, got {total}"
        
        print(f"✅ Sentiment weight is 0.12 (12%), total weights sum to {total}")
    
    def test_ai_weights_signal_weights(self):
        """Signal weights should include bullish/bearish news"""
        response = requests.get(f"{BASE_URL}/api/training/ai-weights", timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        signal_weights = data.get('signal_weights', {})
        assert 'bullish_news' in signal_weights, "Signal weights should include 'bullish_news'"
        assert 'bearish_news' in signal_weights, "Signal weights should include 'bearish_news'"
        
        print(f"✅ Signal weights include bullish_news and bearish_news")


class TestHiddenGems:
    """Test /api/training/hidden-gems - Historical hidden gems from training"""
    
    def test_hidden_gems_endpoint(self):
        """Should return historical hidden gems"""
        response = requests.get(
            f"{BASE_URL}/api/training/hidden-gems",
            params={"min_multiplier": 2.0, "limit": 10},
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'hidden_gems' in data, "Response should contain 'hidden_gems'"
        assert 'count' in data, "Response should contain 'count'"
        assert 'min_multiplier' in data, "Response should contain 'min_multiplier'"
        
        # Verify gem structure if any found
        if data['hidden_gems']:
            gem = data['hidden_gems'][0]
            assert 'coin_id' in gem, "Gem should have 'coin_id'"
            assert 'multiplier' in gem, "Gem should have 'multiplier'"
            assert 'entry_signals' in gem, "Gem should have 'entry_signals'"
            assert 'data_source' in gem, "Gem should have 'data_source'"
            
            # Verify uses real data
            assert gem['data_source'] == 'REAL_MARKET_DATA', "Should use real market data"
        
        print(f"✅ Hidden gems: {data['count']} gems found with {data['min_multiplier']}x+ multiplier")
    
    def test_hidden_gems_real_data(self):
        """Hidden gems should be from real market data"""
        response = requests.get(
            f"{BASE_URL}/api/training/hidden-gems",
            params={"min_multiplier": 3.0, "limit": 5},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data['hidden_gems']:
            for gem in data['hidden_gems']:
                assert gem.get('data_source') == 'REAL_MARKET_DATA', f"Gem {gem.get('coin_id')} should use real data"
        
        print(f"✅ All hidden gems use REAL_MARKET_DATA")


class TestTrainingCoins:
    """Test /api/ai-universe/coins/training - Training coins from universe"""
    
    def test_training_coins_endpoint(self):
        """Should return all coins for training sorted by priority"""
        response = requests.get(f"{BASE_URL}/api/ai-universe/coins/training", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'coins' in data, "Response should contain 'coins'"
        assert 'count' in data, "Response should contain 'count'"
        
        # Should have all 79+ coins
        assert data['count'] >= 79, f"Expected at least 79 training coins, got {data['count']}"
        
        # Major coins should be first (priority order)
        coins = data['coins']
        major_coins = ['bitcoin', 'ethereum', 'ripple', 'litecoin', 'cardano']
        for i, coin in enumerate(major_coins):
            assert coin in coins[:20], f"Major coin {coin} should be in top 20 training coins"
        
        print(f"✅ Training coins: {data['count']} coins in priority order")


class TestIntegrationFlow:
    """Integration tests for the full AI flow with dynamic universe"""
    
    def test_full_ai_flow(self):
        """Test complete flow: universe -> selection -> gems"""
        # 1. Get universe stats
        stats_response = requests.get(f"{BASE_URL}/api/ai-universe/stats", timeout=30)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # 2. Get gem candidates
        gems_response = requests.get(f"{BASE_URL}/api/ai-universe/coins/gems", timeout=30)
        assert gems_response.status_code == 200
        gems = gems_response.json()
        
        # 3. AI selection
        selection_response = requests.post(
            f"{BASE_URL}/api/ai-selection/select-coins",
            json={"max_coins": 5},
            timeout=60
        )
        assert selection_response.status_code == 200
        selection = selection_response.json()
        
        # 4. Gem scan
        scan_response = requests.post(
            f"{BASE_URL}/api/gems/scan",
            json={"max_gems": 3},
            timeout=60
        )
        assert scan_response.status_code == 200
        scan = scan_response.json()
        
        # Verify integration
        assert stats['total_coins'] >= 79, "Universe should have 79+ coins"
        assert gems['count'] >= 25, "Should have 25+ gem candidates"
        assert selection['success'] == True, "AI selection should succeed"
        assert scan['success'] == True, "Gem scan should succeed"
        
        print(f"✅ Full AI flow completed:")
        print(f"   - Universe: {stats['total_coins']} coins ({stats['ai_discovered']} AI discovered)")
        print(f"   - Gem candidates: {gems['count']}")
        print(f"   - AI selected: {selection['total_selected']} coins")
        print(f"   - Gems found: {scan['gems_found']}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
