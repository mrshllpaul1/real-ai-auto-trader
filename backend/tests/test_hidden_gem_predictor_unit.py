import os
import sys

import pytest

# Make backend modules importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.hidden_gem_predictor import HiddenGemPredictor, LlmChat


class DummyPredictor(HiddenGemPredictor):
    """Minimal stub to bypass heavy DB/market dependencies."""

    async def scan_for_gems(self, limit: int = 30, use_full_universe: bool = True):
        return [
            {
                "coin_id": "test-coin",
                "symbol": "TEST",
                "name": "Test Coin",
                "current_price": 1.23,
                "market_cap": 100_000_000,
                "scores": {"price_momentum": 80, "volume_surge": 75, "relative_strength": 70},
                "total_score": 78.5,
                "gem_rating": "🌟 HIGH POTENTIAL",
            }
        ]


@pytest.mark.asyncio
async def test_predict_next_gems_graceful_without_llm(monkeypatch):
    """Hidden gem predictions should still work when LLM client isn't installed."""

    # Ensure LlmChat behaves as unavailable
    monkeypatch.setattr("services.hidden_gem_predictor.LlmChat", None)

    predictor = DummyPredictor(db=None, market_service=None)
    result = await predictor.predict_next_gems(days_ahead=5)

    assert "predictions" in result
    assert result["predictions"], "Should return fallback predictions without LLM"
    assert all("gem_score" in p for p in result["predictions"])
