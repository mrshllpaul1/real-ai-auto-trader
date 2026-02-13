"""
Test Suite for Iteration 45 - Comprehensive Regression Testing:
1. Loading skeletons on major pages (AdvancedOrders, YieldFarming, OptionsTrading, PerpetualFutures, AICommandCenter, etc.)
2. Push notification settings in Settings > Email > Error Alerts tab
3. Error Alerting API endpoints still working after skeleton updates
4. Performance Monitor WebSocket still showing LIVE badge
5. PWA manifest shortcuts (Dashboard, Trading Hub, AI Hub, Performance)
6. Service worker caching strategies
7. Portfolio Dashboard still functional
8. Command Center loading properly
9. Trading page functionality
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic health checks to ensure system is running"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "healthy"
        assert data.get("database") == "connected"
        print(f"✓ Health check passed: status={data['status']}, db={data['database']}")
    
    def test_frontend_accessible(self):
        """Test frontend is accessible"""
        response = requests.get(BASE_URL, timeout=10)
        assert response.status_code == 200
        print("✓ Frontend accessible")


class TestErrorAlertingAPI:
    """Tests for Error Alerting Service endpoints - regression after skeleton updates"""
    
    def test_get_error_alerting_config(self):
        """Test GET /api/error-alerting/config returns config"""
        response = requests.get(f"{BASE_URL}/api/error-alerting/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "enabled" in data
        assert "thresholds" in data
        assert "cooldown_minutes" in data
        assert "has_api_key" in data
        assert "recipient_emails" in data
        
        thresholds = data.get("thresholds", {})
        assert "errors_per_hour" in thresholds
        assert "critical_errors_trigger" in thresholds
        
        print(f"✓ Error alerting config: enabled={data['enabled']}, has_api_key={data['has_api_key']}")
    
    def test_get_error_alerting_status(self):
        """Test GET /api/error-alerting/status returns service status"""
        response = requests.get(f"{BASE_URL}/api/error-alerting/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "initialized" in data
        assert "enabled" in data
        assert "has_api_key" in data
        assert "recipient_count" in data
        assert "thresholds" in data
        assert data["initialized"] == True
        
        print(f"✓ Error alerting status: initialized={data['initialized']}, enabled={data['enabled']}")
    
    def test_check_thresholds(self):
        """Test GET /api/error-alerting/check-thresholds"""
        response = requests.get(f"{BASE_URL}/api/error-alerting/check-thresholds")
        assert response.status_code == 200
        
        data = response.json()
        assert "triggered" in data
        print(f"✓ Threshold check: triggered={data['triggered']}")
    
    def test_get_alert_history(self):
        """Test GET /api/error-alerting/history"""
        response = requests.get(f"{BASE_URL}/api/error-alerting/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "count" in data
        assert isinstance(data["alerts"], list)
        
        print(f"✓ Alert history: {data['count']} alerts")


class TestPerformanceMonitorAPI:
    """Tests for Performance Monitor endpoints"""
    
    def test_perf_monitor_summary(self):
        """Test GET /api/perf-monitor/summary returns metrics"""
        response = requests.get(f"{BASE_URL}/api/perf-monitor/summary")
        assert response.status_code == 200
        
        data = response.json()
        # Verify key metrics exist
        expected_fields = ["avg_response_time", "requests_per_minute", "error_rate", "uptime"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Perf monitor summary: avg_response={data.get('avg_response_time', 'N/A')}ms, uptime={data.get('uptime', 'N/A')}")
    
    def test_perf_monitor_cache_stats(self):
        """Test GET /api/perf-monitor/cache-stats"""
        response = requests.get(f"{BASE_URL}/api/perf-monitor/cache-stats")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Cache stats retrieved")
    
    def test_perf_monitor_db_stats(self):
        """Test GET /api/perf-monitor/db-stats"""
        response = requests.get(f"{BASE_URL}/api/perf-monitor/db-stats")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ DB stats retrieved")


class TestPWAManifest:
    """Tests for PWA manifest and service worker"""
    
    def test_manifest_json_accessible(self):
        """Test manifest.json is accessible and has correct structure"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("short_name") == "Tethys AI"
        assert data.get("name") == "Tethys AI - Crypto Trading Platform"
        assert "icons" in data
        assert "shortcuts" in data
        
        # Verify shortcuts
        shortcuts = data.get("shortcuts", [])
        assert len(shortcuts) >= 4, f"Expected at least 4 shortcuts, got {len(shortcuts)}"
        
        shortcut_names = [s.get("name") for s in shortcuts]
        expected_shortcuts = ["Dashboard", "Trading Hub", "AI Hub", "Performance"]
        for expected in expected_shortcuts:
            assert expected in shortcut_names, f"Missing shortcut: {expected}"
        
        print(f"✓ PWA manifest valid: {len(shortcuts)} shortcuts configured")
    
    def test_service_worker_accessible(self):
        """Test service-worker.js is accessible"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        assert response.status_code == 200
        assert "self.addEventListener" in response.text
        print("✓ Service worker accessible")


class TestPortfolioAndDashboard:
    """Tests for Portfolio and Dashboard functionality"""
    
    def test_portfolio_summary(self):
        """Test GET /api/portfolio/visualization/summary"""
        response = requests.get(f"{BASE_URL}/api/portfolio/visualization/summary")
        assert response.status_code == 200
        
        data = response.json()
        # Portfolio may not be initialized - that's OK
        print(f"✓ Portfolio summary endpoint accessible: {data.get('message', 'data retrieved')}")
    
    def test_kraken_balance(self):
        """Test GET /api/kraken/balance - main portfolio endpoint"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert "balances" in data
        print(f"✓ Kraken balance retrieved: {data.get('total_currencies', 0)} currencies")
    
    def test_command_center_data(self):
        """Test GET /api/command-center/data - command center data"""
        response = requests.get(f"{BASE_URL}/api/command-center/data")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Command center data retrieved")


