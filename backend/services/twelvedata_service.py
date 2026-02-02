"""
Twelve Data API Service
Financial data provider for stocks, forex, and cryptocurrencies.
Provides historical price data with good coverage.
"""

import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


class TwelveDataService:
    """
    Service for fetching cryptocurrency data from Twelve Data API.
    Supports historical OHLCV data with extended history.
    """
    
    BASE_URL = "https://api.twelvedata.com"
    
    # Twelve Data crypto symbols (format: SYMBOL/USD)
    CRYPTO_SYMBOLS = {
        'bitcoin': 'BTC/USD',
        'ethereum': 'ETH/USD',
        'litecoin': 'LTC/USD',
        'ripple': 'XRP/USD',
        'cardano': 'ADA/USD',
        'solana': 'SOL/USD',
        'polkadot': 'DOT/USD',
        'dogecoin': 'DOGE/USD',
        'avalanche': 'AVAX/USD',
        'chainlink': 'LINK/USD',
        'polygon': 'MATIC/USD',
        'uniswap': 'UNI/USD',
        'cosmos': 'ATOM/USD',
        'tron': 'TRX/USD',
        'stellar': 'XLM/USD',
        'monero': 'XMR/USD',
        'ethereum-classic': 'ETC/USD',
        'bitcoin-cash': 'BCH/USD',
        'algorand': 'ALGO/USD',
        'vechain': 'VET/USD',
        'tezos': 'XTZ/USD',
        'eos': 'EOS/USD',
        'aave': 'AAVE/USD',
        'maker': 'MKR/USD',
        'compound': 'COMP/USD',
        'sushiswap': 'SUSHI/USD',
        'yearn-finance': 'YFI/USD',
        'the-sandbox': 'SAND/USD',
        'decentraland': 'MANA/USD',
        'axie-infinity': 'AXS/USD',
        'enjincoin': 'ENJ/USD',
        'the-graph': 'GRT/USD',
        'filecoin': 'FIL/USD',
        'zcash': 'ZEC/USD',
        'dash': 'DASH/USD',
        'neo': 'NEO/USD',
        'iota': 'IOTA/USD',
        'waves': 'WAVES/USD',
        'qtum': 'QTUM/USD',
        'zilliqa': 'ZIL/USD',
        'near': 'NEAR/USD',
        'fantom': 'FTM/USD',
        'hedera': 'HBAR/USD',
        'shiba-inu': 'SHIB/USD',
        'aptos': 'APT/USD',
        'arbitrum': 'ARB/USD',
        'optimism': 'OP/USD',
        'injective': 'INJ/USD',
        'sei': 'SEI/USD',
        'celestia': 'TIA/USD',
        'sui': 'SUI/USD',
        'pepe': 'PEPE/USD',
        'bonk': 'BONK/USD',
        'fetch-ai': 'FET/USD',
        'render-token': 'RNDR/USD',
        'thorchain': 'RUNE/USD',
        'curve-dao-token': 'CRV/USD',
        'lido-dao': 'LDO/USD',
        'gmx': 'GMX/USD',
        'pancakeswap': 'CAKE/USD',
        'synthetix': 'SNX/USD',
        '1inch': '1INCH/USD',
        'gala': 'GALA/USD',
        'immutable-x': 'IMX/USD',
        'arweave': 'AR/USD',
        'ocean-protocol': 'OCEAN/USD',
        'cronos': 'CRO/USD',
        'kucoin-token': 'KCS/USD',
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('TWELVEDATA_API_KEY')
        self.client = None
        self.requests_this_minute = 0
        self.minute_start = datetime.now()
        self.rate_limit = 8  # Free tier: 8 requests per minute
    
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
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        if (now - self.minute_start).seconds >= 60:
            self.requests_this_minute = 0
            self.minute_start = now
        
        if self.requests_this_minute >= self.rate_limit:
            wait_time = 60 - (now - self.minute_start).seconds
            print(f"  ⏳ Rate limit reached, waiting {wait_time}s...")
            await asyncio.sleep(wait_time + 1)
            self.requests_this_minute = 0
            self.minute_start = datetime.now()
        
        self.requests_this_minute += 1
    
    async def get_time_series(
        self,
        symbol: str,
        interval: str = "1day",
        outputsize: int = 365,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Get time series data for a symbol.
        
        Args:
            symbol: Twelve Data symbol (e.g., 'BTC/USD')
            interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
            outputsize: Number of data points (max 5000)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Time series data with OHLCV values
        """
        await self._rate_limit_check()
        
        try:
            client = await self._get_client()
            
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            response = await client.get(
                f"{self.BASE_URL}/time_series",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    return data
                elif 'code' in data:
                    print(f"  ❌ API error: {data.get('message', 'Unknown error')}")
                    return {}
            else:
                print(f"  ❌ HTTP error: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"  ❌ Request error: {e}")
            return {}
    
    async def get_crypto_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for a cryptocurrency"""
        await self._rate_limit_check()
        
        try:
            client = await self._get_client()
            
            response = await client.get(
                f"{self.BASE_URL}/quote",
                params={
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
            
        except Exception as e:
            print(f"Quote error: {e}")
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
        symbol = self.CRYPTO_SYMBOLS.get(coin_id)
        if not symbol:
            print(f"  ⚠️ Unknown coin: {coin_id}")
            return []
        
        print(f"  📥 Fetching {coin_id} ({symbol}) from Twelve Data...")
        
        data = await self.get_time_series(
            symbol=symbol,
            interval="1day",
            outputsize=min(days, 5000)
        )
        
        if not data or 'values' not in data:
            return []
        
        records = []
        for entry in data['values']:
            try:
                dt = datetime.strptime(entry['datetime'], '%Y-%m-%d')
                
                records.append({
                    'coin_id': coin_id,
                    'symbol': symbol.split('/')[0],
                    'timestamp': dt.isoformat(),
                    'date': entry['datetime'],
                    'open': float(entry['open']),
                    'high': float(entry['high']),
                    'low': float(entry['low']),
                    'close': float(entry['close']),
                    'price': float(entry['close']),
                    'volume': float(entry.get('volume', 0)),
                    'source': 'twelvedata'
                })
            except (KeyError, ValueError) as e:
                continue
        
        # Reverse to chronological order (oldest first)
        records.reverse()
        
        return records
    
    async def fetch_extended_history(
        self,
        coin_id: str,
        start_date: str = "2015-01-01",
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch extended historical data with date range.
        
        Args:
            coin_id: Our internal coin ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
            
        Returns:
            List of price records
        """
        symbol = self.CRYPTO_SYMBOLS.get(coin_id)
        if not symbol:
            return []
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"  📥 Fetching {coin_id} ({start_date} to {end_date})...")
        
        data = await self.get_time_series(
            symbol=symbol,
            interval="1day",
            outputsize=5000,
            start_date=start_date,
            end_date=end_date
        )
        
        if not data or 'values' not in data:
            return []
        
        records = []
        for entry in data['values']:
            try:
                dt = datetime.strptime(entry['datetime'], '%Y-%m-%d')
                
                records.append({
                    'coin_id': coin_id,
                    'symbol': symbol.split('/')[0],
                    'timestamp': dt.isoformat(),
                    'date': entry['datetime'],
                    'open': float(entry['open']),
                    'high': float(entry['high']),
                    'low': float(entry['low']),
                    'close': float(entry['close']),
                    'price': float(entry['close']),
                    'volume': float(entry.get('volume', 0)),
                    'source': 'twelvedata'
                })
            except (KeyError, ValueError):
                continue
        
        records.reverse()
        return records
    
    async def seed_all_coins(self, db, days: int = 365) -> int:
        """
        Seed historical data for all supported coins.
        
        Args:
            db: MongoDB database instance
            days: Number of days of history
            
        Returns:
            Total records seeded
        """
        print(f"\n{'='*60}")
        print("📊 SEEDING FROM TWELVE DATA")
        print(f"{'='*60}")
        print(f"API Key: {self.api_key[:8]}...{self.api_key[-4:]}")
        print(f"Coins: {len(self.CRYPTO_SYMBOLS)}")
        print(f"Days: {days}")
        print(f"{'='*60}\n")
        
        total_records = 0
        
        for coin_id in self.CRYPTO_SYMBOLS.keys():
            records = await self.fetch_historical_for_db(coin_id, days)
            
            if records:
                await db.historical_prices.delete_many({'coin_id': coin_id})
                await db.historical_prices.insert_many(records)
                total_records += len(records)
                print(f"    ✅ {coin_id}: {len(records)} records ({records[0]['date']} to {records[-1]['date']})")
            else:
                print(f"    ⚠️ {coin_id}: No data")
            
            await asyncio.sleep(0.5)
        
        # Create indexes
        await db.historical_prices.create_index([('coin_id', 1), ('timestamp', 1)])
        await db.historical_prices.create_index([('timestamp', 1)])
        
        print(f"\n{'='*60}")
        print(f"✅ SEEDING COMPLETE: {total_records} total records")
        print(f"{'='*60}\n")
        
        return total_records


# Singleton instance
twelvedata_service = None

def get_twelvedata_service(api_key: str = None) -> TwelveDataService:
    """Get or create Twelve Data service instance"""
    global twelvedata_service
    if twelvedata_service is None:
        twelvedata_service = TwelveDataService(api_key)
    return twelvedata_service
