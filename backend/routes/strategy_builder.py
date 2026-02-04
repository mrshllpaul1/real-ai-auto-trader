"""
Custom Strategy Builder API Routes
AI-assisted strategy creation endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

router = APIRouter(prefix="/strategy-builder", tags=["Custom Strategy Builder"])
logger = logging.getLogger(__name__)

# Service instances
_db = None
_strategy_builder = None


def set_dependencies(db, strategy_builder=None):
    """Set dependencies"""
    global _db, _strategy_builder
    _db = db
    _strategy_builder = strategy_builder


class NaturalLanguageStrategyRequest(BaseModel):
    description: str
    session_id: Optional[str] = "default"


class TemplateStrategyRequest(BaseModel):
    template_name: str
    customizations: Optional[Dict] = None


class SaveStrategyRequest(BaseModel):
    strategy: Dict


class SuggestionRequest(BaseModel):
    strategy: Dict
    session_id: Optional[str] = "default"


@router.get("/templates")
async def list_templates():
    """
    List all available strategy templates
    Returns pre-built templates for quick strategy creation
    """
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.list_templates()


@router.get("/templates/{template_name}")
async def get_template(template_name: str):
    """Get a specific strategy template"""
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.get_template(template_name)


@router.post("/from-template")
async def create_from_template(request: TemplateStrategyRequest):
    """
    Create a new strategy from a template
    Optionally customize risk parameters and conditions
    """
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.create_from_template(
        request.template_name,
        request.customizations
    )


@router.post("/from-description")
async def build_from_natural_language(request: NaturalLanguageStrategyRequest):
    """
    Build a strategy from natural language description
    AI will parse your description and create a structured strategy
    
    Example descriptions:
    - "Buy BTC when RSI is below 30 and sell when it reaches 70"
    - "Follow the trend using 20 and 50 day moving averages"
    - "Accumulate ETH during fear with 5% position size and 50% take profit"
    """
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.build_from_natural_language(
        request.description,
        request.session_id
    )


@router.post("/save")
async def save_strategy(request: SaveStrategyRequest):
    """Save a custom strategy"""
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.save_strategy(request.strategy)


@router.get("/strategies")
async def list_strategies(status: Optional[str] = None):
    """
    List all saved strategies
    Filter by status: 'draft', 'active', 'inactive'
    """
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.list_strategies(status)


@router.get("/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get a specific strategy by ID"""
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    strategy = await _strategy_builder.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return strategy


@router.post("/strategies/{strategy_id}/activate")
async def activate_strategy(strategy_id: str):
    """Activate a strategy for live/paper trading"""
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.activate_strategy(strategy_id)


@router.post("/strategies/{strategy_id}/deactivate")
async def deactivate_strategy(strategy_id: str):
    """Deactivate a strategy"""
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.deactivate_strategy(strategy_id)


@router.get("/indicators")
async def get_available_indicators():
    """Get all available indicators for strategy building"""
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return _strategy_builder.get_available_indicators()


@router.post("/suggestions")
async def get_ai_suggestions(request: SuggestionRequest):
    """
    Get AI suggestions to improve a strategy
    Provides recommendations for entry/exit conditions, risk management, etc.
    """
    if not _strategy_builder:
        raise HTTPException(status_code=503, detail="Strategy builder not initialized")
    
    return await _strategy_builder.get_ai_suggestions(
        request.strategy,
        request.session_id
    )


@router.get("/status")
async def get_status():
    """Get strategy builder service status"""
    return {
        'initialized': _strategy_builder is not None,
        'ai_enabled': _strategy_builder.ai_chat is not None if _strategy_builder else False,
        'templates_available': len(_strategy_builder.templates) if _strategy_builder else 0,
        'timestamp': datetime.utcnow().isoformat()
    }
