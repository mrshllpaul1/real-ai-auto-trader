"""
News-Market Correlation Analyzer
Correlates news sentiment with actual price movements to identify predictive signals.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np
import logging

logger = logging.getLogger(__name__)


class NewsMarketCorrelationAnalyzer:
    """
    Analyzes correlation between news sentiment and market price movements.
    Helps identify which news types and sentiments are actually predictive.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.news_collection = db.crypto_news
        self.ohlcv_collection = db.historical_ohlcv
        self.correlation_collection = db.news_market_correlations
        
        # Analysis parameters
        self.lag_periods = [1, 4, 24, 168]  # hours: 1h, 4h, 24h, 1week
        self.min_news_count = 5  # Minimum news items for analysis
    
    async def analyze_correlation(
        self,
        coin: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze correlation between news sentiment and price movements.
        
        Args:
            coin: Coin symbol (BTC, ETH, etc.)
            start_date: Start date for analysis (default: 30 days ago)
            end_date: End date for analysis (default: now)
            
        Returns:
            Dict with correlation metrics and analysis
        """
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        # Fetch news data
        news_data = await self._fetch_news_data(coin, start_date, end_date)
        if len(news_data) < self.min_news_count:
            return {
                "coin": coin,
                "error": f"Insufficient news data (found {len(news_data)}, need {self.min_news_count})"
            }
        
        # Fetch price data
        price_data = await self._fetch_price_data(coin, start_date, end_date)
        if not price_data:
            return {
                "coin": coin,
                "error": "No price data available"
            }
        
        # Calculate correlations for different lag periods
        correlations = {}
        for lag_hours in self.lag_periods:
            corr = await self._calculate_lagged_correlation(
                news_data, price_data, lag_hours
            )
            correlations[f"{lag_hours}h"] = corr
        
        # Identify significant correlations
        significant = self._identify_significant_correlations(correlations)
        
        # Generate insights
        insights = self._generate_insights(correlations, significant)
        
        # Store results
        result = {
            "coin": coin,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "news_count": len(news_data),
            "price_points": len(price_data),
            "correlations": correlations,
            "significant_lags": significant,
            "insights": insights,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in database
        await self._store_correlation_result(coin, result)
        
        return result
    
    async def _fetch_news_data(
        self,
        coin: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch news data for the coin in the date range"""
        try:
            query = {
                "coins": coin.upper(),
                "published_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            cursor = self.news_collection.find(query).sort("published_at", 1)
            news_items = await cursor.to_list(length=None)
            
            return news_items
        except Exception as e:
            logger.error(f"Error fetching news data: {e}")
            return []
    
    async def _fetch_price_data(
        self,
        coin: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch hourly price data for the coin"""
        try:
            query = {
                "symbol": coin.upper(),
                "interval": "hourly",
                "timestamp": {
                    "$gte": int(start_date.timestamp()),
                    "$lte": int(end_date.timestamp())
                }
            }
            
            cursor = self.ohlcv_collection.find(query).sort("timestamp", 1)
            price_data = await cursor.to_list(length=None)
            
            # If no hourly data, try daily and interpolate
            if not price_data:
                query["interval"] = "daily"
                cursor = self.ohlcv_collection.find(query).sort("timestamp", 1)
                daily_data = await cursor.to_list(length=None)
                
                if daily_data:
                    price_data = self._interpolate_to_hourly(daily_data)
            
            return price_data
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            return []
    
    def _interpolate_to_hourly(self, daily_data: List[Dict]) -> List[Dict]:
        """Convert daily data to approximate hourly data"""
        hourly_data = []
        
        for i in range(len(daily_data) - 1):
            start_candle = daily_data[i]
            end_candle = daily_data[i + 1]
            
            start_price = start_candle["close"]
            end_price = end_candle["open"]
            
            # Create 24 hourly candles
            for hour in range(24):
                # Linear interpolation
                progress = hour / 24.0
                interpolated_price = start_price + (end_price - start_price) * progress
                
                hourly_data.append({
                    "timestamp": start_candle["timestamp"] + (hour * 3600),
                    "close": interpolated_price,
                    "interpolated": True
                })
        
        return hourly_data
    
    async def _calculate_lagged_correlation(
        self,
        news_data: List[Dict],
        price_data: List[Dict],
        lag_hours: int
    ) -> Dict[str, Any]:
        """Calculate correlation between news sentiment and price change after lag period"""
        try:
            correlations = []
            
            for news_item in news_data:
                news_time = news_item.get("published_at")
                if not news_time:
                    continue
                
                sentiment = news_item.get("sentiment", {}).get("final", 0.0)
                
                # Find price at news time
                news_timestamp = int(news_time.timestamp())
                price_at_news = self._find_closest_price(price_data, news_timestamp)
                
                # Find price after lag period
                lag_timestamp = news_timestamp + (lag_hours * 3600)
                price_after_lag = self._find_closest_price(price_data, lag_timestamp)
                
                if price_at_news and price_after_lag:
                    # Calculate price change percentage
                    price_change = ((price_after_lag - price_at_news) / price_at_news) * 100
                    
                    correlations.append({
                        "sentiment": sentiment,
                        "price_change": price_change
                    })
            
            if len(correlations) < 3:
                return {
                    "correlation": 0.0,
                    "p_value": 1.0,
                    "sample_size": len(correlations),
                    "error": "Insufficient data points"
                }
            
            # Calculate Pearson correlation
            sentiments = [c["sentiment"] for c in correlations]
            price_changes = [c["price_change"] for c in correlations]
            
            correlation = np.corrcoef(sentiments, price_changes)[0, 1]
            
            # Simple significance test (t-test approximation)
            n = len(correlations)
            t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2)) if correlation != 1 else 0
            # Approximate p-value (simplified)
            p_value = 2 * (1 - self._t_cdf(abs(t_stat), n - 2))
            
            return {
                "correlation": round(float(correlation), 3) if not np.isnan(correlation) else 0.0,
                "p_value": round(float(p_value), 4) if not np.isnan(p_value) else 1.0,
                "sample_size": len(correlations),
                "avg_sentiment": round(float(np.mean(sentiments)), 3),
                "avg_price_change": round(float(np.mean(price_changes)), 3),
                "is_significant": p_value < 0.05 if not np.isnan(p_value) else False
            }
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return {
                "correlation": 0.0,
                "error": str(e)
            }
    
    def _find_closest_price(
        self,
        price_data: List[Dict],
        target_timestamp: int,
        max_tolerance: int = 7200  # 2 hours
    ) -> Optional[float]:
        """Find the closest price to target timestamp"""
        closest_price = None
        min_diff = float('inf')
        
        for candle in price_data:
            diff = abs(candle["timestamp"] - target_timestamp)
            if diff < min_diff and diff <= max_tolerance:
                min_diff = diff
                closest_price = candle.get("close", candle.get("price"))
        
        return closest_price
    
    def _t_cdf(self, t: float, df: int) -> float:
        """Approximate t-distribution CDF (simplified)"""
        # Very simplified approximation
        if df < 1:
            return 0.5
        
        # Normal approximation for large df
        if df > 30:
            return 0.5 * (1 + np.tanh(t / np.sqrt(2)))
        
        # Rough approximation for small df
        return 0.5 + 0.5 * np.tanh(t / (1 + df/10))
    
    def _identify_significant_correlations(
        self,
        correlations: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """Identify statistically significant correlations"""
        significant = []
        
        for lag_period, corr_data in correlations.items():
            if corr_data.get("is_significant", False):
                significant.append({
                    "lag_period": lag_period,
                    "correlation": corr_data.get("correlation", 0.0),
                    "p_value": corr_data.get("p_value", 1.0),
                    "sample_size": corr_data.get("sample_size", 0)
                })
        
        # Sort by absolute correlation strength
        significant.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return significant
    
    def _generate_insights(
        self,
        correlations: Dict[str, Dict],
        significant: List[Dict]
    ) -> List[str]:
        """Generate human-readable insights from correlation data"""
        insights = []
        
        if not significant:
            insights.append("No statistically significant correlations found between news sentiment and price movements.")
            return insights
        
        # Find strongest correlation
        strongest = max(significant, key=lambda x: abs(x["correlation"]))
        
        if strongest["correlation"] > 0.3:
            insights.append(
                f"Strong positive correlation ({strongest['correlation']:.2f}) found at {strongest['lag_period']} lag. "
                f"Positive news sentiment tends to predict price increases."
            )
        elif strongest["correlation"] < -0.3:
            insights.append(
                f"Strong negative correlation ({strongest['correlation']:.2f}) found at {strongest['lag_period']} lag. "
                f"Positive news sentiment tends to predict price decreases (contrarian signal)."
            )
        
        # Identify optimal prediction window
        positive_corrs = [s for s in significant if s["correlation"] > 0.2]
        if positive_corrs:
            best_window = positive_corrs[0]["lag_period"]
            insights.append(
                f"News sentiment is most predictive within {best_window} timeframe. "
                f"Consider using this window for trading signals."
            )
        
        # Sample size warnings
        small_samples = [s for s in significant if s["sample_size"] < 10]
        if small_samples:
            insights.append(
                "Warning: Some correlations are based on small sample sizes (<10 events). "
                "Results may not be reliable. Collect more data for better analysis."
            )
        
        return insights
    
    async def _store_correlation_result(self, coin: str, result: Dict[str, Any]):
        """Store correlation analysis result in database"""
        try:
            await self.correlation_collection.update_one(
                {
                    "coin": coin,
                    "period.start": result["period"]["start"],
                    "period.end": result["period"]["end"]
                },
                {"$set": result},
                upsert=True
            )
            logger.info(f"Stored correlation analysis for {coin}")
        except Exception as e:
            logger.error(f"Failed to store correlation result: {e}")
    
    async def get_correlation_history(
        self,
        coin: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get historical correlation analyses for a coin"""
        try:
            cursor = self.correlation_collection.find(
                {"coin": coin}
            ).sort("analyzed_at", -1).limit(limit)
            
            results = await cursor.to_list(length=limit)
            
            return results
        except Exception as e:
            logger.error(f"Error fetching correlation history: {e}")
            return []
    
    async def get_predictive_signals(
        self,
        coin: str,
        recent_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get current predictive signals based on recent news and historical correlations.
        
        Args:
            coin: Coin symbol
            recent_hours: Hours of recent news to analyze
            
        Returns:
            Dict with trading signals based on news-price correlations
        """
        try:
            # Get latest correlation analysis
            correlations = await self.get_correlation_history(coin, limit=1)
            if not correlations:
                return {
                    "coin": coin,
                    "signal": "neutral",
                    "confidence": 0.0,
                    "reason": "No historical correlation data available"
                }
            
            latest_corr = correlations[0]
            
            # Find the most predictive lag period
            significant = latest_corr.get("significant_lags", [])
            if not significant:
                return {
                    "coin": coin,
                    "signal": "neutral",
                    "confidence": 0.0,
                    "reason": "No significant correlations found"
                }
            
            best_lag = significant[0]
            best_correlation = best_lag["correlation"]
            
            # Get recent news sentiment
            from services.news_aggregator import get_news_aggregator
            news_agg = get_news_aggregator(self.db)
            
            start_time = datetime.now(timezone.utc) - timedelta(hours=recent_hours)
            sentiment_summary = await news_agg.get_sentiment_summary(coin, days=recent_hours // 24 or 1)
            
            if sentiment_summary.get("news_count", 0) == 0:
                return {
                    "coin": coin,
                    "signal": "neutral",
                    "confidence": 0.0,
                    "reason": "No recent news available"
                }
            
            recent_sentiment = sentiment_summary.get("score", 0.0)
            
            # Generate signal based on correlation and sentiment
            if best_correlation > 0.2:
                # Positive correlation: sentiment predicts same direction
                if recent_sentiment > 0.2:
                    signal = "bullish"
                    confidence = min(abs(best_correlation) * abs(recent_sentiment), 1.0)
                elif recent_sentiment < -0.2:
                    signal = "bearish"
                    confidence = min(abs(best_correlation) * abs(recent_sentiment), 1.0)
                else:
                    signal = "neutral"
                    confidence = 0.3
            elif best_correlation < -0.2:
                # Negative correlation: sentiment predicts opposite direction (contrarian)
                if recent_sentiment > 0.2:
                    signal = "bearish"
                    confidence = min(abs(best_correlation) * abs(recent_sentiment), 1.0)
                elif recent_sentiment < -0.2:
                    signal = "bullish"
                    confidence = min(abs(best_correlation) * abs(recent_sentiment), 1.0)
                else:
                    signal = "neutral"
                    confidence = 0.3
            else:
                signal = "neutral"
                confidence = 0.2
            
            return {
                "coin": coin,
                "signal": signal,
                "confidence": round(confidence, 3),
                "recent_sentiment": round(recent_sentiment, 3),
                "sentiment_label": sentiment_summary.get("sentiment", "neutral"),
                "news_count": sentiment_summary.get("news_count", 0),
                "correlation": round(best_correlation, 3),
                "optimal_lag": best_lag["lag_period"],
                "reason": self._generate_signal_reason(signal, confidence, recent_sentiment, best_correlation)
            }
        except Exception as e:
            logger.error(f"Error generating predictive signals: {e}")
            return {
                "coin": coin,
                "signal": "neutral",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _generate_signal_reason(
        self,
        signal: str,
        confidence: float,
        sentiment: float,
        correlation: float
    ) -> str:
        """Generate human-readable explanation for signal"""
        if signal == "neutral":
            return "Insufficient data or weak correlations for directional signal"
        
        sentiment_desc = "positive" if sentiment > 0 else "negative"
        corr_type = "positive" if correlation > 0 else "negative (contrarian)"
        
        return (
            f"{signal.capitalize()} signal with {confidence:.1%} confidence. "
            f"Recent news sentiment is {sentiment_desc} ({sentiment:.2f}), "
            f"and historical correlation is {corr_type} ({correlation:.2f})."
        )


# Singleton instance
_correlation_analyzer = None


def get_correlation_analyzer(db: AsyncIOMotorDatabase) -> NewsMarketCorrelationAnalyzer:
    """Get or create correlation analyzer instance"""
    global _correlation_analyzer
    if _correlation_analyzer is None:
        _correlation_analyzer = NewsMarketCorrelationAnalyzer(db)
    return _correlation_analyzer
