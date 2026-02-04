"""
Database Configuration Module
Handles MongoDB connection setup
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')


def get_database() -> tuple[AsyncIOMotorClient, AsyncIOMotorDatabase]:
    """
    Get MongoDB client and database connection
    
    Returns:
        Tuple of (client, database)
    """
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'crypto_trading_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    return client, db


# Initialize database connection
mongo_client, db = get_database()
