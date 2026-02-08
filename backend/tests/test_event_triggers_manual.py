"""
Test Event Triggers - Manual Event and Templates
Tests for the new event trigger features including:
- 20 trigger templates (including new ones like blackrock_tokenization, trump_crypto, etc.)
- Manual event submission endpoint
- Ensemble AI rebuild endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestEventTriggerTemplates:
    """Test event trigger templates - should have 20 templates"""
    
    def test_templates_endpoint_returns_20_templates(self):
        """Verify /api/triggers/templates returns 20 templates"""
        response = requests.get(f"{BASE_URL}/api/triggers/templates")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "templates" in data
        assert data["count"] == 20, f"Expected 20 templates, got {data['count']}"
        
        # Verify template structure
        templates = data["templates"]
        assert isinstance(templates, dict)
        assert len(templates) == 20
    
    def test_new_templates_exist(self):
        """Verify new templates are present"""
        response = requests.get(f"{BASE_URL}/api/triggers/templates")
        assert response.status_code == 200
        
        templates = response.json()["templates"]
        
        # New templates that should exist
        new_templates = [
            "blackrock_tokenization",
            "fed_rate_decision", 
            "major_partnership",
            "trump_crypto",
            "defi_exploit",
            "stablecoin_depeg",
            "sovereign_adoption",
            "grayscale_flows",
            "ai_crypto",
            "layer2_launch",
            "halving_event",
            "protocol_upgrade"
        ]
        
        for template_name in new_templates:
            assert template_name in templates, f"Missing template: {template_name}"
            
            # Verify template has required fields
            template = templates[template_name]
            assert "name" in template
            assert "keywords" in template
            assert "coins" in template
            assert "action" in template
            assert "description" in template
    
    def test_blackrock_tokenization_template_details(self):
        """Verify blackrock_tokenization template has correct details"""
        response = requests.get(f"{BASE_URL}/api/triggers/templates")
        assert response.status_code == 200
        
        template = response.json()["templates"]["blackrock_tokenization"]
        
        assert template["name"] == "BlackRock Tokenization News"
        assert "blackrock" in template["keywords"]
        assert "tokenize" in template["keywords"] or "tokenization" in template["keywords"]
        assert "ETH" in template["coins"]
        assert template["action"] == "buy"
        assert template["sentiment_filter"] == "positive"


class TestManualEventEndpoint:
    """Test manual event submission endpoint"""
    
    def test_manual_event_endpoint_exists(self):
        """Verify POST /api/triggers/manual-event endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/triggers/manual-event",
            json={
                "title": "Test event",
                "body": "Test body",
                "sentiment": "NEUTRAL"
            }
        )
        # Should return 200, not 404 or 405
        assert response.status_code == 200
    
    def test_manual_event_processes_correctly(self):
        """Test manual event is processed against triggers"""
        response = requests.post(
            f"{BASE_URL}/api/triggers/manual-event",
            json={
                "title": "BlackRock begins tokenizing its assets on Ethereum",
                "body": "BlackRock announced today that they will tokenize $10B worth of assets",
                "sentiment": "POSITIVE",
                "source": "test"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processed"
        assert "event" in data
        assert "triggers_checked" in data
        assert "triggers_matched" in data
        assert "matched_triggers" in data
        assert "executions" in data
        
        # Verify event data was captured
        event = data["event"]
        assert event["title"] == "BlackRock begins tokenizing its assets on Ethereum"
        assert event["sentiment"] == "POSITIVE"
        assert event["source"] == "test"
    
    def test_manual_event_requires_title(self):
        """Test that title is required for manual event"""
        response = requests.post(
            f"{BASE_URL}/api/triggers/manual-event",
            json={
                "body": "Test body without title",
                "sentiment": "NEUTRAL"
            }
        )
        # Should fail validation
        assert response.status_code == 422  # Validation error


class TestEnsembleAIEndpoints:
    """Test Ensemble AI endpoints"""
    
    def test_ensemble_status_endpoint(self):
        """Verify /api/ensemble/status returns correct data"""
        response = requests.get(f"{BASE_URL}/api/ensemble/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "ensemble_initialized" in data
        assert "model_weights" in data
        assert "universe_rebuild_status" in data
    
    def test_ensemble_rebuild_endpoint(self):
        """Verify POST /api/ensemble/rebuild-universe works"""
        response = requests.post(
            f"{BASE_URL}/api/ensemble/rebuild-universe",
            json={
                "target_size": 50,
                "analyze_count": 100
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should either start or report already running
        assert data["status"] in ["started", "already_running"]
    
    def test_ensemble_build_status_endpoint(self):
        """Verify /api/ensemble/build-status returns progress"""
        response = requests.get(f"{BASE_URL}/api/ensemble/build-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "progress" in data
    
    def test_ensemble_optimal_universe_endpoint(self):
        """Verify /api/ensemble/optimal-universe returns data"""
        response = requests.get(f"{BASE_URL}/api/ensemble/optimal-universe")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data or "coins" in data or "top_10" in data


class TestTriggerServiceStatus:
    """Test trigger service status endpoint"""
    
    def test_trigger_status_shows_templates_count(self):
        """Verify trigger status shows available templates"""
        response = requests.get(f"{BASE_URL}/api/triggers/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "available_templates" in data
        assert len(data["available_templates"]) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
