"""
Tethys Training & Monitoring API Routes
========================================
Endpoints for model training, MLflow registry, and live monitoring.
Includes WebSocket for real-time training progress.
"""

import logging
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Set
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tethys-train", tags=["Tethys Training"])

_db = None

# WebSocket connections for training progress
_training_connections: Set[WebSocket] = set()


def set_db(db):
    global _db
    _db = db


async def broadcast_training_update(data: dict):
    """Broadcast training progress to all connected clients"""
    if not _training_connections:
        return
    
    message = json.dumps(data)
    disconnected = set()
    
    for ws in _training_connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    
    _training_connections.difference_update(disconnected)


class TrainConfig(BaseModel):
    episodes: int = 100
    symbol: str = "BTC/USD"
    save_every: int = 10
    early_stopping_patience: int = 20


# =============================================================================
# WEBSOCKET ENDPOINT FOR REAL-TIME TRAINING
# =============================================================================

@router.websocket("/ws/progress")
async def training_progress_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time training progress updates"""
    await websocket.accept()
    _training_connections.add(websocket)
    
    try:
        # Send initial status
        from services.tethys_training import get_trainer
        trainer = get_trainer(_db)
        await websocket.send_json({
            "type": "initial",
            "data": trainer.get_training_status()
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for ping/pong or client messages
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send status update every 30 seconds
                await websocket.send_json({
                    "type": "status",
                    "data": trainer.get_training_status()
                })
    except WebSocketDisconnect:
        pass
    finally:
        _training_connections.discard(websocket)


# =============================================================================
# TRAINING ENDPOINTS
# =============================================================================

@router.post("/start")
async def start_training(
    config: TrainConfig = None,
    background_tasks: BackgroundTasks = None
):
    """Start Rainbow DQN training"""
    global _db
    
    config = config or TrainConfig()
    
    # Mark training as starting immediately
    async def train_task():
        try:
            from services.tethys_training import get_trainer
            trainer = get_trainer(_db)
            
            if trainer.is_training:
                logger.info("Training already in progress")
                return
            
            await trainer.train(
                episodes=config.episodes,
                symbol=config.symbol,
                save_every=config.save_every,
                early_stopping_patience=config.early_stopping_patience
            )
        except Exception as e:
            logger.error(f"Training error: {e}")
    
    # Start training in background immediately without waiting
    background_tasks.add_task(train_task)
    
    return {
        "status": "training_started",
        "config": config.dict(),
        "message": "Training initialization started in background"
    }


@router.post("/stop")
async def stop_training():
    """Stop training"""
    from services.tethys_training import get_trainer
    trainer = get_trainer(_db)
    trainer.stop_training()
    return {"status": "stop_requested"}


@router.get("/status")
async def get_training_status():
    """Get training status"""
    try:
        from services.tethys_training import get_trainer
        trainer = get_trainer(_db)
        return trainer.get_training_status()
    except Exception as e:
        # Return default status if trainer can't be initialized
        return {
            'is_training': False,
            'is_active': False,
            'current_episode': 0,
            'total_episodes': 0,
            'progress_pct': 0,
            'best_sharpe': 0,
            'recent_history': [],
            'rainbow_dqn_status': 'Initializing',
            'transformer_status': 'Ready',
            'ensemble_status': 'Ready',
            'risk_manager': 'Active',
            'signals_generated': 0,
            'confidence': 50,
            'market_regime': 'Normal',
            'error': str(e)
        }


# =============================================================================
# MODEL REGISTRY ENDPOINTS
# =============================================================================

@router.get("/registry/status")
async def get_registry_status():
    """Get MLflow registry status"""
    from services.tethys_training import get_registry
    registry = get_registry()
    return registry.get_registry_status()


@router.get("/registry/models")
async def get_registered_models():
    """Get all registered models"""
    from services.tethys_training import get_registry
    registry = get_registry()
    return {
        "models": registry.get_model_versions()
    }


@router.get("/registry/best")
async def get_best_model(metric: str = "sharpe_ratio"):
    """Get best model by metric"""
    from services.tethys_training import get_registry
    registry = get_registry()
    run_id = registry.get_best_model(metric)
    return {
        "metric": metric,
        "best_run_id": run_id
    }


@router.post("/registry/promote")
async def promote_model(
    model_name: str = "tethys_rainbow_dqn",
    version: str = "1",
    stage: str = "Production"
):
    """Promote model to stage"""
    from services.tethys_training import get_registry
    registry = get_registry()
    
    try:
        registry.promote_model(model_name, version, stage)
        return {"status": "promoted", "model": model_name, "version": version, "stage": stage}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# MONITORING ENDPOINTS
# =============================================================================

@router.post("/monitor/start")
async def start_monitoring(
    interval: int = 60,
    background_tasks: BackgroundTasks = None
):
    """Start live monitoring"""
    from services.tethys_training import get_monitor
    monitor = get_monitor(_db)
    
    if monitor.is_running:
        return {"status": "already_running"}
    
    background_tasks.add_task(monitor.start_monitoring, interval)
    
    return {
        "status": "monitoring_started",
        "interval": interval
    }


@router.post("/monitor/stop")
async def stop_monitoring():
    """Stop monitoring"""
    from services.tethys_training import get_monitor
    monitor = get_monitor(_db)
    monitor.stop_monitoring()
    return {"status": "stopped"}


@router.get("/monitor/status")
async def get_monitoring_status():
    """Get monitoring status"""
    from services.tethys_training import get_monitor
    monitor = get_monitor(_db)
    return monitor.get_monitoring_status()


@router.get("/monitor/alerts")
async def get_alerts():
    """Get active alerts"""
    from services.tethys_training import get_monitor
    monitor = get_monitor(_db)
    return {
        "alerts": monitor.alerts[-20:],
        "total": len(monitor.alerts)
    }


# =============================================================================
# DASHBOARD ENDPOINT
# =============================================================================

@router.get("/dashboard")
async def get_full_dashboard():
    """Get complete training and monitoring dashboard"""
    from services.tethys_training import get_trainer, get_registry, get_monitor
    
    trainer = get_trainer(_db)
    registry = get_registry()
    monitor = get_monitor(_db)
    
    return {
        "training": trainer.get_training_status(),
        "registry": registry.get_registry_status(),
        "monitoring": monitor.get_monitoring_status()
    }
