"""
Vulnerability Scanner API Routes
Exposes scan results and allows manual trigger.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/security/vulnerabilities", tags=["Security"])

_scanner = None


def set_scanner(scanner):
    global _scanner
    _scanner = scanner


@router.get("/latest")
async def get_latest_scan():
    """Get the most recent vulnerability scan result."""
    if not _scanner:
        raise HTTPException(503, detail="Scanner service not initialized")
    result = await _scanner.get_latest_scan()
    if not result:
        return {"message": "No scans have been run yet. The first scan runs within 60s of startup, then every 24h."}
    return result


@router.get("/history")
async def get_scan_history(limit: int = 30):
    """Get vulnerability scan history (summaries)."""
    if not _scanner:
        raise HTTPException(503, detail="Scanner service not initialized")
    return await _scanner.get_scan_history(limit)


@router.post("/scan")
async def trigger_scan():
    """Manually trigger a vulnerability scan."""
    if not _scanner:
        raise HTTPException(503, detail="Scanner service not initialized")
    result = await _scanner.run_full_scan()
    return result
