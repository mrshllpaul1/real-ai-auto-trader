import os
import sys
from pathlib import Path

import requests
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def test_spot_ai_recommendations_include_drivers():
    """Recommendations should expose top/weak contributing components."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    
    resp = requests.get(f"{BASE_URL}/api/spot/ai-recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    if data["recommendations"]:
        rec = data["recommendations"][0]
        assert "top_component" in rec
        assert "weak_component" in rec
