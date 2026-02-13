from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()

class SendEmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    html_content: str

class TestGemEmailRequest(BaseModel):
    recipient: Optional[str] = None

@router.post("/send")
async def send_email(request: SendEmailRequest):
    """Send a custom email"""
    try:
        from services.email_service import get_email_service
        service = get_email_service()
        result = await service.send_email(
            request.recipient,
            request.subject,
            request.html_content
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-gem-alert")
async def test_gem_alert(request: TestGemEmailRequest):
    """Send a test HIGH priority gem alert email"""
    try:
        from services.email_service import get_email_service
        service = get_email_service()
        
        # Sample gem data for testing
        test_gem = {
            'symbol': 'PEPE',
            'match_score': 78,
            'alert_level': 'HIGH',
            'potential_multiplier': '50x-100x',
            'current_price': 0.00001234,
            'price_change_24h': 15.7,
            'volume_change_24h': 340,
            'market_cap': 5000000,
            'matching_signals': [
                {'signal': 'EXTREME_VOLUME'},
                {'signal': 'OVERSOLD_ACCUMULATION'},
                {'signal': 'MACD_BULLISH'},
                {'signal': 'MOMENTUM_BUILDING'},
                {'signal': 'WHALE_ACTIVITY'}
            ],
            'reasons': [
                'Historical pattern matches previous 10x+ runners',
                'Volume/price divergence indicates accumulation phase',
                'Social sentiment turning positive across platforms'
            ]
        }
        
        result = await service.send_high_priority_gem_alert(
            test_gem,
            request.recipient
        )
        
        return {
            "message": "Test gem alert email sent",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_email_settings():
    """Get current email settings"""
    from services.email_service import get_email_service
    service = get_email_service()
    
    return {
        "configured": bool(service.api_key),
        "sender_email": service.sender_email,
        "default_recipient": service.default_recipient
    }
