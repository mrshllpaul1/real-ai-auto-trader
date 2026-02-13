"""
WebSocket Manager for Real-time Training Progress
Provides real-time updates instead of polling.
"""

import asyncio
import json
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time progress updates"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected clients"""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message, default=str)
        disconnected = set()
        
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected clients
            self.active_connections -= disconnected
    
    async def send_progress_update(
        self,
        task_id: str,
        task_type: str,
        progress: int,
        message: str,
        current_item: str = "",
        items_processed: int = 0,
        total_items: int = 0,
        status: str = "running",
        result: Dict = None
    ):
        """Send a progress update to all clients"""
        await self.broadcast({
            "type": "progress_update",
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "progress": progress,
            "message": message,
            "current_item": current_item,
            "items_processed": items_processed,
            "total_items": total_items,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


class PerformanceWebSocketManager:
    """Manages WebSocket connections for real-time performance monitoring"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._metrics_cache: Dict[str, Any] = {}
        self._running = False
        self._broadcast_task = None
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"Performance WS connected. Total: {len(self.active_connections)}")
        
        # Send current cached metrics immediately
        if self._metrics_cache:
            try:
                await websocket.send_json(self._metrics_cache)
            except Exception:
                pass
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"Performance WS disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast performance metrics to all connected clients"""
        self._metrics_cache = {
            "type": "performance_metrics",
            "data": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if not self.active_connections:
            return
        
        message_json = json.dumps(self._metrics_cache, default=str)
        disconnected = set()
        
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.debug(f"Failed to send performance metrics: {e}")
                    disconnected.add(connection)
            
            self.active_connections -= disconnected
    
    async def start_metrics_broadcast(self, interval: float = 2.0):
        """Start broadcasting metrics at regular intervals"""
        if self._running:
            return
        
        self._running = True
        
        async def broadcast_loop():
            while self._running:
                try:
                    # Collect and broadcast metrics
                    metrics = await self._collect_metrics()
                    await self.broadcast_metrics(metrics)
                except Exception as e:
                    logger.error(f"Error in metrics broadcast: {e}")
                
                await asyncio.sleep(interval)
        
        self._broadcast_task = asyncio.create_task(broadcast_loop())
        logger.info("Performance metrics broadcast started")
    
    async def stop_metrics_broadcast(self):
        """Stop the metrics broadcast loop"""
        self._running = False
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance metrics broadcast stopped")
    
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics"""
        import psutil
        import time
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        # Simulated API latency tracking (in real impl, track actual API calls)
        # For now, generate realistic mock data
        import random
        base_latency = 100 + random.random() * 50
        
        return {
            "avg_response_time": round(base_latency, 1),
            "p95_response_time": round(base_latency * 2.2, 1),
            "p99_response_time": round(base_latency * 3.8, 1),
            "requests_per_minute": random.randint(30, 60),
            "error_rate": round(random.random() * 0.5, 2),
            "uptime": 99.97,
            "active_connections": len(self.active_connections),
            "memory_usage": round(memory.percent, 1),
            "cpu_usage": round(cpu_percent, 1),
            "cache_hit_rate": round(85 + random.random() * 10, 1),
            "system": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2)
            }
        }


# Singleton instances
_ws_manager = None
_performance_ws_manager = None

def get_ws_manager() -> ConnectionManager:
    """Get the singleton WebSocket manager"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = ConnectionManager()
    return _ws_manager


def get_performance_ws_manager() -> PerformanceWebSocketManager:
    """Get the singleton Performance WebSocket manager"""
    global _performance_ws_manager
    if _performance_ws_manager is None:
        _performance_ws_manager = PerformanceWebSocketManager()
    return _performance_ws_manager
