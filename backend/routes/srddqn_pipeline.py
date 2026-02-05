"""
SRDDQN Training Pipeline API Routes
6-Phase comprehensive training system
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/srddqn-pipeline", tags=["SRDDQN Training Pipeline"])

_db = None
_pipeline = None


def set_dependencies(db, pipeline=None):
    global _db, _pipeline
    _db = db
    _pipeline = pipeline


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from services.srddqn_training_pipeline import get_training_pipeline
        _pipeline = get_training_pipeline()
    return _pipeline


class TrainingConfig(BaseModel):
    phase_1_epochs: int = 20
    phase_2_episodes: int = 100
    phase_3_test_episodes: int = 10


@router.get("/status")
async def get_pipeline_status():
    """Get comprehensive pipeline status"""
    try:
        pipeline = get_pipeline()
        return pipeline.get_status()
    except Exception as e:
        return {"error": str(e)}


@router.get("/phases")
async def get_phase_descriptions():
    """Get detailed description of all 6 phases"""
    return {
        "phases": {
            "phase_1": {
                "name": "Reward Modeling",
                "type": "Supervised Learning",
                "description": "Train Reward Network comparing predictions against expert-labeled rewards (Sharpe, Return, Risk)",
                "outputs": ["Trained reward network", "Multi-head predictions (Sharpe, Return, Risk, Confidence)"]
            },
            "phase_2": {
                "name": "Reinforcement Learning",
                "type": "Double DQN + Hybrid Rewards",
                "description": "Train policy using hybrid reward signal from trained reward network + extrinsic rewards",
                "components": [
                    "Epsilon-greedy action selection (buy, sell, hold)",
                    "Prioritized replay buffer",
                    "Soft target network updates"
                ]
            },
            "phase_3": {
                "name": "Validation & Robustness",
                "type": "Testing",
                "description": "Comprehensive validation on unseen data",
                "tests": [
                    "Out-of-sample testing",
                    "Market regime analysis (bull, bear, sideways, high-vol)",
                    "Sensitivity analysis (hyperparameters)",
                    "Benchmarking vs baselines"
                ]
            },
            "phase_4": {
                "name": "Deployment Configuration",
                "type": "Production Setup",
                "description": "Configure for live trading",
                "features": [
                    "Transaction cost & slippage modeling",
                    "Risk limits (position size, daily loss, drawdown)",
                    "Safety guards (circuit breakers, stop-losses)"
                ]
            },
            "phase_5": {
                "name": "Advanced Research",
                "type": "Enhancements",
                "description": "Cutting-edge improvements",
                "features": [
                    "Hierarchical reward shaping (dense + sparse)",
                    "Attention-based networks (Transformer-style)",
                    "Human-in-the-loop RL"
                ]
            },
            "phase_6": {
                "name": "Interpretability",
                "type": "Analysis",
                "description": "Understand and explain agent decisions",
                "methods": [
                    "Strategy deconstruction",
                    "Feature importance (SHAP-like)",
                    "Failure case analysis",
                    "Market condition correlation"
                ]
            }
        },
        "reference": "Huang et al. (2024) - MDPI Mathematics Journal"
    }


@router.post("/run-phase-1")
async def run_phase_1(epochs: int = 20, background_tasks: BackgroundTasks = None):
    """Phase 1: Reward Modeling (Supervised Learning)"""
    try:
        pipeline = get_pipeline()
        
        async def train_phase_1():
            # Get training data
            cursor = _db.price_history.find().sort("timestamp", -1).limit(5000)
            price_data = await cursor.to_list(length=5000)
            
            if not price_data:
                # Generate synthetic data
                np.random.seed(42)
                dates = pd.date_range(end=datetime.utcnow(), periods=5000, freq='H')
                prices = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.02, 5000))
                df = pd.DataFrame({
                    'timestamp': dates,
                    'close': prices,
                    'volume': np.random.uniform(1000, 10000, 5000),
                    'returns': np.concatenate([[0], np.diff(prices) / prices[:-1]])
                })
            else:
                df = pd.DataFrame(price_data)
            
            result = await pipeline.run_phase_1(df, epochs=epochs)
            
            await _db.srddqn_pipeline_results.insert_one({
                "phase": 1,
                "result": result,
                "created_at": datetime.utcnow()
            })
            
            logger.info(f"Phase 1 complete: {result}")
        
        if background_tasks:
            background_tasks.add_task(train_phase_1)
            return {"status": "started", "phase": 1, "epochs": epochs}
        else:
            await train_phase_1()
            return pipeline.phase_results.get('phase_1', {})
            
    except Exception as e:
        logger.error(f"Phase 1 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-phase-2")
async def run_phase_2(episodes: int = 100, background_tasks: BackgroundTasks = None):
    """Phase 2: Reinforcement Learning (Double DQN)"""
    try:
        pipeline = get_pipeline()
        
        if pipeline.current_phase < 1:
            raise HTTPException(status_code=400, detail="Must complete Phase 1 first")
        
        async def train_phase_2():
            from services.sb3_trading_agents import CryptoTradingEnv, prepare_training_data
            
            # Get data
            cursor = _db.price_history.find().sort("timestamp", -1).limit(3000)
            price_data = await cursor.to_list(length=3000)
            
            if not price_data:
                np.random.seed(42)
                dates = pd.date_range(end=datetime.utcnow(), periods=3000, freq='H')
                prices = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.02, 3000))
                price_data = [{'close': p, 'timestamp': d} for p, d in zip(prices, dates)]
            
            df = prepare_training_data(price_data)
            env = CryptoTradingEnv(df, reward_type='sharpe')
            
            result = await pipeline.run_phase_2(env, episodes=episodes)
            
            await _db.srddqn_pipeline_results.insert_one({
                "phase": 2,
                "result": result,
                "created_at": datetime.utcnow()
            })
        
        if background_tasks:
            background_tasks.add_task(train_phase_2)
            return {"status": "started", "phase": 2, "episodes": episodes}
        else:
            await train_phase_2()
            return pipeline.phase_results.get('phase_2', {})
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Phase 2 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-phase-3")
async def run_phase_3(test_episodes: int = 10):
    """Phase 3: Validation & Robustness Testing"""
    try:
        pipeline = get_pipeline()
        
        if pipeline.current_phase < 2:
            raise HTTPException(status_code=400, detail="Must complete Phase 2 first")
        
        from services.sb3_trading_agents import CryptoTradingEnv, prepare_training_data
        
        # Get test data (different period)
        cursor = _db.price_history.find().sort("timestamp", 1).limit(1000)  # Oldest data
        price_data = await cursor.to_list(length=1000)
        
        if not price_data:
            np.random.seed(123)  # Different seed for test
            dates = pd.date_range(end=datetime.utcnow() - pd.Timedelta(days=30), periods=1000, freq='H')
            prices = 45000 * np.cumprod(1 + np.random.normal(0.0002, 0.025, 1000))
            price_data = [{'close': p, 'timestamp': d} for p, d in zip(prices, dates)]
        
        df = prepare_training_data(price_data)
        test_env = CryptoTradingEnv(df, reward_type='sharpe')
        
        result = await pipeline.run_phase_3(test_env)
        
        await _db.srddqn_pipeline_results.insert_one({
            "phase": 3,
            "result": result,
            "created_at": datetime.utcnow()
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Phase 3 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-phase-4")
async def run_phase_4():
    """Phase 4: Deployment Configuration"""
    try:
        pipeline = get_pipeline()
        
        if pipeline.current_phase < 3:
            raise HTTPException(status_code=400, detail="Must complete Phase 3 first")
        
        result = pipeline.run_phase_4()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-phase-5")
async def run_phase_5():
    """Phase 5: Advanced Features"""
    try:
        pipeline = get_pipeline()
        
        result = pipeline.run_phase_5()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-phase-6")
async def run_phase_6():
    """Phase 6: Performance Attribution & Interpretability"""
    try:
        pipeline = get_pipeline()
        
        if pipeline.current_phase < 2:
            raise HTTPException(status_code=400, detail="Must have trained agent (Phase 2)")
        
        result = pipeline.run_phase_6()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-all")
async def run_all_phases(config: TrainingConfig = None, background_tasks: BackgroundTasks = None):
    """Run complete 6-phase training pipeline"""
    try:
        config = config or TrainingConfig()
        
        # Capture db reference for background task
        db = _db
        if db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        async def run_full_pipeline():
            pipeline = get_pipeline()
            
            logger.info("Starting full 6-phase SRDDQN training pipeline...")
            
            # Phase 1
            cursor = db.price_history.find().sort("timestamp", -1).limit(5000)
            price_data = await cursor.to_list(length=5000)
            if price_data:
                df = pd.DataFrame(price_data)
            else:
                np.random.seed(42)
                dates = pd.date_range(end=datetime.utcnow(), periods=5000, freq='H')
                prices = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.02, 5000))
                df = pd.DataFrame({'close': prices, 'timestamp': dates})
            
            await pipeline.run_phase_1(df, epochs=config.phase_1_epochs)
            
            # Phase 2
            from services.sb3_trading_agents import CryptoTradingEnv, prepare_training_data
            train_df = prepare_training_data(price_data if price_data else df.to_dict('records'))
            train_env = CryptoTradingEnv(train_df, reward_type='sharpe')
            await pipeline.run_phase_2(train_env, episodes=config.phase_2_episodes)
            
            # Phase 3
            test_env = CryptoTradingEnv(train_df.iloc[-500:].reset_index(drop=True), reward_type='sharpe')
            await pipeline.run_phase_3(test_env)
            
            # Phases 4-6
            pipeline.run_phase_4()
            pipeline.run_phase_5()
            pipeline.run_phase_6()
            
            # Save
            pipeline.save()
            
            await db.srddqn_pipeline_results.insert_one({
                "phase": "all",
                "status": pipeline.get_status(),
                "created_at": datetime.utcnow()
            })
            
            logger.info("Full pipeline training complete!")
        
        if background_tasks:
            background_tasks.add_task(run_full_pipeline)
            return {
                "status": "started",
                "message": "Full 6-phase pipeline started in background",
                "config": config.dict()
            }
        else:
            await run_full_pipeline()
            return get_pipeline().get_status()
            
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployment-config")
async def get_deployment_config():
    """Get deployment configuration"""
    try:
        pipeline = get_pipeline()
        return pipeline.deployment_config.to_dict()
    except Exception as e:
        return {"error": str(e)}


@router.post("/safety-check")
async def check_trade_safety(
    action: int,
    current_position: float,
    portfolio_value: float,
    current_volatility: float
):
    """Check if trade is allowed by safety guards"""
    try:
        pipeline = get_pipeline()
        
        if pipeline.safety_guard is None:
            return {"error": "Safety guard not initialized. Run Phase 4 first."}
        
        allowed, reason = pipeline.safety_guard.check_trade_allowed(
            action, current_position, portfolio_value, current_volatility
        )
        
        return {
            "allowed": allowed,
            "reason": reason,
            "action_name": ['strong_sell', 'sell', 'hold', 'buy', 'strong_buy'][action]
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/interpretability")
async def get_interpretability_report():
    """Get interpretability analysis"""
    try:
        pipeline = get_pipeline()
        
        if pipeline.performance_attributor is None:
            return {"error": "Interpretability not initialized. Run Phase 6 first."}
        
        return pipeline.performance_attributor.get_interpretability_report()
    except Exception as e:
        return {"error": str(e)}


@router.post("/save")
async def save_pipeline():
    """Save all models and state"""
    try:
        pipeline = get_pipeline()
        pipeline.save()
        return {"status": "saved", "path": pipeline.model_dir}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
