from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
import os
import re
import logging

from utils.safe_errors import safe_error_response, log_security_event
from utils.input_sanitizer import sanitize_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

class KrakenCredentials(BaseModel):
    api_key: str = Field(..., min_length=1, max_length=256)
    api_secret: str = Field(..., min_length=1, max_length=512)

    @field_validator('api_key', 'api_secret')
    @classmethod
    def no_injection(cls, v):
        if '$' in v and any(op in v for op in ['$gt', '$ne', '$or', '$where']):
            raise ValueError('Invalid characters in credential')
        return v

class BinanceCredentials(BaseModel):
    api_key: str = Field(..., min_length=1, max_length=256)
    api_secret: str = Field(..., min_length=1, max_length=512)

class CryptoComCredentials(BaseModel):
    api_key: str = Field(..., min_length=1, max_length=256)
    api_secret: str = Field(..., min_length=1, max_length=512)

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
        clean_user_id = sanitize_user_id(user_id)
        
        encrypted_key = cipher.encrypt(credentials.api_key.encode()).decode()
        encrypted_secret = cipher.encrypt(credentials.api_secret.encode()).decode()
        
        stored = {
            "user_id": clean_user_id,
            "encrypted_key": encrypted_key,
            "encrypted_secret": encrypted_secret,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await db.credentials.replace_one(
            {"user_id": clean_user_id},
            stored,
            upsert=True
        )
        
        log_security_event("credential_store", {"exchange": "kraken", "user_id": clean_user_id}, severity="info")
        return {"message": "Credentials stored successfully", "has_credentials": True}
    except Exception as e:
        raise safe_error_response(e, category="auth", context="store kraken credentials")

@router.get("/check-credentials")
async def check_credentials(user_id: str, db = Depends(get_database)):
    """Check if user has stored credentials"""
    clean_user_id = sanitize_user_id(user_id)
    stored = await db.credentials.find_one({"user_id": clean_user_id})
    return {
        "has_credentials": stored is not None,
        "message": "Credentials found" if stored else "No credentials stored"
    }

@router.delete("/delete-credentials")
async def delete_credentials(user_id: str, db = Depends(get_database)):
    """Delete stored credentials"""
    clean_user_id = sanitize_user_id(user_id)
    result = await db.credentials.delete_one({"user_id": clean_user_id})
    if result.deleted_count > 0:
        log_security_event("credential_delete", {"exchange": "kraken", "user_id": clean_user_id}, severity="warning")
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
        raise safe_error_response(e, category="auth", context="store binance credentials")


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
# CRYPTO.COM EXCHANGE CREDENTIALS (Best for Arbitrage - US Friendly)
# =============================================================================

@router.post("/crypto-com/store")
async def store_crypto_com_credentials(
    credentials: CryptoComCredentials,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Store encrypted Crypto.com API credentials"""
    try:
        encrypted_key = cipher.encrypt(credentials.api_key.encode()).decode()
        encrypted_secret = cipher.encrypt(credentials.api_secret.encode()).decode()
        
        stored = {
            "user_id": user_id,
            "exchange": "crypto_com",
            "encrypted_key": encrypted_key,
            "encrypted_secret": encrypted_secret,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await db.exchange_credentials.replace_one(
            {"user_id": user_id, "exchange": "crypto_com"},
            stored,
            upsert=True
        )
        
        return {"message": "Crypto.com credentials stored successfully", "has_credentials": True}
    except Exception as e:
        raise safe_error_response(e, category="auth", context="store crypto.com credentials")


@router.get("/crypto-com/check")
async def check_crypto_com_credentials(user_id: str = "default_user", db = Depends(get_database)):
    """Check if user has stored Crypto.com credentials"""
    stored = await db.exchange_credentials.find_one({"user_id": user_id, "exchange": "crypto_com"})
    return {
        "has_credentials": stored is not None,
        "exchange": "crypto_com",
        "message": "Crypto.com credentials found" if stored else "No Crypto.com credentials stored"
    }


@router.delete("/crypto-com/delete")
async def delete_crypto_com_credentials(user_id: str = "default_user", db = Depends(get_database)):
    """Delete stored Crypto.com credentials"""
    result = await db.exchange_credentials.delete_one({"user_id": user_id, "exchange": "crypto_com"})
    if result.deleted_count > 0:
        return {"message": "Crypto.com credentials deleted successfully"}
    raise HTTPException(status_code=404, detail="No Crypto.com credentials found")


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
    crypto_com = await db.exchange_credentials.find_one({"user_id": user_id, "exchange": "crypto_com"})
    
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
            "crypto_com": {
                "connected": crypto_com is not None,
                "description": "Best for cross-exchange arbitrage (US friendly)"
            }
        },
        "total_connected": sum([
            kraken is not None,
            binance is not None,
            crypto_com is not None
        ]),
        "arbitrage_ready": (kraken is not None or binance is not None) and crypto_com is not None
    }
