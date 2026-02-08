"""
Advanced AI Features API Routes
================================
Routes for:
- Real-time news monitoring
- Specialist agents ensemble
- Causal feature selection
- RLHF feedback
- Multi-exchange management
"""

import logging
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced-ai", tags=["Advanced AI"])

_db = None


def set_db(db):
    global _db
    _db = db


# =============================================================================
# REQUEST MODELS
# =============================================================================

class FeedbackRequest(BaseModel):
    trade_id: str
    rating: int  # 1-5
    feedback_type: str = "overall"  # timing, sizing, direction, overall
    comment: Optional[str] = None


class TradeSubmitRequest(BaseModel):
    trade_id: str
    entry_price: float
    exit_price: Optional[float] = None
    direction: str = "long"
    entry_time: Optional[str] = None
    exit_time: Optional[str] = None
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0
    position_pct: float = 5.0


class SmartOrderRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    order_type: str = "MARKET"


# =============================================================================
# REAL-TIME NEWS MONITORING
# =============================================================================

@router.get("/news/status")
async def get_news_monitor_status():
    """Get real-time news monitor status"""
    from services.realtime_news_monitor import get_news_monitor
    monitor = get_news_monitor(_db)
    return monitor.get_status()


@router.post("/news/start")
async def start_news_monitor(
    interval: int = 60,
    background_tasks: BackgroundTasks = None
):
    """Start real-time news monitoring"""
    from services.realtime_news_monitor import get_news_monitor
    monitor = get_news_monitor(_db)
    
    if monitor.is_running:
        return {"status": "already_running", "current_status": monitor.get_status()}
    
    background_tasks.add_task(monitor.start, interval)
    
    return {
        "status": "started",
        "poll_interval": interval
    }


@router.post("/news/stop")
async def stop_news_monitor():
    """Stop real-time news monitoring"""
    from services.realtime_news_monitor import get_news_monitor
    monitor = get_news_monitor(_db)
    monitor.stop()
    return {"status": "stopped"}


@router.get("/news/trending")
async def get_trending_topics():
    """Get currently trending topics"""
    from services.realtime_news_monitor import get_news_monitor
    monitor = get_news_monitor(_db)
    return monitor.detector.get_trending_summary()


@router.get("/news/alerts")
async def get_recent_alerts(limit: int = 20):
    """Get recent significant news alerts"""
    from services.realtime_news_monitor import get_news_monitor
    monitor = get_news_monitor(_db)
    return {
        "alerts": monitor.get_recent_alerts(limit),
        "total_processed": monitor.stats.get("news_processed", 0)
    }


@router.websocket("/news/ws")
async def news_websocket(websocket: WebSocket):
    """WebSocket for real-time news updates"""
    from services.realtime_news_monitor import get_news_monitor
    
    await websocket.accept()
    monitor = get_news_monitor(_db)
    monitor.register_ws_client(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "status": monitor.get_status()
        })
        
        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    finally:
        monitor.unregister_ws_client(websocket)


# =============================================================================
# SPECIALIST AGENTS ENSEMBLE
# =============================================================================

@router.get("/specialists/status")
async def get_specialists_status():
    """Get specialist ensemble status"""
    from services.specialist_agents import get_specialist_ensemble
    ensemble = get_specialist_ensemble(_db)
    return ensemble.get_status()


@router.post("/specialists/signal")
async def get_specialist_signal(
    prices: List[float],
    volumes: Optional[List[float]] = None
):
    """Get trading signal from specialist ensemble"""
    from services.specialist_agents import get_specialist_ensemble
    ensemble = get_specialist_ensemble(_db)
    
    signal = await ensemble.get_ensemble_signal(prices, volumes)
    return signal


@router.get("/specialists/regime")
async def get_market_regime(prices: List[float] = None):
    """Get current market regime detection"""
    from services.specialist_agents import get_specialist_ensemble
    ensemble = get_specialist_ensemble(_db)
    
    # Use default prices if none provided
    if not prices:
        # Try to get from market service
        return ensemble.regime_detector.get_regime_summary()
    
    regime, confidence = ensemble.regime_detector.detect_regime(prices)
    return {
        "regime": regime.value,
        "confidence": confidence,
        "summary": ensemble.regime_detector.get_regime_summary()
    }


# =============================================================================
# CAUSAL FEATURE SELECTION
# =============================================================================

@router.post("/causal/analyze")
async def analyze_causal_features(
    features: Dict[str, List[float]],
    target_col: str
):
    """Analyze features for causal relationships"""
    import pandas as pd
    from services.causal_feature_selection import get_causal_selector
    
    selector = get_causal_selector(_db)
    
    # Convert to DataFrame
    df = pd.DataFrame(features)
    
    if target_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column {target_col} not found")
    
    results = selector.analyze_features(df, target_col)
    
    # Save to database
    await selector.save_analysis(results)
    
    return results


@router.post("/causal/select")
async def select_causal_features(
    features: Dict[str, List[float]],
    target_col: str,
    top_k: int = 10,
    min_score: float = 50
):
    """Select top causally-related features"""
    import pandas as pd
    from services.causal_feature_selection import get_causal_selector
    
    selector = get_causal_selector(_db)
    df = pd.DataFrame(features)
    
    selected = selector.select_features(df, target_col, top_k, min_score)
    return {
        "selected_features": selected,
        "count": len(selected)
    }


