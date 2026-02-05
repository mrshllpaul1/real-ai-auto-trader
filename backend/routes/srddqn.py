"""
SRDDQN (Self-Rewarding Double Deep Q-Network) API Routes
Advanced DRL agent with intrinsic motivation and curiosity-driven exploration.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/srddqn", tags=["SRDDQN Agent"])

# Service references
_db = None
_manager = None


def set_dependencies(db, manager=None):
    """Set service dependencies"""
    global _db, _manager
    _db = db
    _manager = manager


def get_manager():
    """Get or create SRDDQN manager"""
    global _manager
    if _manager is None:
        from services.srddqn_agent import get_srddqn_manager
        _manager = get_srddqn_manager(_db)
    return _manager


# Request models
class CreateAgentRequest(BaseModel):
    agent_name: str = "srddqn_trader"
    state_dim: int = 24
    config: Optional[Dict] = None


class TrainRequest(BaseModel):
    agent_name: str
    episodes: int = 100
    max_steps_per_episode: int = 1000


class PredictRequest(BaseModel):
    agent_name: str
    state: List[float]
    training_mode: bool = False


class UpdateWeightsRequest(BaseModel):
    agent_name: str
    sharpe_weight: float = 0.5
    self_reward_weight: float = 0.3
    curiosity_weight: float = 0.2


@router.get("/status")
async def get_manager_status():
    """Get SRDDQN manager status"""
    try:
        manager = get_manager()
        if manager is None:
            return {"initialized": False, "message": "Manager not initialized"}
        
        return manager.get_status()
    except Exception as e:
        return {"error": str(e), "initialized": False}


@router.post("/initialize")
async def initialize_manager():
    """Initialize the SRDDQN manager"""
    try:
        from services.srddqn_agent import initialize_srddqn_manager
        global _manager
        _manager = await initialize_srddqn_manager(_db)
        
        return {
            "status": "initialized",
            "message": "SRDDQN Manager initialized",
            "description": "Self-Rewarding Double Deep Q-Network for advanced trading",
            "features": [
                "Double DQN with target network for stable learning",
                "Dueling architecture (Value + Advantage streams)",
                "Self-reward predictor for intrinsic motivation",
                "Curiosity module (ICM) for exploration bonus",
                "Sharpe ratio-based extrinsic rewards",
                "Adaptive reward weighting"
            ],
            "reward_components": {
                "extrinsic": "Sharpe ratio from trading performance",
                "intrinsic": "Self-reward predictor output",
                "curiosity": "Prediction error from ICM"
            }
        }
    except Exception as e:
        logger.error(f"SRDDQN initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-agent")
async def create_agent(request: CreateAgentRequest):
    """Create a new SRDDQN agent"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        config = request.config or {
            'action_dim': 5,
            'hidden_dims': [256, 256, 128],
            'learning_rate': 1e-4,
            'gamma': 0.99,
            'self_reward_weight': 0.3,
            'curiosity_weight': 0.2,
            'sharpe_weight': 0.5
        }
        
        agent = manager.create_agent(
            agent_name=request.agent_name,
            state_dim=request.state_dim,
            config=config
        )
        
        return {
            "status": "created",
            "agent_name": request.agent_name,
            "state_dim": request.state_dim,
            "config": config,
            "agent_status": agent.get_status()
        }
    except Exception as e:
        logger.error(f"Agent creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_name}")
