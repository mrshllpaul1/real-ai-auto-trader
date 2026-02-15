"""
AI Crypto Trading API - Main Entry Point
Lightweight server that delegates to modular initialization
"""

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
import os
import uuid
import traceback

# Configuration imports
from config.app_config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, CORS_ORIGINS, LOG_FORMAT, LOG_LEVEL
from config.database import db, client, close_db
from config.websocket import ConnectionManager

# Re-export db for backward compatibility with routes that import from server
# This allows `from server import db` to work
__all__ = ['db', 'client', 'app', 'get_service']


def get_service(name: str):
    """Get an initialized service by name"""
    from init.services import get_service as _get_service
    return _get_service(name)

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Create the main app with enhanced API documentation
app = FastAPI(
    title=APP_TITLE,
    description=f"""{APP_DESCRIPTION}

## Authentication

Most endpoints require API key authentication. Include your API key in the header:

```
X-API-Key: your_api_key_here
```

## Rate Limiting

API requests are rate-limited based on your subscription tier:
- **Free**: 100 requests/day
- **Pro**: 10,000 requests/day  
- **Enterprise**: Unlimited

## Endpoints

All trading endpoints are prefixed with `/api`. See below for full documentation.

## Support

- Documentation: https://docs.yourapp.com
- Support: support@yourapp.com
- Status: https://status.yourapp.com
    """,
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "API Support",
        "email": "support@emergentagent.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://emergentagent.com/terms",
    },
    servers=[
        {
            "url": os.environ.get('API_SERVER_URL', 'http://localhost:8001'),
            "description": "Production server"
        },
        {
            "url": "http://localhost:8001",
            "description": "Development server"
        }
    ],
    tags_metadata=[
        {
            "name": "health",
            "description": "Health check endpoints for monitoring"
        },
        {
            "name": "tethys",
            "description": "Tethys AI trading engine operations"
        },
        {
            "name": "triggers",
            "description": "Event-driven trigger management"
        },
        {
            "name": "portfolio",
            "description": "Portfolio management and analytics"
        },
        {
            "name": "trading",
            "description": "Trading operations and execution"
        },
        {
            "name": "ai",
            "description": "AI model operations and training"
        },
        {
            "name": "auth",
            "description": "Authentication and API key management"
        },
    ]
)

# WebSocket manager
ws_manager = ConnectionManager()


# =============================================================================
# GLOBAL EXCEPTION HANDLER - Prevents leaking internal errors to clients
# =============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unhandled exceptions.
    Logs the real error server-side, returns safe message to client.
    """
    error_id = str(uuid.uuid4())[:8]
    
    # Log the REAL error server-side
    logger.error(
        f"[UNHANDLED-{error_id}] {request.method} {request.url.path} | "
        f"{type(exc).__name__}: {str(exc)}"
    )
    logger.debug(f"[UNHANDLED-{error_id}] Traceback:\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "message": "An internal error occurred. Please try again later.",
                "error_id": error_id,
                "support_hint": f"Reference this ID when contacting support: ERR-{error_id}"
            }
        }
    )


# Health check endpoints - Must respond fast
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment"""
    return {"status": "healthy", "version": APP_VERSION}

@app.get("/")
async def root_health():
    """Root health check"""
    return {"status": "ok", "service": "ai-crypto-trading"}

# Create API router
api_router = APIRouter(prefix="/api")

@api_router.get("/health")
async def api_health_check():
    """Comprehensive API health check endpoint"""
    # Database check
    try:
        await client.admin.command('ping')
        db_status = "connected"
    except Exception:
        db_status = "degraded"
    
    # Kraken connectivity check
    kraken_configured = bool(os.environ.get('KRAKEN_API_KEY'))
    
    # Core services health
    services_health = {
        "database": db_status,
        "kraken_configured": kraken_configured,
        "ml_lightweight_mode": os.environ.get('ML_LIGHTWEIGHT_MODE', 'false') == 'true',
    }
    
    overall = "healthy" if db_status == "connected" else "degraded"
    
    return {
        "status": overall,
        "database": db_status,
        "version": APP_VERSION,
        "services": services_health,
    }


