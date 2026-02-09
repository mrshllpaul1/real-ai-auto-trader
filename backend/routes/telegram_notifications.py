"""
Telegram Notifications API Routes
==================================
Send trading alerts, portfolio updates, and risk warnings via Telegram.
"""

import logging
import os
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["Telegram Notifications"])

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


# =============================================================================
# MODELS
# =============================================================================

class TelegramConfig(BaseModel):
    chat_id: str
    enabled: bool = True
    alert_types: List[str] = ["trade", "price", "risk", "portfolio"]
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None


class SendMessageRequest(BaseModel):
    chat_id: str
    message: str
    parse_mode: str = "HTML"


class PriceAlertRequest(BaseModel):
    symbol: str
    target_price: float
    direction: str  # "above" or "below"
    chat_id: str


class NotificationPreferences(BaseModel):
    trade_executed: bool = True
    trade_copied: bool = True
    price_alerts: bool = True
    risk_warnings: bool = True
    portfolio_updates: bool = True
    daily_summary: bool = True
    weekly_report: bool = True


# =============================================================================
# TELEGRAM BOT HELPERS
# =============================================================================

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


async def send_telegram_message(chat_id: str, text: str, parse_mode: str = "HTML") -> Dict:
    """Send a message via Telegram Bot API"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return {"success": False, "error": "Bot token not configured"}
    
    url = f"{TELEGRAM_API_BASE}{bot_token}/sendMessage"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }, timeout=10)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return {"success": False, "error": str(e)}


def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_currency(value: float) -> str:
    """Format currency value"""
    if abs(value) >= 1000000:
        return f"${value/1000000:.2f}M"
    elif abs(value) >= 1000:
        return f"${value/1000:.1f}K"
    else:
        return f"${value:.2f}"


# =============================================================================
# NOTIFICATION TEMPLATES
# =============================================================================

def format_trade_notification(trade: Dict) -> str:
    """Format trade execution notification"""
    symbol = trade.get("symbol", "Unknown")
    side = trade.get("side", "").upper()
    price = trade.get("price", 0)
    amount = trade.get("amount_usd", 0)
    pnl = trade.get("pnl", 0)
    
    side_emoji = "🟢" if side == "BUY" else "🔴"
    pnl_emoji = "📈" if pnl >= 0 else "📉"
    
    return f"""
{side_emoji} <b>Trade Executed</b>

<b>Symbol:</b> {symbol}
<b>Side:</b> {side}
<b>Price:</b> ${price:,.2f}
<b>Amount:</b> {format_currency(amount)}
{f"<b>P&L:</b> {pnl_emoji} {format_currency(pnl)}" if pnl != 0 else ""}

<i>Via Tethys Trading</i>
"""


def format_price_alert(symbol: str, current_price: float, target_price: float, direction: str) -> str:
    """Format price alert notification"""
    emoji = "🚀" if direction == "above" else "⚠️"
    
    return f"""
{emoji} <b>Price Alert Triggered</b>

<b>Symbol:</b> {symbol}
<b>Current:</b> ${current_price:,.2f}
<b>Target:</b> ${target_price:,.2f}
<b>Direction:</b> {direction.capitalize()}

<i>Set via Tethys Trading</i>
"""


def format_risk_warning(warning: Dict) -> str:
    """Format risk warning notification"""
    level = warning.get("level", "warning")
    message = warning.get("message", "")
    category = warning.get("category", "general")
    
    emoji_map = {"critical": "🚨", "high": "⚠️", "medium": "📊", "low": "ℹ️"}
    emoji = emoji_map.get(level, "⚠️")
    
    return f"""
{emoji} <b>Risk Alert - {level.upper()}</b>

<b>Category:</b> {category.capitalize()}
<b>Message:</b> {message}

<i>Review your positions in Tethys</i>
"""


def format_portfolio_update(portfolio: Dict) -> str:
    """Format portfolio update notification"""
    total_value = portfolio.get("total_value", 0)
    change_24h = portfolio.get("change_24h", 0)
    change_pct = portfolio.get("change_pct_24h", 0)
    
    emoji = "📈" if change_24h >= 0 else "📉"
    
    return f"""
{emoji} <b>Portfolio Update</b>

<b>Total Value:</b> {format_currency(total_value)}
<b>24h Change:</b> {format_currency(change_24h)} ({change_pct:+.2f}%)

<b>Top Positions:</b>
"""


def format_daily_summary(data: Dict) -> str:
    """Format daily trading summary"""
    trades = data.get("trades_today", 0)
    volume = data.get("volume_today", 0)
    pnl = data.get("pnl_today", 0)
    win_rate = data.get("win_rate", 0)
    
    pnl_emoji = "📈" if pnl >= 0 else "📉"
    
    return f"""