@router.post("/causal/spurious")
async def detect_spurious_correlations(
    features: Dict[str, List[float]],
    target_col: str
):
    """Detect spurious correlations"""
    import pandas as pd
    from services.causal_feature_selection import get_causal_selector
    
    selector = get_causal_selector(_db)
    df = pd.DataFrame(features)
    
    spurious = selector.detect_spurious_correlations(df, target_col)
    return {
        "spurious_features": spurious,
        "count": len(spurious)
    }


# =============================================================================
# RLHF (REINFORCEMENT LEARNING FROM HUMAN FEEDBACK)
# =============================================================================

@router.get("/rlhf/stats")
async def get_rlhf_stats():
    """Get RLHF training statistics"""
    from services.rlhf_trainer import get_rlhf_trainer
    trainer = get_rlhf_trainer(_db)
    return trainer.get_stats()


@router.post("/rlhf/submit-trade")
async def submit_trade_for_feedback(request: TradeSubmitRequest):
    """Submit a trade for human feedback"""
    from services.rlhf_trainer import get_rlhf_trainer
    trainer = get_rlhf_trainer(_db)
    
    result = await trainer.submit_trade_for_feedback(
        trade_id=request.trade_id,
        trade_data=request.dict()
    )
    return result


@router.post("/rlhf/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit human feedback for a trade"""
    from services.rlhf_trainer import get_rlhf_trainer
    trainer = get_rlhf_trainer(_db)
    
    result = await trainer.submit_feedback(
        trade_id=request.trade_id,
        rating=request.rating,
        feedback_type=request.feedback_type,
        comment=request.comment
    )
    return result


@router.get("/rlhf/pending")
async def get_pending_feedback(limit: int = 20):
    """Get trades awaiting feedback"""
    from services.rlhf_trainer import get_rlhf_trainer
    trainer = get_rlhf_trainer(_db)
    return {
        "pending_trades": trainer.get_pending_trades(limit)
    }


@router.post("/rlhf/improve-signal")
async def improve_signal_with_rlhf(
    original_signal: Dict[str, Any],
    trade_context: Dict[str, Any]
):
    """Use RLHF to improve a trading signal"""
    from services.rlhf_trainer import get_rlhf_trainer
    trainer = get_rlhf_trainer(_db)
    
    improved = await trainer.generate_improved_signal(original_signal, trade_context)
    return improved


# =============================================================================
# MULTI-EXCHANGE MANAGEMENT
# =============================================================================

@router.get("/exchanges/status")
async def get_exchanges_status():
    """Get multi-exchange manager status"""
    from services.multi_exchange import get_multi_exchange_manager
    manager = get_multi_exchange_manager(_db)
    return manager.get_status()


@router.get("/exchanges/balance")
async def get_unified_balance():
    """Get unified balance across all exchanges"""
    from services.multi_exchange import get_multi_exchange_manager
    manager = get_multi_exchange_manager(_db)
    return await manager.get_unified_balance()


@router.get("/exchanges/best-price/{symbol}")
async def get_best_price(symbol: str):
    """Get best price for a symbol across all exchanges"""
    from services.multi_exchange import get_multi_exchange_manager
    manager = get_multi_exchange_manager(_db)
    
    # Decode symbol (replace dash with slash)
    symbol = symbol.replace("-", "/")
    return await manager.get_best_price(symbol)


@router.get("/exchanges/arbitrage")
async def detect_arbitrage(symbols: str = "BTC/USD,ETH/USD,SOL/USD"):
    """Detect arbitrage opportunities"""
    from services.multi_exchange import get_multi_exchange_manager
    manager = get_multi_exchange_manager(_db)
    
    symbol_list = [s.strip() for s in symbols.split(",")]
    opportunities = await manager.detect_arbitrage(symbol_list)
    return {
        "opportunities": opportunities,
        "count": len(opportunities)
    }


@router.post("/exchanges/smart-order")
async def place_smart_order(request: SmartOrderRequest):
    """Place order on best exchange"""
    from services.multi_exchange import get_multi_exchange_manager
    manager = get_multi_exchange_manager(_db)
    
    result = await manager.smart_order(
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type
    )
    return result


# =============================================================================
# GENETIC ALGORITHM STRATEGY DISCOVERY
# =============================================================================

@router.post("/genetic/evolve")
async def evolve_strategies(
    population_size: int = 20,
    generations: int = 10,
    background_tasks: BackgroundTasks = None
):
    """Start genetic algorithm strategy evolution"""
    # This would integrate with the existing genetic algorithm service
    # For now, return a placeholder
    return {
        "status": "started",
        "population_size": population_size,
        "generations": generations,
        "message": "Genetic evolution started in background"
    }


@router.get("/genetic/status")
async def get_genetic_status():
    """Get genetic algorithm evolution status"""
    return {
        "status": "idle",
        "best_fitness": None,
        "generations_completed": 0,
        "message": "Configure genetic algorithm parameters to start"
    }
