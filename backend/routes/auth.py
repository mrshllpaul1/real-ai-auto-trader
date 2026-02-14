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

class CryptoComCredentials(BaseModel):
    api_key: str
    api_secret: str

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
    user_id: str = "default_user",
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
async def check_credentials(user_id: str = "default_user", db = Depends(get_database)):
    """Check if user has stored credentials"""
    stored = await db.credentials.find_one({"user_id": user_id})
    return {
        "has_credentials": stored is not None,
        "message": "Credentials found" if stored else "No credentials stored"
    }

@router.delete("/delete-credentials")
async def delete_credentials(user_id: str = "default_user", db = Depends(get_database)):
    """Delete stored credentials"""
    result = await db.credentials.delete_one({"user_id": user_id})
    if result.deleted_count > 0:
        return {"message": "Credentials deleted successfully"}
    raise HTTPException(status_code=404, detail="No credentials found")


# =============================================================================
# KRAKEN API KEY FINDER
# =============================================================================

def _mask_key(key: str) -> str:
    """Mask an API key, showing only first 4 and last 4 characters"""
    if not key or len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


@router.get("/kraken/find-keys")
async def find_kraken_keys(user_id: str = "default_user", db = Depends(get_database)):
    """
    Find where Kraken API keys are configured.

    Checks both environment variables and database-stored credentials.
    Returns masked key previews (never full keys) to help identify which keys are set.
    """
    sources = []

    # Check environment variables
    env_api_key = os.getenv("KRAKEN_API_KEY")
    env_api_secret = os.getenv("KRAKEN_API_SECRET")

    env_source = {
        "source": "environment_variables",
        "configured": bool(env_api_key and env_api_secret),
        "api_key_set": bool(env_api_key),
        "api_secret_set": bool(env_api_secret),
    }
    if env_api_key:
        env_source["api_key_preview"] = _mask_key(env_api_key)
    if env_api_secret:
        env_source["api_secret_preview"] = _mask_key(env_api_secret)
    sources.append(env_source)

    # Check database-stored credentials
    db_source = {
        "source": "database",
        "configured": False,
        "api_key_set": False,
        "api_secret_set": False,
    }
    try:
        stored = await db.credentials.find_one({"user_id": user_id})
        if stored and stored.get("encrypted_key") and stored.get("encrypted_secret"):
            db_source["configured"] = True
            db_source["api_key_set"] = True
            db_source["api_secret_set"] = True
            db_source["stored_at"] = stored.get("created_at")
            db_source["updated_at"] = stored.get("updated_at")
            # Try to show masked preview of decrypted key
            try:
                decrypted_key = cipher.decrypt(stored["encrypted_key"].encode()).decode()
                db_source["api_key_preview"] = _mask_key(decrypted_key)
                del decrypted_key
            except Exception:
                db_source["api_key_preview"] = "****"
    except Exception as e:
        db_source["error"] = f"Could not check database: {type(e).__name__}"
    sources.append(db_source)

    any_configured = any(s["configured"] for s in sources)

    return {
        "found": any_configured,
        "sources": sources,
        "active_source": (
            "environment_variables" if sources[0]["configured"]
            else "database" if sources[1]["configured"]
            else None
        ),
        "message": (
            "Kraken API keys found"
            if any_configured
            else "No Kraken API keys configured. Add them in Settings or set KRAKEN_API_KEY and KRAKEN_API_SECRET environment variables."
        ),
    }


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
        raise HTTPException(status_code=500, detail=str(e))


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
