import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure backend modules can be imported when running from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import server
from health import check_database_connection


class DummyAdmin:
    def __init__(self, should_raise: bool = False, expected_command: str | None = "ping"):
        self.should_raise = should_raise
        self.expected_command = expected_command

    async def command(self, name: str):
        if self.expected_command:
            assert name == self.expected_command
        if self.should_raise:
            raise RuntimeError("ping failed")
        return {"ok": 1}


class DummyClient:
    def __init__(self, should_raise: bool = False):
        self.admin = DummyAdmin(should_raise=should_raise)


@pytest.mark.asyncio
async def test_check_database_connection_success():
    dummy = DummyClient()
    result = await check_database_connection(dummy)
    assert result["status"] == "healthy"
    assert result["database"] == "connected"


@pytest.mark.asyncio
async def test_check_database_connection_failure():
    dummy = DummyClient(should_raise=True)
    result = await check_database_connection(dummy)
    assert result["status"] == "unhealthy"
    assert "error" in result["database"]


def test_health_endpoint_uses_database_status(monkeypatch):
    async def fake_check(_client):
        return {"status": "healthy", "database": "connected"}

    monkeypatch.setattr(server, "check_database_connection", fake_check)
    client = TestClient(server.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_health_endpoint_returns_503_when_unhealthy(monkeypatch):
    async def fake_check(_client):
        return {"status": "unhealthy", "database": "error: ping failed"}

    monkeypatch.setattr(server, "check_database_connection", fake_check)
    client = TestClient(server.app)
    resp = client.get("/health")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "unhealthy"
    assert "error" in data["database"]
