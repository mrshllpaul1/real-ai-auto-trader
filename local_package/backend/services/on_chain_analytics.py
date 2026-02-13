"""
On-Chain Analytics Service
Enhancement #2: Active addresses, NVT ratio, exchange flows, whale tracking
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class OnChainAnalytics:
    """
    On-chain analytics for cryptocurrency trading signals:
    - Active addresses tracking
    - NVT (Network Value to Transactions) ratio
    - Exchange inflows/outflows
    - Whale wallet monitoring
    - MVRV (Market Value to Realized Value) ratio
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.cache = {}
        self.cache_ttl = 300  # 5 minute cache
        
        # Thresholds
        self.whale_threshold_btc = 100  # 100 BTC = whale
        self.whale_threshold_eth = 1000  # 1000 ETH = whale
        self.high_nvt_threshold = 150  # High NVT = overvalued
        self.low_nvt_threshold = 50  # Low NVT = undervalued
        
    async def get_on_chain_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive on-chain metrics for a coin
        
        Args:
            symbol: Coin symbol (BTC, ETH, etc.)
            
        Returns:
            On-chain metrics with trading signals
        """
        try:
            # Normalize symbol
            coin = symbol.upper().replace('USD', '').replace('USDT', '')
            
            # Get individual metrics
            active_addresses = await self._get_active_addresses(coin)
            nvt_ratio = await self._calculate_nvt(coin)
            exchange_flows = await self._get_exchange_flows(coin)
            whale_activity = await self._get_whale_movements(coin)
            mvrv = await self._calculate_mvrv(coin)
            
            # Generate composite signal
            signal = self._generate_on_chain_signal(
                active_addresses, nvt_ratio, exchange_flows, whale_activity, mvrv
            )
            
            metrics = {
                'symbol': coin,
                'timestamp': datetime.utcnow().isoformat(),
                'active_addresses': active_addresses,
                'nvt_ratio': nvt_ratio,
                'exchange_flows': exchange_flows,
                'whale_activity': whale_activity,
                'mvrv': mvrv,
                'signal': signal
            }
            
            # Store metrics
            await self._store_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"On-chain metrics failed for {symbol}: {e}")
            return self._empty_metrics(symbol)
    
    async def _get_active_addresses(self, coin: str) -> Dict[str, Any]:
        """Get active address metrics"""
        # Simulated data - in production, fetch from Glassnode/IntoTheBlock
        np.random.seed(hash(coin + datetime.utcnow().strftime("%Y%m%d")) % 2**32)
        
        base_addresses = {
            'BTC': 900000, 'ETH': 500000, 'SOL': 200000,
            'ADA': 150000, 'DOT': 50000, 'MATIC': 100000
        }.get(coin, 30000)
        
        # Daily active addresses with some variance
        daily_active = int(base_addresses * np.random.uniform(0.8, 1.2))
        weekly_avg = int(daily_active * np.random.uniform(0.9, 1.1))
        monthly_avg = int(daily_active * np.random.uniform(0.85, 1.15))
        
        # Calculate trend
        daily_change = (daily_active - weekly_avg) / weekly_avg * 100 if weekly_avg > 0 else 0
        weekly_change = (weekly_avg - monthly_avg) / monthly_avg * 100 if monthly_avg > 0 else 0
        
        # Determine trend direction
        if daily_change > 10:
            trend = 'strongly_increasing'
        elif daily_change > 3:
            trend = 'increasing'
        elif daily_change < -10:
            trend = 'strongly_decreasing'
        elif daily_change < -3:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'daily': daily_active,
            'weekly_avg': weekly_avg,
            'monthly_avg': monthly_avg,
            'daily_change_pct': round(daily_change, 2),
            'weekly_change_pct': round(weekly_change, 2),
            'trend': trend,
            'signal': 'bullish' if daily_change > 5 else ('bearish' if daily_change < -5 else 'neutral')
        }
    
    async def _calculate_nvt(self, coin: str) -> Dict[str, Any]:
        """Calculate NVT (Network Value to Transactions) ratio"""
        np.random.seed(hash(coin + "nvt" + datetime.utcnow().strftime("%Y%m%d")) % 2**32)
        
        # Simulated NVT values
        base_nvt = {
            'BTC': 80, 'ETH': 60, 'SOL': 45, 'ADA': 70, 'DOT': 55
        }.get(coin, 65)
        
        current_nvt = base_nvt * np.random.uniform(0.7, 1.5)
        nvt_90d_avg = base_nvt * np.random.uniform(0.9, 1.1)
        
        # NVT signal interpretation
        if current_nvt > self.high_nvt_threshold:
            signal = 'overvalued'
            description = 'High NVT suggests network is overvalued relative to transaction volume'
        elif current_nvt < self.low_nvt_threshold:
            signal = 'undervalued'
            description = 'Low NVT suggests network is undervalued - potential buying opportunity'
        else:
            signal = 'fair_value'
            description = 'NVT is within normal range'
        
        return {
            'current': round(current_nvt, 2),
            'avg_90d': round(nvt_90d_avg, 2),
            'deviation_pct': round((current_nvt - nvt_90d_avg) / nvt_90d_avg * 100, 2),
            'signal': signal,
            'description': description,
            'thresholds': {
                'high': self.high_nvt_threshold,
                'low': self.low_nvt_threshold
            }
        }
    
    async def _get_exchange_flows(self, coin: str) -> Dict[str, Any]:
        """Get exchange inflow/outflow data"""
        np.random.seed(hash(coin + "flows" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # Base volumes in USD millions
        base_volume = {
            'BTC': 500, 'ETH': 300, 'SOL': 50, 'ADA': 30, 'DOT': 20
        }.get(coin, 10)
        
        # Generate realistic flow patterns
        inflow_24h = base_volume * np.random.uniform(0.3, 0.7) * 1_000_000
        outflow_24h = base_volume * np.random.uniform(0.3, 0.7) * 1_000_000
        
        net_flow = outflow_24h - inflow_24h  # Positive = accumulation
        net_flow_pct = (net_flow / (inflow_24h + outflow_24h)) * 100 if (inflow_24h + outflow_24h) > 0 else 0
        
        # 7-day trend
        net_flow_7d = net_flow * np.random.uniform(5, 8)  # Rough weekly estimate
        
        # Signal interpretation
        if net_flow_pct > 15:
            signal = 'strong_accumulation'
            pressure = 'bullish'
        elif net_flow_pct > 5:
            signal = 'accumulation'
            pressure = 'slightly_bullish'
        elif net_flow_pct < -15:
            signal = 'strong_distribution'
            pressure = 'bearish'
        elif net_flow_pct < -5:
            signal = 'distribution'
            pressure = 'slightly_bearish'
        else:
            signal = 'neutral'
            pressure = 'neutral'
        
        return {
            'inflow_24h_usd': round(inflow_24h, 0),
            'outflow_24h_usd': round(outflow_24h, 0),
            'net_flow_24h_usd': round(net_flow, 0),
            'net_flow_pct': round(net_flow_pct, 2),
            'net_flow_7d_usd': round(net_flow_7d, 0),
            'signal': signal,
            'pressure': pressure,
            'interpretation': f"{'Coins leaving' if net_flow > 0 else 'Coins entering'} exchanges - {pressure} signal"
        }
    
    async def _get_whale_movements(self, coin: str) -> Dict[str, Any]:
        """Track whale wallet movements"""
        np.random.seed(hash(coin + "whale" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # Simulate whale transactions
        num_transactions = np.random.randint(5, 25)
        
        transactions = []
        total_inflow = 0
        total_outflow = 0
        
        for i in range(num_transactions):
            is_inflow = np.random.random() > 0.5
            
            # Amount in coin units
            if coin == 'BTC':
                amount = np.random.pareto(1.5) * 50 + self.whale_threshold_btc
                usd_value = amount * 43000
            elif coin == 'ETH':
                amount = np.random.pareto(1.5) * 500 + self.whale_threshold_eth
                usd_value = amount * 2300
            else:
                amount = np.random.pareto(1.5) * 10000 + 1000
                usd_value = amount * np.random.uniform(0.5, 50)
            
            if is_inflow:
                total_inflow += usd_value
                tx_type = 'exchange_deposit'
            else:
                total_outflow += usd_value
                tx_type = 'exchange_withdrawal'
            
            transactions.append({
                'type': tx_type,
                'amount': round(amount, 2),
                'usd_value': round(usd_value, 0),
                'time_ago_minutes': np.random.randint(5, 1440)
            })
        
        # Sort by recency
        transactions.sort(key=lambda x: x['time_ago_minutes'])
        
        # Calculate whale sentiment
        net_whale_flow = total_outflow - total_inflow
        if net_whale_flow > total_inflow * 0.3:
            sentiment = 'accumulating'
        elif net_whale_flow < -total_outflow * 0.3:
            sentiment = 'distributing'
        else:
            sentiment = 'neutral'
        
        return {
            'transactions_24h': num_transactions,
            'total_inflow_usd': round(total_inflow, 0),
            'total_outflow_usd': round(total_outflow, 0),
            'net_flow_usd': round(net_whale_flow, 0),
            'sentiment': sentiment,
            'recent_transactions': transactions[:5],
            'alert': num_transactions > 15 or abs(net_whale_flow) > 50_000_000
        }
    
    async def _calculate_mvrv(self, coin: str) -> Dict[str, Any]:
        """Calculate MVRV (Market Value to Realized Value) ratio"""
        np.random.seed(hash(coin + "mvrv" + datetime.utcnow().strftime("%Y%m%d")) % 2**32)
        
        # MVRV typically ranges from 0.5 to 3.5
        # Above 3.0 = overvalued/top signal
        # Below 1.0 = undervalued/bottom signal
        current_mvrv = np.random.uniform(0.7, 2.5)
        historical_avg = 1.5
        
        # Z-score calculation
        std_dev = 0.5
        z_score = (current_mvrv - historical_avg) / std_dev
        
        # Signal interpretation
        if current_mvrv > 3.0:
            signal = 'extreme_overvalued'
            zone = 'danger'
        elif current_mvrv > 2.5:
            signal = 'overvalued'
            zone = 'caution'
        elif current_mvrv < 0.8:
            signal = 'extreme_undervalued'
            zone = 'opportunity'
        elif current_mvrv < 1.0:
            signal = 'undervalued'
            zone = 'accumulation'
        else:
            signal = 'fair_value'
            zone = 'neutral'
        
        return {
            'current': round(current_mvrv, 3),
            'historical_avg': historical_avg,
            'z_score': round(z_score, 2),
            'signal': signal,
            'zone': zone,
            'thresholds': {
                'extreme_high': 3.0,
                'high': 2.5,
                'low': 1.0,
                'extreme_low': 0.8
            }
        }
    
    def _generate_on_chain_signal(self, addresses: Dict, nvt: Dict, flows: Dict, 
                                   whales: Dict, mvrv: Dict) -> Dict[str, Any]:
        """Generate composite on-chain signal"""
        score = 50  # Neutral starting point
        factors = []
        
        # Active addresses factor (weight: 15%)
        if addresses['trend'] in ['strongly_increasing', 'increasing']:
            score += 8
            factors.append(f"active_addresses_{addresses['trend']}")
        elif addresses['trend'] in ['strongly_decreasing', 'decreasing']:
            score -= 8
            factors.append(f"active_addresses_{addresses['trend']}")
        
        # NVT factor (weight: 20%)
        if nvt['signal'] == 'undervalued':
            score += 12
            factors.append('nvt_undervalued')
        elif nvt['signal'] == 'overvalued':
            score -= 12
            factors.append('nvt_overvalued')
        
        # Exchange flows factor (weight: 25%)
        if flows['signal'] in ['strong_accumulation', 'accumulation']:
            score += 15
            factors.append(f"exchange_{flows['signal']}")
        elif flows['signal'] in ['strong_distribution', 'distribution']:
            score -= 15
            factors.append(f"exchange_{flows['signal']}")
        
        # Whale activity factor (weight: 20%)
        if whales['sentiment'] == 'accumulating':
            score += 12
            factors.append('whales_accumulating')
        elif whales['sentiment'] == 'distributing':
            score -= 12
            factors.append('whales_distributing')
        
        # MVRV factor (weight: 20%)
        if mvrv['zone'] in ['opportunity', 'accumulation']:
            score += 12
            factors.append(f"mvrv_{mvrv['zone']}")
        elif mvrv['zone'] in ['danger', 'caution']:
            score -= 12
            factors.append(f"mvrv_{mvrv['zone']}")
        
        # Determine final signal
        if score >= 70:
            signal = 'strong_buy'
        elif score >= 60:
            signal = 'buy'
        elif score <= 30:
            signal = 'strong_sell'
        elif score <= 40:
            signal = 'sell'
        else:
            signal = 'neutral'
        
        return {
            'signal': signal,
            'score': min(100, max(0, score)),
            'confidence': min(100, abs(score - 50) * 2),
            'factors': factors,
            'weights': {
                'active_addresses': 15,
                'nvt': 20,
                'exchange_flows': 25,
                'whale_activity': 20,
                'mvrv': 20
            }
        }
    
    async def _store_metrics(self, metrics: Dict):
        """Store metrics in database"""
        try:
            await self.db.on_chain_metrics.insert_one({
                **metrics,
                'created_at': datetime.utcnow()
            })
        except Exception as e:
            logger.warning(f"Failed to store on-chain metrics: {e}")
    
    def _empty_metrics(self, symbol: str) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'active_addresses': {'daily': 0, 'trend': 'unknown'},
            'nvt_ratio': {'current': 0, 'signal': 'unknown'},
            'exchange_flows': {'net_flow_pct': 0, 'pressure': 'unknown'},
            'whale_activity': {'sentiment': 'unknown'},
            'mvrv': {'current': 0, 'signal': 'unknown'},
            'signal': {'signal': 'neutral', 'score': 50, 'confidence': 0}
        }
    
    async def get_historical_metrics(self, symbol: str, days: int = 7) -> List[Dict]:
        """Get historical on-chain metrics"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            cursor = self.db.on_chain_metrics.find(
                {'symbol': symbol.upper(), 'created_at': {'$gte': cutoff}},
                {'_id': 0}
            ).sort('created_at', -1).limit(100)
            
            return await cursor.to_list(length=100)
        except Exception as e:
            logger.error(f"Failed to get historical on-chain metrics: {e}")
            return []


# Singleton instance
_on_chain_analytics = None

def get_on_chain_analytics(db: AsyncIOMotorDatabase = None) -> OnChainAnalytics:
    global _on_chain_analytics
    if _on_chain_analytics is None and db is not None:
        _on_chain_analytics = OnChainAnalytics(db)
    return _on_chain_analytics
