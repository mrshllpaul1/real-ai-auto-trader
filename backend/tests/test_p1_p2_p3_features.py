"""
Test P1, P2, P3 Features:
- P1: AI Chat Trading Execution (execute-trade, trade-history)
- P2: Continuous AI Learning Loop (store-prediction, record-outcome, status, model-performance, insights, training-feedback)
- P3: Daily OHLCV Updates Scheduling (daily-ohlcv-update, ohlcv-update-now, scheduler status)
"""

import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestP1AITradingExecution:
    """P1: AI Chat Trading Execution Tests"""
    
    def test_execute_trade_preview_buy_btc(self):
        """Test trade preview with confirm=false for BTC buy"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-trade",
            json={
                "action": "buy",
                "coin": "BTC",
                "amount_usd": 100,
                "confirm": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify preview response structure
        assert data["status"] == "confirmation_required"
        assert "trade_id" in data
        assert "preview" in data
        assert "message" in data
        assert "instruction" in data
        assert "warning" in data
        
        # Verify preview details
        preview = data["preview"]
        assert preview["action"] == "buy"
        assert preview["coin"] == "BTC"
        assert preview["pair"] == "XXBTZUSD"
        assert preview["volume"] > 0
        assert preview["price"] > 0
        assert preview["total_usd"] == 100.0
        assert preview["order_type"] == "market"
        
        print(f"✓ Trade preview: BUY {preview['volume']:.6f} BTC at ${preview['price']:.2f}")
    
    def test_execute_trade_preview_sell_eth(self):
        """Test trade preview with confirm=false for ETH sell"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-trade",
            json={
                "action": "sell",
                "coin": "ETH",
                "amount_usd": 50,
                "confirm": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "confirmation_required"
        assert data["preview"]["action"] == "sell"
        assert data["preview"]["coin"] == "ETH"
        assert data["preview"]["pair"] == "XETHZUSD"
        
        print(f"✓ Trade preview: SELL ETH at ${data['preview']['price']:.2f}")
    
    def test_execute_trade_invalid_action(self):
        """Test trade with invalid action"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-trade",
            json={
                "action": "hold",  # Invalid action
                "coin": "BTC",
                "amount_usd": 100,
                "confirm": False
            }
        )
        assert response.status_code == 400
        assert "buy" in response.json()["detail"].lower() or "sell" in response.json()["detail"].lower()
    
    def test_execute_trade_unsupported_coin(self):
        """Test trade with unsupported coin"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-trade",
            json={
                "action": "buy",
                "coin": "UNKNOWN",
                "amount_usd": 100,
                "confirm": False
            }
        )
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()
    
    def test_execute_trade_missing_amount(self):
        """Test trade without amount"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-trade",
            json={
                "action": "buy",
                "coin": "BTC",
                "confirm": False
            }
        )
        assert response.status_code == 400
        assert "amount" in response.json()["detail"].lower()
    
    def test_trade_history_endpoint(self):
        """Test trade history endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai-chat/trade-history")
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert "trades" in data
        assert isinstance(data["trades"], list)
        
        print(f"✓ Trade history: {data['count']} trades")
    
    def test_trade_history_with_limit(self):
        """Test trade history with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/ai-chat/trade-history?limit=5")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["trades"]) <= 5


class TestP2AILearningLoop:
    """P2: Continuous AI Learning Loop Tests"""
    
    def test_learning_service_status(self):
        """Test learning service status endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/status")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "operational"
        assert "total_predictions" in data
        assert "verified_predictions" in data
        assert "total_outcomes" in data
        assert "verification_rate" in data
        
        print(f"✓ Learning status: {data['total_predictions']} predictions, {data['verified_predictions']} verified")
    
    def test_store_prediction_price_direction(self):
        """Test storing a price direction prediction"""
        response = requests.post(
            f"{BASE_URL}/api/ai-learning/store-prediction",
            json={
                "prediction_type": "price_direction",
                "coin_symbol": "BTC",
                "prediction": {"direction": "up", "target_price": 80000},
                "confidence": 80,
                "source_model": "lstm_test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "prediction_id" in data
        assert "BTC" in data["message"]
        
        print(f"✓ Stored prediction: {data['prediction_id']}")
        return data["prediction_id"]
    
    def test_store_prediction_gem_potential(self):
        """Test storing a gem potential prediction"""
        response = requests.post(
            f"{BASE_URL}/api/ai-learning/store-prediction",
            json={
                "prediction_type": "gem_potential",
                "coin_symbol": "SOL",
                "prediction": {"expected_gain_pct": 50, "timeframe_days": 30},
                "confidence": 65,
                "source_model": "gem_predictor_test",
                "metadata": {"market_cap": "medium", "volume_trend": "increasing"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "prediction_id" in data
        
        print(f"✓ Stored gem prediction: {data['prediction_id']}")
    
    def test_store_prediction_signal(self):
        """Test storing a trading signal prediction"""
        response = requests.post(
            f"{BASE_URL}/api/ai-learning/store-prediction",
            json={
                "prediction_type": "signal",
                "coin_symbol": "ETH",
                "prediction": {"signal": "BUY", "strength": "strong"},
                "confidence": 75,
                "source_model": "ensemble_test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        print(f"✓ Stored signal prediction: {data['prediction_id']}")
    
    def test_record_outcome_by_coin_and_type(self):
        """Test recording outcome by coin and prediction type"""
        # First store a prediction
        store_response = requests.post(
            f"{BASE_URL}/api/ai-learning/store-prediction",
            json={
                "prediction_type": "price_direction",
                "coin_symbol": "ADA",
                "prediction": {"direction": "up"},
                "confidence": 70,
                "source_model": "test_model"
            }
        )
        assert store_response.status_code == 200
        
        # Record outcome
        response = requests.post(
            f"{BASE_URL}/api/ai-learning/record-outcome",
            json={
                "coin_symbol": "ADA",
                "prediction_type": "price_direction",
                "actual_outcome": {"direction": "up"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "prediction_id" in data
        assert "accuracy_score" in data
        assert "was_correct" in data
        
        print(f"✓ Recorded outcome: accuracy={data['accuracy_score']}, correct={data['was_correct']}")
    
    def test_record_outcome_by_prediction_id(self):
        """Test recording outcome by prediction ID"""
        # First store a prediction
        store_response = requests.post(
            f"{BASE_URL}/api/ai-learning/store-prediction",
            json={
                "prediction_type": "price_target",
                "coin_symbol": "DOT",
                "prediction": {"target_price": 10.0},
                "confidence": 60,
                "source_model": "test_model"
            }
        )
        assert store_response.status_code == 200
        prediction_id = store_response.json()["prediction_id"]
        
        # Record outcome by ID
        response = requests.post(
            f"{BASE_URL}/api/ai-learning/record-outcome",
            json={
                "prediction_id": prediction_id,
                "actual_outcome": {"actual_price": 9.5}
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["prediction_id"] == prediction_id
        
        print(f"✓ Recorded outcome by ID: {prediction_id}")
    
    def test_model_performance_all_models(self):
        """Test getting performance for all models"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/model-performance")
        assert response.status_code == 200
        data = response.json()
        
        assert "model" in data
        assert "days" in data
        assert "performance" in data
        
        print(f"✓ Model performance: {data['model']} over {data['days']} days")
    
    def test_model_performance_specific_model(self):
        """Test getting performance for specific model"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/model-performance?model=lstm_test&days=7")
        assert response.status_code == 200
        data = response.json()
        
        assert data["model"] == "lstm_test"
        assert data["days"] == 7
    
    def test_learning_insights(self):
        """Test getting learning insights"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/insights")
        assert response.status_code == 200
        data = response.json()
        
        assert "generated_at" in data
        assert "model_rankings" in data
        assert "weak_areas" in data
        assert "strong_areas" in data
        assert "recommended_weight_adjustments" in data
        assert "total_predictions_analyzed" in data
        
        print(f"✓ Learning insights: {data['total_predictions_analyzed']} predictions analyzed")
    
    def test_training_feedback_all_models(self):
        """Test getting training feedback for all models"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/training-feedback")
        assert response.status_code == 200
        data = response.json()
        
        assert "model" in data
        assert "period_days" in data
        assert "total_verified" in data
        assert "successful_patterns" in data
        assert "failed_patterns" in data
        assert "by_coin" in data
        assert "by_confidence" in data
        
        print(f"✓ Training feedback: {data['total_verified']} verified predictions")
    
    def test_training_feedback_specific_model(self):
        """Test getting training feedback for specific model"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/training-feedback?model=lstm_test")
        assert response.status_code == 200
        data = response.json()
        
        assert data["model"] == "lstm_test"


class TestP3DailyOHLCVScheduling:
    """P3: Daily OHLCV Updates Scheduling Tests"""
    
    def test_scheduler_status(self):
        """Test scheduler status endpoint"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "running" in data
        assert "jobs" in data
        assert "job_count" in data
        assert "scheduled_jobs" in data
        
        print(f"✓ Scheduler status: running={data['running']}, jobs={data['job_count']}")
    
    def test_add_daily_ohlcv_update_job(self):
        """Test adding daily OHLCV update job"""
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/daily-ohlcv-update",
            json={"hour": 5}  # 5 AM UTC
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["job_id"] == "daily_ohlcv_update"
        assert "Daily at 5:00 UTC" in data["schedule"]
        
        print(f"✓ Added OHLCV update job: {data['schedule']}")
    
    def test_add_daily_ohlcv_update_with_coins(self):
        """Test adding daily OHLCV update job with specific coins"""
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/daily-ohlcv-update",
            json={"hour": 4, "coins": ["BTC", "ETH", "SOL"]}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["coins"] == ["BTC", "ETH", "SOL"]
    
    def test_run_ohlcv_update_now(self):
        """Test running OHLCV update immediately"""
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/ohlcv-update-now",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return update results
        assert "coins_updated" in data or "error" in data
        
        if "coins_updated" in data:
            print(f"✓ OHLCV update: {data['coins_updated']} coins updated, {data.get('new_records', 0)} records")
        else:
            print(f"⚠ OHLCV update: {data.get('error', 'unknown error')}")
    
    def test_run_ohlcv_update_specific_coins(self):
        """Test running OHLCV update for specific coins"""
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/ohlcv-update-now?coins=BTC&coins=ETH",
            json={}
        )
        # Note: The endpoint accepts coins as query params or body
        assert response.status_code == 200
    
    def test_verify_job_scheduled(self):
        """Test verifying OHLCV job is scheduled"""
        # First add the job
        requests.post(
            f"{BASE_URL}/api/scheduler/jobs/daily-ohlcv-update",
            json={"hour": 4}
        )
        
        # Check scheduler status
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify job is in scheduled jobs
        scheduled_jobs = data.get("scheduled_jobs", {})
        assert "daily_ohlcv_update" in scheduled_jobs
        
        job_info = scheduled_jobs["daily_ohlcv_update"]
        assert "next_run" in job_info
        assert job_info["name"] == "Daily OHLCV Data Update"
        
        print(f"✓ OHLCV job scheduled: next run at {job_info['next_run']}")
    
    def test_scheduler_execution_history(self):
        """Test getting scheduler execution history"""
        response = requests.get(f"{BASE_URL}/api/scheduler/history?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "count" in data
        assert isinstance(data["history"], list)
        
        print(f"✓ Scheduler history: {data['count']} executions")


class TestIntegrationFlows:
    """Integration tests for complete flows"""
    
    def test_prediction_to_outcome_flow(self):
        """Test complete flow: store prediction -> record outcome -> check performance"""
        # 1. Store prediction
        store_response = requests.post(
            f"{BASE_URL}/api/ai-learning/store-prediction",
            json={
                "prediction_type": "price_direction",
                "coin_symbol": "LINK",
                "prediction": {"direction": "up"},
                "confidence": 85,
                "source_model": "integration_test"
            }
        )
        assert store_response.status_code == 200
        prediction_id = store_response.json()["prediction_id"]
        
        # 2. Record outcome
        outcome_response = requests.post(
            f"{BASE_URL}/api/ai-learning/record-outcome",
            json={
                "prediction_id": prediction_id,
                "actual_outcome": {"direction": "up"}
            }
        )
        assert outcome_response.status_code == 200
        assert outcome_response.json()["was_correct"] == True
        
        # 3. Check status updated
        status_response = requests.get(f"{BASE_URL}/api/ai-learning/status")
        assert status_response.status_code == 200
        
        print("✓ Complete prediction-to-outcome flow successful")
    
    def test_trade_preview_multiple_coins(self):
        """Test trade preview for multiple supported coins"""
        coins = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "AVAX", "LINK"]
        
        for coin in coins:
            response = requests.post(
                f"{BASE_URL}/api/ai-chat/execute-trade",
                json={
                    "action": "buy",
                    "coin": coin,
                    "amount_usd": 50,
                    "confirm": False
                }
            )
            assert response.status_code == 200, f"Failed for {coin}"
            data = response.json()
            assert data["status"] == "confirmation_required"
            assert data["preview"]["coin"] == coin
        
        print(f"✓ Trade preview successful for {len(coins)} coins")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
