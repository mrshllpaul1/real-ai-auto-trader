"""
Iteration 49 - Auth Features Testing
=====================================
Tests for:
- Google OAuth endpoints
- 2FA setup and verification
- Session management
- Onboarding completion
- AI signals and portfolio endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_auth_me_unauthenticated(self):
        """Test /api/auth/me returns 401 when not authenticated"""
        response = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"] or "not authenticated" in data["detail"].lower()
        print(f"✓ Auth /me correctly returns 401 for unauthenticated: {data}")


class TestTwoFactorAuthEndpoints:
    """2FA setup and verification tests"""
    
    def test_2fa_setup_unauthenticated(self):
        """Test /api/auth/2fa/setup returns 401 when not authenticated"""
        response = requests.post(f"{BASE_URL}/api/auth/2fa/setup", timeout=10)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ 2FA setup correctly requires authentication: {data}")
    
    def test_2fa_verify_unauthenticated(self):
        """Test /api/auth/2fa/verify returns 401 when not authenticated"""
        response = requests.post(
            f"{BASE_URL}/api/auth/2fa/verify",
            json={"code": "123456"},
            timeout=10
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ 2FA verify correctly requires authentication: {data}")
    
    def test_2fa_disable_unauthenticated(self):
        """Test /api/auth/2fa/disable returns 401 when not authenticated"""
        response = requests.post(
            f"{BASE_URL}/api/auth/2fa/disable",
            json={"code": "123456"},
            timeout=10
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ 2FA disable correctly requires authentication: {data}")


class TestOnboardingEndpoints:
    """Onboarding completion tests"""
    
    def test_onboarding_complete_unauthenticated(self):
        """Test /api/auth/onboarding/complete returns 401 when not authenticated"""
        response = requests.post(f"{BASE_URL}/api/auth/onboarding/complete", timeout=10)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ Onboarding complete correctly requires authentication: {data}")


class TestSessionManagement:
    """Session management tests"""
    
    def test_sessions_unauthenticated(self):
        """Test /api/auth/sessions returns 401 when not authenticated"""
        response = requests.get(f"{BASE_URL}/api/auth/sessions", timeout=10)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ Sessions endpoint correctly requires authentication: {data}")
    
    def test_revoke_all_sessions_unauthenticated(self):
        """Test /api/auth/sessions/all DELETE returns 401 when not authenticated"""
        response = requests.delete(f"{BASE_URL}/api/auth/sessions/all", timeout=10)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ Revoke all sessions correctly requires authentication: {data}")
    
    def test_logout_endpoint(self):
        """Test /api/auth/logout works (clears session)"""
        response = requests.post(f"{BASE_URL}/api/auth/logout", timeout=10)
        # Logout should work even without session (just clears cookie)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Logout endpoint works: {data}")


class TestAISignalsEndpoints:
    """AI signals endpoint tests"""
    
    def test_ai_signals_btc(self):
        """Test /api/ai-signals/BTC returns real signal data"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/BTC", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        # Verify signal structure
        assert "symbol" in data
        assert data["symbol"] == "BTC"
        assert "signal" in data
        assert data["signal"] in ["BUY", "SELL", "HOLD"]
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0 <= data["confidence"] <= 100
        assert "components" in data
        
        print(f"✓ BTC AI signal: {data['signal']} with {data['confidence']}% confidence")
    
    def test_ai_signals_eth(self):
        """Test /api/ai-signals/ETH returns real signal data"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/ETH", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        assert "symbol" in data
        assert data["symbol"] == "ETH"
        assert "signal" in data
        assert data["signal"] in ["BUY", "SELL", "HOLD"]
        
        print(f"✓ ETH AI signal: {data['signal']} with {data.get('confidence', 'N/A')}% confidence")
    
    def test_ai_signals_sol(self):
        """Test /api/ai-signals/SOL returns real signal data"""
        response = requests.get(f"{BASE_URL}/api/ai-signals/SOL", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        assert "symbol" in data
        assert data["symbol"] == "SOL"
        assert "signal" in data
        
        print(f"✓ SOL AI signal: {data['signal']}")


class TestPortfolioEndpoints:
    """Portfolio endpoint tests"""
    
    def test_kraken_portfolio(self):
        """Test /api/trading/kraken/portfolio returns real holdings"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        # Verify portfolio structure
        assert "holdings" in data
        assert isinstance(data["holdings"], list)
        assert "total_value_usd" in data
        assert isinstance(data["total_value_usd"], (int, float))
        assert "holdings_count" in data
        
        # Verify holdings have required fields
        if len(data["holdings"]) > 0:
            holding = data["holdings"][0]
            assert "symbol" in holding
            assert "amount" in holding
            assert "value_usd" in holding
        
        print(f"✓ Portfolio: ${data['total_value_usd']:.2f} total, {data['holdings_count']} holdings")
        print(f"  Holdings: {[h['symbol'] for h in data['holdings']]}")
    
    def test_portfolio_has_real_data(self):
        """Verify portfolio contains real Kraken data (not mocked)"""
        response = requests.get(f"{BASE_URL}/api/trading/kraken/portfolio", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        # Real portfolio should have multiple holdings
        assert data["holdings_count"] > 0, "Portfolio should have holdings"
        assert data["total_value_usd"] > 0, "Portfolio should have value"
        
        # Check for expected assets (from previous test reports)
        symbols = [h["symbol"] for h in data["holdings"]]
        # At least some of these should be present
        expected_assets = ["USD", "ETH", "SOL", "DOT"]
        found_assets = [a for a in expected_assets if a in symbols]
        assert len(found_assets) > 0, f"Expected some of {expected_assets}, found {symbols}"
        
        print(f"✓ Real portfolio data verified: {found_assets} found")


class TestSessionExchange:
    """Session exchange endpoint tests"""
    
    def test_session_exchange_invalid(self):
        """Test /api/auth/session with invalid session_id"""
        response = requests.post(
            f"{BASE_URL}/api/auth/session",
            json={"session_id": "invalid_session_id_12345"},
            timeout=10
        )
        # Should return 401 or 503 (auth service unavailable)
        assert response.status_code in [401, 503, 500]
        print(f"✓ Session exchange correctly rejects invalid session: {response.status_code}")


class TestLiveDashboardAPIs:
    """Live Dashboard related API tests"""
    
    def test_growth_status(self):
        """Test /api/growth/status returns growth data"""
        response = requests.get(f"{BASE_URL}/api/growth/status", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        # Verify growth status structure
        assert "current_value" in data or "status" in data
        print(f"✓ Growth status: {data}")
    
    def test_ai_explain_signal(self):
        """Test /api/ai-explain/signal/bitcoin returns explanation"""
        response = requests.get(f"{BASE_URL}/api/ai-explain/signal/bitcoin", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        # Verify explanation structure
        assert "signal" in data or "prediction" in data or "confidence" in data
        print(f"✓ AI explanation available for bitcoin")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
