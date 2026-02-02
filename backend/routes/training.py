from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class TrainingRequest(BaseModel):
    coins: List[str] = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot', 'avalanche', 'chainlink']
    start_year: int = 2009
    include_hidden_gems: bool = True

class ProfitableGemsRequest(BaseModel):
    coins: List[str] = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot', 'avalanche', 'chainlink', 'polygon', 'uniswap', 'litecoin']
    min_profit_multiplier: float = 2.0
    start_year: int = 2009

class EnhancedTrainingRequest(BaseModel):
    coins: List[str] = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']

async def get_database():
    from server import db
    return db

async def get_historical_trainer():
    from services.historical_trainer import HistoricalTrainer
    from server import db
    return HistoricalTrainer(db)

async def get_enhanced_trainer():
    from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
    from server import db
    return EnhancedHistoricalTrainer(db)

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

@router.post("/train-profitable-gems")
async def train_profitable_gems(
    request: ProfitableGemsRequest,
    background_tasks: BackgroundTasks,
    trainer = Depends(get_historical_trainer)
):
    """
    ADVANCED TRAINING: Focus specifically on PROFITABLE hidden gems
    Learns the exact conditions that led to successful 2x-100x+ gains
    """
    try:
        background_tasks.add_task(
            trainer.train_profitable_gems,
            request.coins,
            request.min_profit_multiplier,
            request.start_year
        )
        
        return {
            "message": "Profitable gems training started",
            "focus": f"Learning patterns for {request.min_profit_multiplier}x+ gains",
            "coins": request.coins,
            "status": "processing",
            "note": "This training analyzes ONLY successful gems to learn what makes them profitable."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profitable-gems-status")
async def get_profitable_gems_status(trainer = Depends(get_historical_trainer)):
    """Get status of profitable gems training"""
    try:
        return await trainer.get_profitable_gems_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profitable-gem-signals")
async def get_profitable_gem_signals(trainer = Depends(get_historical_trainer)):
    """
    Get the AI's learned signals for finding profitable hidden gems
    Returns the most effective entry conditions based on historical success
    """
    try:
        return await trainer.get_profitable_gem_signals()
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



@router.post("/train-enhanced")
async def train_enhanced_historical(
    request: EnhancedTrainingRequest,
    background_tasks: BackgroundTasks,
    trainer = Depends(get_enhanced_trainer)
):
    """
    ENHANCED TRAINING: Train AI with REAL market data and news sentiment.
    Uses Twelve Data API for historical OHLCV data.
    NEVER uses simulated data - only real market data.
    """
    try:
        background_tasks.add_task(
            trainer.train_with_real_data,
            request.coins
        )
        
        return {
            "message": "Enhanced AI training started with REAL DATA",
            "coins": request.coins,
            "data_source": "REAL_MARKET_DATA_ONLY",
            "status": "processing",
            "note": "Training uses Twelve Data API for real OHLCV data. Check /status endpoint for progress."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-all")
async def train_all_systems(
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """
    COMPREHENSIVE TRAINING: Train ALL AI systems with REAL market data.
    - Historical Trainer (patterns + hidden gems)
    - Enhanced Historical Trainer (technical indicators + gems)
    - Profitable Gems Trainer (success patterns)
    
    All training uses REAL market data from Twelve Data API.
    """
    from services.historical_trainer import HistoricalTrainer
    from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
    
    try:
        historical_trainer = HistoricalTrainer(db)
        enhanced_trainer = EnhancedHistoricalTrainer(db)
        
        coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
        
        # Queue all training tasks
        background_tasks.add_task(
            historical_trainer.train_on_historical_data,
            coins, 2020, True
        )
        
        background_tasks.add_task(
            enhanced_trainer.train_with_real_data,
            coins
        )
        
        background_tasks.add_task(
            historical_trainer.train_profitable_gems,
            coins, 2.0, 2020
        )
        
        return {
            "message": "ALL AI training systems started with REAL DATA",
            "systems": [
                "Historical Trainer (patterns + hidden gems)",
                "Enhanced Historical Trainer (technical indicators)",
                "Profitable Gems Trainer (success patterns)"
            ],
            "coins": coins,
            "data_source": "REAL_MARKET_DATA_ONLY (Twelve Data API)",
            "status": "processing",
            "note": "Training may take 5-10 minutes. Check /status endpoint for progress."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
