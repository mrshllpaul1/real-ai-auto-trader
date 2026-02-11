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
    COMPREHENSIVE TRAINING: Train ALL AI systems with REAL market data + SENTIMENT.
    - Historical Trainer (patterns + hidden gems)
    - Enhanced Historical Trainer (technical indicators + gems)
    - Profitable Gems Trainer (success patterns)
    - AI Weekly Trainer (sentiment-enhanced selection)
    
    All training uses REAL market data from Twelve Data API.
    NOW INCLUDES: AI News Sentiment Analysis integration.
    """
    from services.historical_trainer import HistoricalTrainer
    from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
    from services.ai_weekly_trainer import AIWeeklyTrainer
    from services.dynamic_coin_universe import get_training_coins
    from services.training_progress_manager import get_progress_manager
    import uuid
    
    try:
        # Create unique task ID
        task_id = f"train-all-{uuid.uuid4().hex[:8]}"
        progress_manager = get_progress_manager()
        
        historical_trainer = HistoricalTrainer(db)
        enhanced_trainer = EnhancedHistoricalTrainer(db)
        weekly_trainer = AIWeeklyTrainer(db)
        
        # Get ALL coins from dynamic universe (no artificial limit)
        try:
            all_coins = await get_training_coins()
        except Exception:
            all_coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot', 
                        'avalanche', 'chainlink', 'polygon', 'dogecoin', 'shiba-inu',
                        'ripple', 'litecoin', 'binancecoin', 'tron', 'uniswap',
                        'cosmos', 'stellar', 'monero', 'near', 'aptos']
        
        # Use ALL coins - no limit!
        training_coins = all_coins
        total_coins = len(training_coins)
        
        # Create progress task with total items = coins * 3 phases
        progress_manager.create_task(
            task_id=task_id,
            task_type="train-all",
            total_items=total_coins * 3,  # 3 coin-based training phases
            total_steps=4  # 4 major steps
        )
        
        async def train_with_progress():
            """Background task with granular per-coin progress tracking"""
            try:
                await progress_manager.start_task(task_id, f"Starting training on {total_coins} coins...")
                
                items_done = 0
                
                # Step 1: Historical Training (per-coin progress)
                await progress_manager.update_progress(
                    task_id, 
                    progress=0, 
                    message="Phase 1/4: Historical Pattern Training",
                    steps_completed=0
                )
                
                for i, coin in enumerate(training_coins):
                    await progress_manager.update_progress(
                        task_id,
                        current_item=f"Historical: {coin}",
                        items_processed=items_done + i + 1,
                        message=f"Phase 1/4: Training {coin} ({i+1}/{total_coins})"
                    )
                    try:
                        await historical_trainer.train_on_historical_data([coin], 2020, True)
                    except Exception as e:
                        logger.warning(f"Historical training failed for {coin}: {e}")
                
                items_done += total_coins
                
                # Step 2: Enhanced Historical Training (per-coin progress)
                await progress_manager.update_progress(
                    task_id, 
                    progress=33, 
                    message="Phase 2/4: Technical Indicator Training",
                    steps_completed=1
                )
                
                for i, coin in enumerate(training_coins):
                    await progress_manager.update_progress(
                        task_id,
                        current_item=f"Technical: {coin}",
                        items_processed=items_done + i + 1,
                        message=f"Phase 2/4: Training {coin} ({i+1}/{total_coins})"
                    )
                    try:
                        await enhanced_trainer.train_with_real_data([coin])
                    except Exception as e:
                        logger.warning(f"Enhanced training failed for {coin}: {e}")
                
                items_done += total_coins
                
                # Step 3: Profitable Gems Training (per-coin progress)
                await progress_manager.update_progress(
                    task_id, 
                    progress=66, 
                    message="Phase 3/4: Gem Pattern Training",
                    steps_completed=2
                )
                
                for i, coin in enumerate(training_coins):
                    await progress_manager.update_progress(
                        task_id,
                        current_item=f"Gems: {coin}",
                        items_processed=items_done + i + 1,
                        message=f"Phase 3/4: Training {coin} ({i+1}/{total_coins})"
                    )
                    try:
                        await historical_trainer.train_profitable_gems([coin], 2.0, 2020)
                    except Exception as e:
                        logger.warning(f"Gems training failed for {coin}: {e}")
                
                items_done += total_coins
                
                # Step 4: Save Weights
                await progress_manager.update_progress(
                    task_id, 
                    progress=95, 
                    message="Phase 4/4: Saving AI Weights...",
                    steps_completed=3,
                    current_item="Saving weights"
                )
                await weekly_trainer.save_weights()
                
                # Complete
                await progress_manager.complete_task(
                    task_id,
                    result={
                        "coins_trained": total_coins,
                        "systems": ["historical", "enhanced", "gems", "weights"]
                    },
                    message=f"Completed training on {total_coins} coins"
                )
                
            except Exception as e:
                await progress_manager.fail_task(task_id, str(e))
        
        # Queue the background task
        background_tasks.add_task(train_with_progress)
        
        return {
            "task_id": task_id,
            "message": f"ALL AI training started on {total_coins} coins",
            "systems": [
                "Historical Trainer (patterns + hidden gems)",
                "Enhanced Historical Trainer (technical indicators)",
                "Profitable Gems Trainer (success patterns)",
                "AI Weekly Trainer (sentiment-enhanced, NEW weights)"
            ],
            "new_parameters": {
                "sentiment_weight": 0.12,
                "momentum_weight": 0.18,
                "volatility_weight": 0.13,
                "volume_weight": 0.18,
                "trend_weight": 0.18,
                "historical_weight": 0.13,
                "category_weight": 0.08,
                "total": "100%"
            },
            "coins": training_coins[:20],  # Show first 20 in response
            "coin_count": total_coins,
            "data_source": "REAL_MARKET_DATA_ONLY (Twelve Data API)",
            "sentiment_source": "AI News Analysis (CryptoPanic + LLM)",
            "status": "processing",
            "progress_endpoint": f"/api/training-progress/task/{task_id}",
            "websocket_endpoint": "/api/training-progress/ws",
            "note": f"Training {total_coins} coins. Use WebSocket for real-time updates."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UniverseTrainingRequest(BaseModel):
    max_coins: int = 50
    start_year: int = 2020
    include_discovered: bool = True


@router.post("/train-universe")
async def train_with_full_universe(
    request: UniverseTrainingRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """
    FULL UNIVERSE TRAINING: Train AI on ALL coins from dynamic universe.
    Includes AI-discovered coins for comprehensive learning.
    Uses REAL market data from Twelve Data API + CryptoPanic sentiment.
    """
    from services.historical_trainer import HistoricalTrainer
    from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
    from services.ai_weekly_trainer import AIWeeklyTrainer
    from services.dynamic_coin_universe import get_training_coins, get_universe_manager
    
    try:
        historical_trainer = HistoricalTrainer(db)
        enhanced_trainer = EnhancedHistoricalTrainer(db)
        weekly_trainer = AIWeeklyTrainer(db)
        
        # Get ALL coins from dynamic universe
        try:
            all_coins = await get_training_coins()
            universe_mgr = get_universe_manager()
            
            # Get AI-discovered coins if requested
            discovered_coins = []
            if request.include_discovered and universe_mgr:
                discovered = await universe_mgr.get_ai_discovered_coins()
                discovered_coins = [c['coin_id'] for c in discovered if c.get('active', True)]
        except Exception as e:
            all_coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
            discovered_coins = []
        
        # Use requested number of coins (up to max available)
        training_coins = all_coins[:request.max_coins]
        
        # Ensure AI-discovered coins are included
        for coin in discovered_coins:
            if coin not in training_coins:
                training_coins.append(coin)
        
        # Queue all training tasks
        background_tasks.add_task(
            historical_trainer.train_on_historical_data,
            training_coins, request.start_year, True
        )
        
        background_tasks.add_task(
            enhanced_trainer.train_with_real_data,
            training_coins
        )
        
        background_tasks.add_task(
            historical_trainer.train_profitable_gems,
            training_coins, 2.0, request.start_year
        )
        
        # Save updated weights with sentiment parameters
        background_tasks.add_task(
            weekly_trainer.save_weights
        )
        
        return {
            "message": "FULL UNIVERSE TRAINING started with REAL DATA + SENTIMENT",
            "systems": [
                "Historical Trainer (patterns + hidden gems)",
                "Enhanced Historical Trainer (technical indicators)",
                "Profitable Gems Trainer (success patterns)",
                "AI Weekly Trainer (sentiment-enhanced)"
            ],
            "training_parameters": {
                "sentiment_weight": 0.12,
                "momentum_weight": 0.18,
                "volatility_weight": 0.13,
                "volume_weight": 0.18,
                "trend_weight": 0.18,
                "historical_weight": 0.13,
                "category_weight": 0.08,
            },
            "coins": training_coins,
            "coin_count": len(training_coins),
            "ai_discovered_included": discovered_coins,
            "start_year": request.start_year,
            "data_source": "REAL_MARKET_DATA_ONLY (Twelve Data API)",
            "sentiment_source": "AI News Analysis (CryptoPanic + LLM)",
            "status": "processing",
            "note": f"Training {len(training_coins)} coins. May take 10-15 minutes. Check /status endpoint."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-weights")
async def get_ai_weights(db = Depends(get_database)):
    """
    Get current AI training weights including sentiment parameters.
    Shows how the AI weighs different factors in coin selection.
    """
    from services.ai_weekly_trainer import AIWeeklyTrainer
    
    try:
        trainer = AIWeeklyTrainer(db)
        await trainer.load_weights()
        
        weights = trainer.learned_weights
        
        return {
            "selection_weights": {
                "momentum": weights.get('momentum', 0.18),
                "volatility": weights.get('volatility', 0.13),
                "volume": weights.get('volume', 0.18),
                "trend": weights.get('trend', 0.18),
                "historical_performance": weights.get('historical_performance', 0.13),
                "category_preference": weights.get('category_preference', 0.08),
                "sentiment": weights.get('sentiment', 0.12),
            },
            "signal_weights": weights.get('signal_weights', {}),
            "sentiment_tracking": weights.get('sentiment_accuracy', {}),
            "top_category_scores": dict(sorted(
                weights.get('category_scores', {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "training_stats": {
                "total_weeks_trained": trainer.total_weeks,
                "winning_weeks": trainer.winning_weeks,
                "win_rate": f"{(trainer.winning_weeks / max(1, trainer.total_weeks) * 100):.1f}%"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-weights")
async def update_ai_weights(
    weights: dict,
    db = Depends(get_database)
):
    """
    Update AI selection weights manually.
    Use with caution - affects all trading decisions.
    """
    from services.ai_weekly_trainer import AIWeeklyTrainer
    
    try:
        trainer = AIWeeklyTrainer(db)
        await trainer.load_weights()
        
        # Update only provided weights
        for key, value in weights.items():
            if key in trainer.learned_weights:
                trainer.learned_weights[key] = value
        
        # Save updated weights
        await trainer.save_weights()
        
        return {
            "message": "AI weights updated successfully",
            "updated_weights": weights,
            "current_weights": trainer.learned_weights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
