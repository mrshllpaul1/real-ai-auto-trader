from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
import os

router = APIRouter()

class KrakenCredentials(BaseModel):
    api_key: str
    api_secret: str

class CredentialsResponse(BaseModel):
    message: str
    has_credentials: bool

async def get_database():
    from server import db
    return db

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key()).encode()
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