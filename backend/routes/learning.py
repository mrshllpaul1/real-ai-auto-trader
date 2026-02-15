from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
from datetime import datetime, timezone

router = APIRouter()

# Global reference for learning service
_learning_service = None


def set_learning_service(learning_service):
    """Set the learning service reference"""
    global _learning_service
    _learning_service = learning_service


async def get_database():
    from server import db
    return db

async def get_learning_engine():
    from server import db
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized. Please wait for system startup.")
    try:
        from services.learning_engine import AILearningEngine
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Learning engine module unavailable: {exc}")
    try:
        return AILearningEngine(db)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to create learning engine: {exc}")

@router.get("/insights/{strategy_id}")
async def get_strategy_learning_insights(
    strategy_id: str,
    learning_engine = Depends(get_learning_engine)
):
    """Get learning insights for a specific strategy"""
    try:
        insights = await learning_engine.get_learning_insights(strategy_id)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/indicators/performance")
async def get_indicator_performance(
    learning_engine = Depends(get_learning_engine)
):
    """Get performance analysis of technical indicators"""
    try:
        # Add timeout to prevent hanging
        import asyncio
        try:
            indicators = await asyncio.wait_for(
                learning_engine.get_best_performing_indicators(),
                timeout=5.0
            )
            return {
                "indicators": indicators,
                "count": len(indicators)
            }
        except asyncio.TimeoutError:
            return {
                "indicators": [],
                "count": 0,
                "note": "Data loading in progress. Refresh in a few seconds."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/report")
async def get_learning_report(
    learning_engine = Depends(get_learning_engine)
):
    """Get comprehensive AI learning report"""
    try:
        # Add timeout to prevent hanging
        import asyncio
        try:
            report = await asyncio.wait_for(
                learning_engine.generate_learning_report(),
                timeout=5.0
            )
            return report
        except asyncio.TimeoutError:
            # Return basic report if timeout
            return {
                "total_strategies_evaluated": 0,
                "total_learning_samples": 0,
                "overall_accuracy": 0,
                "total_learned_profit_loss": 0,
                "best_performing_indicators": [],
                "learning_system_status": "initializing",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "note": "Data loading in progress. Refresh in a few seconds."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/train")
async def trigger_continuous_learning(
    learning_engine = Depends(get_learning_engine)
):
    """Manually trigger AI continuous learning update"""
    try:
        await learning_engine.continuous_learning_update()
        return {
            "message": "Continuous learning update completed",
            "status": "success"
        }
    except AttributeError as e:
        raise HTTPException(status_code=503, detail=f"Learning engine missing required method: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/record-outcome")
async def record_trade_outcome(
    strategy_id: str = None,
    trade_id: str = None,
    actual_profit_loss: float = 0,
    learning_engine = Depends(get_learning_engine),
    db = Depends(get_database)
):
    """Record actual trade outcome for learning"""
    try:
        if not strategy_id or not trade_id:
            raise HTTPException(status_code=400, detail="strategy_id and trade_id are required")
        
        # Get strategy and trade details
        strategy = await db.strategies.find_one({"strategy_id": strategy_id}, {"_id": 0})
        trade = await db.trades.find_one({"trade_id": trade_id}, {"_id": 0})
        
        if not strategy and not trade:
            # Create a basic learning record even without strategy/trade
            await learning_engine.record_strategy_outcome(
                strategy_id=strategy_id,
                predicted_action="UNKNOWN",
                actual_outcome="BUY" if actual_profit_loss > 0 else "SELL" if actual_profit_loss < 0 else "HOLD",
                profit_loss=actual_profit_loss,
                confidence_score=50
            )
            return {
                "message": "Trade outcome recorded for learning (basic)",
                "learning_applied": True
            }
        
        # Determine actual outcome
        actual_outcome = "BUY" if actual_profit_loss > 0 else "SELL" if actual_profit_loss < 0 else "HOLD"
        
        # Record for learning
        await learning_engine.record_strategy_outcome(
            strategy_id=strategy_id,
            predicted_action=strategy.get('technical_signal', 'HOLD') if strategy else 'UNKNOWN',
            actual_outcome=actual_outcome,
            profit_loss=actual_profit_loss,
            confidence_score=strategy.get('confidence_score', 50) if strategy else 50
        )
        
        return {
            "message": "Trade outcome recorded for learning",
            "learning_applied": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")



# ============================================
# Enhanced Learning Endpoints (Using Learning Service)
# ============================================

@router.get("/status")
async def get_learning_status():
    """Get current learning status and statistics"""
    if _learning_service is None:
        return {
            "learning_active": False,
            "stats": {
                "total_sessions": 0,
                "current_accuracy": 0
            },
            "message": "Learning service not initialized"
        }
    
    return await _learning_service.get_learning_status()


@router.post("/analyze")
async def analyze_recent_trades(days: int = 7):
    """Analyze recent trades for learning insights"""
    if _learning_service is None:
        raise HTTPException(status_code=503, detail="Learning service not initialized")
    
    return await _learning_service.learn_from_recent_trades(days=days)


@router.post("/cycle")
async def start_learning_cycle(background_tasks: BackgroundTasks):
    """Start a full learning cycle (analyze trades + retrain models)"""
    if _learning_service is None:
        raise HTTPException(status_code=503, detail="Learning service not initialized")
    
    if _learning_service.learning_active:
        return {
            "status": "already_running",
            "message": "A learning cycle is already in progress"
        }
    
    # Run learning cycle in background
    async def run_cycle():
        return await _learning_service.start_learning_cycle()
    
    background_tasks.add_task(run_cycle)
    
    return {
        "status": "started",
        "message": "Learning cycle started in background",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/recommendations")
async def get_recommendations():
    """Get AI recommendations for improving trading performance"""
    if _learning_service is None:
        return {
            "recommendations": [],
            "count": 0,
            "message": "Learning service not initialized"
        }
    
    recommendations = await _learning_service.get_learning_recommendations()
    
    return {
        "recommendations": recommendations,
        "count": len(recommendations),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/history")
async def get_learning_history(limit: int = 20):
    """Get recent learning session history"""
    if _learning_service is None:
        return {
            "history": [],
            "count": 0
        }
    
    history = _learning_service.get_learning_history(limit=limit)
    
    return {
        "history": history,
        "count": len(history),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
