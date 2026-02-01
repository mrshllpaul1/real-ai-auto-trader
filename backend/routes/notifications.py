from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

# Global notification service instance
_notification_service = None

class NotificationSettingsUpdate(BaseModel):
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    sms_phone: Optional[str] = None
    notify_trade_open: Optional[bool] = None
    notify_trade_close: Optional[bool] = None
    notify_high_alerts: Optional[bool] = None
    notify_medium_alerts: Optional[bool] = None

class TestSmsRequest(BaseModel):
    message: str = "Test notification from AI Crypto Trading"
    phone: Optional[str] = None

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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-read/{notification_id}")
async def mark_read(notification_id: str):
    """Mark a notification as read"""
    try:
        service = await get_notification_service()
        await service.mark_notification_read(notification_id)
        return {"message": "Notification marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-all-read")
async def mark_all_read():
    """Mark all notifications as read"""
    try:
        service = await get_notification_service()
        await service.mark_all_read()
        return {"message": "All notifications marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_settings(user_id: str = 'default'):
    """Get notification settings"""
    try:
        service = await get_notification_service()
        settings = await service.get_notification_settings(user_id)
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-sms")
async def test_sms(request: TestSmsRequest):
    """Send a test SMS notification"""
    try:
        service = await get_notification_service()
        result = await service.send_sms(request.message, request.phone)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-push")
async def test_push():
    """Send a test push notification"""
    try:
        service = await get_notification_service()
        result = await service.send_push_notification(
            title="Test Notification",
            body="This is a test notification from AI Crypto Trading",
            data={"type": "test"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
