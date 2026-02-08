"""
Real-Time News Monitoring Service
==================================
WebSocket-based live news feed that auto-detects trending events
and suggests trigger creation for breaking crypto news.
"""

import asyncio
import aiohttp
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set, Callable
from collections import deque
import json
import re

logger = logging.getLogger(__name__)


class TrendingEventDetector:
    """
    Detects trending events from news feeds and suggests trigger creation.
    Uses keyword frequency analysis and sentiment spike detection.
    """
    
    def __init__(self):
        # Trending keywords tracking (last 1 hour)
        self.keyword_counts = {}  # keyword -> [(timestamp, count)]
        self.keyword_window = timedelta(hours=1)
        
        # High-impact keywords that should always trigger alerts
        self.high_impact_keywords = {
            # Regulatory
            "sec", "lawsuit", "charges", "ban", "regulation", "etf", "approval",
            # Market events
            "crash", "surge", "hack", "exploit", "breach", "bankrupt",
            # Major players
            "blackrock", "fidelity", "grayscale", "microstrategy", "tesla",
            "trump", "biden", "fed", "fomc", "powell",
            # Network events
            "halving", "fork", "upgrade", "outage", "congestion",
            # Institutional
            "institutional", "whale", "billion", "million"
        }
        
        # Coin mention tracking
        self.coin_mentions = {}  # coin -> [(timestamp, sentiment)]
        
        # Recent events cache
        self.recent_events = deque(maxlen=100)
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
    def register_alert_callback(self, callback: Callable):
        """Register a callback for trending alerts"""
        self.alert_callbacks.append(callback)
        
    async def _notify_alert(self, alert: Dict):
        """Notify all registered callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        text_lower = text.lower()
        words = re.findall(r'\b[a-z]+\b', text_lower)
        
        # Filter to relevant keywords
        relevant = []
        for word in words:
            if len(word) >= 3:
                # Check against high impact keywords
                for keyword in self.high_impact_keywords:
                    if keyword in word or word in keyword:
                        relevant.append(keyword)
                        break
        
        return list(set(relevant))
    
    def extract_coins(self, text: str) -> List[str]:
        """Extract cryptocurrency mentions from text"""
        text_upper = text.upper()
        
        coin_patterns = {
            "BTC": ["BITCOIN", "BTC"],
            "ETH": ["ETHEREUM", "ETH", "ETHER"],
            "SOL": ["SOLANA", "SOL"],
            "XRP": ["RIPPLE", "XRP"],
            "ADA": ["CARDANO", "ADA"],
            "DOGE": ["DOGECOIN", "DOGE"],
            "BNB": ["BINANCE", "BNB"],
            "AVAX": ["AVALANCHE", "AVAX"],
            "MATIC": ["POLYGON", "MATIC"],
            "LINK": ["CHAINLINK", "LINK"],
            "DOT": ["POLKADOT", "DOT"],
            "UNI": ["UNISWAP", "UNI"],
        }
        
        found_coins = []
        for symbol, patterns in coin_patterns.items():
            for pattern in patterns:
                if pattern in text_upper:
                    found_coins.append(symbol)
                    break
        
        return list(set(found_coins))
    
    async def process_news_item(self, news: Dict) -> Optional[Dict]:
        """
        Process a news item and detect if it's trending/important.
        Returns alert if significant event detected.
        """
        title = news.get("title", "")
        body = news.get("body", news.get("description", ""))
        full_text = f"{title} {body}"
        
        # Extract data
        keywords = self.extract_keywords(full_text)
        coins = self.extract_coins(full_text)
        sentiment = news.get("sentiment", "NEUTRAL")
        
        now = datetime.now(timezone.utc)
        
        # Update keyword counts
        for keyword in keywords:
            if keyword not in self.keyword_counts:
                self.keyword_counts[keyword] = []
            self.keyword_counts[keyword].append((now, 1))
        
        # Update coin mentions
        for coin in coins:
            if coin not in self.coin_mentions:
                self.coin_mentions[coin] = []
            self.coin_mentions[coin].append((now, sentiment))
        
        # Clean old data
        self._cleanup_old_data(now)
        
        # Calculate trending score
        trending_score = self._calculate_trending_score(keywords, coins)
        
        # Check if this is a significant event
        is_significant = (
            trending_score >= 70 or
            any(k in self.high_impact_keywords for k in keywords) or
            len(coins) >= 2
        )
        
        event_data = {
            "title": title,
            "keywords": keywords,
            "coins": coins,
            "sentiment": sentiment,
            "trending_score": trending_score,
            "timestamp": now.isoformat(),
            "source": news.get("source", "unknown"),
            "url": news.get("url"),
            "is_significant": is_significant
        }
        
        # Store recent event
        self.recent_events.append(event_data)
        
        # Trigger alert if significant
        if is_significant:
            alert = {
                "type": "trending_event",
                "event": event_data,
                "suggested_trigger": self._suggest_trigger(event_data),
                "urgency": "high" if trending_score >= 85 else "medium"
            }
            await self._notify_alert(alert)
            return alert
        
        return None
    
    def _cleanup_old_data(self, now: datetime):
        """Remove data older than the tracking window"""
        cutoff = now - self.keyword_window
        
        for keyword in list(self.keyword_counts.keys()):
            self.keyword_counts[keyword] = [
                (ts, count) for ts, count in self.keyword_counts[keyword]
                if ts > cutoff
            ]
            if not self.keyword_counts[keyword]:
                del self.keyword_counts[keyword]
        
        for coin in list(self.coin_mentions.keys()):
            self.coin_mentions[coin] = [
                (ts, sent) for ts, sent in self.coin_mentions[coin]
                if ts > cutoff
            ]
            if not self.coin_mentions[coin]:
                del self.coin_mentions[coin]
    
    def _calculate_trending_score(self, keywords: List[str], coins: List[str]) -> float:
        """Calculate how trending this event is"""
        score = 50  # Base score
        
        # High impact keywords boost
        high_impact_count = sum(1 for k in keywords if k in self.high_impact_keywords)
        score += high_impact_count * 15
        
        # Multiple coin mentions boost
        score += len(coins) * 10
        
        # Keyword frequency boost
        for keyword in keywords:
            if keyword in self.keyword_counts:
                recent_count = len(self.keyword_counts[keyword])
                if recent_count >= 3:  # Trending if mentioned 3+ times
                    score += 10
        
        return min(100, score)
    
    def _suggest_trigger(self, event: Dict) -> Dict:
        """Suggest a trigger configuration for this event"""
        keywords = event.get("keywords", [])
        coins = event.get("coins", ["BTC", "ETH"])
        sentiment = event.get("sentiment", "NEUTRAL")
        
        # Determine action based on sentiment
        if sentiment == "POSITIVE":
            action = "buy"
        elif sentiment == "NEGATIVE":
            action = "sell"
        else:
            action = "alert"
        
        return {
            "name": f"Auto: {event.get('title', 'Event')[:50]}",
            "keywords": keywords[:5],
            "coins": coins[:4],
            "action": action,
            "sentiment_filter": sentiment.lower() if sentiment != "NEUTRAL" else "any",
            "cooldown_hours": 6,
            "description": f"Auto-suggested trigger for: {event.get('title', '')[:100]}"
        }
    
    def get_trending_summary(self) -> Dict:
        """Get summary of currently trending topics"""
        now = datetime.now(timezone.utc)
        self._cleanup_old_data(now)
        
        # Top keywords
        keyword_freq = {
            k: len(v) for k, v in self.keyword_counts.items()
        }
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top coins
        coin_freq = {
            c: len(v) for c, v in self.coin_mentions.items()
        }
        top_coins = sorted(coin_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Coin sentiments
        coin_sentiments = {}
        for coin, mentions in self.coin_mentions.items():
            sentiments = [s for _, s in mentions]
            positive = sentiments.count("POSITIVE")
            negative = sentiments.count("NEGATIVE")
            total = len(sentiments)
            if total > 0:
                coin_sentiments[coin] = {
                    "positive_pct": (positive / total) * 100,
                    "negative_pct": (negative / total) * 100,
                    "neutral_pct": ((total - positive - negative) / total) * 100,
                    "total_mentions": total
                }
        
        return {
            "top_keywords": [{"keyword": k, "count": c} for k, c in top_keywords],
            "top_coins": [{"coin": c, "mentions": m} for c, m in top_coins],
            "coin_sentiments": coin_sentiments,
            "recent_events_count": len(self.recent_events),
            "timestamp": now.isoformat()
        }


class RealTimeNewsMonitor:
    """
    Real-time news monitoring service with WebSocket support.
    Polls multiple news sources and broadcasts updates.
    """
    
    def __init__(self, db=None, coinstats_api_key: str = None):
        self.db = db
        self.coinstats_api_key = coinstats_api_key or os.getenv("COINSTATS_API_KEY")
        
        self.is_running = False
        self.poll_interval = 60  # seconds
        
        # Event detector
        self.detector = TrendingEventDetector()
        
        # WebSocket clients
        self.ws_clients: Set = set()
        
        # News cache to avoid duplicates
        self.seen_news_ids: Set[str] = set()
        self.max_cache_size = 1000
        
        # Stats
        self.stats = {
            "news_processed": 0,
            "alerts_triggered": 0,
            "last_poll": None,
            "started_at": None
        }
        
        logger.info("📰 Real-Time News Monitor initialized")
    
    async def start(self, poll_interval: int = 60):
        """Start the news monitoring service"""
        self.is_running = True
        self.poll_interval = poll_interval
        self.stats["started_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"🚀 Starting news monitor (interval: {poll_interval}s)")
        
        while self.is_running:
            try:
                await self._poll_news_sources()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"News monitor error: {e}")
                await asyncio.sleep(10)
    
    def stop(self):
        """Stop the monitoring service"""
        self.is_running = False
        logger.info("⏹️ News monitor stopped")
    
    async def _poll_news_sources(self):
        """Poll all configured news sources"""
        self.stats["last_poll"] = datetime.now(timezone.utc).isoformat()
        
        news_items = []
        
        # 1. CoinStats API
        if self.coinstats_api_key:
            try:
                coinstats_news = await self._fetch_coinstats_news()
                news_items.extend(coinstats_news)
            except Exception as e:
                logger.warning(f"CoinStats fetch error: {e}")
        
        # 2. CoinDesk RSS (fallback)
        try:
            coindesk_news = await self._fetch_coindesk_news()
            news_items.extend(coindesk_news)
        except Exception as e:
            logger.warning(f"CoinDesk fetch error: {e}")
        
        # Process new items
        for news in news_items:
            news_id = news.get("id") or news.get("url") or news.get("title")
            
            if news_id and news_id not in self.seen_news_ids:
                self.seen_news_ids.add(news_id)
                self.stats["news_processed"] += 1
                
                # Process through detector
                alert = await self.detector.process_news_item(news)
                
                if alert:
                    self.stats["alerts_triggered"] += 1
                    await self._broadcast_alert(alert)
                
                # Broadcast news update to WebSocket clients
                await self._broadcast_news(news)
        
        # Cleanup cache
        if len(self.seen_news_ids) > self.max_cache_size:
            self.seen_news_ids = set(list(self.seen_news_ids)[-500:])
    
    async def _fetch_coinstats_news(self) -> List[Dict]:
        """Fetch news from CoinStats API"""
        url = "https://openapiv1.coinstats.app/news"
        headers = {
            "accept": "application/json",
            "X-API-KEY": self.coinstats_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    news_list = data.get("result", [])
                    
                    return [
                        {
                            "id": n.get("id"),
                            "title": n.get("title"),
                            "body": n.get("description"),
                            "url": n.get("link"),
                            "source": n.get("source"),
                            "sentiment": self._detect_sentiment(n.get("title", "") + " " + n.get("description", "")),
                            "published_at": n.get("feedDate"),
                            "coins": n.get("coins", [])
                        }
                        for n in news_list[:20]
                    ]
        
        return []
    
    async def _fetch_coindesk_news(self) -> List[Dict]:
        """Fetch news from CoinDesk"""
        url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Simple RSS parsing
                    items = []
                    for match in re.finditer(r'<item>.*?</item>', text, re.DOTALL):
                        item_text = match.group()
                        title_match = re.search(r'<title>(?:<!\[CDATA\[)?(.+?)(?:\]\]>)?</title>', item_text)
                        link_match = re.search(r'<link>(.+?)</link>', item_text)
                        desc_match = re.search(r'<description>(?:<!\[CDATA\[)?(.+?)(?:\]\]>)?</description>', item_text, re.DOTALL)
                        
                        if title_match:
                            title = title_match.group(1).strip()
                            items.append({
                                "id": link_match.group(1) if link_match else title,
                                "title": title,
                                "body": desc_match.group(1)[:500] if desc_match else "",
                                "url": link_match.group(1) if link_match else "",
                                "source": "coindesk",
                                "sentiment": self._detect_sentiment(title)
                            })
                    
                    return items[:10]
        
        return []
    
    def _detect_sentiment(self, text: str) -> str:
        """Simple sentiment detection"""
        text_lower = text.lower()
        
        positive_words = ["surge", "rally", "bullish", "gains", "soars", "breakthrough", 
                         "approval", "adoption", "partnership", "milestone", "record"]
        negative_words = ["crash", "plunge", "bearish", "losses", "hack", "exploit", 
                         "lawsuit", "ban", "fraud", "scam", "collapse"]
        
        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)
        
        if positive_count > negative_count:
            return "POSITIVE"
        elif negative_count > positive_count:
            return "NEGATIVE"
        return "NEUTRAL"
    
    async def _broadcast_news(self, news: Dict):
        """Broadcast news to WebSocket clients"""
        message = json.dumps({
            "type": "news",
            "data": news
        })
        
        disconnected = set()
        for ws in self.ws_clients:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)
        
        self.ws_clients -= disconnected
    
    async def _broadcast_alert(self, alert: Dict):
        """Broadcast alert to WebSocket clients"""
        message = json.dumps({
            "type": "alert",
            "data": alert
        })
        
        disconnected = set()
        for ws in self.ws_clients:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)
        
        self.ws_clients -= disconnected
        
        # Store alert in database
        if self.db is not None:
            try:
                await self.db.news_alerts.insert_one({
                    **alert,
                    "created_at": datetime.now(timezone.utc)
                })
            except Exception as e:
                logger.error(f"Failed to store alert: {e}")
    
    def register_ws_client(self, ws):
        """Register a WebSocket client"""
        self.ws_clients.add(ws)
    
    def unregister_ws_client(self, ws):
        """Unregister a WebSocket client"""
        self.ws_clients.discard(ws)
    
    def get_status(self) -> Dict:
        """Get monitor status"""
        return {
            "is_running": self.is_running,
            "poll_interval": self.poll_interval,
            "ws_clients": len(self.ws_clients),
            "trending": self.detector.get_trending_summary(),
            "stats": self.stats
        }
    
    def get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent significant events"""
        events = list(self.detector.recent_events)
        significant = [e for e in events if e.get("is_significant")]
        return significant[-limit:]


# Singleton instance
_news_monitor: Optional[RealTimeNewsMonitor] = None


def get_news_monitor(db=None) -> RealTimeNewsMonitor:
    """Get or create news monitor singleton"""
    global _news_monitor
    if _news_monitor is None:
        _news_monitor = RealTimeNewsMonitor(db)
    return _news_monitor
