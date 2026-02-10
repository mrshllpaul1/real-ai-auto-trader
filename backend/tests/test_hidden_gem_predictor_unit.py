import os
import sys

import pytest
from unittest.mock import MagicMock

# Make backend modules importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.hidden_gem_predictor import HiddenGemPredictor


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

    predictor = DummyPredictor(db=MagicMock(), market_service=MagicMock())
    result = await predictor.predict_next_gems(days_ahead=5)

    assert "predictions" in result
    assert result["predictions"], "Should return fallback predictions without LLM"
    assert all("gem_score" in p for p in result["predictions"])
    assert all("prediction_confidence" not in p for p in result["predictions"])


@pytest.mark.asyncio
async def test_predict_next_gems_skips_llm_when_no_api_key(monkeypatch):
    """Even if LLM client exists, fallback should be used when no API key is configured."""

    created = {"called": False}

    class DummyChat:
        def __init__(self, *args, **kwargs):
            created["called"] = True

        async def send_message(self, *_args, **_kwargs):
            raise AssertionError("LLM should not be invoked without API key")

        def with_model(self, *_args, **_kwargs):
            return self

    # Pretend LLM client is available but keep api_key unset
    monkeypatch.setattr("services.hidden_gem_predictor.LlmChat", DummyChat)

    predictor = DummyPredictor(db=MagicMock(), market_service=MagicMock())
    predictor.api_key = None  # Explicitly ensure missing key

    result = await predictor.predict_next_gems(days_ahead=3)

    assert result["predictions"], "Should still return fallback predictions"
    assert created["called"] is False, "LLM client should not be constructed without API key"
