import os
import sys

import pytest

# Ensure backend modules can be imported when running from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from health import check_database_connection


class MockDatabaseAdmin:
    def __init__(self, should_raise: bool = False):
        self.should_raise = should_raise

    async def command(self, name: str):
        assert name == "ping"
        if self.should_raise:
            raise RuntimeError("ping failed")
        return {"ok": 1}


class MockDatabaseClient:
    def __init__(self, should_raise: bool = False):
        self.admin = MockDatabaseAdmin(should_raise=should_raise)


@pytest.mark.asyncio
async def test_check_database_connection_success():
    healthy_client = MockDatabaseClient()
    result = await check_database_connection(healthy_client)
    assert result["status"] == "healthy"
    assert result["database"] == "connected"


@pytest.mark.asyncio
async def test_check_database_connection_failure():
    failing_client = MockDatabaseClient(should_raise=True)
    result = await check_database_connection(failing_client)
    assert result["status"] == "unhealthy"
    assert "error" in result["database"]


@pytest.mark.asyncio
async def test_check_database_connection_without_client():
    result = await check_database_connection(None)
    assert result["status"] == "unhealthy"
    assert "no database client" in result["database"]
