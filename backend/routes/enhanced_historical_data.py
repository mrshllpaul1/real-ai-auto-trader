"""
Enhanced Historical Data API Routes
Provides advanced historical market data features:
- Extended intraday data storage
- Volume profile analysis
- Data quality reports
- Historical event markers
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/enhanced-historical", tags=["Enhanced Historical Data"])

# Service dependency
_enhanced_service = None

def set_dependencies(enhanced_service):
    """Set service dependencies"""
    global _enhanced_service
    _enhanced_service = enhanced_service


# Request models
class EnhancedOHLCVRequest(BaseModel):
    symbol: str = Field(..., description="Coin symbol (BTC, ETH, etc.)")
    timeframe: str = Field(..., description="Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W)")
    candles: List[Dict[str, Any]] = Field(..., description="List of OHLCV candles")
    source: Optional[str] = Field("kraken", description="Data source")


class VolumeProfileRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")
    price_bins: Optional[int] = Field(50, description="Number of price levels")


class HistoricalEventRequest(BaseModel):
    symbol: str = Field(..., description="Coin symbol or 'GLOBAL'")
    timestamp: str = Field(..., description="Event timestamp (ISO format)")
    event_type: str = Field(..., description="Type: news, regulatory, technical, whale_movement, etc.")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    impact_score: Optional[float] = Field(0.5, ge=0, le=1, description="Impact score 0-1")
    source: Optional[str] = Field("manual", description="Event source")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# ============ ENDPOINTS ============

@router.get("/status")
async def get_service_status():
    """Get enhanced historical data service status"""
    if not _enhanced_service:
        return {
            "status": "not_initialized",
            "message": "Enhanced historical data service not initialized"
        }
    
    stats = await _enhanced_service.get_statistics()
    
    return {
        "status": "operational",
        "stats": stats,
        "features": [
            "Extended intraday data retention",
            "Volume profile analysis",
            "Data quality scoring",
            "Historical event markers"
        ]
    }


@router.post("/store-ohlcv")
async def store_enhanced_ohlcv(request: EnhancedOHLCVRequest):
    """
    Store OHLCV data with enhanced metrics.
    Automatically calculates quality scores, volatility, patterns, etc.
    """
    if not _enhanced_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    result = await _enhanced_service.store_enhanced_ohlcv(
        symbol=request.symbol,
        timeframe=request.timeframe,
        candles=request.candles,
        source=request.source
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/volume-profile")
async def calculate_volume_profile(request: VolumeProfileRequest):
    """
    Calculate volume profile for a time period.
    Shows volume distribution across price levels, POC, and value area.
    """
    if not _enhanced_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    
    result = await _enhanced_service.calculate_volume_profile(
        symbol=request.symbol,
        timeframe=request.timeframe,
        start_date=start_date,
        end_date=end_date,
        price_bins=request.price_bins
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/volume-profile/{symbol}/{timeframe}")
async def get_latest_volume_profile(
    symbol: str,
    timeframe: str,
    days: int = Query(7, description="Number of days to analyze")
):
    """
    Calculate and return volume profile for recent period.
    """
    if not _enhanced_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    result = await _enhanced_service.calculate_volume_profile(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        price_bins=50
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/events/add")
async def add_historical_event(request: HistoricalEventRequest):
    """
    Add a historical event marker.
    Use this to mark important market events (news, regulatory changes, etc.)
    """
    if not _enhanced_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        timestamp = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {e}")
    
    result = await _enhanced_service.add_historical_event(
        symbol=request.symbol,
        timestamp=timestamp,
        event_type=request.event_type,
        title=request.title,
        description=request.description,
        impact_score=request.impact_score,
        source=request.source,
        metadata=request.metadata
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/events/{symbol}")
async def get_historical_events(
    symbol: str,
    days: int = Query(30, description="Number of days to retrieve"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types")
):
    """
    Get historical events for a symbol.
    Includes both symbol-specific and global market events.
    """
    if not _enhanced_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    event_type_list = event_types.split(",") if event_types else None
    
    result = await _enhanced_service.get_events_for_period(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        event_types=event_type_list
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/quality-report/{symbol}/{timeframe}")
async def get_data_quality_report(
    symbol: str,
    timeframe: str,
    days: int = Query(30, description="Number of days to analyze")
):
    """
    Get data quality report for a symbol/timeframe.
    Analyzes completeness, consistency, and identifies issues.
    """
    if not _enhanced_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    result = await _enhanced_service.get_data_quality_report(
        symbol=symbol,
        timeframe=timeframe,
        days=days
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/stats")
async def get_enhanced_stats():
    """Get statistics about enhanced historical data"""
    if not _enhanced_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    return await _enhanced_service.get_statistics()


@router.get("/retention-periods")
async def get_retention_periods():
    """Get extended retention periods for each timeframe"""
    if not _enhanced_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    return {
        "retention_periods": _enhanced_service.EXTENDED_RETENTION,
        "improvements": {
            "1h": "Extended from 180 to 730 days (2 years)",
            "4h": "Extended from 365 to 1095 days (3 years)",
            "1m": "Extended from 7 to 30 days",
            "5m": "Extended from 14 to 60 days",
            "15m": "Extended from 30 to 90 days",
            "30m": "Extended from 60 to 180 days"
        },
        "benefits": [
            "Full strategy backtesting on short timeframes",
            "Better ML model training with more historical data",
            "Long-term pattern analysis on intraday data"
        ]
    }


@router.get("/features")
async def get_feature_list():
    """Get list of enhanced features"""
    return {
        "features": [
            {
                "name": "Extended Data Retention",
                "description": "Store 1h/4h data for 2-3 years instead of 6-12 months",
                "benefit": "Enable full strategy backtesting on short timeframes"
            },
            {
                "name": "Enhanced Metrics",
                "description": "Automatic calculation of volatility, patterns, body/wick ratios",
                "benefit": "Rich data for ML training and technical analysis"
            },
            {
                "name": "Volume Profile",
                "description": "Volume distribution analysis with POC and value area",
                "benefit": "Identify key support/resistance levels"
            },
            {
                "name": "Data Quality Scoring",
                "description": "Automatic validation and quality scoring (0-100)",
                "benefit": "Ensure reliable data for trading decisions"
            },
            {
                "name": "Historical Event Markers",
                "description": "Link market movements to real-world events",
                "benefit": "Understand price action context"
            },
            {
                "name": "Gap Detection",
                "description": "Identify missing data periods",
                "benefit": "Maintain data completeness"
            }
        ],
        "status": "operational"
    }
