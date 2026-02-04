"""
Test Auto-Spot Scan Real Trading Mode
Tests the new UI features and real trading mode switch
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAutoSpotRealMode:
    """Test Auto-Spot Scan in Real Trading Mode"""
    
    def test_auto_spot_status_returns_paper_trade_false(self):
        """Test that /api/training-scheduler/auto-spot-scan/status returns paper_trade=false"""
        response = requests.get(f"{BASE_URL}/api/training-scheduler/auto-spot-scan/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"Auto-spot status response: {data}")
        
        # Verify paper_trade is false (REAL mode)
        assert "paper_trade" in data, "Response should contain paper_trade field"
        assert data["paper_trade"] == False, f"Expected paper_trade=false, got {data['paper_trade']}"
        
        # Verify other required fields
        assert "enabled" in data, "Response should contain enabled field"
        assert "schedule_id" in data, "Response should contain schedule_id field"
        assert "interval_minutes" in data, "Response should contain interval_minutes field"
        
        print(f"✅ paper_trade={data['paper_trade']} (REAL mode confirmed)")
        print(f"✅ enabled={data['enabled']}")
        print(f"✅ interval_minutes={data['interval_minutes']}")
    
    def test_auto_spot_status_shows_active(self):
        """Test that auto-spot scan is enabled/active"""
        response = requests.get(f"{BASE_URL}/api/training-scheduler/auto-spot-scan/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("enabled") == True, f"Expected enabled=true, got {data.get('enabled')}"
        print(f"✅ Auto-spot scan is ACTIVE (enabled={data['enabled']})")
    
    def test_auto_spot_run_now_endpoint_exists(self):
        """Test that run-now endpoint is accessible"""
        # Just test the endpoint exists - don't actually run a scan
        response = requests.post(
            f"{BASE_URL}/api/training-scheduler/auto-spot-scan/run-now",
            params={"paper_trade": True}  # Use paper trade for safety
        )
        
        # Should return 200 or 503 (if trader not initialized)
        assert response.status_code in [200, 503], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scan Now endpoint working - returned {len(str(data))} bytes")
            
            # Verify response structure
            assert "timestamp" in data or "scanned_symbols" in data or "error" not in data
        else:
            print(f"⚠️ Scan Now returned 503 - trader may not be initialized")
    
    def test_auto_spot_toggle_endpoint_exists(self):
        """Test that toggle endpoint is accessible"""
        # Get current status first
        status_response = requests.get(f"{BASE_URL}/api/training-scheduler/auto-spot-scan/status")
        current_enabled = status_response.json().get("enabled", True)
        
        # Toggle endpoint should work
        response = requests.post(
            f"{BASE_URL}/api/training-scheduler/auto-spot-scan/toggle",
            params={"enabled": current_enabled}  # Keep same state
        )
        
        assert response.status_code == 200, f"Toggle endpoint failed: {response.status_code}"
        print(f"✅ Toggle endpoint working")
    
    def test_training_dashboard_api_health(self):
        """Test that all training dashboard APIs are healthy"""
        endpoints = [
            "/api/training-scheduler/",
            "/api/training-scheduler/presets/list",
            "/api/predictions/status",
            "/api/learning/status",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 200, f"{endpoint} failed with {response.status_code}"
            print(f"✅ {endpoint} - OK")


class TestAutoSpotUIComponents:
    """Test UI component data requirements"""
    
    def test_status_response_has_ui_fields(self):
        """Test that status response has all fields needed by UI"""
        response = requests.get(f"{BASE_URL}/api/training-scheduler/auto-spot-scan/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Fields required by TrainingDashboard.js
        required_fields = [
            "enabled",
            "schedule_id", 
            "interval_minutes",
            "paper_trade",
            "run_count"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required UI field: {field}"
            print(f"✅ {field}: {data[field]}")
        
        # Optional fields that UI handles gracefully
        optional_fields = ["last_run", "next_run", "last_result"]
        for field in optional_fields:
            if field in data:
                print(f"  {field}: {data[field]}")
    
    def test_predictions_status_for_service_badges(self):
        """Test predictions status for service badges in UI"""
        response = requests.get(f"{BASE_URL}/api/predictions/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "services" in data, "Response should contain services"
        services = data["services"]
        
        # Services shown in UI
        expected_services = [
            "order_book_analyzer",
            "on_chain_analytics", 
            "social_sentiment",
            "transformer_predictor",
            "rl_trading_agent",
            "cross_asset_correlation",
            "advanced_technical_analysis"
        ]
        
        for service in expected_services:
            if service in services:
                print(f"✅ {service}: {services[service]}")
            else:
                print(f"⚠️ {service}: not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
