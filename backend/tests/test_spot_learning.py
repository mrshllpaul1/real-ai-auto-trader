"""
Test Spot Trading and Learning API Endpoints
Tests for new Spot Trading and AI Learning features
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tethys-trade.preview.emergentagent.com')


class TestSpotTradingStatus:
    """Test /api/spot/status endpoint"""
    
    def test_spot_status_returns_200(self):
        """Test spot trading status endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/spot/status")
        assert response.status_code == 200
        
    def test_spot_status_has_required_fields(self):
        """Test spot status response has required fields"""
        response = requests.get(f"{BASE_URL}/api/spot/status")
        data = response.json()
        
        assert "available" in data
        assert "features" in data
        assert "supported_pairs" in data
        assert "timestamp" in data
        
    def test_spot_status_kraken_connected(self):
        """Test Kraken is connected"""
        response = requests.get(f"{BASE_URL}/api/spot/status")
        data = response.json()
        
        assert data["available"] == True
        assert "kraken_connected" in data["features"]
        
    def test_spot_status_has_budget_info(self):
        """Test budget info is present"""
        response = requests.get(f"{BASE_URL}/api/spot/status")
        data = response.json()
        
        if data.get("budget"):
            assert "available_usd" in data["budget"]
            assert "total_value" in data["budget"]
            assert "real_trading_enabled" in data["budget"]


class TestSpotTradingPairs:
    """Test /api/spot/pairs endpoint"""
    
    def test_pairs_returns_200(self):
        """Test pairs endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        assert response.status_code == 200
        
    def test_pairs_has_required_structure(self):
        """Test pairs response has required structure"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        data = response.json()
        
        assert "pairs" in data
        assert "count" in data
        assert "timestamp" in data
        assert isinstance(data["pairs"], list)
        
    def test_pairs_have_price_data(self):
        """Test each pair has price data"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        data = response.json()
        
        assert len(data["pairs"]) > 0
        
        for pair in data["pairs"][:5]:  # Check first 5 pairs
            assert "symbol" in pair
            assert "name" in pair
            assert "price" in pair
            assert "change_24h" in pair
            
    def test_pairs_include_major_cryptos(self):
        """Test major cryptos are included"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        data = response.json()
        
        symbols = [p["symbol"] for p in data["pairs"]]
        
        # Check for major cryptos
        assert "BTC" in symbols
        assert "ETH" in symbols
        
    def test_pairs_have_24h_change(self):
        """Test pairs have 24h change data"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        data = response.json()
        
        for pair in data["pairs"][:5]:
            assert "change_24h" in pair
            assert isinstance(pair["change_24h"], (int, float))


class TestSpotTradingBalance:
    """Test /api/spot/balance endpoint"""
    
    def test_balance_returns_200(self):
        """Test balance endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/spot/balance")
        assert response.status_code == 200
        
    def test_balance_has_required_fields(self):
        """Test balance response has required fields"""
        response = requests.get(f"{BASE_URL}/api/spot/balance")
        data = response.json()
        
        assert "holdings" in data
        assert "usd_balance" in data
        assert "total_crypto_value" in data
        assert "total_portfolio_value" in data
        assert "holdings_count" in data
        
    def test_balance_holdings_structure(self):
        """Test holdings have correct structure"""
        response = requests.get(f"{BASE_URL}/api/spot/balance")
        data = response.json()
        
        if data["holdings"]:
            holding = data["holdings"][0]
            assert "symbol" in holding
            assert "amount" in holding
            assert "usd_value" in holding


class TestSpotTradingPairDetails:
    """Test /api/spot/pair/{symbol} endpoint"""
    
    def test_btc_pair_details(self):
        """Test BTC pair details"""
        response = requests.get(f"{BASE_URL}/api/spot/pair/BTC")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "BTC"
        assert "price" in data
        assert "last" in data["price"]
        
    def test_eth_pair_details(self):
        """Test ETH pair details"""
        response = requests.get(f"{BASE_URL}/api/spot/pair/ETH")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "ETH"
        
    def test_invalid_pair_returns_404(self):
        """Test invalid pair returns 404"""
        response = requests.get(f"{BASE_URL}/api/spot/pair/INVALID123")
        assert response.status_code == 404


