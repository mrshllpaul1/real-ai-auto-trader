import pytest


@pytest.mark.asyncio
async def test_trader_finder_returns_five(client):
    """GET /api/copy-trading/trader-finder should always return 5 prospects."""
    response = await client.get("/api/copy-trading/trader-finder")
    assert response.status_code == 200

    data = response.json()
    prospects = data.get("prospects", [])
    assert len(prospects) == 5

    required_fields = {
        "trader_id",
        "display_name",
        "specialty",
        "expected_roi",
        "risk",
        "trend",
        "signal_strength",
    }
    for p in prospects:
        assert required_fields.issubset(p.keys())
        assert isinstance(p.get("expected_roi"), (int, float))
        assert isinstance(p.get("signal_strength"), (int, float))
