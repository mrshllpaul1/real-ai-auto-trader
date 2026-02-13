"""
Dashboard Customization API Routes
===================================
Allow users to customize their dashboard layout, widgets, and theme.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Customization"])

# Global database reference
_db = None


def set_db(db):
    """Set database reference"""
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

class WidgetConfig(BaseModel):
    widget_id: str
    type: str  # portfolio, chart, positions, triggers, news, ai_signals, etc.
    title: Optional[str] = None
    position: Dict[str, int]  # {x, y, w, h} for grid layout
    settings: Optional[Dict[str, Any]] = None
    visible: bool = True


class LayoutConfig(BaseModel):
    layout_id: Optional[str] = None
    name: str = "Default"
    widgets: List[WidgetConfig]
    columns: int = 12
    row_height: int = 100


class ThemeConfig(BaseModel):
    mode: str = "dark"  # dark, light, system
    accent_color: str = "#00FF94"  # Primary accent
    secondary_color: str = "#9D00FF"  # Secondary accent
    danger_color: str = "#FF0055"
    warning_color: str = "#FFB800"
    chart_colors: List[str] = ["#00FF94", "#9D00FF", "#007AFF", "#FF9500", "#FF0055"]
    background_blur: bool = True
    animations_enabled: bool = True
    compact_mode: bool = False


class DashboardPreferences(BaseModel):
    default_page: str = "/"
    sidebar_collapsed: bool = False
    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    notifications_position: str = "top-right"
    show_portfolio_value: bool = True
    currency: str = "USD"
    timezone: str = "UTC"


# =============================================================================
# DEFAULT CONFIGURATIONS
# =============================================================================

DEFAULT_WIDGETS = [
    {
        "widget_id": "portfolio_summary",
        "type": "portfolio",
        "title": "Portfolio Overview",
        "position": {"x": 0, "y": 0, "w": 6, "h": 2},
        "settings": {"show_chart": True, "show_breakdown": True},
        "visible": True
    },
    {
        "widget_id": "price_chart",
        "type": "chart",
        "title": "Price Chart",
        "position": {"x": 6, "y": 0, "w": 6, "h": 3},
        "settings": {"symbol": "BTC/USD", "interval": "1h"},
        "visible": True
    },
    {
        "widget_id": "active_positions",
        "type": "positions",
        "title": "Active Positions",
        "position": {"x": 0, "y": 2, "w": 6, "h": 2},
        "settings": {"show_pnl": True},
        "visible": True
    },
    {
        "widget_id": "ai_signals",
        "type": "signals",
        "title": "AI Trading Signals",
        "position": {"x": 0, "y": 4, "w": 4, "h": 2},
        "settings": {"max_signals": 5},
        "visible": True
    },
    {
        "widget_id": "news_feed",
        "type": "news",
        "title": "Latest News",
        "position": {"x": 4, "y": 4, "w": 4, "h": 2},
        "settings": {"max_items": 5, "filter": "all"},
        "visible": True
    },
    {
        "widget_id": "quick_trade",
        "type": "trade",
        "title": "Quick Trade",
        "position": {"x": 8, "y": 4, "w": 4, "h": 2},
        "settings": {"default_symbol": "BTC/USD"},
        "visible": True
    }
]


# =============================================================================
# LAYOUT ENDPOINTS
# =============================================================================

@router.get("/layout")
async def get_dashboard_layout(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's dashboard layout configuration"""
    try:
        layout = await db.dashboard_layouts.find_one(
            {"user_id": user_id, "is_active": True},
            {"_id": 0}
        )
        
        if not layout:
            # Return default layout
            return {
                "layout_id": "default",
                "name": "Default Layout",
                "widgets": DEFAULT_WIDGETS,
                "columns": 12,
                "row_height": 100,
                "is_default": True
            }
        
        return layout
    except Exception as e:
        logger.error(f"Error getting dashboard layout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/layout")
