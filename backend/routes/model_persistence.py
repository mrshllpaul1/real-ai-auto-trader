"""
Model Persistence API Routes
Endpoints for managing saved models
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import os
from pathlib import Path

router = APIRouter(prefix="/models", tags=["Model Persistence"])

MODELS_DIR = Path(__file__).parent.parent / "models"


@router.get("/")
async def list_saved_models():
    """
    List all saved models with their metadata
    """
    models = []
    
    if MODELS_DIR.exists():
        for model_dir in MODELS_DIR.iterdir():
            if model_dir.is_dir():
                model_type = model_dir.name
                metadata_file = model_dir / "metadata.json"
                
                model_info = {
                    "model_type": model_type,
                    "exists": True,
                    "files": [f.name for f in model_dir.iterdir() if f.is_file()]
                }
                
                if metadata_file.exists():
                    import json
                    with open(metadata_file, 'r') as f:
                        model_info["metadata"] = json.load(f)
                
                models.append(model_info)
    
    return {
        "count": len(models),
        "models": models,
        "models_dir": str(MODELS_DIR)
    }


@router.get("/{model_type}")
async def get_model_info(model_type: str):
    """
    Get info about a specific saved model
    """
    model_dir = MODELS_DIR / model_type
    
    if not model_dir.exists():
        raise HTTPException(status_code=404, detail=f"Model {model_type} not found")
    
    metadata_file = model_dir / "metadata.json"
    metadata = None
    
    if metadata_file.exists():
        import json
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    
    files = [f.name for f in model_dir.iterdir() if f.is_file()]
    total_size = sum(f.stat().st_size for f in model_dir.iterdir() if f.is_file())
    
    return {
        "model_type": model_type,
        "files": files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "metadata": metadata
    }


@router.delete("/{model_type}")
async def delete_saved_model(model_type: str):
    """
    Delete a saved model
    """
    from services.model_persistence import ModelPersistence
    
    persistence = ModelPersistence(model_type)
    
    if not persistence.model_exists():
        raise HTTPException(status_code=404, detail=f"Model {model_type} not found")
    
    if persistence.delete_model():
        return {"status": "deleted", "model_type": model_type}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete model")


@router.post("/{model_type}/save")
async def trigger_model_save(model_type: str):
    """
    Manually trigger saving the current in-memory model
    """
    if model_type == "rl_agent":
        from services.rl_trading_agent import get_rl_agent
        # Need db reference - this is a simplified version
        return {"error": "Use the training endpoint to save RL agent"}
    
    elif model_type == "transformer":
        from services.transformer_predictor import get_transformer_predictor
        return {"error": "Use the training endpoint to save Transformer"}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown model type: {model_type}")


@router.get("/status/all")
async def get_all_models_status():
    """
    Get status of all model types (saved on disk vs loaded in memory)
    """
    from services.model_persistence import (
        get_rl_persistence, 
        get_transformer_persistence,
        get_regime_persistence
    )
    
    models_status = []
    
    # RL Agent
    rl_pers = get_rl_persistence()
    models_status.append({
        "model_type": "rl_agent",
        "saved_to_disk": rl_pers.model_exists(),
        "metadata": rl_pers.get_metadata()
    })
    
    # Transformer
    trans_pers = get_transformer_persistence()
    models_status.append({
        "model_type": "transformer",
        "saved_to_disk": trans_pers.model_exists(),
        "metadata": trans_pers.get_metadata()
    })
    
    # Regime
    regime_pers = get_regime_persistence()
    models_status.append({
        "model_type": "regime",
        "saved_to_disk": regime_pers.model_exists(),
        "metadata": regime_pers.get_metadata()
    })
    
    return {
        "models": models_status,
        "models_dir": str(MODELS_DIR)
    }
