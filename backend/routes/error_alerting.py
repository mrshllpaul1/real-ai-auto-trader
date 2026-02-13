"""
Error Alerting Routes
API endpoints for configuring and managing error alerts
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from services.error_alerting_service import get_error_alerting_service

router = APIRouter(prefix="/api/error-alerting", tags=["Error Alerting"])


class AlertConfig(BaseModel):
    resend_api_key: Optional[str] = None
    sender_email: Optional[str] = "onboarding@resend.dev"
    recipient_emails: List[str] = []
    enabled: bool = False
    thresholds: Optional[Dict[str, int]] = None
    cooldown_minutes: int = 30
    alert_on_critical: bool = True
    alert_on_threshold: bool = True
    include_error_details: bool = True


class TestEmailRequest(BaseModel):
    api_key: str
    recipient_email: EmailStr


@router.get("/config")
async def get_config():
    """Get current alerting configuration"""
    service = get_error_alerting_service()
    if not service:
        raise HTTPException(status_code=503, detail="Error alerting service not initialized")
    
    config = await service.get_config()
    # Mask API key for security
    if config.get("resend_api_key"):
        config["resend_api_key_masked"] = config["resend_api_key"][:8] + "..." + config["resend_api_key"][-4:]
        config["has_api_key"] = True
    else:
        config["has_api_key"] = False
    config.pop("resend_api_key", None)
    
    return config


@router.post("/config")
async def save_config(config: AlertConfig):
    """Save alerting configuration"""
    service = get_error_alerting_service()
    if not service:
        raise HTTPException(status_code=503, detail="Error alerting service not initialized")
    
    config_dict = config.dict(exclude_none=True)
    result = await service.save_config(config_dict)
    
    # Mask API key in response
    if result.get("resend_api_key"):
        result["resend_api_key_masked"] = result["resend_api_key"][:8] + "..." + result["resend_api_key"][-4:]
        result["has_api_key"] = True
    else:
        result["has_api_key"] = False
    result.pop("resend_api_key", None)
    
    return result


@router.post("/test-connection")
async def test_connection(request: TestEmailRequest):
    """Test Resend connection by sending a test email"""
    service = get_error_alerting_service()
    if not service:
        raise HTTPException(status_code=503, detail="Error alerting service not initialized")
    
    result = await service.test_connection(request.api_key, request.recipient_email)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send test email"))
    
    return result


@router.get("/check-thresholds")
async def check_thresholds():
    """Check if any alert thresholds have been exceeded"""
    service = get_error_alerting_service()
    if not service:
        raise HTTPException(status_code=503, detail="Error alerting service not initialized")
    
    return await service.check_thresholds()


@router.post("/send-alert")
async def send_alert(force: bool = False):
    """Manually trigger an alert (for testing)"""
    service = get_error_alerting_service()
    if not service:
        raise HTTPException(status_code=503, detail="Error alerting service not initialized")
    
    check_result = await service.check_thresholds()
    
    if not check_result.get("triggered") and not force:
        return {"sent": False, "reason": "No thresholds exceeded", "check_result": check_result}
    
    triggers = check_result.get("triggers", [{"type": "manual_test", "threshold": 0, "actual": 0}])
    result = await service.send_alert(triggers, force=force)
    
    return {"sent": result.get("success", False), "result": result}


@router.post("/run-check")
async def run_check_and_alert():
    """Run threshold check and send alert if needed"""
    service = get_error_alerting_service()
    if not service:
        raise HTTPException(status_code=503, detail="Error alerting service not initialized")
    
    return await service.run_check_and_alert()


@router.get("/history")
async def get_alert_history(limit: int = 20):
    """Get alert history"""
    service = get_error_alerting_service()
    if not service:
        raise HTTPException(status_code=503, detail="Error alerting service not initialized")
    
    history = await service.get_alert_history(limit)
    return {"alerts": history, "count": len(history)}


@router.get("/status")
async def get_status():
    """Get alerting service status"""
    service = get_error_alerting_service()
    if not service:
        return {"initialized": False, "enabled": False}
    
    config = await service.get_config()
    return {
        "initialized": True,
        "enabled": config.get("enabled", False),
        "has_api_key": bool(config.get("resend_api_key")),
        "recipient_count": len(config.get("recipient_emails", [])),
        "thresholds": config.get("thresholds", {})
    }
