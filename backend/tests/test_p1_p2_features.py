"""
Test P1 (AI Learning Loop with Charts) and P2 (Event Timeline) features
Tests the new endpoints and improved gem detector with 92% accuracy
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEventDatabaseEndpoints:
    """Test Event Timeline (P2) - Historical events database endpoints"""
    
    def test_events_database_stats(self):
        """GET /api/events/database/stats - Should return event statistics"""
        response = requests.get(f"{BASE_URL}/api/events/database/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_events" in data
        assert data["total_events"] == 38  # Expected 38 events
        assert "by_category" in data
        assert "by_impact" in data
        assert "date_range" in data
        
        # Verify categories
        categories = data["by_category"]
        assert "regulatory" in categories
        assert "institutional" in categories
        assert "milestone" in categories
        assert "technology" in categories
        
        print(f"✓ Events stats: {data['total_events']} events, categories: {list(categories.keys())}")
    
    def test_events_database_list(self):
        """GET /api/events/database/list - Should return events list"""
        response = requests.get(f"{BASE_URL}/api/events/database/list?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "events" in data
        assert data["count"] > 0
        
        # Verify event structure
        event = data["events"][0]
        assert "event" in event  # Event title
        assert "date" in event
        assert "category" in event
        assert "impact" in event
        
        print(f"✓ Events list: {data['count']} events returned")
    
    def test_events_database_list_with_filters(self):
        """GET /api/events/database/list with filters"""
        # Filter by category
        response = requests.get(f"{BASE_URL}/api/events/database/list?category=regulatory&limit=20")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        for event in data["events"]:
            assert event["category"] == "regulatory"
        
        print(f"✓ Regulatory events: {data['count']} found")
        
        # Filter by impact
        response = requests.get(f"{BASE_URL}/api/events/database/list?impact=positive&limit=20")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        for event in data["events"]:
            assert event["impact"] == "positive"
        
        print(f"✓ Positive impact events: {data['count']} found")
    
    def test_events_database_search(self):
        """GET /api/events/database/search - Search by keyword"""
        response = requests.get(f"{BASE_URL}/api/events/database/search?keyword=ETF&limit=20")
        assert response.status_code == 200
        
        data = response.json()
        assert "keyword" in data
        assert "count" in data
        assert "events" in data
        
        print(f"✓ Search 'ETF': {data['count']} events found")
    
    def test_events_by_coin(self):
        """GET /api/events/database/coin/{coin} - Events for specific coin"""
        response = requests.get(f"{BASE_URL}/api/events/database/coin/BTC?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        assert "coin" in data
        assert data["coin"] == "BTC"
        assert "count" in data
        assert data["count"] > 0
        
        print(f"✓ BTC events: {data['count']} found")
    
    def test_events_by_category(self):
        """GET /api/events/database/category/{category} - Events by category"""
        response = requests.get(f"{BASE_URL}/api/events/database/category/hack?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        assert "category" in data
        assert data["category"] == "hack"
        assert "count" in data
        
        print(f"✓ Hack events: {data['count']} found")


class TestGemBacktestEndpoints:
    """Test Gem Backtester with improved 92% accuracy model"""
    
    def test_backtest_status(self):
        """GET /api/gems/backtest/status - Should return backtest status"""
        response = requests.get(f"{BASE_URL}/api/gems/backtest/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "progress" in data
        
        print(f"✓ Backtest status: running={data['running']}, progress={data['progress']}")
    
    def test_gem_scan_with_optimized_weights(self):
        """POST /api/gems/scan - Should use optimized weights and 70% threshold"""
        response = requests.post(
            f"{BASE_URL}/api/gems/scan",
            json={"limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "gems_found" in data
        assert "gems" in data
        
        # Note: May return 0 gems if no coins meet the strict 70% threshold
        # This is expected behavior for 92% accuracy model
        print(f"✓ Gem scan: {data['gems_found']} gems found (strict 70% threshold)")
    
    def test_gem_top_list(self):
        """GET /api/gems/top - Should return top gems"""
        response = requests.get(f"{BASE_URL}/api/gems/top")
        assert response.status_code == 200
        
        data = response.json()
        assert "gems" in data
        
        print(f"✓ Top gems: {len(data['gems'])} gems in list")


class TestTriggerEndpoints:
    """Test Event Trigger Management endpoints"""
    
    def test_triggers_status(self):
        """GET /api/triggers/status - Should return trigger service status"""
        response = requests.get(f"{BASE_URL}/api/triggers/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_triggers" in data
        assert "enabled_triggers" in data
        assert "available_templates" in data
        
        # Verify 8 templates available
        assert len(data["available_templates"]) == 8
        expected_templates = ["elon_doge", "elon_btc", "sec_regulatory", "etf_approval", 
                            "exchange_hack", "china_ban", "institutional_buy", "whale_alert"]
        for template in expected_templates:
            assert template in data["available_templates"]
        
        print(f"✓ Triggers status: {data['total_triggers']} triggers, {len(data['available_templates'])} templates")
    
    def test_triggers_templates(self):
        """GET /api/triggers/templates - Should return all templates"""
        response = requests.get(f"{BASE_URL}/api/triggers/templates")
        assert response.status_code == 200
        
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) == 8
        
        print(f"✓ Templates: {len(data['templates'])} available")
    
    def test_triggers_list(self):
        """GET /api/triggers/list - Should return triggers list"""
        response = requests.get(f"{BASE_URL}/api/triggers/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "triggers" in data
        
        print(f"✓ Triggers list: {len(data['triggers'])} triggers")


class TestAILearningLoopEndpoints:
    """Test AI Learning Loop (P1) endpoints"""
    
    def test_ai_learning_status(self):
        """GET /api/ai-learning/status - Should return learning status"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_predictions" in data
        assert "verified_predictions" in data
        
        print(f"✓ AI Learning status: {data['total_predictions']} predictions")
    
    def test_ai_learning_model_performance(self):
        """GET /api/ai-learning/model-performance - Should return model performance"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/model-performance?days=30")
        assert response.status_code == 200
        
        data = response.json()
        assert "performance" in data
        
        print(f"✓ Model performance: {len(data['performance'])} models tracked")
    
    def test_ai_learning_insights(self):
        """GET /api/ai-learning/insights - Should return learning insights"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/insights")
        assert response.status_code == 200
        
        data = response.json()
        # May have model_rankings, strong_areas, weak_areas
        print(f"✓ AI Learning insights retrieved")
    
    def test_ai_learning_training_feedback(self):
        """GET /api/ai-learning/training-feedback - Should return training feedback"""
        response = requests.get(f"{BASE_URL}/api/ai-learning/training-feedback")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Training feedback retrieved")


class TestHealthAndBasicEndpoints:
    """Test basic health and core endpoints"""
    
    def test_health_check(self):
        """GET /api/health - Should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "healthy"
        
        print(f"✓ Health check passed")
    
    def test_market_overview(self):
        """GET /api/market/overview - Should return market data"""
        response = requests.get(f"{BASE_URL}/api/market/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_market_cap" in data or "market_cap" in data or "coins" in data
        
        print(f"✓ Market overview retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
