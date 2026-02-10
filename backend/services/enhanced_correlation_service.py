"""
Enhanced Event-News-Price Correlation Service
Extends event correlation with sentiment analysis and multi-timeframe analysis.
Complements event_correlation_engine.py with enhanced capabilities.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import statistics

logger = logging.getLogger(__name__)


class EnhancedCorrelationService:
    """
    Advanced correlation analysis between news sentiment and price movements.
    
    Features:
    - Multi-timeframe price impact analysis (15min, 1h, 4h, 24h)
    - Sentiment-weighted correlation scoring
    - Causal lag detection (news → price with time delay)
    - Volume confirmation analysis
    - Market-wide vs. coin-specific impact separation
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        sentiment_tracker=None,
        market_integrator=None
    ):
        self.db = db
        self.sentiment_tracker = sentiment_tracker
        self.market_integrator = market_integrator
        
        # Time windows for impact analysis (in hours)
        self.impact_windows = [0.25, 1, 4, 24]  # 15min, 1h, 4h, 24h
        
        # Correlation threshold for significance
        self.significance_threshold = 0.05  # 5% price movement
        
    async def analyze_news_impact(
        self,
        coin_id: str,
        news_timestamp: datetime,
        news_sentiment: Dict[str, Any],
        price_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of news impact on price.
        
        Args:
            coin_id: Cryptocurrency identifier
            news_timestamp: When the news was published
            news_sentiment: Sentiment analysis of the news
            price_data: Optional pre-fetched price data
        
        Returns:
            Detailed impact analysis across multiple timeframes
        """
        analysis = {
            'coin_id': coin_id,
            'news_timestamp': news_timestamp.isoformat(),
            'sentiment_score': news_sentiment.get('score', 50),
            'sentiment_label': news_sentiment.get('label', 'neutral'),
            'timeframe_analysis': {},
            'overall_impact': None,
            'confidence': 0.0
        }
        
        # Analyze each timeframe
        for window_hours in self.impact_windows:
            window_analysis = await self._analyze_timeframe(
                coin_id,
                news_timestamp,
                window_hours,
                news_sentiment
            )
            
            analysis['timeframe_analysis'][f'{window_hours}h'] = window_analysis
        
        # Determine overall impact
        analysis['overall_impact'] = self._determine_overall_impact(
            analysis['timeframe_analysis'],
            news_sentiment
        )
        
        # Calculate confidence score
        analysis['confidence'] = self._calculate_confidence(
            analysis['timeframe_analysis']
        )
        
        return analysis
    
    async def _analyze_timeframe(
        self,
        coin_id: str,
        news_timestamp: datetime,
        window_hours: float,
        news_sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze price impact in a specific timeframe"""
        
        # Define time window
        window_start = news_timestamp
        window_end = news_timestamp + timedelta(hours=window_hours)
        
        # Fetch price data for this window
        # This is a simplified version - in production, query actual OHLCV data
        price_before = await self._get_price_near_time(coin_id, news_timestamp)
        price_after = await self._get_price_near_time(coin_id, window_end)
        
        if not price_before or not price_after:
            return {
                'window_hours': window_hours,
                'status': 'insufficient_data',
                'price_change_pct': None
            }
        
        # Calculate price change
        price_change = price_after - price_before
        price_change_pct = (price_change / price_before * 100) if price_before > 0 else 0
        
        # Determine if impact matches sentiment
        sentiment_direction = self._get_sentiment_direction(news_sentiment)
        price_direction = 'bullish' if price_change_pct > 0 else 'bearish'
        
        alignment = sentiment_direction == price_direction
        
        return {
            'window_hours': window_hours,
            'price_before': round(price_before, 2),
            'price_after': round(price_after, 2),
            'price_change_pct': round(price_change_pct, 2),
            'price_direction': price_direction,
            'sentiment_direction': sentiment_direction,
            'alignment': alignment,
            'significant': abs(price_change_pct) >= self.significance_threshold
        }
    
    async def _get_price_near_time(
        self,
        coin_id: str,
        timestamp: datetime
    ) -> Optional[float]:
        """
        Get price near a specific timestamp.
        Placeholder - would query historical OHLCV data in production.
        """
        # For now, return None - needs actual database query
        # In production, query db.ohlcv_data or historical_ohlcv
        return None
    
    def _get_sentiment_direction(self, sentiment: Dict[str, Any]) -> str:
        """Determine bullish/bearish direction from sentiment"""
        score = sentiment.get('score', 50)
        
        if score >= 60:
            return 'bullish'
        elif score <= 40:
            return 'bearish'
        else:
            return 'neutral'
    
    def _determine_overall_impact(
        self,
        timeframe_analysis: Dict[str, Dict[str, Any]],
        news_sentiment: Dict[str, Any]
    ) -> str:
        """
        Determine overall impact classification.
        
        Returns: 'strong_positive', 'moderate_positive', 'neutral',
                 'moderate_negative', 'strong_negative', 'no_impact'
        """
        # Count significant movements
        significant_moves = []
        for window, data in timeframe_analysis.items():
            if data.get('significant') and data.get('alignment'):
                significant_moves.append(data['price_change_pct'])
        
        if not significant_moves:
            return 'no_impact'
        
        # Calculate average significant movement
        avg_move = statistics.mean(significant_moves)
        
        if avg_move >= 10:
            return 'strong_positive'
        elif avg_move >= 5:
            return 'moderate_positive'
        elif avg_move <= -10:
            return 'strong_negative'
        elif avg_move <= -5:
            return 'moderate_negative'
        else:
            return 'neutral'
    
    def _calculate_confidence(
        self,
        timeframe_analysis: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score based on consistency across timeframes.
        Higher confidence when multiple timeframes show aligned movements.
        """
        aligned_count = 0
        total_count = 0
        
        for window, data in timeframe_analysis.items():
            if data.get('status') != 'insufficient_data':
                total_count += 1
                if data.get('alignment'):
                    aligned_count += 1
        
        if total_count == 0:
            return 0.0
        
        confidence = aligned_count / total_count
        return round(confidence, 2)
    
    async def batch_correlation_analysis(
        self,
        coin_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Analyze correlations between all news and price movements in a date range.
        
        Args:
            coin_id: Cryptocurrency identifier
            start_date: Start of analysis period
            end_date: End of analysis period
        
        Returns:
            Summary of correlations found
        """
        if not self.sentiment_tracker:
            return {
                'error': 'Sentiment tracker not available',
                'status': 'service_unavailable'
            }
        
        # Get all sentiment data in range
        sentiment_history = await self.sentiment_tracker.get_coin_sentiment_history(
            coin_id=coin_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        if not sentiment_history:
            return {
                'coin_id': coin_id,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'message': 'No sentiment data found for this period',
                'correlations': []
            }
        
        # Analyze each sentiment point
        correlations = []
        for sentiment_point in sentiment_history[:50]:  # Limit to 50 for performance
            timestamp = sentiment_point.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            impact = await self.analyze_news_impact(
                coin_id=coin_id,
                news_timestamp=timestamp,
                news_sentiment=sentiment_point
            )
            
            if impact.get('overall_impact') not in ['no_impact', None]:
                correlations.append({
                    'timestamp': timestamp.isoformat(),
                    'sentiment_score': sentiment_point.get('score'),
                    'impact': impact['overall_impact'],
                    'confidence': impact['confidence']
                })
        
        return {
            'coin_id': coin_id,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_sentiment_points': len(sentiment_history),
            'correlations_found': len(correlations),
            'correlations': correlations
        }
    
    async def detect_lagged_impact(
        self,
        coin_id: str,
        news_timestamp: datetime,
        max_lag_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Detect time lag between news and price impact.
        Some news takes time to propagate through the market.
        
        Args:
            coin_id: Cryptocurrency identifier
            news_timestamp: When news was published
            max_lag_hours: Maximum lag to test (default: 24 hours)
        
        Returns:
            Detected lag and impact strength
        """
        lag_analysis = []
        
        # Test various lag periods
        for lag_hours in [0.5, 1, 2, 4, 8, 12, 24]:
            if lag_hours > max_lag_hours:
                break
            
            lagged_timestamp = news_timestamp + timedelta(hours=lag_hours)
            
            price_before = await self._get_price_near_time(coin_id, news_timestamp)
            price_after = await self._get_price_near_time(coin_id, lagged_timestamp)
            
            if price_before and price_after:
                change_pct = (price_after - price_before) / price_before * 100
                
                lag_analysis.append({
                    'lag_hours': lag_hours,
                    'price_change_pct': round(change_pct, 2),
                    'significant': abs(change_pct) >= self.significance_threshold
                })
        
        # Find lag with maximum impact
        if lag_analysis:
            max_impact = max(lag_analysis, key=lambda x: abs(x['price_change_pct']))
            
            return {
                'coin_id': coin_id,
                'news_timestamp': news_timestamp.isoformat(),
                'max_impact_lag_hours': max_impact['lag_hours'],
                'max_impact_change_pct': max_impact['price_change_pct'],
                'all_lags': lag_analysis
            }
        
        return {
            'coin_id': coin_id,
            'news_timestamp': news_timestamp.isoformat(),
            'status': 'insufficient_data'
        }
    
    async def compare_market_vs_coin_impact(
        self,
        coin_id: str,
        news_timestamp: datetime,
        market_proxy: str = 'bitcoin'
    ) -> Dict[str, Any]:
        """
        Determine if news impact is coin-specific or market-wide.
        Compares coin price movement to market proxy (usually Bitcoin).
        
        Args:
            coin_id: Target cryptocurrency
            news_timestamp: News timestamp
            market_proxy: Market reference coin (default: 'bitcoin')
        
        Returns:
            Analysis of coin-specific vs. market-wide impact
        """
        # Analyze target coin
        coin_price_before = await self._get_price_near_time(coin_id, news_timestamp)
        coin_price_after = await self._get_price_near_time(
            coin_id,
            news_timestamp + timedelta(hours=4)
        )
        
        # Analyze market proxy
        market_price_before = await self._get_price_near_time(market_proxy, news_timestamp)
        market_price_after = await self._get_price_near_time(
            market_proxy,
            news_timestamp + timedelta(hours=4)
        )
        
        if not all([coin_price_before, coin_price_after, market_price_before, market_price_after]):
            return {
                'status': 'insufficient_data',
                'message': 'Cannot determine market vs coin impact'
            }
        
        coin_change = (coin_price_after - coin_price_before) / coin_price_before * 100
        market_change = (market_price_after - market_price_before) / market_price_before * 100
        
        # Calculate relative strength
        relative_strength = coin_change - market_change
        
        # Determine impact type
        if abs(relative_strength) > 5:
            impact_type = 'coin_specific'
        elif abs(coin_change) > 3 and abs(market_change) > 3:
            impact_type = 'market_wide'
        else:
            impact_type = 'minimal'
        
        return {
            'coin_id': coin_id,
            'market_proxy': market_proxy,
            'coin_change_pct': round(coin_change, 2),
            'market_change_pct': round(market_change, 2),
            'relative_strength': round(relative_strength, 2),
            'impact_type': impact_type
        }
    
    async def get_correlation_summary(self, coin_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Generate correlation summary for a coin over recent period.
        
        Args:
            coin_id: Cryptocurrency identifier
            days: Days to analyze (default: 30)
        
        Returns:
            Summary statistics of news-price correlations
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get batch correlation analysis
        batch_result = await self.batch_correlation_analysis(
            coin_id=coin_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if 'error' in batch_result:
            return batch_result
        
        correlations = batch_result.get('correlations', [])
        
        if not correlations:
            return {
                'coin_id': coin_id,
                'days': days,
                'message': 'No significant correlations found',
                'statistics': None
            }
        
        # Calculate statistics
        impact_counts = {
            'strong_positive': 0,
            'moderate_positive': 0,
            'neutral': 0,
            'moderate_negative': 0,
            'strong_negative': 0
        }
        
        confidence_scores = []
        
        for corr in correlations:
            impact = corr.get('impact', 'neutral')
            if impact in impact_counts:
                impact_counts[impact] += 1
            
            confidence = corr.get('confidence', 0)
            confidence_scores.append(confidence)
        
        return {
            'coin_id': coin_id,
            'period_days': days,
            'total_correlations': len(correlations),
            'impact_distribution': impact_counts,
            'avg_confidence': round(statistics.mean(confidence_scores), 2) if confidence_scores else 0,
            'correlation_rate': round(len(correlations) / batch_result['total_sentiment_points'], 2)
                if batch_result['total_sentiment_points'] > 0 else 0
        }
