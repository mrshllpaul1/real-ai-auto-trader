"""
AI Crypto Trading API - Main Entry Point
Lightweight server that delegates to modular initialization
"""

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
import asyncio
import os

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
    """API health check endpoint"""
    try:
        await client.admin.command('ping')
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "healthy", "database": db_status, "version": APP_VERSION}

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

# Add middleware in correct order (last added = first executed)
# 1. Security Headers (outermost - first to execute)
try:
    from middleware.security_headers import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True, enable_csp=True)
    logger.info("✅ Security Headers middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import security headers middleware: {e}")

# 2. Error Monitoring
try:
    from middleware.error_monitoring import ErrorMonitoringMiddleware
    app.add_middleware(ErrorMonitoringMiddleware, log_all_requests=False)
    logger.info("✅ Error Monitoring middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import error monitoring middleware: {e}")

# 3. Rate Limiting
try:
    from middleware.rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    logger.info("✅ Rate Limiting middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import rate limiting middleware: {e}")

# 4. Request Validation
try:
    from middleware.request_validation import ValidationMiddleware
    app.add_middleware(ValidationMiddleware)
    logger.info("✅ Request Validation middleware enabled")
except ImportError as e:
    logger.warning(f"Could not import validation middleware: {e}")

# 5. ETag Middleware - 40-60% bandwidth reduction for unchanged responses
try:
    from middleware.etag_middleware import ETagMiddleware
    app.add_middleware(ETagMiddleware, min_size=100)
    logger.info("✅ ETag middleware enabled (40-60% bandwidth reduction)")
except ImportError as e:
    logger.warning(f"Could not import ETag middleware: {e}")

# 6. GZIP Compression - Compress responses >500 bytes for 60-80% smaller transfers
app.add_middleware(GZipMiddleware, minimum_size=500)
logger.info("✅ GZIP Compression middleware enabled (min_size=500 bytes)")

# CORS middleware (must be after custom middleware)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
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
        
    except Exception as e:
        logger.warning(f"⚠️ Performance enhancement initialization warning: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_db()
