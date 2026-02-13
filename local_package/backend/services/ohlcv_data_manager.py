"""
OHLCV Data Manager Service
Handles bulk download and management of historical OHLCV data for AI training
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class OHLCVDataManager:
    """
    Manages OHLCV data download, storage, and retrieval for ML/DL training:
    - Bulk download from CryptoCompare API
    - Database storage with efficient indexing
    - Data quality validation
    - Training data preparation
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = None  # Set via set_api_key
        self.base_url = "https://min-api.cryptocompare.com/data/v2"
        
        # Top coins to download for ML training
        self.training_coins = [
            'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'MATIC', 'LINK', 'AVAX',
            'ATOM', 'UNI', 'LTC', 'XRP', 'DOGE', 'SHIB', 'ARB', 'OP',
            'NEAR', 'APT', 'INJ', 'FTM', 'ALGO', 'VET', 'SAND', 'MANA',
            'AXS', 'GALA', 'ENJ', 'CRV', 'AAVE', 'MKR', 'SNX', 'COMP'
        ]
        
        # Download progress tracking
        self.download_progress = {
            'running': False,
            'total_coins': 0,
            'completed_coins': 0,
            'current_coin': None,
            'errors': [],
            'started_at': None
        }
    
    def set_api_key(self, api_key: str):
        """Set CryptoCompare API key"""
        self.api_key = api_key
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored OHLCV data"""
        try:
            total_records = await self.db.ohlcv_data.count_documents({})
            
            # Get unique symbols
            symbols = await self.db.ohlcv_data.distinct('symbol')
            
            # Get date range
            oldest = await self.db.ohlcv_data.find_one(
                {}, sort=[('timestamp', 1)], projection={'timestamp': 1, '_id': 0}
            )
            newest = await self.db.ohlcv_data.find_one(
                {}, sort=[('timestamp', -1)], projection={'timestamp': 1, '_id': 0}
            )
            
            # Count per symbol
            pipeline = [
                {'$group': {'_id': '$symbol', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 20}
            ]
            symbol_counts = await self.db.ohlcv_data.aggregate(pipeline).to_list(length=20)
            
            return {
                'total_records': total_records,
                'unique_symbols': len(symbols),
                'symbols': symbols[:30],  # First 30
                'date_range': {
                    'oldest': oldest['timestamp'] if oldest else None,
                    'newest': newest['timestamp'] if newest else None
                },
                'top_symbols': {s['_id']: s['count'] for s in symbol_counts},
                'sufficient_for_training': total_records >= 10000
            }
        except Exception as e:
            logger.error(f"Failed to get OHLCV stats: {e}")
            return {'error': str(e)}
    
    async def download_historical_data(
        self,
        symbols: List[str] = None,
        days: int = 365,
        timeframe: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Download historical OHLCV data for multiple coins
        
        Args:
            symbols: List of coin symbols (default: training_coins)
            days: Number of days of history (default: 365)
            timeframe: 'daily' or 'hourly'
            
        Returns:
            Download status and statistics
        """
        if self.download_progress['running']:
            return {
                'error': 'Download already in progress',
                'progress': self.download_progress
            }
        
        symbols = symbols or self.training_coins
        
        self.download_progress = {
            'running': True,
            'total_coins': len(symbols),
            'completed_coins': 0,
            'current_coin': None,
            'errors': [],
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        total_records = 0
        
        try:
            for i, symbol in enumerate(symbols):
                self.download_progress['current_coin'] = symbol
                self.download_progress['completed_coins'] = i
                
                try:
                    records = await self._download_coin_data(symbol, days, timeframe)
                    total_records += records
                    logger.info(f"✅ Downloaded {records} records for {symbol}")
                except Exception as e:
                    self.download_progress['errors'].append({
                        'symbol': symbol,
                        'error': str(e)
                    })
                    logger.warning(f"⚠️ Failed to download {symbol}: {e}")
                
                # Rate limiting - 50 requests per minute for free tier
                await asyncio.sleep(1.5)
            
            self.download_progress['completed_coins'] = len(symbols)
            self.download_progress['running'] = False
            
            return {
                'success': True,
                'total_records': total_records,
                'coins_processed': len(symbols),
                'errors': self.download_progress['errors'],
                'progress': self.download_progress
            }
            
        except Exception as e:
            self.download_progress['running'] = False
            logger.error(f"Download failed: {e}")
            return {'error': str(e), 'progress': self.download_progress}
    
    async def _download_coin_data(self, symbol: str, days: int, timeframe: str) -> int:
        """Download and store data for a single coin"""
        import httpx
        
        if timeframe == 'hourly':
            endpoint = f"{self.base_url}/histohour"
            limit = min(days * 24, 2000)  # API limit
        else:
            endpoint = f"{self.base_url}/histoday"
            limit = min(days, 2000)
        
        params = {
            'fsym': symbol.upper(),
            'tsym': 'USD',
            'limit': limit,
            'e': 'CCCAGG'  # Aggregated data across exchanges
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(endpoint, params=params)
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
            
            data = response.json()
            
            if data.get('Response') == 'Error':
                raise Exception(data.get('Message', 'Unknown error'))
            
            ohlcv_data = data.get('Data', {}).get('Data', [])
            
            if not ohlcv_data:
                return 0
            
            # Prepare documents for insertion
            documents = []
            for candle in ohlcv_data:
                if candle.get('close', 0) == 0:
                    continue  # Skip empty candles
                
                doc = {
                    'symbol': symbol.upper(),
                    'timestamp': candle['time'],
                    'datetime': datetime.fromtimestamp(candle['time'], tz=timezone.utc),
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle.get('volumefrom', 0),
                    'volume_to': candle.get('volumeto', 0),
                    'timeframe': timeframe,
                    'source': 'cryptocompare',
                    'updated_at': datetime.now(timezone.utc)
                }
                documents.append(doc)
            
            if documents:
                # Use upsert to avoid duplicates
                from pymongo import UpdateOne
                
                operations = [
                    UpdateOne(
                        {'symbol': doc['symbol'], 'timestamp': doc['timestamp'], 'timeframe': doc['timeframe']},
                        {'$set': doc},
                        upsert=True
                    )
                    for doc in documents
                ]
                
                result = await self.db.ohlcv_data.bulk_write(operations, ordered=False)
                return result.upserted_count + result.modified_count
            
            return 0
    
    async def get_training_data(
        self,
        symbols: List[str] = None,
        min_records: int = 100,
        timeframe: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Get OHLCV data formatted for ML/DL training
        
        Args:
            symbols: List of symbols to include
            min_records: Minimum records per symbol
            timeframe: 'daily' or 'hourly'
            
        Returns:
            Training data organized by symbol
        """
        symbols = symbols or self.training_coins[:10]  # Default to top 10
        
        training_data = {}
        
        for symbol in symbols:
            cursor = self.db.ohlcv_data.find(
                {'symbol': symbol.upper(), 'timeframe': timeframe},
                {'_id': 0, 'symbol': 1, 'timestamp': 1, 'open': 1, 'high': 1, 
                 'low': 1, 'close': 1, 'volume': 1}
            ).sort('timestamp', 1)
            
            data = await cursor.to_list(length=5000)
            
            if len(data) >= min_records:
                training_data[symbol] = {
                    'count': len(data),
                    'data': data
                }
        
        return {
            'symbols': list(training_data.keys()),
            'total_records': sum(d['count'] for d in training_data.values()),
            'data': training_data
        }
    
    def get_download_progress(self) -> Dict[str, Any]:
        """Get current download progress"""
        return self.download_progress
    
    async def ensure_indexes(self):
        """Create indexes for efficient queries"""
        try:
            await self.db.ohlcv_data.create_index([('symbol', 1), ('timestamp', -1)])
            await self.db.ohlcv_data.create_index([('symbol', 1), ('timeframe', 1), ('timestamp', -1)])
            await self.db.ohlcv_data.create_index('timestamp')
            logger.info("✅ OHLCV indexes created")
        except Exception as e:
            logger.warning(f"Index creation failed: {e}")


# Singleton
_ohlcv_manager = None

def get_ohlcv_manager(db: AsyncIOMotorDatabase = None) -> OHLCVDataManager:
    global _ohlcv_manager
    if _ohlcv_manager is None and db is not None:
        _ohlcv_manager = OHLCVDataManager(db)
    return _ohlcv_manager
