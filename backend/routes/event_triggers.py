"""
Event Triggers API Routes
Endpoints for creating and managing custom event triggers for automated trading.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio

router = APIRouter(prefix="/triggers", tags=["Event Triggers"])

# Dependencies
_db = None
_trigger_service = None


def set_dependencies(db, trigger_service):
    """Set dependencies from server.py"""
    global _db, _trigger_service
    _db = db
    _trigger_service = trigger_service


# Request models
class CreateTriggerRequest(BaseModel):
    trigger_id: str
    name: str
    keywords: List[str]
    coins: List[str]
    action: str  # "buy", "sell", "alert"
    amount_usd: Optional[float] = None
    amount_pct: Optional[float] = None
    sentiment_filter: Optional[str] = None  # "positive", "negative", "any"
    category_filter: Optional[str] = None
    cooldown_hours: Optional[int] = 24
    enabled: Optional[bool] = True


class CreateFromTemplateRequest(BaseModel):
    template_name: str
    trigger_id: str
    amount_usd: Optional[float] = None
    amount_pct: Optional[float] = None
    enabled: Optional[bool] = True


class UpdateTriggerRequest(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    coins: Optional[List[str]] = None
    action: Optional[str] = None
    amount_usd: Optional[float] = None
    amount_pct: Optional[float] = None
    sentiment_filter: Optional[str] = None
    category_filter: Optional[str] = None
    cooldown_hours: Optional[int] = None
    enabled: Optional[bool] = None


class ManualEventRequest(BaseModel):
    """Request model for manually adding a missed event"""
    title: str
    body: Optional[str] = ""
    sentiment: Optional[str] = "NEUTRAL"  # POSITIVE, NEGATIVE, NEUTRAL
    source: Optional[str] = "manual"
    url: Optional[str] = None


@router.get("/status")
async def get_trigger_service_status():
    """Get event trigger service status and statistics"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    return await _trigger_service.get_stats()


@router.get("/templates")
async def get_trigger_templates():
    """
    Get available pre-built trigger templates.
    
    Templates include:
    - elon_doge: Buy DOGE on Elon Musk positive tweets
    - elon_btc: Alert on Elon Bitcoin mentions
    - sec_regulatory: Sell on SEC negative actions
    - etf_approval: Buy on ETF approval news
    - exchange_hack: Alert on security breaches
    - china_ban: Sell on China crypto bans
    - institutional_buy: Buy on institutional purchases
    - whale_alert: Alert on large crypto movements
    """
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    templates = await _trigger_service.get_templates()
    return {
        "count": len(templates),
        "templates": templates
    }


@router.post("/create")
async def create_trigger(request: CreateTriggerRequest):
    """
    Create a custom event trigger.
    
    Example:
    {
        "trigger_id": "my_elon_trigger",
        "name": "Elon Bitcoin Tweets",
        "keywords": ["elon", "musk", "bitcoin"],
        "coins": ["BTC"],
        "action": "buy",
        "amount_usd": 100,
        "sentiment_filter": "positive",
        "cooldown_hours": 12
    }
    
    Actions:
    - "buy": Create buy order (requires confirmation)
    - "sell": Create sell order (requires confirmation)  
    - "alert": Send notification only
    """
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    from services.event_triggers import EventTrigger
    
    trigger = EventTrigger(
        trigger_id=request.trigger_id,
        name=request.name,
        keywords=request.keywords,
        coins=request.coins,
        action=request.action,
        amount_usd=request.amount_usd,
        amount_pct=request.amount_pct,
        sentiment_filter=request.sentiment_filter,
        category_filter=request.category_filter,
        cooldown_hours=request.cooldown_hours or 24,
        enabled=request.enabled if request.enabled is not None else True
    )
    
    result = await _trigger_service.create_trigger(trigger)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/create-from-template")
async def create_trigger_from_template(request: CreateFromTemplateRequest):
    """
    Create a trigger from a pre-built template.
    
    Example:
    {
        "template_name": "elon_doge",
        "trigger_id": "my_elon_doge",
        "amount_usd": 50
    }
    """
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    result = await _trigger_service.create_from_template(
        template_name=request.template_name,
        trigger_id=request.trigger_id,
        amount_usd=request.amount_usd,
        amount_pct=request.amount_pct,
        enabled=request.enabled if request.enabled is not None else True
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/list")
async def list_triggers(enabled_only: bool = False):
    """List all triggers"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    triggers = await _trigger_service.list_triggers(enabled_only)
    return {
        "count": len(triggers),
        "triggers": triggers
    }


@router.get("/{trigger_id}")
async def get_trigger(trigger_id: str):
    """Get a specific trigger by ID"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    trigger = await _trigger_service.get_trigger(trigger_id)
    
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    return trigger.to_dict()


@router.put("/{trigger_id}")
async def update_trigger(trigger_id: str, request: UpdateTriggerRequest):
    """Update a trigger"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    updates = {k: v for k, v in request.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = await _trigger_service.update_trigger(trigger_id, updates)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.delete("/{trigger_id}")
async def delete_trigger(trigger_id: str):
    """Delete a trigger"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    result = await _trigger_service.delete_trigger(trigger_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/{trigger_id}/enable")
