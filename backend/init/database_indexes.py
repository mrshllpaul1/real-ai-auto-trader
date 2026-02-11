"""
Database Index Initialization
Creates optimized compound indexes for frequently queried collections
"""

import logging
from config.database import db

logger = logging.getLogger(__name__)


async def ensure_database_indexes():
    """
    Create compound indexes for performance optimization
    These indexes significantly improve query performance for common access patterns
    """
    
    index_definitions = {
        # OHLCV data - most frequently queried with symbol + timestamp
        'ohlcv_data': [
            {'keys': [('symbol', 1), ('timestamp', -1)], 'name': 'symbol_timestamp_idx'},
            {'keys': [('interval', 1), ('timestamp', -1)], 'name': 'interval_timestamp_idx'},
            {'keys': [('symbol', 1), ('interval', 1), ('timestamp', -1)], 'name': 'symbol_interval_timestamp_idx'},
        ],
        
        # Trades collection - queries by symbol, status, and timestamp
        'trades': [
            {'keys': [('symbol', 1), ('status', 1), ('timestamp', -1)], 'name': 'symbol_status_timestamp_idx'},
            {'keys': [('user_id', 1), ('timestamp', -1)], 'name': 'user_timestamp_idx'},
            {'keys': [('strategy_id', 1), ('timestamp', -1)], 'name': 'strategy_timestamp_idx'},
        ],
        
        # Performance snapshots - time-series data
        'performance_snapshots': [
            {'keys': [('timestamp', -1)], 'name': 'timestamp_desc_idx'},
            {'keys': [('portfolio_id', 1), ('timestamp', -1)], 'name': 'portfolio_timestamp_idx'},
        ],
        
        # Sentiment history - queried by coin and time range
        'sentiment_history': [
            {'keys': [('coin', 1), ('timestamp', -1)], 'name': 'coin_timestamp_idx'},
            {'keys': [('source', 1), ('timestamp', -1)], 'name': 'source_timestamp_idx'},
        ],
        
        # Training history - model performance tracking
        'training_history': [
            {'keys': [('model_name', 1), ('timestamp', -1)], 'name': 'model_timestamp_idx'},
            {'keys': [('status', 1), ('timestamp', -1)], 'name': 'status_timestamp_idx'},
        ],
        
        # Position entries - portfolio tracking
        'position_entries': [
            {'keys': [('symbol', 1), ('status', 1)], 'name': 'symbol_status_idx'},
            {'keys': [('portfolio_id', 1), ('status', 1)], 'name': 'portfolio_status_idx'},
        ],
        
        # Gem scans - discovery queries
        'gem_scans': [
            {'keys': [('timestamp', -1)], 'name': 'timestamp_desc_idx'},
            {'keys': [('status', 1), ('timestamp', -1)], 'name': 'status_timestamp_idx'},
        ],
        
        # Strategies - user and status queries
        'strategies': [
            {'keys': [('user_id', 1), ('active', 1)], 'name': 'user_active_idx'},
            {'keys': [('created_at', -1)], 'name': 'created_desc_idx'},
        ],
        
        # News articles - sentiment and time-based queries
        'news_articles': [
            {'keys': [('symbol', 1), ('published_at', -1)], 'name': 'symbol_published_idx'},
            {'keys': [('sentiment_score', -1), ('published_at', -1)], 'name': 'sentiment_published_idx'},
        ],
        
        # Whale transactions - tracking large movements
        'whale_transactions': [
            {'keys': [('symbol', 1), ('timestamp', -1)], 'name': 'symbol_timestamp_idx'},
            {'keys': [('amount_usd', -1), ('timestamp', -1)], 'name': 'amount_timestamp_idx'},
        ],
        
        # Backtest results - strategy evaluation
        'backtest_results': [
            {'keys': [('strategy_id', 1), ('created_at', -1)], 'name': 'strategy_created_idx'},
            {'keys': [('symbol', 1), ('created_at', -1)], 'name': 'symbol_created_idx'},
        ],
        
        # API keys - user authentication
        'api_keys': [
            {'keys': [('user_id', 1), ('active', 1)], 'name': 'user_active_idx'},
            {'keys': [('key_hash', 1)], 'name': 'key_hash_idx', 'unique': True},
        ],
        
        # Alerts - notification system
        'alerts': [
            {'keys': [('user_id', 1), ('status', 1), ('created_at', -1)], 'name': 'user_status_created_idx'},
            {'keys': [('symbol', 1), ('alert_type', 1)], 'name': 'symbol_type_idx'},
        ],
    }
    
    total_created = 0
    total_existing = 0
    
    for collection_name, indexes in index_definitions.items():
        collection = db[collection_name]
        
        try:
            for index_def in indexes:
                keys = index_def['keys']
                name = index_def['name']
                unique = index_def.get('unique', False)
                
                try:
                    # Check if index already exists
                    existing_indexes = await collection.index_information()
                    
                    if name in existing_indexes:
                        total_existing += 1
                        logger.debug(f"Index '{name}' already exists on '{collection_name}'")
                    else:
                        # Create the index
                        await collection.create_index(
                            keys,
                            name=name,
                            unique=unique,
                            background=True  # Non-blocking index creation
                        )
                        total_created += 1
                        logger.info(f"✅ Created index '{name}' on '{collection_name}'")
                        
                except Exception as e:
                    logger.warning(f"Failed to create index '{name}' on '{collection_name}': {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to process collection '{collection_name}': {e}")
    
    logger.info(f"✅ Database indexing complete: {total_created} created, {total_existing} existing")
    
    return {
        'created': total_created,
        'existing': total_existing,
        'total_collections': len(index_definitions)
    }


