"""
Test Tethys Trading App - Core Features
Tests Command Center, Growth Engine, Master Orchestrator, Enhanced AI, and Spot Trading APIs
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
        assert data.get('database') == 'connected'
        print(f"✓ Health check passed: {data}")


class TestKrakenPortfolio:
    """Kraken Portfolio API tests - Command Center Dashboard"""
    
    def test_kraken_portfolio_returns_total_value(self):
        """Test /api/trading/kraken/portfolio returns total_value_usd"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'total_value_usd' in data, "Missing total_value_usd field"
        assert 'holdings' in data, "Missing holdings field"
        assert isinstance(data['total_value_usd'], (int, float)), "total_value_usd should be numeric"
        
        # Verify portfolio value is reasonable (should be around $1168 based on test data)
        assert data['total_value_usd'] > 0, "Portfolio value should be positive"
        
        print(f"✓ Kraken Portfolio: ${data['total_value_usd']:.2f}")
        print(f"  Holdings count: {len(data.get('holdings', []))}")
    
    def test_kraken_portfolio_holdings_structure(self):
        """Test holdings have correct structure"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio")
        assert response.status_code == 200
        data = response.json()
        
        holdings = data.get('holdings', [])
        if holdings:
            holding = holdings[0]
            required_fields = ['asset', 'symbol', 'amount', 'price_usd', 'value_usd']
            for field in required_fields:
                assert field in holding, f"Missing field: {field}"
            print(f"✓ Holdings structure verified with {len(holdings)} assets")


class TestGrowthEngine:
    """Growth Engine API tests - $500 → $100K tab"""
    
    def test_growth_status_returns_required_fields(self):
        """Test /api/growth/status returns autopilot_active and current_value"""
        response = requests.get(f"{BASE_URL}/api/growth/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'autopilot_active' in data, "Missing autopilot_active field"
        assert 'current_value' in data, "Missing current_value field"
        assert 'total_pnl' in data, "Missing total_pnl field"
        assert 'target_value' in data, "Missing target_value field"
        
        # Verify data types
        assert isinstance(data['autopilot_active'], bool), "autopilot_active should be boolean"
        assert isinstance(data['current_value'], (int, float)), "current_value should be numeric"
        
        print(f"✓ Growth Status:")
        print(f"  Autopilot: {data['autopilot_active']}")
        print(f"  Current Value: ${data['current_value']:.2f}")
        print(f"  Total P/L: ${data['total_pnl']:.2f}")
        print(f"  Progress: {data.get('progress_pct', 0):.2f}%")
    
    def test_growth_start_endpoint(self):
        """Test /api/growth/start endpoint"""
        response = requests.post(f"{BASE_URL}/api/growth/start")
        assert response.status_code == 200
        data = response.json()
        assert 'success' in data or 'autopilot_active' in data
        print(f"✓ Growth start endpoint working")
    
    def test_growth_stop_endpoint(self):
        """Test /api/growth/stop endpoint"""
        response = requests.post(f"{BASE_URL}/api/growth/stop")
        assert response.status_code == 200
        data = response.json()
        assert 'success' in data or 'autopilot_active' in data
        print(f"✓ Growth stop endpoint working")


class TestMasterOrchestrator:
    """Master Orchestrator API tests - Master Control tab"""
    
    def test_master_status_returns_is_active(self):
        """Test /api/master/status returns is_active"""
        response = requests.get(f"{BASE_URL}/api/master/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'is_active' in data, "Missing is_active field"
        assert 'mode' in data, "Missing mode field"
        
        # Verify data types
        assert isinstance(data['is_active'], bool), "is_active should be boolean"
        
        print(f"✓ Master Orchestrator Status:")
        print(f"  Active: {data['is_active']}")
        print(f"  Mode: {data['mode']}")
        print(f"  Executed Trades: {data.get('stats', {}).get('executed_trades', 0)}")
    
    def test_master_start_endpoint(self):
        """Test /api/master/start endpoint"""
        response = requests.post(f"{BASE_URL}/api/master/start")
        assert response.status_code == 200
        print(f"✓ Master start endpoint working")
    
    def test_master_stop_endpoint(self):
        """Test /api/master/stop endpoint"""
        response = requests.post(f"{BASE_URL}/api/master/stop")
        assert response.status_code == 200
        print(f"✓ Master stop endpoint working")


class TestEnhancedAI:
    """Enhanced AI API tests - AI Command Center"""
    
    def test_enhanced_ai_status_returns_model_statuses(self):
        """Test /api/enhanced-ai/status returns model statuses"""
        response = requests.get(f"{BASE_URL}/api/enhanced-ai/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'initialized' in data, "Missing initialized field"
        assert 'accuracy' in data, "Missing accuracy field"
        assert 'models_active' in data, "Missing models_active field"
        
        # Verify model status fields
        model_fields = ['ensemble_active', 'transformer_active', 'rl_active', 
                       'regime_active', 'sentiment_active', 'technical_active']
        for field in model_fields:
            assert field in data, f"Missing model status field: {field}"
        
        print(f"✓ Enhanced AI Status:")
        print(f"  Initialized: {data['initialized']}")
        print(f"  Accuracy: {data['accuracy']}%")
        print(f"  Win Rate: {data.get('win_rate', 0)}%")
        print(f"  Models Active: {data['models_active']}")
        print(f"  Ensemble: {data['ensemble_active']}, Transformer: {data['transformer_active']}")
        print(f"  Sentiment: {data['sentiment_active']}, Technical: {data['technical_active']}")


class TestSpotTrading:
    """Spot Trading API tests"""
    
    def test_spot_ai_recommendations_returns_array(self):
        """Test /api/spot/ai-recommendations returns recommendations array"""
        response = requests.get(f"{BASE_URL}/api/spot/ai-recommendations")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'recommendations' in data, "Missing recommendations field"
        assert isinstance(data['recommendations'], list), "recommendations should be an array"
        
        # Verify recommendation structure if any exist
        if data['recommendations']:
            rec = data['recommendations'][0]
            required_fields = ['symbol', 'signal', 'score', 'confidence']
            for field in required_fields:
                assert field in rec, f"Missing recommendation field: {field}"
            
            print(f"✓ Spot AI Recommendations: {len(data['recommendations'])} coins")
            for r in data['recommendations'][:5]:
                print(f"  {r['symbol']}: {r['signal']} (score: {r['score']}, conf: {r['confidence']})")
        else:
            print(f"✓ Spot AI Recommendations endpoint working (no recommendations currently)")
    
    def test_spot_status_endpoint(self):
        """Test /api/spot/status endpoint"""
        response = requests.get(f"{BASE_URL}/api/spot/status")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Spot status endpoint working")
    
    def test_spot_pairs_endpoint(self):
        """Test /api/spot/pairs endpoint"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        assert response.status_code == 200
        data = response.json()
        assert 'pairs' in data, "Missing pairs field"
        print(f"✓ Spot pairs endpoint: {len(data.get('pairs', []))} pairs available")
    
    def test_spot_balance_endpoint(self):
        """Test /api/spot/balance endpoint"""
        response = requests.get(f"{BASE_URL}/api/spot/balance")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Spot balance endpoint working")


