"""
AI Crypto Trading API - Main Entry Point
Lightweight server that delegates to modular initialization
"""

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio

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
            "url": "https://status-checkup.preview.emergentagent.com",
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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_db()
