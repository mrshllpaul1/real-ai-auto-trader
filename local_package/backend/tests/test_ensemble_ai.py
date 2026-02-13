"""
Ensemble AI API Tests
Tests for the Ensemble AI feature that combines all ML/DL models
to optimize predictions and rebuild the coin universe.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEnsembleAIStatus:
    """Test Ensemble AI status and initialization"""
    
    def test_ensemble_status_returns_initialized(self):
        """GET /api/ensemble/status - Should return ensemble_initialized: true"""
        response = requests.get(f"{BASE_URL}/api/ensemble/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "ensemble_initialized" in data
        assert data["ensemble_initialized"] == True
        assert "optimizer_initialized" in data
        assert data["optimizer_initialized"] == True
        assert "deep_learning_available" in data
        assert "model_weights" in data
        assert "timestamp" in data
        
    def test_ensemble_status_has_model_weights(self):
        """GET /api/ensemble/status - Should return model weights"""
        response = requests.get(f"{BASE_URL}/api/ensemble/status")
        assert response.status_code == 200
        
        data = response.json()
        weights = data.get("model_weights", {})
        
        # Verify all expected models are present
        expected_models = ["lstm", "technical", "pattern", "momentum", "trend", "volatility", "sentiment"]
        for model in expected_models:
            assert model in weights, f"Missing model weight: {model}"
            assert isinstance(weights[model], (int, float))
            assert 0 <= weights[model] <= 1
        
        # Weights should sum to approximately 1
        total_weight = sum(weights.values())
        assert 0.99 <= total_weight <= 1.01, f"Weights sum to {total_weight}, expected ~1.0"


class TestEnsemblePrediction:
    """Test Ensemble AI prediction endpoints"""
    
    def test_predict_bitcoin_returns_signal(self):
        """POST /api/ensemble/predict/{coin_id} - Should return ensemble prediction"""
        response = requests.post(f"{BASE_URL}/api/ensemble/predict/bitcoin?optimize_weights=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "coin_id" in data
        assert data["coin_id"] == "bitcoin"
        assert "final_signal" in data
        assert data["final_signal"] in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 100
        assert "model_results" in data
        assert isinstance(data["model_results"], list)
        assert "weights_used" in data
        assert "timestamp" in data
        
    def test_predict_ethereum_returns_signal(self):
        """POST /api/ensemble/predict/{coin_id} - Test with ethereum"""
        response = requests.post(f"{BASE_URL}/api/ensemble/predict/ethereum?optimize_weights=false")
        assert response.status_code == 200
        
        data = response.json()
        assert data["coin_id"] == "ethereum"
        assert "final_signal" in data
        assert "confidence" in data
        assert "accuracy_estimate" in data
        assert 0 <= data["accuracy_estimate"] <= 1
        
    def test_predict_invalid_coin_returns_error(self):
        """POST /api/ensemble/predict/{coin_id} - Invalid coin should return 404"""
        response = requests.post(f"{BASE_URL}/api/ensemble/predict/invalid_coin_xyz123")
        assert response.status_code == 404
        
    def test_predict_has_model_results(self):
        """POST /api/ensemble/predict/{coin_id} - Should include individual model results"""
        response = requests.post(f"{BASE_URL}/api/ensemble/predict/bitcoin")
        assert response.status_code == 200
        
        data = response.json()
        model_results = data.get("model_results", [])
        assert len(model_results) > 0
        
        for result in model_results:
            assert "model" in result
            assert "signal" in result
            assert result["signal"] in ["bullish", "bearish", "neutral"]
            assert "confidence" in result
            assert "weight" in result


class TestUniverseRebuild:
    """Test Universe rebuild functionality"""
    
    def test_rebuild_universe_starts_task(self):
        """POST /api/ensemble/rebuild-universe - Should start background task"""
        response = requests.post(
            f"{BASE_URL}/api/ensemble/rebuild-universe",
            json={"target_size": 30, "analyze_count": 100}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Either started or already running
        assert data["status"] in ["started", "already_running"]
        
    def test_build_status_returns_progress(self):
        """GET /api/ensemble/build-status - Should return progress info"""
        response = requests.get(f"{BASE_URL}/api/ensemble/build-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "progress" in data
        assert isinstance(data["progress"], (int, float))
        assert 0 <= data["progress"] <= 100
        assert "progress_message" in data
        assert "endpoints" in data


class TestOptimalUniverse:
    """Test optimal universe retrieval"""
    
    def test_optimal_universe_returns_coins(self):
        """GET /api/ensemble/optimal-universe - Should return list of coins"""
        response = requests.get(f"{BASE_URL}/api/ensemble/optimal-universe")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "coins" in data
        assert isinstance(data["coins"], list)
        assert "top_10" in data
        assert "categories" in data
        assert "avg_ensemble_score" in data
        
    def test_optimal_universe_coins_have_scores(self):
        """GET /api/ensemble/optimal-universe - Coins should have ensemble scores"""
        response = requests.get(f"{BASE_URL}/api/ensemble/optimal-universe")
        assert response.status_code == 200
        
        data = response.json()
        coins = data.get("coins", [])
        
        if len(coins) > 0:
            for coin in coins[:5]:  # Check first 5 coins
                assert "coin_id" in coin
                assert "symbol" in coin
                assert "ensemble_score" in coin
                assert 0 <= coin["ensemble_score"] <= 100
                assert "market_cap" in coin
                
    def test_optimal_universe_categories_breakdown(self):
        """GET /api/ensemble/optimal-universe - Should have category breakdown"""
        response = requests.get(f"{BASE_URL}/api/ensemble/optimal-universe")
        assert response.status_code == 200
        
        data = response.json()
        categories = data.get("categories", {})
        
        expected_categories = ["large_cap", "mid_cap", "small_cap", "micro_cap", "hidden_gems"]
        for cat in expected_categories:
            assert cat in categories, f"Missing category: {cat}"
            assert isinstance(categories[cat], int)


class TestHiddenGems:
    """Test hidden gems endpoint"""
    
    def test_hidden_gems_returns_list(self):
        """GET /api/ensemble/hidden-gems - Should return high-score low-cap coins"""
        response = requests.get(f"{BASE_URL}/api/ensemble/hidden-gems")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "hidden_gems" in data
        assert isinstance(data["hidden_gems"], list)
        assert "criteria" in data
        
    def test_hidden_gems_criteria_explained(self):
        """GET /api/ensemble/hidden-gems - Should explain criteria"""
        response = requests.get(f"{BASE_URL}/api/ensemble/hidden-gems")
        assert response.status_code == 200
        
        data = response.json()
        criteria = data.get("criteria", {})
        assert "min_score" in criteria
        assert "max_market_cap" in criteria
        assert "description" in criteria


class TestPortfolioComparison:
    """Test portfolio comparison endpoint"""
    
    def test_comparison_returns_data(self):
        """GET /api/ensemble/comparison - Should return old vs new comparison"""
        response = requests.get(f"{BASE_URL}/api/ensemble/comparison")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        
        # If comparison is available
        if data["status"] in ["available", "from_history"]:
            comparison = data.get("comparison", {})
            if comparison:
                # Check for comparison fields
                assert "overlap_count" in comparison or "retained" in comparison
                assert "added_count" in comparison or "new_additions" in comparison
                assert "removed_count" in comparison or "dropped" in comparison


class TestModelWeights:
    """Test model weights endpoint"""
    
    def test_weights_returns_all_models(self):
        """GET /api/ensemble/weights - Should return current model weights"""
        response = requests.get(f"{BASE_URL}/api/ensemble/weights")
        assert response.status_code == 200
        
        data = response.json()
        assert "weights" in data
        assert "description" in data
        
        weights = data["weights"]
        expected_models = ["lstm", "technical", "pattern", "momentum", "trend", "volatility", "sentiment"]
        for model in expected_models:
            assert model in weights
            
    def test_weights_descriptions_present(self):
        """GET /api/ensemble/weights - Should have model descriptions"""
        response = requests.get(f"{BASE_URL}/api/ensemble/weights")
        assert response.status_code == 200
        
        data = response.json()
        descriptions = data.get("description", {})
        
        assert "lstm" in descriptions
        assert "technical" in descriptions
        assert "pattern" in descriptions


class TestBatchPrediction:
    """Test batch prediction endpoint"""
    
    def test_batch_predict_multiple_coins(self):
        """POST /api/ensemble/predict-batch - Should predict multiple coins"""
        response = requests.post(
            f"{BASE_URL}/api/ensemble/predict-batch",
            json={"coin_ids": ["bitcoin", "ethereum"], "optimize_weights": False}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "predictions" in data
        assert len(data["predictions"]) >= 1
        
    def test_batch_predict_max_limit(self):
        """POST /api/ensemble/predict-batch - Should enforce max 20 coins"""
        # Create list of 25 coins
        coin_ids = ["bitcoin"] * 25
        response = requests.post(
            f"{BASE_URL}/api/ensemble/predict-batch",
            json={"coin_ids": coin_ids, "optimize_weights": False}
        )
        assert response.status_code == 400


class TestOptimizeWeights:
    """Test weight optimization endpoint"""
    
    def test_optimize_weights_returns_old_and_new(self):
        """POST /api/ensemble/optimize-weights - Should return old and new weights"""
        response = requests.post(f"{BASE_URL}/api/ensemble/optimize-weights")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "optimized"
        assert "old_weights" in data
        assert "new_weights" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
