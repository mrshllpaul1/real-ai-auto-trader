"""
Historical Price Data Seeder
Fetches and stores real historical price data for backtesting and AI training.
Uses CoinGecko API with rate limiting to avoid hitting limits.
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import time

load_dotenv()


class HistoricalDataSeeder:
    """
    Seed the database with real historical crypto price data.
    Uses CoinGecko's free API with rate limiting.
    """
    
    def __init__(self, db):
        self.db = db
        
        # Coin IDs and their CoinGecko identifiers
        self.coins = {
            'bitcoin': 'bitcoin',
            'ethereum': 'ethereum',
            'litecoin': 'litecoin',
            'ripple': 'ripple',
            'dogecoin': 'dogecoin',
            'cardano': 'cardano',
            'polkadot': 'polkadot',
            'solana': 'solana',
            'avalanche-2': 'avalanche',
            'chainlink': 'chainlink',
            'polygon': 'matic-network',
            'uniswap': 'uniswap',
            'cosmos': 'cosmos',
            'tron': 'tron',
            'near': 'near',
        }
        
        # Rate limiting
        self.requests_per_minute = 10  # CoinGecko free tier limit
        self.last_request_time = 0
    
    async def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60 / self.requests_per_minute
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    async def fetch_historical_prices(
        self,
        coin_id: str,
        days: int = 365
    ) -> list:
        """Fetch historical prices from CoinGecko"""
        await self._rate_limit()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                    params={
                        'vs_currency': 'usd',
                        'days': str(days),
                        'interval': 'daily'
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    prices = data.get('prices', [])
                    volumes = data.get('total_volumes', [])
                    
                    # Convert to our format
                    records = []
                    for i, (timestamp, price) in enumerate(prices):
                        volume = volumes[i][1] if i < len(volumes) else 0
                        
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        
                        records.append({
                            'coin_id': coin_id,
                            'timestamp': dt.isoformat(),
                            'date': dt.strftime('%Y-%m-%d'),
                            'price': price,
                            'open': price * 0.99,  # Approximate OHLC
                            'high': price * 1.02,
                            'low': price * 0.98,
                            'close': price,
                            'volume': volume,
                            'source': 'coingecko'
                        })
                    
                    return records
                elif response.status_code == 429:
                    print(f"Rate limited, waiting 60s...")
                    await asyncio.sleep(60)
                    return await self.fetch_historical_prices(coin_id, days)
                else:
                    print(f"Failed to fetch {coin_id}: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Error fetching {coin_id}: {e}")
            return []
    
    async def seed_coin(self, coin_id: str, days: int = 365):
        """Seed historical data for a single coin"""
        print(f"  Fetching {coin_id}...")
        
        records = await self.fetch_historical_prices(coin_id, days)
        
        if records:
            # Delete existing data for this coin to avoid duplicates
            await self.db.historical_prices.delete_many({'coin_id': coin_id})
            
            # Insert new records
            await self.db.historical_prices.insert_many(records)
            print(f"  ✅ {coin_id}: {len(records)} records saved")
            return len(records)
        else:
            print(f"  ❌ {coin_id}: No data fetched")
            return 0
    
    async def seed_all_coins(self, days: int = 365):
        """Seed historical data for all coins"""
        print(f"\n{'='*60}")
        print("📊 SEEDING HISTORICAL PRICE DATA")
        print(f"{'='*60}")
        print(f"Coins: {len(self.coins)}")
        print(f"Days: {days}")
        print(f"{'='*60}\n")
        
        total_records = 0
        
        for coin_id in self.coins.keys():
            count = await self.seed_coin(coin_id, days)
            total_records += count
            
            # Small delay between coins
            await asyncio.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"✅ SEEDING COMPLETE: {total_records} total records")
        print(f"{'='*60}\n")
        
        return total_records
    
    async def seed_extended_historical(self):
        """
        Seed extended historical data by fetching maximum available.
        CoinGecko free tier allows up to 365 days.
        For longer history, we use 'max' parameter where available.
        """
        print(f"\n{'='*60}")
        print("📊 SEEDING EXTENDED HISTORICAL DATA")
        print(f"{'='*60}\n")
        
        # For BTC, try to get max available data
        major_coins = ['bitcoin', 'ethereum', 'litecoin']
        
        for coin_id in major_coins:
            print(f"  Fetching max history for {coin_id}...")
            
            await self._rate_limit()
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                        params={
                            'vs_currency': 'usd',
                            'days': 'max',
                            'interval': 'daily'
                        },
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
                                'open': price * 0.99,
                                'high': price * 1.02,
                                'low': price * 0.98,
                                'close': price,
                                'volume': volume,
                                'source': 'coingecko_max'
                            })
                        
                        if records:
                            await self.db.historical_prices.delete_many({'coin_id': coin_id})
                            await self.db.historical_prices.insert_many(records)
                            print(f"  ✅ {coin_id}: {len(records)} records (from {records[0]['date']} to {records[-1]['date']})")
                    
            except Exception as e:
                print(f"  ❌ Error fetching max history for {coin_id}: {e}")
        
        # Seed remaining coins with 365 days
        remaining_coins = [c for c in self.coins.keys() if c not in major_coins]
        
        for coin_id in remaining_coins:
            await self.seed_coin(coin_id, 365)
            await asyncio.sleep(1)
        
        # Create indexes
        await self.db.historical_prices.create_index([('coin_id', 1), ('timestamp', 1)])
        await self.db.historical_prices.create_index([('timestamp', 1)])
        
        print(f"\n✅ Extended seeding complete")


async def seed_data():
    """Entry point for seeding"""
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'crypto_trading_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    seeder = HistoricalDataSeeder(db)
    await seeder.seed_extended_historical()


if __name__ == "__main__":
    asyncio.run(seed_data())
