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
            # Try Kraken as fallback
            kraken_data = await self.get_historical_from_kraken(coin_id, days)
            if kraken_data:
                return kraken_data
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
            # Try Kraken as fallback
            kraken_data = await self.get_historical_from_kraken(coin_id, days)
            if kraken_data:
                return kraken_data
            return self._generate_fallback_historical(coin_id, days)
    
    def _generate_fallback_historical(self, coin_id: str, days: int) -> Dict[str, Any]:
        """
        Return error indicator when API fails.
        NEVER generates fake or simulated data - only real market data is used.
        """
        return {
            "coin_id": coin_id,
            "days": days,
            "prices": [],
            "market_caps": [],
            "total_volumes": [],
            "error": True,
            "data_available": False,
            "message": f"No real historical data available for {coin_id}. API unavailable.",
            "fetched_at": datetime.now().isoformat()
        }
    
    async def get_historical_from_kraken(self, coin_id: str, days: int = 30) -> Dict[str, Any]:
        """Get historical OHLC data from Kraken public API as fallback"""
        try:
            import httpx
            
            # Map coin IDs to Kraken pairs
            pair_map = {
                'bitcoin': 'XBTUSD',
                'ethereum': 'ETHUSD',
                'solana': 'SOLUSD',
                'cardano': 'ADAUSD',
                'dogecoin': 'DOGEUSD',
                'ripple': 'XRPUSD',
                'polkadot': 'DOTUSD',
                'litecoin': 'LTCUSD',
                'chainlink': 'LINKUSD',
                'avalanche-2': 'AVAXUSD',
            }
            
            pair = pair_map.get(coin_id.lower(), f"{coin_id.upper()[:3]}USD")
            
            # Use daily interval (1440 minutes) for historical view
            interval = 1440 if days > 7 else 60  # Daily or hourly
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.kraken.com/0/public/OHLC",
                    params={"pair": pair, "interval": interval}
                )
                data = response.json()
                
                if data.get("error"):
                    print(f"Kraken OHLC error for {coin_id}: {data['error']}")
                    return None
                
                result = data.get("result", {})
                # Get the first key that's not 'last'
                ohlc_data = None
                for key in result:
                    if key != "last":
                        ohlc_data = result[key]
                        break
                
                if not ohlc_data:
                    return None
                
                # Convert OHLC to price format [timestamp_ms, close_price]
                # OHLC format: [time, open, high, low, close, vwap, volume, count]
                prices = []
                for candle in ohlc_data[-days:]:  # Last N days
                    timestamp_ms = int(candle[0]) * 1000
                    close_price = float(candle[4])
                    prices.append([timestamp_ms, close_price])
                
                return {
                    "coin_id": coin_id,
                    "days": days,
                    "prices": prices,
                    "market_caps": [],
                    "total_volumes": [],
                    "source": "kraken",
                    "fetched_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"Kraken historical data error for {coin_id}: {e}")
            return None
    
    async def get_all_coins(self, per_page: int = 250, page: int = 1) -> List[Dict[str, Any]]:
        """Get a list of coins with market data from CoinGecko"""
        try:
            cache_key = f"all_coins_{per_page}_page_{page}"
            cached = self._get_cached(cache_key, 'coins')
            if cached:
                return cached
            
            loop = asyncio.get_event_loop()
            
            # Get coins market data
            data = await loop.run_in_executor(
                None,
                lambda: self.cg.get_coins_markets(
                    vs_currency='usd',
                    order='market_cap_desc',
                    per_page=per_page,
                    page=page,
                    sparkline=False,
                    price_change_percentage='24h,7d'
                )
            )
            
            result = []
            for coin in data:
                result.append({
                    "id": coin.get('id'),
                    "symbol": coin.get('symbol', '').upper(),
                    "name": coin.get('name'),
                    "current_price": coin.get('current_price', 0),
                    "market_cap": coin.get('market_cap', 0),
                    "market_cap_rank": coin.get('market_cap_rank', 0),
                    "total_volume": coin.get('total_volume', 0),
                    "price_change_24h": coin.get('price_change_percentage_24h', 0),
                    "price_change_7d": coin.get('price_change_percentage_7d_in_currency', 0)
                })
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            print(f"Get all coins error: {str(e)}")
            return []
    
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