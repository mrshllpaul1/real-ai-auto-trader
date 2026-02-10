import pytest


@pytest.mark.asyncio
async def test_top_five_copy_traders_returns_five(client):
    """GET /api/copy-trading/top-five should always return 5 traders."""
    response = await client.get("/api/copy-trading/top-five")
    assert response.status_code == 200

    data = response.json()
    traders = data.get("leaderboard", [])
    assert len(traders) == 5

    required_fields = {"trader_id", "display_name", "stats"}
    for trader in traders:
        assert required_fields.issubset(trader.keys())
        assert isinstance(trader.get("stats", {}), dict)
