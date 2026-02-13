"""
Master Trading Orchestrator API Tests
=====================================
Tests for all Master Orchestrator endpoints:
- /api/master/status - Get orchestrator status
- /api/master/start - Start orchestrator
- /api/master/stop - Stop orchestrator
- /api/master/set-mode - Change trading mode
- /api/master/set-limits - Update risk limits
- /api/master/dashboard - Get dashboard data
- /api/master/pending - Get pending signals
- /api/master/risk - Get risk status
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestMasterOrchestratorStatus:
    """Test /api/master/status endpoint"""
    
    def test_get_status_returns_200(self):
        """Status endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/master/status")
        assert response.status_code == 200
        
    def test_status_contains_required_fields(self):
        """Status should contain all required fields"""
        response = requests.get(f"{BASE_URL}/api/master/status")
        data = response.json()
        
        # Check required fields
        assert "is_active" in data
        assert "mode" in data
        assert "portfolio_value" in data
        assert "pending_signals" in data
        assert "stats" in data
        assert "risk_status" in data
        
    def test_status_mode_is_valid(self):
        """Mode should be one of valid values"""
        response = requests.get(f"{BASE_URL}/api/master/status")
        data = response.json()
        
        valid_modes = ["manual", "auto_small", "full_auto"]
        assert data["mode"] in valid_modes
        
    def test_status_stats_structure(self):
        """Stats should have correct structure"""
        response = requests.get(f"{BASE_URL}/api/master/status")
        data = response.json()
        
        stats = data["stats"]
        assert "total_signals" in stats
        assert "executed_trades" in stats
        assert "auto_executed" in stats
        assert "rejected" in stats


