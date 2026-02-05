"""
Rainbow DQN & Order Book API Routes
====================================
Endpoints for Rainbow DQN agent and real-time order book data.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rainbow", tags=["Rainbow DQN"])

# Global references
_order_book_ws = None
_rainbow_agent = None
_feature_extractor = None


class TrainingConfig(BaseModel):
    episodes: int = 100
    max_steps_per_episode: int = 1000


class ActionRequest(BaseModel):
    symbol: str = "BTC/USD"


# =============================================================================
# ORDER BOOK ENDPOINTS
# =============================================================================

class OrderBookConfig(BaseModel):
    symbols: List[str] = ["BTC/USD", "ETH/USD", "SOL/USD"]
    depth: int = 25


@router.post("/orderbook/start")
async def start_orderbook_stream(config: OrderBookConfig = None):
    """Start Kraken order book WebSocket stream"""
    global _order_book_ws, _feature_extractor
    
    config = config or OrderBookConfig()
    
    try:
        from services.kraken_orderbook_ws import (
            initialize_order_book_service,
            get_order_book_service,
            get_feature_extractor
        )
        
        symbols = config.symbols
        
        # Initialize if not already running
        if _order_book_ws is None or not _order_book_ws.connected:
            _order_book_ws = await initialize_order_book_service(
                symbols=symbols,
                depth=config.depth
            )
            _feature_extractor = get_feature_extractor()
        
        return {
            "status": "started",
            "symbols": symbols,
            "depth": config.depth,
            "message": "Order book WebSocket stream started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start order book stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orderbook/stop")
async def stop_orderbook_stream():
    """Stop order book WebSocket stream"""
    global _order_book_ws
    
    if _order_book_ws:
        await _order_book_ws.stop()
        return {"status": "stopped"}
    
    return {"status": "not_running"}


@router.get("/orderbook/status")
async def get_orderbook_status():
    """Get order book WebSocket status"""
    global _order_book_ws
    
    if _order_book_ws:
        return _order_book_ws.get_status()
    
    return {
        "connected": False,
        "running": False,
        "message": "Order book service not initialized"
    }


@router.get("/orderbook/{symbol}")
async def get_orderbook(symbol: str, levels: int = 10):
    """Get current order book for symbol"""
    global _order_book_ws
    
    if not _order_book_ws or not _order_book_ws.connected:
        raise HTTPException(
            status_code=503,
            detail="Order book service not running"
        )
    
    # Convert symbol format (BTC/USD -> BTC/USD)
    book = _order_book_ws.get_order_book(symbol)
    
    if not book or not book.snapshot_received:
        raise HTTPException(
            status_code=404,
            detail=f"Order book not available for {symbol}"
        )
    
    sorted_bids = sorted(book.bids.items(), reverse=True)[:levels]
    sorted_asks = sorted(book.asks.items())[:levels]
    
    return {
        "symbol": symbol,
        "timestamp": book.last_update,
        "bids": [
            {"price": price, "quantity": level.quantity}
            for price, level in sorted_bids
        ],
        "asks": [
            {"price": price, "quantity": level.quantity}
            for price, level in sorted_asks
        ],
        "metrics": {
            "spread": book.get_spread(),
            "mid_price": book.get_mid_price(),
            "imbalance": book.get_imbalance(levels),
            "depth": book.get_depth(levels)
        }
    }


@router.get("/orderbook/{symbol}/features")
async def get_orderbook_features(symbol: str, levels: int = 10):
    """Get order book features for RL"""
    global _order_book_ws
    
    if not _order_book_ws:
        raise HTTPException(status_code=503, detail="Service not running")
    
    features = _order_book_ws.get_features(symbol, levels)
    
    return {
        "symbol": symbol,
        "features": features.tolist(),
        "feature_dim": len(features)
    }


# =============================================================================
# RAINBOW DQN ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_rainbow_status():
    """Get Rainbow DQN agent status"""
    global _rainbow_agent
    
    if _rainbow_agent:
        return _rainbow_agent.get_status()
    
    return {
        "initialized": False,
        "message": "Rainbow DQN not initialized. Call /api/rainbow/init first."
    }


@router.post("/init")
async def initialize_rainbow(
    state_dim: int = 45,
    action_dim: int = 5,
    sequence_length: int = 168
):
    """Initialize Rainbow DQN agent"""
    global _rainbow_agent
    
    try:
        from services.rainbow_dqn import RainbowDQN
        
        _rainbow_agent = RainbowDQN(
            state_dim=state_dim,
            action_dim=action_dim,
            sequence_length=sequence_length
        )
        
        return {
            "status": "initialized",
            "config": {
                "state_dim": state_dim,
                "action_dim": action_dim,
                "sequence_length": sequence_length
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize Rainbow DQN: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action")
async def get_action(request: ActionRequest):
    """Get trading action from Rainbow DQN"""
    global _rainbow_agent, _feature_extractor
    
    if not _rainbow_agent:
        raise HTTPException(
            status_code=503,
            detail="Rainbow DQN not initialized"
        )
    
    if not _feature_extractor:
        raise HTTPException(
            status_code=503,
            detail="Feature extractor not initialized. Start order book first."
        )
    
    try:
        # Get feature sequence
        state_sequence = _feature_extractor.get_sequence(request.symbol)
        
        # Get action
        action = _rainbow_agent.select_action(state_sequence, training=False)
        
        action_names = ['strong_sell', 'sell', 'hold', 'buy', 'strong_buy']
        
        return {
            "symbol": request.symbol,
            "action": action,
            "action_name": action_names[action],
            "sequence_length": len(state_sequence)
        }
        
    except Exception as e:
        logger.error(f"Action selection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/start")
async def start_training(
    config: TrainingConfig = None,
    background_tasks: BackgroundTasks = None
):
    """Start Rainbow DQN training in background"""
    global _rainbow_agent, _feature_extractor
    
    if not _rainbow_agent:
        raise HTTPException(status_code=503, detail="Rainbow DQN not initialized")
    
    config = config or TrainingConfig()
    
    async def train_loop():
        """Background training loop"""
        try:
            from services.sb3_trading_agents import CryptoTradingEnv, prepare_training_data
            from services.kraken_service import get_kraken_service
            
            kraken = get_kraken_service()
            
            # Get training data
            ohlc_data = await kraken.get_ohlc("XXBTZUSD", interval=60, since=None)
            train_df = prepare_training_data(ohlc_data)
            
            env = CryptoTradingEnv(train_df, reward_type='sharpe')
            
            for episode in range(config.episodes):
                state, _ = env.reset()
                episode_reward = 0
                
                # Build sequence (pad with zeros initially)
                import numpy as np
                state_sequence = np.zeros((168, 45), dtype=np.float32)
                
                for step in range(config.max_steps_per_episode):
                    # Shift sequence and add new state
                    state_sequence = np.roll(state_sequence, -1, axis=0)
                    state_features = np.zeros(45, dtype=np.float32)
                    state_features[:len(state)] = state
                    state_sequence[-1] = state_features
                    
                    action = _rainbow_agent.select_action(state_sequence, training=True)
                    
                    action_continuous = [-1.0, -0.5, 0.0, 0.5, 1.0][action]
                    next_state, reward, terminated, truncated, info = env.step(
                        np.array([action_continuous])
                    )
                    done = terminated or truncated
                    
                    # Build next sequence
                    next_sequence = np.roll(state_sequence, -1, axis=0)
                    next_features = np.zeros(45, dtype=np.float32)
                    next_features[:len(next_state)] = next_state
                    next_sequence[-1] = next_features
                    
                    _rainbow_agent.store_transition(
                        state_sequence, action, reward, next_sequence, done
                    )
                    
                    _rainbow_agent.train_step()
                    
                    episode_reward += reward
                    state = next_state
                    state_sequence = next_sequence
                    
                    if done:
                        break
                
                if episode % 10 == 0:
                    logger.info(f"Rainbow Episode {episode}: Reward = {episode_reward:.4f}")
            
            _rainbow_agent.save()
            logger.info("Rainbow DQN training complete")
            
        except Exception as e:
            logger.error(f"Training error: {e}")
    
    background_tasks.add_task(train_loop)
    
    return {
        "status": "training_started",
        "episodes": config.episodes,
        "max_steps": config.max_steps_per_episode
    }


@router.post("/save")
async def save_model():
    """Save Rainbow DQN model"""
    global _rainbow_agent
    
    if not _rainbow_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    _rainbow_agent.save()
    
    return {"status": "saved", "path": _rainbow_agent.model_dir}


# =============================================================================
# COMBINED ENDPOINTS
# =============================================================================

@router.post("/full-init")
async def full_initialization(
    symbols: List[str] = None,
    depth: int = 25
):
    """Initialize both order book stream and Rainbow DQN"""
    symbols = symbols or ["BTC/USD", "ETH/USD", "SOL/USD"]
    
    # Start order book
    ob_result = await start_orderbook_stream(symbols, depth)
    
    # Calculate state dim based on order book features
    levels = 10
    per_level = 4  # bid_price, bid_qty, ask_price, ask_qty
    aggregate = 5  # spread, imbalance, bid_depth, ask_depth, total_depth
    state_dim = levels * per_level + aggregate
    
    # Initialize Rainbow
    rainbow_result = await initialize_rainbow(
        state_dim=state_dim,
        action_dim=5,
        sequence_length=168
    )
    
    return {
        "order_book": ob_result,
        "rainbow_dqn": rainbow_result,
        "status": "fully_initialized"
    }
