from pycoingecko import CoinGeckoAPI
from typing import Dict, Any, List
import httpx
from datetime import datetime, timedelta
import asyncio

class MarketDataService:
    def __init__(self):
        self.cg = CoinGeckoAPI()
        # In-memory cache to reduce API calls and improve performance
        self._cache = {}
        self._cache_ttl = {
            'price': 60,           # 1 minute for prices
            'historical': 600,     # 10 minutes for historical data
            'trending': 300,       # 5 minutes for trending
        }
    
    def _get_cached(self, key: str, cache_type: str = 'price') -> Any:
        """Get item from cache if not expired"""
        if key in self._cache:
            item, timestamp = self._cache[key]
            ttl = self._cache_ttl.get(cache_type, 60)
            if (datetime.now() - timestamp).total_seconds() < ttl:
                return item
            del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set item in cache"""
        self._cache[key] = (value, datetime.now())
    
    async def get_coin_price(self, coin_ids: List[str]) -> Dict[str, Any]:
        """Get current price for cryptocurrencies with caching"""
        try:
            cache_key = f"price_{','.join(sorted(coin_ids))}"
            cached = self._get_cached(cache_key, 'price')
            if cached:
                return cached
            
            # Run synchronous CoinGecko call in thread pool
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                lambda: self.cg.get_price(
                    ids=coin_ids,
                    vs_currencies='usd',
                    include_24hr_change=True,
                    include_market_cap=True,
                    include_24hr_vol=True
                )
            )
            
            result = {}
            for coin_id in coin_ids:
                if coin_id in data:
                    result[coin_id] = {
                        "price_usd": data[coin_id].get('usd', 0),
                        "price_change_24h": data[coin_id].get('usd_24h_change', 0),
                        "market_cap": data[coin_id].get('usd_market_cap', 0),
                        "volume_24h": data[coin_id].get('usd_24h_vol', 0),
                        "last_updated": datetime.now().isoformat()
                    }
            
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"Market data error: {str(e)}")
            # Return empty dict instead of raising to prevent chart failures
            return {}
    
    async def get_historical_data(self, coin_id: str, days: int = 30) -> Dict[str, Any]:
        """Get historical price data with caching and fallback"""
        try:
            cache_key = f"historical_{coin_id}_{days}"
            cached = self._get_cached(cache_key, 'historical')
            if cached:
                return cached
            
            # Run synchronous CoinGecko call in thread pool with timeout
            loop = asyncio.get_event_loop()
            data = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.cg.get_coin_market_chart_by_id(
                        id=coin_id,
                        vs_currency='usd',
                        days=days
                    )
                ),
                timeout=20.0  # 20 second timeout
            )
            
            result = {
                "coin_id": coin_id,
                "days": days,
                "prices": data['prices'],
                "market_caps": data['market_caps'],
                "total_volumes": data['total_volumes'],
                "cached": False,
                "fetched_at": datetime.now().isoformat()
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except asyncio.TimeoutError:
            print(f"Historical data timeout for {coin_id}")
            # Return cached data even if expired, or generate fallback
            old_cached = self._cache.get(cache_key)
            if old_cached:
                item, _ = old_cached
                item['cached'] = True
                item['stale'] = True
                return item
            return self._generate_fallback_historical(coin_id, days)
            
        except Exception as e:
            print(f"Historical data error for {coin_id}: {str(e)}")
            return self._generate_fallback_historical(coin_id, days)
    
    def _generate_fallback_historical(self, coin_id: str, days: int) -> Dict[str, Any]:
        """Generate fallback historical data when API fails"""
        import random
        
        # Use realistic base prices for common coins
        base_prices = {
            'bitcoin': 95000,
            'ethereum': 3500,
            'solana': 200,
            'cardano': 0.65,
            'polkadot': 8,
            'chainlink': 18,
            'avalanche': 40,
        }
        
        base_price = base_prices.get(coin_id, 100)
        now = datetime.now()
        
        prices = []
        market_caps = []
        volumes = []
        
        # Generate realistic-looking data
        current_price = base_price
        for i in range(days * 24):  # Hourly data points
            timestamp = int((now - timedelta(hours=days*24 - i)).timestamp() * 1000)
            
            # Add some realistic volatility
            change = random.uniform(-0.02, 0.02)
            current_price = current_price * (1 + change)
            
            prices.append([timestamp, current_price])
            market_caps.append([timestamp, current_price * random.uniform(1e9, 1e11)])
            volumes.append([timestamp, current_price * random.uniform(1e7, 1e9)])
        
        return {
            "coin_id": coin_id,
            "days": days,
            "prices": prices,
            "market_caps": market_caps,
            "total_volumes": volumes,
            "fallback": True,
            "message": "Using generated data due to API unavailability",
            "fetched_at": datetime.now().isoformat()
        }
    
    async def get_trending_coins(self) -> List[Dict[str, Any]]:
        """Get trending cryptocurrencies with caching"""
        try:
            cache_key = "trending_coins"
            cached = self._get_cached(cache_key, 'trending')
            if cached:
                return cached
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                self.cg.get_search_trending
            )
            
            result = [
                {
                    "id": coin['item']['id'],
                    "name": coin['item']['name'],
                    "symbol": coin['item']['symbol'],
                    "market_cap_rank": coin['item']['market_cap_rank']
                }
                for coin in data['coins'][:10]
            ]
            
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"Trending coins error: {str(e)}")
            return []
    
    async def get_crypto_news(self) -> List[Dict[str, Any]]:
        """Get latest crypto news - deprecated, use news_service instead"""
        return []