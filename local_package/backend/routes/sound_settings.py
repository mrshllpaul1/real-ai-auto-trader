"""
Sound Settings API Routes
==========================
Manage sound alert preferences.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sound-settings", tags=["Sound Settings"])

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


class SoundSettings(BaseModel):
    enabled: bool = True
    volume: float = 0.5  # 0.0 to 1.0
    trade_executed: bool = True
    trade_copied: bool = True
    price_alert: bool = True
    risk_warning: bool = True
    ai_signal: bool = True
    achievement_unlocked: bool = True
    error_alert: bool = False


# Available sound effects
SOUND_EFFECTS = {
    "trade_executed": {
        "name": "Trade Executed",
        "description": "Plays when a trade is successfully executed",
        "default_sound": "success-chime",
        "options": ["success-chime", "cash-register", "notification", "bell"]
    },
    "trade_copied": {
        "name": "Trade Copied",
        "description": "Plays when a copy trade is executed",
        "default_sound": "notification",
        "options": ["notification", "pop", "ding", "swoosh"]
    },
    "price_alert": {
        "name": "Price Alert",
        "description": "Plays when a price alert triggers",
        "default_sound": "alert",
        "options": ["alert", "bell", "alarm", "notification"]
    },
    "risk_warning": {
        "name": "Risk Warning",
        "description": "Plays for risk alerts (drawdown, exposure)",
        "default_sound": "warning",
        "options": ["warning", "alarm", "alert", "siren"]
    },
    "ai_signal": {
        "name": "AI Signal",
        "description": "Plays when AI generates a trading signal",
        "default_sound": "digital",
        "options": ["digital", "tech", "notification", "ping"]
    },
    "achievement_unlocked": {
        "name": "Achievement Unlocked",
        "description": "Plays when earning a badge or achievement",
        "default_sound": "fanfare",
        "options": ["fanfare", "celebration", "level-up", "victory"]
    },
    "error_alert": {
        "name": "Error Alert",
        "description": "Plays when an error occurs",
        "default_sound": "error",
        "options": ["error", "warning", "buzz", "beep"]
    }
}


@router.get("/")
async def get_sound_settings(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's sound settings"""
    settings = await db.sound_settings.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not settings:
        # Return defaults
        settings = SoundSettings().model_dump()
        settings["user_id"] = user_id
        settings["sound_choices"] = {k: v["default_sound"] for k, v in SOUND_EFFECTS.items()}
    
    return settings


@router.post("/")
async def save_sound_settings(
    settings: SoundSettings,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save user's sound settings"""
    data = settings.model_dump()
    data["user_id"] = user_id
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.sound_settings.replace_one(
        {"user_id": user_id},
        data,
        upsert=True
    )
    
    return {"status": "saved", "settings": data}


@router.post("/sound-choice")
async def set_sound_choice(
    alert_type: str,
    sound_name: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Set specific sound for an alert type"""
    if alert_type not in SOUND_EFFECTS:
        raise HTTPException(status_code=400, detail=f"Invalid alert type: {alert_type}")
    
    if sound_name not in SOUND_EFFECTS[alert_type]["options"]:
        raise HTTPException(status_code=400, detail=f"Invalid sound: {sound_name}")
    
    await db.sound_settings.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"sound_choices.{alert_type}": sound_name,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    return {"status": "updated", "alert_type": alert_type, "sound": sound_name}


@router.get("/available-sounds")
async def get_available_sounds():
    """Get all available sound effects"""
    return {
        "sounds": SOUND_EFFECTS,
        "total_types": len(SOUND_EFFECTS)
    }


@router.post("/toggle/{alert_type}")
async def toggle_sound(
    alert_type: str,
    enabled: bool,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Toggle sound for specific alert type"""
    if alert_type not in SOUND_EFFECTS and alert_type != "enabled":
        raise HTTPException(status_code=400, detail=f"Invalid alert type: {alert_type}")
    
    await db.sound_settings.update_one(
        {"user_id": user_id},
        {
            "$set": {
                alert_type: enabled,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    return {"status": "toggled", "alert_type": alert_type, "enabled": enabled}


@router.post("/volume")
async def set_volume(
    volume: float,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Set global volume level (0.0 to 1.0)"""
    if not 0.0 <= volume <= 1.0:
        raise HTTPException(status_code=400, detail="Volume must be between 0.0 and 1.0")
    
    await db.sound_settings.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "volume": volume,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    return {"status": "updated", "volume": volume}
