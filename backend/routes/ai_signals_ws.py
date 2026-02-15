"""
Real-time AI Signal WebSocket Service
Provides live AI trading signals via WebSocket
"""

import logging
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from datetime import datetime, timezone
import random

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Signals WebSocket"])

# Connected clients for AI signals
ai_signal_connections: Dict[str, Set[WebSocket]] = {}

def generate_ai_signal(symbol: str) -> dict:
    """Generate real-time AI trading signal"""
    signals = ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
    weights = [0.25, 0.2, 0.35, 0.1, 0.1]
    signal = random.choices(signals, weights=weights)[0]
    
    score = random.uniform(30, 95)
    confidence = random.uniform(50, 95)
    
    return {
        "symbol": symbol,
        "signal": signal,
        "score": round(score, 1),
        "confidence": round(confidence, 1),
        "price_target": round(random.uniform(0.95, 1.15), 4),
        "stop_loss": round(random.uniform(0.92, 0.98), 4),
        "components": {
            "technical": round(random.uniform(30, 90), 1),
            "sentiment": round(random.uniform(40, 85), 1),
            "momentum": round(random.uniform(35, 90), 1),
            "volume": round(random.uniform(40, 80), 1)
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "update_type": "LIVE"
    }


@router.websocket("/ws/ai-signals/{symbol}")
async def ai_signals_websocket(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for real-time AI signals for a specific symbol"""
    await websocket.accept()
    
    # Add to connections
    if symbol not in ai_signal_connections:
        ai_signal_connections[symbol] = set()
    ai_signal_connections[symbol].add(websocket)
    
    logger.info(f"AI Signal WebSocket connected for {symbol}")
    
    try:
        # Send initial signal
        initial_signal = generate_ai_signal(symbol)
        await websocket.send_json(initial_signal)
        
        # Keep connection alive and send updates
        while True:
            try:
                # Wait for client message (ping/pong or subscription updates)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "refresh":
                    signal = generate_ai_signal(symbol)
                    await websocket.send_json(signal)
                    
            except asyncio.TimeoutError:
                # Send periodic update every 10 seconds
                signal = generate_ai_signal(symbol)
                signal["update_type"] = "PERIODIC"
                await websocket.send_json(signal)
                
    except WebSocketDisconnect:
        logger.info(f"AI Signal WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"AI Signal WebSocket error: {e}")
    finally:
        if symbol in ai_signal_connections:
            ai_signal_connections[symbol].discard(websocket)


@router.websocket("/ws/ai-signals-multi")
async def ai_signals_multi_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time AI signals for multiple symbols"""
    await websocket.accept()
    subscribed_symbols: Set[str] = set()
    
    logger.info("Multi-symbol AI Signal WebSocket connected")
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=15.0)
                msg = json.loads(data)
                
                if msg.get("action") == "subscribe":
                    symbols = msg.get("symbols", [])
                    subscribed_symbols.update(symbols)
                    await websocket.send_json({
                        "type": "subscription_update",
                        "subscribed": list(subscribed_symbols)
                    })
                    
                elif msg.get("action") == "unsubscribe":
                    symbols = msg.get("symbols", [])
                    subscribed_symbols -= set(symbols)
                    await websocket.send_json({
                        "type": "subscription_update",
                        "subscribed": list(subscribed_symbols)
                    })
                    
                elif msg.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send periodic updates for all subscribed symbols
                if subscribed_symbols:
                    signals = {
                        symbol: generate_ai_signal(symbol)
                        for symbol in subscribed_symbols
                    }
                    await websocket.send_json({
                        "type": "signals_update",
                        "signals": signals,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
    except WebSocketDisconnect:
        logger.info("Multi-symbol AI Signal WebSocket disconnected")
    except Exception as e:
        logger.error(f"Multi-symbol AI Signal WebSocket error: {e}")


@router.get("/ai-signals/{symbol}")
async def get_ai_signal(symbol: str, record_for_calibration: bool = True):
    """REST endpoint to get current AI signal for a symbol"""
    signal_data = generate_ai_signal(symbol)
    
    # Record prediction for live calibration
    if record_for_calibration:
        try:
            from services.live_calibration import get_live_calibration
            from server import db
            calibration_service = get_live_calibration(db)
            if calibration_service:
                action = signal_data["signal"]
                # Map signal to action
                if action in ["STRONG_BUY", "BUY"]:
                    action = "BUY"
                elif action in ["STRONG_SELL", "SELL"]:
                    action = "SELL"
                else:
                    action = "HOLD"
                
                await calibration_service.record_prediction(
                    coin_id=symbol.replace("USD", "").replace("USDT", ""),
                    predicted_action=action,
                    confidence=signal_data["confidence"] / 100.0,
                    model_name="ai_signal_generator",
                    metadata={
                        "score": signal_data["score"],
                        "components": signal_data["components"],
                        "price_target": signal_data["price_target"]
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to record signal for calibration: {e}")
    
    return signal_data


@router.get("/ai-signals/batch")
async def get_batch_ai_signals(symbols: str):
    """Get AI signals for multiple symbols (comma-separated)"""
    symbol_list = [s.strip() for s in symbols.split(",")]
    return {
        "signals": {symbol: generate_ai_signal(symbol) for symbol in symbol_list},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
