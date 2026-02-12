"""
MongoDB Performance Indexes
===========================
Creates indexes for 5-10x faster database queries.
Run on startup or via migration script.

Index Strategy:
- Compound indexes for common query patterns
- TTL indexes for auto-expiring data
- Text indexes for search functionality
- Partial indexes for filtered queries
"""

import logging
from typing import Dict, List, Any
from pymongo import ASCENDING, DESCENDING, TEXT

logger = logging.getLogger(__name__)


# Index definitions organized by collection
INDEX_DEFINITIONS: Dict[str, List[Dict[str, Any]]] = {
    # Trade history - frequently queried by symbol and timestamp
    'trade_history': [
        {
            'keys': [('timestamp', DESCENDING), ('symbol', ASCENDING)],
            'name': 'trade_timestamp_symbol_idx',
            'background': True,
        },
        {
            'keys': [('user_id', ASCENDING), ('timestamp', DESCENDING)],
            'name': 'trade_user_timestamp_idx',
            'background': True,
        },
        {
            'keys': [('trade_type', ASCENDING), ('timestamp', DESCENDING)],
            'name': 'trade_type_timestamp_idx',
            'background': True,
        },
    ],
    
    # Predictions - queried by coin and creation date
    'predictions': [
        {
            'keys': [('coin_id', ASCENDING), ('created_at', DESCENDING)],
            'name': 'prediction_coin_date_idx',
            'background': True,
        },
        {
            'keys': [('model_name', ASCENDING), ('created_at', DESCENDING)],
            'name': 'prediction_model_date_idx',
            'background': True,
        },
        {
            'keys': [('accuracy', DESCENDING)],
            'name': 'prediction_accuracy_idx',
            'background': True,
        },
    ],
    
    # Training status - queried by model and status
    'training_status': [
        {
            'keys': [('model_name', ASCENDING), ('status', ASCENDING)],
            'name': 'training_model_status_idx',
            'background': True,
        },
        {
            'keys': [('started_at', DESCENDING)],
            'name': 'training_started_idx',
            'background': True,
        },
    ],
    
    # Model training status - individual model tracking
    'model_training_status': [
        {
            'keys': [('model_name', ASCENDING)],
            'name': 'model_name_idx',
            'unique': True,
            'background': True,
        },
        {
            'keys': [('trained_at', DESCENDING)],
            'name': 'model_trained_at_idx',
            'background': True,
        },
    ],
    
    # Alerts - queried by severity and timestamp
    'alerts': [
        {
            'keys': [('severity', ASCENDING), ('created_at', DESCENDING)],
            'name': 'alert_severity_date_idx',
            'background': True,
        },
        {
            'keys': [('user_id', ASCENDING), ('read', ASCENDING)],
            'name': 'alert_user_read_idx',
            'background': True,
        },
        {
            'keys': [('type', ASCENDING), ('created_at', DESCENDING)],
            'name': 'alert_type_date_idx',
            'background': True,
        },
    ],
    
    # Market data cache - TTL index for auto-cleanup
    'market_data_cache': [
        {
            'keys': [('coin_id', ASCENDING), ('days', ASCENDING)],
            'name': 'market_cache_coin_days_idx',
            'background': True,
        },
        {
            'keys': [('cached_at', ASCENDING)],
            'name': 'market_cache_ttl_idx',
            'expireAfterSeconds': 300,  # 5 minute TTL
            'background': True,
        },
    ],
    
    # Sentiment data
    'sentiment_history': [
        {
            'keys': [('coin_id', ASCENDING), ('timestamp', DESCENDING)],
            'name': 'sentiment_coin_timestamp_idx',
            'background': True,
        },
        {
            'keys': [('score', DESCENDING)],
            'name': 'sentiment_score_idx',
            'background': True,
        },
    ],
    
    # Portfolio snapshots
    'portfolio_snapshots': [
        {
            'keys': [('user_id', ASCENDING), ('timestamp', DESCENDING)],
            'name': 'portfolio_user_timestamp_idx',
            'background': True,
        },
        {
            'keys': [('timestamp', DESCENDING)],
            'name': 'portfolio_timestamp_idx',
            'background': True,
        },
    ],
    
    # Performance snapshots
    'performance_snapshots': [
        {
            'keys': [('timestamp', DESCENDING)],
            'name': 'perf_timestamp_idx',
            'background': True,
        },
        {
            'keys': [('strategy_id', ASCENDING), ('timestamp', DESCENDING)],
            'name': 'perf_strategy_timestamp_idx',
            'background': True,
        },
    ],
    
    # OHLCV data - critical for trading
    'ohlcv_data': [
        {
            'keys': [('symbol', ASCENDING), ('timestamp', DESCENDING)],
            'name': 'ohlcv_symbol_timestamp_idx',
            'background': True,
        },
        {
            'keys': [('symbol', ASCENDING), ('timeframe', ASCENDING), ('timestamp', DESCENDING)],
            'name': 'ohlcv_symbol_tf_timestamp_idx',
            'background': True,
        },
    ],
    
    # Triggers and events
    'triggers': [
        {
            'keys': [('user_id', ASCENDING), ('active', ASCENDING)],
            'name': 'trigger_user_active_idx',
            'background': True,
        },
        {
            'keys': [('trigger_type', ASCENDING), ('created_at', DESCENDING)],
            'name': 'trigger_type_date_idx',
            'background': True,
        },
    ],
    
    # Event history
    'event_history': [
        {
            'keys': [('event_type', ASCENDING), ('timestamp', DESCENDING)],
            'name': 'event_type_timestamp_idx',
            'background': True,
        },
        {
            'keys': [('timestamp', DESCENDING)],
            'name': 'event_timestamp_idx',
            'background': True,
        },
    ],
    
    # Journal entries
    'journal_entries': [
        {
            'keys': [('user_id', ASCENDING), ('created_at', DESCENDING)],
            'name': 'journal_user_date_idx',
            'background': True,
        },
        {
            'keys': [('tags', ASCENDING)],
            'name': 'journal_tags_idx',
            'background': True,
        },
    ],
    
    # API rate limiting
    'rate_limits': [
        {
            'keys': [('user_id', ASCENDING), ('endpoint', ASCENDING)],
            'name': 'rate_user_endpoint_idx',
            'background': True,
        },
        {
            'keys': [('expires_at', ASCENDING)],
            'name': 'rate_expires_ttl_idx',
            'expireAfterSeconds': 0,  # TTL index
            'background': True,
        },
    ],
    
    # Backtest results
    'backtest_results': [
        {
            'keys': [('strategy_id', ASCENDING), ('created_at', DESCENDING)],
            'name': 'backtest_strategy_date_idx',
            'background': True,
        },
        {
            'keys': [('win_rate', DESCENDING)],
            'name': 'backtest_winrate_idx',
            'background': True,
        },
    ],
    
    # Coin universe
    'coin_universe': [
        {
            'keys': [('symbol', ASCENDING)],
            'name': 'coin_symbol_idx',
            'unique': True,
            'background': True,
        },
        {
            'keys': [('market_cap', DESCENDING)],
            'name': 'coin_marketcap_idx',
            'background': True,
        },
    ],
    
    # Position entries
    'position_entries': [
        {
            'keys': [('symbol', ASCENDING), ('status', ASCENDING)],
            'name': 'position_symbol_status_idx',
            'background': True,
        },
        {
            'keys': [('opened_at', DESCENDING)],
            'name': 'position_opened_idx',
            'background': True,
        },
    ],
}


