import asyncio
from unittest.mock import MagicMock

from services.historical_events_db import HistoricalEventsDatabase, UPCOMING_TOKEN_UNLOCKS


def test_upcoming_predictions_cover_key_patterns():
    """
    Ensure upcoming predictable events include major scheduled catalysts
    like token unlocks and ETF decision windows.
    """
    events_db = HistoricalEventsDatabase(db=MagicMock())

    upcoming = asyncio.run(events_db.get_upcoming_predictable_events())
    event_types = {event.get("event_type", "") for event in upcoming}
    token_unlock_tokens = {
        event["coins_affected"][0]
        for event in upcoming
        if "Token Unlock" in event.get("event_type", "")
        and event.get("coins_affected")
    }
    expected_tokens = {unlock["token"] for unlock in UPCOMING_TOKEN_UNLOCKS}

    assert any("Token Unlock" in et for et in event_types)
    assert any("ETF Decision Window" in et for et in event_types)
    expected_min_events = len(UPCOMING_TOKEN_UNLOCKS) + 1  # token unlocks plus at least one non-unlock catalyst
    assert len(upcoming) >= expected_min_events
    # All configured unlock tokens should appear in the generated upcoming list
    assert expected_tokens.issubset(token_unlock_tokens)
    for event in upcoming:
        assert "predicted_date" in event
        assert "days_until" in event
        assert "coins_affected" in event
