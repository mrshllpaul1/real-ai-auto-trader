"""
Historical Price Data Seeder
Fetches and stores real historical price data for backtesting and AI training.
Uses CoinCodex API (primary, no rate limits) and CoinGecko API (fallback).
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import time
from services.coincodex_service import CoinCodexService

load_dotenv()


class HistoricalDataSeeder:
    """
    Seed the database with real historical crypto price data.
    Uses CoinCodex (primary) and CoinGecko (fallback).
    """
    
    def __init__(self, db):
        self.db = db
        self.coincodex = CoinCodexService()
        
        # Coin IDs
        self.coins = [
            'bitcoin', 'ethereum', 'litecoin', 'ripple', 'dogecoin',
            'cardano', 'polkadot', 'solana', 'avalanche', 'chainlink',
            'polygon', 'uniswap', 'cosmos', 'tron', 'near'
        ]
        
        # CoinGecko rate limiting
        self.requests_per_minute = 10
        self.last_request_time = 0
    
    async def _rate_limit(self):
        """Ensure we don't exceed CoinGecko rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60 / self.requests_per_minute
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    async def seed_from_coincodex(self, coin_id: str, days: int = 365) -> int:
        """Seed historical data from CoinCodex API"""
        print(f"  📥 Fetching {coin_id} from CoinCodex...")
        
        records = await self.coincodex.fetch_historical_for_db(coin_id, days)
        
        if records:
            await self.db.historical_prices.delete_many({'coin_id': coin_id})
            await self.db.historical_prices.insert_many(records)
            print(f"    ✅ {coin_id}: {len(records)} records saved")
            return len(records)
        else:
            print(f"    ⚠️ {coin_id}: No data from CoinCodex")
            return 0
    
    async def seed_from_coingecko(self, coin_id: str, days: int = 365) -> int:
        """Fallback: Seed from CoinGecko API"""
        await self._rate_limit()
        
        print(f"  📥 Fetching {coin_id} from CoinGecko (fallback)...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart',
                    params={'vs_currency': 'usd', 'days': str(days), 'interval': 'daily'},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    prices = data.get('prices', [])
                    volumes = data.get('total_volumes', [])
                    
                    records = []
                    for i, (timestamp, price) in enumerate(prices):
                        volume = volumes[i][1] if i < len(volumes) else 0
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        
                        records.append({
                            'coin_id': coin_id,
                            'timestamp': dt.isoformat(),
                            'date': dt.strftime('%Y-%m-%d'),
                            'price': price,
                            'close': price,
                            'volume': volume,
                            'source': 'coingecko'
                        })
                    
                    if records:
                        await self.db.historical_prices.delete_many({'coin_id': coin_id})
                        await self.db.historical_prices.insert_many(records)
                        print(f"    ✅ {coin_id}: {len(records)} records saved")
                        return len(records)
                        
        except Exception as e:
            print(f"    ❌ {coin_id}: CoinGecko error - {e}")
        
        return 0
    
    async def seed_coin(self, coin_id: str, days: int = 365) -> int:
        """Seed historical data for a single coin (tries CoinCodex first)"""
        # Try CoinCodex first (no rate limits)
        count = await self.seed_from_coincodex(coin_id, days)
        
        if count == 0:
            # Fallback to CoinGecko
            count = await self.seed_from_coingecko(coin_id, days)
        
        return count
    
    async def seed_all_coins(self, days: int = 365):
        """Seed historical data for all coins"""
        print(f"\n{'='*60}")
        print("📊 SEEDING HISTORICAL PRICE DATA")
        print(f"{'='*60}")
        print(f"Coins: {len(self.coins)}")
        print(f"Days: {days}")
        print(f"Primary Source: CoinCodex (no rate limits)")
        print(f"Fallback: CoinGecko")
        print(f"{'='*60}\n")
        
        total_records = 0
        
        for coin_id in self.coins:
            count = await self.seed_coin(coin_id, days)
            total_records += count
            await asyncio.sleep(0.5)  # Small delay between coins
        
        # Create indexes
        await self.db.historical_prices.create_index([('coin_id', 1), ('timestamp', 1)])
        await self.db.historical_prices.create_index([('timestamp', 1)])
        
        print(f"\n{'='*60}")
        print(f"✅ SEEDING COMPLETE: {total_records} total records")
        print(f"{'='*60}\n")
        
        return total_records
    
    async def seed_extended_historical(self):
        """Seed extended historical data (max available)"""
        print(f"\n{'='*60}")
        print("📊 SEEDING EXTENDED HISTORICAL DATA")
        print(f"{'='*60}\n")
        
        # CoinCodex supports longer history
        # Try to get max available (up to several years)
        await self.seed_all_coins(days=1825)  # ~5 years
        
        print(f"\n✅ Extended seeding complete")


async def seed_data():
    """Entry point for seeding"""
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'crypto_trading_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    seeder = HistoricalDataSeeder(db)
    await seeder.seed_all_coins(days=365)


if __name__ == "__main__":
    asyncio.run(seed_data())
