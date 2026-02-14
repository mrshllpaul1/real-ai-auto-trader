"""
Entry Price Management API Routes

Endpoints for viewing and manually correcting entry prices for positions.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entry-prices", tags=["Entry Price Management"])

# Service reference
_db = None
_entry_tracker = None


def init_router(db):
    """Initialize router with database"""
    global _db, _entry_tracker
    _db = db
    from services.entry_price_tracker import EntryPriceTracker
    _entry_tracker = EntryPriceTracker(db)
    logger.info("✅ Entry Price Management routes initialized")


class ManualEntryRequest(BaseModel):
    """Request model for manual entry price correction"""
    symbol: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    entry_price: float = Field(..., gt=0, description="Entry price per unit")
    quantity: Optional[float] = Field(None, ge=0, description="Optional quantity override")
    notes: Optional[str] = Field(None, max_length=500, description="Notes about the correction")


class BulkEntryRequest(BaseModel):
    """Request model for bulk entry price updates"""
    entries: List[ManualEntryRequest]


@router.get("/")
async def get_all_entries():
    """Get all position entry prices"""
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracker not initialized")
    
    try:
        entries = await _entry_tracker.get_all_entries()
        
        # Add additional metadata
        for entry in entries:
            entry["is_manual"] = entry.get("is_manual", False)
            corrections = entry.get("manual_corrections", [])
            entry["correction_count"] = len(corrections)
            if corrections:
                entry["last_correction"] = corrections[-1].get("timestamp")
        
        return {
            "count": len(entries),
            "entries": entries,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching entries: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/{symbol}")
async def get_entry_price(symbol: str):
    """Get entry price data for a specific symbol"""
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracker not initialized")
    
    try:
        symbol = symbol.upper()
        entry = await _entry_tracker.get_entry_price(symbol)
        
        if not entry:
            raise HTTPException(status_code=404, detail=f"No entry found for {symbol}")
        
        # Add correction history
        entry["correction_history"] = await _entry_tracker.get_correction_history(symbol)
        
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching entry for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/correct")
async def correct_entry_price(request: ManualEntryRequest):
    """
    Manually set or correct entry price for a position.
    
    Use this when:
    - Entry price data is missing or incorrect
    - Tracking cost basis for tax purposes
    - Positions transferred from another exchange
    """
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracker not initialized")
    
    try:
        symbol = request.symbol.upper()
        
        result = await _entry_tracker.set_manual_entry_price(
            symbol=symbol,
            entry_price=request.entry_price,
            quantity=request.quantity,
            notes=request.notes
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "message": f"Entry price for {symbol} has been {'corrected' if result['action'] == 'corrected' else 'created'}",
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error correcting entry price: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/correct/bulk")
async def correct_entry_prices_bulk(request: BulkEntryRequest):
    """Bulk update entry prices for multiple positions"""
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracker not initialized")
    
    results = []
    errors = []
    
    for entry in request.entries:
        try:
            symbol = entry.symbol.upper()
            result = await _entry_tracker.set_manual_entry_price(
                symbol=symbol,
                entry_price=entry.entry_price,
                quantity=entry.quantity,
                notes=entry.notes
            )
            
            if "error" in result:
                errors.append({"symbol": symbol, "error": result["error"]})
            else:
                results.append(result)
        except Exception as e:
            errors.append({"symbol": entry.symbol, "error": "An internal error occurred"})
    
    return {
        "status": "completed",
        "updated": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors if errors else None
    }


@router.delete("/{symbol}")
async def delete_entry(symbol: str):
    """Delete an entry price record"""
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracker not initialized")
    
    try:
        symbol = symbol.upper()
        result = await _entry_tracker.delete_entry(symbol)
        
        if result.get("action") == "not_found":
            raise HTTPException(status_code=404, detail=f"No entry found for {symbol}")
        
        return {
            "status": "success",
            "message": f"Entry for {symbol} deleted",
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting entry: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/{symbol}/history")
async def get_correction_history(symbol: str):
    """Get manual correction history for a symbol"""
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracker not initialized")
    
    try:
        symbol = symbol.upper()
        history = await _entry_tracker.get_correction_history(symbol)
        
        return {
            "symbol": symbol,
            "correction_count": len(history),
            "corrections": history
        }
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/sync-from-kraken")
async def sync_from_kraken_holdings():
    """
    Create entry records from current Kraken holdings.
    
    For positions without entry data, creates placeholder entries
    that can be manually corrected.
    """
    if _entry_tracker is None or _db is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Get current Kraken balance
        from services.kraken_service import get_kraken_service
        kraken = get_kraken_service()
        
        if not kraken:
            raise HTTPException(status_code=503, detail="Kraken service not available")
        
        balance = await kraken.get_account_balance()
        
        if "error" in balance:
            raise HTTPException(status_code=500, detail=balance["error"])
        
        created = []
        skipped = []
        
        for asset, amount in balance.items():
            if float(amount) <= 0.00001:
                continue
            
            # Clean asset name
            symbol = asset.replace('X', '').replace('Z', '')[:3] if asset.startswith(('X', 'Z')) else asset
            symbol = symbol.upper()
            
            # Skip USD/stablecoins
            if symbol in ['USD', 'USDT', 'USDC', 'DAI']:
                continue
            
            # Check if entry exists
            existing = await _entry_tracker.get_entry_price(symbol)
            
            if existing:
                skipped.append({"symbol": symbol, "reason": "Entry already exists"})
            else:
                # Create placeholder entry - user should correct the price
                result = await _entry_tracker.set_manual_entry_price(
                    symbol=symbol,
                    entry_price=0.01,  # Placeholder - needs correction
                    quantity=float(amount),
                    notes="Auto-created from Kraken balance - please correct entry price"
                )
                created.append(result)
        
        return {
            "status": "completed",
            "created": len(created),
            "skipped": len(skipped),
            "created_entries": created,
            "skipped_entries": skipped,
            "message": "Please correct the entry prices for newly created positions"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing from Kraken: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")
