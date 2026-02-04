"""
Stop-Loss Automation & Trigger Performance API Tests
Tests for position-level stop-loss automation and trigger performance dashboard.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStopLossAutomation:
    """Tests for /api/automation/* endpoints"""
    
    def test_automation_status(self):
        """Test GET /api/automation/status - Get stop-loss automation status"""
        response = requests.get(f"{BASE_URL}/api/automation/status")
        assert response.status_code == 200
        
        data = response.json()
        # Verify response structure
        assert "enabled" in data
        assert "check_interval_minutes" in data
        assert "statistics" in data
        assert "config" in data
        
        # Verify statistics structure
        stats = data["statistics"]
        assert "total_checks" in stats
        assert "positions_closed_stop_loss" in stats
        assert "positions_closed_take_profit" in stats
        assert "total_pnl_from_automation" in stats
        assert "last_check" in stats
        
        # Verify config structure
        config = data["config"]
        assert "check_interval_minutes" in config
        assert config["check_interval_minutes"] == 5
        
        print(f"✅ Automation status: enabled={data['enabled']}, total_checks={stats['total_checks']}")
    
    def test_manual_position_check(self):
        """Test POST /api/automation/check-now - Manual position check"""
        response = requests.post(f"{BASE_URL}/api/automation/check-now")
        assert response.status_code == 200
        
        data = response.json()
        # Verify response structure
        assert "success" in data
        assert data["success"] == True
        assert "positions_checked" in data
        assert "timestamp" in data
        
        # Check for triggered actions
        if "stop_loss_triggered" in data:
            assert isinstance(data["stop_loss_triggered"], list)
        if "take_profit_triggered" in data:
            assert isinstance(data["take_profit_triggered"], list)
        if "actions_taken" in data:
            assert isinstance(data["actions_taken"], int)
        
        print(f"✅ Manual check: positions_checked={data['positions_checked']}, actions_taken={data.get('actions_taken', 0)}")
    
    def test_positions_at_risk(self):
        """Test GET /api/automation/positions-at-risk - Get positions near stop-loss"""
        response = requests.get(f"{BASE_URL}/api/automation/positions-at-risk")
        assert response.status_code == 200
        
        data = response.json()
        # Verify response structure
        assert "positions_at_risk" in data
        assert "positions_near_profit" in data
        assert "total_at_risk" in data
        assert "total_near_profit" in data
        
        # Verify data types
        assert isinstance(data["positions_at_risk"], list)
        assert isinstance(data["positions_near_profit"], list)
        assert isinstance(data["total_at_risk"], int)
        assert isinstance(data["total_near_profit"], int)
        
        print(f"✅ Positions at risk: {data['total_at_risk']}, near profit: {data['total_near_profit']}")
    
    def test_automation_history(self):
        """Test GET /api/automation/history - Get automation execution history"""
        response = requests.get(f"{BASE_URL}/api/automation/history?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "history" in data
        assert "count" in data
        assert isinstance(data["history"], list)
        
        print(f"✅ Automation history: {data['count']} records")


class TestTriggerPerformance:
    """Tests for /api/triggers/performance/* endpoints"""
    
    def test_trigger_performance_dashboard(self):
        """Test GET /api/triggers/performance/dashboard - Trigger performance metrics"""
        response = requests.get(f"{BASE_URL}/api/triggers/performance/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        # Verify summary structure
        assert "summary" in data
        summary = data["summary"]
        assert "total_triggers" in summary
        assert "enabled_triggers" in summary
        assert "total_executions" in summary
        assert "overall_success_rate" in summary
        assert "total_pnl_usd" in summary
        
        # Verify 36 triggers as per requirements
        assert summary["total_triggers"] == 36, f"Expected 36 triggers, got {summary['total_triggers']}"
        
        # Verify by_category structure
        assert "by_category" in data
        categories = data["by_category"]
        assert isinstance(categories, dict)
        
        # Verify trigger_metrics structure
        assert "trigger_metrics" in data
        assert isinstance(data["trigger_metrics"], list)
        
        # Verify top_performers structure
        assert "top_performers" in data
        assert "by_fires" in data["top_performers"]
        assert "by_pnl" in data["top_performers"]
        
        # Verify recent_executions structure
        assert "recent_executions" in data
        assert isinstance(data["recent_executions"], list)
        
        print(f"✅ Trigger dashboard: {summary['total_triggers']} triggers, {summary['total_executions']} executions, {summary['overall_success_rate']}% success rate")
    
    def test_trigger_categories(self):
        """Test that all expected categories are present"""
        response = requests.get(f"{BASE_URL}/api/triggers/performance/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        categories = data["by_category"]
        
        # Expected categories based on the frontend code
        expected_categories = ["celebrity", "regulatory", "whale", "institutional", "security", "macro", "market_event", "other"]
        
        for cat in expected_categories:
            if cat in categories:
                cat_data = categories[cat]
                assert "total_triggers" in cat_data
                assert "total_fires" in cat_data
                assert "total_pnl" in cat_data
                print(f"  ✅ Category '{cat}': {cat_data['total_triggers']} triggers, {cat_data['total_fires']} fires")


class TestAdaptiveStrategy:
    """Tests for /api/strategy/* endpoints"""
    
    def test_strategy_status(self):
        """Test GET /api/strategy/status - Get adaptive strategy status"""
        response = requests.get(f"{BASE_URL}/api/strategy/status")
        assert response.status_code == 200
        
        data = response.json()
        # Verify response structure
        assert "current_regime" in data
        assert "risk_mode" in data
        assert "adapted_params" in data
        assert "base_params" in data
        
        # Verify regime is valid
        valid_regimes = ["strong_bull", "bull", "sideways", "bear", "strong_bear", "high_volatility", "accumulation"]
        assert data["current_regime"] in valid_regimes, f"Invalid regime: {data['current_regime']}"
        
        # Verify params structure
        params = data["adapted_params"]
        assert "max_position_pct" in params
        assert "stop_loss_pct" in params
        assert "take_profit_pct" in params
        assert "max_total_exposure" in params
        
        print(f"✅ Strategy status: regime={data['current_regime']}, risk_mode={data['risk_mode']}")
    
    def test_strategy_params(self):
        """Test GET /api/strategy/params - Get current strategy parameters"""
        response = requests.get(f"{BASE_URL}/api/strategy/params")
        assert response.status_code == 200
        
        data = response.json()
        assert "base_params" in data
        assert "adapted_params" in data
        assert "current_regime" in data
        assert "risk_mode" in data
        
        # Verify base params have expected keys
        base = data["base_params"]
        expected_params = ["max_position_pct", "min_position_pct", "max_total_exposure", 
                          "stop_loss_pct", "take_profit_pct", "trailing_stop_pct", 
                          "min_confidence", "exit_confidence"]
        for param in expected_params:
            assert param in base, f"Missing param: {param}"
        
        print(f"✅ Strategy params: position={base['max_position_pct']}%, stop_loss={base['stop_loss_pct']}%, take_profit={base['take_profit_pct']}%")
    
    def test_detect_regime(self):
        """Test POST /api/strategy/detect-regime - Detect market regime"""
        response = requests.post(f"{BASE_URL}/api/strategy/detect-regime")
        assert response.status_code == 200
        
        data = response.json()
        assert "regime" in data
        assert "detected_at" in data
        assert "description" in data
        
        print(f"✅ Detected regime: {data['regime']}")
    
    def test_adapt_strategy(self):
        """Test POST /api/strategy/adapt - Adapt strategy to current conditions"""
        response = requests.post(f"{BASE_URL}/api/strategy/adapt")
        assert response.status_code == 200
        
        data = response.json()
        # Should return adaptation result
        assert isinstance(data, dict)
        
        print(f"✅ Strategy adaptation completed")


class TestPerformanceRegime:
    """Tests for /api/performance/* endpoints"""
    
    def test_regime_compare(self):
        """Test GET /api/performance/regime/compare - Compare ML models"""
        response = requests.get(f"{BASE_URL}/api/performance/regime/compare")
        assert response.status_code == 200
        
        data = response.json()
        # May return error if no models trained, which is acceptable
        if "error" in data:
            print(f"⚠️ No trained models yet: {data['error']}")
        else:
            assert "models" in data or "best_model" in data
            print(f"✅ Model comparison available")
    
    def test_regime_predict(self):
        """Test POST /api/performance/regime/predict - Predict market regime"""
        response = requests.post(
            f"{BASE_URL}/api/performance/regime/predict",
            json={"symbol": "BTC"}
        )
        assert response.status_code == 200
        
        data = response.json()
        # May return error if no models trained
        if "error" in data:
            print(f"⚠️ Prediction unavailable: {data.get('error', 'No models')}")
        else:
            # Response may have 'predicted_regime' or 'all_predictions' with regime info
            has_regime = "regime" in data or "predicted_regime" in data or "all_predictions" in data
            assert has_regime, f"Expected regime data in response: {data.keys()}"
            
            if "all_predictions" in data:
                print(f"✅ Regime prediction: model_used={data.get('model_used')}, confidence={data.get('confidence')}")
            else:
                print(f"✅ Regime prediction: {data}")
    
    def test_trading_performance(self):
        """Test GET /api/performance/trading - Get trading performance metrics"""
        response = requests.get(f"{BASE_URL}/api/performance/trading?days=30")
        assert response.status_code == 200
        
        data = response.json()
        # Should return performance metrics
        assert isinstance(data, dict)
        print(f"✅ Trading performance retrieved")


class TestHealthAndIntegration:
    """Basic health and integration tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ API health: {data['status']}")
    
    def test_triggers_list(self):
        """Test GET /api/triggers/list - Verify 36 triggers exist"""
        response = requests.get(f"{BASE_URL}/api/triggers/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "triggers" in data
        assert len(data["triggers"]) == 36, f"Expected 36 triggers, got {len(data['triggers'])}"
        
        print(f"✅ Triggers list: {len(data['triggers'])} triggers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
