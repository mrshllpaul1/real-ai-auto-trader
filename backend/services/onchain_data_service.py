"""
On-Chain Data Service
=====================
Real-time on-chain metrics, whale tracking, and network analysis.
"""

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class WhaleTransaction:
    """Large transaction record"""
    tx_hash: str
    timestamp: str
    amount_btc: float
    amount_usd: float
    from_type: str  # 'exchange', 'unknown', 'whale_wallet', 'miner'
    to_type: str
    from_address: str
    to_address: str
    impact: str  # 'bullish', 'bearish', 'neutral'


@dataclass
class ExchangeFlow:
    """Exchange inflow/outflow data"""
    exchange: str
    inflow_btc: float
    outflow_btc: float
    net_flow_btc: float
    inflow_usd: float
    outflow_usd: float
    timestamp: str


@dataclass
class NetworkMetrics:
    """Blockchain network metrics"""
    active_addresses_24h: int
    transaction_count_24h: int
    transaction_volume_usd: float
    avg_transaction_value: float
    hash_rate: float
    difficulty: float
    block_time_avg: float
    mempool_size: int
    fees_avg_usd: float
    timestamp: str


@dataclass
class WhaleWalletStats:
    """Whale wallet statistics"""
    total_whale_wallets: int
    total_whale_btc: float
    change_7d: int
    change_30d: int
    avg_wallet_age_days: float
    accumulation_score: float  # 0-100, higher = more accumulation