async def get_agent_status(agent_name: str):
    """Get detailed status of an agent"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        agent = manager.get_agent(agent_name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        return agent.get_status()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict")
async def predict_action(request: PredictRequest):
    """Get action prediction from SRDDQN agent"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        agent = manager.get_agent(request.agent_name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_name} not found")
        
        state = np.array(request.state, dtype=np.float32)
        action = agent.select_action(state, training=request.training_mode)
        
        # Map action to trading signal
        action_map = {
            0: {"action": "strong_sell", "position": -1.0, "description": "Strong sell signal"},
            1: {"action": "sell", "position": -0.5, "description": "Moderate sell signal"},
            2: {"action": "hold", "position": 0.0, "description": "Hold current position"},
            3: {"action": "buy", "position": 0.5, "description": "Moderate buy signal"},
            4: {"action": "strong_buy", "position": 1.0, "description": "Strong buy signal"}
        }
        
        signal = action_map.get(action, action_map[2])
        
        # Get self-reward prediction for confidence
        intrinsic_reward, confidence = agent.self_reward_predictor.predict_reward(state, action)
        
        return {
            "agent_name": request.agent_name,
            "raw_action": action,
            "signal": signal,
            "intrinsic_reward": intrinsic_reward,
            "confidence": confidence,
            "epsilon": agent.epsilon,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_agent(request: TrainRequest, background_tasks: BackgroundTasks):
    """Train SRDDQN agent (background task)"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        agent = manager.get_agent(request.agent_name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_name} not found")
        
        # Training will be done with environment
        async def train_task():
            try:
                logger.info(f"Starting SRDDQN training for {request.agent_name}")
                
                # Import environment
                from services.sb3_trading_agents import CryptoTradingEnv, prepare_training_data
                import pandas as pd
                
                # Get historical data
                cursor = _db.price_history.find().sort("timestamp", -1).limit(2000)
                price_data = await cursor.to_list(length=2000)
                
                if not price_data:
                    # Generate synthetic data
                    np.random.seed(42)
                    dates = pd.date_range(end=datetime.utcnow(), periods=2000, freq='H')
                    prices = 50000 * np.cumprod(1 + np.random.normal(0.0001, 0.02, 2000))
                    price_data = [
                        {
                            'timestamp': d,
                            'close': p,
                            'open': p * (1 + np.random.uniform(-0.01, 0.01)),
                            'high': p * (1 + np.random.uniform(0, 0.02)),
                            'low': p * (1 - np.random.uniform(0, 0.02)),
                            'volume': np.random.uniform(1000, 10000)
                        }
                        for d, p in zip(dates, prices)
                    ]
                
                df = prepare_training_data(price_data)
                env = CryptoTradingEnv(df, reward_type='sharpe')
                
                # Train for episodes
                results = []
                for ep in range(request.episodes):
                    result = agent.train_episode(env, max_steps=request.max_steps_per_episode)
                    results.append(result)
                    
                    if ep % 10 == 0:
                        logger.info(f"Episode {ep}: reward={result['total_reward']:.4f}, "
                                   f"epsilon={result['epsilon']:.4f}")
                
                # Save model
                agent.save()
                
                # Store training results
                await _db.srddqn_training_history.insert_one({
                    "agent_name": request.agent_name,
                    "episodes": request.episodes,
                    "results": results[-10:],  # Last 10 episodes
                    "final_epsilon": agent.epsilon,
                    "total_timesteps": agent.total_timesteps,
                    "created_at": datetime.utcnow()
                })
                
                logger.info(f"SRDDQN training complete: {request.agent_name}")
                
            except Exception as e:
                logger.error(f"SRDDQN training error: {e}")
        
        background_tasks.add_task(train_task)
        
        return {
            "status": "training_started",
            "agent_name": request.agent_name,
            "episodes": request.episodes,
            "max_steps_per_episode": request.max_steps_per_episode,
            "message": "SRDDQN training started in background"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-weights")
async def update_reward_weights(request: UpdateWeightsRequest):
    """Update reward component weights"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        agent = manager.get_agent(request.agent_name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_name} not found")
        
        # Normalize weights
        total = request.sharpe_weight + request.self_reward_weight + request.curiosity_weight
        agent.sharpe_weight = request.sharpe_weight / total
        agent.self_reward_weight = request.self_reward_weight / total
        agent.curiosity_weight = request.curiosity_weight / total
        
        return {
            "status": "updated",
            "agent_name": request.agent_name,
            "new_weights": {
                "sharpe": agent.sharpe_weight,
                "self_reward": agent.self_reward_weight,
                "curiosity": agent.curiosity_weight
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """List all SRDDQN agents"""
    try:
        manager = get_manager()
        if manager is None:
            return {"agents": [], "message": "Manager not initialized"}
        
        return {"agents": manager.list_agents()}
    except Exception as e:
        return {"error": str(e)}


@router.get("/reward-components/{agent_name}")
async def get_reward_components(agent_name: str):
    """Get reward component statistics for an agent"""
    try:
        manager = get_manager()
        if manager is None:
            raise HTTPException(status_code=400, detail="Manager not initialized")
        
        agent = manager.get_agent(agent_name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        status = agent.get_status()
        
        return {
            "agent_name": agent_name,
            "reward_weights": status['reward_weights'],
            "self_reward_stats": status['self_reward_stats'],
            "component_stats": status['reward_component_stats'],
            "description": {
                "extrinsic": "Sharpe ratio from actual trading performance",
                "self_reward": "Predicted reward from self-reward network (intrinsic motivation)",
                "curiosity": "Exploration bonus from prediction error (ICM)"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agent/{agent_name}")
async def delete_agent(agent_name: str):
    """Delete an SRDDQN agent"""
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/architecture")
async def get_architecture():
    """Get SRDDQN architecture details"""
    return {
        "name": "Self-Rewarding Double Deep Q-Network (SRDDQN)",
        "based_on": "Huang et al. (2024) - A Self-Rewarding Mechanism in Deep Reinforcement Learning",
        "reference": "https://www.mdpi.com/2227-7390/12/24/4020",
        "components": {
            "q_network": {
                "type": "Dueling DQN",
                "architecture": "[256, 256, 128] + Value/Advantage streams",
                "description": "Separates state value estimation from action advantage"
            },
            "target_network": {
                "type": "Double DQN target",
                "update": "Soft update with tau=0.005",
                "description": "Reduces Q-value overestimation via separate evaluation network"
            },
            "self_reward_predictor": {
                "type": "MLP [128, 64, 32]",
                "inputs": "State + Action (one-hot)",
                "outputs": "Predicted reward + Confidence",
                "description": "Generates intrinsic rewards for dense learning signal"
            },
            "curiosity_module": {
                "type": "Intrinsic Curiosity Module (ICM)",
                "components": ["State encoder", "Forward model", "Inverse model"],
                "description": "Provides exploration bonus based on state prediction error"
            }
        },
        "reward_function": {
            "formula": "R = w1*Sharpe + w2*SelfReward*Confidence + w3*Curiosity",
            "default_weights": {
                "sharpe (w1)": 0.5,
                "self_reward (w2)": 0.3,
                "curiosity (w3)": 0.2
            },
            "description": "Combines extrinsic (Sharpe) and intrinsic (self-reward, curiosity) signals"
        },
        "advantages": [
            "Dense rewards in sparse reward environments",
            "Self-supervised intrinsic motivation",
            "Curiosity-driven exploration",
            "Adaptive learning from expert knowledge",
            "Reduced overestimation via Double DQN",
            "Better value estimation via Dueling architecture"
        ]
    }
