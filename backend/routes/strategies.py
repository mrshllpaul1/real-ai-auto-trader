from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()

class StrategyRequest(BaseModel):
    user_id: str
    coin_pairs: List[str]

async def get_database():
    from server import db
    return db

async def get_strategy_engine():
    from services.strategy_engine import StrategyEngine
    return StrategyEngine()

async def get_market_service():
    from services.market_data_service import MarketDataService
    return MarketDataService()

@router.post("/generate")
async def generate_strategies(
    request: StrategyRequest,
    db = Depends(get_database),
    strategy_engine = Depends(get_strategy_engine),
    market_service = Depends(get_market_service)
):
    """Generate AI-powered trading strategies with learning enhancement"""
    try:
        from services.learning_engine import AILearningEngine
        learning_engine = AILearningEngine(db)
        
        # Get historical data for each coin
        historical_data = {}
        
        for pair in request.coin_pairs:
            coin_id = pair.split('/')[0].lower()
            
            # Get historical data
            hist_data = await market_service.get_historical_data(coin_id, days=30)
            
            # Get current market data
            market_data = await market_service.get_coin_price([coin_id])
            
            historical_data[coin_id] = {
                **hist_data,
                **market_data.get(coin_id, {})
            }
        
        # Generate strategies with learning
        strategies = []
        for pair in request.coin_pairs:
            coin_id = pair.split('/')[0].lower()
            
            try:
                # Get historical prices
                coin_data = historical_data.get(coin_id, {}).get('prices', [])
                
                if coin_data:
                    # Calculate technical indicators
                    indicators = strategy_engine.calculate_technical_indicators(coin_data)
                    
                    # Generate rule-based signals
                    technical_analysis = strategy_engine.generate_rule_based_signals(indicators)
                    
                    # Get market data
                    market_data = historical_data.get(coin_id, {})
                    
                    # Get learning insights for this coin (check if we have past strategies)
                    past_strategies = await db.strategies.find(
                        {"coin_id": coin_id}
                    ).sort("created_at", -1).limit(1).to_list(1)
                    
                    learning_data = None
                    if past_strategies:
                        learning_data = await learning_engine.get_learning_insights(past_strategies[0]['strategy_id'])
                    
                    # Generate AI strategy with learning
                    ai_strategy = await strategy_engine.generate_ai_strategy(
                        coin_id,
                        technical_analysis,
                        market_data,
                        learning_data=learning_data
                    )
                    
                    strategies.append(ai_strategy)
            except Exception as e:
                print(f"Error generating strategy for {coin_id}: {str(e)}")
                continue
        
        # Sort strategies by confidence score
        strategies.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # Store strategies in database
        for strategy in strategies:
            strategy['user_id'] = request.user_id
            await db.strategies.insert_one(strategy)
        
        return {
            "strategies": strategies,
            "count": len(strategies),
            "learning_enabled": True,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list/{user_id}")
async def get_strategies(
    user_id: str,
    status: str = "active",
    limit: int = 10,
    db = Depends(get_database)
):
    """Get strategies for a user"""
    try:
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        strategies = await db.strategies.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {
            "strategies": strategies,
            "count": len(strategies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detail/{strategy_id}")
async def get_strategy_detail(
    strategy_id: str,
    db = Depends(get_database)
):
    """Get detailed information about a specific strategy"""
    try:
        strategy = await db.strategies.find_one({"strategy_id": strategy_id}, {"_id": 0})
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/activate/{strategy_id}")
async def activate_strategy(
    strategy_id: str,
    user_id: str,
    db = Depends(get_database)
):
    """Activate a strategy for auto-trading"""
    try:
        result = await db.strategies.update_one(
            {"strategy_id": strategy_id, "user_id": user_id},
            {"$set": {"status": "active", "activated_at": datetime.now().isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Strategy not found or already active")
        
        return {"message": "Strategy activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deactivate/{strategy_id}")
async def deactivate_strategy(
    strategy_id: str,
    user_id: str,
    db = Depends(get_database)
):
    """Deactivate a strategy"""
    try:
        result = await db.strategies.update_one(
            {"strategy_id": strategy_id, "user_id": user_id},
            {"$set": {"status": "inactive", "deactivated_at": datetime.now().isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {"message": "Strategy deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))