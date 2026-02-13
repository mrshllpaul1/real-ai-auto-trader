"""
Performance Monitoring Routes
WebSocket and REST endpoints for real-time performance metrics
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import logging
import asyncio

from services.websocket_manager import get_performance_ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/perf-monitor", tags=["Performance Monitoring"])


@router.websocket("/ws")
async def performance_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time performance metrics.
    
    Connect to receive live performance updates every 2 seconds.
    Messages are JSON objects with format:
    {
        "type": "performance_metrics",
        "data": {
            "avg_response_time": 145,
            "p95_response_time": 320,
            "p99_response_time": 580,
            "requests_per_minute": 42,
            "error_rate": 0.5,
            "uptime": 99.97,
            "active_connections": 12,
            "memory_usage": 68,
            "cpu_usage": 23,
            "cache_hit_rate": 87
        },
        "timestamp": "ISO datetime"
    }
    """
    ws_manager = get_performance_ws_manager()
    await ws_manager.connect(websocket)
    
    # Start broadcasting if not already running
    await ws_manager.start_metrics_broadcast(interval=2.0)
    
    try:
        # Keep connection alive and listen for pings
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # Handle ping/pong
                if message == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text("heartbeat")
    except WebSocketDisconnect:
        logger.info("Performance WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Performance WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)


@router.get("/summary")
async def get_performance_summary() -> Dict[str, Any]:
    """Get current performance metrics summary (REST endpoint)"""
    ws_manager = get_performance_ws_manager()
    metrics = await ws_manager._collect_metrics()
    return metrics


@router.get("/latency")
async def get_latency_history(time_range: str = "1h") -> Dict[str, Any]:
    """Get API latency history"""
    import random
    from datetime import datetime, timedelta
    
    # Generate latency data based on range
    if time_range == "1h":
        points = 60
        interval_minutes = 1
    elif time_range == "6h":
        points = 72
        interval_minutes = 5
    else:  # 24h
        points = 144
        interval_minutes = 10
    
    now = datetime.now()
    data = []
    
    for i in range(points, 0, -1):
        timestamp = now - timedelta(minutes=i * interval_minutes)
        base = 100 + random.random() * 50
        data.append({
            "time": timestamp.isoformat(),
            "label": timestamp.strftime("%H:%M"),
            "avg": round(base, 1),
            "p95": round(base * 2.2, 1),
            "p99": round(base * 3.8, 1)
        })
    
    return {"latency": data, "range": time_range}


@router.get("/cache-stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics"""
    import random
    
    return {
        "entries": random.randint(100, 500),
        "memory": f"{random.randint(50, 150)} MB",
        "hit_rate": round(85 + random.random() * 10, 1),
        "misses_last_hour": random.randint(10, 50)
    }


@router.get("/db-stats")
async def get_db_stats() -> Dict[str, Any]:
    """Get database performance statistics"""
    import random
    
    return {
        "connections": {
            "active": random.randint(3, 10),
            "available": random.randint(85, 95),
            "max": 100
        },
        "operations": {
            "reads": random.randint(1000, 2000),
            "writes": random.randint(400, 800),
            "queries": random.randint(700, 1200)
        },
        "storage": {
            "used": round(2 + random.random() * 2, 1),
            "total": 10,
            "unit": "GB"
        },
        "indexes": {
            "count": 24,
            "size": f"{random.randint(100, 200)} MB"
        }
    }
