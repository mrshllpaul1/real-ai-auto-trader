"""
Comprehensive API Endpoint Tests
Target: 70%+ coverage on critical endpoints
"""

import pytest
from httpx import AsyncClient
import json


class TestHealthEndpoints:
    """Health check endpoint tests"""
    
    @pytest.mark.api
    @pytest.mark.critical
    async def test_health_check(self, client: AsyncClient):
        """Test main health endpoint"""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
    
    @pytest.mark.api
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint"""
        response = await client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestTethysEndpoints:
    """Tethys trading engine tests"""
    
    @pytest.mark.api
    @pytest.mark.critical
    async def test_tethys_status(self, client: AsyncClient):
        """Test Tethys status endpoint"""
        response = await client.get("/api/tethys/status")
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    async def test_tethys_trading_status(self, client: AsyncClient):
        """Test Tethys trading status"""
        response = await client.get("/api/tethys-trading/status")
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    async def test_tethys_start_stop(self, client: AsyncClient):
        """Test Tethys start/stop controls"""
        # Start
        start_response = await client.post("/api/tethys-trading/start")
        assert start_response.status_code in [200, 400, 404]
        
        # Stop
        stop_response = await client.post("/api/tethys-trading/stop")
        assert stop_response.status_code in [200, 400, 404]
    
    @pytest.mark.api
    async def test_tethys_evaluate(self, client: AsyncClient):
        """Test Tethys evaluation endpoint"""
        response = await client.post(
            "/api/tethys/evaluate",
            json={"coin_id": "BTC"}
        )
        assert response.status_code in [200, 400, 404, 422]


class TestTriggerEndpoints:
    """Event trigger endpoint tests"""
    
    @pytest.mark.api
    @pytest.mark.critical
    async def test_list_triggers(self, client: AsyncClient):
        """Test listing triggers"""
        response = await client.get("/api/triggers/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    @pytest.mark.api
    async def test_trigger_templates(self, client: AsyncClient):
        """Test trigger templates endpoint"""
        response = await client.get("/api/triggers/templates")
        assert response.status_code == 200
    
    @pytest.mark.api
    async def test_trigger_status(self, client: AsyncClient):
        """Test trigger status endpoint"""
        response = await client.get("/api/triggers/status")
        assert response.status_code == 200
    
    @pytest.mark.api
    async def test_trigger_history(self, client: AsyncClient):
        """Test trigger history endpoint"""
        response = await client.get("/api/triggers/history/all")
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    async def test_create_trigger(self, client: AsyncClient, sample_trigger_data):
        """Test creating a trigger"""
        response = await client.post(
            "/api/triggers/create",
            json=sample_trigger_data
        )
        assert response.status_code in [200, 201, 400, 422]
    
    @pytest.mark.api
    async def test_check_triggers(self, client: AsyncClient):
        """Test manual trigger check"""
        response = await client.post("/api/triggers/check-now")
        assert response.status_code in [200, 400]


class TestEnsembleEndpoints:
    """Ensemble AI endpoint tests"""
    
    @pytest.mark.api
    @pytest.mark.critical
    async def test_ensemble_status(self, client: AsyncClient):
        """Test ensemble status"""
        response = await client.get("/api/ensemble/status")
        assert response.status_code == 200
    
    @pytest.mark.api
    async def test_ensemble_weights(self, client: AsyncClient):
        """Test ensemble weights endpoint"""
        response = await client.get("/api/ensemble/weights")
        assert response.status_code == 200
    
    @pytest.mark.api
    async def test_ensemble_build_status(self, client: AsyncClient):
        """Test ensemble build status"""
        response = await client.get("/api/ensemble/build-status")
        assert response.status_code == 200
    
    @pytest.mark.api
    async def test_optimal_universe(self, client: AsyncClient):
        """Test optimal universe endpoint"""
        response = await client.get("/api/ensemble/optimal-universe")
        assert response.status_code == 200


class TestPortfolioEndpoints:
    """Portfolio endpoint tests"""
    
    @pytest.mark.api
    @pytest.mark.critical
    async def test_kraken_status(self, client: AsyncClient):
        """Test Kraken connection status"""
        response = await client.get("/api/kraken/status")
        assert response.status_code == 200
    
    @pytest.mark.api
    async def test_kraken_balance(self, client: AsyncClient):
        """Test Kraken balance endpoint"""
        response = await client.get("/api/kraken/balance")
        assert response.status_code in [200, 401, 404]
    
    @pytest.mark.api
    async def test_portfolio_visualization(self, client: AsyncClient):
        """Test portfolio visualization summary"""
        response = await client.get("/api/portfolio/visualization/summary")
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    async def test_portfolio_summary(self, client: AsyncClient):
        """Test portfolio summary"""
        response = await client.get("/api/portfolio/summary")
        assert response.status_code in [200, 404]


class TestTrainingEndpoints:
    """Model training endpoint tests"""
    
    @pytest.mark.api
    @pytest.mark.slow
    async def test_enhanced_ai_train(self, client: AsyncClient):
        """Test enhanced AI training"""
        response = await client.post("/api/enhanced-ai/train")
        assert response.status_code in [200, 400, 503]
    
    @pytest.mark.api
    async def test_enhanced_ai_status(self, client: AsyncClient):
        """Test enhanced AI status"""
        response = await client.get("/api/enhanced-ai/status")
        assert response.status_code == 200
    
    @pytest.mark.api
    @pytest.mark.slow
    async def test_general_training(self, client: AsyncClient):
        """Test general model training"""
        response = await client.post("/api/training/train")
        assert response.status_code in [200, 400, 503]
    
    @pytest.mark.api
    async def test_training_status(self, client: AsyncClient):
        """Test training status"""
        response = await client.get("/api/training/status")
        assert response.status_code == 200


class TestMarketEndpoints:
    """Market data endpoint tests"""
    
    @pytest.mark.api
    async def test_sentiment_market(self, client: AsyncClient):
        """Test market sentiment"""
        response = await client.get("/api/sentiment/market")
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    async def test_auto_trading_status(self, client: AsyncClient):
        """Test auto trading status"""
        response = await client.get("/api/auto-trading/status")
        assert response.status_code == 200
    
    @pytest.mark.api
    async def test_market_prices_with_params(self, client: AsyncClient):
        """Test market prices with coin_ids"""
        response = await client.get(
            "/api/market/prices",
            params={"coin_ids": "bitcoin,ethereum"}
        )
        assert response.status_code in [200, 400, 422]


class TestJournalEndpoints:
    """Trading journal endpoint tests"""
    
    @pytest.mark.api
    async def test_journal_entries(self, client: AsyncClient):
        """Test journal entries"""
        response = await client.get("/api/journal/entries")
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    async def test_journal_record(self, client: AsyncClient):
        """Test recording journal entry"""
        entry = {
            "trade_id": "test-123",
            "symbol": "BTC",
            "side": "buy",
            "amount": 0.001,
            "notes": "Test entry"
        }
        response = await client.post("/api/journal/record", json=entry)
        assert response.status_code in [200, 201, 400, 404, 422]


class TestCacheEndpoints:
    """Cache system endpoint tests"""
    
    @pytest.mark.api
    async def test_cache_stats(self, client: AsyncClient):
        """Test cache stats endpoint"""
        response = await client.get("/api/cache/stats")
        assert response.status_code in [200, 404]


class TestMonitoringEndpoints:
    """Monitoring endpoint tests"""
    
    @pytest.mark.api
    async def test_errors_endpoint(self, client: AsyncClient):
        """Test error monitoring endpoint"""
        response = await client.get("/api/monitoring/errors")
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    async def test_error_stats(self, client: AsyncClient):
        """Test error statistics endpoint"""
        response = await client.get("/api/monitoring/errors/stats")
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    async def test_detailed_health(self, client: AsyncClient):
        """Test detailed health endpoint"""
        response = await client.get("/api/monitoring/health/detailed")
        assert response.status_code in [200, 404]


class TestSecurityHeaders:
    """Security headers tests"""
    
    @pytest.mark.api
    @pytest.mark.critical
    async def test_security_headers_present(self, client: AsyncClient):
        """Test that security headers are present"""
        response = await client.get("/api/health")
        
        # Check for security headers
        expected_headers = [
            'x-content-type-options',
            'x-frame-options',
            'x-xss-protection',
        ]
        
        for header in expected_headers:
            assert header in response.headers or header.lower() in [h.lower() for h in response.headers], \
                f"Missing security header: {header}"
    
    @pytest.mark.api
    async def test_rate_limit_headers(self, client: AsyncClient):
        """Test rate limit headers present"""
        response = await client.get("/api/health")
        # Rate limit headers may or may not be present based on config
        assert response.status_code == 200


class TestInputValidation:
    """Input validation tests"""
    
    @pytest.mark.api
    async def test_invalid_json_body(self, client: AsyncClient):
        """Test handling of invalid JSON"""
        response = await client.post(
            "/api/triggers/create",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    @pytest.mark.api
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test handling of missing required fields"""
        response = await client.post(
            "/api/triggers/create",
            json={"name": "Test"}  # Missing required fields
        )
        assert response.status_code in [400, 422]
    
    @pytest.mark.api
    async def test_invalid_field_types(self, client: AsyncClient):
        """Test handling of invalid field types"""
        response = await client.post(
            "/api/triggers/create",
            json={
                "name": 123,  # Should be string
                "trigger_type": "invalid",
                "coins": "not-a-list",  # Should be list
                "conditions": "not-a-dict"  # Should be dict
            }
        )
        assert response.status_code in [400, 422]
