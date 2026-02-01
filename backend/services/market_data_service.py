from pycoingecko import CoinGeckoAPI
from typing import Dict, Any, List
import httpx
from datetime import datetime

class MarketDataService:
    def __init__(self):
        self.cg = CoinGeckoAPI()
    
    async def get_coin_price(self, coin_ids: List[str]) -> Dict[str, Any]:
        """Get current price for cryptocurrencies"""
        try:
            data = self.cg.get_price(
                ids=coin_ids,
                vs_currencies='usd',
                include_24hr_change=True,
                include_market_cap=True,
                include_24hr_vol=True
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
            return result
        except Exception as e:
            raise Exception(f"Market data error: {str(e)}")
    
    async def get_historical_data(self, coin_id: str, days: int = 30) -> Dict[str, Any]:
        """Get historical price data"""
        try:
            data = self.cg.get_coin_market_chart_by_id(
                id=coin_id,
                vs_currency='usd',
                days=days
            )
            
            return {
                "coin_id": coin_id,
                "days": days,
                "prices": data['prices'],
                "market_caps": data['market_caps'],
                "total_volumes": data['total_volumes']
            }
        except Exception as e:
            raise Exception(f"Historical data error: {str(e)}")
    
    async def get_trending_coins(self) -> List[Dict[str, Any]]:
        """Get trending cryptocurrencies"""
        try:
            data = self.cg.get_search_trending()
            return [
                {
                    "id": coin['item']['id'],
                    "name": coin['item']['name'],
                    "symbol": coin['item']['symbol'],
                    "market_cap_rank": coin['item']['market_cap_rank']
                }
                for coin in data['coins'][:10]
            ]
        except Exception as e:
            raise Exception(f"Trending coins error: {str(e)}")
    
    async def get_crypto_news(self) -> List[Dict[str, Any]]:
        """Get latest crypto news and events"""
        try:
            # Using CoinGecko status updates as news
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/status_updates",
                    params={"category": "general", "per_page": 10}
                )
                data = response.json()
                
                if 'status_updates' in data:
                    return [
                        {
                            "title": update.get('project', {}).get('name', 'Crypto Update'),
                            "description": update.get('description', ''),
                            "created_at": update.get('created_at', ''),
                            "user": update.get('user', '')
                        }
                        for update in data['status_updates']
                    ]
                return []
        except Exception:
            return []