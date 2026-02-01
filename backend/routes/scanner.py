from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Global scanner instance
_scanner = None
_notification_service = None
_email_service = None

class ScannerConfig(BaseModel):
    interval_seconds: int = 300
    coins: Optional[List[str]] = None

async def get_database():
    from server import db
    return db

async def get_notification_service():
    global _notification_service
    from server import db
    from services.notification_service import NotificationService
    if _notification_service is None:
        _notification_service = NotificationService(db)
    return _notification_service

async def get_email_service():
    global _email_service
    from services.email_service import get_email_service as get_email_svc
    if _email_service is None:
        _email_service = get_email_svc()
    return _email_service

async def get_scanner():
    global _scanner
    from services.gem_scanner import GemScanner
    from server import db
    if _scanner is None:
        _scanner = GemScanner(db)
    return _scanner

@router.post("/start")
async def start_scanner(
    config: ScannerConfig,
    background_tasks: BackgroundTasks,
    scanner = Depends(get_scanner)
):
    """
    Start the real-time hidden gem scanner
    Monitors market conditions and alerts when 10x-100x patterns are detected
    """
    try:
        if scanner.is_running:
            return {
                "message": "Scanner is already running",
                "status": "running",
                "interval": scanner.scan_interval
            }
        
        if config.coins:
            scanner.monitored_coins = config.coins
        
        background_tasks.add_task(scanner.start_scanner, config.interval_seconds)
        
        return {
            "message": "Hidden gem scanner started",
            "interval_seconds": config.interval_seconds,
            "monitoring_coins": len(scanner.monitored_coins),
            "status": "starting"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_scanner(scanner = Depends(get_scanner)):
    """Stop the hidden gem scanner"""
    try:
        scanner.stop_scanner()
        return {"message": "Scanner stopped", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_scanner_status(scanner = Depends(get_scanner)):
    """Get current scanner status"""
    try:
        return await scanner.get_scanner_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan-now")
async def scan_now(scanner = Depends(get_scanner)):
    """
    Perform an immediate market scan
    Returns all current hidden gem alerts
    Sends SMS notification for HIGH priority gems
    """
    try:
        alerts = await scanner.scan_market()
        
        high = [a for a in alerts if a['alert_level'] == 'HIGH']
        medium = [a for a in alerts if a['alert_level'] == 'MEDIUM']
        low = [a for a in alerts if a['alert_level'] == 'LOW']
        
        # Send SMS for HIGH priority alerts
        sms_sent = []
        if high:
            notification_service = await get_notification_service()
            for gem in high[:3]:  # Limit to top 3 HIGH alerts
                result = await notification_service.notify_high_priority_gem(gem)
                if result.get('success'):
                    sms_sent.append(gem['symbol'])
        
        return {
            "scan_time": alerts[0]['scanned_at'] if alerts else None,
            "total_alerts": len(alerts),
            "high_alerts": len(high),
            "medium_alerts": len(medium),
            "low_alerts": len(low),
            "sms_sent_for": sms_sent,
            "top_gems": alerts[:10],
            "all_alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(
    min_score: int = 0,
    alert_level: Optional[str] = None,
    scanner = Depends(get_scanner)
):
    """
    Get current hidden gem alerts
    Filter by minimum score or alert level (HIGH, MEDIUM, LOW)
    """
    try:
        alerts = await scanner.get_current_alerts(min_score)
        
        if alert_level:
            alerts = [a for a in alerts if a['alert_level'] == alert_level.upper()]
        
        return {
            "count": len(alerts),
            "filter": {"min_score": min_score, "alert_level": alert_level},
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/high")
async def get_high_alerts(scanner = Depends(get_scanner)):
    """Get only HIGH priority hidden gem alerts (best opportunities)"""
    try:
        alerts = await scanner.get_current_alerts(0)
        high_alerts = [a for a in alerts if a['alert_level'] == 'HIGH']
        
        return {
            "count": len(high_alerts),
            "potential": "10x-100x",
            "alerts": high_alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/{coin_id}")
async def get_coin_alerts(coin_id: str, scanner = Depends(get_scanner)):
    """Get alerts for a specific coin"""
    try:
        alerts = await scanner.get_current_alerts(0)
        coin_alert = next((a for a in alerts if a['coin_id'] == coin_id), None)
        
        if not coin_alert:
            return {"message": f"No alerts for {coin_id}", "coin_id": coin_id}
        
        return coin_alert
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_alert_history(
    coin_id: Optional[str] = None,
    limit: int = 50,
    scanner = Depends(get_scanner)
):
    """Get historical alerts"""
    try:
        history = await scanner.get_alert_history(coin_id, limit)
        return {
            "count": len(history),
            "coin_filter": coin_id,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coins")
async def get_monitored_coins(scanner = Depends(get_scanner)):
    """Get list of monitored coins"""
    return {
        "count": len(scanner.monitored_coins),
        "coins": scanner.monitored_coins
    }

@router.post("/coins")
async def set_monitored_coins(coins: List[str], scanner = Depends(get_scanner)):
    """Update the list of monitored coins"""
    try:
        scanner.monitored_coins = coins
        return {
            "message": "Monitored coins updated",
            "count": len(coins),
            "coins": coins
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
