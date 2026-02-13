"""
Test Tethys Sentiment Scoring and WebSocket Training Progress
==============================================================
Tests for:
- Sentiment API endpoints (/api/tethys/sentiment, /api/tethys/sentiment/{symbol})
- WebSocket endpoint for training progress
- Training start/stop/status endpoints
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
        # Verify overall_score exists and is valid
        assert "overall_score" in data
        assert isinstance(data["overall_score"], (int, float))
        assert 0 <= data["overall_score"] <= 1
        
        # Verify signal exists
        assert "signal" in data
        assert data["signal"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        
        # Verify breakdown exists with coin sentiments
        assert "breakdown" in data
        assert isinstance(data["breakdown"], dict)
        
        # Verify coins_analyzed count
        assert "coins_analyzed" in data
        assert data["coins_analyzed"] >= 0
        
        print(f"Market sentiment: {data['overall_score']} ({data['signal']})")
        print(f"Breakdown: {data['breakdown']}")
    
    def test_btc_sentiment_returns_score(self):
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
        
        assert "updated_at" in data
        
        print(f"BTC sentiment: {data['score']} ({data['signal']}) confidence: {data['confidence']}")
    
    def test_eth_sentiment_returns_score(self):
        """Test /api/tethys/sentiment/ETH returns individual coin sentiment"""
        response = requests.get(f"{BASE_URL}/api/tethys/sentiment/ETH")
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "ETH"
        assert "score" in data
        assert "signal" in data
        
        print(f"ETH sentiment: {data['score']} ({data['signal']})")
    
    def test_sentiment_with_sources(self):
        """Test sentiment endpoint with include_sources=true"""
        response = requests.get(f"{BASE_URL}/api/tethys/sentiment/BTC?include_sources=true")
        assert response.status_code == 200
        
        data = response.json()
        # When include_sources=true, sources should be included
        if "sources" in data:
            sources = data["sources"]
            # Check for expected source types
            expected_sources = ["news", "technical", "volume", "social"]
            for source in expected_sources:
                if source in sources:
                    assert "score" in sources[source]
                    assert "available" in sources[source]
            print(f"Sources included: {list(sources.keys())}")
    
    def test_sentiment_recommendation(self):
        """Test sentiment recommendation endpoint"""
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
        assert "size_adjustment" in rec
        assert "reason" in rec
        
        print(f"Recommendation for BTC: {rec['action']} - {rec['reason']}")


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
        # Verify training section
        assert "training" in data
        assert "is_training" in data["training"]
        
        # Verify registry section
        assert "registry" in data
        assert "experiment_name" in data["registry"]
        
        # Verify monitoring section
        assert "monitoring" in data
        
        print(f"Dashboard: training={data['training']['is_training']}, experiment={data['registry']['experiment_name']}")
    
    def test_start_training(self):
        """Test /api/tethys-train/start initiates training"""
        response = requests.post(
            f"{BASE_URL}/api/tethys-train/start",
            json={"episodes": 5, "symbol": "BTC/USD"}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should return status (either started or already_training)
        assert "status" in data
        assert data["status"] in ["training_started", "already_training"]
        
        print(f"Start training response: {data['status']}")
    
    def test_stop_training(self):
        """Test /api/tethys-train/stop stops training"""
        response = requests.post(f"{BASE_URL}/api/tethys-train/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "stop_requested"
        
        print("Stop training: stop_requested")
    
    def test_registry_status(self):
        """Test /api/tethys-train/registry/status returns registry info"""
        response = requests.get(f"{BASE_URL}/api/tethys-train/registry/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "experiment_name" in data
        assert "tracking_uri" in data
        
        print(f"Registry: experiment={data['experiment_name']}")


class TestWebSocketEndpoint:
    """Test WebSocket endpoint exists (connection test)"""
    
    def test_websocket_endpoint_exists(self):
        """Verify WebSocket endpoint is configured (HTTP upgrade check)"""
        # WebSocket endpoints return 403 or upgrade required on HTTP GET
        # This verifies the route exists
        response = requests.get(f"{BASE_URL}/api/tethys-train/ws/progress")
        # WebSocket endpoints typically return 403 Forbidden or 426 Upgrade Required
        # when accessed via HTTP instead of WebSocket protocol
        assert response.status_code in [403, 426, 400, 405]
        print(f"WebSocket endpoint exists (HTTP status: {response.status_code})")


class TestTethysDashboard:
    """Test main Tethys dashboard endpoint"""
    
    def test_tethys_dashboard(self):
        """Test /api/tethys/dashboard returns complete data"""
        response = requests.get(f"{BASE_URL}/api/tethys/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        # Verify agent info
        assert "agent" in data
        assert data["agent"]["name"] == "Tethys"
        assert data["agent"]["status"] == "operational"
        
        # Verify risk section
        assert "risk" in data
        assert "limits" in data["risk"]
        assert "state" in data["risk"]
        
        # Verify audit section
        assert "audit" in data
        
        # Verify uncertainty section
        assert "uncertainty" in data
        
        print(f"Dashboard: agent={data['agent']['name']}, status={data['agent']['status']}")
    
    def test_tethys_status(self):
        """Test /api/tethys/status returns safety system status"""
        response = requests.get(f"{BASE_URL}/api/tethys/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "agent" in data
        print(f"Tethys status: {data['agent']}")


class TestHealthCheck:
    """Basic health check"""
    
    def test_health(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        
        print("Health check: OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
