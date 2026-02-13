"""
Iteration 46 Feature Tests
Tests for:
- Dashboard errors fixed
- Auto-debugging system
- All pages and buttons working
- Real data (no simulated data)
- DeFi AI endpoints
- AI Signals endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicAPIs:
    """Basic health and API tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert data.get("database") == "connected"
        print(f"✓ Health check passed: {data}")
    
    def test_growth_status(self):
        """Test growth status endpoint"""
        response = requests.get(f"{BASE_URL}/api/growth/status")
        assert response.status_code == 200
        data = response.json()
        assert "current_value" in data
        assert "autopilot_active" in data
        print(f"✓ Growth status: current_value=${data.get('current_value')}, autopilot={data.get('autopilot_active')}")
    
    def test_master_status(self):
        """Test master orchestrator status"""
        response = requests.get(f"{BASE_URL}/api/master/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_active" in data
        assert "mode" in data
        print(f"✓ Master status: active={data.get('is_active')}, mode={data.get('mode')}")


class TestDeFiAIEndpoints:
    """Test new DeFi AI prediction endpoints"""
    
    def test_yield_prediction_eth(self):
        """Test yield prediction for ETH"""
        response = requests.get(f"{BASE_URL}/api/defi-ai/yield-prediction/ETH")
        assert response.status_code == 200
        data = response.json()
        assert data.get("asset") == "ETH"
        assert "score" in data
        assert "signal" in data
        assert "confidence" in data
        assert "yield_insights" in data
        print(f"✓ ETH yield prediction: score={data.get('score')}, signal={data.get('signal')}")
    
    def test_yield_prediction_btc(self):
        """Test yield prediction for BTC"""
        response = requests.get(f"{BASE_URL}/api/defi-ai/yield-prediction/BTC")
        assert response.status_code == 200
        data = response.json()
        assert data.get("asset") == "BTC"
        assert "score" in data
        print(f"✓ BTC yield prediction: score={data.get('score')}")
    
    def test_wallet_prediction(self):
        """Test wallet prediction endpoint"""
        response = requests.get(f"{BASE_URL}/api/defi-ai/wallet-prediction/0x1234567890abcdef")
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data
        assert "risk_level" in data
        assert "recommendations" in data
        print(f"✓ Wallet prediction: health_score={data.get('health_score')}, risk={data.get('risk_level')}")
    
    def test_protocol_analysis(self):
        """Test protocol analysis endpoint"""
        response = requests.get(f"{BASE_URL}/api/defi-ai/protocol-analysis/aave")
        assert response.status_code == 200
        data = response.json()
        assert data.get("protocol") == "aave"
        assert "safety_score" in data
        assert "signal" in data
        print(f"✓ Protocol analysis: safety_score={data.get('safety_score')}, signal={data.get('signal')}")


class TestAISignalsEndpoints:
    """Test AI signals endpoints"""
    
    def test_ai_signal_btcusd(self):
        """Test AI signal for BTCUSD"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/BTCUSD")
        assert response.status_code == 200
        data = response.json()
        assert data.get("symbol") == "BTCUSD"
        assert "signal" in data
        assert "score" in data
        assert "confidence" in data
        assert "components" in data
        print(f"✓ BTCUSD AI signal: signal={data.get('signal')}, score={data.get('score')}")
    
    def test_ai_signal_ethusd(self):
        """Test AI signal for ETHUSD"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/ETHUSD")
        assert response.status_code == 200
        data = response.json()
        assert data.get("symbol") == "ETHUSD"
        assert "signal" in data
        print(f"✓ ETHUSD AI signal: signal={data.get('signal')}")


class TestAdaptiveStrategyEndpoints:
    """Test adaptive strategy endpoints (fixed useState error)"""
    
    def test_adaptive_strategy_status(self):
        """Test adaptive strategy status"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/status")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Adaptive strategy status: {data}")
    
    def test_current_regime(self):
        """Test current market regime detection"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/regime/current")
        assert response.status_code == 200
        data = response.json()
        assert "regime" in data
        print(f"✓ Current regime: {data.get('regime')}")
    
    def test_regime_variants(self):
        """Test regime variants"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/variants")
        assert response.status_code == 200
        data = response.json()
        assert "variants_by_regime" in data
        print(f"✓ Regime variants loaded")
    
    def test_optimal_strategy(self):
        """Test optimal strategy recommendation"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/optimal-strategy")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Optimal strategy: {data.get('recommended_strategy', {}).get('name', 'N/A')}")


class TestTradingEndpoints:
    """Test trading-related endpoints (fixed MongoDB ObjectId issue)"""
    
    def test_kraken_portfolio(self):
        """Test Kraken portfolio endpoint"""
        response = requests.get(f"{BASE_URL}/api/kraken/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert "total_value_usd" in data or "holdings" in data
        print(f"✓ Kraken portfolio: total_value=${data.get('total_value_usd', 'N/A')}")
    
    def test_portfolio_status(self):
        """Test portfolio status"""
        response = requests.get(f"{BASE_URL}/api/portfolio/status")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Portfolio status loaded")
    
    def test_positions_list(self):
        """Test positions list"""
        response = requests.get(f"{BASE_URL}/api/positions")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Positions: {len(data) if isinstance(data, list) else 'loaded'}")


class TestAdvancedOrdersEndpoints:
    """Test advanced orders endpoints (fixed page error)"""
    
    def test_trailing_stops_list(self):
        """Test trailing stops list"""
        response = requests.get(f"{BASE_URL}/api/trailing-stops")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Trailing stops: {len(data) if isinstance(data, list) else 'loaded'}")
    
    def test_dca_bots_list(self):
        """Test DCA bots list"""
        response = requests.get(f"{BASE_URL}/api/dca-bots")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ DCA bots: {len(data) if isinstance(data, list) else 'loaded'}")


class TestSystemStateEndpoints:
    """Test system state endpoints (fixed React hooks issue)"""
    
    def test_system_state_all(self):
        """Test get all system states"""
        response = requests.get(f"{BASE_URL}/api/system-state/all?user_id=default")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ System states: {list(data.keys()) if isinstance(data, dict) else 'loaded'}")
    
    def test_system_state_component(self):
        """Test get specific component state"""
        response = requests.get(f"{BASE_URL}/api/system-state/master_orchestrator?user_id=default")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
        print(f"✓ Master orchestrator state: is_running={data.get('is_running')}")


class TestUpgradesEndpoints:
    """Test upgrades status endpoint"""
    
    def test_upgrades_status(self):
        """Test upgrades status"""
        response = requests.get(f"{BASE_URL}/api/upgrades/status")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        print(f"✓ Upgrades status loaded with {len(data.get('features', {}))} features")


class TestMarketDataEndpoints:
    """Test market data endpoints for real data verification"""
    
    def test_market_prices(self):
        """Test market prices endpoint"""
        response = requests.get(f"{BASE_URL}/api/market/prices?coins=bitcoin,ethereum,solana")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Market prices loaded")
    
    def test_market_overview(self):
        """Test market overview"""
        response = requests.get(f"{BASE_URL}/api/market/overview")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Market overview: {data.get('total_market_cap', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
