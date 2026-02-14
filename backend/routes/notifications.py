from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

# Global notification service instance
_notification_service = None

class NotificationSettingsUpdate(BaseModel):
    push_enabled: Optional[bool] = None
    vibration_enabled: Optional[bool] = None
    notify_trade_open: Optional[bool] = None
    notify_trade_close: Optional[bool] = None
    notify_high_alerts: Optional[bool] = None
    notify_medium_alerts: Optional[bool] = None
    notify_ai_discoveries: Optional[bool] = None

class TestPushRequest(BaseModel):
    title: str = "Test Notification"
    body: str = "This is a test notification from AI Crypto Trading"
    priority: str = "normal"  # high, normal, low

async def get_notification_service():
    global _notification_service
    from server import db
    from services.notification_service import NotificationService
    
    if _notification_service is None:
        _notification_service = NotificationService(db)
    
    return _notification_service

@router.get("/")
async def get_notifications(limit: int = 50):
    """Get unread notifications"""
    try:
        service = await get_notification_service()
        notifications = await service.get_unread_notifications(limit)
        return {
            "count": len(notifications),
            "notifications": notifications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/mark-read/{notification_id}")
async def mark_read(notification_id: str):
    """Mark a notification as read"""
    try:
        service = await get_notification_service()
        await service.mark_notification_read(notification_id)
        return {"message": "Notification marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/mark-all-read")
async def mark_all_read():
    """Mark all notifications as read"""
    try:
        service = await get_notification_service()
        await service.mark_all_read()
        return {"message": "All notifications marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/settings")
async def get_settings(user_id: str = 'default'):
    """Get notification settings"""
    try:
        service = await get_notification_service()
        settings = await service.get_notification_settings(user_id)
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/settings")
async def update_settings(
    updates: NotificationSettingsUpdate,
    user_id: str = 'default'
):
    """Update notification settings"""
    try:
        service = await get_notification_service()
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        settings = await service.update_notification_settings(user_id, update_dict)
        return {
            "message": "Settings updated",
            "settings": settings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/test-push")
async def test_push(request: TestPushRequest = None):
    """Send a test push notification with vibration"""
    try:
        service = await get_notification_service()
        
        title = request.title if request else "Test Notification"
        body = request.body if request else "This is a test notification from AI Crypto Trading"
        priority = request.priority if request else "normal"
        
        result = await service.send_push_notification(
            title=title,
            body=body,
            data={"type": "test"},
            priority=priority,
            vibrate=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")