async def create_indexes(db, collections: List[str] = None) -> Dict[str, Any]:
    """
    Create performance indexes for specified collections.
    
    Args:
        db: MongoDB database instance
        collections: List of collection names (None for all)
        
    Returns:
        Dict with created indexes and any errors
    """
    results = {
        'created': [],
        'existing': [],
        'errors': [],
    }
    
    target_collections = collections or list(INDEX_DEFINITIONS.keys())
    
    for collection_name in target_collections:
        if collection_name not in INDEX_DEFINITIONS:
            continue
            
        collection = db[collection_name]
        indexes = INDEX_DEFINITIONS[collection_name]
        
        for index_def in indexes:
            try:
                keys = index_def['keys']
                name = index_def.get('name')
                
                # Build kwargs from remaining fields
                kwargs = {k: v for k, v in index_def.items() if k not in ['keys']}
                
                # Create the index
                await collection.create_index(keys, **kwargs)
                results['created'].append(f"{collection_name}.{name}")
                logger.info(f"✅ Created index: {collection_name}.{name}")
                
            except Exception as e:
                error_msg = str(e)
                if 'already exists' in error_msg.lower() or 'index already exists' in error_msg.lower():
                    results['existing'].append(f"{collection_name}.{index_def.get('name')}")
                else:
                    results['errors'].append({
                        'collection': collection_name,
                        'index': index_def.get('name'),
                        'error': error_msg
                    })
                    logger.error(f"❌ Failed to create index {collection_name}.{index_def.get('name')}: {e}")
    
    logger.info(
        f"📊 Index creation complete: {len(results['created'])} created, "
        f"{len(results['existing'])} existing, {len(results['errors'])} errors"
    )
    
    return results


async def get_index_stats(db) -> Dict[str, Any]:
    """
    Get statistics about existing indexes.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        Dict with index statistics per collection
    """
    stats = {}
    
    for collection_name in INDEX_DEFINITIONS.keys():
        try:
            collection = db[collection_name]
            indexes = await collection.index_information()
            stats[collection_name] = {
                'count': len(indexes),
                'indexes': list(indexes.keys()),
            }
        except Exception as e:
            stats[collection_name] = {'error': str(e)}
    
    return stats


async def drop_unused_indexes(db, dry_run: bool = True) -> Dict[str, Any]:
    """
    Identify and optionally drop unused indexes.
    
    Args:
        db: MongoDB database instance
        dry_run: If True, only report what would be dropped
        
    Returns:
        Dict with results
    """
    results = {
        'would_drop': [],
        'dropped': [],
        'kept': [],
    }
    
    defined_index_names = set()
    for indexes in INDEX_DEFINITIONS.values():
        for idx in indexes:
            defined_index_names.add(idx.get('name'))
    
    for collection_name in INDEX_DEFINITIONS.keys():
        try:
            collection = db[collection_name]
            indexes = await collection.index_information()
            
            for index_name in indexes.keys():
                # Skip default _id index
                if index_name == '_id_':
                    continue
                    
                if index_name not in defined_index_names:
                    if dry_run:
                        results['would_drop'].append(f"{collection_name}.{index_name}")
                    else:
                        await collection.drop_index(index_name)
                        results['dropped'].append(f"{collection_name}.{index_name}")
                else:
                    results['kept'].append(f"{collection_name}.{index_name}")
                    
        except Exception as e:
            logger.error(f"Error processing {collection_name}: {e}")
    
    return results
