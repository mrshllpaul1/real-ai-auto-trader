"""
Test Sentiment Scoring and WebSocket Training Progress
=======================================================
Tests for the new sentiment scoring system and WebSocket training updates.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSentimentEndpoints:
    """Test sentiment scoring API endpoints"""
    
    def test_market_sentiment_returns_overall_score(self):
        """Test /api/tethys/sentiment returns overall_score and breakdown"""
        response = requests.get(f"{BASE_URL}/api/tethys/sentiment")
        assert response.status_code == 200
        
        data = response.json()
        # Verify overall_score exists and is a number between 0 and 1
        assert "overall_score" in data
        assert isinstance(data["overall_score"], (int, float))
        assert 0 <= data["overall_score"] <= 1
        
        # Verify signal exists
        assert "signal" in data
        assert data["signal"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        
        # Verify breakdown exists with coin data
        assert "breakdown" in data
        assert isinstance(data["breakdown"], dict)
        
        # Verify coins_analyzed count
        assert "coins_analyzed" in data
        assert data["coins_analyzed"] >= 0
        
        print(f"Market sentiment: {data['overall_score']} ({data['signal']})")
        print(f"Breakdown: {data['breakdown']}")
    
    def test_coin_sentiment_btc(self):
        """Test /api/tethys/sentiment/BTC returns individual coin sentiment"""
        response = requests.get(f"{BASE_URL}/api/tethys/sentiment/BTC")
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields
        assert "symbol" in data
        assert data["symbol"] == "BTC"
        
        assert "score" in data
        assert isinstance(data["score"], (int, float))
        assert 0 <= data["score"] <= 1
        
        assert "signal" in data
        assert data["signal"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        
        print(f"BTC sentiment: {data['score']} ({data['signal']}) confidence: {data['confidence']}")
    
    def test_coin_sentiment_eth(self):
        """Test /api/tethys/sentiment/ETH returns individual coin sentiment"""
        response = requests.get(f"{BASE_URL}/api/tethys/sentiment/ETH")
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "ETH"
        assert "score" in data
        assert "signal" in data
        
        print(f"ETH sentiment: {data['score']} ({data['signal']})")
    
    def test_coin_sentiment_with_sources(self):
        """Test /api/tethys/sentiment/BTC?include_sources=true returns source breakdown"""
        response = requests.get(f"{BASE_URL}/api/tethys/sentiment/BTC?include_sources=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "sources" in data
        
        sources = data["sources"]
        # Verify source categories exist
        expected_sources = ["news", "technical", "volume", "social"]
        for source in expected_sources:
            assert source in sources, f"Missing source: {source}"
            assert "score" in sources[source]
            assert "available" in sources[source]
        
        print(f"BTC sources: {sources}")
    
    def test_sentiment_recommendation(self):
        """Test /api/tethys/sentiment/recommendation endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/tethys/sentiment/recommendation?symbol=BTC&current_position=0"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert "sentiment" in data
        assert "recommendation" in data
        
        rec = data["recommendation"]
        assert "action" in rec
        assert rec["action"] in ["BUY", "SELL", "HOLD"]
        assert "reason" in rec
        
        print(f"BTC recommendation: {rec['action']} - {rec['reason']}")


class TestTrainingEndpoints:
    """Test training API endpoints"""
    
    def test_training_status(self):
        """Test /api/tethys-train/status returns training status"""
        response = requests.get(f"{BASE_URL}/api/tethys-train/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "is_training" in data
        assert isinstance(data["is_training"], bool)
        
        assert "current_episode" in data
        assert "total_episodes" in data
        assert "progress_pct" in data
        
        print(f"Training status: is_training={data['is_training']}, progress={data['progress_pct']}%")
    
    def test_training_dashboard(self):
        """Test /api/tethys-train/dashboard returns full dashboard data"""
        response = requests.get(f"{BASE_URL}/api/tethys-train/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "training" in data
        assert "registry" in data
        assert "monitoring" in data
        
        print(f"Training dashboard: {list(data.keys())}")
    
    def test_start_training(self):
        """Test /api/tethys-train/start can start training"""
        response = requests.post(
            f"{BASE_URL}/api/tethys-train/start",
            json={"episodes": 2, "symbol": "BTC/USD"}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Either training started or already training
        assert data["status"] in ["training_started", "already_training"]
        
        print(f"Start training response: {data['status']}")
    
    def test_stop_training(self):
        """Test /api/tethys-train/stop can stop training"""
        response = requests.post(f"{BASE_URL}/api/tethys-train/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        
        print(f"Stop training response: {data['status']}")


class TestWebSocketEndpoint:
    """Test WebSocket endpoint exists (connection test)"""
    
    def test_websocket_endpoint_exists(self):
        """Verify WebSocket endpoint is accessible via HTTP upgrade check"""
        # WebSocket endpoints return 403 or upgrade required when accessed via HTTP
        # This verifies the route exists
        response = requests.get(f"{BASE_URL}/api/tethys-train/ws/progress")
        # WebSocket endpoints typically return 403 or 400 when accessed via HTTP
        # A 404 would mean the endpoint doesn't exist
        assert response.status_code != 404, "WebSocket endpoint not found"
        print(f"WebSocket endpoint exists (HTTP status: {response.status_code})")


class TestTethysDashboard:
    """Test Tethys dashboard endpoint"""
    
    def test_tethys_dashboard(self):
        """Test /api/tethys/dashboard returns all dashboard data"""
        response = requests.get(f"{BASE_URL}/api/tethys/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "agent" in data
        assert "risk" in data
        assert "audit" in data
        assert "uncertainty" in data
        
        # Verify agent info
        assert data["agent"]["name"] == "Tethys"
        assert data["agent"]["status"] == "operational"
        
        print(f"Tethys dashboard: agent={data['agent']['name']}, status={data['agent']['status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
