"""
Test P1/P2 Fixes - Iteration 43
================================
Tests for:
1. Optimal Strategy tab displays real strategy data with name, parameters, and risk level
2. API endpoint /api/adaptive-strategy/optimal-strategy returns recommended_strategy with non-empty parameters
3. Universe rebuild state persists across page navigation
4. Ensemble AI page shows rebuild status correctly
5. System state persistence API works correctly
6. Training does not interfere with trading states
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOptimalStrategyAPI:
    """Test Optimal Strategy API returns proper data"""
    
    def test_optimal_strategy_returns_recommended_strategy(self):
        """P1: Verify optimal strategy endpoint returns recommended_strategy with name and parameters"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/optimal-strategy")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify recommended_strategy exists
        assert "recommended_strategy" in data, "Missing recommended_strategy in response"
        
        strategy = data["recommended_strategy"]
        
        # Verify strategy has name
        assert "name" in strategy, "Missing name in recommended_strategy"
        assert strategy["name"], "Strategy name is empty"
        assert strategy["name"] != "Default", f"Strategy name should not be 'Default', got: {strategy['name']}"
        
        # Verify strategy has parameters
        assert "parameters" in strategy, "Missing parameters in recommended_strategy"
        assert strategy["parameters"], "Strategy parameters is empty"
        assert isinstance(strategy["parameters"], dict), "Parameters should be a dict"
        assert len(strategy["parameters"]) > 0, "Parameters dict is empty"
        
        # Verify specific parameters exist
        expected_params = ["lookback", "stop_loss_pct", "take_profit_pct"]
        for param in expected_params:
            assert param in strategy["parameters"], f"Missing expected parameter: {param}"
        
        print(f"✅ Optimal Strategy: {strategy['name']}")
        print(f"✅ Parameters count: {len(strategy['parameters'])}")
    
    def test_optimal_strategy_has_risk_level(self):
        """P1: Verify optimal strategy returns risk_level"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/optimal-strategy")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify risk_level exists
        assert "risk_level" in data, "Missing risk_level in response"
        assert data["risk_level"] in ["low", "moderate", "high"], f"Invalid risk_level: {data['risk_level']}"
        
        print(f"✅ Risk Level: {data['risk_level']}")
    
    def test_optimal_strategy_has_current_regime(self):
        """P1: Verify optimal strategy returns current_regime with indicators"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/optimal-strategy")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify current_regime exists
        assert "current_regime" in data, "Missing current_regime in response"
        
        regime = data["current_regime"]
        assert "regime" in regime, "Missing regime type"
        assert "confidence" in regime, "Missing confidence"
        assert "indicators" in regime, "Missing indicators"
        
        # Verify indicators have expected fields
        indicators = regime["indicators"]
        expected_indicators = ["trend_strength", "volatility", "rsi"]
        for ind in expected_indicators:
            assert ind in indicators, f"Missing indicator: {ind}"
        
        print(f"✅ Current Regime: {regime['regime']} (confidence: {regime['confidence']:.2%})")