📊 <b>Daily Trading Summary</b>

<b>Trades:</b> {trades}
<b>Volume:</b> {format_currency(volume)}
<b>P&L:</b> {pnl_emoji} {format_currency(pnl)}
<b>Win Rate:</b> {win_rate:.1f}%

<b>Best Trade:</b> {data.get('best_trade', 'N/A')}
<b>Worst Trade:</b> {data.get('worst_trade', 'N/A')}

<i>Generated by Tethys at {datetime.now().strftime('%H:%M UTC')}</i>
"""


def format_copy_trade_notification(trade: Dict, trader_name: str) -> str:
    """Format copy trade notification"""
    symbol = trade.get("symbol", "Unknown")
    side = trade.get("side", "").upper()
    amount = trade.get("amount_usd", 0)
    
    return f"""
👥 <b>Trade Copied</b>

<b>Trader:</b> {trader_name}
<b>Symbol:</b> {symbol}
<b>Side:</b> {side}
<b>Your Amount:</b> {format_currency(amount)}

<i>Via Copy Trading</i>
"""


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/config")
async def save_telegram_config(
    config: TelegramConfig,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save Telegram notification configuration"""
    config_data = {
        "user_id": user_id,
        "chat_id": config.chat_id,
        "enabled": config.enabled,
        "alert_types": config.alert_types,
        "quiet_hours_start": config.quiet_hours_start,
        "quiet_hours_end": config.quiet_hours_end,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.telegram_config.replace_one(
        {"user_id": user_id},
        config_data,
        upsert=True
    )
    
    return {"status": "success", "config": config_data}


@router.get("/config")
async def get_telegram_config(user_id: str = "default_user", db = Depends(get_database)):
    """Get Telegram notification configuration"""
    config = await db.telegram_config.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not config:
        return {
            "configured": False,
            "config": None
        }
    
    return {
        "configured": True,
        "config": config
    }


@router.post("/test")
async def test_telegram_connection(
    chat_id: str,
    db = Depends(get_database)
):
    """Test Telegram connection by sending a test message"""
    test_message = """
🤖 <b>Tethys Trading Bot Connected!</b>

Your Telegram notifications are now active.

You will receive alerts for:
• Trade executions
• Price alerts
• Risk warnings
• Portfolio updates

<i>Configure your preferences in Settings</i>
"""
    
    result = await send_telegram_message(chat_id, test_message)
    
    if result["success"]:
        return {
            "status": "success",
            "message": "Test message sent successfully",
            "chat_id": chat_id
        }
    else:
        raise HTTPException(status_code=400, detail=f"Failed to send message: {result.get('error')}")


@router.post("/send")
async def send_custom_message(
    request: SendMessageRequest,
    db = Depends(get_database)
):
    """Send a custom message to Telegram"""
    result = await send_telegram_message(request.chat_id, request.message, request.parse_mode)
    
    # Log the message
    await db.telegram_messages.insert_one({
        "chat_id": request.chat_id,
        "message": request.message,
        "type": "custom",
        "success": result["success"],
        "sent_at": datetime.now(timezone.utc).isoformat()
    })
    
    if result["success"]:
        return {"status": "sent"}
    else:
        raise HTTPException(status_code=400, detail=result.get("error"))


@router.post("/notify/trade")
async def notify_trade_executed(
    trade: Dict,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Send trade execution notification"""
    config = await db.telegram_config.find_one({"user_id": user_id})
    
    if not config or not config.get("enabled"):
        return {"status": "skipped", "reason": "notifications disabled"}
    
    if "trade" not in config.get("alert_types", []):
        return {"status": "skipped", "reason": "trade alerts disabled"}
    
    message = format_trade_notification(trade)
    result = await send_telegram_message(config["chat_id"], message)
    
    return {"status": "sent" if result["success"] else "failed"}


@router.post("/notify/price-alert")
async def notify_price_alert(
    symbol: str,
    current_price: float,
    target_price: float,
    direction: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Send price alert notification"""
    config = await db.telegram_config.find_one({"user_id": user_id})
    
    if not config or not config.get("enabled"):
        return {"status": "skipped"}
    
    message = format_price_alert(symbol, current_price, target_price, direction)
    result = await send_telegram_message(config["chat_id"], message)
    
    return {"status": "sent" if result["success"] else "failed"}


@router.post("/notify/risk")
async def notify_risk_warning(
    warning: Dict,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Send risk warning notification"""
    config = await db.telegram_config.find_one({"user_id": user_id})
    
    if not config or not config.get("enabled"):
        return {"status": "skipped"}
    
    if "risk" not in config.get("alert_types", []):
        return {"status": "skipped", "reason": "risk alerts disabled"}
    
    message = format_risk_warning(warning)
    result = await send_telegram_message(config["chat_id"], message)
    
    return {"status": "sent" if result["success"] else "failed"}


@router.post("/notify/portfolio")
async def notify_portfolio_update(
    portfolio: Dict,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Send portfolio update notification"""
    config = await db.telegram_config.find_one({"user_id": user_id})
    
    if not config or not config.get("enabled"):
        return {"status": "skipped"}
    
    message = format_portfolio_update(portfolio)
    result = await send_telegram_message(config["chat_id"], message)
    
    return {"status": "sent" if result["success"] else "failed"}


@router.post("/notify/copy-trade")
async def notify_copy_trade(
    trade: Dict,
    trader_name: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Send copy trade notification"""
    config = await db.telegram_config.find_one({"user_id": user_id})
    
    if not config or not config.get("enabled"):
        return {"status": "skipped"}
    
    message = format_copy_trade_notification(trade, trader_name)
    result = await send_telegram_message(config["chat_id"], message)
    
    return {"status": "sent" if result["success"] else "failed"}


@router.post("/notify/daily-summary")
async def send_daily_summary(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Send daily trading summary"""
    config = await db.telegram_config.find_one({"user_id": user_id})
    
    if not config or not config.get("enabled"):
        return {"status": "skipped"}
    
    # Gather daily stats
    from datetime import timedelta
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    trades = await db.trade_history.find({
        "user_id": user_id,
        "executed_at": {"$gte": today_start.isoformat()}
    }).to_list(1000)
    
    if trades:
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        total_volume = sum(t.get("amount_usd", 0) for t in trades)
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        best_trade = max(trades, key=lambda x: x.get("pnl", 0))
        worst_trade = min(trades, key=lambda x: x.get("pnl", 0))
        
        data = {
            "trades_today": len(trades),
            "volume_today": total_volume,
            "pnl_today": total_pnl,
            "win_rate": (wins / len(trades)) * 100 if trades else 0,
            "best_trade": f"{best_trade.get('symbol')} +{format_currency(best_trade.get('pnl', 0))}",
            "worst_trade": f"{worst_trade.get('symbol')} {format_currency(worst_trade.get('pnl', 0))}"
        }
    else:
        data = {
            "trades_today": 0,
            "volume_today": 0,
            "pnl_today": 0,
            "win_rate": 0,
            "best_trade": "No trades",
            "worst_trade": "No trades"
        }
    
    message = format_daily_summary(data)
    result = await send_telegram_message(config["chat_id"], message)
    
    return {"status": "sent" if result["success"] else "failed", "data": data}


# =============================================================================
# PRICE ALERTS
# =============================================================================

@router.post("/price-alert/create")
async def create_price_alert(
    alert: PriceAlertRequest,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Create a price alert"""
    import uuid
    
    alert_data = {
        "alert_id": str(uuid.uuid4()),
        "user_id": user_id,
        "chat_id": alert.chat_id,
        "symbol": alert.symbol,
        "target_price": alert.target_price,
        "direction": alert.direction,
        "triggered": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.price_alerts.insert_one(alert_data)
    
    return {
        "status": "created",
        "alert": {k: v for k, v in alert_data.items() if k != "_id"}
    }


@router.get("/price-alerts")
async def get_price_alerts(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get all price alerts for user"""
    alerts = await db.price_alerts.find(
        {"user_id": user_id, "triggered": False},
        {"_id": 0}
    ).to_list(100)
    
    return {"alerts": alerts, "total": len(alerts)}


@router.delete("/price-alert/{alert_id}")
async def delete_price_alert(
    alert_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Delete a price alert"""
    result = await db.price_alerts.delete_one({
        "alert_id": alert_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"status": "deleted"}


# =============================================================================
# MESSAGE HISTORY
# =============================================================================

@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get notification history"""
    config = await db.telegram_config.find_one({"user_id": user_id})
    
    if not config:
        return {"messages": [], "total": 0}
    
    messages = await db.telegram_messages.find(
        {"chat_id": config["chat_id"]},
        {"_id": 0}
    ).sort("sent_at", -1).limit(limit).to_list(limit)
    
    return {
        "messages": messages,
        "total": len(messages)
    }


@router.get("/status")
async def get_telegram_status(user_id: str = "default_user", db = Depends(get_database)):
    """Get Telegram integration status"""
    config = await db.telegram_config.find_one({"user_id": user_id})
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    return {
        "bot_configured": bool(bot_token),
        "user_configured": bool(config),
        "enabled": config.get("enabled", False) if config else False,
        "chat_id": config.get("chat_id") if config else None,
        "alert_types": config.get("alert_types", []) if config else []
    }
