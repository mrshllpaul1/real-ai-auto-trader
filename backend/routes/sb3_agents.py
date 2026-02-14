"""
Stable-Baselines3 Trading Agents API Routes
Provides endpoints for professional DRL trading agents.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sb3-agents", tags=["SB3 Trading Agents"])

# Service references
_db = None
_manager = None


def set_dependencies(db, manager=None):
    """Set service dependencies"""
    global _db, _manager
    _db = db
    _manager = manager


def get_manager():
    """Get or create manager"""
    global _manager
    if _manager is None:
        from services.sb3_trading_agents import get_sb3_manager
        _manager = get_sb3_manager(_db)
    return _manager


# Request models
class CreateAgentRequest(BaseModel):
    algorithm: str = "ddqn"  # dqn, ddqn, ppo, a2c, sac
    agent_name: str = "default_agent"
    custom_params: Optional[Dict] = None


class CreateEnvironmentRequest(BaseModel):
    lookback_days: int = 90
    reward_type: str = "sharpe"  # sharpe, simple, sortino
    sharpe_window: int = 24


class TrainAgentRequest(BaseModel):
    agent_name: str
    total_timesteps: int = 50000
    eval_freq: int = 5000
    save_freq: int = 10000


class PredictRequest(BaseModel):
    agent_name: str
    observation: List[float]
    deterministic: bool = True


class EvaluateRequest(BaseModel):
    agent_name: str
    n_episodes: int = 10


@router.get("/status")
async def get_manager_status():
    """Get SB3 agent manager status"""
    try:
        manager = get_manager()
        if manager is None:
            return {
                "initialized": False, 
                "agents": {},
                "environment_ready": False,
                "training_history": [],
                "available_algorithms": ["dqn", "ddqn", "ppo", "a2c", "sac"],
                "message": "Manager not initialized - click Initialize to start"
            }
        
        return manager.get_status()
    except Exception as e:
        logger.error(f"Error getting manager status: {e}")
        return {
            "initialized": False, 
            "error": "An internal error occurred",
            "agents": {},
            "environment_ready": False,
            "training_history": [],
            "available_algorithms": ["dqn", "ddqn", "ppo", "a2c", "sac"]
        }


@router.post("/initialize")
async def initialize_manager():
    """Initialize the SB3 agent manager"""
    try:
        from services.sb3_trading_agents import initialize_sb3_manager
        global _manager
        _manager = await initialize_sb3_manager(_db)
        
        return {
            "status": "initialized",
            "message": "SB3 Trading Agent Manager initialized",
            "supported_algorithms": ["dqn", "ddqn", "ppo", "a2c", "sac"],
            "features": [
                "Double DQN (DDQN) with target network action selection",
                "Sharpe ratio-based reward function",
                "Drawdown penalty for risk management",
                "PPO with GAE",
                "A2C with entropy regularization",
                "SAC with automatic entropy tuning",
                "Custom Gymnasium trading environment",
                "Vectorized training support"
            ],
            "reward_function": "sharpe_ratio"
        }
    except Exception as e:
        logger.error(f"Manager initialization error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/create-environment")
async def create_environment(request: CreateEnvironmentRequest = None):
    """Create trading environment with Sharpe ratio reward"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        lookback_days = request.lookback_days if request else 90
        reward_type = request.reward_type if request else "sharpe"
        sharpe_window = request.sharpe_window if request else 24
        
        # Fetch historical data
        cursor = _db.price_history.find().sort("timestamp", -1).limit(lookback_days * 24)
        price_data = await cursor.to_list(length=lookback_days * 24)
        
        if not price_data:
            # Generate synthetic data for demo
            np.random.seed(42)
            dates = pd.date_range(end=datetime.utcnow(), periods=2000, freq='H')
            prices = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.02, 2000))
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
        
        # Prepare data
        from services.sb3_trading_agents import prepare_training_data
        df = prepare_training_data(price_data)
        
        # Create environment with Sharpe ratio reward
        env = manager.create_env(
            df, 
            env_name="crypto_trading",
            reward_type=reward_type,
            sharpe_window=sharpe_window
        )
        
        return {
            "status": "created",
            "env_name": "crypto_trading",
            "data_points": len(df),
            "features": list(df.columns),
            "observation_space": str(env.observation_space),
            "action_space": str(env.action_space),
            "reward_type": reward_type,
            "sharpe_window": sharpe_window
        }
    except Exception as e:
        logger.error(f"Environment creation error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/create-agent")
