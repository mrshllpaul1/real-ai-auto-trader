"""
Historical Events Database
Downloads and stores major crypto events for AI training.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


# Major historical events to download
MAJOR_EVENTS = [
    # 2013-2014
    {"date": "2013-12-05", "event": "China bans banks from Bitcoin", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2014-02-24", "event": "Mt. Gox exchange collapse", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    
    # 2017 Bull Run
    {"date": "2017-08-01", "event": "Bitcoin Cash hard fork", "coins": ["BTC", "BCH"], "impact": "mixed", "category": "technology"},
    {"date": "2017-12-11", "event": "CBOE launches Bitcoin futures", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2017-12-17", "event": "Bitcoin reaches $20k ATH", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    
    # 2018 Bear Market
    {"date": "2018-01-26", "event": "Coincheck hack - $530M stolen", "coins": ["XEM"], "impact": "negative", "category": "hack"},
    {"date": "2018-11-15", "event": "Bitcoin Cash hash war", "coins": ["BCH", "BSV"], "impact": "negative", "category": "technology"},
    
    # 2020-2021 Bull Run
    {"date": "2020-05-11", "event": "Bitcoin halving", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2020-08-11", "event": "MicroStrategy announces BTC purchase", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2020-12-16", "event": "Bitcoin breaks $20k again", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    
    # 2021 - Elon Era
    {"date": "2021-01-29", "event": "Elon Musk adds #Bitcoin to bio", "coins": ["BTC"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-02-08", "event": "Tesla buys $1.5B Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2021-02-04", "event": "Elon tweets about Dogecoin", "coins": ["DOGE"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-04-14", "event": "Coinbase IPO on NASDAQ", "coins": ["BTC", "ETH"], "impact": "positive", "category": "institutional"},
    {"date": "2021-05-08", "event": "Elon hosts SNL - DOGE crashes", "coins": ["DOGE"], "impact": "negative", "category": "celebrity"},
    {"date": "2021-05-12", "event": "Tesla suspends BTC payments", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2021-05-19", "event": "China crypto crackdown", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2021-09-07", "event": "El Salvador adopts Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2021-11-10", "event": "Bitcoin ATH $69k", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    
    # 2022 - Crash Year
    {"date": "2022-01-21", "event": "Russia proposes crypto ban", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2022-05-09", "event": "Terra/Luna collapse begins", "coins": ["LUNA", "UST"], "impact": "negative", "category": "hack"},
    {"date": "2022-06-13", "event": "Celsius freezes withdrawals", "coins": ["BTC", "ETH"], "impact": "negative", "category": "exchange"},
    {"date": "2022-07-01", "event": "Three Arrows Capital bankruptcy", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2022-09-15", "event": "Ethereum Merge completed", "coins": ["ETH"], "impact": "positive", "category": "technology"},
    {"date": "2022-11-02", "event": "CoinDesk reveals FTX/Alameda issues", "coins": ["FTT", "SOL"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-08", "event": "Binance backs out of FTX deal", "coins": ["BTC", "FTT"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-11", "event": "FTX files for bankruptcy", "coins": ["BTC", "SOL", "FTT"], "impact": "negative", "category": "exchange"},
    
    # 2023 Recovery
    {"date": "2023-01-14", "event": "Bitcoin breaks $20k after FTX", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2023-03-10", "event": "Silicon Valley Bank collapse", "coins": ["BTC", "USDC"], "impact": "mixed", "category": "macro"},
    {"date": "2023-06-05", "event": "SEC sues Binance", "coins": ["BNB", "BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-06-06", "event": "SEC sues Coinbase", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-06-15", "event": "BlackRock files Bitcoin ETF", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2023-08-29", "event": "Grayscale wins SEC lawsuit", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    
    # 2024 ETF Era
    {"date": "2024-01-10", "event": "SEC approves Bitcoin ETFs", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-01-11", "event": "Bitcoin ETFs begin trading", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2024-03-14", "event": "Bitcoin reaches new ATH $73k", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-04-20", "event": "Bitcoin halving 2024", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2024-05-23", "event": "SEC approves Ethereum ETFs", "coins": ["ETH"], "impact": "positive", "category": "regulatory"},
]


class HistoricalEventsDatabase:
    """
    Downloads and stores historical crypto events.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, coindesk_service=None, correlation_engine=None):
        self.db = db
        self.coindesk_service = coindesk_service
        self.correlation_engine = correlation_engine
        self.events_collection = "historical_events"
        
    async def seed_major_events(self) -> Dict[str, Any]:
        """
        Seed the database with known major events.
        """
        inserted = 0
        updated = 0
        
        for event in MAJOR_EVENTS:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            doc = {
                "date": event["date"],
                "timestamp": int(event_date.timestamp()),
                "event": event["event"],
                "coins": event["coins"],
                "impact": event["impact"],
                "category": event["category"],
                "source": "curated",
                "is_major": True,
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await self.db[self.events_collection].update_one(
                {"date": event["date"], "event": event["event"]},
                {"$set": doc},
                upsert=True
            )
            
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1
        
        # Create indexes
        await self.db[self.events_collection].create_index([("date", 1)])
        await self.db[self.events_collection].create_index([("coins", 1)])
        await self.db[self.events_collection].create_index([("category", 1)])
        await self.db[self.events_collection].create_index([("timestamp", 1)])
        
        return {
            "status": "success",
            "total_events": len(MAJOR_EVENTS),
            "inserted": inserted,
            "updated": updated
        }
    
    async def enrich_events_with_news(self, limit: int = 20) -> Dict[str, Any]:
        """
        Enrich stored events with actual news articles from CoinDesk.
        """
        if not self.coindesk_service:
            return {"error": "CoinDesk service not available"}
        
        # Get events without news enrichment
        events = await self.db[self.events_collection].find(
            {"news_enriched": {"$ne": True}},
            {"_id": 0}
        ).limit(limit).to_list(limit)
        
        enriched = 0
        
        for event in events:
            try:
                # Get news around the event date
                event_ts = event.get("timestamp", 0)
                if not event_ts:
                    continue
                
                to_ts = event_ts + 86400  # Next day
                
                result = await self.coindesk_service._request(
                    "/news/v1/article/list",
                    {"limit": 30, "to_ts": to_ts, "lang": "EN"}
                )
                
                related_news = []
                for article in result.get("Data", []):
                    pub_ts = article.get("PUBLISHED_ON", 0)
                    # Within 2 days of event
                    if event_ts - 86400 <= pub_ts <= event_ts + 86400:
                        title = article.get("TITLE", "").lower()
                        # Check relevance
                        event_words = event.get("event", "").lower().split()
                        if any(word in title for word in event_words if len(word) > 4):
                            related_news.append({
                                "title": article.get("TITLE"),
                                "url": article.get("URL"),
                                "sentiment": article.get("SENTIMENT"),
                                "published_at": datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat()
                            })
                
                # Update event with news
                await self.db[self.events_collection].update_one(
                    {"date": event["date"], "event": event["event"]},
                    {
                        "$set": {
                            "news_enriched": True,
                            "related_news": related_news[:5],
                            "news_count": len(related_news),
                            "enriched_at": datetime.now(timezone.utc)
                        }
                    }
                )
                enriched += 1
                
                await asyncio.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"Error enriching event {event.get('event')}: {e}")
                continue
        
        return {
            "status": "success",
            "events_processed": len(events),
            "events_enriched": enriched
        }
    
    async def add_price_impact(self) -> Dict[str, Any]:
        """
        Add price impact data to events by correlating with OHLCV data.
        """
        events = await self.db[self.events_collection].find(
            {"price_impact_calculated": {"$ne": True}},
            {"_id": 0}
        ).to_list(length=100)
        
        updated = 0
        
        for event in events:
            try:
                event_ts = event.get("timestamp", 0)
                coins = event.get("coins", [])
                
                if not event_ts or not coins:
                    continue
                
                price_impacts = {}
                
                for coin in coins:
                    # Get price data around event
                    data = await self.db.historical_ohlcv.find({
                        "symbol": coin.upper(),
                        "timestamp": {
                            "$gte": event_ts - 86400 * 3,  # 3 days before
                            "$lte": event_ts + 86400 * 7   # 7 days after
                        }
                    }, {"_id": 0}).sort("timestamp", 1).to_list(length=20)
                    
                    if len(data) >= 3:
                        # Find price before and after
                        before_prices = [d["close"] for d in data if d["timestamp"] < event_ts]
                        after_prices = [d["close"] for d in data if d["timestamp"] >= event_ts]
                        
                        if before_prices and after_prices:
                            price_before = before_prices[-1]
                            price_at_event = after_prices[0]
                            price_1d = after_prices[1] if len(after_prices) > 1 else price_at_event
                            price_7d = after_prices[-1]
                            
                            if price_before > 0:
                                price_impacts[coin] = {
                                    "price_before": round(price_before, 2),
                                    "price_at_event": round(price_at_event, 2),
                                    "price_1d_after": round(price_1d, 2),
                                    "price_7d_after": round(price_7d, 2),
                                    "change_immediate_pct": round(((price_at_event - price_before) / price_before) * 100, 2),
                                    "change_1d_pct": round(((price_1d - price_before) / price_before) * 100, 2),
                                    "change_7d_pct": round(((price_7d - price_before) / price_before) * 100, 2)
                                }
                
                if price_impacts:
                    await self.db[self.events_collection].update_one(
                        {"date": event["date"], "event": event["event"]},
                        {
                            "$set": {
                                "price_impact": price_impacts,
                                "price_impact_calculated": True
                            }
                        }
                    )
                    updated += 1
                    
            except Exception as e:
                print(f"Error calculating price impact for {event.get('event')}: {e}")
                continue
        
        return {
            "status": "success",
            "events_processed": len(events),
            "events_updated": updated
        }
    
    async def get_events(
        self,
        coin: str = None,
        category: str = None,
        impact: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Query events with filters.
        """
        query = {}
        
        if coin:
            query["coins"] = coin.upper()
        if category:
            query["category"] = category.lower()
        if impact:
            query["impact"] = impact.lower()
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        
        events = await self.db[self.events_collection].find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return events
    
    async def get_events_for_coin(self, coin: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all events affecting a specific coin"""
        return await self.get_events(coin=coin, limit=limit)
    
    async def get_events_by_category(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get events by category (celebrity, regulatory, hack, etc.)"""
        return await self.get_events(category=category, limit=limit)
    
    async def search_events(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search events by keyword"""
        events = await self.db[self.events_collection].find(
            {"event": {"$regex": keyword, "$options": "i"}},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return events
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored events"""
        total = await self.db[self.events_collection].count_documents({})
        
        # Count by category
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_category = await self.db[self.events_collection].aggregate(pipeline).to_list(length=20)
        
        # Count by impact
        pipeline = [
            {"$group": {"_id": "$impact", "count": {"$sum": 1}}}
        ]
        by_impact = await self.db[self.events_collection].aggregate(pipeline).to_list(length=5)
        
        # Date range
        oldest = await self.db[self.events_collection].find_one(
            {}, {"date": 1}, sort=[("timestamp", 1)]
        )
        newest = await self.db[self.events_collection].find_one(
            {}, {"date": 1}, sort=[("timestamp", -1)]
        )
        
        return {
            "total_events": total,
            "by_category": {c["_id"]: c["count"] for c in by_category if c["_id"]},
            "by_impact": {i["_id"]: i["count"] for i in by_impact if i["_id"]},
            "date_range": {
                "oldest": oldest.get("date") if oldest else None,
                "newest": newest.get("date") if newest else None
            },
            "events_with_news": await self.db[self.events_collection].count_documents({"news_enriched": True}),
            "events_with_price_impact": await self.db[self.events_collection].count_documents({"price_impact_calculated": True})
        }


# Global instance
_events_db = None

def get_historical_events_db(db: AsyncIOMotorDatabase = None, coindesk_service=None, correlation_engine=None):
    """Get or create historical events database instance"""
    global _events_db
    if _events_db is None and db is not None:
        _events_db = HistoricalEventsDatabase(db, coindesk_service, correlation_engine)
    return _events_db
