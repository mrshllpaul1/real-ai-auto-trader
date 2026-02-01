import httpx
from typing import Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class CoinMarketCapService:
    """
    CoinMarketCap API integration for cryptocurrency data
    Provides professional-grade market data, quotes, and global metrics
    """
    
    def __init__(self):
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        # Symbol to CoinMarketCap ID mapping
        self.symbol_map = {
            'bitcoin': 1,
            'ethereum': 1027,
            'solana': 5426,
            'cardano': 2010,
            'ripple': 52,
            'dogecoin': 74,
            'polkadot': 6636,
            'avalanche': 5805
        }
    
    async def get_latest_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get latest market quotes for cryptocurrencies"""
        try:
            # Convert symbols to CMC IDs
            ids = [str(self.symbol_map.get(symbol.lower(), symbol)) for symbol in symbols]
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/cryptocurrency/quotes/latest",
                    headers=self.headers,
                    params={'id': ','.join(ids)},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"CoinMarketCap API error: {response.status_code}")
                
                data = response.json()
                
                # Transform to consistent format
                result = {}
                for symbol in symbols:
                    cmc_id = str(self.symbol_map.get(symbol.lower(), symbol))
                    if cmc_id in data.get('data', {}):
                        coin_data = data['data'][cmc_id]
                        quote = coin_data['quote']['USD']
                        
                        result[symbol.lower()] = {
                            'price_usd': quote['price'],
                            'price_change_24h': quote['percent_change_24h'],
                            'price_change_7d': quote.get('percent_change_7d', 0),
                            'market_cap': quote['market_cap'],
                            'volume_24h': quote['volume_24h'],
                            'circulating_supply': coin_data.get('circulating_supply', 0),
                            'total_supply': coin_data.get('total_supply', 0),
                            'max_supply': coin_data.get('max_supply', 0),
                            'market_cap_rank': coin_data.get('cmc_rank', 0),
                            'last_updated': quote['last_updated'],
                            'source': 'coinmarketcap'
                        }
                
                return result
        except Exception as e:
            print(f"CoinMarketCap error: {str(e)}")
            return {}
    
    async def get_global_metrics(self) -> Dict[str, Any]:
        """Get global cryptocurrency market metrics"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/global-metrics/quotes/latest",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return {}
                
                data = response.json()
                metrics = data.get('data', {})
                quote = metrics.get('quote', {}).get('USD', {})
                
                return {
                    'total_market_cap': quote.get('total_market_cap', 0),
                    'total_volume_24h': quote.get('total_volume_24h', 0),
                    'bitcoin_dominance': metrics.get('btc_dominance', 0),
                    'ethereum_dominance': metrics.get('eth_dominance', 0),
                    'active_cryptocurrencies': metrics.get('active_cryptocurrencies', 0),
                    'active_exchanges': metrics.get('active_exchanges', 0),
                    'last_updated': quote.get('last_updated', datetime.now().isoformat())
                }
        except Exception as e:
            print(f"CoinMarketCap global metrics error: {str(e)}")
            return {}
    
    async def get_trending(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending cryptocurrencies"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/cryptocurrency/trending/latest",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                trending = data.get('data', [])[:limit]
                
                return [
                    {
                        'id': coin.get('id'),
                        'name': coin.get('name'),
                        'symbol': coin.get('symbol'),
                        'rank': coin.get('cmc_rank', 0),
                        'price': coin.get('quote', {}).get('USD', {}).get('price', 0),
                        'change_24h': coin.get('quote', {}).get('USD', {}).get('percent_change_24h', 0)
                    }
                    for coin in trending
                ]
        except Exception as e:
            print(f"CoinMarketCap trending error: {str(e)}")
            return []


class CoinStatsService:
    """
    CoinStats API integration for cryptocurrency data
    Provides additional market data and portfolio tracking capabilities
    """
    
    def __init__(self):
        self.api_key = os.getenv('COINSTATS_API_KEY')
        self.base_url = "https://openapi.coinstats.app/public/v1"
        self.headers = {
            'X-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
    
    async def get_coin_data(self, coin_id: str) -> Dict[str, Any]:
        """Get detailed data for a specific coin"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/coins/{coin_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return {}
                
                data = response.json()
                
                return {
                    'price_usd': data.get('price', 0),
                    'price_change_24h': data.get('priceChange1d', 0),
                    'price_change_7d': data.get('priceChange1w', 0),
                    'market_cap': data.get('marketCap', 0),
                    'volume_24h': data.get('volume', 0),
                    'rank': data.get('rank', 0),
                    'source': 'coinstats'
                }
        except Exception as e:
            print(f"CoinStats error: {str(e)}")
            return {}
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market overview"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/markets",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return {}
                
                data = response.json()
                
                return {
                    'total_market_cap': data.get('totalMarketCap', 0),
                    'total_volume_24h': data.get('totalVolume', 0),
                    'bitcoin_dominance': data.get('btcDominance', 0),
                    'source': 'coinstats'
                }
        except Exception as e:
            print(f"CoinStats market overview error: {str(e)}")
            return {}


class AggregatedMarketDataService:
    """
    Aggregates data from multiple sources (CoinGecko, CoinMarketCap, CoinStats)
    Provides the most accurate and comprehensive market data
    """
    
    def __init__(self):
        from services.market_data_service import MarketDataService
        self.coingecko = MarketDataService()
        self.coinmarketcap = CoinMarketCapService()
        self.coinstats = CoinStatsService()
    
    async def get_aggregated_prices(self, coin_ids: List[str]) -> Dict[str, Any]:
        """
        Get aggregated price data from multiple sources
        Returns the most reliable data with source attribution
        """
        # Fetch from all sources in parallel
        cmc_data = await self.coinmarketcap.get_latest_quotes(coin_ids)
        cg_data = await self.coingecko.get_coin_price(coin_ids)
        
        # Aggregate and prioritize
        result = {}
        for coin_id in coin_ids:
            coin_id_lower = coin_id.lower()
            
            # Start with CoinMarketCap (most reliable for institutional data)
            if coin_id_lower in cmc_data:
                result[coin_id_lower] = cmc_data[coin_id_lower]
            # Fallback to CoinGecko
            elif coin_id_lower in cg_data:
                result[coin_id_lower] = cg_data[coin_id_lower]
            # Final fallback to CoinStats
            else:
                cs_data = await self.coinstats.get_coin_data(coin_id_lower)
                if cs_data:
                    result[coin_id_lower] = cs_data
            
            # Add aggregation metadata
            if coin_id_lower in result:
                result[coin_id_lower]['data_sources'] = []
                if coin_id_lower in cmc_data:
                    result[coin_id_lower]['data_sources'].append('coinmarketcap')
                if coin_id_lower in cg_data:
                    result[coin_id_lower]['data_sources'].append('coingecko')
                
                result[coin_id_lower]['aggregated'] = True
        
        return result
    
    async def get_comprehensive_market_data(self) -> Dict[str, Any]:
        """Get comprehensive market data from all sources"""
        cmc_global = await self.coinmarketcap.get_global_metrics()
        cs_market = await self.coinstats.get_market_overview()
        
        return {
            'global_metrics': {
                'total_market_cap': cmc_global.get('total_market_cap', 0),
                'total_volume_24h': cmc_global.get('total_volume_24h', 0),
                'bitcoin_dominance': cmc_global.get('bitcoin_dominance', 0),
                'ethereum_dominance': cmc_global.get('ethereum_dominance', 0),
                'active_cryptocurrencies': cmc_global.get('active_cryptocurrencies', 0),
                'active_exchanges': cmc_global.get('active_exchanges', 0),
            },
            'sources': ['coinmarketcap', 'coinstats', 'coingecko'],
            'last_updated': datetime.now().isoformat()
        }
