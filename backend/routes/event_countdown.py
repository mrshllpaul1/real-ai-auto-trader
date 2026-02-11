"""
Event Countdown API Routes
===========================
Countdown timers for upcoming market events.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/event-countdown", tags=["Event Countdown"])

_db = None


def set_db(db):
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


# Scheduled events calendar (2025-2026)
SCHEDULED_EVENTS = [
    # FOMC Meetings 2025
    {"date": "2025-01-29", "name": "FOMC Meeting", "type": "fomc", "impact": "high", "icon": "🏛️"},
    {"date": "2025-03-19", "name": "FOMC Meeting", "type": "fomc", "impact": "high", "icon": "🏛️"},
    {"date": "2025-05-07", "name": "FOMC Meeting", "type": "fomc", "impact": "high", "icon": "🏛️"},
    {"date": "2025-06-18", "name": "FOMC Meeting", "type": "fomc", "impact": "high", "icon": "🏛️"},
    {"date": "2025-07-30", "name": "FOMC Meeting", "type": "fomc", "impact": "high", "icon": "🏛️"},
    {"date": "2025-09-17", "name": "FOMC Meeting", "type": "fomc", "impact": "high", "icon": "🏛️"},
    {"date": "2025-11-05", "name": "FOMC Meeting", "type": "fomc", "impact": "high", "icon": "🏛️"},
    {"date": "2025-12-17", "name": "FOMC Meeting", "type": "fomc", "impact": "high", "icon": "🏛️"},
    
    # Bitcoin Halving
    {"date": "2028-04-15", "name": "Bitcoin Halving (Est.)", "type": "halving", "impact": "critical", "icon": "₿"},
    
    # Options Expiry (Monthly - last Friday)
    {"date": "2025-07-25", "name": "Monthly Options Expiry", "type": "options_expiry", "impact": "medium", "icon": "📊"},
    {"date": "2025-08-29", "name": "Monthly Options Expiry", "type": "options_expiry", "impact": "medium", "icon": "📊"},
    {"date": "2025-09-26", "name": "Monthly Options Expiry", "type": "options_expiry", "impact": "medium", "icon": "📊"},
    {"date": "2025-10-31", "name": "Monthly Options Expiry", "type": "options_expiry", "impact": "medium", "icon": "📊"},
    {"date": "2025-11-28", "name": "Monthly Options Expiry", "type": "options_expiry", "impact": "medium", "icon": "📊"},
    {"date": "2025-12-26", "name": "Quarterly Options Expiry", "type": "options_expiry", "impact": "high", "icon": "📊"},
    
    # ETH Upgrades
    {"date": "2025-09-15", "name": "ETH Prague Upgrade (Est.)", "type": "upgrade", "impact": "high", "icon": "⬨"},
    
    # Major Token Unlocks (estimates)
    {"date": "2025-08-01", "name": "Major Token Unlocks", "type": "unlock", "impact": "medium", "icon": "🔓"},
    {"date": "2025-09-01", "name": "ARB Token Unlock", "type": "unlock", "impact": "medium", "icon": "🔓"},
    {"date": "2025-10-01", "name": "APT Token Unlock", "type": "unlock", "impact": "medium", "icon": "🔓"},
    
    # SEC Deadlines
    {"date": "2025-10-15", "name": "SEC ETF Deadline", "type": "regulatory", "impact": "high", "icon": "⚖️"},
    
    # Holidays
    {"date": "2025-12-25", "name": "Christmas (Low Liquidity)", "type": "holiday", "impact": "low", "icon": "🎄"},
    {"date": "2026-01-01", "name": "New Year", "type": "holiday", "impact": "low", "icon": "🎆"},
]


def calculate_countdown(event_date_str: str) -> Dict:
    """Calculate countdown to event"""
    event_date = datetime.strptime(event_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    
    diff = event_date - now
    
    if diff.total_seconds() < 0:
        return {
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0,
            "passed": True,
            "total_seconds": 0
        }
    
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    seconds = diff.seconds % 60
    
    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "passed": False,
        "total_seconds": int(diff.total_seconds())
    }


@router.get("/upcoming")
async def get_upcoming_events(
    limit: int = 10,
    event_type: Optional[str] = None,
    db = Depends(get_database)
):
    """Get upcoming events with countdown"""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    
    # Filter future events
    upcoming = []
    for event in SCHEDULED_EVENTS:
        if event["date"] >= today_str:
            if event_type is None or event["type"] == event_type:
                event_copy = event.copy()
                event_copy["countdown"] = calculate_countdown(event["date"])
                upcoming.append(event_copy)
    
    # Sort by date
    upcoming.sort(key=lambda x: x["date"])
    
    # Get custom events from database
    custom_events = await db.custom_events.find({
        "date": {"$gte": today_str}
    }, {"_id": 0}).to_list(50)
    
    for event in custom_events:
        event["countdown"] = calculate_countdown(event["date"])
        event["custom"] = True
        upcoming.append(event)
    
    # Re-sort and limit
    upcoming.sort(key=lambda x: x["date"])
    upcoming = upcoming[:limit]
    
    return {
        "events": upcoming,
        "total": len(upcoming),
        "next_event": upcoming[0] if upcoming else None
    }


@router.get("/next")
async def get_next_event(db = Depends(get_database)):
    """Get the next upcoming event with live countdown"""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    
    # Find next event
    next_event = None
    for event in sorted(SCHEDULED_EVENTS, key=lambda x: x["date"]):
        if event["date"] >= today_str:
            next_event = event.copy()
            break
    
    if not next_event:
        return {"next_event": None, "message": "No upcoming events"}
    
    next_event["countdown"] = calculate_countdown(next_event["date"])
    
    return {
        "next_event": next_event,
        "server_time": now.isoformat()
    }


@router.get("/by-type/{event_type}")
async def get_events_by_type(
    event_type: str,
    db = Depends(get_database)
):
    """Get events of a specific type"""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    
    events = []
    for event in SCHEDULED_EVENTS:
        if event["type"] == event_type and event["date"] >= today_str:
            event_copy = event.copy()
            event_copy["countdown"] = calculate_countdown(event["date"])
            events.append(event_copy)
    
    events.sort(key=lambda x: x["date"])
    
    return {
        "type": event_type,
        "events": events,
        "count": len(events)
    }


@router.get("/types")
async def get_event_types():
    """Get available event types"""
    types = {}
    for event in SCHEDULED_EVENTS:
        t = event["type"]
        if t not in types:
            types[t] = {
                "type": t,
                "icon": event["icon"],
                "count": 0
            }
        types[t]["count"] += 1
    
    return {"types": list(types.values())}


@router.post("/custom")
async def add_custom_event(
    name: str,
    date: str,
    event_type: str = "custom",
    impact: str = "medium",
    icon: str = "📌",
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Add a custom event"""
    import uuid
    
    event = {
        "event_id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": name,
        "date": date,
        "type": event_type,
        "impact": impact,
        "icon": icon,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_events.insert_one(event)
    event["countdown"] = calculate_countdown(date)
    
    return {"status": "created", "event": {k: v for k, v in event.items() if k != "_id"}}


@router.delete("/custom/{event_id}")
async def delete_custom_event(
    event_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Delete a custom event"""
    result = await db.custom_events.delete_one({
        "event_id": event_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"status": "deleted"}


@router.get("/this-week")
async def get_this_week_events(db = Depends(get_database)):
    """Get events happening this week"""
    now = datetime.now(timezone.utc)
    week_end = now + timedelta(days=7)
    
    today_str = now.strftime("%Y-%m-%d")
    week_end_str = week_end.strftime("%Y-%m-%d")
    
    events = []
    for event in SCHEDULED_EVENTS:
        if today_str <= event["date"] <= week_end_str:
            event_copy = event.copy()
            event_copy["countdown"] = calculate_countdown(event["date"])
            events.append(event_copy)
    
    events.sort(key=lambda x: x["date"])
    
    return {
        "week_start": today_str,
        "week_end": week_end_str,
        "events": events,
        "count": len(events)
    }