async def enable_trigger(trigger_id: str):
    """Enable a trigger"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    return await _trigger_service.toggle_trigger(trigger_id, True)


@router.post("/{trigger_id}/disable")
async def disable_trigger(trigger_id: str):
    """Disable a trigger"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    return await _trigger_service.toggle_trigger(trigger_id, False)


@router.post("/check-now")
async def check_events_now():
    """
    Manually check recent news against all enabled triggers.
    
    This will:
    1. Fetch latest 30 news articles from CoinDesk
    2. Check each article against all enabled triggers
    3. Execute matching triggers (alerts or trade intents)
    
    Normally this runs automatically via scheduler.
    """
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    executions = await _trigger_service.check_recent_events()
    
    return {
        "status": "checked",
        "triggers_executed": len(executions),
        "executions": executions
    }


@router.post("/manual-event")
async def process_manual_event(request: ManualEventRequest):
    """
    Manually add an event that may have been missed by news feeds.
    
    Use this when you notice breaking news that wasn't picked up automatically.
    The event will be checked against all enabled triggers.
    
    Example:
    {
        "title": "BlackRock begins tokenizing its assets",
        "body": "BlackRock announced today that they will tokenize $10B worth of assets on Ethereum",
        "sentiment": "POSITIVE",
        "source": "twitter"
    }
    
    Sentiment options: POSITIVE, NEGATIVE, NEUTRAL
    """
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    from datetime import timezone
    
    # Create event data structure
    event_data = {
        "title": request.title,
        "body": request.body or "",
        "sentiment": request.sentiment.upper() if request.sentiment else "NEUTRAL",
        "categories": [],
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": request.url,
        "source": request.source or "manual"
    }
    
    # Get all enabled triggers
    triggers_data = await _trigger_service.list_triggers(enabled_only=True)
    
    from services.event_triggers import EventTrigger
    triggers = [EventTrigger.from_dict(t) for t in triggers_data]
    
    executions = []
    matched_triggers = []
    
    # Check each trigger against this manual event
    for trigger in triggers:
        match_result = _trigger_service.check_event_matches_trigger(trigger, event_data)
        
        if match_result["matches"]:
            matched_triggers.append({
                "trigger_id": trigger.trigger_id,
                "name": trigger.name,
                "action": trigger.action,
                "confidence": match_result.get("confidence", 0),
                "keyword_matches": match_result.get("keyword_matches", [])
            })
            
            # Execute the trigger
            execution = await _trigger_service.execute_trigger(trigger, event_data, match_result)
            executions.append(execution)
    
    # Store the manual event in history
    if _db:
        await _db.manual_events.insert_one({
            "event": event_data,
            "matched_triggers": [t["trigger_id"] for t in matched_triggers],
            "executions_count": len(executions),
            "created_at": datetime.now(timezone.utc)
        })
    
    return {
        "status": "processed",
        "event": event_data,
        "triggers_checked": len(triggers),
        "triggers_matched": len(matched_triggers),
        "matched_triggers": matched_triggers,
        "executions": executions
    }


