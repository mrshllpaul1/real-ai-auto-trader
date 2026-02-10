"""
On-Chain Data API Routes
========================
Whale tracking, exchange flows, and network metrics endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional


router = APIRouter(prefix="/on-chain", tags=["On-Chain Data"])

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


@router.get("/whale-activity")
async def get_whale_activity(db=Depends(get_database)):
    """Get comprehensive whale activity data including exchange flows and large transactions"""
    from services.onchain_data_service import get_onchain_service
    service = get_onchain_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="On-chain data service not available")
    
    return await service.get_whale_activity()


@router.get("/exchange-flows")
async def get_exchange_flows(db=Depends(get_database)):
    """Get detailed exchange inflow/outflow data"""
    from services.onchain_data_service import get_onchain_service
    service = get_onchain_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="On-chain data service not available")
    
    return await service.get_exchange_flows()


@router.get("/whale-transactions")
async def get_whale_transactions(limit: int = 20, db=Depends(get_database)):
    """Get recent large whale transactions"""
    from services.onchain_data_service import get_onchain_service
    service = get_onchain_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="On-chain data service not available")
    
    return await service.get_recent_whale_transactions(limit=limit)


@router.get("/network-metrics")
async def get_network_metrics(db=Depends(get_database)):
    """Get blockchain network metrics (active addresses, hash rate, etc.)"""
    from services.onchain_data_service import get_onchain_service
    service = get_onchain_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="On-chain data service not available")
    
    return await service.get_network_metrics()


@router.get("/whale-distribution")
async def get_whale_distribution(db=Depends(get_database)):
    """Get whale wallet distribution analysis"""
    from services.onchain_data_service import get_onchain_service
    service = get_onchain_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="On-chain data service not available")
    
    return await service.get_whale_wallet_distribution()


@router.post("/tracking/start")
async def start_tracking(db=Depends(get_database)):
    """Start real-time on-chain tracking"""
    from services.onchain_data_service import get_onchain_service
    service = get_onchain_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="On-chain data service not available")
    
    return await service.start_tracking()


@router.post("/tracking/stop")
async def stop_tracking(db=Depends(get_database)):
    """Stop real-time on-chain tracking"""
    from services.onchain_data_service import get_onchain_service
    service = get_onchain_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="On-chain data service not available")
    
    return await service.stop_tracking()


@router.get("/summary")
async def get_onchain_summary(db=Depends(get_database)):
    """Get a quick summary of on-chain data"""
    from services.onchain_data_service import get_onchain_service
    service = get_onchain_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="On-chain data service not available")
    
    activity = await service.get_whale_activity()
    
    return {
        "btc_price": activity.get("btc_price"),
        "exchange_flow_signal": activity.get("exchange_flows", {}).get("signal"),
        "net_flow_btc": activity.get("exchange_flows", {}).get("net_flow_btc"),
        "whale_sentiment": activity.get("analysis", {}).get("whale_sentiment", {}).get("sentiment"),
        "accumulation_score": activity.get("analysis", {}).get("accumulation_score"),
        "network_health": activity.get("analysis", {}).get("network_health"),
        "key_observations": activity.get("analysis", {}).get("key_observations", [])[:3]
    }
