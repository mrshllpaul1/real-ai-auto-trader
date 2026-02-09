"""
Unit tests for Kraken portfolio resilience and caching.
These tests ensure the endpoint returns quickly using cached data when Kraken is slow.
"""

import asyncio
import os
import sys
import time
import types

import pytest

# Ensure backend modules are importable when running tests directly
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


def test_use_cached_portfolio_with_data():
    """_use_cached_portfolio should return cached payload with stale flag."""
    from routes import trading

    trading._kraken_portfolio_cache["data"] = {
        "holdings": [{"asset": "BTC", "value_usd": 100}],
        "total_value_usd": 100,
        "holdings_count": 1,
        "last_updated": "2026-02-09T00:00:00Z",
        "stale": False,
    }
    trading._kraken_portfolio_cache["timestamp"] = time.time() - 5

    result = trading._use_cached_portfolio("timeout")

    assert result["stale"] is True
    assert result["holdings_count"] == 1
    assert result["total_value_usd"] == 100
    assert result.get("error") == "timeout"


def test_use_cached_portfolio_without_data():
    """Returns structured empty response when no cache exists."""
    from routes import trading

    trading._kraken_portfolio_cache["data"] = None
    trading._kraken_portfolio_cache["timestamp"] = None

    result = trading._use_cached_portfolio("unavailable")

    assert result["holdings"] == []
    assert result["holdings_count"] == 0
    assert result["stale"] is True
    assert "unavailable" in result.get("error", "unavailable")


@pytest.mark.asyncio
async def test_kraken_portfolio_falls_back_to_cache(monkeypatch):
    """If Kraken calls time out, cached portfolio should be returned."""
    from routes import trading

    trading._kraken_portfolio_cache["data"] = {
        "holdings": [{"asset": "BTC", "value_usd": 250}],
        "total_value_usd": 250,
        "holdings_count": 1,
        "last_updated": "2026-02-09T00:00:00Z",
        "stale": False,
    }
    trading._kraken_portfolio_cache["timestamp"] = time.time() - 120  # expired cache

    class SlowKraken:
        async def get_balance(self):
            await asyncio.sleep(trading._KRAKEN_BALANCE_TIMEOUT + 0.5)

        async def get_tickers_batch(self, pairs):
            await asyncio.sleep(trading._KRAKEN_TICKER_TIMEOUT + 0.5)
            return {}

    slow_service = SlowKraken()
    dummy_server = types.ModuleType("server")
    dummy_server.get_service = lambda name: slow_service
    monkeypatch.setitem(sys.modules, "server", dummy_server)

    result = await trading.get_kraken_portfolio()

    assert result["stale"] is True
    assert result["holdings_count"] == 1
    assert result["total_value_usd"] == 250