@router.get("/history/all")
async def get_all_execution_history(limit: int = 50):
    """Get execution history for all triggers"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    history = await _trigger_service.get_execution_history(limit=limit)
    return {
        "count": len(history),
        "history": history
    }


@router.get("/history/{trigger_id}")
async def get_trigger_execution_history(trigger_id: str, limit: int = 20):
    """Get execution history for a specific trigger"""
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    history = await _trigger_service.get_execution_history(trigger_id, limit)
    return {
        "trigger_id": trigger_id,
        "count": len(history),
        "history": history
    }


@router.get("/performance/dashboard")
async def get_trigger_performance_dashboard():
    """
    Get comprehensive trigger performance analytics for dashboard.
    Includes fire counts, success rates, and P&L per trigger.
    """
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    # Get all triggers
    triggers = await _trigger_service.list_triggers(enabled_only=False)
    
    # Get all execution history
    all_history = await _db.trigger_executions.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(1000).to_list(1000)
    
    # Calculate metrics per trigger
    trigger_metrics = {}
    
    for trigger in triggers:
        trigger_id = trigger.get('trigger_id')
        trigger_history = [h for h in all_history if h.get('trigger_id') == trigger_id]
        
        # Calculate metrics
        total_fires = len(trigger_history)
        successful_fires = len([h for h in trigger_history if h.get('success', False)])
        success_rate = (successful_fires / total_fires * 100) if total_fires > 0 else 0
        
        # Calculate P&L if available
        total_pnl = sum(h.get('pnl_usd', 0) for h in trigger_history if h.get('pnl_usd'))
        
        # Get last fire time
        last_fired = trigger_history[0].get('timestamp') if trigger_history else None
        
        trigger_metrics[trigger_id] = {
            "trigger_id": trigger_id,
            "name": trigger.get('name', trigger_id),
            "keywords": trigger.get('keywords', []),
            "action": trigger.get('action'),
            "enabled": trigger.get('enabled', True),
            "total_fires": total_fires,
            "successful_fires": successful_fires,
            "success_rate": round(success_rate, 1),
            "total_pnl_usd": round(total_pnl, 2),
            "last_fired": last_fired,
            "category": _categorize_trigger(trigger.get('keywords', []))
        }
    
    # Aggregate by category
    categories = {}
    for metrics in trigger_metrics.values():
        cat = metrics['category']
        if cat not in categories:
            categories[cat] = {
                "total_triggers": 0,
                "total_fires": 0,
                "total_pnl": 0,
                "triggers": []
            }
        categories[cat]['total_triggers'] += 1
        categories[cat]['total_fires'] += metrics['total_fires']
        categories[cat]['total_pnl'] += metrics['total_pnl_usd']
        categories[cat]['triggers'].append(metrics['trigger_id'])
    
    # Sort triggers by fires for top performers
    sorted_by_fires = sorted(trigger_metrics.values(), key=lambda x: x['total_fires'], reverse=True)
    sorted_by_pnl = sorted(trigger_metrics.values(), key=lambda x: x['total_pnl_usd'], reverse=True)
    
    return {
        "summary": {
            "total_triggers": len(triggers),
            "enabled_triggers": len([t for t in triggers if t.get('enabled', True)]),
            "total_executions": len(all_history),
            "overall_success_rate": round(
                len([h for h in all_history if h.get('success', False)]) / len(all_history) * 100
                if all_history else 0, 1
            ),
            "total_pnl_usd": round(sum(h.get('pnl_usd', 0) for h in all_history if h.get('pnl_usd')), 2)
        },
        "by_category": categories,
        "trigger_metrics": list(trigger_metrics.values()),
        "top_performers": {
            "by_fires": sorted_by_fires[:5],
            "by_pnl": sorted_by_pnl[:5]
        },
        "recent_executions": all_history[:20]
    }


def _categorize_trigger(keywords: list) -> str:
    """Categorize trigger based on keywords"""
    keywords_lower = [k.lower() for k in keywords]
    keywords_text = ' '.join(keywords_lower)
    
    if any(k in keywords_text for k in ['elon', 'musk', 'doge', 'tweet']):
        return 'celebrity'
    elif any(k in keywords_text for k in ['sec', 'regulation', 'ban', 'legal', 'lawsuit']):
        return 'regulatory'
    elif any(k in keywords_text for k in ['whale', 'large', 'million', 'billion', 'institutional']):
        return 'whale'
    elif any(k in keywords_text for k in ['etf', 'approval', 'blackrock', 'grayscale']):
        return 'institutional'
    elif any(k in keywords_text for k in ['hack', 'exploit', 'security', 'breach']):
        return 'security'
    elif any(k in keywords_text for k in ['partner', 'integration', 'launch', 'announce']):
        return 'partnership'
    elif any(k in keywords_text for k in ['fed', 'fomc', 'rate', 'inflation', 'gdp']):
        return 'macro'
    elif any(k in keywords_text for k in ['crash', 'dump', 'panic', 'capitulation']):
        return 'market_event'
    else:
        return 'other'


# Scheduler job integration
@router.post("/schedule/enable")
async def enable_scheduled_checking(interval_minutes: int = 15):
    """
    Enable scheduled trigger checking.
    
    Will check news every N minutes against enabled triggers.
    """
    if not _trigger_service:
        raise HTTPException(status_code=503, detail="Trigger service not initialized")
    
    # This would integrate with the scheduler service
    # For now, return info about manual checking
    return {
        "status": "info",
        "message": f"Automatic checking every {interval_minutes} minutes requires scheduler integration.",
        "manual_check": "Use POST /api/triggers/check-now to manually check events",
        "recommendation": "Add to scheduler via POST /api/scheduler/jobs/trigger-check"
    }
