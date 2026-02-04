"""
Event Triggers API Tests
Tests for custom event triggers for automated trading based on news events.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestEventTriggerStatus:
    """Tests for trigger service status endpoint"""
    
    def test_get_trigger_status(self):
        """GET /api/triggers/status - Get event trigger service status"""
        response = requests.get(f"{BASE_URL}/api/triggers/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_triggers" in data
        assert "enabled_triggers" in data
        assert "total_executions" in data
        assert "successful_executions" in data
        assert "success_rate" in data
        assert "available_templates" in data
        assert isinstance(data["available_templates"], list)
        assert len(data["available_templates"]) == 8  # 8 templates expected


class TestEventTriggerTemplates:
    """Tests for trigger templates endpoint"""
    
    def test_get_templates(self):
        """GET /api/triggers/templates - Get available trigger templates"""
        response = requests.get(f"{BASE_URL}/api/triggers/templates")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert data["count"] == 8
        assert "templates" in data
        
        # Verify all expected templates exist
        expected_templates = [
            "elon_doge", "elon_btc", "sec_regulatory", "etf_approval",
            "exchange_hack", "china_ban", "institutional_buy", "whale_alert"
        ]
        for template in expected_templates:
            assert template in data["templates"]
            assert "name" in data["templates"][template]
            assert "keywords" in data["templates"][template]
            assert "coins" in data["templates"][template]
            assert "action" in data["templates"][template]
            assert "description" in data["templates"][template]


class TestEventTriggerCRUD:
    """Tests for trigger CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        self.test_trigger_id = f"TEST_trigger_{int(time.time())}"
        yield
        # Cleanup: Delete test trigger if it exists
        requests.delete(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
    
    def test_create_custom_trigger(self):
        """POST /api/triggers/create - Create custom trigger"""
        payload = {
            "trigger_id": self.test_trigger_id,
            "name": "Test Custom Trigger",
            "keywords": ["bitcoin", "btc", "test"],
            "coins": ["BTC"],
            "action": "alert",
            "sentiment_filter": "any",
            "cooldown_hours": 6,
            "enabled": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/triggers/create",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "created"
        assert "trigger" in data
        assert data["trigger"]["trigger_id"] == self.test_trigger_id
        assert data["trigger"]["name"] == "Test Custom Trigger"
        assert data["trigger"]["action"] == "alert"
        
        # Verify trigger was persisted - GET to confirm
        get_response = requests.get(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["trigger_id"] == self.test_trigger_id
    
    def test_create_trigger_from_template(self):
        """POST /api/triggers/create-from-template - Create trigger from template"""
        payload = {
            "template_name": "whale_alert",
            "trigger_id": self.test_trigger_id,
            "amount_usd": 100,
            "enabled": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/triggers/create-from-template",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "created"
        assert data["trigger"]["trigger_id"] == self.test_trigger_id
        assert data["trigger"]["name"] == "Whale Movement Alert"  # From template
        assert data["trigger"]["amount_usd"] == 100
        
        # Verify trigger was persisted
        get_response = requests.get(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
        assert get_response.status_code == 200
    
    def test_create_trigger_invalid_template(self):
        """POST /api/triggers/create-from-template - Invalid template returns 400"""
        payload = {
            "template_name": "invalid_template",
            "trigger_id": self.test_trigger_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/triggers/create-from-template",
            json=payload
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_duplicate_trigger(self):
        """POST /api/triggers/create - Duplicate trigger returns 400"""
        # First create
        payload = {
            "trigger_id": self.test_trigger_id,
            "name": "Test Trigger",
            "keywords": ["test"],
            "coins": ["BTC"],
            "action": "alert"
        }
        requests.post(f"{BASE_URL}/api/triggers/create", json=payload)
        
        # Try to create duplicate
        response = requests.post(f"{BASE_URL}/api/triggers/create", json=payload)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_get_trigger(self):
        """GET /api/triggers/{trigger_id} - Get specific trigger"""
        # Create trigger first
        payload = {
            "trigger_id": self.test_trigger_id,
            "name": "Test Get Trigger",
            "keywords": ["test"],
            "coins": ["BTC"],
            "action": "alert"
        }
        requests.post(f"{BASE_URL}/api/triggers/create", json=payload)
        
        # Get trigger
        response = requests.get(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["trigger_id"] == self.test_trigger_id
        assert data["name"] == "Test Get Trigger"
    
    def test_get_nonexistent_trigger(self):
        """GET /api/triggers/{trigger_id} - Non-existent trigger returns 404"""
        response = requests.get(f"{BASE_URL}/api/triggers/nonexistent_trigger_xyz")
        assert response.status_code == 404
    
    def test_update_trigger(self):
        """PUT /api/triggers/{trigger_id} - Update trigger"""
        # Create trigger first
        payload = {
            "trigger_id": self.test_trigger_id,
            "name": "Original Name",
            "keywords": ["test"],
            "coins": ["BTC"],
            "action": "alert",
            "cooldown_hours": 6
        }
        requests.post(f"{BASE_URL}/api/triggers/create", json=payload)
        
        # Update trigger
        update_payload = {
            "name": "Updated Name",
            "cooldown_hours": 12
        }
        response = requests.put(
            f"{BASE_URL}/api/triggers/{self.test_trigger_id}",
            json=update_payload
        )
        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        
        # Verify update was persisted
        get_response = requests.get(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "Updated Name"
        assert data["cooldown_hours"] == 12
    
    def test_update_nonexistent_trigger(self):
        """PUT /api/triggers/{trigger_id} - Update non-existent trigger returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/triggers/nonexistent_trigger_xyz",
            json={"name": "Test"}
        )
        assert response.status_code == 404
    
    def test_delete_trigger(self):
        """DELETE /api/triggers/{trigger_id} - Delete trigger"""
        # Create trigger first
        payload = {
            "trigger_id": self.test_trigger_id,
            "name": "To Be Deleted",
            "keywords": ["test"],
            "coins": ["BTC"],
            "action": "alert"
        }
        requests.post(f"{BASE_URL}/api/triggers/create", json=payload)
        
        # Delete trigger
        response = requests.delete(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_trigger(self):
        """DELETE /api/triggers/{trigger_id} - Delete non-existent trigger returns 404"""
        response = requests.delete(f"{BASE_URL}/api/triggers/nonexistent_trigger_xyz")
        assert response.status_code == 404


class TestEventTriggerEnableDisable:
    """Tests for trigger enable/disable operations"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        self.test_trigger_id = f"TEST_enable_disable_{int(time.time())}"
        # Create test trigger
        payload = {
            "trigger_id": self.test_trigger_id,
            "name": "Enable/Disable Test",
            "keywords": ["test"],
            "coins": ["BTC"],
            "action": "alert",
            "enabled": True
        }
        requests.post(f"{BASE_URL}/api/triggers/create", json=payload)
        yield
        # Cleanup
        requests.delete(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
    
    def test_disable_trigger(self):
        """POST /api/triggers/{trigger_id}/disable - Disable trigger"""
        response = requests.post(f"{BASE_URL}/api/triggers/{self.test_trigger_id}/disable")
        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        
        # Verify disabled
        get_response = requests.get(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
        assert get_response.json()["enabled"] == False
    
    def test_enable_trigger(self):
        """POST /api/triggers/{trigger_id}/enable - Enable trigger"""
        # First disable
        requests.post(f"{BASE_URL}/api/triggers/{self.test_trigger_id}/disable")
        
        # Then enable
        response = requests.post(f"{BASE_URL}/api/triggers/{self.test_trigger_id}/enable")
        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        
        # Verify enabled
        get_response = requests.get(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
        assert get_response.json()["enabled"] == True


class TestEventTriggerList:
    """Tests for trigger list endpoint"""
    
    def test_list_all_triggers(self):
        """GET /api/triggers/list - List all triggers"""
        response = requests.get(f"{BASE_URL}/api/triggers/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "triggers" in data
        assert isinstance(data["triggers"], list)
    
    def test_list_enabled_only(self):
        """GET /api/triggers/list?enabled_only=true - List only enabled triggers"""
        response = requests.get(f"{BASE_URL}/api/triggers/list?enabled_only=true")
        assert response.status_code == 200
        
        data = response.json()
        # All returned triggers should be enabled
        for trigger in data["triggers"]:
            assert trigger["enabled"] == True


class TestEventTriggerCheckNow:
    """Tests for manual trigger checking"""
    
    def test_check_now(self):
        """POST /api/triggers/check-now - Manually check events against triggers"""
        response = requests.post(f"{BASE_URL}/api/triggers/check-now")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "checked"
        assert "triggers_executed" in data
        assert "executions" in data
        assert isinstance(data["executions"], list)


class TestEventTriggerHistory:
    """Tests for trigger execution history"""
    
    def test_get_all_history(self):
        """GET /api/triggers/history/all - Get all execution history"""
        response = requests.get(f"{BASE_URL}/api/triggers/history/all")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "history" in data
        assert isinstance(data["history"], list)
        
        # Verify history entry structure if any exist
        if data["history"]:
            entry = data["history"][0]
            assert "trigger_id" in entry
            assert "trigger_name" in entry
            assert "action" in entry
            assert "executed_at" in entry
            assert "success" in entry
    
    def test_get_trigger_specific_history(self):
        """GET /api/triggers/history/{trigger_id} - Get history for specific trigger"""
        # Use existing trigger
        response = requests.get(f"{BASE_URL}/api/triggers/history/test_elon_doge_1")
        assert response.status_code == 200
        
        data = response.json()
        assert "trigger_id" in data
        assert data["trigger_id"] == "test_elon_doge_1"
        assert "count" in data
        assert "history" in data


class TestSchedulerEventTriggerJobs:
    """Tests for scheduler event trigger job endpoints"""
    
    def test_add_event_trigger_check_job(self):
        """POST /api/scheduler/jobs/event-trigger-check - Schedule periodic trigger checking"""
        payload = {"interval_minutes": 15}
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/event-trigger-check",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["job_id"] == "event_trigger_check"
        assert data["interval_minutes"] == 15
        assert "message" in data
    
    def test_run_event_trigger_check_now(self):
        """POST /api/scheduler/jobs/event-trigger-check-now - Manually run trigger check via scheduler"""
        response = requests.post(f"{BASE_URL}/api/scheduler/jobs/event-trigger-check-now")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "triggers_matched" in data
        assert "executions" in data


class TestEventTriggerDataValidation:
    """Tests for data validation in trigger operations"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        self.test_trigger_id = f"TEST_validation_{int(time.time())}"
        yield
        # Cleanup
        requests.delete(f"{BASE_URL}/api/triggers/{self.test_trigger_id}")
    
    def test_create_trigger_with_all_fields(self):
        """Create trigger with all optional fields"""
        payload = {
            "trigger_id": self.test_trigger_id,
            "name": "Full Trigger",
            "keywords": ["bitcoin", "btc", "crypto"],
            "coins": ["BTC", "ETH"],
            "action": "buy",
            "amount_usd": 100.0,
            "amount_pct": 10.0,
            "sentiment_filter": "positive",
            "category_filter": "regulatory",
            "cooldown_hours": 24,
            "enabled": True
        }
        
        response = requests.post(f"{BASE_URL}/api/triggers/create", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        trigger = data["trigger"]
        assert trigger["amount_usd"] == 100.0
        assert trigger["amount_pct"] == 10.0
        assert trigger["sentiment_filter"] == "positive"
        assert trigger["category_filter"] == "regulatory"
        assert trigger["cooldown_hours"] == 24
    
    def test_create_trigger_minimal_fields(self):
        """Create trigger with only required fields"""
        payload = {
            "trigger_id": self.test_trigger_id,
            "name": "Minimal Trigger",
            "keywords": ["test"],
            "coins": ["BTC"],
            "action": "alert"
        }
        
        response = requests.post(f"{BASE_URL}/api/triggers/create", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        trigger = data["trigger"]
        assert trigger["amount_usd"] is None
        assert trigger["amount_pct"] is None
        assert trigger["cooldown_hours"] == 24  # Default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
