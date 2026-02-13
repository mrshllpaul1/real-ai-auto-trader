"""
Training History API Routes
Endpoints for viewing and managing training history
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/training-history", tags=["Training History"])

# Service reference
_history_service = None


def set_dependencies(history_service):
    """Set the training history service dependency"""
    global _history_service
    _history_service = history_service


@router.get("/")
async def get_training_history(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query(None, description="Filter by status (running, completed, failed)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return")
):
    """
    Get training history with optional filters
    
    Returns list of training sessions sorted by start time (newest first)
    """
    if not _history_service:
        raise HTTPException(status_code=503, detail="Training history service not initialized")
    
    history = await _history_service.get_history(
        model_type=model_type,
        status=status,
        limit=limit
    )
    
    return {
        "count": len(history),
        "history": history,
        "filters": {
            "model_type": model_type,
            "status": status,
            "limit": limit
        }
    }


@router.get("/stats")
async def get_all_training_stats():
    """
    Get overall training statistics across all model types
    """
    if not _history_service:
        raise HTTPException(status_code=503, detail="Training history service not initialized")
    
    return await _history_service.get_all_stats()


@router.get("/stats/{model_type}")
async def get_model_stats(model_type: str):
    """
    Get detailed statistics for a specific model type
    
    Args:
        model_type: Model type (e.g., 'rl_agent', 'transformer', 'regime')
    """
    if not _history_service:
        raise HTTPException(status_code=503, detail="Training history service not initialized")
    
    return await _history_service.get_model_stats(model_type)


@router.get("/recent")
async def get_recent_training():
    """
    Get the 10 most recent training sessions
    """
    if not _history_service:
        raise HTTPException(status_code=503, detail="Training history service not initialized")
    
    history = await _history_service.get_history(limit=10)
    
    # Add summary
    running = sum(1 for h in history if h.get("status") == "running")
    completed = sum(1 for h in history if h.get("status") == "completed")
    failed = sum(1 for h in history if h.get("status") == "failed")
    
    return {
        "summary": {
            "running": running,
            "completed": completed,
            "failed": failed
        },
        "sessions": history
    }


@router.get("/model-types")
async def get_available_model_types():
    """
    Get list of available model types with session counts
    """
    if not _history_service:
        raise HTTPException(status_code=503, detail="Training history service not initialized")
    
    stats = await _history_service.get_all_stats()
    
    return {
        "model_types": list(stats.get("by_model", {}).keys()),
        "details": stats.get("by_model", {})
    }