class OnChainDataService:
    """
    On-chain data service for:
    1. Whale activity tracking
    2. Exchange flow monitoring
    3. Network metrics analysis
    4. Large transaction alerts
    """
    
    # Major exchanges for tracking
    EXCHANGES = [
        "Binance", "Coinbase", "Kraken", "Bitfinex", "Gemini", 
        "Bitstamp", "OKX", "Bybit", "KuCoin", "Huobi"
    ]
    
    # Whale wallet thresholds (BTC)
    WHALE_THRESHOLD_BTC = 1000
    LARGE_TX_THRESHOLD_USD = 10_000_000
    
    def __init__(self, db):
        self.db = db
        self.recent_whale_txs: List[WhaleTransaction] = []
        self.exchange_flows: Dict[str, ExchangeFlow] = {}
        self.network_metrics: Optional[NetworkMetrics] = None
        self.whale_stats: Optional[WhaleWalletStats] = None
        self.is_tracking = False
        self._tracking_task = None
        
        # Simulated real-time data (in production, connect to APIs)
        self._btc_price = 95000
        
        logger.info("✅ On-Chain Data Service initialized")
    
    async def get_whale_activity(self) -> Dict[str, Any]:
        """Get comprehensive whale activity data"""
        await self._update_simulated_data()
        
        # Calculate aggregate metrics
        total_inflow = sum(f.inflow_btc for f in self.exchange_flows.values())
        total_outflow = sum(f.outflow_btc for f in self.exchange_flows.values())
        net_flow = total_outflow - total_inflow  # Positive = accumulation
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "btc_price": self._btc_price,
            "exchange_flows": {
                "total_inflow_btc": round(total_inflow, 2),
                "total_outflow_btc": round(total_outflow, 2),
                "net_flow_btc": round(net_flow, 2),
                "total_inflow_usd": round(total_inflow * self._btc_price, 0),
                "total_outflow_usd": round(total_outflow * self._btc_price, 0),
                "net_flow_usd": round(net_flow * self._btc_price, 0),
                "signal": "accumulation" if net_flow > 100 else "distribution" if net_flow < -100 else "neutral"
            },
            "whale_wallets": asdict(self.whale_stats) if self.whale_stats else None,
            "recent_large_transactions": [asdict(tx) for tx in self.recent_whale_txs[:10]],
            "exchange_breakdown": [asdict(f) for f in self.exchange_flows.values()],
            "network_metrics": asdict(self.network_metrics) if self.network_metrics else None,
            "analysis": {
                "whale_sentiment": self._calculate_whale_sentiment(),
                "accumulation_score": self.whale_stats.accumulation_score if self.whale_stats else 50,
                "network_health": self._calculate_network_health(),
                "key_observations": self._generate_observations()
            }
        }
    
    async def get_exchange_flows(self) -> Dict[str, Any]:
        """Get detailed exchange flow data"""
        await self._update_simulated_data()
        
        flows_list = []
        for exchange, flow in self.exchange_flows.items():
            flows_list.append({
                "exchange": exchange,
                "inflow_btc": flow.inflow_btc,
                "outflow_btc": flow.outflow_btc,
                "net_flow_btc": flow.net_flow_btc,
                "inflow_usd": flow.inflow_usd,
                "outflow_usd": flow.outflow_usd,
                "sentiment": "bullish" if flow.net_flow_btc < -50 else "bearish" if flow.net_flow_btc > 50 else "neutral"
            })
        
        # Sort by absolute net flow
        flows_list.sort(key=lambda x: abs(x["net_flow_btc"]), reverse=True)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "exchanges": flows_list,
            "summary": {
                "most_inflows": max(flows_list, key=lambda x: x["inflow_btc"])["exchange"],
                "most_outflows": max(flows_list, key=lambda x: x["outflow_btc"])["exchange"],
                "total_exchanges_tracked": len(flows_list)
            }
        }
    
    async def get_recent_whale_transactions(self, limit: int = 20) -> Dict[str, Any]:
        """Get recent large transactions"""
        await self._update_simulated_data()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transactions": [asdict(tx) for tx in self.recent_whale_txs[:limit]],
            "summary": {
                "total_volume_btc": sum(tx.amount_btc for tx in self.recent_whale_txs[:limit]),
                "total_volume_usd": sum(tx.amount_usd for tx in self.recent_whale_txs[:limit]),
                "bullish_count": sum(1 for tx in self.recent_whale_txs[:limit] if tx.impact == "bullish"),
                "bearish_count": sum(1 for tx in self.recent_whale_txs[:limit] if tx.impact == "bearish")
            }
        }
    
    async def get_network_metrics(self) -> Dict[str, Any]:
        """Get blockchain network metrics"""
        await self._update_simulated_data()
        
        if not self.network_metrics:
            return {"error": "Network metrics not available"}
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": asdict(self.network_metrics),
            "trends": {
                "active_addresses_trend": "up" if random.random() > 0.4 else "down",
                "transaction_volume_trend": "up" if random.random() > 0.45 else "down",
                "hash_rate_trend": "up",  # Generally trending up
                "fees_trend": "stable"
            },
            "health_score": self._calculate_network_health()
        }
    
    async def get_whale_wallet_distribution(self) -> Dict[str, Any]:
        """Get whale wallet distribution analysis"""
        await self._update_simulated_data()
        
        # Simulated distribution data
        distribution = {
            "1000-5000_btc": {"count": 1842, "total_btc": 4_500_000, "pct_supply": 21.4},
            "5000-10000_btc": {"count": 215, "total_btc": 1_500_000, "pct_supply": 7.1},
            "10000-50000_btc": {"count": 78, "total_btc": 1_800_000, "pct_supply": 8.6},
            "50000+_btc": {"count": 7, "total_btc": 850_000, "pct_supply": 4.0}
        }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "distribution": distribution,
            "total_whale_wallets": sum(d["count"] for d in distribution.values()),
            "total_whale_btc": sum(d["total_btc"] for d in distribution.values()),
            "whale_dominance_pct": sum(d["pct_supply"] for d in distribution.values()),
            "concentration_index": 0.72,  # Gini-like measure
            "whale_stats": asdict(self.whale_stats) if self.whale_stats else None
        }
    
    async def _update_simulated_data(self):
        """Update simulated on-chain data (replace with real API calls in production)"""
        now = datetime.now(timezone.utc)
        
        # Update BTC price with small random walk
        self._btc_price *= (1 + random.gauss(0, 0.002))
        
        # Generate exchange flows
        for exchange in self.EXCHANGES:
            inflow = random.uniform(100, 800)
            outflow = random.uniform(150, 900)
            
            self.exchange_flows[exchange] = ExchangeFlow(
                exchange=exchange,
                inflow_btc=round(inflow, 2),
                outflow_btc=round(outflow, 2),
                net_flow_btc=round(inflow - outflow, 2),
                inflow_usd=round(inflow * self._btc_price, 0),
                outflow_usd=round(outflow * self._btc_price, 0),
                timestamp=now.isoformat()
            )
        
        # Generate whale transactions
        self.recent_whale_txs = []
        for i in range(15):
            amount = random.uniform(200, 3000)
            from_type = random.choice(["exchange", "unknown", "whale_wallet", "miner"])
            to_type = random.choice(["exchange", "unknown", "whale_wallet"])
            
            # Determine impact
            if from_type == "exchange" and to_type != "exchange":
                impact = "bullish"  # Withdrawal from exchange
            elif from_type != "exchange" and to_type == "exchange":
                impact = "bearish"  # Deposit to exchange
            else:
                impact = "neutral"
            
            tx = WhaleTransaction(
                tx_hash=f"0x{random.randbytes(32).hex()[:64]}",
                timestamp=(now - timedelta(minutes=random.randint(1, 120))).isoformat(),
                amount_btc=round(amount, 2),
                amount_usd=round(amount * self._btc_price, 0),
                from_type=from_type,
                to_type=to_type,
                from_address=f"bc1q{random.randbytes(20).hex()[:38]}",
                to_address=f"bc1q{random.randbytes(20).hex()[:38]}",
                impact=impact
            )
            self.recent_whale_txs.append(tx)
        
        # Sort by time (most recent first)
        self.recent_whale_txs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Update network metrics
        self.network_metrics = NetworkMetrics(
            active_addresses_24h=random.randint(850000, 950000),
            transaction_count_24h=random.randint(280000, 350000),
            transaction_volume_usd=random.uniform(35_000_000_000, 50_000_000_000),
            avg_transaction_value=random.uniform(15000, 25000),
            hash_rate=random.uniform(550, 600),  # EH/s
            difficulty=random.uniform(75, 85) * 1e12,
            block_time_avg=random.uniform(9.5, 10.5),
            mempool_size=random.randint(5000, 50000),
            fees_avg_usd=random.uniform(2, 15),
            timestamp=now.isoformat()
        )
        
        # Update whale stats
        whale_change = random.randint(-5, 15)
        self.whale_stats = WhaleWalletStats(
            total_whale_wallets=2142 + whale_change,
            total_whale_btc=8_650_000 + random.randint(-50000, 50000),
            change_7d=whale_change,
            change_30d=random.randint(-20, 50),
            avg_wallet_age_days=random.uniform(800, 1200),
            accumulation_score=random.uniform(45, 75)
        )
    
    def _calculate_whale_sentiment(self) -> Dict[str, Any]:
        """Calculate overall whale sentiment"""
        if not self.recent_whale_txs:
            return {"sentiment": "neutral", "score": 50}
        
        bullish = sum(1 for tx in self.recent_whale_txs if tx.impact == "bullish")
        bearish = sum(1 for tx in self.recent_whale_txs if tx.impact == "bearish")
        total = len(self.recent_whale_txs)
        
        score = 50 + (bullish - bearish) / total * 50 if total > 0 else 50
        
        if score > 60:
            sentiment = "bullish"
        elif score < 40:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": round(score, 1),
            "bullish_txs": bullish,
            "bearish_txs": bearish,
            "neutral_txs": total - bullish - bearish
        }
    
    def _calculate_network_health(self) -> float:
        """Calculate network health score (0-100)"""
        if not self.network_metrics:
            return 50.0
        
        score = 50.0
        
        # Active addresses contribution
        if self.network_metrics.active_addresses_24h > 900000:
            score += 15
        elif self.network_metrics.active_addresses_24h > 800000:
            score += 10
        
        # Hash rate contribution (security)
        if self.network_metrics.hash_rate > 580:
            score += 15
        elif self.network_metrics.hash_rate > 550:
            score += 10
        
        # Block time contribution
        if 9.5 <= self.network_metrics.block_time_avg <= 10.5:
            score += 10
        
        # Mempool not congested
        if self.network_metrics.mempool_size < 20000:
            score += 10
        
        return min(100, score)
    
    def _generate_observations(self) -> List[str]:
        """Generate key observations from the data"""
        observations = []
        
        # Exchange flow observation
        total_net = sum(f.net_flow_btc for f in self.exchange_flows.values())
        if total_net < -500:
            observations.append("Strong accumulation: More BTC leaving exchanges than entering")
        elif total_net > 500:
            observations.append("Distribution pressure: More BTC flowing into exchanges")
        
        # Whale activity
        whale_sentiment = self._calculate_whale_sentiment()
        if whale_sentiment["sentiment"] == "bullish":
            observations.append(f"Whale activity bullish: {whale_sentiment['bullish_txs']} accumulation transactions")
        elif whale_sentiment["sentiment"] == "bearish":
            observations.append(f"Whale activity bearish: {whale_sentiment['bearish_txs']} distribution transactions")
        
        # Network health
        health = self._calculate_network_health()
        if health > 80:
            observations.append("Network health excellent: High activity and security")
        elif health < 50:
            observations.append("Network health concerns: Monitor closely")
        
        # Whale wallet changes
        if self.whale_stats and self.whale_stats.change_7d > 10:
            observations.append(f"New whale wallets: {self.whale_stats.change_7d} added this week")
        
        return observations
    
    async def start_tracking(self):
        """Start real-time tracking"""
        if self.is_tracking:
            return {"status": "already_tracking"}
        
        self.is_tracking = True
        self._tracking_task = asyncio.create_task(self._tracking_loop())
        
        logger.info("📊 On-chain tracking started")
        return {"status": "started"}
    
    async def stop_tracking(self):
        """Stop real-time tracking"""
        self.is_tracking = False
        if self._tracking_task:
            self._tracking_task.cancel()
        
        return {"status": "stopped"}
    
    async def _tracking_loop(self):
        """Continuous tracking loop"""
        while self.is_tracking:
            try:
                await self._update_simulated_data()
                
                # Save to database
                await self.db.onchain_snapshots.insert_one({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "whale_sentiment": self._calculate_whale_sentiment(),
                    "network_health": self._calculate_network_health(),
                    "accumulation_score": self.whale_stats.accumulation_score if self.whale_stats else 50
                })
                
                await asyncio.sleep(60)  # Update every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Tracking error: {e}")
                await asyncio.sleep(30)


# Singleton instance
_onchain_service = None


def get_onchain_service(db=None):
    """Get or create on-chain data service instance"""
    global _onchain_service
    
    if _onchain_service is None and db is not None:
        _onchain_service = OnChainDataService(db)
    
    return _onchain_service