class TestLearningStatus:
    """Test /api/learning/status endpoint"""
    
    def test_learning_status_returns_200(self):
        """Test learning status endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/learning/status")
        assert response.status_code == 200
        
    def test_learning_status_has_required_fields(self):
        """Test learning status has required fields"""
        response = requests.get(f"{BASE_URL}/api/learning/status")
        data = response.json()
        
        assert "learning_active" in data
        assert "stats" in data
        assert "models" in data
        
    def test_learning_stats_structure(self):
        """Test learning stats have correct structure"""
        response = requests.get(f"{BASE_URL}/api/learning/status")
        data = response.json()
        
        stats = data["stats"]
        assert "total_sessions" in stats
        assert "current_accuracy" in stats
        
    def test_learning_models_status(self):
        """Test model statuses are present"""
        response = requests.get(f"{BASE_URL}/api/learning/status")
        data = response.json()
        
        models = data["models"]
        assert "transformer" in models
        assert "rl_agent" in models
        assert "regime" in models


class TestLearningRecommendations:
    """Test /api/learning/recommendations endpoint"""
    
    def test_recommendations_returns_200(self):
        """Test recommendations endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/learning/recommendations")
        assert response.status_code == 200
        
    def test_recommendations_has_required_fields(self):
        """Test recommendations response has required fields"""
        response = requests.get(f"{BASE_URL}/api/learning/recommendations")
        data = response.json()
        
        assert "recommendations" in data
        assert "count" in data
        assert "timestamp" in data
        
    def test_recommendations_structure(self):
        """Test each recommendation has correct structure"""
        response = requests.get(f"{BASE_URL}/api/learning/recommendations")
        data = response.json()
        
        if data["recommendations"]:
            rec = data["recommendations"][0]
            assert "priority" in rec
            assert "category" in rec
            assert "message" in rec
            assert "action" in rec


class TestSpotTradingRecentTrades:
    """Test /api/spot/recent-trades endpoint"""
    
    def test_recent_trades_returns_200(self):
        """Test recent trades endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/spot/recent-trades")
        assert response.status_code == 200
        
    def test_recent_trades_structure(self):
        """Test recent trades response structure"""
        response = requests.get(f"{BASE_URL}/api/spot/recent-trades")
        data = response.json()
        
        assert "trades" in data
        assert "count" in data


class TestLearningHistory:
    """Test /api/learning/history endpoint"""
    
    def test_learning_history_returns_200(self):
        """Test learning history endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/learning/history")
        assert response.status_code == 200
        
    def test_learning_history_structure(self):
        """Test learning history response structure"""
        response = requests.get(f"{BASE_URL}/api/learning/history")
        data = response.json()
        
        assert "history" in data
        assert "count" in data


class TestIntegration:
    """Integration tests for Spot Trading and Learning"""
    
    def test_spot_and_learning_services_available(self):
        """Test both services are available"""
        spot_res = requests.get(f"{BASE_URL}/api/spot/status")
        learning_res = requests.get(f"{BASE_URL}/api/learning/status")
        
        assert spot_res.status_code == 200
        assert learning_res.status_code == 200
        
    def test_spot_pairs_have_live_prices(self):
        """Test spot pairs have live prices from Kraken"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        data = response.json()
        
        # At least some pairs should have non-zero prices
        prices_with_data = [p for p in data["pairs"] if p["price"] > 0]
        assert len(prices_with_data) > 10, "Expected at least 10 pairs with live prices"
        
    def test_balance_reflects_real_holdings(self):
        """Test balance shows real Kraken holdings"""
        response = requests.get(f"{BASE_URL}/api/spot/balance")
        data = response.json()
        
        # Should have some holdings based on previous test context
        assert data["holdings_count"] > 0, "Expected some holdings"
        assert data["total_portfolio_value"] > 0, "Expected positive portfolio value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
