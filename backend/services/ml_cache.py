"""
ML Caching System
Comprehensive caching for feature engineering, predictions, and training data
"""

import os
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import numpy as np
import pandas as pd

# Try Redis first, fallback to DiskCache
try:
    import redis
    REDIS_AVAILABLE = True
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=False
    )
    # Test connection
    redis_client.ping()
    print("✅ Redis cache available")
except Exception as e:
    REDIS_AVAILABLE = False
    print(f"⚠️ Redis not available, using DiskCache: {e}")
    from diskcache import Cache
    disk_cache = Cache('/tmp/ml_cache', size_limit=2**30)  # 1GB

class MLCache:
    """
    Multi-layer caching system for ML operations
    
    Cache Layers:
    1. Feature Engineering Cache - TTL: 1 hour
    2. Model Prediction Cache - TTL: 5 minutes
    3. Training Data Cache - TTL: 24 hours
    4. Sequence Preparation Cache - TTL: 30 minutes
    """
    
    def __init__(self):
        self.use_redis = REDIS_AVAILABLE
        if self.use_redis:
            self.redis = redis_client
        else:
            self.disk = disk_cache
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments
        
        Args:
            prefix: Cache key prefix (e.g., 'features', 'prediction')
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Unique cache key
        """
        # Create deterministic key from arguments
        key_data = {
            'args': [str(arg) for arg in args],
            'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis:
                data = self.redis.get(key)
                if data:
                    return pickle.loads(data)
            else:
                return self.disk.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            if self.use_redis:
                self.redis.setex(key, ttl, pickle.dumps(value))
            else:
                self.disk.set(key, value, expire=ttl)
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        try:
            if self.use_redis:
                self.redis.delete(key)
            else:
                self.disk.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        try:
            if self.use_redis:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            else:
                # DiskCache doesn't support pattern matching, clear all
                self.disk.clear()
        except Exception as e:
            print(f"Cache clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.use_redis:
                info = self.redis.info()
                return {
                    'type': 'redis',
                    'keys': self.redis.dbsize(),
                    'memory_used': info.get('used_memory_human', 'N/A'),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                }
            else:
                return {
                    'type': 'disk',
                    'size': self.disk.volume(),
                    'keys': len(self.disk),
                }
        except Exception as e:
            return {'error': str(e)}


# Global cache instance
ml_cache = MLCache()


# Decorator for feature engineering cache
def cache_features(ttl: int = 3600):
    """
    Cache feature engineering output
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        
    Usage:
        @cache_features(ttl=3600)
        def calculate_features(symbol, timeframe, data):
            # Expensive feature calculations
            return features
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = ml_cache._generate_key('features', func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached = ml_cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Compute and cache
            result = func(*args, **kwargs)
            ml_cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


# Decorator for model prediction cache
def cache_prediction(ttl: int = 300):
    """
    Cache model predictions
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        
    Usage:
        @cache_prediction(ttl=300)
        def predict(model_name, symbol, features):
            # Expensive model inference
            return prediction
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = ml_cache._generate_key('prediction', func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached = ml_cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Compute and cache
            result = func(*args, **kwargs)
            ml_cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


# Decorator for training data cache
def cache_training_data(ttl: int = 86400):
    """
    Cache pre-processed training data
    
    Args:
        ttl: Time to live in seconds (default: 24 hours)
        
    Usage:
        @cache_training_data(ttl=86400)
        def prepare_training_data(symbols, start_date, end_date):
            # Expensive data preparation
            return X_train, y_train
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = ml_cache._generate_key('training_data', func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached = ml_cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Compute and cache
            result = func(*args, **kwargs)
            ml_cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


# Decorator for sequence preparation cache
def cache_sequences(ttl: int = 1800):
    """
    Cache prepared sequences for time-series models
    
    Args:
        ttl: Time to live in seconds (default: 30 minutes)
        
    Usage:
        @cache_sequences(ttl=1800)
        def prepare_sequences(data, sequence_length, target_col):
            # Expensive sequence preparation
            return X_seq, y_seq
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = ml_cache._generate_key('sequences', func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached = ml_cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Compute and cache
            result = func(*args, **kwargs)
            ml_cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


class FeatureCache:
    """
    Specialized cache for feature engineering
    Handles DataFrames and numpy arrays efficiently
    """
    
    @staticmethod
    def get_technical_indicators(symbol: str, timeframe: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Get cached technical indicators
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (1h, 4h, 1d, etc.)
            data: Price data DataFrame
            
        Returns:
            Cached features or None
        """
        # Create key based on symbol, timeframe, and data hash
        data_hash = hashlib.md5(
            pd.util.hash_pandas_object(data, index=True).values
        ).hexdigest()[:8]
        
        key = f"features:indicators:{symbol}:{timeframe}:{data_hash}"
        return ml_cache.get(key)
    
    @staticmethod
    def set_technical_indicators(
        symbol: str,
        timeframe: str,
        data: pd.DataFrame,
        features: pd.DataFrame,
        ttl: int = 3600
    ):
        """Cache technical indicators"""
        data_hash = hashlib.md5(
            pd.util.hash_pandas_object(data, index=True).values
        ).hexdigest()[:8]
        
        key = f"features:indicators:{symbol}:{timeframe}:{data_hash}"
        ml_cache.set(key, features, ttl=ttl)
    
    @staticmethod
    def get_normalized_features(symbol: str, feature_hash: str) -> Optional[np.ndarray]:
        """Get cached normalized features"""
        key = f"features:normalized:{symbol}:{feature_hash}"
        return ml_cache.get(key)
    
    @staticmethod
    def set_normalized_features(symbol: str, feature_hash: str, features: np.ndarray, ttl: int = 7200):
        """Cache normalized features"""
        key = f"features:normalized:{symbol}:{feature_hash}"
        ml_cache.set(key, features, ttl=ttl)


class PredictionCache:
    """
    Specialized cache for model predictions
    Invalidates when new data arrives
    """
    
    @staticmethod
    def get_prediction(model_name: str, symbol: str, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Get cached prediction
        
        Args:
            model_name: Name of the model
            symbol: Trading pair symbol
            timestamp: Prediction timestamp
            
        Returns:
            Cached prediction or None
        """
        # Round timestamp to nearest minute
        ts_rounded = timestamp.replace(second=0, microsecond=0)
        key = f"prediction:{model_name}:{symbol}:{ts_rounded.isoformat()}"
        return ml_cache.get(key)
    
    @staticmethod
    def set_prediction(
        model_name: str,
        symbol: str,
        timestamp: datetime,
        prediction: Dict[str, Any],
        ttl: int = 300
    ):
        """Cache prediction"""
        ts_rounded = timestamp.replace(second=0, microsecond=0)
        key = f"prediction:{model_name}:{symbol}:{ts_rounded.isoformat()}"
        ml_cache.set(key, prediction, ttl=ttl)
    
    @staticmethod
    def invalidate_symbol(symbol: str):
        """Invalidate all predictions for a symbol"""
        ml_cache.clear_pattern(f"prediction:*:{symbol}:*")


class TrainingDataCache:
    """
    Cache for pre-processed training data
    Reduces expensive database queries and normalization
    """
    
    @staticmethod
    def get_training_data(
        symbols: List[str],
        start_date: str,
        end_date: str,
        features: List[str]
    ) -> Optional[tuple]:
        """
        Get cached training data
        
        Returns:
            (X_train, y_train, scaler) or None
        """
        symbols_key = ",".join(sorted(symbols))
        features_key = ",".join(sorted(features))
        key = f"training:{symbols_key}:{start_date}:{end_date}:{features_key}"
        return ml_cache.get(key)
    
    @staticmethod
    def set_training_data(
        symbols: List[str],
        start_date: str,
        end_date: str,
        features: List[str],
        data: tuple,
        ttl: int = 86400
    ):
        """Cache training data"""
        symbols_key = ",".join(sorted(symbols))
        features_key = ",".join(sorted(features))
        key = f"training:{symbols_key}:{start_date}:{end_date}:{features_key}"
        ml_cache.set(key, data, ttl=ttl)


class SequenceCache:
    """
    Cache for prepared time-series sequences
    Critical for LSTM/Transformer models
    """
    
    @staticmethod
    def get_sequences(
        symbol: str,
        sequence_length: int,
        data_hash: str
    ) -> Optional[tuple]:
        """
        Get cached sequences
        
        Returns:
            (X_sequences, y_sequences) or None
        """
        key = f"sequences:{symbol}:{sequence_length}:{data_hash}"
        return ml_cache.get(key)
    
    @staticmethod
    def set_sequences(
        symbol: str,
        sequence_length: int,
        data_hash: str,
        sequences: tuple,
        ttl: int = 1800
    ):
        """Cache sequences"""
        key = f"sequences:{symbol}:{sequence_length}:{data_hash}"
        ml_cache.set(key, sequences, ttl=ttl)


# Utility functions
def warm_cache_for_symbol(symbol: str, timeframe: str = '1h'):
    """
    Pre-warm cache for a symbol
    Fetches and caches common data
    """
    # This would be called during off-peak hours
    # to prepare cache for trading hours
    pass


def get_cache_stats() -> Dict[str, Any]:
    """Get comprehensive cache statistics"""
    stats = ml_cache.get_stats()
    
    # Add cache effectiveness metrics
    if stats.get('hits') and stats.get('misses'):
        total = stats['hits'] + stats['misses']
        stats['hit_rate'] = f"{(stats['hits'] / total * 100):.2f}%"
    
    return stats


def clear_expired_caches():
    """Clear all expired cache entries (Redis handles this automatically)"""
    if not REDIS_AVAILABLE:
        # DiskCache: manually remove expired
        ml_cache.disk.expire()


def clear_all_caches():
    """Clear ALL caches - use with caution!"""
    ml_cache.clear_pattern('*')


# Health check
def cache_health_check() -> Dict[str, Any]:
    """Check cache health and connectivity"""
    try:
        # Test set/get
        test_key = "health_check"
        test_value = {"timestamp": datetime.utcnow().isoformat()}
        
        ml_cache.set(test_key, test_value, ttl=60)
        retrieved = ml_cache.get(test_key)
        ml_cache.delete(test_key)
        
        return {
            "status": "healthy" if retrieved == test_value else "degraded",
            "cache_type": "redis" if REDIS_AVAILABLE else "disk",
            "read_write": "ok" if retrieved == test_value else "failed",
            "stats": get_cache_stats()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
