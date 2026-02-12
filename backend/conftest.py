"""
Pytest Configuration and Fixtures
Shared fixtures for all tests
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def app():
    """Get FastAPI app instance"""
    from server import app
    yield app


@pytest.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
async def db_client():
    """Create MongoDB test client"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    yield client
    client.close()


@pytest.fixture(scope="function")
async def test_db(db_client):
    """Get test database with cleanup"""
    db_name = 'crypto_trading_test_db'
    db = db_client[db_name]
    yield db
    # Cleanup after each test
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})


@pytest.fixture
def sample_trigger_data():
    """Sample trigger data for tests"""
    return {
        "name": "Test Bitcoin Alert",
        "description": "Alert when BTC reaches target",
        "trigger_type": "price_above",
        "coins": ["BTC"],
        "conditions": {"price": 50000},
        "action": "notify",
        "is_active": True,
        "cooldown_minutes": 60
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for tests"""
    return {
        "symbol": "BTCUSD",
        "side": "buy",
        "order_type": "market",
        "amount": 0.001,
        "trading_mode": "paper"
    }


@pytest.fixture
def mock_kraken_response():
    """Mock Kraken API response"""
    return {
        "result": {
            "XXBTZUSD": {
                "a": ["45000.00000", "1", "1.000"],
                "b": ["44999.00000", "1", "1.000"],
                "c": ["45000.00000", "0.10000000"],
                "v": ["1000.00000000", "5000.00000000"],
                "p": ["44500.00000", "44800.00000"],
                "t": [1000, 5000],
                "l": ["44000.00000", "43500.00000"],
                "h": ["46000.00000", "46500.00000"],
                "o": "44500.00000"
            }
        }
    }


# Test markers helpers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "critical: Critical path tests")


def should_skip_backend_tests(module) -> bool:
    """Return True when BASE_URL is present but invalid; False when missing (non-backend tests) or valid."""
    base_url = getattr(module, "BASE_URL", None)
    if base_url is None:
        return False
    if not base_url:
        return True
    return not base_url.startswith(("http://", "https://"))


def pytest_runtest_setup(item):
    if should_skip_backend_tests(item.module):
        pytest.skip("BASE_URL (from REACT_APP_BACKEND_URL) not set or invalid; skipping backend integration tests")
