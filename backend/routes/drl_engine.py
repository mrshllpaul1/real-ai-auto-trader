"""
Deep Reinforcement Learning API Routes
Provides endpoints for the integrated DL + DRL trading system
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drl-engine", tags=["Deep RL Engine"])

# Service reference
_db = None
_engine = None


def set_dependencies(db, engine=None):
    """Set service dependencies"""
    global _db, _engine
    _db = db
    _engine = engine


def get_engine():
    """Get or create engine"""
    global _engine
    if _engine is None:
        from services.deep_rl_trading_engine import get_drl_engine
        _engine = get_drl_engine(_db)
    return _engine


class TrainRequest(BaseModel):
    episodes: int = 100
    include_lstm: bool = True
    include_dqn: bool = True


class SignalRequest(BaseModel):
    symbol: str
    price_change_24h: float = 0
    price_change_7d: float = 0
    volume_24h: float = 0
    market_cap: float = 0
    rsi: float = 50
    recent_news: List[str] = []


class ExecuteRequest(BaseModel):
    symbol: str
    action: str  # buy, sell, strong_buy, strong_sell
    position_size_pct: float = 10
    mode: str = "paper"  # paper or real


@router.get("/status")
async def get_engine_status():
    """Get Deep RL Engine status"""
    try:
        engine = get_engine()
        if engine is None:
            return {
                "initialized": False, 
                "lstm_trained": False,
                "dqn_epsilon": 1.0,
                "dqn_memory_size": 0,
                "hft_metrics": {
                    "total_orders": 0,
                    "successful_orders": 0,
                    "failed_orders": 0,
                    "avg_latency_ms": 0,
                    "total_slippage": 0,
                    "avg_slippage_pct": 0.0,
                    "success_rate": 0.0,
                    "queue_size": 0
                },
                "backtest_approved": False,
                "latest_backtest": {"message": "No backtest run yet"},
                "message": "Engine not initialized - click Initialize to start"
            }
        
        return engine.get_status()
    except Exception as e:
        logger.error(f"Error getting engine status: {e}")
        return {
            "initialized": False, 
            "error": str(e),
            "lstm_trained": False,
            "dqn_epsilon": 1.0,
            "dqn_memory_size": 0,
            "hft_metrics": {
                "total_orders": 0,
                "successful_orders": 0,
                "failed_orders": 0,
                "avg_latency_ms": 0
            },
            "backtest_approved": False
        }


@router.post("/initialize")
async def initialize_engine():
    """Initialize the Deep RL Engine"""
    try:
        from services.deep_rl_trading_engine import initialize_drl_engine
        global _engine
        _engine = await initialize_drl_engine(_db)
        
        return {
            "status": "initialized",
            "message": "Deep RL Trading Engine initialized successfully",
            "components": [
                "LSTM Time Series Predictor",
                "DQN Trading Agent (Dueling + Double)",
                "PPO Position Sizer",
                "Deep Sentiment Analyzer",
                "PCA Feature Reducer",
                "HFT Execution Engine",
                "Continuous Backtester"
            ]
        }
    except Exception as e:
        logger.error(f"Engine initialization error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/train")
async def train_models(request: TrainRequest, background_tasks: BackgroundTasks):
    """Train DL/DRL models in background"""
    try:
        engine = get_engine()
        if engine is None:
            raise HTTPException(status_code=400, detail="Engine not initialized")
        
        # Start training in background
        async def train_task():
            # Get historical data from database
            cursor = _db.price_history.find().sort("timestamp", -1).limit(5000)
            historical_data = await cursor.to_list(length=5000)
            
            if not historical_data:
                logger.warning("No historical data available for training")
                return
            
            await engine.train_all_models(historical_data)
        
        background_tasks.add_task(train_task)
        
        return {
            "status": "training_started",
            "message": f"Training {request.episodes} episodes in background",
            "components": {
                "lstm": request.include_lstm,
                "dqn": request.include_dqn
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/signal")
async def get_trading_signal(request: SignalRequest):
    """Get trading signal for a symbol"""
    try:
        engine = get_engine()
        if engine is None:
            raise HTTPException(status_code=400, detail="Engine not initialized")
        
        market_data = {
            "price_change_24h": request.price_change_24h,
            "price_change_7d": request.price_change_7d,
            "volume_24h": request.volume_24h,
            "market_cap": request.market_cap,
            "rsi": request.rsi,
            "recent_news": request.recent_news
        }
        
        signal = await engine.get_trading_signal(request.symbol, market_data)
        
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/execute")
async def execute_trade(request: ExecuteRequest):
    """Execute trading signal via HFT engine"""
    try:
        engine = get_engine()
        if engine is None:
            raise HTTPException(status_code=400, detail="Engine not initialized")
        
        signal = {
            "symbol": request.symbol,
            "action": request.action,
            "position_size_pct": request.position_size_pct,
            "execution_ready": True  # Manual execution
        }
        
        result = await engine.execute_signal(signal, mode=request.mode)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/hft/metrics")
async def get_hft_metrics():
    """Get HFT execution metrics"""
    try:
        engine = get_engine()
        if engine is None:
            return {"error": "Engine not initialized"}
        
        return engine.hft_engine.get_metrics()
    except Exception as e:
        return {"error": str(e)}


@router.get("/backtest/status")
async def get_backtest_status():
    """Get continuous backtest status"""
    try:
        engine = get_engine()
        if engine is None:
            return {"error": "Engine not initialized"}
        
        return {
            "approved_for_live": engine.backtester.is_live_approved(),
            "latest_results": engine.backtester.get_latest_results()
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/backtest/run")
async def run_backtest(days: int = 30, background_tasks: BackgroundTasks = None):
    """Run manual backtest"""
    try:
        engine = get_engine()
        if engine is None:
            raise HTTPException(status_code=400, detail="Engine not initialized")
        
        if background_tasks:
            background_tasks.add_task(engine.backtester.run_backtest, days)
            return {"status": "started", "period_days": days}
        else:
            results = await engine.backtester.run_backtest(days)
            return results
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/sentiment/analyze")
async def analyze_sentiment(texts: List[str]):
    """Analyze sentiment of texts"""
    try:
        engine = get_engine()
        if engine is None:
            raise HTTPException(status_code=400, detail="Engine not initialized")
        
        result = await engine.sentiment_analyzer.analyze_multiple(texts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/components")
async def get_components_info():
    """Get information about DRL engine components"""
    return {
        "architecture": "Deep Learning + Deep Reinforcement Learning",
        "components": {
            "lstm_predictor": {
                "type": "Bidirectional LSTM with Attention",
                "purpose": "Time series price prediction",
                "features": ["Multi-head attention", "Stacked BiLSTM", "Technical indicators"]
            },
            "dqn_agent": {
                "type": "Dueling Double DQN",
                "purpose": "Trading action decisions",
                "features": ["Prioritized replay", "Soft target updates", "5 action space"]
            },
            "ppo_sizer": {
                "type": "Proximal Policy Optimization",
                "purpose": "Position sizing",
                "features": ["Continuous action space", "Gaussian policy"]
            },
            "sentiment_analyzer": {
                "type": "Transformer-style with Attention",
                "purpose": "News/social sentiment analysis",
                "features": ["Multi-source aggregation", "Market impact scoring"]
            },
            "pca_reducer": {
                "type": "Principal Component Analysis",
                "purpose": "Feature dimensionality reduction",
                "features": ["Noise reduction", "Pattern extraction"]
            },
            "hft_engine": {
                "type": "High-Frequency Trading Executor",
                "purpose": "Low-latency order execution",
                "features": ["Order queuing", "Slippage control", "Retry logic"]
            },
            "backtester": {
                "type": "Continuous Strategy Validator",
                "purpose": "Validate before live trading",
                "features": ["Auto validation", "Sharpe/Sortino metrics", "Drawdown limits"]
            }
        },
        "no_traditional_ml": True,
        "note": "Pure Deep Learning + Deep Reinforcement Learning architecture"
    }
