"""
Trading Journal API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/journal", tags=["Trading Journal"])

# Global reference
journal_service = None


def set_dependencies(service):
    global journal_service
    journal_service = service


class RecordTradeRequest(BaseModel):
    trade_type: str
    coin_id: str
    symbol: str
    action: str
    amount_usd: float
    price: float
    quantity: float
    is_paper: Optional[bool] = True
    ai_reasoning: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_factors: Optional[List[dict]] = None
    is_gem: Optional[bool] = False
    pnl_usd: Optional[float] = None
    pnl_pct: Optional[float] = None
    exit_reason: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class AddNoteRequest(BaseModel):
    note: str


class AddTagsRequest(BaseModel):
    tags: List[str]


@router.post("/record")
async def record_trade(request: RecordTradeRequest):
    """Record a trade in the journal"""
    if journal_service is None:
        raise HTTPException(status_code=500, detail="Journal service not initialized")
    
    return await journal_service.record_trade(**request.dict())


@router.get("/entries")
async def get_journal_entries(
    limit: int = 50,
    offset: int = 0,
    coin_id: Optional[str] = None,
    trade_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    is_paper: Optional[bool] = None,
    tags: Optional[str] = None
):
    """Get journal entries with filters"""
    if journal_service is None:
        raise HTTPException(status_code=500, detail="Journal service not initialized")
    
    tag_list = tags.split(",") if tags else None
    
    return await journal_service.get_journal_entries(
        limit=limit,
        offset=offset,
        coin_id=coin_id,
        trade_type=trade_type,
        date_from=date_from,
        date_to=date_to,
        is_paper=is_paper,
        tags=tag_list
    )


@router.get("/daily")
async def get_daily_summary(date: Optional[str] = None):
    """Get daily trading summary"""
    if journal_service is None:
        raise HTTPException(status_code=500, detail="Journal service not initialized")
    
    return await journal_service.get_daily_summary(date=date)


@router.get("/stats")
async def get_performance_stats(days: int = 30):
    """Get performance statistics"""
    if journal_service is None:
        raise HTTPException(status_code=500, detail="Journal service not initialized")
    
    return await journal_service.get_performance_stats(days=days)


@router.get("/ai-insights")
async def get_ai_insights(days: int = 30):
    """Get AI decision insights and patterns"""
    if journal_service is None:
        raise HTTPException(status_code=500, detail="Journal service not initialized")
    
    return await journal_service.get_ai_insights_summary(days=days)


@router.post("/entries/{trade_id}/note")
async def add_note(trade_id: str, request: AddNoteRequest):
    """Add a note to a trade"""
    if journal_service is None:
        raise HTTPException(status_code=500, detail="Journal service not initialized")
    
    return await journal_service.add_note_to_trade(trade_id, request.note)


@router.post("/entries/{trade_id}/tags")
async def add_tags(trade_id: str, request: AddTagsRequest):
    """Add tags to a trade"""
    if journal_service is None:
        raise HTTPException(status_code=500, detail="Journal service not initialized")
    
    return await journal_service.add_tags_to_trade(trade_id, request.tags)
