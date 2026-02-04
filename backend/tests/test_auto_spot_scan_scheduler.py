"""
Test Auto-Spot Scan Scheduling Feature
Tests the new scheduled auto-spot scan endpoints:
- POST /api/training-scheduler/auto-spot-scan - Create schedule
- GET /api/training-scheduler/auto-spot-scan/status - Get status
- POST /api/training-scheduler/auto-spot-scan/run-now - Manual trigger
- DELETE /api/training-scheduler/auto-spot-scan - Remove schedule
- POST /api/training-scheduler/auto-spot-scan/toggle - Enable/disable
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAutoSpotScanScheduler:
    """Test auto-spot scan scheduling endpoints"""
    
    def test_get_auto_spot_scan_status(self):
        """Test GET /api/training-scheduler/auto-spot-scan/status"""
        response = requests.get(f"{BASE_URL}/api/training-scheduler/auto-spot-scan/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "enabled" in data
        assert isinstance(data["enabled"], bool)
        
        # If schedule exists, verify additional fields
        if data.get("schedule_id"):
            assert "interval_minutes" in data
            assert "paper_trade" in data
            assert "run_count" in data
            print(f"✓ Auto-spot scan status: enabled={data['enabled']}, interval={data.get('interval_minutes')}m")
        else:
            print("✓ No auto-spot scan schedule configured")
    
    def test_create_auto_spot_scan_schedule(self):
        """Test POST /api/training-scheduler/auto-spot-scan - Create schedule"""
        # First check if schedule already exists
        status_response = requests.get(f"{BASE_URL}/api/training-scheduler/auto-spot-scan/status")
        existing = status_response.json()
        
        # Create schedule request
        payload = {
            "interval_minutes": 60,
            "paper_trade": True,
            "enabled": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/training-scheduler/auto-spot-scan",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should either create new or return exists
        assert data.get("status") in ["created", "exists"]
        
        if data["status"] == "created":
            assert data.get("schedule_id") == "auto_spot_scan_60m"
            assert data.get("interval_minutes") == 60
            assert data.get("paper_trade") == True
            print(f"✓ Created new auto-spot scan schedule: {data['schedule_id']}")
        else:
            assert "message" in data
            print(f"✓ Schedule already exists: {data.get('message')}")
    
    def test_run_auto_spot_scan_now(self):
        """Test POST /api/training-scheduler/auto-spot-scan/run-now - Manual trigger"""
        response = requests.post(
            f"{BASE_URL}/api/training-scheduler/auto-spot-scan/run-now",
            params={"paper_trade": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify comprehensive AI analysis response
        assert "timestamp" in data
        assert "paper_trade" in data
        assert data["paper_trade"] == True
        assert "scanned_symbols" in data
        assert data["scanned_symbols"] == 10  # Should scan 10 coins
        
        # Verify opportunity counts
        assert "buy_opportunities" in data
        assert "sell_opportunities" in data
        assert "executed_trades" in data
        
        # Verify scan results contain AI analysis
        assert "scan_results" in data
        assert isinstance(data["scan_results"], list)
        assert len(data["scan_results"]) == 10
        
        # Verify each scan result has comprehensive AI analysis
        for result in data["scan_results"]:
            assert "symbol" in result
            assert "current_price" in result
            assert "signal" in result
            assert "score" in result
            assert "confidence" in result
            assert "action" in result
            assert "components" in result
            
            # Verify AI components
            components = result["components"]
            assert "order_book" in components
            assert "on_chain" in components
            assert "social" in components
            assert "transformer" in components
            assert "cross_asset" in components
            assert "advanced_ta" in components
        
        print(f"✓ Auto-spot scan completed: {data['scanned_symbols']} symbols scanned")
        print(f"  Buy opportunities: {data['buy_opportunities']}")
        print(f"  Sell opportunities: {data['sell_opportunities']}")
        print(f"  Executed trades: {data['executed_trades']}")
    
    def test_toggle_auto_spot_scan(self):
        """Test POST /api/training-scheduler/auto-spot-scan/toggle"""
        # First ensure schedule exists
        status_response = requests.get(f"{BASE_URL}/api/training-scheduler/auto-spot-scan/status")
        status = status_response.json()
        
        if not status.get("schedule_id"):
            pytest.skip("No auto-spot scan schedule to toggle")
        
        # Toggle to disabled
        response = requests.post(
            f"{BASE_URL}/api/training-scheduler/auto-spot-scan/toggle",
            params={"enabled": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if "error" not in data:
            assert data.get("enabled") == False
            print("✓ Toggled auto-spot scan to disabled")
            
            # Toggle back to enabled
            response = requests.post(
                f"{BASE_URL}/api/training-scheduler/auto-spot-scan/toggle",
                params={"enabled": True}
            )
            assert response.status_code == 200
            print("✓ Toggled auto-spot scan back to enabled")
        else:
            print(f"✓ Toggle returned: {data.get('error')}")
    
    def test_get_all_schedules(self):
        """Test GET /api/training-scheduler/ - List all schedules"""
        response = requests.get(f"{BASE_URL}/api/training-scheduler/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert "schedules" in data
        assert isinstance(data["schedules"], list)
        
        # Find auto-spot scan schedule
        auto_spot_schedules = [s for s in data["schedules"] if s.get("model_type") == "auto_spot_scan"]
        
        print(f"✓ Total schedules: {data['count']}")
        print(f"  Auto-spot scan schedules: {len(auto_spot_schedules)}")
        
        for schedule in data["schedules"]:
            print(f"  - {schedule.get('schedule_id')}: {schedule.get('model_type')} ({schedule.get('schedule_type')})")


class TestRegimePredictorDLModels:
    """Test regime predictor DL models (bilstm, cnn_lstm, attention)"""
    
    def test_regime_models_list(self):
        """Test GET /api/performance/regime/models - All 8 models trained"""
        response = requests.get(f"{BASE_URL}/api/performance/regime/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert "total" in data
        assert data["total"] == 8  # 3 ML + 5 DL models
        
        # Verify ML models
        ml_models = [m for m in data["models"] if m["type"] == "ML"]
        assert len(ml_models) == 3
        ml_names = [m["name"] for m in ml_models]
        assert "random_forest" in ml_names
        assert "gradient_boosting" in ml_names
        assert "svm" in ml_names
        
        # Verify DL models
        dl_models = [m for m in data["models"] if m["type"] == "DL"]
        assert len(dl_models) == 5
        dl_names = [m["name"] for m in dl_models]
        assert "lstm" in dl_names
        assert "gru" in dl_names
        assert "bilstm" in dl_names
        assert "cnn_lstm" in dl_names
        assert "attention" in dl_names
        
        # Verify all models are trained
        for model in data["models"]:
            assert model["is_trained"] == True
            assert model["accuracy"] > 0
        
        print(f"✓ All {data['total']} regime models trained")
        print(f"  ML models: {ml_names}")
        print(f"  DL models: {dl_names}")
        print(f"  Best model: {data['best_model']}")
    
    def test_regime_prediction_all_models(self):
        """Test POST /api/performance/regime/predict - All models return predictions"""
        response = requests.post(
            f"{BASE_URL}/api/performance/regime/predict",
            json={"symbol": "BTC"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "symbol" in data
        assert data["symbol"] == "BTC"
        assert "predicted_regime" in data
        assert "confidence" in data
        assert "model_used" in data
        assert "all_predictions" in data
        
        # Verify all 8 models return predictions
        predictions = data["all_predictions"]
        expected_models = ["random_forest", "gradient_boosting", "svm", "lstm", "gru", "bilstm", "cnn_lstm", "attention"]
        
        for model_name in expected_models:
            assert model_name in predictions, f"Missing prediction from {model_name}"
            model_pred = predictions[model_name]
            
            # Each model should return regime, confidence, accuracy
            assert "regime" in model_pred, f"{model_name} missing regime"
            assert "confidence" in model_pred, f"{model_name} missing confidence"
            assert "accuracy" in model_pred, f"{model_name} missing accuracy"
            
            # Verify valid regime values
            valid_regimes = ["strong_bull", "bull", "sideways", "bear", "strong_bear", "high_volatility", "accumulation"]
            assert model_pred["regime"] in valid_regimes, f"{model_name} returned invalid regime: {model_pred['regime']}"
        
        print(f"✓ All 8 models returned predictions for BTC")
        print(f"  Best model ({data['model_used']}): {data['predicted_regime']} ({data['confidence']}% confidence)")
        
        # Print all predictions
        for model_name, pred in predictions.items():
            print(f"  {model_name}: {pred['regime']} ({pred['confidence']}%)")


class TestRLTrainingStatus:
    """Test RL Agent training status"""
    
    def test_learning_status(self):
        """Test GET /api/learning/status - Check RL training status"""
        response = requests.get(f"{BASE_URL}/api/learning/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "learning_active" in data
        assert "models" in data
        
        # Check model training status
        models = data["models"]
        assert "transformer" in models
        assert "rl_agent" in models
        assert "regime" in models
        
        print(f"✓ Learning status retrieved")
        print(f"  Learning active: {data['learning_active']}")
        print(f"  Transformer trained: {models['transformer']['trained']}")
        print(f"  RL Agent trained: {models['rl_agent']['trained']}")
        print(f"  Regime trained: {models['regime']['trained']}")
    
    def test_rl_training_schedule_exists(self):
        """Test that RL training schedule is configured"""
        response = requests.get(f"{BASE_URL}/api/training-scheduler/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find RL agent schedule
        rl_schedules = [s for s in data["schedules"] if s.get("model_type") == "rl_agent"]
        
        if rl_schedules:
            schedule = rl_schedules[0]
            print(f"✓ RL training schedule found: {schedule['schedule_id']}")
            print(f"  Schedule type: {schedule['schedule_type']}")
            print(f"  Enabled: {schedule['enabled']}")
            print(f"  Next run: {schedule.get('next_run')}")
        else:
            print("⚠ No RL training schedule configured")


class TestAutoSpotScanAIAnalysis:
    """Test that auto-spot scan returns comprehensive AI analysis"""
    
    def test_scan_results_have_all_components(self):
        """Verify scan results include all AI prediction components"""
        response = requests.post(
            f"{BASE_URL}/api/training-scheduler/auto-spot-scan/run-now",
            params={"paper_trade": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Get first scan result
        scan_results = data.get("scan_results", [])
        assert len(scan_results) > 0
        
        result = scan_results[0]
        components = result.get("components", {})
        
        # Test order_book component
        assert "order_book" in components
        order_book = components["order_book"]
        assert "score" in order_book
        assert "imbalance" in order_book
        
        # Test on_chain component
        assert "on_chain" in components
        on_chain = components["on_chain"]
        assert "score" in on_chain
        assert "nvt_ratio" in on_chain
        
        # Test social component
        assert "social" in components
        social = components["social"]
        assert "score" in social
        
        # Test transformer component
        assert "transformer" in components
        transformer = components["transformer"]
        assert "score" in transformer
        assert "prediction" in transformer
        assert "confidence" in transformer
        
        # Test cross_asset component
        assert "cross_asset" in components
        cross_asset = components["cross_asset"]
        assert "score" in cross_asset
        assert "risk_regime" in cross_asset
        
        # Test advanced_ta component
        assert "advanced_ta" in components
        advanced_ta = components["advanced_ta"]
        assert "score" in advanced_ta
        assert "divergence" in advanced_ta
        
        print(f"✓ Scan result for {result['symbol']} has all AI components")
        print(f"  Order Book Score: {order_book['score']}")
        print(f"  On-Chain Score: {on_chain['score']}")
        print(f"  Social Score: {social['score']}")
        print(f"  Transformer Score: {transformer['score']} ({transformer['prediction']})")
        print(f"  Cross-Asset Score: {cross_asset['score']}")
        print(f"  Advanced TA Score: {advanced_ta['score']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
