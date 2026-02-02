from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

_alert_service = None

class CreateAlertRequest(BaseModel):
    coin_id: str
    condition: str = 'above'  # above, below
    target_price: float
    notification_type: str = 'push'  # push only (with vibration)

async def get_alert_service():
    global _alert_service
    from server import db
    from services.price_alerts import PriceAlertService
    from services.notification_service import NotificationService
    
    if _alert_service is None:
        notification_service = NotificationService(db)
        _alert_service = PriceAlertService(db, notification_service)
    
    return _alert_service

@router.post("/create")
async def create_alert(request: CreateAlertRequest, user_id: str = 'default'):
    """Create a new price alert"""
    try:
        service = await get_alert_service()
        alert = await service.create_alert(user_id, request.dict())
        return {"message": "Alert created", "alert": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_alerts(user_id: str = 'default'):
    """Get all alerts for a user"""
    try:
        service = await get_alert_service()
        alerts = await service.get_user_alerts(user_id)
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    try:
        service = await get_alert_service()
        success = await service.delete_alert(alert_id)
        if success:
            return {"message": "Alert deleted"}
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check")
async def check_alerts(prices: dict):
    """Manually check alerts against provided prices"""
    try:
        service = await get_alert_service()
        triggered = await service.check_alerts(prices)
        return {"triggered": triggered, "count": len(triggered)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