async def save_dashboard_layout(
    layout: LayoutConfig,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save dashboard layout configuration"""
    try:
        layout_data = {
            "layout_id": layout.layout_id or str(uuid.uuid4()),
            "user_id": user_id,
            "name": layout.name,
            "widgets": [w.dict() for w in layout.widgets],
            "columns": layout.columns,
            "row_height": layout.row_height,
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Deactivate other layouts
        await db.dashboard_layouts.update_many(
            {"user_id": user_id},
            {"$set": {"is_active": False}}
        )
        
        # Save new layout
        await db.dashboard_layouts.replace_one(
            {"user_id": user_id, "layout_id": layout_data["layout_id"]},
            layout_data,
            upsert=True
        )
        
        return {"status": "success", "layout": layout_data}
    except Exception as e:
        logger.error(f"Error saving dashboard layout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layouts")
async def list_saved_layouts(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get all saved layouts for user"""
    try:
        layouts = await db.dashboard_layouts.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(20)
        
        # Add default layout if no custom layouts
        if not layouts:
            layouts = [{
                "layout_id": "default",
                "name": "Default Layout",
                "is_active": True,
                "is_default": True
            }]
        
        return {"layouts": layouts}
    except Exception as e:
        logger.error(f"Error listing layouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/layout/{layout_id}")
async def delete_layout(
    layout_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Delete a saved layout"""
    try:
        result = await db.dashboard_layouts.delete_one({
            "user_id": user_id,
            "layout_id": layout_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Layout not found")
        
        return {"status": "deleted", "layout_id": layout_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting layout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# THEME ENDPOINTS
# =============================================================================

@router.get("/theme")
async def get_theme(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's theme configuration"""
    try:
        theme = await db.dashboard_themes.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not theme:
            # Return default dark theme
            return {
                "mode": "dark",
                "accent_color": "#00FF94",
                "secondary_color": "#9D00FF",
                "danger_color": "#FF0055",
                "warning_color": "#FFB800",
                "chart_colors": ["#00FF94", "#9D00FF", "#007AFF", "#FF9500", "#FF0055"],
                "background_blur": True,
                "animations_enabled": True,
                "compact_mode": False,
                "is_default": True
            }
        
        return theme
    except Exception as e:
        logger.error(f"Error getting theme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/theme")
async def save_theme(
    theme: ThemeConfig,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save theme configuration"""
    try:
        theme_data = {
            "user_id": user_id,
            **theme.dict(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.dashboard_themes.replace_one(
            {"user_id": user_id},
            theme_data,
            upsert=True
        )
        
        return {"status": "success", "theme": theme_data}
    except Exception as e:
        logger.error(f"Error saving theme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/theme/presets")
async def get_theme_presets():
    """Get available theme presets"""
    return {
        "presets": [
            {
                "name": "Tethys Dark",
                "description": "Default dark theme with green and purple accents",
                "config": {
                    "mode": "dark",
                    "accent_color": "#00FF94",
                    "secondary_color": "#9D00FF",
                    "danger_color": "#FF0055",
                    "warning_color": "#FFB800",
                    "chart_colors": ["#00FF94", "#9D00FF", "#007AFF", "#FF9500", "#FF0055"],
                    "background_blur": True
                }
            },
            {
                "name": "Ocean Blue",
                "description": "Cool blue theme for reduced eye strain",
                "config": {
                    "mode": "dark",
                    "accent_color": "#00B8FF",
                    "secondary_color": "#0066FF",
                    "danger_color": "#FF4444",
                    "warning_color": "#FFB800",
                    "chart_colors": ["#00B8FF", "#0066FF", "#00FF94", "#9D00FF", "#FF4444"],
                    "background_blur": True
                }
            },
            {
                "name": "Neon Purple",
                "description": "Vibrant purple theme for a futuristic feel",
                "config": {
                    "mode": "dark",
                    "accent_color": "#9D00FF",
                    "secondary_color": "#FF00FF",
                    "danger_color": "#FF0055",
                    "warning_color": "#FFB800",
                    "chart_colors": ["#9D00FF", "#FF00FF", "#00FF94", "#00B8FF", "#FF0055"],
                    "background_blur": True
                }
            },
            {
                "name": "Monochrome",
                "description": "Clean grayscale theme for minimalists",
                "config": {
                    "mode": "dark",
                    "accent_color": "#FFFFFF",
                    "secondary_color": "#888888",
                    "danger_color": "#FF4444",
                    "warning_color": "#FFAA00",
                    "chart_colors": ["#FFFFFF", "#CCCCCC", "#999999", "#666666", "#333333"],
                    "background_blur": False
                }
            },
            {
                "name": "Forest",
                "description": "Nature-inspired green theme",
                "config": {
                    "mode": "dark",
                    "accent_color": "#22C55E",
                    "secondary_color": "#059669",
                    "danger_color": "#DC2626",
                    "warning_color": "#EAB308",
                    "chart_colors": ["#22C55E", "#059669", "#0D9488", "#0891B2", "#7C3AED"],
                    "background_blur": True
                }
            },
            {
                "name": "Light Mode",
                "description": "Clean light theme for daytime use",
                "config": {
                    "mode": "light",
                    "accent_color": "#059669",
                    "secondary_color": "#7C3AED",
                    "danger_color": "#DC2626",
                    "warning_color": "#D97706",
                    "chart_colors": ["#059669", "#7C3AED", "#0284C7", "#EA580C", "#DC2626"],
                    "background_blur": False
                }
            }
        ]
    }


# =============================================================================
# PREFERENCES ENDPOINTS
# =============================================================================

@router.get("/preferences")
async def get_preferences(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's dashboard preferences"""
    try:
        prefs = await db.dashboard_preferences.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not prefs:
            return {
                "default_page": "/",
                "sidebar_collapsed": False,
                "auto_refresh": True,
                "refresh_interval": 30,
                "notifications_position": "top-center",
                "show_portfolio_value": True,
                "currency": "USD",
                "timezone": "UTC",
                "is_default": True
            }
        
        return prefs
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def save_preferences(
    preferences: DashboardPreferences,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save dashboard preferences"""
    try:
        pref_data = {
            "user_id": user_id,
            **preferences.dict(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.dashboard_preferences.replace_one(
            {"user_id": user_id},
            pref_data,
            upsert=True
        )
        
        return {"status": "success", "preferences": pref_data}
    except Exception as e:
        logger.error(f"Error saving preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WIDGET ENDPOINTS
# =============================================================================

@router.get("/widgets")
async def get_available_widgets():
    """Get list of available widget types"""
    return {
        "widgets": [
            {
                "type": "portfolio",
                "name": "Portfolio Overview",
                "description": "Shows total portfolio value, P&L, and allocation",
                "default_size": {"w": 6, "h": 2},
                "settings_schema": {
                    "show_chart": {"type": "boolean", "default": True},
                    "show_breakdown": {"type": "boolean", "default": True}
                }
            },
            {
                "type": "chart",
                "name": "Price Chart",
                "description": "Interactive price chart with indicators",
                "default_size": {"w": 6, "h": 3},
                "settings_schema": {
                    "symbol": {"type": "string", "default": "BTC/USD"},
                    "interval": {"type": "string", "options": ["1m", "5m", "15m", "1h", "4h", "1d"]}
                }
            },
            {
                "type": "positions",
                "name": "Active Positions",
                "description": "Current open positions with P&L",
                "default_size": {"w": 6, "h": 2},
                "settings_schema": {
                    "show_pnl": {"type": "boolean", "default": True}
                }
            },
            {
                "type": "signals",
                "name": "AI Trading Signals",
                "description": "Latest AI-generated trading signals",
                "default_size": {"w": 4, "h": 2},
                "settings_schema": {
                    "max_signals": {"type": "number", "default": 5}
                }
            },
            {
                "type": "news",
                "name": "News Feed",
                "description": "Latest crypto news and sentiment",
                "default_size": {"w": 4, "h": 2},
                "settings_schema": {
                    "max_items": {"type": "number", "default": 5},
                    "filter": {"type": "string", "options": ["all", "positive", "negative"]}
                }
            },
            {
                "type": "trade",
                "name": "Quick Trade",
                "description": "Fast buy/sell widget",
                "default_size": {"w": 4, "h": 2},
                "settings_schema": {
                    "default_symbol": {"type": "string", "default": "BTC/USD"}
                }
            },
            {
                "type": "triggers",
                "name": "Event Triggers",
                "description": "Active event triggers status",
                "default_size": {"w": 4, "h": 2},
                "settings_schema": {}
            },
            {
                "type": "market_maker",
                "name": "Market Maker",
                "description": "Market maker status and orders",
                "default_size": {"w": 4, "h": 2},
                "settings_schema": {}
            },
            {
                "type": "copy_trading",
                "name": "Copy Trading",
                "description": "Traders you're following",
                "default_size": {"w": 4, "h": 2},
                "settings_schema": {
                    "max_traders": {"type": "number", "default": 5}
                }
            },
            {
                "type": "watchlist",
                "name": "Watchlist",
                "description": "Track your favorite coins",
                "default_size": {"w": 3, "h": 3},
                "settings_schema": {
                    "coins": {"type": "array", "default": ["BTC", "ETH", "SOL"]}
                }
            },
            {
                "type": "stats",
                "name": "Trading Stats",
                "description": "Win rate, total trades, P&L stats",
                "default_size": {"w": 3, "h": 1},
                "settings_schema": {
                    "timeframe": {"type": "string", "options": ["24h", "7d", "30d", "all"]}
                }
            },
            {
                "type": "calendar",
                "name": "Event Calendar",
                "description": "Upcoming crypto events",
                "default_size": {"w": 4, "h": 2},
                "settings_schema": {}
            }
        ]
    }


@router.post("/widget/add")
async def add_widget(
    widget: WidgetConfig,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Add a widget to the dashboard"""
    try:
        # Get current layout
        layout = await db.dashboard_layouts.find_one(
            {"user_id": user_id, "is_active": True}
        )
        
        if not layout:
            # Create new layout with widget
            layout = {
                "layout_id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": "Custom Layout",
                "widgets": [widget.dict()],
                "columns": 12,
                "row_height": 100,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.dashboard_layouts.insert_one(layout)
        else:
            # Add widget to existing layout
            await db.dashboard_layouts.update_one(
                {"user_id": user_id, "is_active": True},
                {
                    "$push": {"widgets": widget.dict()},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                }
            )
        
        return {"status": "added", "widget": widget.dict()}
    except Exception as e:
        logger.error(f"Error adding widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/widget/{widget_id}")
async def remove_widget(
    widget_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Remove a widget from the dashboard"""
    try:
        result = await db.dashboard_layouts.update_one(
            {"user_id": user_id, "is_active": True},
            {
                "$pull": {"widgets": {"widget_id": widget_id}},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return {"status": "removed", "widget_id": widget_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))
