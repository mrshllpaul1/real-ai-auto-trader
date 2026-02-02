"""
Trading Journal Service
Records all trades with AI insights and performance analysis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class TradingJournalService:
    """
    Trading Journal - Records and analyzes all trades with AI insights.
    Helps users understand their trading patterns and AI decisions.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.trading_journal
    
    async def record_trade(
        self,
        trade_type: str,  # 'OPEN' or 'CLOSE'
        coin_id: str,
        symbol: str,
        action: str,  # 'BUY' or 'SELL'
        amount_usd: float,
        price: float,
        quantity: float,
        is_paper: bool = True,
        ai_reasoning: str = None,
        ai_confidence: float = None,
        ai_factors: List[Dict] = None,
        is_gem: bool = False,
        pnl_usd: float = None,
        pnl_pct: float = None,
        exit_reason: str = None,
        tags: List[str] = None,
        notes: str = None,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """Record a trade entry in the journal"""
        
        entry = {
            "user_id": user_id,
            "trade_type": trade_type,
            "coin_id": coin_id,
            "symbol": symbol,
            "action": action,
            "amount_usd": round(amount_usd, 2),
            "price": price,
            "quantity": quantity,
            "is_paper": is_paper,
            "is_gem": is_gem,
            "timestamp": datetime.utcnow().isoformat(),
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "ai_insights": {
                "reasoning": ai_reasoning,
                "confidence": ai_confidence,
                "factors": ai_factors or []
            },
            "performance": {
                "pnl_usd": pnl_usd,
                "pnl_pct": pnl_pct,
                "exit_reason": exit_reason
            } if trade_type == "CLOSE" else None,
            "tags": tags or [],
            "notes": notes
        }
        
        await self.collection.insert_one(entry)
        logger.info(f"📝 Journal: {trade_type} {action} {coin_id} ${amount_usd:.2f}")
        
        return {**entry, "_id": None}
    
    async def add_note_to_trade(
        self,
        trade_id: str,
        note: str,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """Add a personal note to a trade entry"""
        from bson import ObjectId
        
        result = await self.collection.update_one(
            {"_id": ObjectId(trade_id), "user_id": user_id},
            {
                "$set": {"notes": note, "updated_at": datetime.utcnow().isoformat()},
                "$push": {"note_history": {"note": note, "timestamp": datetime.utcnow().isoformat()}}
            }
        )
        
        return {"success": result.modified_count > 0}
    
    async def add_tags_to_trade(
        self,
        trade_id: str,
        tags: List[str],
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """Add tags to a trade for categorization"""
        from bson import ObjectId
        
        result = await self.collection.update_one(
            {"_id": ObjectId(trade_id), "user_id": user_id},
            {"$addToSet": {"tags": {"$each": tags}}}
        )
        
        return {"success": result.modified_count > 0}
    
    async def get_journal_entries(
        self,
        user_id: str = "default",
        limit: int = 50,
        offset: int = 0,
        coin_id: str = None,
        trade_type: str = None,
        date_from: str = None,
        date_to: str = None,
        is_paper: bool = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Get journal entries with filters"""
        
        query = {"user_id": user_id}
        
        if coin_id:
            query["coin_id"] = coin_id
        if trade_type:
            query["trade_type"] = trade_type
        if is_paper is not None:
            query["is_paper"] = is_paper
        if date_from:
            query["date"] = {"$gte": date_from}
        if date_to:
            if "date" in query:
                query["date"]["$lte"] = date_to
            else:
                query["date"] = {"$lte": date_to}
        if tags:
            query["tags"] = {"$in": tags}
        
        entries = await self.collection.find(
            query, {"_id": 0}
        ).sort("timestamp", -1).skip(offset).limit(limit).to_list(limit)
        
        total = await self.collection.count_documents(query)
        
        return {
            "entries": entries,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def get_daily_summary(
        self,
        date: str = None,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """Get summary for a specific day"""
        
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        entries = await self.collection.find(
            {"user_id": user_id, "date": date},
            {"_id": 0}
        ).to_list(1000)
        
        opens = [e for e in entries if e.get("trade_type") == "OPEN"]
        closes = [e for e in entries if e.get("trade_type") == "CLOSE"]
        
        total_pnl = sum(
            e.get("performance", {}).get("pnl_usd", 0) or 0 
            for e in closes
        )
        
        winners = [e for e in closes if (e.get("performance", {}).get("pnl_usd", 0) or 0) > 0]
        
        return {
            "date": date,
            "total_trades": len(entries),
            "opens": len(opens),
            "closes": len(closes),
            "total_pnl": round(total_pnl, 2),
            "winners": len(winners),
            "losers": len(closes) - len(winners),
            "win_rate": round(len(winners) / len(closes) * 100, 1) if closes else 0,
            "coins_traded": list(set(e.get("coin_id") for e in entries)),
            "total_volume": round(sum(e.get("amount_usd", 0) for e in entries), 2)
        }
    
    async def get_performance_stats(
        self,
        user_id: str = "default",
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance statistics over a period"""
        
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        closes = await self.collection.find(
            {
                "user_id": user_id,
                "trade_type": "CLOSE",
                "date": {"$gte": start_date}
            },
            {"_id": 0}
        ).to_list(10000)
        
        if not closes:
            return {
                "period_days": days,
                "total_trades": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "best_trade": None,
                "worst_trade": None,
                "most_traded_coin": None,
                "daily_pnl": []
            }
        
        pnls = [(e.get("performance", {}).get("pnl_usd", 0) or 0) for e in closes]
        winners = [p for p in pnls if p > 0]
        losers = [p for p in pnls if p < 0]
        
        # Group by date for daily P/L
        daily_pnl = {}
        for e in closes:
            date = e.get("date")
            pnl = e.get("performance", {}).get("pnl_usd", 0) or 0
            daily_pnl[date] = daily_pnl.get(date, 0) + pnl
        
        # Most traded coin
        coin_counts = {}
        for e in closes:
            coin = e.get("coin_id")
            coin_counts[coin] = coin_counts.get(coin, 0) + 1
        most_traded = max(coin_counts, key=coin_counts.get) if coin_counts else None
        
        # Best and worst trades
        best = max(closes, key=lambda x: x.get("performance", {}).get("pnl_usd", 0) or 0)
        worst = min(closes, key=lambda x: x.get("performance", {}).get("pnl_usd", 0) or 0)
        
        return {
            "period_days": days,
            "total_trades": len(closes),
            "total_pnl": round(sum(pnls), 2),
            "win_rate": round(len(winners) / len(closes) * 100, 1),
            "avg_win": round(sum(winners) / len(winners), 2) if winners else 0,
            "avg_loss": round(sum(losers) / len(losers), 2) if losers else 0,
            "best_trade": {
                "coin_id": best.get("coin_id"),
                "pnl_usd": best.get("performance", {}).get("pnl_usd"),
                "pnl_pct": best.get("performance", {}).get("pnl_pct"),
                "date": best.get("date")
            },
            "worst_trade": {
                "coin_id": worst.get("coin_id"),
                "pnl_usd": worst.get("performance", {}).get("pnl_usd"),
                "pnl_pct": worst.get("performance", {}).get("pnl_pct"),
                "date": worst.get("date")
            },
            "most_traded_coin": most_traded,
            "daily_pnl": [
                {"date": k, "pnl": round(v, 2)} 
                for k, v in sorted(daily_pnl.items())
            ]
        }
    
    async def get_ai_insights_summary(
        self,
        user_id: str = "default",
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze AI decision patterns and their success rates"""
        
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        closes = await self.collection.find(
            {
                "user_id": user_id,
                "trade_type": "CLOSE",
                "date": {"$gte": start_date}
            },
            {"_id": 0}
        ).to_list(10000)
        
        if not closes:
            return {
                "period_days": days,
                "total_analyzed": 0,
                "factor_performance": {},
                "confidence_accuracy": {},
                "gem_performance": {},
                "insights": []
            }
        
        # Analyze factor performance
        factor_stats = {}
        confidence_buckets = {"high": [], "medium": [], "low": []}
        gem_trades = []
        regular_trades = []
        
        for trade in closes:
            pnl = trade.get("performance", {}).get("pnl_usd", 0) or 0
            ai = trade.get("ai_insights", {})
            confidence = ai.get("confidence", 50)
            factors = ai.get("factors", [])
            is_gem = trade.get("is_gem", False)
            
            # Track confidence accuracy
            if confidence >= 70:
                confidence_buckets["high"].append(pnl)
            elif confidence >= 50:
                confidence_buckets["medium"].append(pnl)
            else:
                confidence_buckets["low"].append(pnl)
            
            # Track factor performance
            for factor in factors:
                f_type = factor.get("type", "unknown")
                if f_type not in factor_stats:
                    factor_stats[f_type] = {"wins": 0, "losses": 0, "total_pnl": 0}
                
                if pnl > 0:
                    factor_stats[f_type]["wins"] += 1
                else:
                    factor_stats[f_type]["losses"] += 1
                factor_stats[f_type]["total_pnl"] += pnl
            
            # Track gem performance
            if is_gem:
                gem_trades.append(pnl)
            else:
                regular_trades.append(pnl)
        
        # Generate insights
        insights = []
        
        # Confidence insight
        high_win_rate = len([p for p in confidence_buckets["high"] if p > 0]) / len(confidence_buckets["high"]) * 100 if confidence_buckets["high"] else 0
        if high_win_rate > 60:
            insights.append({
                "type": "positive",
                "title": "High Confidence = High Success",
                "message": f"Trades with 70%+ AI confidence have a {high_win_rate:.0f}% win rate. Trust the AI when it's confident!"
            })
        
        # Gem insight
        if gem_trades:
            gem_win_rate = len([p for p in gem_trades if p > 0]) / len(gem_trades) * 100
            gem_avg = sum(gem_trades) / len(gem_trades)
            if gem_avg > 0:
                insights.append({
                    "type": "positive",
                    "title": "Gems Are Performing",
                    "message": f"Hidden gem trades average ${gem_avg:.2f} profit with {gem_win_rate:.0f}% win rate."
                })
        
        # Factor insight
        best_factor = max(factor_stats.items(), key=lambda x: x[1]["total_pnl"]) if factor_stats else None
        if best_factor and best_factor[1]["total_pnl"] > 0:
            insights.append({
                "type": "info",
                "title": f"Best Factor: {best_factor[0].title()}",
                "message": f"Trades driven by {best_factor[0]} signals generated ${best_factor[1]['total_pnl']:.2f} total profit."
            })
        
        return {
            "period_days": days,
            "total_analyzed": len(closes),
            "factor_performance": {
                k: {
                    "win_rate": round(v["wins"] / (v["wins"] + v["losses"]) * 100, 1) if (v["wins"] + v["losses"]) > 0 else 0,
                    "total_pnl": round(v["total_pnl"], 2),
                    "trades": v["wins"] + v["losses"]
                }
                for k, v in factor_stats.items()
            },
            "confidence_accuracy": {
                "high": {
                    "trades": len(confidence_buckets["high"]),
                    "win_rate": round(len([p for p in confidence_buckets["high"] if p > 0]) / len(confidence_buckets["high"]) * 100, 1) if confidence_buckets["high"] else 0,
                    "avg_pnl": round(sum(confidence_buckets["high"]) / len(confidence_buckets["high"]), 2) if confidence_buckets["high"] else 0
                },
                "medium": {
                    "trades": len(confidence_buckets["medium"]),
                    "win_rate": round(len([p for p in confidence_buckets["medium"] if p > 0]) / len(confidence_buckets["medium"]) * 100, 1) if confidence_buckets["medium"] else 0,
                    "avg_pnl": round(sum(confidence_buckets["medium"]) / len(confidence_buckets["medium"]), 2) if confidence_buckets["medium"] else 0
                },
                "low": {
                    "trades": len(confidence_buckets["low"]),
                    "win_rate": round(len([p for p in confidence_buckets["low"] if p > 0]) / len(confidence_buckets["low"]) * 100, 1) if confidence_buckets["low"] else 0,
                    "avg_pnl": round(sum(confidence_buckets["low"]) / len(confidence_buckets["low"]), 2) if confidence_buckets["low"] else 0
                }
            },
            "gem_performance": {
                "total_gems": len(gem_trades),
                "gem_win_rate": round(len([p for p in gem_trades if p > 0]) / len(gem_trades) * 100, 1) if gem_trades else 0,
                "gem_avg_pnl": round(sum(gem_trades) / len(gem_trades), 2) if gem_trades else 0,
                "regular_win_rate": round(len([p for p in regular_trades if p > 0]) / len(regular_trades) * 100, 1) if regular_trades else 0,
                "regular_avg_pnl": round(sum(regular_trades) / len(regular_trades), 2) if regular_trades else 0
            },
            "insights": insights
        }
