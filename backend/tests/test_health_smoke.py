import os
import sys
from pathlib import Path

import requests
import pytest

# Ensure backend root is importable if needed for dynamic imports
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def test_health_endpoint_up():
    """Basic health check to ensure backend is responding."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")

    resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"


def test_spot_status_endpoint_up():
    """Ensure spot trading status endpoint responds."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")

    resp = requests.get(f"{BASE_URL}/api/spot/status", timeout=5)
    assert resp.status_code == 200