class TestUniverseRebuildPersistence:
    """Test Universe Rebuild state persistence"""
    
    def test_universe_rebuild_state_endpoint(self):
        """P2: Verify universe rebuild state endpoint works"""
        response = requests.get(f"{BASE_URL}/api/system-state/universe_rebuild?user_id=default")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "component" in data, "Missing component field"
        assert data["component"] == "universe_rebuild", f"Wrong component: {data['component']}"
        assert "is_running" in data, "Missing is_running field"
        
        print(f"✅ Universe Rebuild State: is_running={data.get('is_running')}")
    
    def test_ensemble_build_status_endpoint(self):
        """P2: Verify ensemble build status endpoint works"""
        response = requests.get(f"{BASE_URL}/api/ensemble/build-status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "running" in data, "Missing running field"
        assert "progress" in data, "Missing progress field"
        assert "endpoints" in data, "Missing endpoints field"
        
        print(f"✅ Ensemble Build Status: running={data.get('running')}, progress={data.get('progress')}")


class TestSystemStatePersistence:
    """Test System State Persistence API"""
    
    def test_get_all_states(self):
        """Verify /api/system-state/all returns all states"""
        response = requests.get(f"{BASE_URL}/api/system-state/all?user_id=default")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "running_components" in data, "Missing running_components"
        assert "stopped_components" in data, "Missing stopped_components"
        assert "total_running" in data, "Missing total_running"
        assert "states" in data, "Missing states"
        
        print(f"✅ Running components: {data.get('running_components')}")
        print(f"✅ Total running: {data.get('total_running')}")
    
    def test_get_specific_state(self):
        """Verify getting specific component state"""
        response = requests.get(f"{BASE_URL}/api/system-state/auto_trading?user_id=default")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "component" in data, "Missing component field"
        assert "is_running" in data, "Missing is_running field"
        
        print(f"✅ Auto Trading State: is_running={data.get('is_running')}")


class TestTrainingDoesNotInterfereWithTrading:
    """Test that training does not interfere with trading states"""
    
    def test_training_status_independent(self):
        """Verify training status is independent from trading state"""
        # Get current auto_trading state
        trading_response = requests.get(f"{BASE_URL}/api/system-state/auto_trading?user_id=default")
        assert trading_response.status_code == 200
        initial_trading_state = trading_response.json().get("is_running")
        
        # Get training status
        training_response = requests.get(f"{BASE_URL}/api/tethys-train/status?user_id=default")
        assert training_response.status_code == 200
        training_data = training_response.json()
        
        # Verify training status has expected fields
        assert "is_training" in training_data, "Missing is_training field"
        assert "is_active" in training_data, "Missing is_active field"
        
        # Verify auto_trading state is unchanged
        trading_response2 = requests.get(f"{BASE_URL}/api/system-state/auto_trading?user_id=default")
        assert trading_response2.status_code == 200
        final_trading_state = trading_response2.json().get("is_running")
        
        assert initial_trading_state == final_trading_state, \
            f"Trading state changed unexpectedly: {initial_trading_state} -> {final_trading_state}"
        
        print(f"✅ Training status: is_training={training_data.get('is_training')}")
        print(f"✅ Auto trading state unchanged: {initial_trading_state}")
    
    def test_training_progress_endpoint(self):
        """Verify training progress endpoint works"""
        response = requests.get(f"{BASE_URL}/api/training-progress/active?user_id=default")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure - this endpoint returns active tasks
        assert "active_count" in data, "Missing active_count field"
        assert "tasks" in data, "Missing tasks field"
        
        print(f"✅ Training Progress: active_count={data.get('active_count')}")


class TestAdaptiveStrategyVariants:
    """Test Adaptive Strategy Variants - via optimal-strategy endpoint"""
    
    def test_optimal_strategy_has_variant_id(self):
        """Verify optimal strategy returns variant_id"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/optimal-strategy")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify recommended_strategy has variant_id
        strategy = data.get("recommended_strategy", {})
        assert "variant_id" in strategy, "Missing variant_id in recommended_strategy"
        assert strategy["variant_id"], "variant_id is empty"
        
        print(f"✅ Variant ID: {strategy['variant_id']}")
        print(f"✅ Variant Name: {strategy.get('name')}")
    
    def test_optimal_strategy_regime_info(self):
        """Verify optimal strategy returns regime info"""
        response = requests.get(f"{BASE_URL}/api/adaptive-strategy/optimal-strategy")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify current_regime exists
        regime = data.get("current_regime", {})
        assert "regime" in regime, "Missing regime field"
        assert "confidence" in regime, "Missing confidence field"
        
        # Verify regime is valid
        valid_regimes = ["bull", "bear", "sideways", "high_volatility", "low_volatility", "recovery", "distribution"]
        assert regime["regime"] in valid_regimes, f"Invalid regime: {regime['regime']}"
        
        print(f"✅ Current Regime: {regime.get('regime')} (confidence: {regime.get('confidence', 0):.2%})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