class TestUpgrades:
    """Upgrades API tests - Upgrades tab"""
    
    def test_upgrades_status_endpoint(self):
        """Test /api/upgrades/status endpoint"""
        response = requests.get(f"{BASE_URL}/api/upgrades/status")
        assert response.status_code == 200
        data = response.json()
        
        # Check for features field
        if 'features' in data:
            features = data['features']
            expected_features = ['whale_tracking', 'sentiment', 'arbitrage', 
                               'trailing_stops', 'rebalancer', 'ab_testing']
            for feature in expected_features:
                if feature in features:
                    print(f"  {feature}: {features[feature].get('is_monitoring', features[feature].get('enabled', 'N/A'))}")
        
        print(f"✓ Upgrades status endpoint working")


class TestTethysAI:
    """Tethys AI specific tests"""
    
    def test_tethys_train_status(self):
        """Test /api/tethys-train/status endpoint"""
        response = requests.get(f"{BASE_URL}/api/tethys-train/status")
        # May return 404 if not implemented, which is acceptable
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Tethys train status: {data.get('is_active', 'N/A')}")
        else:
            print(f"⚠ Tethys train status endpoint returned {response.status_code}")
    
    def test_learning_status(self):
        """Test /api/learning/status endpoint"""
        response = requests.get(f"{BASE_URL}/api/learning/status")
        # May return 404 if not implemented, which is acceptable
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Learning status endpoint working")
        else:
            print(f"⚠ Learning status endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
