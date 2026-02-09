"""
Unit Tests for Middleware Components
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch


class TestRateLimiter:
    """Rate limiter unit tests"""
    
    @pytest.mark.unit
    def test_rate_limit_config_tiers(self):
        """Test rate limit tier configuration"""
        from middleware.rate_limiter import RateLimitConfig
        
        assert 'free' in RateLimitConfig.TIERS
        assert 'pro' in RateLimitConfig.TIERS
        assert 'enterprise' in RateLimitConfig.TIERS
        
        # Free tier should have lowest limits
        assert RateLimitConfig.TIERS['free']['requests_per_minute'] < \
               RateLimitConfig.TIERS['pro']['requests_per_minute']
    
    @pytest.mark.unit
    async def test_rate_limiter_allows_initial_requests(self):
        """Test that initial requests are allowed"""
        from middleware.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/api/test"
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        allowed, info = await limiter.check_rate_limit(mock_request)
        assert allowed is True
    
    @pytest.mark.unit
    async def test_rate_limiter_skips_health_endpoints(self):
        """Test that health endpoints skip rate limiting"""
        from middleware.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        mock_request = Mock()
        mock_request.url.path = "/api/health"
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        allowed, info = await limiter.check_rate_limit(mock_request)
        assert allowed is True
        assert info is None  # No rate limit info for skipped paths


class TestErrorMonitoring:
    """Error monitoring unit tests"""
    
    @pytest.mark.unit
    def test_error_record_creation(self):
        """Test error record creation"""
        from middleware.error_monitoring import ErrorRecord, ErrorSeverity
        
        record = ErrorRecord(
            error_id="test123",
            timestamp=datetime.utcnow(),
            severity=ErrorSeverity.ERROR,
            error_type="TestError",
            message="Test error message",
            stack_trace="",
            request_info={"method": "GET", "path": "/test"}
        )
        
        assert record.error_id == "test123"
        assert record.severity == ErrorSeverity.ERROR
        assert record.error_type == "TestError"
    
    @pytest.mark.unit
    def test_error_record_to_dict(self):
        """Test error record serialization"""
        from middleware.error_monitoring import ErrorRecord, ErrorSeverity
        
        record = ErrorRecord(
            error_id="test123",
            timestamp=datetime.utcnow(),
            severity=ErrorSeverity.ERROR,
            error_type="TestError",
            message="Test message",
            stack_trace="traceback here",
            request_info={"method": "GET"}
        )
        
        data = record.to_dict()
        assert data['error_id'] == "test123"
        assert data['severity'] == ErrorSeverity.ERROR
        assert 'timestamp' in data
    
    @pytest.mark.unit
    async def test_error_store_add_and_retrieve(self):
        """Test error store operations"""
        from middleware.error_monitoring import ErrorStore, ErrorRecord, ErrorSeverity
        
        store = ErrorStore(max_errors=100)
        
        record = ErrorRecord(
            error_id="test123",
            timestamp=datetime.utcnow(),
            severity=ErrorSeverity.ERROR,
            error_type="TestError",
            message="Test",
            stack_trace="",
            request_info={}
        )
        
        await store.add_error(record)
        
        errors = await store.get_recent_errors(limit=10)
        assert len(errors) == 1
        assert errors[0]['error_id'] == "test123"
    
    @pytest.mark.unit
    async def test_error_store_stats(self):
        """Test error statistics"""
        from middleware.error_monitoring import ErrorStore, ErrorRecord, ErrorSeverity
        
        store = ErrorStore()
        
        # Add multiple errors
        for i in range(5):
            record = ErrorRecord(
                error_id=f"test{i}",
                timestamp=datetime.utcnow(),
                severity=ErrorSeverity.ERROR if i % 2 == 0 else ErrorSeverity.WARNING,
                error_type="TestError",
                message="Test",
                stack_trace="",
                request_info={}
            )
            await store.add_error(record)
        
        stats = await store.get_error_stats()
        assert stats['total_errors'] == 5
        assert stats['errors_last_hour'] == 5


class TestSecurityHeaders:
    """Security headers unit tests"""
    
    @pytest.mark.unit
    def test_csp_directive_building(self):
        """Test CSP header building"""
        from middleware.security_headers import SecurityHeadersMiddleware
        
        middleware = SecurityHeadersMiddleware(app=None)
        csp = middleware._build_csp_header()
        
        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp
    
    @pytest.mark.unit
    def test_permissions_policy_building(self):
        """Test permissions policy building"""
        from middleware.security_headers import SecurityHeadersMiddleware
        
        middleware = SecurityHeadersMiddleware(app=None)
        policy = middleware._build_permissions_policy()
        
        assert "camera" in policy
        assert "microphone" in policy
        assert "geolocation" in policy


class TestPydanticModels:
    """Pydantic model validation tests"""
    
    @pytest.mark.unit
    def test_create_order_request_validation(self):
        """Test order request validation"""
        from models.schemas.trading import CreateOrderRequest, OrderSide
        
        # Valid order
        order = CreateOrderRequest(
            symbol="BTCUSD",
            side=OrderSide.BUY,
            amount=0.001
        )
        assert order.symbol == "BTCUSD"
        assert order.amount == 0.001
    
    @pytest.mark.unit
    def test_create_order_symbol_normalization(self):
        """Test symbol normalization"""
        from models.schemas.trading import CreateOrderRequest, OrderSide
        
        order = CreateOrderRequest(
            symbol="  btcusd  ",
            side=OrderSide.BUY,
            amount=0.001
        )
        assert order.symbol == "BTCUSD"
    
    @pytest.mark.unit
    def test_create_order_limit_requires_price(self):
        """Test limit order requires price"""
        from models.schemas.trading import CreateOrderRequest, OrderSide, OrderType
        import pydantic
        
        with pytest.raises(pydantic.ValidationError):
            CreateOrderRequest(
                symbol="BTCUSD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                amount=0.001
                # Missing price
            )
    
    @pytest.mark.unit
    def test_create_trigger_request_validation(self):
        """Test trigger request validation"""
        from models.schemas.triggers import CreateTriggerRequest, TriggerType
        
        trigger = CreateTriggerRequest(
            name="Test Trigger",
            trigger_type=TriggerType.PRICE_ABOVE,
            coins=["btc", "eth"],
            conditions={"price": 50000}
        )
        
        assert trigger.name == "Test Trigger"
        assert trigger.coins == ["BTC", "ETH"]  # Normalized
    
    @pytest.mark.unit
    def test_create_trigger_invalid_conditions(self):
        """Test trigger validation for invalid conditions"""
        from models.schemas.triggers import CreateTriggerRequest, TriggerType
        import pydantic
        
        with pytest.raises(pydantic.ValidationError):
            CreateTriggerRequest(
                name="Test",
                trigger_type=TriggerType.PRICE_ABOVE,
                coins=["BTC"],
                conditions={}  # Missing required price condition
            )
    
    @pytest.mark.unit
    def test_rebalance_request_allocation_sum(self):
        """Test rebalance allocation sum validation"""
        from models.schemas.portfolio import RebalanceRequest
        import pydantic
        
        # Valid allocations (sum to 100%)
        rebalance = RebalanceRequest(
            target_allocations={"BTC": 50.0, "ETH": 30.0, "USD": 20.0}
        )
        assert sum(rebalance.target_allocations.values()) == 100.0
        
        # Invalid allocations (don't sum to 100%)
        with pytest.raises(pydantic.ValidationError):
            RebalanceRequest(
                target_allocations={"BTC": 50.0, "ETH": 30.0}  # Only 80%
            )
    
    @pytest.mark.unit
    def test_ensemble_weights_validation(self):
        """Test ensemble weights validation"""
        from models.schemas.ai import EnsembleConfigRequest
        import pydantic
        
        # Valid weights (sum to 1.0)
        config = EnsembleConfigRequest(
            weights={"lstm": 0.3, "technical": 0.4, "sentiment": 0.3}
        )
        assert sum(config.weights.values()) == 1.0
        
        # Invalid weights
        with pytest.raises(pydantic.ValidationError):
            EnsembleConfigRequest(
                weights={"lstm": 0.5, "technical": 0.6}  # Sum > 1
            )


class TestDatabasePooling:
    """Database connection pooling tests"""
    
    @pytest.mark.unit
    @pytest.mark.integration
    async def test_db_health_check(self):
        """Test database health check"""
        from config.database import health_check
        
        result = await health_check()
        assert 'status' in result
        assert 'connected' in result
    
    @pytest.mark.unit
    @pytest.mark.integration
    async def test_pool_stats(self):
        """Test pool statistics retrieval"""
        from config.database import get_pool_stats
        
        stats = await get_pool_stats()
        # Stats should return pool config even if we can't get server status
        assert 'pool_config' in stats or 'error' in stats
