import os
import sys
from pathlib import Path

import requests
import pytest

# Ensure backend root is in path for any dynamic imports during test run
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def test_spot_ai_recommendations_include_composite():
    """Spot AI recommendations should include composite signal metadata."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    
    response = requests.get(f"{BASE_URL}/api/spot/ai-recommendations")
    assert response.status_code == 200

    data = response.json()
    assert 'recommendations' in data

    if data['recommendations']:
        rec = data['recommendations'][0]
        assert 'composite' in rec, "Composite block missing from recommendation"
        assert 'signal' in rec['composite'], "Composite signal missing"
        assert 'score' in rec['composite'], "Composite score missing"
