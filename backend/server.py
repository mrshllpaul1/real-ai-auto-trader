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

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, version=APP_VERSION)

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
register_routes(api_router)

# Include the router
app.include_router(api_router)

# CORS middleware
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
    await asyncio.sleep(2)  # Let health check pass first
    
    from init.services import initialize_all_services
    await initialize_all_services(db)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_db()
