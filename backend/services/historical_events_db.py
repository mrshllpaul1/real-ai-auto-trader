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
    # 2013-2014 Early Days
    {"date": "2013-04-10", "event": "Bitcoin crashes 83% from $266 to $45", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2013-10-02", "event": "Silk Road seized by FBI", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2013-11-29", "event": "Bitcoin hits $1,000 for first time", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2013-12-05", "event": "China bans banks from Bitcoin", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2014-02-24", "event": "Mt. Gox exchange collapse - 850k BTC lost", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2014-07-18", "event": "Dell accepts Bitcoin payments", "coins": ["BTC"], "impact": "positive", "category": "partnership"},
    
    # 2015-2016 Recovery
    {"date": "2015-01-04", "event": "Bitstamp hack - 19,000 BTC stolen", "coins": ["BTC"], "impact": "negative", "category": "hack"},
    {"date": "2015-06-03", "event": "New York introduces BitLicense", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2016-01-14", "event": "Mike Hearn declares Bitcoin failed", "coins": ["BTC"], "impact": "negative", "category": "technology"},
    {"date": "2016-06-17", "event": "The DAO hack - $60M stolen from Ethereum", "coins": ["ETH"], "impact": "negative", "category": "hack"},
    {"date": "2016-07-09", "event": "Bitcoin halving 2016", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2016-07-20", "event": "Ethereum hard fork creates ETC", "coins": ["ETH", "ETC"], "impact": "mixed", "category": "technology"},
    {"date": "2016-08-02", "event": "Bitfinex hack - 120,000 BTC stolen", "coins": ["BTC"], "impact": "negative", "category": "hack"},
    
    # 2017 Bull Run
    {"date": "2017-03-10", "event": "SEC rejects Winklevoss Bitcoin ETF", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2017-04-01", "event": "Japan recognizes Bitcoin as legal payment", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2017-08-01", "event": "Bitcoin Cash hard fork", "coins": ["BTC", "BCH"], "impact": "mixed", "category": "technology"},
    {"date": "2017-09-04", "event": "China bans ICOs", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2017-10-13", "event": "Bitcoin breaks $5,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2017-11-08", "event": "SegWit2x fork cancelled", "coins": ["BTC"], "impact": "mixed", "category": "technology"},
    {"date": "2017-12-07", "event": "NiceHash hack - $64M stolen", "coins": ["BTC"], "impact": "negative", "category": "hack"},
    {"date": "2017-12-11", "event": "CBOE launches Bitcoin futures", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2017-12-17", "event": "Bitcoin reaches $20k ATH", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2017-12-22", "event": "Bitcoin crashes 45% in 5 days", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    
    # 2018 Bear Market
    {"date": "2018-01-13", "event": "Ripple XRP reaches ATH $3.84", "coins": ["XRP"], "impact": "positive", "category": "milestone"},
    {"date": "2018-01-26", "event": "Coincheck hack - $530M NEM stolen", "coins": ["XEM"], "impact": "negative", "category": "hack"},
    {"date": "2018-02-06", "event": "Bitcoin drops below $6,000", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2018-03-07", "event": "SEC says crypto exchanges must register", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2018-06-11", "event": "South Korea exchange Coinrail hacked", "coins": ["BTC"], "impact": "negative", "category": "hack"},
    {"date": "2018-09-20", "event": "Goldman Sachs shelves crypto desk plans", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2018-11-14", "event": "Bitcoin crashes below $6,000 support", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2018-11-15", "event": "Bitcoin Cash hash war begins", "coins": ["BCH", "BSV"], "impact": "negative", "category": "technology"},
    {"date": "2018-12-15", "event": "Bitcoin hits $3,200 bear market bottom", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    
    # 2019 Recovery
    {"date": "2019-02-07", "event": "QuadrigaCX founder dies with $190M", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2019-04-02", "event": "Bitcoin breaks $5,000 after 4 months", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2019-05-07", "event": "Binance hack - 7,000 BTC stolen", "coins": ["BTC", "BNB"], "impact": "negative", "category": "hack"},
    {"date": "2019-06-18", "event": "Facebook announces Libra cryptocurrency", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2019-06-26", "event": "Bitcoin reaches $13,800 yearly high", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2019-10-24", "event": "Xi Jinping endorses blockchain", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    
    # 2020-2021 Bull Run
    {"date": "2020-03-12", "event": "Black Thursday - BTC drops 50% in one day", "coins": ["BTC", "ETH"], "impact": "negative", "category": "macro"},
    {"date": "2020-05-11", "event": "Bitcoin halving 2020", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2020-07-27", "event": "US banks can custody crypto - OCC", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2020-08-11", "event": "MicroStrategy buys $250M Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2020-10-08", "event": "Square buys $50M Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2020-10-21", "event": "PayPal enables crypto buying", "coins": ["BTC", "ETH"], "impact": "positive", "category": "institutional"},
    {"date": "2020-11-30", "event": "Bitcoin breaks 2017 ATH of $20k", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2020-12-16", "event": "Bitcoin reaches $21,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    
    # 2021 - Elon Era & NFT Boom
    {"date": "2021-01-02", "event": "Bitcoin reaches $30,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-01-08", "event": "Bitcoin hits $40,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-01-29", "event": "Elon Musk adds #Bitcoin to Twitter bio", "coins": ["BTC"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-02-04", "event": "Elon tweets about Dogecoin being people's crypto", "coins": ["DOGE"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-02-08", "event": "Tesla buys $1.5B Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2021-02-19", "event": "Bitcoin market cap reaches $1 trillion", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-03-11", "event": "Beeple NFT sells for $69M", "coins": ["ETH"], "impact": "positive", "category": "milestone"},
    {"date": "2021-03-14", "event": "Bitcoin reaches $60,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-04-14", "event": "Coinbase IPO - COIN starts trading", "coins": ["BTC", "ETH"], "impact": "positive", "category": "institutional"},
    {"date": "2021-04-16", "event": "Dogecoin surges 400% in a week", "coins": ["DOGE"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-04-20", "event": "Dogecoin Day - Elon pumps DOGE", "coins": ["DOGE"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-05-08", "event": "Elon hosts SNL - DOGE crashes 30%", "coins": ["DOGE"], "impact": "negative", "category": "celebrity"},
    {"date": "2021-05-12", "event": "Tesla suspends BTC payments", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2021-05-13", "event": "Elon says looking for greener crypto", "coins": ["BTC", "DOGE"], "impact": "negative", "category": "celebrity"},
    {"date": "2021-05-19", "event": "China bans financial institutions from crypto", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2021-06-09", "event": "El Salvador makes Bitcoin legal tender", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2021-06-21", "event": "China shuts down Bitcoin miners", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2021-07-21", "event": "Elon and Jack Dorsey Bitcoin B-Word event", "coins": ["BTC"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-09-07", "event": "El Salvador officially adopts Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2021-09-24", "event": "China declares all crypto transactions illegal", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2021-10-19", "event": "First Bitcoin futures ETF (BITO) launches", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2021-11-10", "event": "Bitcoin reaches ATH $69,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-11-10", "event": "Ethereum reaches ATH $4,870", "coins": ["ETH"], "impact": "positive", "category": "milestone"},
    {"date": "2021-12-04", "event": "Bitcoin flash crashes 22% to $42k", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    
    # 2022 - Crash Year
    {"date": "2022-01-21", "event": "Russia proposes crypto ban", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2022-01-24", "event": "Bitcoin drops below $33,000", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2022-02-24", "event": "Russia invades Ukraine - crypto volatility", "coins": ["BTC"], "impact": "mixed", "category": "macro"},
    {"date": "2022-03-09", "event": "Biden signs crypto executive order", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2022-04-27", "event": "Central African Republic adopts Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2022-05-09", "event": "UST depeg begins - Terra collapse starts", "coins": ["LUNA", "UST"], "impact": "negative", "category": "hack"},
    {"date": "2022-05-12", "event": "Luna crashes 99% - $40B wiped out", "coins": ["LUNA"], "impact": "negative", "category": "hack"},
    {"date": "2022-06-13", "event": "Celsius freezes withdrawals", "coins": ["BTC", "ETH"], "impact": "negative", "category": "exchange"},
    {"date": "2022-06-18", "event": "Bitcoin drops below $18,000", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2022-07-01", "event": "Three Arrows Capital files bankruptcy", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2022-07-13", "event": "Celsius files for bankruptcy", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2022-09-15", "event": "Ethereum Merge - PoS transition", "coins": ["ETH"], "impact": "positive", "category": "technology"},
    {"date": "2022-11-02", "event": "CoinDesk exposes FTX/Alameda balance sheet", "coins": ["FTT", "SOL"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-06", "event": "CZ announces Binance selling FTT", "coins": ["FTT", "BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-08", "event": "FTX halts withdrawals", "coins": ["FTT", "SOL"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-08", "event": "Binance backs out of FTX acquisition", "coins": ["BTC", "FTT"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-11", "event": "FTX files for bankruptcy - SBF resigns", "coins": ["BTC", "SOL", "FTT"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-12", "event": "FTX hacked - $600M drained", "coins": ["FTT"], "impact": "negative", "category": "hack"},
    {"date": "2022-11-21", "event": "Bitcoin hits $15,500 - 2-year low", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2022-12-12", "event": "SBF arrested in Bahamas", "coins": ["FTT"], "impact": "mixed", "category": "regulatory"},
    
    # 2023 Recovery
    {"date": "2023-01-14", "event": "Bitcoin breaks $20k - post-FTX recovery", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2023-01-21", "event": "Genesis files for bankruptcy", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2023-02-09", "event": "SEC charges Kraken for staking", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-03-08", "event": "Silvergate Bank announces liquidation", "coins": ["BTC"], "impact": "negative", "category": "macro"},
    {"date": "2023-03-10", "event": "Silicon Valley Bank collapses", "coins": ["BTC", "USDC"], "impact": "mixed", "category": "macro"},
    {"date": "2023-03-12", "event": "Signature Bank closed by regulators", "coins": ["BTC"], "impact": "negative", "category": "macro"},
    {"date": "2023-03-13", "event": "Bitcoin pumps 20% on banking fears", "coins": ["BTC"], "impact": "positive", "category": "macro"},
    {"date": "2023-04-14", "event": "Bitcoin breaks $30,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2023-04-17", "event": "Ethereum Shanghai upgrade - staking withdrawals", "coins": ["ETH"], "impact": "positive", "category": "technology"},
    {"date": "2023-06-05", "event": "SEC sues Binance and CZ", "coins": ["BNB", "BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-06-06", "event": "SEC sues Coinbase", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-06-15", "event": "BlackRock files for spot Bitcoin ETF", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2023-07-13", "event": "Ripple wins partial victory vs SEC", "coins": ["XRP"], "impact": "positive", "category": "regulatory"},
    {"date": "2023-08-29", "event": "Grayscale wins lawsuit against SEC", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2023-10-16", "event": "Fake BlackRock ETF approval pumps BTC", "coins": ["BTC"], "impact": "mixed", "category": "institutional"},
    {"date": "2023-11-21", "event": "Binance settles with DOJ - $4.3B fine", "coins": ["BNB"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-11-21", "event": "CZ steps down as Binance CEO", "coins": ["BNB"], "impact": "negative", "category": "exchange"},
    {"date": "2023-12-04", "event": "Bitcoin breaks $40,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    
    # 2024 ETF Era
    {"date": "2024-01-02", "event": "Matrixport predicts SEC ETF rejection - BTC dumps", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2024-01-09", "event": "SEC Twitter hacked - fake ETF approval", "coins": ["BTC"], "impact": "mixed", "category": "regulatory"},
    {"date": "2024-01-10", "event": "SEC approves 11 spot Bitcoin ETFs", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-01-11", "event": "Bitcoin ETFs begin trading - $4.5B volume day 1", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2024-02-15", "event": "Bitcoin breaks $50,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-02-28", "event": "Bitcoin ETFs hit $6B daily volume", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2024-03-05", "event": "Bitcoin breaks previous ATH $69k", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-03-14", "event": "Bitcoin reaches new ATH $73,750", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-04-20", "event": "Bitcoin halving 2024", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2024-05-20", "event": "SEC approves Ethereum ETFs", "coins": ["ETH"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-07-23", "event": "Ethereum ETFs begin trading", "coins": ["ETH"], "impact": "positive", "category": "institutional"},
    
    # 2025 Expansion
    {"date": "2025-01-20", "event": "Trump inaugurated - pro-crypto administration", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2025-01-23", "event": "Trump signs executive order on Bitcoin reserve", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
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
