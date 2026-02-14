"""
Database Configuration
Central configuration for MongoDB connection with optimized connection pooling
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'crypto_trading_db')

# Connection Pooling Configuration for 3-5x faster queries
POOL_CONFIG = {
    'minPoolSize': int(os.environ.get('MONGO_MIN_POOL_SIZE', '10')),
    'maxPoolSize': int(os.environ.get('MONGO_MAX_POOL_SIZE', '100')),
    'maxIdleTimeMS': int(os.environ.get('MONGO_MAX_IDLE_TIME_MS', '30000')),
    'waitQueueTimeoutMS': int(os.environ.get('MONGO_WAIT_QUEUE_TIMEOUT_MS', '5000')),
    'connectTimeoutMS': int(os.environ.get('MONGO_CONNECT_TIMEOUT_MS', '10000')),
    'socketTimeoutMS': int(os.environ.get('MONGO_SOCKET_TIMEOUT_MS', '45000')),
    'serverSelectionTimeoutMS': int(os.environ.get('MONGO_SERVER_SELECTION_TIMEOUT_MS', '10000')),
    'retryWrites': True,
    'retryReads': True,
    'w': 'majority',
    'readPreference': 'primaryPreferred',
}

# Create client with optimized pooling
client = AsyncIOMotorClient(
    MONGO_URL,
    **POOL_CONFIG
)
db = client[DB_NAME]

logger.info(f"✅ MongoDB connection pool configured: min={POOL_CONFIG['minPoolSize']}, max={POOL_CONFIG['maxPoolSize']}")


def get_db():
    """Get database instance"""
    return db


def get_client():
    """Get MongoDB client"""
    return client


async def get_pool_stats():
    """Get connection pool statistics"""
    try:
        server_status = await client.admin.command('serverStatus')
        return {
            'current_connections': server_status.get('connections', {}).get('current', 0),
            'available_connections': server_status.get('connections', {}).get('available', 0),
            'total_created': server_status.get('connections', {}).get('totalCreated', 0),
            'pool_config': {
                'min_pool_size': POOL_CONFIG['minPoolSize'],
                'max_pool_size': POOL_CONFIG['maxPoolSize'],
                'max_idle_time_ms': POOL_CONFIG['maxIdleTimeMS'],
            }
        }
    except Exception as e:
        logger.error(f"Failed to get pool stats: {e}")
        return {'error': str(e)}


async def health_check():
    """Check database health and connection pool status"""
    try:
        await client.admin.command('ping')
        pool_stats = await get_pool_stats()
        return {
            'status': 'healthy',
            'connected': True,
            'pool_stats': pool_stats
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'connected': False,
            'error': 'Database connection failed'
        }


async def close_db():
    """Close database connection"""
    client.close()
    logger.info("✅ MongoDB connection closed")


async def reconnect_database():
    """Reconnect to database if connection is lost"""
    global client, db
    
    try:
        # Test current connection
        await client.admin.command('ping')
        logger.info("Database connection is healthy, no reconnection needed")
        return True
    except Exception as e:
        logger.warning(f"Database connection test failed: {e}, attempting reconnection...")
    
    try:
        # Close existing connection
        client.close()
        
        # Create new connection
        from motor.motor_asyncio import AsyncIOMotorClient
        
        new_client = AsyncIOMotorClient(
            MONGO_URL,
            maxPoolSize=100,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000
        )
        
        # Test new connection
        await new_client.admin.command('ping')
        
        # Update global references
        client = new_client
        db = new_client[DATABASE_NAME]
        
        logger.info("✅ Database reconnection successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database reconnection failed: {e}")
        return False
