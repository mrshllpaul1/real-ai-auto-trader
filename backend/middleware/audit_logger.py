"""
Audit Logger Middleware
Logs all sensitive operations (trades, credential changes, config changes)
for security audit trail.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Set
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("audit")

# Configure audit log handler
audit_handler = logging.FileHandler("/var/log/supervisor/audit.log")
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s'
))
audit_logger = logging.getLogger("audit")
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)


# Paths that are considered sensitive and should be audit-logged
SENSITIVE_PATHS: Dict[str, str] = {
    # Trade execution
    "/api/kraken-exec/execute": "TRADE_EXECUTION",
    "/api/kraken-exec/place-order": "ORDER_PLACEMENT",
    "/api/kraken-exec/cancel": "ORDER_CANCELLATION",
    "/api/perpetuals/order": "PERP_ORDER",
    "/api/spot/order": "SPOT_ORDER",
    "/api/rebalance/execute": "PORTFOLIO_REBALANCE",
    "/api/auto-trading/start": "AUTO_TRADE_START",
    "/api/auto-trading/stop": "AUTO_TRADE_STOP",
    "/api/tethys-trading/start": "TETHYS_START",
    "/api/tethys-trading/stop": "TETHYS_STOP",
    # Credential management
    "/api/auth/store-credentials": "CREDENTIAL_STORE",
    "/api/auth/delete-credentials": "CREDENTIAL_DELETE",
    "/api/auth/binance/store": "CREDENTIAL_STORE",
    "/api/auth/crypto-com/store": "CREDENTIAL_STORE",
    # API key management
    "/api/api-keys/create": "API_KEY_CREATE",
    "/api/api-keys/revoke": "API_KEY_REVOKE",
    # Config changes
    "/api/settings": "SETTINGS_CHANGE",
    "/api/triggers/create": "TRIGGER_CREATE",
    "/api/budget": "BUDGET_CHANGE",
}

# HTTP methods that indicate state changes
STATE_CHANGING_METHODS: Set[str] = {"POST", "PUT", "PATCH", "DELETE"}


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Logs sensitive API operations for security audit trail"""
    
    async def dispatch(self, request: Request, call_next):
        # Only audit state-changing requests to sensitive paths
        path = request.url.path
        method = request.method
        
        is_sensitive = any(path.startswith(sp) for sp in SENSITIVE_PATHS)
        is_state_change = method in STATE_CHANGING_METHODS
        
        if not (is_sensitive and is_state_change):
            return await call_next(request)
        
        # Build audit record
        audit_id = str(uuid.uuid4())[:8]
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")[:200]
        user_id = request.headers.get("X-User-ID", "anonymous")
        api_key = request.headers.get("X-API-Key", "")[:8]  # Only first 8 chars
        
        # Determine operation type
        operation = "UNKNOWN"
        for sensitive_path, op_type in SENSITIVE_PATHS.items():
            if path.startswith(sensitive_path):
                operation = op_type
                break
        
        start_time = time.time()
        
        # Log the attempt
        audit_logger.info(
            f"AUDIT-{audit_id} | {operation} | {method} {path} | "
            f"IP={client_ip} | User={user_id} | API_Key={api_key}... | "
            f"UA={user_agent[:50]}"
        )
        
        # Execute request
        response = await call_next(request)
        
        duration = round((time.time() - start_time) * 1000, 2)
        status = response.status_code
        
        # Log the result
        result = "SUCCESS" if 200 <= status < 400 else "FAILED"
        audit_logger.info(
            f"AUDIT-{audit_id} | {operation} | {result} | "
            f"Status={status} | Duration={duration}ms"
        )
        
        # Add audit ID to response headers
        response.headers["X-Audit-ID"] = audit_id
        
        return response
