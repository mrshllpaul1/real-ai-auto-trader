"""
Push Notifications API Routes
==============================
Browser push notifications using Web Push protocol.
"""

import logging
import os
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/push-notifications", tags=["Push Notifications"])

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


class PushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]  # p256dh, auth


class NotificationPayload(BaseModel):
    title: str
    body: str
    icon: Optional[str] = "/icons/notification.png"
    badge: Optional[str] = "/icons/badge.png"
    tag: Optional[str] = None
    data: Optional[Dict] = None
    actions: Optional[List[Dict]] = None
    requireInteraction: bool = False


class NotificationPreferences(BaseModel):
    trade_alerts: bool = True
    price_alerts: bool = True
    ai_signals: bool = True
    risk_warnings: bool = True
    portfolio_updates: bool = True
    achievements: bool = True
    news_alerts: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 8  # 8 AM


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for push subscription"""
    # In production, this should be from environment variable
    # For demo, using a placeholder
    public_key = os.environ.get(
        "VAPID_PUBLIC_KEY",
        "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U"
    )
    return {"publicKey": public_key}


@router.post("/subscribe")
async def subscribe_to_push(
    subscription: PushSubscription,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Subscribe to push notifications"""
    sub_data = {
        "subscription_id": str(uuid.uuid4()),
        "user_id": user_id,
        "endpoint": subscription.endpoint,
        "keys": subscription.keys,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Remove existing subscriptions for same endpoint
    await db.push_subscriptions.delete_many({"endpoint": subscription.endpoint})
    
    # Add new subscription
    await db.push_subscriptions.insert_one(sub_data)
    
    return {
        "status": "subscribed",
        "subscription_id": sub_data["subscription_id"]
    }


@router.post("/unsubscribe")
async def unsubscribe_from_push(
    endpoint: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Unsubscribe from push notifications"""
    result = await db.push_subscriptions.delete_one({
        "endpoint": endpoint,
        "user_id": user_id
    })
    
    return {
        "status": "unsubscribed",
        "deleted": result.deleted_count > 0
    }


@router.get("/preferences")
async def get_notification_preferences(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's notification preferences"""
    prefs = await db.notification_preferences.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not prefs:
        prefs = NotificationPreferences().model_dump()
        prefs["user_id"] = user_id
    
    return prefs


@router.post("/preferences")
async def save_notification_preferences(
    preferences: NotificationPreferences,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save user's notification preferences"""
    data = preferences.model_dump()
    data["user_id"] = user_id
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.notification_preferences.replace_one(
        {"user_id": user_id},
        data,
        upsert=True
    )
    
    return {"status": "saved", "preferences": data}


@router.post("/send")
async def send_push_notification(
    payload: NotificationPayload,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Send a push notification to user (internal use)"""
    # Get user's subscriptions
    subscriptions = await db.push_subscriptions.find({
        "user_id": user_id,
        "active": True
    }).to_list(10)
    
    if not subscriptions:
        return {
            "status": "no_subscriptions",
            "message": "User has no active push subscriptions"
        }
    
    # In production, you would use pywebpush library here
    # For now, we'll store the notification for polling
    notification = {
        "notification_id": str(uuid.uuid4()),
        "user_id": user_id,
        "payload": payload.model_dump(),
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "subscriptions_count": len(subscriptions)
    }
    
    await db.push_notifications.insert_one(notification)
    
    return {
        "status": "queued",
        "notification_id": notification["notification_id"],
        "sent_to": len(subscriptions)
    }


@router.get("/pending")
async def get_pending_notifications(
    user_id: str = "default_user",
    limit: int = 20,
    db = Depends(get_database)
):
    """Get pending/unread notifications (for polling fallback)"""
    notifications = await db.push_notifications.find(
        {"user_id": user_id, "read": False},
        {"_id": 0}
    ).sort("sent_at", -1).limit(limit).to_list(limit)
    
    return {
        "notifications": notifications,
        "count": len(notifications)
    }


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Mark a notification as read"""
    await db.push_notifications.update_one(
        {"notification_id": notification_id, "user_id": user_id},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "marked_read"}


@router.post("/mark-all-read")
async def mark_all_read(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Mark all notifications as read"""
    result = await db.push_notifications.update_many(
        {"user_id": user_id, "read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "marked_all_read", "count": result.modified_count}


@router.get("/history")
async def get_notification_history(
    user_id: str = "default_user",
    limit: int = 50,
    db = Depends(get_database)
):
    """Get notification history"""
    notifications = await db.push_notifications.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("sent_at", -1).limit(limit).to_list(limit)
    
    unread_count = await db.push_notifications.count_documents({
        "user_id": user_id,
        "read": False
    })
    
    return {
        "notifications": notifications,
        "total": len(notifications),
        "unread_count": unread_count
    }


@router.delete("/clear-history")
async def clear_notification_history(
    days_old: int = 30,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Clear old notifications"""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
    
    result = await db.push_notifications.delete_many({
        "user_id": user_id,
        "sent_at": {"$lt": cutoff.isoformat()}
    })
    
    return {"status": "cleared", "deleted": result.deleted_count}


@router.get("/status")
async def get_push_status(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get push notification status for user"""
    subscriptions = await db.push_subscriptions.count_documents({
        "user_id": user_id,
        "active": True
    })
    
    unread = await db.push_notifications.count_documents({
        "user_id": user_id,
        "read": False
    })
    
    prefs = await db.notification_preferences.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    return {
        "subscribed": subscriptions > 0,
        "active_subscriptions": subscriptions,
        "unread_notifications": unread,
        "preferences_configured": prefs is not None
    }
