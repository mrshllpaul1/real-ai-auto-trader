"""
Enhanced Market Data Integrator
Provides multi-source validation, data quality monitoring, and advanced correlation analysis.
Complements market_data_service.py with enhanced integration capabilities.
"""

import asyncio
import httpx
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class EnhancedMarketDataIntegrator:
    """
    Advanced market data integration with:
    - Multi-source validation and cross-referencing
    - Data quality scoring and monitoring
    - Intelligent source selection and failover
    - Anomaly detection across sources
    """
    
    def __init__(self):
        self.sources = {
            'coingecko': {'priority': 2, 'available': True, 'failures': 0},
            'coinmarketcap': {'priority': 1, 'available': True, 'failures': 0},
            'coinstats': {'priority': 3, 'available': True, 'failures': 0}
        }
        self.quality_threshold = 0.7  # Minimum quality score to accept data
        self.max_failures = 3  # Mark source unavailable after N failures
        self.divergence_threshold = 0.05  # 5% price divergence triggers alert
        
        # API keys (loaded from environment variables)
        # Note: These are loaded from MARKET_DATA_INTEGRATION.md which documents the configured keys
        # In production, ensure these are set in environment variables
        self.api_keys = {
            'coinmarketcap': os.getenv('COINMARKETCAP_API_KEY', ''),
            'coinstats': os.getenv('COINSTATS_API_KEY', '')
        }
    
    async def get_validated_price(
        self,
        coin_id: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Get price from multiple sources with validation.
        
        Args:
            coin_id: Cryptocurrency identifier (e.g., 'bitcoin')
            validate: Whether to cross-validate across multiple sources
        
        Returns:
            Validated price data with quality metrics
        """
        if not validate:
            # Fast path - use primary source only
            return await self._fetch_from_primary_source(coin_id)
        
        # Fetch from all available sources in parallel
        tasks = []
        for source_name in self.sources:
            if self.sources[source_name]['available']:
                tasks.append(self._fetch_price_from_source(source_name, coin_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        valid_results = []
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result is not None:
                source_name = list(self.sources.keys())[i]
                result['source'] = source_name
                result['priority'] = self.sources[source_name]['priority']
                valid_results.append(result)
        
        if not valid_results:
            return {
                'coin_id': coin_id,
                'error': 'All data sources failed',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Validate and aggregate
        validated = self._validate_multi_source_data(coin_id, valid_results)
        
        return validated
    
    async def _fetch_from_primary_source(self, coin_id: str) -> Dict[str, Any]:
        """Fetch from highest priority available source"""
        sorted_sources = sorted(
            self.sources.items(),
            key=lambda x: x[1]['priority']
        )
        
        for source_name, config in sorted_sources:
            if config['available']:
                result = await self._fetch_price_from_source(source_name, coin_id)
                if result is not None:
                    result['source'] = source_name
                    result['validated'] = False
                    return result
        
        return {
            'coin_id': coin_id,
            'error': 'No available data sources',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _fetch_price_from_source(
        self,
        source: str,
        coin_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch price from specific source"""
        try:
            if source == 'coingecko':
                return await self._fetch_coingecko(coin_id)
            elif source == 'coinmarketcap':
                return await self._fetch_coinmarketcap(coin_id)
            elif source == 'coinstats':
                return await self._fetch_coinstats(coin_id)
            else:
                return None
        except Exception as e:
            logger.warning(f"{source} fetch failed for {coin_id}: {e}")
            self._mark_source_failure(source)
            return None
    
    async def _fetch_coingecko(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Fetch from CoinGecko API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.coingecko.com/api/v3/simple/price",
                    params={
                        'ids': coin_id,
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_market_cap': 'true',
                        'include_24hr_vol': 'true'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if coin_id in data:
                        coin_data = data[coin_id]
                        return {
                            'price_usd': coin_data.get('usd', 0),
                            'price_change_24h': coin_data.get('usd_24h_change', 0),
                            'market_cap': coin_data.get('usd_market_cap', 0),
                            'volume_24h': coin_data.get('usd_24h_vol', 0),
                            'timestamp': datetime.utcnow().isoformat()
                        }
        except Exception as e:
            logger.error(f"CoinGecko error: {e}")
        return None
    
    async def _fetch_coinmarketcap(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Fetch from CoinMarketCap API"""
        try:
            # Map coin_id to CMC slug
            symbol_map = {
                'bitcoin': 'BTC',
                'ethereum': 'ETH',
                'solana': 'SOL',
                'cardano': 'ADA',
                'ripple': 'XRP'
            }
            
            symbol = symbol_map.get(coin_id, coin_id.upper()[:3])
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
                    headers={
                        'X-CMC_PRO_API_KEY': self.api_keys['coinmarketcap']
                    },
                    params={
                        'symbol': symbol,
                        'convert': 'USD'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and symbol in data['data']:
                        coin_data = data['data'][symbol]
                        quote = coin_data['quote']['USD']
                        
                        return {
                            'price_usd': quote.get('price', 0),
                            'price_change_24h': quote.get('percent_change_24h', 0),
                            'market_cap': quote.get('market_cap', 0),
                            'volume_24h': quote.get('volume_24h', 0),
                            'timestamp': datetime.utcnow().isoformat()
                        }
        except Exception as e:
            logger.error(f"CoinMarketCap error: {e}")
        return None
    
    async def _fetch_coinstats(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Fetch from CoinStats API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.coinstats.app/public/v1/coins/{coin_id}",
                    headers={
                        'X-API-KEY': self.api_keys['coinstats']
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    coin = data.get('coin', {})
                    
                    return {
                        'price_usd': coin.get('price', 0),
                        'price_change_24h': coin.get('priceChange1d', 0),
                        'market_cap': coin.get('marketCap', 0),
                        'volume_24h': coin.get('volume', 0),
                        'timestamp': datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"CoinStats error: {e}")
        return None
    
    def _validate_multi_source_data(
        self,
        coin_id: str,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate and aggregate data from multiple sources.
        Detects anomalies and calculates quality score.
        """
        if len(results) == 1:
            # Single source - no validation possible
            result = results[0]
            result['quality_score'] = 0.5
            result['validated'] = False
            result['validation_notes'] = 'Single source - no cross-validation'
            return result
        
        # Extract prices for comparison
        prices = [r['price_usd'] for r in results if r.get('price_usd', 0) > 0]
        
        if not prices:
            return {
                'coin_id': coin_id,
                'error': 'No valid prices from any source',
                'sources_checked': len(results),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Calculate statistics
        avg_price = statistics.mean(prices)
        
        if len(prices) > 1:
            price_stdev = statistics.stdev(prices)
            price_variance = price_stdev / avg_price if avg_price > 0 else 0
        else:
            price_variance = 0
        
        # Detect anomalies (prices significantly different from mean)
        anomalies = []
        for result in results:
            price = result.get('price_usd', 0)
            if price > 0:
                divergence = abs(price - avg_price) / avg_price
                if divergence > self.divergence_threshold:
                    anomalies.append({
                        'source': result['source'],
                        'price': price,
                        'divergence': round(divergence * 100, 2)
                    })
        
        # Quality score calculation
        # Higher score = more agreement between sources
        quality_score = 1.0 - min(price_variance, 0.5) * 2
        
        # Select best source (highest priority with acceptable data)
        valid_sources = [
            r for r in results
            if r.get('price_usd', 0) > 0 and
            abs(r['price_usd'] - avg_price) / avg_price < self.divergence_threshold
        ]
        
        if not valid_sources:
            # All sources are anomalous - use highest priority
            best_source = min(results, key=lambda x: x['priority'])
        else:
            best_source = min(valid_sources, key=lambda x: x['priority'])
        
        # Aggregate result
        aggregated = {
            'coin_id': coin_id,
            'price_usd': best_source['price_usd'],
            'price_change_24h': best_source.get('price_change_24h', 0),
            'market_cap': best_source.get('market_cap', 0),
            'volume_24h': best_source.get('volume_24h', 0),
            'source': best_source['source'],
            'validated': True,
            'quality_score': round(quality_score, 3),
            'sources_checked': len(results),
            'validation': {
                'avg_price': round(avg_price, 2),
                'price_variance': round(price_variance, 4),
                'anomalies_detected': len(anomalies),
                'anomalies': anomalies if anomalies else None
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return aggregated
    
    def _mark_source_failure(self, source: str):
        """Mark a source as having failed"""
        if source in self.sources:
            self.sources[source]['failures'] += 1
            
            if self.sources[source]['failures'] >= self.max_failures:
                self.sources[source]['available'] = False
                logger.warning(f"Source {source} marked as unavailable after {self.max_failures} failures")
    
    def _mark_source_success(self, source: str):
        """Reset failure counter on successful fetch"""
        if source in self.sources:
            self.sources[source]['failures'] = 0
            self.sources[source]['available'] = True
    
    async def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report across all sources"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'sources': {}
        }
        
        # Test coins for quality check
        test_coins = ['bitcoin', 'ethereum', 'solana']
        
        for source_name in self.sources:
            if self.sources[source_name]['available']:
                successes = 0
                failures = 0
                response_times = []
                
                for coin_id in test_coins:
                    start = datetime.utcnow()
                    result = await self._fetch_price_from_source(source_name, coin_id)
                    end = datetime.utcnow()
                    
                    if result and result.get('price_usd', 0) > 0:
                        successes += 1
                        response_times.append((end - start).total_seconds())
                    else:
                        failures += 1
                
                report['sources'][source_name] = {
                    'available': self.sources[source_name]['available'],
                    'priority': self.sources[source_name]['priority'],
                    'success_rate': round(successes / len(test_coins), 2),
                    'avg_response_time': round(statistics.mean(response_times), 3) if response_times else None,
                    'total_failures': self.sources[source_name]['failures']
                }
        
        return report
    
    async def correlate_news_with_price(
        self,
        coin_id: str,
        news_timestamp: datetime,
        lookback_hours: int = 4,
        lookahead_hours: int = 4
    ) -> Dict[str, Any]:
        """
        Analyze price movement correlation with news events.
        
        Args:
            coin_id: Cryptocurrency identifier
            news_timestamp: When the news was published
            lookback_hours: Hours to look back before news
            lookahead_hours: Hours to look ahead after news
        
        Returns:
            Correlation analysis including price impact
        """
        # This is a placeholder for price-news correlation
        # In a full implementation, this would:
        # 1. Fetch historical price data around the news timestamp
        # 2. Calculate price changes in various time windows
        # 3. Compare to normal volatility
        # 4. Determine if news had significant impact
        
        return {
            'coin_id': coin_id,
            'news_timestamp': news_timestamp.isoformat(),
            'analysis_window': {
                'lookback_hours': lookback_hours,
                'lookahead_hours': lookahead_hours
            },
            'status': 'not_implemented',
            'note': 'Full implementation requires historical price database'
        }
    
    def get_source_status(self) -> Dict[str, Any]:
        """Get current status of all data sources"""
        return {
            'sources': self.sources,
            'quality_threshold': self.quality_threshold,
            'divergence_threshold': self.divergence_threshold,
            'timestamp': datetime.utcnow().isoformat()
        }
