"""
Deep Learning AI API Tests
Tests for LSTM price prediction, sentiment analysis, pattern recognition, and ensemble signals.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestDeepLearningStatus:
    """Tests for Deep Learning AI status endpoint"""
    
    def test_get_ai_status(self):
        """Test GET /api/deep-learning/status returns operational status"""
        response = requests.get(f"{BASE_URL}/api/deep-learning/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify status
        assert data["status"] == "operational"
        assert "models" in data
        assert "timestamp" in data
        
        # Verify model components
        models = data["models"]
        assert "lstm_price_predictor" in models
        assert "sentiment_analyzer" in models
        assert "pattern_recognizer" in models
        assert "ensemble_ready" in models
        
        # Verify LSTM model info
        lstm = models["lstm_price_predictor"]
        assert "trained" in lstm
        assert "sequence_length" in lstm
        assert lstm["sequence_length"] == 60
        assert "prediction_horizon" in lstm
        assert lstm["prediction_horizon"] == 5
        
        # Verify sentiment analyzer
        sentiment = models["sentiment_analyzer"]
        assert sentiment["available"] == True
        assert "bullish_keywords" in sentiment
        assert "bearish_keywords" in sentiment
        
        # Verify pattern recognizer
        pattern = models["pattern_recognizer"]
        assert pattern["available"] == True
        assert "patterns_supported" in pattern
        assert len(pattern["patterns_supported"]) > 0
        
        # Verify ensemble
        assert models["ensemble_ready"] == True
        assert "tensorflow_version" in models


class TestLSTMInfo:
    """Tests for LSTM model info endpoint"""
    
    def test_get_lstm_info(self):
        """Test GET /api/deep-learning/lstm/info returns model architecture"""
        response = requests.get(f"{BASE_URL}/api/deep-learning/lstm/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify model type
        assert data["model_type"] == "LSTM (Long Short-Term Memory)"
        
        # Verify architecture
        assert "architecture" in data
        arch = data["architecture"]
        assert "layers" in arch
        assert len(arch["layers"]) > 0
        assert arch["sequence_length"] == 60
        assert arch["prediction_horizon"] == 5
        
        # Verify training status
        assert "training_status" in data
        assert "is_trained" in data["training_status"]
        
        # Verify capabilities
        assert "capabilities" in data
        assert len(data["capabilities"]) > 0


class TestPatternDetection:
    """Tests for pattern detection endpoint"""
    
    def test_detect_patterns_bitcoin(self):
        """Test POST /api/deep-learning/detect-patterns/{coin_id} for Bitcoin"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/detect-patterns/bitcoin?window_days=30"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["coin_id"] == "bitcoin"
        assert data["window_days"] == 30
        assert "prices_analyzed" in data
        assert data["prices_analyzed"] > 0
        
        # Verify patterns
        assert "patterns" in data
        patterns = data["patterns"]
        assert "pattern" in patterns
        assert "confidence" in patterns
        assert patterns["confidence"] >= 0 and patterns["confidence"] <= 100
        
        # Verify pattern classification
        if patterns["pattern"] != "no_clear_pattern" and patterns["pattern"] != "insufficient_data":
            assert "is_bullish" in patterns or "is_bearish" in patterns
    
    def test_detect_patterns_ethereum(self):
        """Test pattern detection for Ethereum"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/detect-patterns/ethereum?window_days=30"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["coin_id"] == "ethereum"
        assert "patterns" in data
    
    def test_detect_patterns_solana(self):
        """Test pattern detection for Solana"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/detect-patterns/solana?window_days=30"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["coin_id"] == "solana"
        assert "patterns" in data


class TestSentimentAnalysis:
    """Tests for sentiment analysis endpoint"""
    
    def test_analyze_sentiment_bullish(self):
        """Test sentiment analysis with bullish news"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/analyze-sentiment",
            json={
                "texts": [
                    "Bitcoin surges to new ATH amid institutional adoption",
                    "Ethereum upgrade brings bullish momentum",
                    "Crypto market rally continues as investors accumulate"
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "overall_sentiment" in data
        assert "confidence" in data
        assert "sentiment_distribution" in data
        assert "news_analyzed" in data
        assert "detailed_analysis" in data
        
        # Verify sentiment is bullish for bullish news
        assert data["overall_sentiment"] == "bullish"
        assert data["confidence"] > 50
        assert data["news_analyzed"] == 3
    
    def test_analyze_sentiment_bearish(self):
        """Test sentiment analysis with bearish news"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/analyze-sentiment",
            json={
                "texts": [
                    "Crypto market crashes as SEC announces new regulations",
                    "Bitcoin dump continues amid fear and panic",
                    "Major exchange hack leads to massive sell-off"
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify sentiment is bearish for bearish news
        assert data["overall_sentiment"] == "bearish"
        assert data["confidence"] > 50
    
    def test_analyze_sentiment_mixed(self):
        """Test sentiment analysis with mixed news"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/analyze-sentiment",
            json={
                "texts": [
                    "Bitcoin price stable today",
                    "Market shows mixed signals",
                    "Traders await next move"
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "overall_sentiment" in data
        assert "sentiment_distribution" in data
    
    def test_analyze_sentiment_empty(self):
        """Test sentiment analysis with empty texts"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/analyze-sentiment",
            json={"texts": []}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return neutral for empty input
        assert data["overall_sentiment"] == "neutral"
        assert data["news_analyzed"] == 0


class TestMultiCoinSignals:
    """Tests for multi-coin signals endpoint (skipped due to long execution time)"""
    
    @pytest.mark.skip(reason="Multi-coin signals can take 2-3 minutes due to LSTM training")
    def test_get_multi_coin_signals(self):
        """Test POST /api/deep-learning/multi-signal"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/multi-signal",
            json={"coin_ids": ["bitcoin", "ethereum"]},
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "signals" in data
        assert "count" in data
        assert "timestamp" in data


class TestPricePrediction:
    """Tests for price prediction endpoint (skipped due to long execution time)"""
    
    @pytest.mark.skip(reason="Price prediction can take 1-2 minutes due to LSTM training")
    def test_predict_price_bitcoin(self):
        """Test POST /api/deep-learning/predict/{coin_id}"""
        response = requests.post(
            f"{BASE_URL}/api/deep-learning/predict/bitcoin?include_news=false",
            timeout=120
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "coin_id" in data
        assert "final_signal" in data
        assert "confidence" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
