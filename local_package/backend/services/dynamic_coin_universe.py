"""
Dynamic Coin Universe Manager
Allows AI to discover and add new coins to the trading universe.
Stores universe in database for persistence and dynamic updates.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Default categories for coin classification
CATEGORIES = {
    'major': 'Blue chip cryptocurrencies (BTC, ETH, etc.)',
    'large': 'Large cap, relatively safe investments',
    'mid': 'Mid cap Layer 1s and Layer 2s',
    'defi': 'DeFi protocols and tokens',
    'gaming': 'Gaming and metaverse tokens',
    'infra': 'Infrastructure tokens (oracles, storage)',
    'privacy': 'Privacy-focused coins',
    'exchange': 'Exchange tokens',
    'meme': 'Meme coins - high risk/reward',
    'ai': 'AI and machine learning tokens',
    'bridge': 'Cross-chain bridge tokens',
    'storage': 'Decentralized storage',
    'older': 'Older altcoins',
    'new': 'New projects (2023-2024)',
    'discovered': 'AI-discovered coins'
}

# Base universe - will be loaded into DB on first run
BASE_UNIVERSE = {
    # Major coins (Top 10)
    'bitcoin': {'symbol': 'BTC', 'category': 'major', 'launch': '2009-01-03'},
    'ethereum': {'symbol': 'ETH', 'category': 'major', 'launch': '2015-07-30'},
    'ripple': {'symbol': 'XRP', 'category': 'major', 'launch': '2012-01-01'},
    'litecoin': {'symbol': 'LTC', 'category': 'major', 'launch': '2011-10-07'},
    'cardano': {'symbol': 'ADA', 'category': 'major', 'launch': '2017-09-29'},
    'solana': {'symbol': 'SOL', 'category': 'major', 'launch': '2020-04-10'},
    'polkadot': {'symbol': 'DOT', 'category': 'major', 'launch': '2020-05-26'},
    'dogecoin': {'symbol': 'DOGE', 'category': 'major', 'launch': '2013-12-06'},
    'avalanche': {'symbol': 'AVAX', 'category': 'major', 'launch': '2020-09-21'},
    'chainlink': {'symbol': 'LINK', 'category': 'major', 'launch': '2017-09-19'},
    
    # Large caps
    'binancecoin': {'symbol': 'BNB', 'category': 'large', 'launch': '2017-07-25'},
    'tron': {'symbol': 'TRX', 'category': 'large', 'launch': '2017-08-28'},
    'polygon': {'symbol': 'MATIC', 'category': 'large', 'launch': '2019-04-22'},
    'shiba-inu': {'symbol': 'SHIB', 'category': 'large', 'launch': '2020-08-01'},
    'uniswap': {'symbol': 'UNI', 'category': 'large', 'launch': '2020-09-17'},
    'cosmos': {'symbol': 'ATOM', 'category': 'large', 'launch': '2019-03-14'},
    'stellar': {'symbol': 'XLM', 'category': 'large', 'launch': '2014-07-31'},
    'monero': {'symbol': 'XMR', 'category': 'large', 'launch': '2014-04-18'},
    'ethereum-classic': {'symbol': 'ETC', 'category': 'large', 'launch': '2016-07-20'},
    'bitcoin-cash': {'symbol': 'BCH', 'category': 'large', 'launch': '2017-08-01'},
    
    # Mid caps
    'near': {'symbol': 'NEAR', 'category': 'mid', 'launch': '2020-04-22'},
    'aptos': {'symbol': 'APT', 'category': 'mid', 'launch': '2022-10-12'},
    'sui': {'symbol': 'SUI', 'category': 'mid', 'launch': '2023-05-03'},
    'algorand': {'symbol': 'ALGO', 'category': 'mid', 'launch': '2019-06-20'},
    'fantom': {'symbol': 'FTM', 'category': 'mid', 'launch': '2018-06-15'},
    'hedera': {'symbol': 'HBAR', 'category': 'mid', 'launch': '2019-09-16'},
    'internet-computer': {'symbol': 'ICP', 'category': 'mid', 'launch': '2021-05-10'},
    'vechain': {'symbol': 'VET', 'category': 'mid', 'launch': '2017-08-22'},
    'tezos': {'symbol': 'XTZ', 'category': 'mid', 'launch': '2018-06-30'},
    'eos': {'symbol': 'EOS', 'category': 'mid', 'launch': '2017-07-01'},
    'arbitrum': {'symbol': 'ARB', 'category': 'mid', 'launch': '2021-08-31'},
    'optimism': {'symbol': 'OP', 'category': 'mid', 'launch': '2021-12-16'},
    'immutable-x': {'symbol': 'IMX', 'category': 'mid', 'launch': '2021-04-08'},
    'starknet': {'symbol': 'STRK', 'category': 'mid', 'launch': '2024-02-20'},
    
    # DeFi
    'aave': {'symbol': 'AAVE', 'category': 'defi', 'launch': '2020-10-02'},
    'maker': {'symbol': 'MKR', 'category': 'defi', 'launch': '2017-12-18'},
    'compound': {'symbol': 'COMP', 'category': 'defi', 'launch': '2020-06-16'},
    'curve-dao-token': {'symbol': 'CRV', 'category': 'defi', 'launch': '2020-08-13'},
    'lido-dao': {'symbol': 'LDO', 'category': 'defi', 'launch': '2021-01-05'},
    'synthetix': {'symbol': 'SNX', 'category': 'defi', 'launch': '2018-02-28'},
    'yearn-finance': {'symbol': 'YFI', 'category': 'defi', 'launch': '2020-07-17'},
    'pancakeswap-token': {'symbol': 'CAKE', 'category': 'defi', 'launch': '2020-09-28'},
    '1inch': {'symbol': '1INCH', 'category': 'defi', 'launch': '2020-12-25'},
    'sushi': {'symbol': 'SUSHI', 'category': 'defi', 'launch': '2020-08-28'},
    'frax-share': {'symbol': 'FXS', 'category': 'defi', 'launch': '2020-12-21'},
    'convex-finance': {'symbol': 'CVX', 'category': 'defi', 'launch': '2021-05-17'},
    'gmx': {'symbol': 'GMX', 'category': 'defi', 'launch': '2021-09-01'},
    'dydx': {'symbol': 'DYDX', 'category': 'defi', 'launch': '2021-09-08'},
    'rocket-pool': {'symbol': 'RPL', 'category': 'defi', 'launch': '2017-11-16'},
    
    # Gaming/Metaverse
    'the-sandbox': {'symbol': 'SAND', 'category': 'gaming', 'launch': '2020-08-14'},
    'decentraland': {'symbol': 'MANA', 'category': 'gaming', 'launch': '2017-09-17'},
    'axie-infinity': {'symbol': 'AXS', 'category': 'gaming', 'launch': '2020-11-04'},
    'gala': {'symbol': 'GALA', 'category': 'gaming', 'launch': '2020-09-16'},
    'enjincoin': {'symbol': 'ENJ', 'category': 'gaming', 'launch': '2017-11-01'},
    'illuvium': {'symbol': 'ILV', 'category': 'gaming', 'launch': '2021-03-30'},
    'render-token': {'symbol': 'RNDR', 'category': 'gaming', 'launch': '2017-10-05'},
    'beam': {'symbol': 'BEAM', 'category': 'gaming', 'launch': '2023-10-26'},
    
    # AI/ML
    'fetch-ai': {'symbol': 'FET', 'category': 'ai', 'launch': '2019-02-25'},
    'singularitynet': {'symbol': 'AGIX', 'category': 'ai', 'launch': '2017-12-21'},
    'ocean-protocol': {'symbol': 'OCEAN', 'category': 'ai', 'launch': '2019-05-06'},
    'bittensor': {'symbol': 'TAO', 'category': 'ai', 'launch': '2021-01-03'},
    'worldcoin': {'symbol': 'WLD', 'category': 'ai', 'launch': '2023-07-24'},
    'akash-network': {'symbol': 'AKT', 'category': 'ai', 'launch': '2020-09-25'},
    'artificial-superintelligence-alliance': {'symbol': 'ASI', 'category': 'ai', 'launch': '2024-07-01'},
    
    # Meme coins
    'pepe': {'symbol': 'PEPE', 'category': 'meme', 'launch': '2023-04-17'},
    'floki': {'symbol': 'FLOKI', 'category': 'meme', 'launch': '2021-06-28'},
    'bonk': {'symbol': 'BONK', 'category': 'meme', 'launch': '2022-12-25'},
    'dogwifcoin': {'symbol': 'WIF', 'category': 'meme', 'launch': '2023-11-20'},
    'brett': {'symbol': 'BRETT', 'category': 'meme', 'launch': '2024-02-27'},
    
    # New projects (2023-2024)
    'jupiter': {'symbol': 'JUP', 'category': 'new', 'launch': '2024-01-31'},
    'celestia': {'symbol': 'TIA', 'category': 'new', 'launch': '2023-10-31'},
    'sei': {'symbol': 'SEI', 'category': 'new', 'launch': '2023-08-15'},
    'pyth-network': {'symbol': 'PYTH', 'category': 'new', 'launch': '2023-11-20'},
    'jito': {'symbol': 'JTO', 'category': 'new', 'launch': '2023-12-07'},
    'eigenlayer': {'symbol': 'EIGEN', 'category': 'new', 'launch': '2024-05-10'},
    'ethena': {'symbol': 'ENA', 'category': 'new', 'launch': '2024-04-02'},
    'wormhole': {'symbol': 'W', 'category': 'new', 'launch': '2024-04-03'},
}


class DynamicCoinUniverseManager:
    """
    Manages a dynamic coin universe that can be expanded by AI.
    Stores coins in MongoDB for persistence.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.coin_universe
        self._initialized = False
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the universe from base coins if empty"""
        count = await self.collection.count_documents({})
        
        if count == 0:
            logger.info("🌌 Initializing coin universe from base...")
            coins_to_insert = []
            for coin_id, info in BASE_UNIVERSE.items():
                coins_to_insert.append({
                    'coin_id': coin_id,
                    'symbol': info['symbol'],
                    'category': info['category'],
                    'launch': info.get('launch'),
                    'added_by': 'system',
                    'added_at': datetime.utcnow().isoformat(),
                    'active': True,
                    'ai_discovered': False
                })
            
            await self.collection.insert_many(coins_to_insert)
            logger.info(f"  ✅ Loaded {len(coins_to_insert)} base coins")
            return {'initialized': True, 'coins_loaded': len(coins_to_insert)}
        
        logger.info(f"🌌 Coin universe has {count} coins")
        self._initialized = True
        return {'initialized': True, 'coins_count': count}
    
    async def get_all_coins(self) -> List[str]:
        """Get all active coin IDs"""
        coins = await self.collection.find(
            {'active': True},
            {'coin_id': 1, '_id': 0}
        ).to_list(500)
        return [c['coin_id'] for c in coins]
    
    async def get_training_coins(self) -> List[str]:
        """Get all coins for training, sorted by priority"""
        priority_order = ['major', 'large', 'mid', 'defi', 'ai', 'gaming', 'infra', 'new', 'meme', 'bridge', 'storage', 'exchange', 'privacy', 'older', 'discovered']
        
        all_coins = []
        for category in priority_order:
            coins = await self.collection.find(
                {'active': True, 'category': category},
                {'coin_id': 1, '_id': 0}
            ).to_list(100)
            all_coins.extend([c['coin_id'] for c in coins])
        
        # Add any remaining
        remaining = await self.collection.find(
            {'active': True, 'coin_id': {'$nin': all_coins}},
            {'coin_id': 1, '_id': 0}
        ).to_list(100)
        all_coins.extend([c['coin_id'] for c in remaining])
        
        return all_coins
    
    async def get_gem_candidates(self) -> List[str]:
        """Get coins that could be gems (high risk/reward)"""
        gem_categories = ['meme', 'ai', 'new', 'gaming', 'discovered']
        coins = await self.collection.find(
            {'active': True, 'category': {'$in': gem_categories}},
            {'coin_id': 1, '_id': 0}
        ).to_list(100)
        return [c['coin_id'] for c in coins]
    
    async def get_coins_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all coins in a category"""
        coins = await self.collection.find(
            {'active': True, 'category': category},
            {'_id': 0}
        ).to_list(100)
        return coins
    
    async def get_coin(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific coin"""
        return await self.collection.find_one(
            {'coin_id': coin_id},
            {'_id': 0}
        )
    
    async def add_coin(
        self,
        coin_id: str,
        symbol: str,
        category: str = 'discovered',
        added_by: str = 'ai',
        reason: str = None,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        Add a new coin to the universe.
        Can be called by AI when it discovers promising coins.
        """
        # Check if already exists
        existing = await self.collection.find_one({'coin_id': coin_id})
        if existing:
            return {
                'success': False,
                'error': f'{coin_id} already exists in universe',
                'existing': existing
            }
        
        coin_doc = {
            'coin_id': coin_id,
            'symbol': symbol.upper(),
            'category': category,
            'added_by': added_by,
            'added_at': datetime.utcnow().isoformat(),
            'active': True,
            'ai_discovered': added_by == 'ai',
            'discovery_reason': reason,
            'metadata': metadata or {}
        }
        
        await self.collection.insert_one(coin_doc)
        
        logger.info(f"🆕 Added {coin_id} ({symbol}) to universe by {added_by}")
        
        return {
            'success': True,
            'coin_id': coin_id,
            'symbol': symbol,
            'category': category,
            'message': f'{symbol} added to coin universe'
        }
    
    async def ai_discover_coin(
        self,
        coin_id: str,
        symbol: str,
        reason: str,
        potential_score: float = 0,
        market_cap: float = None,
        volume_24h: float = None
    ) -> Dict[str, Any]:
        """
        AI-driven coin discovery.
        Called when AI identifies a promising new coin.
        """
        return await self.add_coin(
            coin_id=coin_id,
            symbol=symbol,
            category='discovered',
            added_by='ai',
            reason=reason,
            metadata={
                'potential_score': potential_score,
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'discovered_at': datetime.utcnow().isoformat()
            }
        )
    
    async def update_coin(
        self,
        coin_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a coin's information"""
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        result = await self.collection.update_one(
            {'coin_id': coin_id},
            {'$set': updates}
        )
        
        if result.modified_count > 0:
            return {'success': True, 'coin_id': coin_id, 'updated': True}
        return {'success': False, 'error': f'{coin_id} not found'}
    
    async def deactivate_coin(self, coin_id: str, reason: str = None) -> Dict[str, Any]:
        """Deactivate a coin (soft delete)"""
        return await self.update_coin(coin_id, {
            'active': False,
            'deactivated_reason': reason
        })
    
    async def get_ai_discovered_coins(self) -> List[Dict[str, Any]]:
        """Get all coins discovered by AI"""
        coins = await self.collection.find(
            {'ai_discovered': True},
            {'_id': 0}
        ).to_list(100)
        return coins
    
    async def get_universe_stats(self) -> Dict[str, Any]:
        """Get statistics about the coin universe"""
        total = await self.collection.count_documents({'active': True})
        ai_discovered = await self.collection.count_documents({'ai_discovered': True, 'active': True})
        
        # Count by category
        pipeline = [
            {'$match': {'active': True}},
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        category_counts = await self.collection.aggregate(pipeline).to_list(20)
        
        return {
            'total_coins': total,
            'ai_discovered': ai_discovered,
            'human_added': total - ai_discovered,
            'by_category': {c['_id']: c['count'] for c in category_counts},
            'categories': list(CATEGORIES.keys())
        }


# Singleton instance (will be initialized with db in server.py)
_universe_manager = None

def get_universe_manager() -> DynamicCoinUniverseManager:
    """Get the singleton universe manager"""
    global _universe_manager
    return _universe_manager

def set_universe_manager(manager: DynamicCoinUniverseManager):
    """Set the singleton universe manager"""
    global _universe_manager
    _universe_manager = manager


# Legacy compatibility functions
async def get_all_coins() -> List[str]:
    """Legacy function - get all coins"""
    if _universe_manager:
        return await _universe_manager.get_all_coins()
    return list(BASE_UNIVERSE.keys())

async def get_training_coins() -> List[str]:
    """Legacy function - get training coins"""
    if _universe_manager:
        return await _universe_manager.get_training_coins()
    return list(BASE_UNIVERSE.keys())

async def get_gem_candidates() -> List[str]:
    """Legacy function - get gem candidates"""
    if _universe_manager:
        return await _universe_manager.get_gem_candidates()
    gem_categories = ['meme', 'ai', 'new', 'gaming']
    return [k for k, v in BASE_UNIVERSE.items() if v['category'] in gem_categories]
