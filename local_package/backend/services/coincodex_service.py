"""
CoinCodex API Service
Free API for cryptocurrency market data and historical prices.
No API key required.
"""

import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio


class CoinCodexService:
    """
    Service for fetching cryptocurrency data from CoinCodex API.
    Free tier with no rate limits.
    """
    
    BASE_URL = "https://coincodex.com/api"
    
    # CoinCodex symbol mapping (their internal IDs)
    SYMBOL_MAP = {
        'bitcoin': 'BTC',
        'ethereum': 'ETH',
        'solana': 'SOL',
        'cardano': 'ADA',
        'polkadot': 'DOT',
        'avalanche': 'AVAX',
        'chainlink': 'LINK',
        'polygon': 'MATIC',
        'uniswap': 'UNI',
        'litecoin': 'LTC',
        'dogecoin': 'DOGE',
        'ripple': 'XRP',
        'tron': 'TRX',
        'cosmos': 'ATOM',
        'near': 'NEAR',
        'aptos': 'APT',
        'sui': 'SUI',
        'arbitrum': 'ARB',
        'optimism': 'OP',
        'binancecoin': 'BNB',
        'stellar': 'XLM',
        'monero': 'XMR',
        'algorand': 'ALGO',
        'fantom': 'FTM',
        'aave': 'AAVE',
        'maker': 'MKR',
        'the-sandbox': 'SAND',
        'decentraland': 'MANA',
        'the-graph': 'GRT',
        'filecoin': 'FIL',
        'fetch-ai': 'FET',
        'shiba-inu': 'SHIB',
        'ethereum-classic': 'ETC',
        'bitcoin-cash': 'BCH',
        'hedera': 'HBAR',
        'internet-computer': 'ICP',
        'vechain': 'VET',
        'tezos': 'XTZ',
        'eos': 'EOS',
        'immutable-x': 'IMX',
        'curve-dao-token': 'CRV',
        'lido-dao': 'LDO',
        'render-token': 'RNDR',
        'injective': 'INJ',
        'sei': 'SEI',
        'celestia': 'TIA',
        'thorchain': 'RUNE',
        'zcash': 'ZEC',
        'dash': 'DASH',
        'neo': 'NEO',
        'iota': 'MIOTA',
        'pepe': 'PEPE',
        'floki': 'FLOKI',
        'bonk': 'BONK',
        'worldcoin': 'WLD',
        'bittensor': 'TAO',
        'jupiter': 'JUP',
        'pyth': 'PYTH',
    }
    
    # Reverse mapping
    ID_TO_COIN = {v: k for k, v in SYMBOL_MAP.items()}
    
    def __init__(self):
        self.client = None
    
    async def _get_client(self):
        """Get or create HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def get_firstpage_history(
        self,
        days: int = 365,
        samples: int = 365,
        coins_limit: int = 50
    ) -> Dict[str, List]:
        """
        Get historical data for top coins by market cap.
        
        Args:
            days: Number of days of history
            samples: Number of data points per coin
            coins_limit: Number of top coins to fetch
            
        Returns:
            Dict mapping coin symbols to price history arrays
        """
        try:
            client = await self._get_client()
            url = f"{self.BASE_URL}/coincodex/get_firstpage_history/{days}/{samples}/{coins_limit}"
            
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"CoinCodex API error: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"CoinCodex fetch error: {e}")
            return {}
    
    async def get_coin(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed information for a single coin.
        
        Args:
            symbol: CoinCodex internal ID (e.g., 'BTC', 'ETH')
            
        Returns:
            Coin details including description, ICO price, social links, etc.
        """
        try:
            client = await self._get_client()
            url = f"{self.BASE_URL}/coincodex/get_coin/{symbol}"
            
            response = await client.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"CoinCodex get_coin error: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"CoinCodex get_coin error: {e}")
            return {}
    
    async def get_coin_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        samples: int = 365
    ) -> Dict[str, List]:
        """
        Get historical price data for a single coin.
        
        Args:
            symbol: CoinCodex internal ID (e.g., 'BTC')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            samples: Number of data points
            
        Returns:
            Dict with price history: {symbol: [[timestamp, price, volume], ...]}
        """
        try:
            client = await self._get_client()
            url = f"{self.BASE_URL}/coincodex/get_coin_history/{symbol}/{start_date}/{end_date}/{samples}"
            
            response = await client.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"CoinCodex history error for {symbol}: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"CoinCodex history error: {e}")
            return {}
    
    async def get_coin_markets(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get exchanges and markets for a coin.
        
        Args:
            symbol: CoinCodex internal ID
            
        Returns:
            List of exchange data with volume and price info
        """
        try:
            client = await self._get_client()
            url = f"{self.BASE_URL}/exchange/get_markets_by_coin/{symbol}/"
            
            response = await client.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            print(f"CoinCodex markets error: {e}")
            return []
    
    async def get_coin_ranges(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get price ranges for multiple coins.
        
        Args:
            symbols: List of CoinCodex internal IDs
            
        Returns:
            Dict mapping symbols to their price ranges
        """
        try:
            client = await self._get_client()
            symbols_str = ",".join(symbols)
            url = f"{self.BASE_URL}/coincodex/get_coin_ranges/{symbols_str}/"
            
            response = await client.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            print(f"CoinCodex ranges error: {e}")
            return {}
    
    async def fetch_historical_for_db(
        self,
        coin_id: str,
        days: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical data formatted for database storage.
        
        Args:
            coin_id: Our internal coin ID (e.g., 'bitcoin')
            days: Number of days of history
            
        Returns:
            List of price records ready for MongoDB insertion
        """
        symbol = self.SYMBOL_MAP.get(coin_id)
        if not symbol:
            print(f"Unknown coin: {coin_id}")
            return []
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        data = await self.get_coin_history(symbol, start_date, end_date, days)
        
        if not data or symbol not in data:
            return []
        
        records = []
        for entry in data[symbol]:
            timestamp = entry[0]
            price = entry[1]
            volume = entry[2] if len(entry) > 2 else 0
            
            # Convert timestamp (seconds) to datetime
            dt = datetime.fromtimestamp(timestamp)
            
            records.append({
                'coin_id': coin_id,
                'symbol': symbol,
                'timestamp': dt.isoformat(),
                'date': dt.strftime('%Y-%m-%d'),
                'price': price,
                'close': price,
                'volume': volume,
                'source': 'coincodex'
            })
        
        return records
    
    async def fetch_all_coins_history(
        self,
        days: int = 365,
        coins: List[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Fetch historical data for multiple coins.
        
        Args:
            days: Number of days of history
            coins: List of coin IDs to fetch (defaults to all mapped coins)
            
        Returns:
            Dict mapping coin_id to list of price records
        """
        if coins is None:
            coins = list(self.SYMBOL_MAP.keys())
        
        all_data = {}
        
        for coin_id in coins:
            print(f"  Fetching {coin_id} from CoinCodex...")
            records = await self.fetch_historical_for_db(coin_id, days)
            
            if records:
                all_data[coin_id] = records
                print(f"    ✅ {coin_id}: {len(records)} records")
            else:
                print(f"    ⚠️ {coin_id}: No data")
            
            # Small delay to be nice to the API
            await asyncio.sleep(0.5)
        
        return all_data


# Singleton instance
coincodex_service = CoinCodexService()
