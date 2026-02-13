"""
AI Chat API Tests
Tests for the AI Chat feature including ask, suggestions, quick-analysis, and history endpoints.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAIChatSuggestions:
    """Test AI Chat suggestions endpoint - no LLM call required"""
    
    def test_get_suggestions_success(self):
        """Test GET /api/ai-chat/suggestions returns suggestions"""
        response = requests.get(f"{BASE_URL}/api/ai-chat/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0
        
        # Verify each category has required fields
        for category in data["suggestions"]:
            assert "category" in category
            assert "queries" in category
            assert isinstance(category["queries"], list)
            assert len(category["queries"]) > 0
        
        # Verify expected categories exist
        categories = [s["category"] for s in data["suggestions"]]
        assert "Coin Analysis" in categories
        assert "Market Overview" in categories
        assert "Trading Strategy" in categories


class TestAIChatAsk:
    """Test AI Chat ask endpoint - requires LLM call"""
    
    def test_ask_simple_question(self):
        """Test POST /api/ai-chat/ask with a simple question"""
        payload = {
            "query": "What is Bitcoin?",
            "session_id": "test_session_1",
            "include_market_data": True,
            "include_news": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/ask",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "response" in data
        assert "query" in data
        assert "session_id" in data
        assert "coins_mentioned" in data
        assert "timestamp" in data
        
        # Verify response content
        assert len(data["response"]) > 0
        assert data["query"] == "What is Bitcoin?"
        assert data["session_id"] == "test_session_1"
        assert "bitcoin" in data["coins_mentioned"]
        assert data.get("error") is False or data.get("error") is None
    
    def test_ask_with_coin_mention(self):
        """Test that coin mentions are detected correctly"""
        payload = {
            "query": "Compare Ethereum and Solana",
            "session_id": "test_session_2",
            "include_market_data": True,
            "include_news": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/ask",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify coins are detected
        assert "ethereum" in data["coins_mentioned"]
        assert "solana" in data["coins_mentioned"]
    
    def test_ask_query_too_short(self):
        """Test validation for query too short"""
        payload = {
            "query": "ab",
            "session_id": "test_session_3"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/ask",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_ask_query_too_long(self):
        """Test validation for query too long"""
        payload = {
            "query": "a" * 1001,  # Over 1000 characters
            "session_id": "test_session_4"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/ask",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestAIChatQuickAnalysis:
    """Test AI Chat quick analysis endpoint"""
    
    def test_quick_analysis_bitcoin(self):
        """Test POST /api/ai-chat/quick-analysis for Bitcoin"""
        payload = {
            "coin_id": "bitcoin"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/quick-analysis",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "response" in data
        assert "coins_mentioned" in data
        assert len(data["response"]) > 0
        assert "bitcoin" in data["coins_mentioned"]


class TestAIChatHistory:
    """Test AI Chat history endpoint"""
    
    def test_get_history_empty_session(self):
        """Test GET /api/ai-chat/history for a new session"""
        session_id = f"test_history_{int(time.time())}"
        
        response = requests.get(
            f"{BASE_URL}/api/ai-chat/history/{session_id}",
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "history" in data
        assert "count" in data
        assert data["session_id"] == session_id
        assert isinstance(data["history"], list)
    
    def test_get_history_after_chat(self):
        """Test that history is populated after chat"""
        session_id = f"test_history_chat_{int(time.time())}"
        
        # First, send a message
        ask_payload = {
            "query": "What is Ethereum?",
            "session_id": session_id,
            "include_market_data": False,
            "include_news": False
        }
        
        ask_response = requests.post(
            f"{BASE_URL}/api/ai-chat/ask",
            json=ask_payload,
            timeout=60
        )
        
        assert ask_response.status_code == 200
        
        # Then check history
        history_response = requests.get(
            f"{BASE_URL}/api/ai-chat/history/{session_id}",
            timeout=30
        )
        
        assert history_response.status_code == 200
        data = history_response.json()
        
        # History should have at least one entry
        assert data["count"] >= 1
        assert len(data["history"]) >= 1
        
        # Verify history entry structure
        if data["history"]:
            entry = data["history"][0]
            assert "query" in entry
            assert "response" in entry
    
    def test_delete_history(self):
        """Test DELETE /api/ai-chat/history/{session_id}"""
        session_id = f"test_delete_{int(time.time())}"
        
        response = requests.delete(
            f"{BASE_URL}/api/ai-chat/history/{session_id}",
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "cleared"
        assert data["session_id"] == session_id


class TestAIChatStrategyAdvice:
    """Test AI Chat strategy advice endpoint"""
    
    def test_strategy_advice_moderate_risk(self):
        """Test POST /api/ai-chat/strategy-advice with moderate risk"""
        payload = {
            "portfolio_value": 10000.0,
            "risk_tolerance": "moderate"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/strategy-advice",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert len(data["response"]) > 0
    
    def test_strategy_advice_invalid_portfolio_value(self):
        """Test validation for invalid portfolio value"""
        payload = {
            "portfolio_value": -100.0,
            "risk_tolerance": "moderate"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/strategy-advice",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 400
    
    def test_strategy_advice_invalid_risk_tolerance(self):
        """Test validation for invalid risk tolerance"""
        payload = {
            "portfolio_value": 10000.0,
            "risk_tolerance": "invalid_risk"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/strategy-advice",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 400


class TestAIChatExplainPattern:
    """Test AI Chat explain pattern endpoint"""
    
    def test_explain_pattern(self):
        """Test POST /api/ai-chat/explain-pattern"""
        payload = {
            "pattern_name": "double_top",
            "coin_id": "bitcoin"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/explain-pattern",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert len(data["response"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
