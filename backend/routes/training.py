from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class TrainingRequest(BaseModel):
    coins: List[str] = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot', 'avalanche', 'chainlink']
    start_year: int = 2009
    include_hidden_gems: bool = True

async def get_database():
    from server import db
    return db

async def get_historical_trainer():
    from services.historical_trainer import HistoricalTrainer
    from server import db
    return HistoricalTrainer(db)

@router.post("/train")
async def train_on_historical_data(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    trainer = Depends(get_historical_trainer)
):
    """
    Train AI on historical data from 2009-present
    Includes hidden gems detection for 10-100x opportunities
    """
    try:
        background_tasks.add_task(
            trainer.train_on_historical_data,
            request.coins,
            request.start_year,
            request.include_hidden_gems
        )
        
        return {
            "message": "Comprehensive AI training started",
            "coins": request.coins,
            "period": f"{request.start_year}-2025",
            "hidden_gems_detection": request.include_hidden_gems,
            "status": "processing",
            "note": "Training may take several minutes. Check /status endpoint for progress."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_training_status(trainer = Depends(get_historical_trainer)):
    """Get comprehensive training status including hidden gems stats"""
    try:
        status = await trainer.get_training_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hidden-gems")
async def get_hidden_gems(
    min_multiplier: float = 3.0,
    limit: int = 20,
    trainer = Depends(get_historical_trainer)
):
    """
    Get historical hidden gem patterns (10-100x opportunities)
    These are coins that showed massive gains under specific conditions
    """
    try:
        gems = await trainer.get_hidden_gems(min_multiplier, limit)
        
        return {
            "hidden_gems": gems,
            "count": len(gems),
            "min_multiplier": min_multiplier,
            "note": "These patterns indicate conditions that preceded major price increases"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/find-current-gems")
async def find_current_hidden_gems(
    market_data: dict,
    trainer = Depends(get_historical_trainer)
):
    """
    Analyze current market data to find potential hidden gems
    Compares current conditions against historical 10-100x patterns
    """
    try:
        potential_gems = await trainer.find_current_hidden_gems(market_data)
        
        return {
            "potential_gems": potential_gems,
            "count": len(potential_gems),
            "analysis_time": "real-time",
            "warning": "High risk investment. Past patterns do not guarantee future results."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns/{coin_id}")
async def get_historical_patterns(
    coin_id: str,
    limit: int = 50,
    success_only: bool = False,
    pattern_type: Optional[str] = None,
    db = Depends(get_database)
):
    """Get historical trading patterns for a coin"""
    try:
        query = {'coin_id': coin_id}
        if success_only:
            query['success'] = True
        if pattern_type:
            query['pattern_type'] = pattern_type
        
        patterns = await db.historical_patterns.find(
            query,
            {'_id': 0}
        ).sort('date', -1).limit(limit).to_list(limit)
        
        # Calculate stats
        total = len(patterns)
        successful = sum(1 for p in patterns if p.get('success', False))
        
        return {
            "coin_id": coin_id,
            "patterns": patterns,
            "count": total,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "pattern_types": list(set(p.get('pattern_type', 'unknown') for p in patterns))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar-patterns/{coin_id}")
async def find_similar_patterns(
    coin_id: str,
    rsi: float = 50,
    volume_ratio: float = 1.0,
    limit: int = 10,
    trainer = Depends(get_historical_trainer)
):
    """Find historical patterns similar to current market conditions"""
    try:
        current_indicators = {
            'rsi': rsi,
            'volume_ratio': volume_ratio
        }
        
        similar = await trainer.get_similar_patterns(
            coin_id,
            current_indicators,
            limit
        )
        
        return {
            "coin_id": coin_id,
            "current_indicators": current_indicators,
            "similar_patterns": similar,
            "count": len(similar),
            "recommendation": "Use these patterns to inform trading decisions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gem-signals")
async def get_gem_entry_signals(db = Depends(get_database)):
    """
    Get the most successful entry signals for hidden gems
    Based on historical analysis of 10-100x opportunities
    """
    try:
        gems = await db.hidden_gems.find({}, {'_id': 0}).to_list(1000)
        
        if not gems:
            return {
                "signals": [],
                "message": "No hidden gem data available. Run training first."
            }
        
        # Aggregate entry signals
        signal_stats = {}
        for gem in gems:
            multiplier = gem.get('multiplier', 1)
            for signal in gem.get('entry_signals', []):
                if signal not in signal_stats:
                    signal_stats[signal] = {'count': 0, 'total_multiplier': 0, 'avg_multiplier': 0}
                signal_stats[signal]['count'] += 1
                signal_stats[signal]['total_multiplier'] += multiplier
        
        # Calculate averages
        for signal in signal_stats:
            signal_stats[signal]['avg_multiplier'] = (
                signal_stats[signal]['total_multiplier'] / signal_stats[signal]['count']
            )
        
        # Sort by effectiveness
        sorted_signals = sorted(
            [{'signal': k, **v} for k, v in signal_stats.items()],
            key=lambda x: x['avg_multiplier'],
            reverse=True
        )
        
        return {
            "signals": sorted_signals,
            "total_gems_analyzed": len(gems),
            "interpretation": "Higher avg_multiplier indicates more effective entry signals"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
