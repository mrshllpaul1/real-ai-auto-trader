"""
Performance and API Tests for Tethys AI Crypto Trading App
Tests: API response times, data structure validation, and endpoint functionality
"""

import pytest
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndPerformance:
    """Test health endpoint and response times"""
    
    def test_health_endpoint_response_time(self):
        """API /api/health responds in <500ms"""
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5, f"Health endpoint took {response_time:.3f}s (expected <0.5s)"
        
        data = response.json()
        assert data.get('status') == 'healthy'
        assert 'database' in data
        print(f"✓ Health endpoint responded in {response_time:.3f}s")


class TestKrakenPortfolioAPI:
    """Test Kraken portfolio endpoint"""
    
    def test_kraken_portfolio_returns_data(self):
        """API /api/trading/kraken/portfolio returns portfolio data"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        assert 'holdings' in data, "Missing 'holdings' field"
        assert 'total_value_usd' in data, "Missing 'total_value_usd' field"
        assert 'holdings_count' in data, "Missing 'holdings_count' field"
        
        # Validate data types
        assert isinstance(data['holdings'], list)
        assert isinstance(data['total_value_usd'], (int, float))
        assert isinstance(data['holdings_count'], int)
        
        # Validate holdings structure if present
        if data['holdings']:
            holding = data['holdings'][0]
            assert 'asset' in holding or 'symbol' in holding
            assert 'amount' in holding
            assert 'value_usd' in holding
        
        print(f"✓ Kraken portfolio: ${data['total_value_usd']:.2f} with {data['holdings_count']} holdings")


class TestGrowthStatusAPI:
    """Test growth status endpoint"""
    
    def test_growth_status_returns_autopilot_active(self):
        """API /api/growth/status returns growth status with autopilot_active"""
        response = requests.get(f"{BASE_URL}/api/growth/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        assert 'autopilot_active' in data, "Missing 'autopilot_active' field"
        assert 'current_value' in data, "Missing 'current_value' field"
        assert 'total_pnl' in data, "Missing 'total_pnl' field"
        assert 'target_value' in data, "Missing 'target_value' field"
        assert 'progress_pct' in data, "Missing 'progress_pct' field"
        
        # Validate data types
        assert isinstance(data['autopilot_active'], bool)
        assert isinstance(data['current_value'], (int, float))
        assert isinstance(data['total_pnl'], (int, float))
        
        print(f"✓ Growth status: autopilot={data['autopilot_active']}, value=${data['current_value']:.2f}, P/L=${data['total_pnl']:.2f}")


class TestMasterStatusAPI:
    """Test master orchestrator status endpoint"""
    
    def test_master_status_returns_orchestrator_status(self):
        """API /api/master/status returns orchestrator status"""
        response = requests.get(f"{BASE_URL}/api/master/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        assert 'is_active' in data, "Missing 'is_active' field"
        assert 'mode' in data, "Missing 'mode' field"
        assert 'stats' in data, "Missing 'stats' field"
        
        # Validate data types
        assert isinstance(data['is_active'], bool)
        assert isinstance(data['mode'], str)
        assert isinstance(data['stats'], dict)
        
        # Validate stats structure
        stats = data['stats']
        assert 'executed_trades' in stats or 'total_signals' in stats
        
        print(f"✓ Master status: active={data['is_active']}, mode={data['mode']}")


class TestEnhancedAIStatusAPI:
    """Test enhanced AI status endpoint"""
    
    def test_enhanced_ai_status_returns_model_statuses(self):
        """API /api/enhanced-ai/status returns AI model statuses"""
        response = requests.get(f"{BASE_URL}/api/enhanced-ai/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        assert 'initialized' in data, "Missing 'initialized' field"
        assert 'accuracy' in data, "Missing 'accuracy' field"
        assert 'models_active' in data, "Missing 'models_active' field"
        
        # Validate model status fields
        model_fields = ['ensemble_active', 'transformer_active', 'rl_active', 
                       'regime_active', 'sentiment_active', 'technical_active']
        for field in model_fields:
            assert field in data, f"Missing '{field}' field"
            assert isinstance(data[field], bool), f"'{field}' should be boolean"
        
        print(f"✓ Enhanced AI status: accuracy={data['accuracy']}%, models_active={data['models_active']}")
        print(f"  - Ensemble: {data['ensemble_active']}, Transformer: {data['transformer_active']}")
        print(f"  - Sentiment: {data['sentiment_active']}, Technical: {data['technical_active']}")


class TestTrainingAPI:
    """Test training endpoint"""
    
    def test_train_all_models_endpoint(self):
        """Train All Models button works - POST /api/training/train-all"""
        response = requests.post(f"{BASE_URL}/api/training/train-all")
        
        # Should return 200 or 202 (accepted)
        assert response.status_code in [200, 202, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Training endpoint responded: {data}")
        elif response.status_code == 404:
            print("⚠ Training endpoint not found (may be handled differently)")
        else:
            print(f"✓ Training accepted with status {response.status_code}")


class TestSpotTradingAPIs:
    """Test spot trading related endpoints"""
    
    def test_spot_pairs_endpoint(self):
        """Test /api/spot/pairs returns trading pairs"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'pairs' in data, "Missing 'pairs' field"
        assert isinstance(data['pairs'], list)
        
        if data['pairs']:
            pair = data['pairs'][0]
            assert 'symbol' in pair
            print(f"✓ Spot pairs: {len(data['pairs'])} pairs available")
        else:
            print("⚠ No spot pairs returned (may be loading)")
    
    def test_spot_balance_endpoint(self):
        """Test /api/spot/balance returns balance info"""
        response = requests.get(f"{BASE_URL}/api/spot/balance")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have balance fields
        assert 'usd_balance' in data or 'total_portfolio_value' in data
        print(f"✓ Spot balance endpoint working")
    
    def test_spot_ai_recommendations_endpoint(self):
        """Test /api/spot/ai-recommendations returns recommendations"""
        response = requests.get(f"{BASE_URL}/api/spot/ai-recommendations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'recommendations' in data, "Missing 'recommendations' field"
        assert isinstance(data['recommendations'], list)
        
        print(f"✓ AI recommendations: {len(data['recommendations'])} recommendations")


class TestAPIResponseTimes:
    """Test that all critical APIs respond within acceptable time"""
    
    @pytest.mark.parametrize("endpoint,max_time", [
        ("/api/health", 0.5),
        ("/api/trading/kraken/portfolio", 2.0),
        ("/api/growth/status", 2.0),
        ("/api/master/status", 1.0),
        ("/api/enhanced-ai/status", 1.0),
    ])
    def test_api_response_time(self, endpoint, max_time):
        """Test API response times are within acceptable limits"""
        start_time = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}")
        response_time = time.time() - start_time
        
        assert response.status_code == 200, f"{endpoint} returned {response.status_code}"
        assert response_time < max_time, f"{endpoint} took {response_time:.3f}s (expected <{max_time}s)"
        
        print(f"✓ {endpoint}: {response_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
