"""
Trading Intelligence API Routes
Provides endpoints for the advanced ML/DL trading system
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trading-intelligence", tags=["Trading Intelligence"])

# Service references
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
        from services.trading_intelligence_engine import get_trading_intelligence
        _engine = get_trading_intelligence(_db)
    return _engine


def get_engine_if_exists():
    """Get engine only if already initialized (for status checks)"""
    return _engine


class TrainRequest(BaseModel):
    epochs: int = 50
    include_ensemble: bool = True
    include_time_series: bool = True
    include_finrl: bool = True


class PredictRequest(BaseModel):
    symbol: str = "BTC"
    lookback_days: int = 90


@router.get("/status")
async def get_engine_status():
    """Get Trading Intelligence Engine status (instant - no initialization)"""
    try:
        # Don't initialize on status call - just check if already initialized
        engine = get_engine_if_exists()
        if engine is None:
            return {
                "initialized": False, 
                "models": {
                    "ensemble": {"trained": False, "xgboost_available": True, "lightgbm_available": True},
                    "time_series": {"trained": False, "lstm": False, "gru": False, "transformer": False},
                    "finrl_agent": {"trained": False, "epsilon": 1.0, "memory_size": 0, "training_steps": 0}
                },
                "environment": {
                    "transaction_cost": 0.001,
                    "slippage": 0.0005,
                    "max_position": 0.25
                },
                "training_results": {},
                "message": "Engine not initialized - click Initialize to start"
            }
        
        return engine.get_status()
    except Exception as e:
        logger.error(f"Error getting engine status: {e}")
        return {
            "initialized": False, 
            "error": str(e),
            "models": {
                "ensemble": {"trained": False},
                "time_series": {"trained": False},
                "finrl_agent": {"trained": False}
            },
            "environment": {},
            "training_results": {}
        }


@router.post("/initialize")
async def initialize_engine():
    """Initialize the Trading Intelligence Engine"""
    try:
        from services.trading_intelligence_engine import initialize_trading_intelligence
        global _engine
        _engine = await initialize_trading_intelligence(_db)
        
        return {
            "status": "initialized",
            "message": "Trading Intelligence Engine initialized",
            "components": {
                "data_preprocessing": {
                    "scalers": ["RobustScaler", "StandardScaler", "MinMaxScaler"],
                    "features": "Automated feature engineering with 40+ indicators"
                },
                "ensemble_models": {
                    "xgboost": "Gradient boosting for direction prediction",
                    "lightgbm": "Fast gradient boosting for high-frequency signals"
                },
                "time_series_models": {
                    "lstm": "Bidirectional LSTM with attention",
                    "gru": "Residual GRU for sequence modeling",
                    "transformer": "Multi-head attention transformer"
                },
                "finrl_agent": {
                    "architecture": "Dueling Double DQN",
                    "environment": "Realistic simulation with costs/slippage"
                },
                "pca_features": "15-component dimensionality reduction"
            }
        }
    except Exception as e:
        logger.error(f"Engine initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_models(request: TrainRequest, background_tasks: BackgroundTasks):
    """Train all ML/DL models"""
    try:
        engine = get_engine()
        if engine is None:
            raise HTTPException(status_code=400, detail="Engine not initialized")
        
        async def train_task():
            # Fetch historical price data
            cursor = _db.price_history.find().sort("timestamp", -1).limit(5000)
            price_data = await cursor.to_list(length=5000)
            
            if not price_data:
                # Generate synthetic data for demo
                import numpy as np
                np.random.seed(42)
                dates = pd.date_range(end=datetime.utcnow(), periods=1000, freq='H')
                prices = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.02, 1000))
                price_data = [
                    {
                        'timestamp': d,
                        'open': p * (1 + np.random.uniform(-0.01, 0.01)),
                        'high': p * (1 + np.random.uniform(0, 0.02)),
                        'low': p * (1 - np.random.uniform(0, 0.02)),
                        'close': p,
                        'volume': np.random.uniform(1000, 10000)
                    }
                    for d, p in zip(dates, prices)
                ]
            
            await engine.train_all(price_data, epochs=request.epochs)
        
        background_tasks.add_task(train_task)
        
        return {
            "status": "training_started",
            "epochs": request.epochs,
            "models": {
                "ensemble": request.include_ensemble,
                "time_series": request.include_time_series,
                "finrl": request.include_finrl
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict")
async def get_prediction(request: PredictRequest):
    """Get trading signal prediction"""
    try:
        engine = get_engine()
        if engine is None:
            raise HTTPException(status_code=400, detail="Engine not initialized")
        
        # Fetch recent data
        cursor = _db.price_history.find(
            {"symbol": request.symbol}
        ).sort("timestamp", -1).limit(request.lookback_days * 24)
        
        price_data = await cursor.to_list(length=request.lookback_days * 24)
        
        if not price_data:
            # Generate synthetic data
            import numpy as np
            np.random.seed(42)
            prices = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.02, 200))
            price_data = [
                {
                    'open': p * 0.99,
                    'high': p * 1.01,
                    'low': p * 0.98,
                    'close': p,
                    'volume': 5000
                }
                for p in prices
            ]
        
        df = pd.DataFrame(price_data)
        signal = engine.get_trading_signal(df)
        
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ensemble/status")
async def get_ensemble_status():
    """Get ensemble model status"""
    try:
        engine = get_engine()
        if engine is None:
            return {"error": "Engine not initialized"}
        
        return {
            "trained": engine.ensemble.is_trained,
            "xgboost_available": engine.ensemble.xgb_model is not None,
            "lightgbm_available": engine.ensemble.lgb_model is not None,
            "feature_importance": engine.ensemble.feature_importance
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/time-series/status")
async def get_time_series_status():
    """Get time series models status"""
    try:
        engine = get_engine()
        if engine is None:
            return {"error": "Engine not initialized"}
        
        return {
            "trained": engine.time_series.is_trained,
            "lstm_ready": engine.time_series.lstm_model is not None,
            "gru_ready": engine.time_series.gru_model is not None,
            "transformer_ready": engine.time_series.transformer_model is not None,
            "sequence_length": engine.time_series.sequence_length,
            "forecast_horizon": engine.time_series.forecast_horizon,
            "training_history": engine.time_series.training_history
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/finrl/status")
async def get_finrl_status():
    """Get FinRL agent status"""
    try:
        engine = get_engine()
        if engine is None:
            return {"error": "Engine not initialized"}
        
        return {
            "trained": engine.finrl_agent.is_trained,
            "epsilon": engine.finrl_agent.epsilon,
            "memory_size": len(engine.finrl_agent.memory),
            "training_steps": engine.finrl_agent.training_steps,
            "state_dim": engine.finrl_agent.state_dim,
            "action_dim": engine.finrl_agent.action_dim
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/environment/config")
async def get_environment_config():
    """Get trading environment configuration"""
    try:
        engine = get_engine()
        if engine is None:
            return {"error": "Engine not initialized"}
        
        env = engine.environment
        return {
            "initial_capital": env.initial_capital,
            "transaction_cost_pct": env.transaction_cost_pct,
            "slippage_pct": env.slippage_pct,
            "max_position_pct": env.max_position_pct,
            "leverage": env.leverage,
            "current_metrics": env.get_metrics() if env.portfolio_history else {}
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/environment/simulate")
async def run_simulation(days: int = 30, episodes: int = 10):
    """Run environment simulation"""
    try:
        engine = get_engine()
        if engine is None:
            raise HTTPException(status_code=400, detail="Engine not initialized")
        
        import numpy as np
        
        # Generate synthetic price data for simulation
        np.random.seed(42)
        prices = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.02, days * 24))
        
        # Generate features
        df = pd.DataFrame({
            'close': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'volume': np.random.uniform(1000, 10000, len(prices))
        })
        
        features_df = engine.feature_engineer.extract_features(df)
        features, _ = engine.feature_engineer.extract_pca_features(features_df)
        
        # Run simulation
        engine.environment.prices = prices
        engine.environment.features = features
        
        results = await engine.finrl_agent.train(engine.environment, episodes=episodes)
        
        return {
            "simulation_days": days,
            "episodes": episodes,
            "results": results,
            "final_metrics": engine.environment.get_metrics()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components")
async def get_components_info():
    """Get detailed information about all components"""
    return {
        "architecture": "Advanced ML/DL Trading Intelligence",
        "components": {
            "data_preprocessing": {
                "type": "Multi-stage Pipeline",
                "scalers": ["RobustScaler", "StandardScaler", "MinMaxScaler"],
                "features": [
                    "Outlier-resistant scaling",
                    "Online normalization",
                    "Missing value imputation"
                ]
            },
            "feature_engineering": {
                "type": "Comprehensive Technical Analysis",
                "indicators": [
                    "Price momentum (1, 5, 10, 20 day)",
                    "Volatility (5, 20, 60 day)",
                    "Moving Averages (5, 10, 20, 50, 100)",
                    "MACD with histogram",
                    "RSI (7, 14, 21)",
                    "Bollinger Bands",
                    "Stochastic Oscillator",
                    "ATR (14)",
                    "Volume ratios"
                ],
                "pca_components": 15
            },
            "ensemble_models": {
                "xgboost": {
                    "type": "Gradient Boosting",
                    "objective": "Binary classification",
                    "regularization": "L1 + L2"
                },
                "lightgbm": {
                    "type": "Light Gradient Boosting",
                    "boosting": "GBDT",
                    "features": "Feature/bagging fraction"
                }
            },
            "time_series_models": {
                "lstm": {
                    "type": "Bidirectional LSTM",
                    "layers": "Stacked with attention",
                    "outputs": "Direction + Magnitude"
                },
                "gru": {
                    "type": "Residual GRU",
                    "features": "Skip connections"
                },
                "transformer": {
                    "type": "Multi-head Attention",
                    "blocks": 3,
                    "heads": 4
                }
            },
            "finrl_agent": {
                "type": "Dueling Double DQN",
                "features": [
                    "Prioritized experience replay",
                    "Soft target updates",
                    "Epsilon-greedy exploration"
                ],
                "actions": ["strong_sell", "sell", "hold", "buy", "strong_buy"]
            },
            "trading_environment": {
                "type": "Realistic Market Simulation",
                "features": [
                    "Transaction costs (0.1%)",
                    "Slippage modeling (0.05%)",
                    "Position size limits",
                    "Risk-adjusted rewards"
                ]
            }
        },
        "training_flow": [
            "1. Data preprocessing and scaling",
            "2. Feature engineering (40+ indicators)",
            "3. PCA dimensionality reduction",
            "4. Ensemble model training",
            "5. Time series model training",
            "6. FinRL agent training in simulated environment",
            "7. Continuous backtesting validation"
        ]
    }
