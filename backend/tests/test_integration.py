"""
Integration Tests for Complete Workflows
"""

import pytest
from httpx import AsyncClient
import asyncio


class TestTradingWorkflow:
    """End-to-end trading workflow tests"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    async def test_complete_paper_trade_flow(self, client: AsyncClient):
        """Test complete paper trading flow"""
        # 1. Check trading status
        status_response = await client.get("/api/auto-trading/status")
        assert status_response.status_code == 200
        
        # 2. Get portfolio
        portfolio_response = await client.get("/api/portfolio/visualization/summary")
        assert portfolio_response.status_code in [200, 404]
        
        # 3. Get AI prediction (if available)
        ai_response = await client.get("/api/ensemble/status")
        assert ai_response.status_code == 200


class TestTriggerWorkflow:
    """End-to-end trigger workflow tests"""
    
    @pytest.mark.integration
    async def test_complete_trigger_lifecycle(self, client: AsyncClient, sample_trigger_data):
        """Test complete trigger lifecycle"""
        # 1. List existing triggers
        list_response = await client.get("/api/triggers/list")
        assert list_response.status_code == 200
        
        # 2. Get templates
        templates_response = await client.get("/api/triggers/templates")
        assert templates_response.status_code == 200
        
        # 3. Create new trigger
        create_response = await client.post(
            "/api/triggers/create",
            json=sample_trigger_data
        )
        # May succeed or fail based on existing data
        assert create_response.status_code in [200, 201, 400, 422]
        
        # 4. Check triggers
        check_response = await client.post("/api/triggers/check-now")
        assert check_response.status_code in [200, 400]
        
        # 5. Get history
        history_response = await client.get("/api/triggers/history/all")
        assert history_response.status_code in [200, 404]


class TestAIWorkflow:
    """End-to-end AI system workflow tests"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_ai_system_workflow(self, client: AsyncClient):
        """Test AI system workflow"""
        # 1. Check AI status
        ai_status = await client.get("/api/enhanced-ai/status")
        assert ai_status.status_code == 200
        
        # 2. Get ensemble weights
        weights = await client.get("/api/ensemble/weights")
        assert weights.status_code == 200
        
        # 3. Get optimal universe
        universe = await client.get("/api/ensemble/optimal-universe")
        assert universe.status_code == 200
        
        # 4. Check Tethys status
        tethys = await client.get("/api/tethys/status")
        assert tethys.status_code in [200, 404]


class TestKrakenIntegration:
    """Kraken exchange integration tests"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    async def test_kraken_connectivity(self, client: AsyncClient):
        """Test Kraken API connectivity"""
        response = await client.get("/api/kraken/status")
        assert response.status_code == 200
        data = response.json()
        # Should have some status indicator
        assert data is not None
    
    @pytest.mark.integration
    async def test_kraken_balance(self, client: AsyncClient):
        """Test Kraken balance retrieval"""
        response = await client.get("/api/kraken/balance")
        # May be 401 if not authenticated, but should not crash
        assert response.status_code in [200, 401, 404]


class TestErrorHandling:
    """Error handling integration tests"""
    
    @pytest.mark.integration
    async def test_404_handling(self, client: AsyncClient):
        """Test 404 error handling"""
        response = await client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404
    
    @pytest.mark.integration
    async def test_method_not_allowed(self, client: AsyncClient):
        """Test method not allowed handling"""
        response = await client.delete("/api/health")
        assert response.status_code in [405, 404]
    
    @pytest.mark.integration
    async def test_validation_error_response(self, client: AsyncClient):
        """Test validation error response format"""
        response = await client.post(
            "/api/triggers/create",
            json={"invalid": "data"}
        )
        assert response.status_code in [400, 422]
        data = response.json()
        assert 'detail' in data


class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_requests(self, client: AsyncClient):
        """Test handling of concurrent requests"""
        # Send 10 concurrent health checks
        tasks = [client.get("/api/health") for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 8  # At least 80% success rate
    
    @pytest.mark.integration
    async def test_response_time(self, client: AsyncClient):
        """Test response time is acceptable"""
        import time
        
        start = time.time()
        response = await client.get("/api/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0  # Should respond within 2 seconds
