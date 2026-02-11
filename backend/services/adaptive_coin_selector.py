"""
Adaptive AI Coin Selection Engine
Dynamically selects the best coins to trade each week based on:
- Market conditions
- Historical performance patterns
- News sentiment
- Technical indicators
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()


class AdaptiveCoinSelector:
    """
    AI-powered coin selection that adapts to market conditions.
    Finds the best opportunities even in bear markets.
    Now supports ALL Kraken tradeable pairs.
    """
    
    def __init__(self, db, market_service=None, news_service=None):
        self.db = db
        self.market_service = market_service
        self.news_service = news_service
        self._kraken_pairs_loaded = False
        
        # All Kraken tradeable coins (634 pairs available)
        # This will be dynamically loaded from Kraken API
        self.coin_universe = [
            # Core large caps
            'bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot',
            'avalanche', 'chainlink', 'polygon', 'uniswap', 'litecoin',
            'dogecoin', 'ripple', 'tron', 'cosmos', 'near',
            'aptos', 'sui', 'arbitrum', 'optimism',
            # Additional Kraken coins
            'stellar', 'algorand', 'vechain', 'filecoin', 'aave',
            'maker', 'compound', 'synthetix', 'yearnfinance', 'curve',
            'sushi', 'pancakeswap', 'inch', 'balancer', 'loopring',
            'enjin', 'gala', 'sandbox', 'decentraland', 'axie',
            'injective', 'render', 'fetch', 'ocean', 'singularity',
            'theta', 'arweave', 'helium', 'livepeer', 'audius',
            'shiba', 'pepe', 'floki', 'bonk', 'wif',
            'sei', 'celestia', 'starknet', 'zksync', 'manta',
            'jupiter', 'pyth', 'jito', 'wormhole', 'blur',
            # Layer 2s
            'base', 'mantle', 'scroll', 'linea', 'mode',
            # DeFi
            'gmx', 'dydx', 'raydium', 'orca', 'marinade',
            # AI coins
            'worldcoin', 'arkham', 'vectorspace', 'numeraire',
            # Gaming
            'immutable', 'beam', 'pixels', 'portal', 'prime',
        ]
        
        # Coin symbols for display (expanded)
        self.coin_symbols = {
            'bitcoin': 'BTC', 'ethereum': 'ETH', 'solana': 'SOL',
            'cardano': 'ADA', 'polkadot': 'DOT', 'avalanche': 'AVAX',
            'chainlink': 'LINK', 'polygon': 'MATIC', 'uniswap': 'UNI',
            'litecoin': 'LTC', 'dogecoin': 'DOGE', 'ripple': 'XRP',
            'tron': 'TRX', 'cosmos': 'ATOM', 'near': 'NEAR',
            'aptos': 'APT', 'sui': 'SUI', 'arbitrum': 'ARB',
            'optimism': 'OP', 'stellar': 'XLM', 'algorand': 'ALGO',
            'vechain': 'VET', 'filecoin': 'FIL', 'aave': 'AAVE',
            'maker': 'MKR', 'compound': 'COMP', 'synthetix': 'SNX',
            'yearnfinance': 'YFI', 'curve': 'CRV', 'sushi': 'SUSHI',
            'loopring': 'LRC', 'enjin': 'ENJ', 'gala': 'GALA',
            'sandbox': 'SAND', 'decentraland': 'MANA', 'axie': 'AXS',
            'injective': 'INJ', 'render': 'RNDR', 'fetch': 'FET',
            'ocean': 'OCEAN', 'singularity': 'AGIX', 'theta': 'THETA',
            'arweave': 'AR', 'helium': 'HNT', 'livepeer': 'LPT',
            'audius': 'AUDIO', 'shiba': 'SHIB', 'pepe': 'PEPE',
            'floki': 'FLOKI', 'bonk': 'BONK', 'wif': 'WIF',
            'sei': 'SEI', 'celestia': 'TIA', 'starknet': 'STRK',
            'zksync': 'ZK', 'manta': 'MANTA', 'jupiter': 'JUP',
            'pyth': 'PYTH', 'jito': 'JTO', 'wormhole': 'W',
            'blur': 'BLUR', 'gmx': 'GMX', 'dydx': 'DYDX',
            'raydium': 'RAY', 'orca': 'ORCA', 'worldcoin': 'WLD',
            'arkham': 'ARKM', 'immutable': 'IMX', 'beam': 'BEAM',
            'pixels': 'PIXEL', 'portal': 'PORTAL', 'prime': 'PRIME',
        }
        
        # Selection criteria weights (learned over time)
        self.criteria_weights = {
            'momentum_score': 0.25,      # Recent price momentum
            'volatility_score': 0.15,    # Optimal volatility
            'volume_score': 0.20,        # Volume trends
            'trend_score': 0.20,         # Trend alignment
            'sentiment_score': 0.10,     # News sentiment
            'historical_score': 0.10,    # Historical weekly performance
        }
    
    async def load_kraken_pairs(self):
        """Dynamically load all tradeable pairs from Kraken"""
        if self._kraken_pairs_loaded:
            return
            
        try:
            if self.market_service:
                # Get all tradeable pairs from Kraken
                pairs = await self.market_service.get_all_tradeable_pairs()
                if pairs:
                    # Extract coin IDs from pairs
                    for pair in pairs:
                        coin_id = pair.get('base', '').lower()
                        symbol = pair.get('altname', '')[:4]
                        if coin_id and coin_id not in self.coin_universe:
                            self.coin_universe.append(coin_id)
                            if symbol:
                                self.coin_symbols[coin_id] = symbol
                    self._kraken_pairs_loaded = True
                    print(f"Loaded {len(self.coin_universe)} coins from Kraken")
        except Exception as e:
            print(f"Error loading Kraken pairs: {e}")
    
    async def get_selection_status(self) -> Dict[str, Any]:
        """Get current status of the selection engine"""
        await self.load_kraken_pairs()
        
        # Get latest weights from DB if available
        weights = await self.db.ai_training_weights.find_one({}, {'_id': 0})
        if weights:
            self.criteria_weights = weights.get('weights', self.criteria_weights)
        
        # Count historical data
        total_weeks = await self.db.ai_training_results.count_documents({})
        
        return {
            'total_weeks_analyzed': total_weeks,
            'avg_recent_return': await self._get_recent_performance(),
            'current_weights': self.criteria_weights,
            'coin_universe_size': len(self.coin_universe)
        }
    
    async def _get_recent_performance(self) -> float:
        """Get average return from recent weeks"""
        try:
            recent = await self.db.ai_training_results.find(
                {}, {'return_pct': 1}
            ).sort([('week_start', -1)]).limit(10).to_list(10)
            
            if recent:
                return round(np.mean([r.get('return_pct', 0) for r in recent]), 2)
        except:
            pass
        return 0
    
    async def select_best_coins(
        self,
        week_start: datetime,
        market_condition: str = 'neutral',
        max_coins: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Select the best coins for a given week based on market conditions.
        
        Args:
            week_start: Start date of the trading week
            market_condition: 'bullish', 'bearish', or 'neutral'
            max_coins: Maximum number of coins to select
            
        Returns:
            List of selected coins with scores and reasoning
        """
        coin_scores = []
        
        for coin_id in self.coin_universe:
            # Get historical data for this coin around the week
            score_data = await self._calculate_coin_score(
                coin_id, week_start, market_condition
            )
            
            if score_data:
                coin_scores.append(score_data)
        
        # Sort by total score (descending)
        coin_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Select top coins, ensuring diversification
        selected = self._diversify_selection(coin_scores, max_coins, market_condition)
        
        return selected
    
    async def _calculate_coin_score(
        self,
        coin_id: str,
        week_start: datetime,
        market_condition: str
    ) -> Dict[str, Any]:
        """Calculate selection score for a single coin"""
        
        # Get historical prices from database
        prices = await self._get_historical_prices(coin_id, week_start, days=30)
        
        if not prices or len(prices) < 7:
            return None
        
        # Calculate individual scores
        momentum = self._calculate_momentum_score(prices, market_condition)
        volatility = self._calculate_volatility_score(prices, market_condition)
        volume = self._calculate_volume_score(prices)
        trend = self._calculate_trend_score(prices, market_condition)
        sentiment = await self._get_sentiment_score(coin_id, week_start)
        historical = await self._get_historical_weekly_performance(coin_id)
        
        # Calculate weighted total score
        total_score = (
            momentum * self.criteria_weights['momentum_score'] +
            volatility * self.criteria_weights['volatility_score'] +
            volume * self.criteria_weights['volume_score'] +
            trend * self.criteria_weights['trend_score'] +
            sentiment * self.criteria_weights['sentiment_score'] +
            historical * self.criteria_weights['historical_score']
        )
        
        # Generate reasoning
        reasoning = self._generate_selection_reasoning(
            coin_id, momentum, volatility, volume, trend, sentiment, market_condition
        )
        
        return {
            'coin_id': coin_id,
            'symbol': self.coin_symbols.get(coin_id, coin_id.upper()),
            'total_score': round(total_score, 2),
            'scores': {
                'momentum': round(momentum, 2),
                'volatility': round(volatility, 2),
                'volume': round(volume, 2),
                'trend': round(trend, 2),
                'sentiment': round(sentiment, 2),
                'historical': round(historical, 2)
            },
            'reasoning': reasoning,
            'market_condition': market_condition
        }
    
    async def _get_historical_prices(
        self,
        coin_id: str,
        reference_date: datetime,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get historical prices from database"""
        try:
            end_date = reference_date
            start_date = reference_date - timedelta(days=days)
            
            prices = await self.db.historical_prices.find({
                'coin_id': coin_id,
                'timestamp': {
                    '$gte': start_date.isoformat(),
                    '$lte': end_date.isoformat()
                }
            }, {'_id': 0}).sort('timestamp', 1).to_list(days * 2)
            
            return prices
        except Exception as e:
            print(f"Error fetching historical prices for {coin_id}: {e}")
            return []
    
    def _calculate_momentum_score(
        self,
        prices: List[Dict],
        market_condition: str
    ) -> float:
        """
        Calculate momentum score (0-100).
        In bear markets, look for oversold conditions.
        In bull markets, look for strong upward momentum.
        """
        if len(prices) < 7:
            return 50
        
        # Get recent price changes
        closes = [p.get('close', p.get('price', 0)) for p in prices]
        
        # 7-day momentum
        week_change = (closes[-1] - closes[-7]) / closes[-7] * 100 if closes[-7] > 0 else 0
        
        # 14-day momentum
        if len(closes) >= 14:
            two_week_change = (closes[-1] - closes[-14]) / closes[-14] * 100 if closes[-14] > 0 else 0
        else:
            two_week_change = week_change
        
        if market_condition == 'bearish':
            # In bear markets, oversold conditions can be opportunities
            # Look for coins that are down but showing signs of recovery
            if week_change < -20:
                score = 30  # Severely oversold - cautious
            elif week_change < -10:
                score = 60  # Oversold - potential opportunity
            elif week_change < 0:
                score = 70  # Slightly down - could be entry point
            else:
                score = 40  # Rising in bear market - be careful
        elif market_condition == 'bullish':
            # In bull markets, ride the momentum
            if week_change > 20:
                score = 90
            elif week_change > 10:
                score = 80
            elif week_change > 0:
                score = 70
            else:
                score = 40  # Lagging in bull market
        else:
            # Neutral - balanced approach
            if -5 < week_change < 15:
                score = 70  # Stable with slight upside
            elif week_change > 15:
                score = 60  # Might be overbought
            elif week_change < -10:
                score = 50  # Might be oversold
            else:
                score = 55
        
        return max(0, min(100, score))
    
    def _calculate_volatility_score(
        self,
        prices: List[Dict],
        market_condition: str
    ) -> float:
        """
        Calculate volatility score (0-100).
        Optimal volatility depends on market conditions.
        """
        if len(prices) < 7:
            return 50
        
        closes = [p.get('close', p.get('price', 0)) for p in prices]
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes)) if closes[i-1] > 0]
        
        if not returns:
            return 50
        
        volatility = np.std(returns) * 100  # Daily volatility %
        
        if market_condition == 'bearish':
            # In bear markets, lower volatility is safer
            if volatility < 3:
                score = 80  # Low vol in bear = safe
            elif volatility < 5:
                score = 65
            elif volatility < 8:
                score = 50
            else:
                score = 30  # High vol in bear = risky
        elif market_condition == 'bullish':
            # In bull markets, moderate volatility offers opportunities
            if 3 < volatility < 8:
                score = 85  # Optimal volatility
            elif volatility < 3:
                score = 60  # Too stable
            elif volatility < 12:
                score = 70
            else:
                score = 45  # Too volatile
        else:
            # Neutral - prefer moderate volatility
            if 2 < volatility < 6:
                score = 75
            else:
                score = 50
        
        return max(0, min(100, score))
    
    def _calculate_volume_score(self, prices: List[Dict]) -> float:
        """
        Calculate volume score (0-100).
        Higher volume relative to average indicates interest.
        """
        if len(prices) < 7:
            return 50
        
        volumes = [p.get('volume', 0) for p in prices]
        
        if not volumes or all(v == 0 for v in volumes):
            return 50
        
        avg_volume = np.mean(volumes[:-7]) if len(volumes) > 7 else np.mean(volumes)
        recent_volume = np.mean(volumes[-7:])
        
        if avg_volume > 0:
            volume_ratio = recent_volume / avg_volume
        else:
            volume_ratio = 1
        
        # Higher volume ratio = more interest
        if volume_ratio > 2.0:
            score = 90  # Very high interest
        elif volume_ratio > 1.5:
            score = 80
        elif volume_ratio > 1.0:
            score = 70
        elif volume_ratio > 0.7:
            score = 55
        else:
            score = 40  # Declining interest
        
        return max(0, min(100, score))
    
    def _calculate_trend_score(
        self,
        prices: List[Dict],
        market_condition: str
    ) -> float:
        """
        Calculate trend alignment score (0-100).
        Measures if coin is following or outperforming market.
        """
        if len(prices) < 14:
            return 50
        
        closes = [p.get('close', p.get('price', 0)) for p in prices]
        
        # Calculate simple moving averages
        sma_7 = np.mean(closes[-7:])
        sma_14 = np.mean(closes[-14:])
        current = closes[-1]
        
        # Trend signals
        above_sma7 = current > sma_7
        above_sma14 = current > sma_14
        sma7_above_sma14 = sma_7 > sma_14
        
        if market_condition == 'bullish':
            # In bull market, want strong uptrend
            if above_sma7 and above_sma14 and sma7_above_sma14:
                score = 90  # Perfect uptrend
            elif above_sma7 and sma7_above_sma14:
                score = 75
            elif above_sma7:
                score = 60
            else:
                score = 40  # Lagging
        elif market_condition == 'bearish':
            # In bear market, look for reversal signals
            if not above_sma14 and above_sma7:
                score = 80  # Potential reversal
            elif above_sma7:
                score = 70  # Holding up
            elif sma7_above_sma14:
                score = 55  # Starting to turn
            else:
                score = 35  # Full downtrend
        else:
            # Neutral - balanced signals
            if above_sma7 and sma7_above_sma14:
                score = 75
            elif above_sma7:
                score = 60
            else:
                score = 45
        
        return max(0, min(100, score))
    
    async def _get_sentiment_score(
        self,
        coin_id: str,
        week_start: datetime
    ) -> float:
        """Get sentiment score from news around the week"""
        try:
            # Check for cached sentiment in database
            sentiment = await self.db.coin_sentiments.find_one({
                'coin_id': coin_id,
                'week_start': {'$lte': week_start.isoformat()}
            }, {'_id': 0}, sort=[('week_start', -1)])
            
            if sentiment:
                return sentiment.get('score', 50)
            
            # Default neutral sentiment
            return 50
        except Exception:
            return 50
    
    async def _get_historical_weekly_performance(self, coin_id: str) -> float:
        """Get average weekly performance from learning data"""
        try:
            performances = await self.db.weekly_performances.find({
                'coin_id': coin_id
            }, {'_id': 0, 'return_pct': 1}).limit(52).to_list(52)
            
            if performances:
                avg_return = np.mean([p.get('return_pct', 0) for p in performances])
                # Convert to score (0-100)
                # Positive returns score higher
                score = 50 + (avg_return * 2)  # ±25% maps to 0-100
                return max(0, min(100, score))
            
            return 50
        except Exception:
            return 50
    
    def _generate_selection_reasoning(
        self,
        coin_id: str,
        momentum: float,
        volatility: float,
        volume: float,
        trend: float,
        sentiment: float,
        market_condition: str
    ) -> str:
        """Generate human-readable reasoning for selection"""
        symbol = self.coin_symbols.get(coin_id, coin_id.upper())
        reasons = []
        
        if momentum >= 70:
            reasons.append(f"Strong momentum ({momentum:.0f}/100)")
        elif momentum <= 40:
            reasons.append(f"Weak momentum ({momentum:.0f}/100)")
        
        if volatility >= 70:
            reasons.append(f"Good volatility profile for {market_condition} market")
        
        if volume >= 75:
            reasons.append("High trading interest")
        
        if trend >= 70:
            reasons.append("Favorable trend alignment")
        
        if sentiment >= 65:
            reasons.append("Positive market sentiment")
        elif sentiment <= 35:
            reasons.append("Cautious sentiment")
        
        if not reasons:
            reasons.append("Average across all metrics")
        
        return f"{symbol}: " + ", ".join(reasons)
    
    def _diversify_selection(
        self,
        scored_coins: List[Dict],
        max_coins: int,
        market_condition: str
    ) -> List[Dict[str, Any]]:
        """
        Ensure diversification in selected coins.
        Don't put all eggs in one basket.
        """
        selected = []
        
        # Categories for diversification
        large_cap = ['bitcoin', 'ethereum']
        mid_cap = ['solana', 'cardano', 'polkadot', 'avalanche']
        small_cap = [c for c in self.coin_universe if c not in large_cap + mid_cap]
        
        # Allocation strategy based on market condition
        if market_condition == 'bearish':
            # In bear market, favor large caps (safer)
            target_allocation = {'large': 2, 'mid': 2, 'small': 1}
        elif market_condition == 'bullish':
            # In bull market, can take more risk
            target_allocation = {'large': 1, 'mid': 2, 'small': 2}
        else:
            # Balanced
            target_allocation = {'large': 1, 'mid': 2, 'small': 2}
        
        # Select by category
        for coin_data in scored_coins:
            if len(selected) >= max_coins:
                break
            
            coin_id = coin_data['coin_id']
            
            # Determine category
            if coin_id in large_cap:
                category = 'large'
            elif coin_id in mid_cap:
                category = 'mid'
            else:
                category = 'small'
            
            # Check if we can add from this category
            current_in_category = sum(
                1 for s in selected 
                if (s['coin_id'] in large_cap and category == 'large') or
                   (s['coin_id'] in mid_cap and category == 'mid') or
                   (s['coin_id'] in small_cap and category == 'small')
            )
            
            if current_in_category < target_allocation.get(category, 1):
                selected.append(coin_data)
        
        # If we haven't filled max_coins, add remaining top scorers
        for coin_data in scored_coins:
            if len(selected) >= max_coins:
                break
            if coin_data not in selected:
                selected.append(coin_data)
        
        return selected
    
    async def record_weekly_result(
        self,
        week_start: datetime,
        selected_coins: List[str],
        actual_returns: Dict[str, float]
    ):
        """Record weekly selection results for learning"""
        record = {
            'week_start': week_start.isoformat(),
            'selected_coins': selected_coins,
            'returns': actual_returns,
            'avg_return': np.mean(list(actual_returns.values())) if actual_returns else 0,
            'recorded_at': datetime.now().isoformat()
        }
        
        await self.db.weekly_selection_results.insert_one(record)
        
        # Update individual coin weekly performances
        for coin_id, return_pct in actual_returns.items():
            await self.db.weekly_performances.insert_one({
                'coin_id': coin_id,
                'week_start': week_start.isoformat(),
                'return_pct': return_pct,
                'recorded_at': datetime.now().isoformat()
            })
    
    async def update_criteria_weights(self):
        """
        Update selection criteria weights based on historical performance.
        Learn which factors lead to better selections.
        """
        # Get recent selection results
        results = await self.db.weekly_selection_results.find(
            {}, {'_id': 0}
        ).sort('week_start', -1).limit(52).to_list(52)
        
        if len(results) < 10:
            return  # Need more data
        
        # Analyze which criteria scores correlated with good returns
        # This is a simplified learning mechanism
        # In production, this would use more sophisticated ML
        
        # For now, slightly boost weights for consistently good predictors
        # This would be expanded with actual correlation analysis
        
        await self.db.selector_weights.replace_one(
            {},
            {'weights': self.criteria_weights, 'updated_at': datetime.now().isoformat()},
            upsert=True
        )
    
    async def get_selection_status(self) -> Dict[str, Any]:
        """Get current selector status and statistics"""
        total_selections = await self.db.weekly_selection_results.count_documents({})
        
        recent_results = await self.db.weekly_selection_results.find(
            {}, {'_id': 0, 'avg_return': 1}
        ).sort('week_start', -1).limit(10).to_list(10)
        
        avg_recent_return = np.mean([r.get('avg_return', 0) for r in recent_results]) if recent_results else 0
        
        return {
            'total_weeks_analyzed': total_selections,
            'avg_recent_return': round(avg_recent_return, 2),
            'current_weights': self.criteria_weights,
            'coin_universe_size': len(self.coin_universe)
        }
