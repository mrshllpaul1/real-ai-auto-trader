"""
Custom Event Triggers for Automated Trading
Monitors news events and executes trades based on user-defined triggers.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import re


class EventTrigger:
    """Represents a custom event trigger for automated trading"""
    
    def __init__(
        self,
        trigger_id: str,
        name: str,
        keywords: List[str],
        coins: List[str],
        action: str,  # "buy", "sell", "alert"
        amount_usd: float = None,
        amount_pct: float = None,  # Percentage of portfolio
        sentiment_filter: str = None,  # "positive", "negative", "any"
        category_filter: str = None,
        cooldown_hours: int = 24,
        enabled: bool = True,
        created_at: datetime = None
    ):
        self.trigger_id = trigger_id
        self.name = name
        self.keywords = [k.lower() for k in keywords]
        self.coins = [c.upper() for c in coins]
        self.action = action.lower()
        self.amount_usd = amount_usd
        self.amount_pct = amount_pct
        self.sentiment_filter = sentiment_filter
        self.category_filter = category_filter
        self.cooldown_hours = cooldown_hours
        self.enabled = enabled
        self.created_at = created_at or datetime.now(timezone.utc)
        self.last_triggered = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "name": self.name,
            "keywords": self.keywords,
            "coins": self.coins,
            "action": self.action,
            "amount_usd": self.amount_usd,
            "amount_pct": self.amount_pct,
            "sentiment_filter": self.sentiment_filter,
            "category_filter": self.category_filter,
            "cooldown_hours": self.cooldown_hours,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventTrigger':
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        
        trigger = cls(
            trigger_id=data["trigger_id"],
            name=data["name"],
            keywords=data["keywords"],
            coins=data["coins"],
            action=data["action"],
            amount_usd=data.get("amount_usd"),
            amount_pct=data.get("amount_pct"),
            sentiment_filter=data.get("sentiment_filter"),
            category_filter=data.get("category_filter"),
            cooldown_hours=data.get("cooldown_hours", 24),
            enabled=data.get("enabled", True),
            created_at=created_at
        )
        
        last_triggered = data.get("last_triggered")
        if last_triggered and isinstance(last_triggered, str):
            trigger.last_triggered = datetime.fromisoformat(last_triggered.replace("Z", "+00:00"))
        
        return trigger


# Pre-built trigger templates
TRIGGER_TEMPLATES = {
    "elon_doge": {
        "name": "Elon Musk DOGE Tweets",
        "keywords": ["elon", "musk", "doge", "dogecoin"],
        "coins": ["DOGE"],
        "action": "buy",
        "sentiment_filter": "positive",
        "cooldown_hours": 12,
        "description": "Buy DOGE when Elon Musk tweets positively about it"
    },
    "elon_btc": {
        "name": "Elon Musk Bitcoin News",
        "keywords": ["elon", "musk", "bitcoin", "btc", "tesla"],
        "coins": ["BTC"],
        "action": "alert",
        "sentiment_filter": "any",
        "cooldown_hours": 6,
        "description": "Alert when Elon Musk mentions Bitcoin"
    },
    "sec_regulatory": {
        "name": "SEC Regulatory Actions",
        "keywords": ["sec", "gensler", "lawsuit", "charges", "enforcement"],
        "coins": ["BTC", "ETH", "BNB", "SOL"],
        "action": "sell",
        "sentiment_filter": "negative",
        "cooldown_hours": 24,
        "description": "Sell when SEC takes negative action"
    },
    "etf_approval": {
        "name": "ETF Approval News",
        "keywords": ["etf", "approved", "approval", "blackrock", "fidelity"],
        "coins": ["BTC", "ETH"],
        "action": "buy",
        "sentiment_filter": "positive",
        "cooldown_hours": 24,
        "description": "Buy on ETF approval news"
    },
    "exchange_hack": {
        "name": "Exchange Hack Alert",
        "keywords": ["hack", "hacked", "exploit", "breach", "stolen", "drained"],
        "coins": ["BTC", "ETH"],
        "action": "alert",
        "sentiment_filter": "negative",
        "cooldown_hours": 6,
        "description": "Alert on exchange security breaches"
    },
    "china_ban": {
        "name": "China Crypto Ban News",
        "keywords": ["china", "ban", "crackdown", "illegal", "prohibition"],
        "coins": ["BTC"],
        "action": "sell",
        "sentiment_filter": "negative",
        "cooldown_hours": 48,
        "description": "Sell on China crypto ban news"
    },
    "institutional_buy": {
        "name": "Institutional Bitcoin Purchase",
        "keywords": ["microstrategy", "saylor", "institutional", "purchase", "bought", "buys", "acquires"],
        "coins": ["BTC"],
        "action": "buy",
        "sentiment_filter": "positive",
        "cooldown_hours": 24,
        "description": "Buy when institutions announce BTC purchases"
    },
    "whale_alert": {
        "name": "Whale Movement Alert",
        "keywords": ["whale", "large transfer", "moved", "million", "billion"],
        "coins": ["BTC", "ETH"],
        "action": "alert",
        "sentiment_filter": "any",
        "cooldown_hours": 4,
        "description": "Alert on large crypto movements"
    }
}


class EventTriggerService:
    """
    Service for managing and executing custom event triggers.
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        coindesk_service=None,
        correlation_engine=None,
        kraken_service=None,
        alert_service=None
    ):
        self.db = db
        self.coindesk_service = coindesk_service
        self.correlation_engine = correlation_engine
        self.kraken_service = kraken_service
        self.alert_service = alert_service
        self.triggers_collection = "event_triggers"
        self.trigger_history_collection = "trigger_executions"
        self._triggers_cache: Dict[str, EventTrigger] = {}
        self._monitoring = False
        self._last_check = None
    
    async def create_trigger(self, trigger: EventTrigger) -> Dict[str, Any]:
        """Create a new event trigger"""
        trigger_dict = trigger.to_dict()
        
        # Check if trigger with same ID exists
        existing = await self.db[self.triggers_collection].find_one({"trigger_id": trigger.trigger_id})
        if existing:
            return {"error": f"Trigger with ID {trigger.trigger_id} already exists"}
        
        await self.db[self.triggers_collection].insert_one(trigger_dict)
        self._triggers_cache[trigger.trigger_id] = trigger
        
        # Remove MongoDB _id before returning
        trigger_dict.pop("_id", None)
        
        return {
            "status": "created",
            "trigger": trigger_dict
        }
    
    async def create_from_template(
        self,
        template_name: str,
        trigger_id: str,
        amount_usd: float = None,
        amount_pct: float = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """Create a trigger from a pre-built template"""
        if template_name not in TRIGGER_TEMPLATES:
            return {
                "error": f"Template '{template_name}' not found",
                "available_templates": list(TRIGGER_TEMPLATES.keys())
            }
        
        template = TRIGGER_TEMPLATES[template_name]
        
        trigger = EventTrigger(
            trigger_id=trigger_id,
            name=template["name"],
            keywords=template["keywords"],
            coins=template["coins"],
            action=template["action"],
            amount_usd=amount_usd,
            amount_pct=amount_pct,
            sentiment_filter=template.get("sentiment_filter"),
            cooldown_hours=template.get("cooldown_hours", 24),
            enabled=enabled
        )
        
        return await self.create_trigger(trigger)
    
    async def get_trigger(self, trigger_id: str) -> Optional[EventTrigger]:
        """Get a trigger by ID"""
        if trigger_id in self._triggers_cache:
            return self._triggers_cache[trigger_id]
        
        data = await self.db[self.triggers_collection].find_one({"trigger_id": trigger_id})
        if data:
            trigger = EventTrigger.from_dict(data)
            self._triggers_cache[trigger_id] = trigger
            return trigger
        return None
    
    async def list_triggers(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """List all triggers"""
        query = {"enabled": True} if enabled_only else {}
        triggers = await self.db[self.triggers_collection].find(
            query, {"_id": 0}
        ).to_list(length=100)
        return triggers
    
    async def update_trigger(self, trigger_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a trigger"""
        result = await self.db[self.triggers_collection].update_one(
            {"trigger_id": trigger_id},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            # Clear cache
            if trigger_id in self._triggers_cache:
                del self._triggers_cache[trigger_id]
            return {"status": "updated", "trigger_id": trigger_id}
        
        return {"error": "Trigger not found"}
    
    async def delete_trigger(self, trigger_id: str) -> Dict[str, Any]:
        """Delete a trigger"""
        result = await self.db[self.triggers_collection].delete_one({"trigger_id": trigger_id})
        
        if result.deleted_count > 0:
            if trigger_id in self._triggers_cache:
                del self._triggers_cache[trigger_id]
            return {"status": "deleted", "trigger_id": trigger_id}
        
        return {"error": "Trigger not found"}
    
    async def toggle_trigger(self, trigger_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable a trigger"""
        return await self.update_trigger(trigger_id, {"enabled": enabled})
    
    def check_event_matches_trigger(
        self,
        trigger: EventTrigger,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if an event matches a trigger's criteria"""
        title = event.get("title", "").lower()
        body = event.get("body", "").lower()
        text = title + " " + body
        
        # Check keywords
        keyword_matches = [kw for kw in trigger.keywords if kw in text]
        if not keyword_matches:
            return {"matches": False, "reason": "No keyword match"}
        
        # Check sentiment filter
        sentiment = event.get("sentiment", "NEUTRAL")
        if trigger.sentiment_filter:
            if trigger.sentiment_filter == "positive" and sentiment != "POSITIVE":
                return {"matches": False, "reason": "Sentiment not positive"}
            if trigger.sentiment_filter == "negative" and sentiment != "NEGATIVE":
                return {"matches": False, "reason": "Sentiment not negative"}
        
        # Check category filter
        if trigger.category_filter:
            categories = event.get("categories", [])
            if trigger.category_filter.upper() not in [c.upper() for c in categories]:
                return {"matches": False, "reason": "Category not matched"}
        
        # Check cooldown
        if trigger.last_triggered:
            cooldown_end = trigger.last_triggered + timedelta(hours=trigger.cooldown_hours)
            if datetime.now(timezone.utc) < cooldown_end:
                return {"matches": False, "reason": "Cooldown active"}
        
        return {
            "matches": True,
            "keyword_matches": keyword_matches,
            "sentiment": sentiment,
            "confidence": len(keyword_matches) * 25  # Basic confidence score
        }
    
    async def execute_trigger(
        self,
        trigger: EventTrigger,
        event: Dict[str, Any],
        match_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a triggered action"""
        execution = {
            "trigger_id": trigger.trigger_id,
            "trigger_name": trigger.name,
            "event_title": event.get("title"),
            "event_sentiment": event.get("sentiment"),
            "action": trigger.action,
            "coins": trigger.coins,
            "match_confidence": match_result.get("confidence"),
            "keyword_matches": match_result.get("keyword_matches"),
            "executed_at": datetime.now(timezone.utc),
            "success": False,
            "result": None
        }
        
        try:
            if trigger.action == "alert":
                # Send alert only
                if self.alert_service:
                    await self.alert_service.send_alert(
                        title=f"🚨 Event Trigger: {trigger.name}",
                        message=f"Event: {event.get('title')}\nCoins: {', '.join(trigger.coins)}\nSentiment: {event.get('sentiment')}",
                        alert_type="event_trigger",
                        priority="high"
                    )
                execution["result"] = {"type": "alert_sent"}
                execution["success"] = True
                
            elif trigger.action in ["buy", "sell"]:
                # Execute trade (if Kraken service available)
                if self.kraken_service:
                    for coin in trigger.coins:
                        trade_result = {
                            "coin": coin,
                            "action": trigger.action,
                            "amount_usd": trigger.amount_usd,
                            "amount_pct": trigger.amount_pct,
                            "status": "pending_confirmation"
                        }
                        
                        # For safety, we log the intent but require manual confirmation
                        # Real trades should go through the AI chat confirmation flow
                        execution["result"] = trade_result
                        execution["success"] = True
                        
                        # Send alert about trade intent
                        if self.alert_service:
                            await self.alert_service.send_alert(
                                title=f"💰 Trade Trigger: {trigger.action.upper()} {coin}",
                                message=f"Event: {event.get('title')}\nAction: {trigger.action.upper()} {coin}\nAmount: ${trigger.amount_usd or 'Portfolio %'}\nConfirm in AI Chat to execute.",
                                alert_type="trade_trigger",
                                priority="critical"
                            )
                else:
                    execution["result"] = {"error": "Trading service not available"}
            
            # Update last triggered time
            trigger.last_triggered = datetime.now(timezone.utc)
            await self.update_trigger(trigger.trigger_id, {
                "last_triggered": trigger.last_triggered.isoformat()
            })
            
        except Exception as e:
            execution["success"] = False
            execution["result"] = {"error": str(e)}
        
        # Store execution history
        await self.db[self.trigger_history_collection].insert_one(execution)
        
        return execution
    
    async def check_recent_events(self) -> List[Dict[str, Any]]:
        """Check recent news events against all enabled triggers"""
        if not self.coindesk_service:
            return []
        
        # Get enabled triggers
        triggers_data = await self.list_triggers(enabled_only=True)
        triggers = [EventTrigger.from_dict(t) for t in triggers_data]
        
        if not triggers:
            return []
        
        # Get recent news
        try:
            result = await self.coindesk_service._request(
                "/news/v1/article/list",
                {"limit": 30, "lang": "EN"}
            )
            events = result.get("Data", [])
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
        
        executions = []
        
        for event in events:
            event_data = {
                "title": event.get("TITLE", ""),
                "body": event.get("BODY", "")[:500],
                "sentiment": event.get("SENTIMENT", "NEUTRAL"),
                "categories": [c.get("NAME") for c in event.get("CATEGORY_DATA", [])],
                "published_at": event.get("PUBLISHED_ON"),
                "url": event.get("URL")
            }
            
            for trigger in triggers:
                match_result = self.check_event_matches_trigger(trigger, event_data)
                
                if match_result["matches"]:
                    execution = await self.execute_trigger(trigger, event_data, match_result)
                    executions.append(execution)
        
        self._last_check = datetime.now(timezone.utc)
        
        return executions
    
    async def get_execution_history(self, trigger_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trigger execution history"""
        query = {"trigger_id": trigger_id} if trigger_id else {}
        
        history = await self.db[self.trigger_history_collection].find(
            query, {"_id": 0}
        ).sort("executed_at", -1).limit(limit).to_list(limit)
        
        return history
    
    async def get_templates(self) -> Dict[str, Any]:
        """Get available trigger templates"""
        return TRIGGER_TEMPLATES
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get trigger service statistics"""
        total_triggers = await self.db[self.triggers_collection].count_documents({})
        enabled_triggers = await self.db[self.triggers_collection].count_documents({"enabled": True})
        total_executions = await self.db[self.trigger_history_collection].count_documents({})
        successful_executions = await self.db[self.trigger_history_collection].count_documents({"success": True})
        
        # Recent executions
        recent = await self.db[self.trigger_history_collection].find(
            {}, {"_id": 0}
        ).sort("executed_at", -1).limit(5).to_list(5)
        
        return {
            "total_triggers": total_triggers,
            "enabled_triggers": enabled_triggers,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": round(successful_executions / total_executions * 100, 1) if total_executions > 0 else 0,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "recent_executions": recent,
            "available_templates": list(TRIGGER_TEMPLATES.keys())
        }


# Global instance
_trigger_service = None

def get_event_trigger_service(
    db: AsyncIOMotorDatabase = None,
    coindesk_service=None,
    correlation_engine=None,
    kraken_service=None,
    alert_service=None
):
    """Get or create event trigger service instance"""
    global _trigger_service
    if _trigger_service is None and db is not None:
        _trigger_service = EventTriggerService(
            db, coindesk_service, correlation_engine, kraken_service, alert_service
        )
    return _trigger_service
