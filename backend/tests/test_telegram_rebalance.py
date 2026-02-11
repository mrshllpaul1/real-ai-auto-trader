"""
Test Suite for Telegram Notifications and Portfolio Rebalancing APIs
=====================================================================
Tests for P1 features: Telegram Notifications and Portfolio Rebalancing
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fast-analyzer.preview.emergentagent.com').rstrip('/')


class TestTelegramNotifications:
    """Telegram Notifications API Tests"""
    
    def test_telegram_status(self):
        """Test GET /api/telegram/status - Get Telegram integration status"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "bot_configured" in data
        assert "user_configured" in data
        assert "enabled" in data
        assert "chat_id" in data
        assert "alert_types" in data
        
        # Bot token not configured is expected behavior
        assert isinstance(data["bot_configured"], bool)
        print(f"✓ Telegram status: bot_configured={data['bot_configured']}, user_configured={data['user_configured']}")
    
    def test_telegram_config_get(self):
        """Test GET /api/telegram/config - Get Telegram configuration"""
        response = requests.get(f"{BASE_URL}/api/telegram/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "config" in data
        print(f"✓ Telegram config: configured={data['configured']}")
    
    def test_telegram_config_save(self):
        """Test POST /api/telegram/config - Save Telegram configuration"""
        test_chat_id = f"TEST_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/telegram/config",
            json={
                "chat_id": test_chat_id,
                "enabled": True,
                "alert_types": ["trade", "price", "risk", "portfolio"]
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "config" in data
        assert data["config"]["chat_id"] == test_chat_id
        assert data["config"]["enabled"] == True
        assert "trade" in data["config"]["alert_types"]
        print(f"✓ Telegram config saved with chat_id={test_chat_id}")
    
    def test_telegram_price_alerts_get(self):
        """Test GET /api/telegram/price-alerts - Get price alerts"""
        response = requests.get(f"{BASE_URL}/api/telegram/price-alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        assert isinstance(data["alerts"], list)
        print(f"✓ Price alerts: total={data['total']}")
    
    def test_telegram_price_alert_create(self):
        """Test POST /api/telegram/price-alert/create - Create price alert"""
        response = requests.post(
            f"{BASE_URL}/api/telegram/price-alert/create",
            json={
                "symbol": "BTC/USD",
                "target_price": 100000,
                "direction": "above",
                "chat_id": "TEST_123456"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "created"
        assert "alert" in data
        assert data["alert"]["symbol"] == "BTC/USD"
        assert data["alert"]["target_price"] == 100000
        assert data["alert"]["direction"] == "above"
        assert "alert_id" in data["alert"]
        print(f"✓ Price alert created: {data['alert']['alert_id']}")
        
        return data["alert"]["alert_id"]
    
    def test_telegram_price_alert_delete(self):
        """Test DELETE /api/telegram/price-alert/{alert_id} - Delete price alert"""
        # First create an alert
        create_response = requests.post(
            f"{BASE_URL}/api/telegram/price-alert/create",
            json={
                "symbol": "ETH/USD",
                "target_price": 5000,
                "direction": "below",
                "chat_id": "TEST_DELETE"
            }
        )
        assert create_response.status_code == 200
        alert_id = create_response.json()["alert"]["alert_id"]
        
        # Then delete it
        delete_response = requests.delete(f"{BASE_URL}/api/telegram/price-alert/{alert_id}")
        assert delete_response.status_code == 200
        
        data = delete_response.json()
        assert data["status"] == "deleted"
        print(f"✓ Price alert deleted: {alert_id}")
    
    def test_telegram_history(self):
        """Test GET /api/telegram/history - Get notification history"""
        response = requests.get(f"{BASE_URL}/api/telegram/history?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "messages" in data
        assert "total" in data
        print(f"✓ Notification history: total={data['total']}")


class TestPortfolioRebalancing:
    """Portfolio Rebalancing API Tests"""
    
    def test_rebalance_analyze(self):
        """Test GET /api/rebalance/analyze - Analyze current portfolio"""
        response = requests.get(f"{BASE_URL}/api/rebalance/analyze")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_allocation" in data
        assert "total_value" in data
        assert "holdings_detail" in data
        assert "metrics" in data
        
        # Verify metrics structure
        metrics = data["metrics"]
        assert "num_assets" in metrics
        assert "concentration_risk" in metrics
        assert "max_allocation" in metrics
        assert "diversification_score" in metrics
        
        print(f"✓ Portfolio analysis: total_value=${data['total_value']}, assets={metrics['num_assets']}")
    
    def test_rebalance_suggest(self):
        """Test POST /api/rebalance/suggest - Get AI rebalancing suggestions"""
        response = requests.post(
            f"{BASE_URL}/api/rebalance/suggest",
            json={"risk_based": True}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "current_allocation" in data
        assert "target_allocation" in data
        assert "suggested_trades" in data
        assert "summary" in data
        assert "portfolio_value" in data
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_trades" in summary
        assert "total_volume" in summary
        assert "estimated_fees" in summary
        assert "risk_impact" in summary
        
        print(f"✓ Rebalance suggestions: {summary['total_trades']} trades, volume=${summary['total_volume']}")
    
    def test_rebalance_suggest_with_target(self):
        """Test POST /api/rebalance/suggest with risk_based=false (uses default allocation)"""
        response = requests.post(
            f"{BASE_URL}/api/rebalance/suggest?risk_based=false"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "suggested_trades" in data
        assert "target_allocation" in data
        print(f"✓ Custom rebalance suggestions generated with default allocation")
    
    def test_rebalance_templates(self):
        """Test GET /api/rebalance/templates - Get allocation templates"""
        response = requests.get(f"{BASE_URL}/api/rebalance/templates")
        assert response.status_code == 200
        
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        assert len(data["templates"]) > 0
        
        # Verify template structure
        template = data["templates"][0]
        assert "name" in template
        assert "description" in template
        assert "allocation" in template
        assert "risk_level" in template
        
        template_names = [t["name"] for t in data["templates"]]
        assert "Conservative" in template_names
        assert "Balanced" in template_names
        assert "Growth" in template_names
        
        print(f"✓ Rebalance templates: {len(data['templates'])} templates available")
    
    def test_rebalance_drift(self):
        """Test GET /api/rebalance/drift - Check portfolio drift"""
        response = requests.get(f"{BASE_URL}/api/rebalance/drift")
        assert response.status_code == 200
        
        data = response.json()
        assert "has_target" in data
        assert "needs_rebalancing" in data
        
        print(f"✓ Portfolio drift: has_target={data['has_target']}, needs_rebalancing={data['needs_rebalancing']}")
    
    def test_rebalance_config_save(self):
        """Test POST /api/rebalance/config - Save rebalancing configuration"""
        response = requests.post(
            f"{BASE_URL}/api/rebalance/config",
            json={
                "target_allocation": {"BTC": 50, "ETH": 30, "USDC": 20},
                "rebalance_threshold": 5.0,
                "min_trade_size": 50.0,
                "max_slippage_pct": 0.5,
                "auto_execute": False
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "saved"
        assert "config" in data
        print(f"✓ Rebalance config saved")
    
    def test_rebalance_config_get(self):
        """Test GET /api/rebalance/config - Get rebalancing configuration"""
        response = requests.get(f"{BASE_URL}/api/rebalance/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "config" in data
        print(f"✓ Rebalance config: configured={data['configured']}")
    
    def test_rebalance_history(self):
        """Test GET /api/rebalance/history - Get rebalancing history"""
        response = requests.get(f"{BASE_URL}/api/rebalance/history?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "history" in data
        assert "total" in data
        print(f"✓ Rebalance history: total={data['total']}")


class TestRiskAnalyzer:
    """Risk Analyzer API Tests"""
    
    def test_risk_overview(self):
        """Test GET /api/risk-analyzer/overview - Get risk overview"""
        response = requests.get(f"{BASE_URL}/api/risk-analyzer/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_risk_score" in data
        assert "risk_level" in data
        assert "total_portfolio_value" in data
        assert "risk_breakdown" in data
        assert "risk_factors" in data
        assert "recommendations" in data
        
        # Verify risk breakdown structure
        breakdown = data["risk_breakdown"]
        assert "perpetuals" in breakdown
        assert "yield_farming" in breakdown
        assert "options" in breakdown
        
        print(f"✓ Risk overview: score={data['overall_risk_score']}, level={data['risk_level']}")
    
    def test_risk_stress_test(self):
        """Test POST /api/risk-analyzer/stress-test - Run stress test"""
        response = requests.post(f"{BASE_URL}/api/risk-analyzer/stress-test?scenario=market_crash")
        assert response.status_code == 200
        
        data = response.json()
        assert "scenario" in data
        assert "scenario_params" in data
        assert "current_portfolio_value" in data
        assert "projected_portfolio_value" in data
        assert "total_impact" in data
        assert "impact_breakdown" in data
        assert "liquidations_triggered" in data
        assert "survival" in data
        
        print(f"✓ Stress test (market_crash): impact=${data['total_impact']}, survival={data['survival']}")
    
    def test_risk_stress_test_scenarios(self):
        """Test different stress test scenarios"""
        scenarios = ["market_crash", "flash_crash", "bull_run", "black_swan"]
        
        for scenario in scenarios:
            response = requests.post(f"{BASE_URL}/api/risk-analyzer/stress-test?scenario={scenario}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["scenario"] == scenario
            print(f"✓ Stress test ({scenario}): impact=${data['total_impact']}")
    
    def test_risk_exposure(self):
        """Test GET /api/risk-analyzer/exposure - Get exposure breakdown"""
        response = requests.get(f"{BASE_URL}/api/risk-analyzer/exposure")
        assert response.status_code == 200
        
        data = response.json()
        assert "by_asset" in data
        assert "by_type" in data
        assert "total_exposure" in data
        assert "concentration" in data
        
        print(f"✓ Risk exposure: total=${data['total_exposure']}")
    
    def test_risk_var(self):
        """Test GET /api/risk-analyzer/var - Get Value at Risk"""
        response = requests.get(f"{BASE_URL}/api/risk-analyzer/var")
        assert response.status_code == 200
        
        data = response.json()
        assert "var_95" in data
        assert "var_99" in data
        assert "expected_shortfall" in data
        assert "portfolio_value" in data
        assert "methodology" in data
        
        print(f"✓ VaR: 95%=${data['var_95']}, 99%=${data['var_99']}")
    
    def test_risk_correlations(self):
        """Test GET /api/risk-analyzer/correlations - Get correlation matrix"""
        response = requests.get(f"{BASE_URL}/api/risk-analyzer/correlations")
        assert response.status_code == 200
        
        data = response.json()
        assert "matrix" in data
        assert "high_correlation_pairs" in data
        assert "diversification_tip" in data
        
        print(f"✓ Correlations: {len(data['high_correlation_pairs'])} high correlation pairs")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
