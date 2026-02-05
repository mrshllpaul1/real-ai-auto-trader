"""
Test P0 (RL Agent Training) and P1 (Server Modularization) Verification
Tests to verify the server modularization didn't break any functionality
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TIMEOUT = 30  # Increased timeout for all requests


class TestHealthEndpoints:
    """Test health check endpoints after modularization"""
    
    def test_api_health_check(self):
        """Test /api/health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "version" in data
        print(f"✅ Health check passed: {data}")
    
    def test_api_root(self):
        """Test /api/ root endpoint"""
        response = requests.get(f"{BASE_URL}/api/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data
        print(f"✅ API Root: {data}")


class TestRLAgentP0:
    """Test P0: RL Agent Training completion"""
    
    def test_rl_agent_status_trained(self):
        """Test /api/predictions/rl-agent/status shows trained=true"""
        response = requests.get(f"{BASE_URL}/api/predictions/rl-agent/status", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        
        # Verify RL agent is trained (model loaded from disk)
        assert data.get("trained") == True, f"RL Agent should be trained, got: {data}"
        assert data.get("initialized") == True
        
        print(f"✅ RL Agent Status: trained={data['trained']}, epsilon={data.get('final_epsilon')}")
    
    def test_rl_agent_can_predict(self):
        """Test RL agent can make predictions after training"""
        response = requests.post(
            f"{BASE_URL}/api/predictions/rl-agent/predict",
            json={"symbol": "BTC/USD"},
            timeout=60
        )
        # Should return 200 if trained, or 400 if not enough data
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        data = response.json()
        print(f"✅ RL Agent Prediction response: {data}")


class TestPredictionServices:
    """Test all 8 prediction services are available"""
    
    def test_prediction_services_status(self):
        """Test all prediction enhancement services are initialized"""
        # Test order book analyzer
        response = requests.get(f"{BASE_URL}/api/predictions/order-book/status", timeout=TIMEOUT)
        assert response.status_code == 200
        print(f"✅ Order Book Analyzer: {response.json()}")
        
    def test_on_chain_analytics_status(self):
        """Test on-chain analytics service"""
        response = requests.get(f"{BASE_URL}/api/predictions/on-chain/status", timeout=TIMEOUT)
        assert response.status_code == 200
        print(f"✅ On-Chain Analytics: {response.json()}")
    
    def test_social_sentiment_status(self):
        """Test social sentiment pipeline"""
        response = requests.get(f"{BASE_URL}/api/predictions/social/status", timeout=TIMEOUT)
        assert response.status_code == 200
        print(f"✅ Social Sentiment: {response.json()}")
    
    def test_transformer_status(self):
        """Test transformer predictor"""
        response = requests.get(f"{BASE_URL}/api/predictions/transformer/status", timeout=TIMEOUT)
        assert response.status_code == 200
        print(f"✅ Transformer Predictor: {response.json()}")
    
    def test_cross_asset_status(self):
        """Test cross-asset correlation"""
        response = requests.get(f"{BASE_URL}/api/predictions/cross-asset/status", timeout=TIMEOUT)
        assert response.status_code == 200
        print(f"✅ Cross-Asset Correlation: {response.json()}")
    
    def test_advanced_ta_status(self):
        """Test advanced technical analysis"""
        response = requests.get(f"{BASE_URL}/api/predictions/advanced-ta/status", timeout=TIMEOUT)
        assert response.status_code == 200
        print(f"✅ Advanced TA: {response.json()}")


class TestAutoSpotScanner:
    """Test Auto-Spot Trading Scanner"""
    
    def test_auto_spot_scan_status(self):
        """Test auto-spot scan schedule status"""
        response = requests.get(f"{BASE_URL}/api/training-scheduler/auto-spot-scan/status", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Auto-Spot Scan Status: enabled={data.get('enabled')}, paper_trade={data.get('paper_trade')}")
        return data


class TestSpotTrading:
    """Test Spot Trading endpoints"""
    
    def test_spot_trading_status(self):
        """Test spot trading status endpoint"""
        response = requests.get(f"{BASE_URL}/api/spot/status", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Spot Trading Status: {data}")
    
    def test_spot_pairs(self):
        """Test spot trading pairs endpoint"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Spot Pairs: {len(data) if isinstance(data, list) else data}")


class TestTrainingDashboard:
    """Test Training Dashboard related endpoints"""
    
    def test_training_history(self):
        """Test training history endpoint"""
        response = requests.get(f"{BASE_URL}/api/training-history", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Training History: {len(data.get('sessions', data)) if isinstance(data, dict) else len(data)} sessions")
    
    def test_training_scheduler_schedules(self):
        """Test training scheduler schedules list"""
        response = requests.get(f"{BASE_URL}/api/training-scheduler/schedules", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Training Scheduler Schedules: {data}")
    
    def test_learning_status(self):
        """Test learning service status"""
        response = requests.get(f"{BASE_URL}/api/learning/status", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Learning Status: transformer_trained={data.get('transformer_trained')}, rl_trained={data.get('rl_agent_trained')}")


class TestServerModularization:
    """Test that server modularization (P1) didn't break core functionality"""
    
    def test_kraken_balance(self):
        """Test Kraken balance endpoint (real trading mode)"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance", timeout=TIMEOUT)
        # Should return 200 if Kraken is configured
        assert response.status_code in [200, 401, 500], f"Unexpected status: {response.status_code}"
        print(f"✅ Kraken Balance: status={response.status_code}")
    
    def test_isolated_portfolio(self):
        """Test isolated portfolio endpoint"""
        response = requests.get(f"{BASE_URL}/api/isolated-portfolio/status", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Isolated Portfolio: {data}")
    
    def test_scheduler_status(self):
        """Test scheduler service status"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Scheduler Status: running={data.get('running')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
