import os
import sys
import time
from pathlib import Path

import requests
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _require_base_url():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")


def _check_latency(endpoint: str, max_seconds: float = 2.5):
    start = time.time()
    resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
    elapsed = time.time() - start
    assert resp.status_code == 200, f"{endpoint} status {resp.status_code}"
    assert elapsed < max_seconds, f"{endpoint} took {elapsed:.3f}s (> {max_seconds}s)"
    return resp.json(), elapsed


def test_health_and_dependencies():
    _require_base_url()
    data, elapsed = _check_latency("/api/health", max_seconds=1.5)
    assert data.get("status") == "healthy"
    assert "database" in data
    assert "services" in data
    assert isinstance(data.get("services", {}), dict)


def test_spot_status_and_ai_latency():
    _require_base_url()
    data, elapsed = _check_latency("/api/spot/status", max_seconds=2.0)
    assert "features" in data
    assert "kraken_connected" in data.get("features", {})


def test_master_and_enhanced_ai_status():
    _require_base_url()
    master, _ = _check_latency("/api/master/status", max_seconds=2.0)
    assert "is_active" in master
    assert "mode" in master

    enhanced, _ = _check_latency("/api/enhanced-ai/status", max_seconds=2.0)
    assert "initialized" in enhanced
    assert "models_active" in enhanced


def test_kraken_portfolio_health():
    _require_base_url()
    data, elapsed = _check_latency("/api/trading/kraken/portfolio", max_seconds=3.0)
    assert "holdings" in data
    assert "total_value_usd" in data
