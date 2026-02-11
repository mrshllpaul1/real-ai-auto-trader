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


# Singleton instance
_ws_manager = None

def get_ws_manager() -> ConnectionManager:
    """Get the singleton WebSocket manager"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = ConnectionManager()
    return _ws_manager