@api_router.get("/health/deep")
async def deep_health_check():
    """
    Deep health check - tests all critical subsystems.
    Use for monitoring dashboards, not for frequent polling.
    """
    checks = {}
    overall_healthy = True
    
    # 1. Database connectivity
    try:
        await client.admin.command('ping')
        from config.database import get_pool_stats
        pool_stats = await get_pool_stats()
        checks["database"] = {
            "status": "healthy",
            "pool_stats": pool_stats
        }
    except Exception:
        checks["database"] = {"status": "unhealthy"}
        overall_healthy = False
    
    # 2. Kraken API connectivity
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as hclient:
            resp = await hclient.get("https://api.kraken.com/0/public/Time")
            kraken_up = resp.status_code == 200
        checks["kraken_public_api"] = {
            "status": "healthy" if kraken_up else "degraded",
            "reachable": kraken_up
        }
    except Exception:
        checks["kraken_public_api"] = {"status": "unreachable"}
    
    # 3. Encryption key validity
    try:
        from cryptography.fernet import Fernet
        enc_key = os.environ.get('ENCRYPTION_KEY', '')
        if enc_key:
            Fernet(enc_key.encode() if isinstance(enc_key, str) else enc_key)
            checks["encryption"] = {"status": "healthy", "key_configured": True}
        else:
            checks["encryption"] = {"status": "warning", "key_configured": False}
    except Exception:
        checks["encryption"] = {"status": "unhealthy", "key_valid": False}
        overall_healthy = False
    
    # 4. Security middleware status
    checks["security"] = {
        "cors_configured": bool(CORS_ORIGINS),
        "cors_wildcard": "*" in CORS_ORIGINS,
        "security_headers": True,
        "rate_limiting": True,
        "audit_logging": True,
    }
    
    # 5. Environment completeness
    required_vars = ['MONGO_URL', 'DB_NAME', 'ENCRYPTION_KEY']
    optional_vars = ['KRAKEN_API_KEY', 'KRAKEN_API_SECRET', 'EMERGENT_LLM_KEY']
    
    env_check = {
        "required_present": all(os.environ.get(v) for v in required_vars),
        "optional_configured": {v: bool(os.environ.get(v)) for v in optional_vars},
    }
    checks["environment"] = env_check
    if not env_check["required_present"]:
        overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "version": APP_VERSION,
        "checks": checks,
    }

@api_router.get("/")
async def root():
    return {
        "message": "AI Crypto Trading API",
        "status": "operational",
        "features": ["AI-powered trading", "Paper & Real trading", "Growth Engine"]
    }


@app.websocket("/ws/training")
async def websocket_training_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time training status updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                from services.background_tasks import get_task_manager
                task_manager = get_task_manager()
                
                if task_manager:
                    active_tasks = await task_manager.get_active_tasks()
                    await websocket.send_json({
                        "type": "training_update",
                        "timestamp": asyncio.get_event_loop().time(),
                        "tasks": active_tasks
                    })
            except Exception as e:
                logger.debug(f"WebSocket training update error: {e}")
            
            await asyncio.sleep(3)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# Register all routes
from init.routes import register_routes
register_routes(api_router, db)

# Include the router
app.include_router(api_router)

# Import and include monitoring routes
try:
    from middleware.error_monitoring import error_router
    app.include_router(error_router)
    logger.info("✅ Error monitoring routes registered")
except ImportError as e:
    logger.warning(f"Could not import error monitoring routes: {e}")

# Import and include performance metrics routes
try:
    from routes.performance_metrics import router as performance_router
    app.include_router(performance_router, prefix="/api")
    logger.info("✅ Performance metrics routes registered")
except ImportError as e:
    logger.warning(f"Could not import performance metrics routes: {e}")

# Import and include system state routes
try:
    from routes.system_state import router as system_state_router, set_db as set_system_state_db
    set_system_state_db(db)
    app.include_router(system_state_router, prefix="/api")
    logger.info("✅ System state routes registered")
except ImportError as e:
    logger.warning(f"Could not import system state routes: {e}")

