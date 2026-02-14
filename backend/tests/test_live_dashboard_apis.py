"""
Test Live Dashboard APIs - Iteration 48
Tests for real-time data endpoints used by Live Dashboard
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestKrakenPortfolioAPI:
    """Tests for /api/trading/kraken/portfolio endpoint - Real Kraken data"""
    
    def test_portfolio_endpoint_returns_200(self):
        """Verify portfolio endpoint returns 200 status"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_portfolio_returns_holdings(self):
        """Verify portfolio returns holdings array"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio")
        data = response.json()
        assert "holdings" in data, "Response should contain 'holdings' key"
        assert isinstance(data["holdings"], list), "Holdings should be a list"
    
    def test_portfolio_returns_total_value(self):
        """Verify portfolio returns total_value_usd"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio")
        data = response.json()
        assert "total_value_usd" in data, "Response should contain 'total_value_usd'"
        assert isinstance(data["total_value_usd"], (int, float)), "total_value_usd should be numeric"
        assert data["total_value_usd"] > 0, "Portfolio value should be positive"
    
    def test_portfolio_returns_change_24h(self):
        """Verify portfolio returns 24h change percentage"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio")
        data = response.json()
        assert "change_24h" in data, "Response should contain 'change_24h'"
        assert isinstance(data["change_24h"], (int, float)), "change_24h should be numeric"
    
    def test_portfolio_holdings_structure(self):
        """Verify each holding has required fields"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio")
        data = response.json()
        holdings = data.get("holdings", [])
        
        if len(holdings) > 0:
            holding = holdings[0]
            required_fields = ["symbol", "amount", "value_usd"]
            for field in required_fields:
                assert field in holding, f"Holding should contain '{field}'"


class TestAISignalsAPI:
    """Tests for /api/ai-signals/{symbol} endpoint - Real AI signals"""
    
    def test_btc_signal_returns_200(self):
        """Verify BTC signal endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/BTC")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_eth_signal_returns_200(self):
        """Verify ETH signal endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/ETH")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_signal_returns_required_fields(self):
        """Verify signal response contains required fields"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/BTC")
        data = response.json()
        
        required_fields = ["symbol", "signal", "confidence"]
        for field in required_fields:
            assert field in data, f"Response should contain '{field}'"
    
    def test_signal_type_is_valid(self):
        """Verify signal type is one of expected values"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/BTC")
        data = response.json()
        
        valid_signals = ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
        assert data["signal"] in valid_signals, f"Signal should be one of {valid_signals}"
    
    def test_confidence_is_valid_range(self):
        """Verify confidence is between 0 and 100"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/BTC")
        data = response.json()
        
        confidence = data.get("confidence", 0)
        assert 0 <= confidence <= 100, f"Confidence should be 0-100, got {confidence}"
    
    def test_signal_has_components(self):
        """Verify signal has component breakdown"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/BTC")
        data = response.json()
        
        assert "components" in data, "Response should contain 'components'"
        components = data["components"]
        expected_components = ["technical", "sentiment", "momentum", "volume"]
        for comp in expected_components:
            assert comp in components, f"Components should contain '{comp}'"


class TestGrowthStatusAPI:
    """Tests for /api/growth/status endpoint - Growth tracking"""
    
    def test_growth_status_returns_200(self):
        """Verify growth status endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/growth/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_growth_status_has_current_value(self):
        """Verify growth status returns current value"""
        response = requests.get(f"{BASE_URL}/api/growth/status")
        data = response.json()
        
        assert "current_value" in data, "Response should contain 'current_value'"
        assert isinstance(data["current_value"], (int, float)), "current_value should be numeric"
    
    def test_growth_status_has_target(self):
        """Verify growth status returns target value"""
        response = requests.get(f"{BASE_URL}/api/growth/status")
        data = response.json()
        
        assert "target_value" in data, "Response should contain 'target_value'"
        assert data["target_value"] == 100000, "Target should be $100,000"
    
    def test_growth_status_has_progress(self):
        """Verify growth status returns progress percentage"""
        response = requests.get(f"{BASE_URL}/api/growth/status")
        data = response.json()
        
        assert "progress_pct" in data, "Response should contain 'progress_pct'"


class TestAIExplanationAPI:
    """Tests for /api/ai-explain/signal/{coin_id} endpoint - AI explanations"""
    
    def test_bitcoin_explanation_returns_200(self):
        """Verify bitcoin explanation endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/ai-explain/signal/bitcoin")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_explanation_has_signal(self):
        """Verify explanation contains signal"""
        response = requests.get(f"{BASE_URL}/api/ai-explain/signal/bitcoin")
        data = response.json()
        
        assert "signal" in data, "Response should contain 'signal'"
        valid_signals = ["BUY", "SELL", "HOLD"]
        assert data["signal"] in valid_signals, f"Signal should be one of {valid_signals}"
    
    def test_explanation_has_confidence(self):
        """Verify explanation contains confidence"""
        response = requests.get(f"{BASE_URL}/api/ai-explain/signal/bitcoin")
        data = response.json()
        
        assert "confidence" in data, "Response should contain 'confidence'"
        assert 0 <= data["confidence"] <= 1, "Confidence should be 0-1"
    
    def test_explanation_has_summary(self):
        """Verify explanation contains summary"""
        response = requests.get(f"{BASE_URL}/api/ai-explain/signal/bitcoin")
        data = response.json()
        
        assert "summary" in data, "Response should contain 'summary'"
        assert len(data["summary"]) > 0, "Summary should not be empty"
    
    def test_explanation_has_risk_factors(self):
        """Verify explanation contains risk factors"""
        response = requests.get(f"{BASE_URL}/api/ai-explain/signal/bitcoin")
        data = response.json()
        
        assert "risk_factors" in data, "Response should contain 'risk_factors'"
        assert isinstance(data["risk_factors"], list), "risk_factors should be a list"
    
    def test_explanation_has_recommendation(self):
        """Verify explanation contains recommendation"""
        response = requests.get(f"{BASE_URL}/api/ai-explain/signal/bitcoin")
        data = response.json()
        
        assert "recommendation" in data, "Response should contain 'recommendation'"


class TestHealthEndpoint:
    """Tests for /api/health endpoint"""
    
    def test_health_returns_200(self):
        """Verify health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestMultipleSymbolSignals:
    """Tests for AI signals across multiple symbols"""
    
    @pytest.mark.parametrize("symbol", ["BTC", "ETH", "SOL", "DOT", "AAVE"])
    def test_signal_for_symbol(self, symbol):
        """Verify signal endpoint works for various symbols"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/{symbol}")
        assert response.status_code == 200, f"Expected 200 for {symbol}, got {response.status_code}"
        
        data = response.json()
        assert data["symbol"] == symbol, f"Symbol should be {symbol}"
        assert "signal" in data, f"Response for {symbol} should contain 'signal'"
        assert "confidence" in data, f"Response for {symbol} should contain 'confidence'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
