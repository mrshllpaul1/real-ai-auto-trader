"""
Backend API tests for Notification System
Tests: Push notifications, SMS notifications, notification settings
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNotificationAPIs:
    """Test notification-related API endpoints"""
    
    def test_get_notifications(self):
        """Test GET /api/notifications/ - Get unread notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "count" in data
        assert "notifications" in data
        assert isinstance(data["notifications"], list)
        assert isinstance(data["count"], int)
        print(f"✅ GET /api/notifications/ - Found {data['count']} notifications")
    
    def test_get_notification_settings(self):
        """Test GET /api/notifications/settings - Get notification settings"""
        response = requests.get(f"{BASE_URL}/api/notifications/settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate settings structure
        assert "push_enabled" in data
        assert "sms_enabled" in data
        assert "sms_phone" in data
        assert "notify_trade_open" in data
        assert "notify_trade_close" in data
        assert "notify_high_alerts" in data
        
        # Validate data types
        assert isinstance(data["push_enabled"], bool)
        assert isinstance(data["sms_enabled"], bool)
        assert isinstance(data["sms_phone"], str)
        
        print(f"✅ GET /api/notifications/settings - Settings retrieved successfully")
        print(f"   Push enabled: {data['push_enabled']}, SMS enabled: {data['sms_enabled']}")
    
    def test_update_notification_settings(self):
        """Test POST /api/notifications/settings - Update notification settings"""
        update_payload = {
            "push_enabled": True,
            "sms_enabled": True,
            "notify_high_alerts": True,
            "notify_medium_alerts": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/notifications/settings",
            json=update_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response
        assert "message" in data
        assert "settings" in data
        assert data["settings"]["push_enabled"] == True
        assert data["settings"]["notify_high_alerts"] == True
        
        print(f"✅ POST /api/notifications/settings - Settings updated successfully")
    
    def test_test_push_notification(self):
        """Test POST /api/notifications/test-push - Create test push notification"""
        response = requests.post(f"{BASE_URL}/api/notifications/test-push")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response
        assert "success" in data
        assert data["success"] == True
        assert "notification" in data
        
        notification = data["notification"]
        assert "id" in notification
        assert "title" in notification
        assert "body" in notification
        assert notification["title"] == "Test Notification"
        
        print(f"✅ POST /api/notifications/test-push - Push notification created")
    
    def test_test_sms_notification_without_twilio(self):
        """Test POST /api/notifications/test-sms - SMS without Twilio configured"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/test-sms",
            json={"message": "Test SMS", "phone": "2104412761"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return error since Twilio is not configured
        assert "success" in data
        assert data["success"] == False
        assert "error" in data
        assert "Twilio not configured" in data["error"]
        
        print(f"✅ POST /api/notifications/test-sms - Correctly returns Twilio not configured")
    
    def test_mark_notification_read(self):
        """Test POST /api/notifications/mark-read/{id} - Mark notification as read"""
        # First create a test notification
        create_response = requests.post(f"{BASE_URL}/api/notifications/test-push")
        assert create_response.status_code == 200
        notification_id = create_response.json()["notification"]["id"]
        
        # Mark it as read
        response = requests.post(f"{BASE_URL}/api/notifications/mark-read/{notification_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        print(f"✅ POST /api/notifications/mark-read/{notification_id} - Notification marked as read")
    
    def test_mark_all_notifications_read(self):
        """Test POST /api/notifications/mark-all-read - Mark all notifications as read"""
        response = requests.post(f"{BASE_URL}/api/notifications/mark-all-read")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        print(f"✅ POST /api/notifications/mark-all-read - All notifications marked as read")


class TestAdvancedFeaturesAPIs:
    """Test Advanced Features API endpoints (Backtesting, Rebalancing, Social)"""
    
    def test_backtest_run(self):
        """Test POST /api/backtest/run - Run backtest"""
        payload = {
            "strategy": {
                "min_score": 50,
                "position_size_pct": 10,
                "stop_loss_pct": 10,
                "take_profit_pct": 30,
                "max_positions": 3
            },
            "coins": ["bitcoin", "ethereum"],
            "days": 30,
            "initial_capital": 10000
        }
        
        response = requests.post(f"{BASE_URL}/api/backtest/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate backtest results structure
        assert "total_return_pct" in data or "error" not in data
        print(f"✅ POST /api/backtest/run - Backtest completed")
    
    def test_rebalance_calculate(self):
        """Test GET /api/rebalance/calculate/{user_id} - Calculate rebalance"""
        user_id = "demo_user"
        response = requests.get(f"{BASE_URL}/api/rebalance/calculate/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "total_value" in data or "trades_needed" in data
        print(f"✅ GET /api/rebalance/calculate/{user_id} - Rebalance calculated")
    
    def test_social_leaderboard(self):
        """Test GET /api/social/leaderboard - Get trader leaderboard"""
        response = requests.get(f"{BASE_URL}/api/social/leaderboard?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "traders" in data
        assert isinstance(data["traders"], list)
        print(f"✅ GET /api/social/leaderboard - Found {len(data['traders'])} traders")


class TestCoreAPIs:
    """Test core API endpoints"""
    
    def test_api_root(self):
        """Test GET /api/ - API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "status" in data
        assert data["status"] == "operational"
        print(f"✅ GET /api/ - API is operational")
    
    def test_auth_check_credentials(self):
        """Test GET /api/auth/check-credentials - Check if credentials exist"""
        response = requests.get(f"{BASE_URL}/api/auth/check-credentials")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "has_credentials" in data
        assert isinstance(data["has_credentials"], bool)
        print(f"✅ GET /api/auth/check-credentials - Credentials check: {data['has_credentials']}")
    
    def test_market_prices(self):
        """Test GET /api/market/prices - Get market prices"""
        response = requests.get(f"{BASE_URL}/api/market/prices?coin_ids=bitcoin,ethereum")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return price data
        assert isinstance(data, dict)
        print(f"✅ GET /api/market/prices - Market prices retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