class TestMasterOrchestratorStartStop:
    """Test /api/master/start and /api/master/stop endpoints"""
    
    def test_stop_orchestrator(self):
        """Stop endpoint should return 200"""
        response = requests.post(f"{BASE_URL}/api/master/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "stopped"
        
    def test_verify_stopped_status(self):
        """After stop, status should show is_active=False"""
        # First stop
        requests.post(f"{BASE_URL}/api/master/stop")
        
        # Then check status
        response = requests.get(f"{BASE_URL}/api/master/status")
        data = response.json()
        assert data["is_active"] == False
        
    def test_start_orchestrator(self):
        """Start endpoint should return 200"""
        response = requests.post(f"{BASE_URL}/api/master/start")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["started", "already_running"]
        
    def test_start_when_already_running(self):
        """Start when already running should return already_running"""
        # Start first
        requests.post(f"{BASE_URL}/api/master/start")
        
        # Start again
        response = requests.post(f"{BASE_URL}/api/master/start")
        data = response.json()
        
        # Should either start or say already running
        assert data["status"] in ["started", "already_running"]


class TestMasterOrchestratorSetMode:
    """Test /api/master/set-mode endpoint"""
    
    def test_set_mode_manual(self):
        """Set mode to manual"""
        response = requests.post(
            f"{BASE_URL}/api/master/set-mode",
            json={"mode": "manual"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "mode_set"
        assert data["mode"] == "manual"
        
    def test_set_mode_hybrid(self):
        """Set mode to hybrid (auto_small)"""
        response = requests.post(
            f"{BASE_URL}/api/master/set-mode",
            json={"mode": "hybrid"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "mode_set"
        assert data["mode"] == "auto_small"  # hybrid maps to auto_small
        
    def test_set_mode_full_auto(self):
        """Set mode to full_auto"""
        response = requests.post(
            f"{BASE_URL}/api/master/set-mode",
            json={"mode": "full_auto"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "mode_set"
        assert data["mode"] == "full_auto"
        
    def test_verify_mode_persists(self):
        """Mode change should persist in status"""
        # Set to manual
        requests.post(
            f"{BASE_URL}/api/master/set-mode",
            json={"mode": "manual"}
        )
        
        # Verify in status
        response = requests.get(f"{BASE_URL}/api/master/status")
        data = response.json()
        assert data["mode"] == "manual"
        
        # Set back to hybrid
        requests.post(
            f"{BASE_URL}/api/master/set-mode",
            json={"mode": "hybrid"}
        )


class TestMasterOrchestratorSetLimits:
    """Test /api/master/set-limits endpoint"""
    
    def test_set_max_position_limit(self):
        """Set max position percentage"""
        response = requests.post(
            f"{BASE_URL}/api/master/set-limits",
            json={"max_position_pct": 15.0}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "limits_updated"
        assert data["risk_status"]["limits"]["max_position_pct"] == 15.0
        
    def test_set_max_daily_loss_limit(self):
        """Set max daily loss percentage"""
        response = requests.post(
            f"{BASE_URL}/api/master/set-limits",
            json={"max_daily_loss_pct": 3.0}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "limits_updated"
        assert data["risk_status"]["limits"]["max_daily_loss_pct"] == 3.0
        
    def test_set_multiple_limits(self):
        """Set multiple limits at once"""
        response = requests.post(
            f"{BASE_URL}/api/master/set-limits",
            json={
                "max_position_pct": 10.0,
                "max_daily_loss_pct": 5.0,
                "max_drawdown_pct": 15.0,
                "min_confidence": 60.0,
                "small_trade_threshold": 100.0
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "limits_updated"
        
        limits = data["risk_status"]["limits"]
        assert limits["max_position_pct"] == 10.0
        assert limits["max_daily_loss_pct"] == 5.0
        assert limits["max_drawdown_pct"] == 15.0
        assert limits["min_confidence"] == 60.0
        
    def test_set_small_trade_threshold(self):
        """Set small trade threshold"""
        response = requests.post(
            f"{BASE_URL}/api/master/set-limits",
            json={"small_trade_threshold": 150.0}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["small_trade_threshold"] == 150.0


class TestMasterOrchestratorDashboard:
    """Test /api/master/dashboard endpoint"""
    
    def test_dashboard_returns_200(self):
        """Dashboard endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/master/dashboard")
        assert response.status_code == 200
        
    def test_dashboard_contains_orchestrator_data(self):
        """Dashboard should contain orchestrator data"""
        response = requests.get(f"{BASE_URL}/api/master/dashboard")
        data = response.json()
        
        assert "orchestrator" in data
        assert "is_active" in data["orchestrator"]
        assert "mode" in data["orchestrator"]
        
    def test_dashboard_contains_news_data(self):
        """Dashboard should contain news monitor data"""
        response = requests.get(f"{BASE_URL}/api/master/dashboard")
        data = response.json()
        
        assert "news" in data
        assert "is_running" in data["news"]
        
    def test_dashboard_contains_specialists_data(self):
        """Dashboard should contain specialist agents data"""
        response = requests.get(f"{BASE_URL}/api/master/dashboard")
        data = response.json()
        
        assert "specialists" in data
        assert "regime" in data["specialists"]
        
    def test_dashboard_contains_timestamp(self):
        """Dashboard should contain timestamp"""
        response = requests.get(f"{BASE_URL}/api/master/dashboard")
        data = response.json()
        
        assert "timestamp" in data


class TestMasterOrchestratorPending:
    """Test /api/master/pending endpoint"""
    
    def test_pending_returns_200(self):
        """Pending endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/master/pending")
        assert response.status_code == 200
        
    def test_pending_structure(self):
        """Pending should have correct structure"""
        response = requests.get(f"{BASE_URL}/api/master/pending")
        data = response.json()
        
        assert "pending" in data
        assert "count" in data
        assert isinstance(data["pending"], list)
        assert isinstance(data["count"], int)


class TestMasterOrchestratorRisk:
    """Test /api/master/risk endpoint"""
    
    def test_risk_returns_200(self):
        """Risk endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/master/risk")
        assert response.status_code == 200
        
    def test_risk_contains_pnl(self):
        """Risk should contain daily P&L"""
        response = requests.get(f"{BASE_URL}/api/master/risk")
        data = response.json()
        
        assert "daily_pnl_pct" in data
        
    def test_risk_contains_drawdown(self):
        """Risk should contain drawdown"""
        response = requests.get(f"{BASE_URL}/api/master/risk")
        data = response.json()
        
        assert "current_drawdown_pct" in data
        
    def test_risk_contains_limits(self):
        """Risk should contain limits"""
        response = requests.get(f"{BASE_URL}/api/master/risk")
        data = response.json()
        
        assert "limits" in data
        limits = data["limits"]
        assert "max_position_pct" in limits
        assert "max_daily_loss_pct" in limits
        assert "max_drawdown_pct" in limits
        assert "min_confidence" in limits


class TestMasterOrchestratorHistory:
    """Test /api/master/history endpoint"""
    
    def test_history_returns_200(self):
        """History endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/master/history")
        assert response.status_code == 200
        
    def test_history_structure(self):
        """History should have correct structure"""
        response = requests.get(f"{BASE_URL}/api/master/history")
        data = response.json()
        
        assert "executed" in data
        assert "rejected" in data
        assert "stats" in data


class TestMasterOrchestratorResetDaily:
    """Test /api/master/reset-daily endpoint"""
    
    def test_reset_daily_returns_200(self):
        """Reset daily endpoint should return 200"""
        response = requests.post(f"{BASE_URL}/api/master/reset-daily")
        assert response.status_code == 200
        
    def test_reset_daily_resets_pnl(self):
        """Reset daily should reset daily P&L"""
        response = requests.post(f"{BASE_URL}/api/master/reset-daily")
        data = response.json()
        
        assert data["status"] == "reset"
        assert data["risk_status"]["daily_pnl_pct"] == 0.0


# Cleanup - restore default settings
@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Restore default settings after tests"""
    yield
    # Restore defaults
    requests.post(
        f"{BASE_URL}/api/master/set-limits",
        json={
            "max_position_pct": 10.0,
            "max_daily_loss_pct": 5.0,
            "max_drawdown_pct": 15.0,
            "min_confidence": 60.0,
            "small_trade_threshold": 100.0
        }
    )
    requests.post(
        f"{BASE_URL}/api/master/set-mode",
        json={"mode": "hybrid"}
    )
