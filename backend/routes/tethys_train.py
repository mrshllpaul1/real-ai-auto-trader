"""
Tethys Training & Monitoring API Routes
========================================
Endpoints for model training, MLflow registry, and live monitoring.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tethys-train", tags=["Tethys Training"])

_db = None


def set_db(db):
    global _db
    _db = db


class TrainConfig(BaseModel):
    episodes: int = 100
    symbol: str = "BTC/USD"
    save_every: int = 10
    early_stopping_patience: int = 20


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
    
    from services.tethys_training import get_trainer
    trainer = get_trainer(_db)
    
    if trainer.is_training:
        return {"status": "already_training", "progress": trainer.get_training_status()}
    
    async def train_task():
        await trainer.train(
            episodes=config.episodes,
            symbol=config.symbol,
            save_every=config.save_every,
            early_stopping_patience=config.early_stopping_patience
        )
    
    background_tasks.add_task(train_task)
    
    return {
        "status": "training_started",
        "config": config.dict()
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
    from services.tethys_training import get_trainer
    trainer = get_trainer(_db)
    return trainer.get_training_status()


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
