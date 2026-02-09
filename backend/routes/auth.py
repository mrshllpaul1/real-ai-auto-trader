from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
import os
import base64

router = APIRouter()

class KrakenCredentials(BaseModel):
    api_key: str
    api_secret: str

class BinanceCredentials(BaseModel):
    api_key: str
    api_secret: str

class KuCoinCredentials(BaseModel):
    api_key: str
    api_secret: str
    passphrase: str

class CredentialsResponse(BaseModel):
    message: str
    has_credentials: bool

async def get_database():
    from server import db
    return db

# Get or generate encryption key
encryption_key = os.getenv("ENCRYPTION_KEY")
if not encryption_key:
    # Generate a valid Fernet key (32 url-safe base64-encoded bytes)
    encryption_key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = encryption_key

# Ensure key is properly formatted
try:
    ENCRYPTION_KEY = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
    cipher = Fernet(ENCRYPTION_KEY)
except ValueError:
    # If key is invalid, generate a new one
    encryption_key = Fernet.generate_key().decode()
    ENCRYPTION_KEY = encryption_key.encode()
    cipher = Fernet(ENCRYPTION_KEY)

@router.post("/store-credentials")
async def store_credentials(
    credentials: KrakenCredentials,
    user_id: str,
    db = Depends(get_database)
):
    """Store encrypted Kraken API credentials"""
    try:
        encrypted_key = cipher.encrypt(credentials.api_key.encode()).decode()
        encrypted_secret = cipher.encrypt(credentials.api_secret.encode()).decode()
        
        stored = {
            "user_id": user_id,
            "encrypted_key": encrypted_key,
            "encrypted_secret": encrypted_secret,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await db.credentials.replace_one(
            {"user_id": user_id},
            stored,
            upsert=True
        )
        
        return {"message": "Credentials stored successfully", "has_credentials": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-credentials")
async def check_credentials(user_id: str, db = Depends(get_database)):
    """Check if user has stored credentials"""
    stored = await db.credentials.find_one({"user_id": user_id})
    return {
        "has_credentials": stored is not None,
        "message": "Credentials found" if stored else "No credentials stored"
    }

@router.delete("/delete-credentials")
async def delete_credentials(user_id: str, db = Depends(get_database)):
    """Delete stored credentials"""
    result = await db.credentials.delete_one({"user_id": user_id})
    if result.deleted_count > 0:
        return {"message": "Credentials deleted successfully"}
    raise HTTPException(status_code=404, detail="No credentials found")


# =============================================================================
# BINANCE EXCHANGE CREDENTIALS
# =============================================================================

@router.post("/binance/store")
async def store_binance_credentials(
    credentials: BinanceCredentials,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Store encrypted Binance API credentials"""
    try:
        encrypted_key = cipher.encrypt(credentials.api_key.encode()).decode()
        encrypted_secret = cipher.encrypt(credentials.api_secret.encode()).decode()
        
        stored = {
            "user_id": user_id,
            "exchange": "binance",
            "encrypted_key": encrypted_key,
            "encrypted_secret": encrypted_secret,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await db.exchange_credentials.replace_one(
            {"user_id": user_id, "exchange": "binance"},
            stored,
            upsert=True
        )
        
        return {"message": "Binance credentials stored successfully", "has_credentials": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/binance/check")
async def check_binance_credentials(user_id: str = "default_user", db = Depends(get_database)):
    """Check if user has stored Binance credentials"""
    stored = await db.exchange_credentials.find_one({"user_id": user_id, "exchange": "binance"})
    return {
        "has_credentials": stored is not None,
        "exchange": "binance",
        "message": "Binance credentials found" if stored else "No Binance credentials stored"
    }


@router.delete("/binance/delete")
async def delete_binance_credentials(user_id: str = "default_user", db = Depends(get_database)):
    """Delete stored Binance credentials"""
    result = await db.exchange_credentials.delete_one({"user_id": user_id, "exchange": "binance"})
    if result.deleted_count > 0:
        return {"message": "Binance credentials deleted successfully"}
    raise HTTPException(status_code=404, detail="No Binance credentials found")


# =============================================================================
# KUCOIN EXCHANGE CREDENTIALS (Best for Arbitrage)
# =============================================================================

@router.post("/kucoin/store")
async def store_kucoin_credentials(
    credentials: KuCoinCredentials,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Store encrypted KuCoin API credentials (includes passphrase)"""
    try:
        encrypted_key = cipher.encrypt(credentials.api_key.encode()).decode()
        encrypted_secret = cipher.encrypt(credentials.api_secret.encode()).decode()
        encrypted_passphrase = cipher.encrypt(credentials.passphrase.encode()).decode()
        
        stored = {
            "user_id": user_id,
            "exchange": "kucoin",
            "encrypted_key": encrypted_key,
            "encrypted_secret": encrypted_secret,
            "encrypted_passphrase": encrypted_passphrase,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await db.exchange_credentials.replace_one(
            {"user_id": user_id, "exchange": "kucoin"},
            stored,
            upsert=True
        )
        
        return {"message": "KuCoin credentials stored successfully", "has_credentials": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kucoin/check")
async def check_kucoin_credentials(user_id: str = "default_user", db = Depends(get_database)):
    """Check if user has stored KuCoin credentials"""
    stored = await db.exchange_credentials.find_one({"user_id": user_id, "exchange": "kucoin"})
    return {
        "has_credentials": stored is not None,
        "exchange": "kucoin",
        "message": "KuCoin credentials found" if stored else "No KuCoin credentials stored"
    }


@router.delete("/kucoin/delete")
async def delete_kucoin_credentials(user_id: str = "default_user", db = Depends(get_database)):
    """Delete stored KuCoin credentials"""
    result = await db.exchange_credentials.delete_one({"user_id": user_id, "exchange": "kucoin"})
    if result.deleted_count > 0:
        return {"message": "KuCoin credentials deleted successfully"}
    raise HTTPException(status_code=404, detail="No KuCoin credentials found")


# =============================================================================
# UTILITY FUNCTIONS FOR EXCHANGE CREDENTIAL RETRIEVAL
# =============================================================================

async def get_exchange_credentials(user_id: str, exchange: str, db):
    """
    Retrieve decrypted credentials for a specific exchange.
    Used internally by trading services.
    """
    stored = await db.exchange_credentials.find_one({"user_id": user_id, "exchange": exchange})
    if not stored:
        return None
    
    try:
        decrypted = {
            "api_key": cipher.decrypt(stored["encrypted_key"].encode()).decode(),
            "api_secret": cipher.decrypt(stored["encrypted_secret"].encode()).decode(),
        }
        
        # KuCoin has an additional passphrase
        if exchange == "kucoin" and "encrypted_passphrase" in stored:
            decrypted["passphrase"] = cipher.decrypt(stored["encrypted_passphrase"].encode()).decode()
        
        return decrypted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decrypt {exchange} credentials: {str(e)}")


@router.get("/exchanges/status")
async def get_all_exchange_status(user_id: str = "default_user", db = Depends(get_database)):
    """Get connection status for all supported exchanges"""
    kraken = await db.credentials.find_one({"user_id": user_id})
    binance = await db.exchange_credentials.find_one({"user_id": user_id, "exchange": "binance"})
    kucoin = await db.exchange_credentials.find_one({"user_id": user_id, "exchange": "kucoin"})
    
    return {
        "exchanges": {
            "kraken": {
                "connected": kraken is not None,
                "description": "Primary trading exchange"
            },
            "binance": {
                "connected": binance is not None,
                "description": "World's largest exchange by volume"
            },
            "kucoin": {
                "connected": kucoin is not None,
                "description": "Best for cross-exchange arbitrage"
            }
        },
        "total_connected": sum([
            kraken is not None,
            binance is not None,
            kucoin is not None
        ]),
        "arbitrage_ready": (kraken is not None or binance is not None) and kucoin is not None
    }
