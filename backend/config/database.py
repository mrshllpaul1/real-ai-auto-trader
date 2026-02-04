"""
Database Configuration
Central configuration for MongoDB connection
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'crypto_trading_db')

# Create client and db
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def get_db():
    """Get database instance"""
    return db


def get_client():
    """Get MongoDB client"""
    return client


async def close_db():
    """Close database connection"""
    client.close()