class TestAIEndpoints:
    """Tests for AI-related endpoints"""
    
    def test_enhanced_ai_status(self):
        """Test GET /api/enhanced-ai/status"""
        response = requests.get(f"{BASE_URL}/api/enhanced-ai/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Enhanced AI status retrieved")
    
    def test_tethys_train_status(self):
        """Test GET /api/tethys-train/status"""
        response = requests.get(f"{BASE_URL}/api/tethys-train/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Tethys train status retrieved")
    
    def test_learning_status(self):
        """Test GET /api/learning/status"""
        response = requests.get(f"{BASE_URL}/api/learning/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Learning status retrieved")


class TestTradingEndpoints:
    """Tests for Trading-related endpoints"""
    
    def test_advanced_orders_endpoint(self):
        """Test GET /api/advanced-orders/orders"""
        response = requests.get(f"{BASE_URL}/api/advanced-orders/orders")
        # May return 200 or 404 if no orders
        assert response.status_code in [200, 404]
        print(f"✓ Advanced orders endpoint: status={response.status_code}")
    
    def test_auto_exec_status(self):
        """Test GET /api/auto-exec/status - auto execution status"""
        response = requests.get(f"{BASE_URL}/api/auto-exec/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Auto execution status retrieved")
    
    def test_scanner_status(self):
        """Test GET /api/scanner/status - gem scanner status"""
        response = requests.get(f"{BASE_URL}/api/scanner/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Scanner status retrieved")
    
    def test_triggers_status(self):
        """Test GET /api/triggers/status - event triggers status"""
        response = requests.get(f"{BASE_URL}/api/triggers/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_triggers" in data
        print(f"✓ Triggers status retrieved: {data.get('total_triggers', 0)} triggers")


class TestEmailDigestEndpoints:
    """Tests for Email Digest and Push Notification settings"""
    
    def test_email_digest_settings(self):
        """Test GET /api/email-digest/settings"""
        response = requests.get(f"{BASE_URL}/api/email-digest/settings")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Email digest settings retrieved")
    
    def test_email_digest_history(self):
        """Test GET /api/email-digest/history"""
        response = requests.get(f"{BASE_URL}/api/email-digest/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "digests" in data
        print(f"✓ Email digest history retrieved")


class TestTriggerPerformance:
    """Tests for Trigger Performance endpoints"""
    
    def test_triggers_status(self):
        """Test GET /api/triggers/status"""
        response = requests.get(f"{BASE_URL}/api/triggers/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_triggers" in data
        print(f"✓ Triggers status retrieved")
    
    def test_notifications_endpoint(self):
        """Test GET /api/notifications/ - notifications list"""
        response = requests.get(f"{BASE_URL}/api/notifications/")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Notifications endpoint accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
