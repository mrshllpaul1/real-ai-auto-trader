import asyncio

from services.historical_events_db import HistoricalEventsDatabase


def test_upcoming_predictions_cover_key_patterns():
    """
    Ensure upcoming predictable events include major scheduled catalysts
    like token unlocks and ETF decision windows.
    """
    events_db = HistoricalEventsDatabase(db=None)

    upcoming = asyncio.run(events_db.get_upcoming_predictable_events())
    event_types = {event.get("event_type", "") for event in upcoming}

    assert any("Token Unlock" in et for et in event_types)
    assert any("ETF Decision Window" in et for et in event_types)
    assert len(upcoming) >= 5