async def get_index_stats():
    """
    Get statistics about database indexes
    Returns index counts and sizes for monitoring
    """
    stats = {}
    
    try:
        collections = await db.list_collection_names()
        
        for collection_name in collections:
            collection = db[collection_name]
            
            try:
                # Get index information
                indexes = await collection.index_information()
                index_count = len(indexes)
                
                # Get collection stats
                coll_stats = await db.command('collStats', collection_name)
                total_index_size = coll_stats.get('totalIndexSize', 0)
                
                stats[collection_name] = {
                    'index_count': index_count,
                    'total_index_size_bytes': total_index_size,
                    'total_index_size_mb': round(total_index_size / (1024 * 1024), 2),
                    'indexes': list(indexes.keys())
                }
                
            except Exception as e:
                logger.debug(f"Could not get stats for '{collection_name}': {e}")
                
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        
    return stats


async def analyze_slow_queries():
    """
    Analyze database for slow queries
    Returns recommendations for additional indexes
    """
    # Maximum length for command output in recommendations
    MAX_COMMAND_LENGTH = 200
    
    recommendations = []
    
    try:
        # Enable profiling if not already enabled (level 1 = slow queries only)
        profile_level = await db.command('profile', -1)
        
        if profile_level.get('was', 0) == 0:
            logger.info("Enabling database profiling for slow query analysis...")
            await db.command('profile', 1, slowms=100)  # Log queries > 100ms
        
        # Get slow queries from system.profile
        slow_queries = await db.system.profile.find(
            {'millis': {'$gt': 100}},
            {'ns': 1, 'op': 1, 'command': 1, 'millis': 1}
        ).limit(50).to_list(length=50)
        
        for query in slow_queries:
            recommendations.append({
                'collection': query.get('ns', '').split('.')[-1],
                'operation': query.get('op'),
                'duration_ms': query.get('millis'),
                'command': str(query.get('command', {}))[:MAX_COMMAND_LENGTH]  # Truncate for readability
            })
            
        logger.info(f"Found {len(slow_queries)} slow queries for analysis")
        
    except Exception as e:
        logger.warning(f"Could not analyze slow queries: {e}")
        
    return recommendations


# Export main function for initialization
__all__ = ['ensure_database_indexes', 'get_index_stats', 'analyze_slow_queries']