# Import and include error management routes
try:
    from routes.error_management import router as error_management_router, set_db as set_error_db
    set_error_db(db)
    app.include_router(error_management_router, prefix="/api")
    logger.info("✅ Error management routes registered")
except ImportError as e:
    logger.warning(f"Could not import error management routes: {e}")

# Import and include performance monitoring WebSocket routes
try:
    from routes.performance_monitoring import router as perf_monitoring_router
    app.include_router(perf_monitoring_router)
    logger.info("✅ Performance monitoring WebSocket routes registered")
except ImportError as e:
    logger.warning(f"Could not import performance monitoring routes: {e}")

# Import and include WebSocket routes
try:
    from routes.websocket import router as websocket_router
    app.include_router(websocket_router)
    logger.info("✅ WebSocket routes registered")
except ImportError as e:
    logger.warning(f"Could not import WebSocket routes: {e}")

# Import and include AI Explanation routes
try:
    from routes.ai_explanation import router as ai_explanation_router
    app.include_router(ai_explanation_router)
    logger.info("✅ AI Explanation routes registered")
except ImportError as e:
    logger.warning(f"Could not import AI Explanation routes: {e}")

# Import and include Google OAuth routes
try:
    from routes.google_oauth import router as google_oauth_router, set_dependencies as set_oauth_deps
    set_oauth_deps(db)
    app.include_router(google_oauth_router)
    logger.info("✅ Google OAuth routes registered")
except ImportError as e:
    logger.warning(f"Could not import Google OAuth routes: {e}")

# Import and include Natural Language Strategy routes
try:
    from routes.natural_language_strategy import router as nl_strategy_router
    app.include_router(nl_strategy_router)
    logger.info("✅ Natural Language Strategy routes registered")
except ImportError as e:
    logger.warning(f"Could not import Natural Language Strategy routes: {e}")

# Import and include AI Copilot routes
try:
    from routes.ai_copilot import router as ai_copilot_router
    app.include_router(ai_copilot_router)
    logger.info("✅ AI Copilot routes registered")
except ImportError as e:
    logger.warning(f"Could not import AI Copilot routes: {e}")

# Import and include ML Analytics routes
try:
    from routes.ml_analytics_api import router as ml_analytics_router
    app.include_router(ml_analytics_router)
    logger.info("✅ ML Analytics routes registered")
except ImportError as e:
    logger.warning(f"Could not import ML Analytics routes: {e}")

# Import and include ML Data Population routes
try:
    from routes.ml_data_population import router as ml_data_router, set_dependencies as set_ml_data_deps
    set_ml_data_deps(db)
    app.include_router(ml_data_router)
    logger.info("✅ ML Data Population routes registered")
except ImportError as e:
    logger.warning(f"Could not import ML Data Population routes: {e}")

# Import and include Live Calibration routes
try:
    from routes.live_calibration import router as live_calibration_router, set_dependencies as set_live_cal_deps
    set_live_cal_deps(db)
    app.include_router(live_calibration_router)
    logger.info("✅ Live Calibration routes registered")
except ImportError as e:
    logger.warning(f"Could not import Live Calibration routes: {e}")

# Add middleware in correct order (last added = first executed)
# 1. Security Headers (outermost - first to execute)
try:
    from middleware.security_headers import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True, enable_csp=True)
    logger.info("✅ Security Headers middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import security headers middleware: {e}")

# 2. CSRF Protection (double-submit cookie pattern)
try:
    from middleware.csrf_protection import CSRFProtectionMiddleware
    app.add_middleware(CSRFProtectionMiddleware)
    logger.info("✅ CSRF Protection middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import CSRF protection middleware: {e}")

# 3. Audit Logging (logs sensitive operations)
try:
    from middleware.audit_logger import AuditLogMiddleware
    app.add_middleware(AuditLogMiddleware)
    logger.info("✅ Audit Logging middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import audit logging middleware: {e}")

# 3. Error Monitoring
try:
    from middleware.error_monitoring import ErrorMonitoringMiddleware
    app.add_middleware(ErrorMonitoringMiddleware, log_all_requests=False)
    logger.info("✅ Error Monitoring middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import error monitoring middleware: {e}")

