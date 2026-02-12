"""
System State API Routes
========================
Centralized endpoints for managing running states of all system components.
Provides state persistence across page navigation and service restarts.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system-state", tags=["System State"])

_db = None


def set_db(db):
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


class SetStateRequest(BaseModel):
    component: str
    is_running: bool
    user_id: str = "default"
    metadata: Optional[Dict[str, Any]] = None


class StopAllRequest(BaseModel):
    user_id: str = "default"
    except_components: Optional[List[str]] = None


@router.get("/all")
async def get_all_system_states(
    user_id: str = "default",
    db = Depends(get_database)
):
    """
    Get running states of all system components.
    Use this on page load to restore UI state.
    """
    from services.state_persistence import get_state_persistence
    
    persistence = get_state_persistence(db)
    if not persistence:
        return {"error": "State persistence not initialized", "states": {}}
    
    summary = await persistence.get_running_summary(user_id)
    return summary


@router.get("/{component}")
async def get_component_state(
    component: str,
    user_id: str = "default",
    db = Depends(get_database)
):
    """Get state of a specific component"""
    from services.state_persistence import get_state_persistence
    
    persistence = get_state_persistence(db)
    if not persistence:
        return {"is_running": False, "error": "State persistence not initialized"}
    
    state = await persistence.get_state(component, user_id)
    
    if not state:
        return {"component": component, "is_running": False, "exists": False}
    
    return {
        "component": component,
        "is_running": state.get("is_running", False),
        "exists": True,
        "metadata": state.get("metadata", {}),
        "started_at": state.get("started_at").isoformat() if state.get("started_at") else None,
        "updated_at": state.get("updated_at").isoformat() if state.get("updated_at") else None
    }


@router.post("/set")
async def set_component_state(
    request: SetStateRequest,
    db = Depends(get_database)
):
    """
    Set the running state of a component.
    Call this when starting/stopping any system component.
    """
    from services.state_persistence import get_state_persistence
    
    persistence = get_state_persistence(db)
    if not persistence:
        raise HTTPException(status_code=503, detail="State persistence not initialized")
    
    success = await persistence.set_state(
        component=request.component,
        is_running=request.is_running,
        user_id=request.user_id,
        metadata=request.metadata
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set state")
    
    return {
        "success": True,
        "component": request.component,
        "is_running": request.is_running
    }


@router.post("/stop-all")
async def stop_all_components(
    request: StopAllRequest,
    db = Depends(get_database)
):
    """
    Stop all running components.
    Useful for emergency shutdown or before training.
    """
    from services.state_persistence import get_state_persistence
    
    persistence = get_state_persistence(db)
    if not persistence:
        raise HTTPException(status_code=503, detail="State persistence not initialized")
    
    count = await persistence.stop_all(
        user_id=request.user_id,
        except_components=request.except_components
    )
    
    return {
        "success": True,
        "components_stopped": count
    }


@router.get("/running/summary")
async def get_running_summary(
    user_id: str = "default",
    db = Depends(get_database)
):
    """Get a summary of what's currently running"""
    from services.state_persistence import get_state_persistence
    
    persistence = get_state_persistence(db)
    if not persistence:
        return {
            "running_components": [],
            "total_running": 0,
            "error": "State persistence not initialized"
        }
    
    return await persistence.get_running_summary(user_id)
