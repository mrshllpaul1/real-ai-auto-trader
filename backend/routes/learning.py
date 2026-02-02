from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter()

async def get_database():
    from server import db
    return db

async def get_learning_engine():
    from services.learning_engine import AILearningEngine
    from server import db
    return AILearningEngine(db)

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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indicators/performance")
async def get_indicator_performance(
    learning_engine = Depends(get_learning_engine)
):
    """Get performance analysis of technical indicators"""
    try:
        indicators = await learning_engine.get_best_performing_indicators()
        return {
            "indicators": indicators,
            "count": len(indicators)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report")
async def get_learning_report(
    learning_engine = Depends(get_learning_engine)
):
    """Get comprehensive AI learning report"""
    try:
        report = await learning_engine.generate_learning_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))