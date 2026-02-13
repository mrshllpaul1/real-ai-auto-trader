"""
Order Book Depth Analysis Service
Enhancement #1: Analyze bid/ask spread, order book imbalance, support/resistance walls
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class OrderBookAnalyzer:
    """
    Analyzes order book depth for trading signals:
    - Bid/Ask spread analysis
    - Order book imbalance (buy vs sell pressure)
    - Support/Resistance wall detection
    - Large order detection (whale walls)
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.cache = {}
        self.cache_ttl = 60  # 1 minute cache
        
        # Configuration
        self.depth_levels = 20  # Number of price levels to analyze
        self.whale_threshold = 0.05  # 5% of total volume = whale wall
        self.imbalance_threshold = 0.3  # 30% imbalance is significant
        
    async def analyze_order_book(self, symbol: str, order_book: Dict = None) -> Dict[str, Any]:
        """
        Comprehensive order book analysis
        
        Args:
            symbol: Trading pair symbol
            order_book: Optional pre-fetched order book data
            
        Returns:
            Analysis with spread, imbalance, walls, and trading signal
        """
        try:
            # Use provided order book or generate simulated data
            if not order_book:
                order_book = await self._get_order_book(symbol)
            
            if not order_book or not order_book.get('bids') or not order_book.get('asks'):
                return self._empty_analysis(symbol)
            
            bids = order_book['bids']  # [[price, volume], ...]
            asks = order_book['asks']  # [[price, volume], ...]
            
            # Calculate metrics
            spread_analysis = self._analyze_spread(bids, asks)
            imbalance = self._calculate_imbalance(bids, asks)
            walls = self._detect_walls(bids, asks)
            depth_profile = self._analyze_depth_profile(bids, asks)
            
            # Generate trading signal
            signal = self._generate_signal(spread_analysis, imbalance, walls, depth_profile)
            
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'spread': spread_analysis,
                'imbalance': imbalance,
                'walls': walls,
                'depth_profile': depth_profile,
                'signal': signal,
                'raw_metrics': {
                    'bid_levels': len(bids),
                    'ask_levels': len(asks),
                    'total_bid_volume': sum(b[1] for b in bids[:self.depth_levels]),
                    'total_ask_volume': sum(a[1] for a in asks[:self.depth_levels])
                }
            }
            
            # Store analysis
            await self._store_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Order book analysis failed for {symbol}: {e}")
            return self._empty_analysis(symbol)
    
    def _analyze_spread(self, bids: List, asks: List) -> Dict[str, Any]:
        """Analyze bid-ask spread"""
        if not bids or not asks:
            return {'spread_pct': 0, 'spread_abs': 0, 'quality': 'unknown'}
        
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid_price = (best_bid + best_ask) / 2
        
        spread_abs = best_ask - best_bid
        spread_pct = (spread_abs / mid_price) * 100 if mid_price > 0 else 0
        
        # Classify spread quality
        if spread_pct < 0.05:
            quality = 'excellent'
        elif spread_pct < 0.1:
            quality = 'good'
        elif spread_pct < 0.3:
            quality = 'moderate'
        elif spread_pct < 0.5:
            quality = 'poor'
        else:
            quality = 'very_poor'
        
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'mid_price': mid_price,
            'spread_abs': spread_abs,
            'spread_pct': round(spread_pct, 4),
            'quality': quality
        }
    
    def _calculate_imbalance(self, bids: List, asks: List) -> Dict[str, Any]:
        """Calculate order book imbalance (buy vs sell pressure)"""
        bid_volume = sum(float(b[1]) for b in bids[:self.depth_levels])
        ask_volume = sum(float(a[1]) for a in asks[:self.depth_levels])
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return {'ratio': 0.5, 'pressure': 'neutral', 'strength': 0}
        
        bid_ratio = bid_volume / total_volume
        imbalance = bid_ratio - 0.5  # Positive = buy pressure, negative = sell pressure
        
        # Classify pressure
        if imbalance > self.imbalance_threshold:
            pressure = 'strong_buy'
        elif imbalance > 0.1:
            pressure = 'buy'
        elif imbalance < -self.imbalance_threshold:
            pressure = 'strong_sell'
        elif imbalance < -0.1:
            pressure = 'sell'
        else:
            pressure = 'neutral'
        
        return {
            'bid_volume': round(bid_volume, 2),
            'ask_volume': round(ask_volume, 2),
            'bid_ratio': round(bid_ratio, 4),
            'imbalance': round(imbalance, 4),
            'pressure': pressure,
            'strength': round(abs(imbalance) * 100, 1)
        }
    
    def _detect_walls(self, bids: List, asks: List) -> Dict[str, Any]:
        """Detect support/resistance walls (large orders)"""
        bid_volumes = [float(b[1]) for b in bids[:self.depth_levels]]
        ask_volumes = [float(a[1]) for a in asks[:self.depth_levels]]
        
        total_bid = sum(bid_volumes)
        total_ask = sum(ask_volumes)
        
        support_walls = []
        resistance_walls = []
        
        # Find bid walls (support)
        for i, (price, volume) in enumerate(bids[:self.depth_levels]):
            price, volume = float(price), float(volume)
            if total_bid > 0 and volume / total_bid > self.whale_threshold:
                support_walls.append({
                    'price': price,
                    'volume': volume,
                    'pct_of_total': round((volume / total_bid) * 100, 2),
                    'depth_level': i + 1
                })
        
        # Find ask walls (resistance)
        for i, (price, volume) in enumerate(asks[:self.depth_levels]):
            price, volume = float(price), float(volume)
            if total_ask > 0 and volume / total_ask > self.whale_threshold:
                resistance_walls.append({
                    'price': price,
                    'volume': volume,
                    'pct_of_total': round((volume / total_ask) * 100, 2),
                    'depth_level': i + 1
                })
        
        return {
            'support_walls': support_walls[:3],  # Top 3 support walls
            'resistance_walls': resistance_walls[:3],  # Top 3 resistance walls
            'has_major_support': len(support_walls) > 0,
            'has_major_resistance': len(resistance_walls) > 0,
            'nearest_support': support_walls[0]['price'] if support_walls else None,
            'nearest_resistance': resistance_walls[0]['price'] if resistance_walls else None
        }
    
    def _analyze_depth_profile(self, bids: List, asks: List) -> Dict[str, Any]:
        """Analyze depth profile shape"""
        bid_prices = [float(b[0]) for b in bids[:self.depth_levels]]
        bid_volumes = [float(b[1]) for b in bids[:self.depth_levels]]
        ask_prices = [float(a[0]) for a in asks[:self.depth_levels]]
        ask_volumes = [float(a[1]) for a in asks[:self.depth_levels]]
        
        if not bid_prices or not ask_prices:
            return {'shape': 'unknown', 'liquidity_score': 0}
        
        mid_price = (bid_prices[0] + ask_prices[0]) / 2
        
        # Calculate cumulative depth at different price levels
        depths = [0.5, 1.0, 2.0, 5.0]  # % away from mid
        cumulative_bids = []
        cumulative_asks = []
        
        for depth_pct in depths:
            bid_threshold = mid_price * (1 - depth_pct / 100)
            ask_threshold = mid_price * (1 + depth_pct / 100)
            
            bid_depth = sum(v for p, v in zip(bid_prices, bid_volumes) if p >= bid_threshold)
            ask_depth = sum(v for p, v in zip(ask_prices, ask_volumes) if p <= ask_threshold)
            
            cumulative_bids.append(bid_depth)
            cumulative_asks.append(ask_depth)
        
        # Determine depth profile shape
        total_depth = sum(cumulative_bids) + sum(cumulative_asks)
        near_depth = cumulative_bids[0] + cumulative_asks[0]  # 0.5% depth
        far_depth = cumulative_bids[-1] + cumulative_asks[-1]  # 5% depth
        
        if total_depth == 0:
            shape = 'thin'
            liquidity_score = 0
        elif near_depth / total_depth > 0.5:
            shape = 'concentrated'  # Most liquidity near mid
            liquidity_score = 70
        elif far_depth / total_depth > 0.7:
            shape = 'distributed'  # Liquidity spread out
            liquidity_score = 50
        else:
            shape = 'balanced'
            liquidity_score = 60
        
        return {
            'shape': shape,
            'liquidity_score': liquidity_score,
            'cumulative_bids': cumulative_bids,
            'cumulative_asks': cumulative_asks,
            'depth_levels_pct': depths
        }
    
    def _generate_signal(self, spread: Dict, imbalance: Dict, walls: Dict, depth: Dict) -> Dict[str, Any]:
        """Generate trading signal from order book analysis"""
        score = 50  # Neutral starting point
        factors = []
        
        # Spread factor
        if spread['quality'] in ['excellent', 'good']:
            score += 5
            factors.append('good_spread')
        elif spread['quality'] in ['poor', 'very_poor']:
            score -= 10
            factors.append('poor_spread')
        
        # Imbalance factor
        if imbalance['pressure'] == 'strong_buy':
            score += 15
            factors.append('strong_buy_pressure')
        elif imbalance['pressure'] == 'buy':
            score += 8
            factors.append('buy_pressure')
        elif imbalance['pressure'] == 'strong_sell':
            score -= 15
            factors.append('strong_sell_pressure')
        elif imbalance['pressure'] == 'sell':
            score -= 8
            factors.append('sell_pressure')
        
        # Wall factor
        if walls['has_major_support'] and not walls['has_major_resistance']:
            score += 10
            factors.append('support_wall_present')
        elif walls['has_major_resistance'] and not walls['has_major_support']:
            score -= 10
            factors.append('resistance_wall_present')
        
        # Liquidity factor
        if depth['liquidity_score'] >= 60:
            score += 5
            factors.append('good_liquidity')
        elif depth['liquidity_score'] < 30:
            score -= 10
            factors.append('low_liquidity')
        
        # Determine signal
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
            'factors': factors
        }
    
    async def _get_order_book(self, symbol: str) -> Optional[Dict]:
        """Get order book from cache or generate simulated data"""
        cache_key = f"ob_{symbol}"
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.utcnow().timestamp() - cached['time'] < self.cache_ttl:
                return cached['data']
        
        # Generate simulated order book for demonstration
        # In production, this would fetch from Kraken API
        order_book = self._generate_simulated_order_book(symbol)
        
        self.cache[cache_key] = {
            'data': order_book,
            'time': datetime.utcnow().timestamp()
        }
        
        return order_book
    
    def _generate_simulated_order_book(self, symbol: str) -> Dict:
        """Generate realistic simulated order book"""
        np.random.seed(hash(symbol + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # Base prices for common symbols
        base_prices = {
            'BTC': 43000, 'ETH': 2300, 'SOL': 95, 'ADA': 0.45,
            'DOT': 6.5, 'MATIC': 0.85, 'LINK': 14, 'AVAX': 35
        }
        
        base = base_prices.get(symbol.upper().replace('USD', '').replace('USDT', ''), 100)
        spread_pct = np.random.uniform(0.01, 0.15)
        
        mid_price = base * (1 + np.random.uniform(-0.02, 0.02))
        
        bids = []
        asks = []
        
        # Generate bid levels
        for i in range(self.depth_levels):
            price = mid_price * (1 - spread_pct/2 - i * 0.001)
            # Volume follows power law distribution
            volume = np.random.pareto(1.5) * 10 + np.random.uniform(1, 5)
            bids.append([round(price, 6), round(volume, 4)])
        
        # Generate ask levels
        for i in range(self.depth_levels):
            price = mid_price * (1 + spread_pct/2 + i * 0.001)
            volume = np.random.pareto(1.5) * 10 + np.random.uniform(1, 5)
            asks.append([round(price, 6), round(volume, 4)])
        
        # Randomly add whale walls
        if np.random.random() > 0.7:
            wall_idx = np.random.randint(3, 10)
            bids[wall_idx][1] *= 5  # Support wall
        
        if np.random.random() > 0.7:
            wall_idx = np.random.randint(3, 10)
            asks[wall_idx][1] *= 5  # Resistance wall
        
        return {'bids': bids, 'asks': asks}
    
    async def _store_analysis(self, analysis: Dict):
        """Store analysis in database"""
        try:
            await self.db.order_book_analysis.insert_one({
                **analysis,
                'created_at': datetime.utcnow()
            })
        except Exception as e:
            logger.warning(f"Failed to store order book analysis: {e}")
    
    def _empty_analysis(self, symbol: str) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'spread': {'spread_pct': 0, 'quality': 'unknown'},
            'imbalance': {'ratio': 0.5, 'pressure': 'neutral', 'strength': 0},
            'walls': {'support_walls': [], 'resistance_walls': []},
            'depth_profile': {'shape': 'unknown', 'liquidity_score': 0},
            'signal': {'signal': 'neutral', 'score': 50, 'confidence': 0, 'factors': []}
        }
    
    async def get_historical_imbalance(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get historical imbalance data for trend analysis"""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            cursor = self.db.order_book_analysis.find(
                {'symbol': symbol, 'created_at': {'$gte': cutoff}},
                {'_id': 0, 'timestamp': 1, 'imbalance': 1, 'signal': 1}
            ).sort('created_at', -1).limit(100)
            
            return await cursor.to_list(length=100)
        except Exception as e:
            logger.error(f"Failed to get historical imbalance: {e}")
            return []


# Singleton instance
_order_book_analyzer = None

def get_order_book_analyzer(db: AsyncIOMotorDatabase = None) -> OrderBookAnalyzer:
    global _order_book_analyzer
    if _order_book_analyzer is None and db is not None:
        _order_book_analyzer = OrderBookAnalyzer(db)
    return _order_book_analyzer