async def create_agent(request: CreateAgentRequest):
    """Create a new SB3 trading agent (supports DDQN with Sharpe reward)"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        # Get or create environment
        if "crypto_trading" not in manager.envs:
            raise HTTPException(
                status_code=400, 
                detail="Environment not created. Call /create-environment first."
            )
        
        env = manager.envs["crypto_trading"]
        
        # Create agent
        agent = manager.create_agent(
            algorithm=request.algorithm,
            env=env,
            agent_name=request.agent_name,
            custom_params=request.custom_params
        )
        
        return {
            "status": "created",
            "agent_name": request.agent_name,
            "algorithm": request.algorithm,
            "parameters": manager.default_params.get(request.algorithm.lower(), {})
        }
    except Exception as e:
        logger.error(f"Agent creation error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/train")
async def train_agent(request: TrainAgentRequest, background_tasks: BackgroundTasks):
    """Train an SB3 agent in background"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        if request.agent_name not in manager.agents:
            raise HTTPException(
                status_code=400,
                detail=f"Agent {request.agent_name} not found. Create it first."
            )
        
        # Start training in background
        async def train_task():
            try:
                result = await manager.train_agent(
                    agent_name=request.agent_name,
                    total_timesteps=request.total_timesteps,
                    eval_freq=request.eval_freq,
                    save_freq=request.save_freq
                )
                
                # Store training result in DB
                await _db.sb3_training_history.insert_one({
                    "agent_name": request.agent_name,
                    "result": result,
                    "created_at": datetime.utcnow()
                })
                
            except Exception as e:
                logger.error(f"Training error: {e}")
        
        background_tasks.add_task(train_task)
        
        return {
            "status": "training_started",
            "agent_name": request.agent_name,
            "total_timesteps": request.total_timesteps,
            "message": "Training started in background. Check /status for progress."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/predict")
async def predict_action(request: PredictRequest):
    """Get action prediction from agent"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        observation = np.array(request.observation, dtype=np.float32)
        
        action = manager.predict(
            agent_name=request.agent_name,
            observation=observation,
            deterministic=request.deterministic
        )
        
        # Map action to trading signal
        action_map = {
            0: {"action": "strong_sell", "description": "Strong sell signal"},
            1: {"action": "sell", "description": "Moderate sell signal"},
            2: {"action": "hold", "description": "Hold position"},
            3: {"action": "buy", "description": "Moderate buy signal"},
            4: {"action": "strong_buy", "description": "Strong buy signal"}
        }
        
        action_int = int(action) if isinstance(action, (int, np.integer)) else int(action[0])
        signal = action_map.get(action_int, action_map[2])
        
        return {
            "raw_action": action_int if isinstance(action, (int, np.integer)) else action.tolist(),
            "signal": signal,
            "confidence": 1.0 if request.deterministic else 0.8,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/evaluate")
async def evaluate_agent(request: EvaluateRequest):
    """Evaluate agent performance"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        if "crypto_trading" not in manager.envs:
            raise HTTPException(status_code=400, detail="Environment not found")
        
        env = manager.envs["crypto_trading"]
        
        result = manager.evaluate_agent(
            agent_name=request.agent_name,
            env=env,
            n_eval_episodes=request.n_episodes
        )
        
        return {
            "agent_name": request.agent_name,
            "evaluation": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/agents")
async def list_agents():
    """List all created agents"""
    try:
        manager = get_manager()
        if manager is None:
            return {"agents": [], "message": "Manager not initialized"}
        
        agents_info = []
        for name, info in manager.agents.items():
            agents_info.append({
                "name": name,
                "algorithm": info.get('algorithm'),
                "trained": info.get('trained', False),
                "total_timesteps": info.get('total_timesteps', 0),
                "created_at": info.get('created_at'),
                "last_trained": info.get('last_trained')
            })
        
        return {"agents": agents_info}
    except Exception as e:
        return {"error": "An internal error occurred"}


@router.get("/training-history/{agent_name}")
async def get_training_history(agent_name: str):
    """Get training history for an agent"""
    try:
        manager = get_manager()
        if manager is None:
            return {"history": [], "message": "Manager not initialized"}
        
        history = manager.training_history.get(agent_name, [])
        
        return {
            "agent_name": agent_name,
            "history": history,
            "total_sessions": len(history)
        }
    except Exception as e:
        return {"error": "An internal error occurred"}


@router.delete("/agent/{agent_name}")
async def delete_agent(agent_name: str):
    """Delete an agent"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        if agent_name in manager.agents:
            del manager.agents[agent_name]
            return {"status": "deleted", "agent_name": agent_name}
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/algorithms")
async def get_supported_algorithms():
    """Get information about supported algorithms"""
    return {
        "algorithms": {
            "ddqn": {
                "name": "Double Deep Q-Network",
                "description": "Enhanced DQN with target network action selection to reduce overestimation",
                "best_for": "Discrete trading decisions with better value estimation",
                "reward_function": "Sharpe ratio-based",
                "features": [
                    "Target network for action selection (Double DQN)",
                    "Experience replay buffer (100k transitions)",
                    "Soft target updates (tau=0.005)",
                    "Deeper network architecture [256, 256, 128]",
                    "Lower exploration rate for stability"
                ]
            },
            "dqn": {
                "name": "Deep Q-Network",
                "description": "Value-based DRL with discrete actions",
                "best_for": "Discrete trading decisions (buy/sell/hold)",
                "features": [
                    "Experience replay buffer",
                    "Target network with soft updates",
                    "Epsilon-greedy exploration"
                ]
            },
            "ppo": {
                "name": "Proximal Policy Optimization",
                "description": "Policy gradient with clipped objective",
                "best_for": "Continuous position sizing, stable training",
                "features": [
                    "Clipped surrogate objective",
                    "Generalized Advantage Estimation (GAE)",
                    "Multiple epochs per batch"
                ]
            },
            "a2c": {
                "name": "Advantage Actor-Critic",
                "description": "Synchronous actor-critic method",
                "best_for": "Fast training, simpler environments",
                "features": [
                    "Entropy regularization",
                    "Value function baseline",
                    "N-step returns"
                ]
            },
            "sac": {
                "name": "Soft Actor-Critic",
                "description": "Maximum entropy RL for continuous actions",
                "best_for": "Continuous position sizing, exploration",
                "features": [
                    "Automatic entropy tuning",
                    "Two Q-functions to reduce overestimation",
                    "Reparameterization trick"
                ]
            }
        },
        "recommendation": "DDQN with Sharpe ratio reward for optimal risk-adjusted returns, PPO for stable training, SAC for continuous position sizing",
        "reward_function": {
            "type": "sharpe_ratio",
            "description": "Rolling Sharpe ratio with drawdown penalty",
            "components": [
                "Rolling Sharpe ratio (24-hour window by default)",
                "Risk penalty for over-leveraged positions",
                "Transaction cost penalty",
                "Drawdown penalty (>10% triggers penalty)"
            ]
        }
    }


@router.get("/environment/metrics")
async def get_environment_metrics():
    """Get trading environment metrics including Sharpe ratio"""
    try:
        manager = get_manager()
        if manager is None:
            return {"error": "Manager not initialized"}
        
        if "crypto_trading" not in manager.envs:
            return {"error": "Environment not found"}
        
        env = manager.envs["crypto_trading"]
        
        # Get metrics from unwrapped environment
        base_env = env.env if hasattr(env, 'env') else env
        
        return {
            "environment": "crypto_trading",
            "metrics": base_env.get_metrics() if hasattr(base_env, 'get_metrics') else {},
            "configuration": {
                "initial_balance": base_env.initial_balance,
                "transaction_cost_pct": base_env.transaction_cost_pct,
                "slippage_pct": base_env.slippage_pct,
                "max_position_pct": base_env.max_position_pct,
                "window_size": base_env.window_size,
                "reward_type": getattr(base_env, 'reward_type', 'sharpe'),
                "sharpe_window": getattr(base_env, 'sharpe_window', 24)
            }
        }
    except Exception as e:
        return {"error": "An internal error occurred"}
