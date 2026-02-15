"""Live Calibration API Routes

Endpoints for recording real-time predictions and outcomes
to update ML analytics calibration data.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live-calibration", tags=["Live Calibration"])

_db = None
_calibration_service = None


def set_dependencies(db):
    """Set database dependency."""
    global _db, _calibration_service
    _db = db
    from services.live_calibration import set_live_calibration_db
    _calibration_service = set_live_calibration_db(db)


def get_calibration_service():
    """Get calibration service."""
    if _calibration_service is None:
        raise HTTPException(status_code=503, detail="Live calibration service not initialized")
    return _calibration_service


class PredictionRequest(BaseModel):
    """Request to record a prediction."""
    coin_id: str = Field(..., description="Coin symbol (e.g., BTC, ETH)")
    predicted_action: str = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., description="Confidence 0-1 or 0-100")
    model_name: str = Field(..., description="Model that made prediction")
    trade_id: Optional[str] = Field(default=None, description="Associated trade ID")
    entry_price: Optional[float] = Field(default=None, description="Entry price")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price")
    take_profit: Optional[float] = Field(default=None, description="Take profit price")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata")


class OutcomeRequest(BaseModel):
    """Request to record an outcome."""
    prediction_id: Optional[str] = Field(default=None, description="Prediction ID")
    trade_id: Optional[str] = Field(default=None, description="Trade ID")
    is_correct: Optional[bool] = Field(default=None, description="Was prediction correct?")
    actual_price: Optional[float] = Field(default=None, description="Actual price")
    exit_price: Optional[float] = Field(default=None, description="Exit price")
    pnl_percent: Optional[float] = Field(default=None, description="P/L percentage")
    pnl_usd: Optional[float] = Field(default=None, description="P/L in USD")


class TradeSignalRequest(BaseModel):
    """Request to record a trade with its signal."""
    trade_id: str
    coin_id: str
    action: str  # BUY, SELL
    confidence: float
    model_name: str
    entry_price: float
    amount: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Optional[Dict] = None


class ClosedTradeRequest(BaseModel):
    """Request to record a closed trade."""
    trade_id: str
    exit_price: float
    pnl_percent: Optional[float] = None
    pnl_usd: Optional[float] = None


@router.post("/record-prediction")
async def record_prediction(request: PredictionRequest):
    """Record an AI prediction for live calibration."""
    service = get_calibration_service()
    
    prediction_id = await service.record_prediction(
        coin_id=request.coin_id,
        predicted_action=request.predicted_action,
        confidence=request.confidence,
        model_name=request.model_name,
        trade_id=request.trade_id,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
        metadata=request.metadata
    )
    
    return {
        "success": True,
        "prediction_id": prediction_id,
        "message": f"Prediction recorded for {request.coin_id}"
    }


@router.post("/record-outcome")
async def record_outcome(request: OutcomeRequest):
    """Record the outcome of a prediction."""
    if not request.prediction_id and not request.trade_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide either prediction_id or trade_id"
        )
    
    service = get_calibration_service()
    
    result = await service.record_outcome(
        prediction_id=request.prediction_id,
        trade_id=request.trade_id,
        is_correct=request.is_correct,
        actual_price=request.actual_price,
        exit_price=request.exit_price,
        pnl_percent=request.pnl_percent,
        pnl_usd=request.pnl_usd
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/record-trade-signal")
async def record_trade_signal(request: TradeSignalRequest):
    """Record a trade executed based on an AI signal."""
    service = get_calibration_service()
    
    prediction_id = await service.record_trade_with_signal(
        trade_id=request.trade_id,
        coin_id=request.coin_id,
        action=request.action,
        confidence=request.confidence,
        model_name=request.model_name,
        entry_price=request.entry_price,
        amount=request.amount,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
        metadata=request.metadata
    )
    
    return {
        "success": True,
        "prediction_id": prediction_id,
        "trade_id": request.trade_id,
        "message": f"Trade signal recorded for calibration"
    }


@router.post("/record-closed-trade")
async def record_closed_trade(request: ClosedTradeRequest):
    """Record when a trade is closed to update calibration."""
    service = get_calibration_service()
    
    result = await service.record_closed_trade(
        trade_id=request.trade_id,
        exit_price=request.exit_price,
        pnl_percent=request.pnl_percent,
        pnl_usd=request.pnl_usd
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/pending")
async def get_pending_predictions(limit: int = 100):
    """Get predictions waiting for outcome verification."""
    service = get_calibration_service()
    predictions = await service.get_pending_predictions(limit)
    return {
        "pending_predictions": predictions,
        "count": len(predictions)
    }


@router.get("/outcomes")
async def get_recent_outcomes(limit: int = 100):
    """Get recent verified outcomes."""
    service = get_calibration_service()
    outcomes = await service.get_recent_outcomes(limit)
    return {
        "outcomes": outcomes,
        "count": len(outcomes)
    }


@router.get("/model-stats")
async def get_model_stats(model_name: Optional[str] = None):
    """Get live performance stats for models."""
    service = get_calibration_service()
    stats = await service.get_model_stats(model_name)
    return {
        "stats": stats,
        "model_filter": model_name or "all",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/auto-verify")
async def auto_verify_predictions(hours: int = 24, background_tasks: BackgroundTasks = None):
    """Auto-verify old predictions using market data."""
    service = get_calibration_service()
    result = await service.auto_verify_old_predictions(hours)
    return {
        **result,
        "message": f"Auto-verification completed"
    }


@router.get("/status")
async def get_calibration_status():
    """Get live calibration service status."""
    service = get_calibration_service()
    
    # Get counts from DB
    pending_count = await _db.live_calibration_predictions.count_documents({"status": "pending"})
    verified_count = await _db.live_calibration_predictions.count_documents({"status": "verified"})
    outcomes_count = await _db.live_calibration_outcomes.count_documents({})
    
    # Get calibrator stats
    from services.ml_analytics import get_confidence_calibrator
    calibrator = get_confidence_calibrator()
    accuracy_by_level = calibrator.get_accuracy_by_confidence_level()
    
    return {
        "status": "operational",
        "predictions": {
            "pending": pending_count,
            "verified": verified_count,
            "total": pending_count + verified_count
        },
        "outcomes_recorded": outcomes_count,
        "calibration": {
            "total_in_memory": accuracy_by_level.get("total_predictions", 0),
            "overall_accuracy": accuracy_by_level.get("overall_accuracy")
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ================== Webhook Integration ==================
# These endpoints can be called by trading engine when trades are executed/closed

@router.post("/webhook/trade-opened")
async def webhook_trade_opened(data: Dict[str, Any]):
    """Webhook called when a trade is opened.
    
    Expected data:
    {
        "trade_id": "uuid",
        "coin_id": "BTC",
        "action": "BUY",
        "entry_price": 95000,
        "amount": 0.1,
        "signal_confidence": 0.75,
        "signal_model": "tethys_ensemble"
    }
    """
    service = get_calibration_service()
    
    required = ["trade_id", "coin_id", "action", "entry_price"]
    for field in required:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    prediction_id = await service.record_trade_with_signal(
        trade_id=data["trade_id"],
        coin_id=data["coin_id"],
        action=data["action"],
        confidence=data.get("signal_confidence", 0.5),
        model_name=data.get("signal_model", "unknown"),
        entry_price=data["entry_price"],
        amount=data.get("amount", 0),
        stop_loss=data.get("stop_loss"),
        take_profit=data.get("take_profit"),
        metadata=data.get("metadata")
    )
    
    return {"success": True, "prediction_id": prediction_id}


@router.post("/webhook/trade-closed")
async def webhook_trade_closed(data: Dict[str, Any]):
    """Webhook called when a trade is closed.
    
    Expected data:
    {
        "trade_id": "uuid",
        "exit_price": 97000,
        "pnl_percent": 2.1,
        "pnl_usd": 200
    }
    """
    service = get_calibration_service()
    
    if "trade_id" not in data:
        raise HTTPException(status_code=400, detail="Missing required field: trade_id")
    
    result = await service.record_closed_trade(
        trade_id=data["trade_id"],
        exit_price=data.get("exit_price", 0),
        pnl_percent=data.get("pnl_percent"),
        pnl_usd=data.get("pnl_usd")
    )
    
    return result


@router.post("/bulk-generate")
async def bulk_generate_trades(
    num_trades: int = 500,
    include_outcomes: bool = True
):
    """Generate bulk trade data for calibration testing."""
    import random
    
    service = get_calibration_service()
    
    MODELS = {
        "tethys_ensemble": 0.73,
        "lstm_predictor": 0.68,
        "xgboost_classifier": 0.71,
        "gem_ml_dl": 0.65,
        "mtf_analyzer": 0.70,
        "sentiment_analyzer": 0.58,
        "whale_tracker": 0.75,
    }
    
    COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "LINK", "AVAX", "MATIC", "ATOM"]
    ACTIONS = ["BUY", "SELL", "HOLD"]
    
    predictions = []
    
    for i in range(num_trades):
        model_name = random.choice(list(MODELS.keys()))
        base_accuracy = MODELS[model_name]
        coin = random.choice(COINS)
        action = random.choice(ACTIONS)
        
        # Generate confidence with beta distribution for realistic spread
        confidence = random.betavariate(2, 2) * 0.65 + 0.30
        confidence = round(confidence, 3)
        
        trade_id = f"bulk_{datetime.utcnow().timestamp()}_{i}"
        
        prediction_id = await service.record_prediction(
            coin_id=coin,
            predicted_action=action,
            confidence=confidence,
            model_name=model_name,
            trade_id=trade_id,
            entry_price=random.uniform(100, 100000)
        )
        
        predictions.append({
            "prediction_id": prediction_id,
            "confidence": confidence,
            "base_accuracy": base_accuracy
        })
    
    outcomes_recorded = 0
    correct_count = 0
    
    if include_outcomes:
        for pred in predictions:
            confidence = pred["confidence"]
            base_accuracy = pred["base_accuracy"]
            
            # Well-calibrated: accuracy correlates with confidence
            actual_prob = confidence * base_accuracy / 0.7 + random.uniform(-0.05, 0.05)
            actual_prob = max(0.1, min(0.95, actual_prob))
            
            is_correct = random.random() < actual_prob
            if is_correct:
                correct_count += 1
            
            pnl = random.uniform(1, 15) if is_correct else random.uniform(-8, -1)
            
            await service.record_outcome(
                prediction_id=pred["prediction_id"],
                is_correct=is_correct,
                pnl_percent=round(pnl, 2)
            )
            outcomes_recorded += 1
    
    return {
        "predictions_generated": len(predictions),
        "outcomes_recorded": outcomes_recorded,
        "accuracy": round(correct_count / len(predictions) * 100, 2) if predictions else 0,
        "message": f"Generated {num_trades} trades for calibration"
    }
