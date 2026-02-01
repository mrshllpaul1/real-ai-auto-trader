from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List

router = APIRouter()

class TrainingRequest(BaseModel):
    coins: List[str] = ['bitcoin', 'ethereum', 'solana']
    start_year: int = 2009

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
    """Train AI on historical data from 2009-2025"""
    try:
        # Start training in background
        background_tasks.add_task(
            trainer.train_on_historical_data,
            request.coins
        )
        
        return {
            "message": "Historical training started",
            "coins": request.coins,
            "period": f"{request.start_year}-2025",
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_training_status(
    db = Depends(get_database)
):
    """Get historical training status"""
    try:
        # Get latest training summary
        summary = await db.training_summary.find_one(
            {},
            {'_id': 0},
            sort=[('completed_at', -1)]
        )
        
        if not summary:
            return {
                "trained": False,
                "message": "No training completed yet"
            }
        
        return {
            "trained": True,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns/{coin_id}")
async def get_historical_patterns(
    coin_id: str,
    limit: int = 50,
    success_only: bool = False,
    db = Depends(get_database)
):
    """Get historical trading patterns for a coin"""
    try:
        query = {'coin_id': coin_id}
        if success_only:
            query['success'] = True
        
        patterns = await db.historical_patterns.find(
            query,
            {'_id': 0}
        ).sort('date', -1).limit(limit).to_list(limit)
        
        return {
            "coin_id": coin_id,
            "patterns": patterns,
            "count": len(patterns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar-patterns/{coin_id}")
async def find_similar_patterns(
    coin_id: str,
    rsi: float,
    macd: float,
    limit: int = 10,
    trainer = Depends(get_historical_trainer)
):
    """Find historical patterns similar to current market conditions"""
    try:
        current_indicators = {
            'rsi': rsi,
            'macd': macd,
            'volatility': 0
        }
        
        similar = await trainer.get_similar_historical_patterns(
            coin_id,
            current_indicators,
            limit
        )
        
        return {
            "coin_id": coin_id,
            "current_indicators": current_indicators,
            "similar_patterns": similar,
            "count": len(similar)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))