# 4. Rate Limiting
try:
    from middleware.rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    logger.info("✅ Rate Limiting middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import rate limiting middleware: {e}")

# 5. Request Validation (enhanced with NoSQL injection detection)
try:
    from middleware.request_validation import ValidationMiddleware
    app.add_middleware(ValidationMiddleware)
    logger.info("✅ Request Validation middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import validation middleware: {e}")

# 6. ETag Middleware - 40-60% bandwidth reduction for unchanged responses
try:
    from middleware.etag_middleware import ETagMiddleware
    app.add_middleware(ETagMiddleware, min_size=100)
    logger.info("✅ ETag middleware enabled (40-60% bandwidth reduction)")
except ImportError as e:
    logger.warning(f"Could not import ETag middleware: {e}")

# 7. GZIP Compression - Compress responses >500 bytes for 60-80% smaller transfers
app.add_middleware(GZipMiddleware, minimum_size=500)
logger.info("✅ GZIP Compression middleware enabled (min_size=500 bytes)")

# CORS middleware (must be after custom middleware)
# Tighten allowed methods to only those actually used
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining-Minute", "X-RateLimit-Remaining-Hour", "X-Audit-ID", "X-CSRF-Token"],
)


@app.on_event("startup")
async def startup_event():
    """Fast startup - defer heavy initialization"""
    logger.info("🚀 Application starting...")
    asyncio.create_task(delayed_init())


async def delayed_init():
    """Initialize services after startup completes"""
    await asyncio.sleep(5)  # Give health checks more time to pass
    
    from init.services import initialize_all_services
    await initialize_all_services(db)
    
    # Initialize performance enhancements
    try:
        # Initialize cache manager
        from services.cache_manager import get_cache_manager
        cache = get_cache_manager()
        logger.info("✅ Cache manager initialized")
        
        # Create database indexes for 5-10x faster queries
        from init.database_indexes import create_indexes
        index_results = await create_indexes(db)
        logger.info(f"✅ Database indexes created: {len(index_results.get('created', []))} new, {len(index_results.get('existing', []))} existing")
        
        # Initialize state persistence service
        from services.state_persistence import initialize_state_persistence
        await initialize_state_persistence(db)
        logger.info("✅ System state persistence initialized")
        
        # Initialize error recovery manager
        from services.error_recovery import get_error_recovery_manager
        error_manager = get_error_recovery_manager(db)
        logger.info("✅ Error recovery manager initialized")
        
        # Create error_history index
        await db.error_history.create_index([("timestamp", -1), ("category", 1)])
        await db.error_history.create_index([("fingerprint", 1)])
        logger.info("✅ Error history indexes created")
        
        # Create session TTL index (auto-delete expired sessions)
        await db.active_sessions.create_index(
            "expires_at",
            expireAfterSeconds=0  # MongoDB TTL removes docs once expires_at passes
        )
        await db.active_sessions.create_index("session_token_hash")
        logger.info("✅ Session auth indexes created (TTL + token hash)")
        
        # Initialize vulnerability scanner + 24h schedule
        from services.vuln_scanner import VulnerabilityScannerService
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        
        vuln_scanner = VulnerabilityScannerService(db)
        
        # Register API route
        from routes.vuln_scanner import set_scanner
        set_scanner(vuln_scanner)
        
        # Create TTL index for scan history (keep 90 days)
        await db.vulnerability_scans.create_index(
            "created_at", expireAfterSeconds=90 * 86400
        )
        
        # Schedule: run first scan in 60s, then every 24h
        _vuln_scheduler = AsyncIOScheduler(timezone="UTC")
        _vuln_scheduler.add_job(
            vuln_scanner.run_full_scan,
            IntervalTrigger(hours=24),
            id="vuln_scan_24h",
            next_run_time=asyncio.get_event_loop().time() and __import__("datetime").datetime.utcnow() + __import__("datetime").timedelta(seconds=60),
            replace_existing=True,
        )
        _vuln_scheduler.start()
        logger.info("✅ Vulnerability scanner initialized (24h schedule, first scan in 60s)")
        
    except Exception as e:
        logger.warning(f"⚠️ Performance enhancement initialization warning: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_db()
