"""
WebSocket Manager for Real-Time Updates
======================================
Handles real-time communication for prices, signals, and training status.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import asyncio
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        # Active connections by channel
        self.connections: Dict[str, Set[WebSocket]] = {
            'prices': set(),
            'portfolio': set(),
            'signals': set(),
            'training': set(),
            'alerts': set(),
            'all': set(),  # Receives all updates
        }
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, channels: List[str] = None):
        """Accept connection and subscribe to channels."""
        await websocket.accept()
        
        if channels is None:
            channels = ['all']
        
        async with self._lock:
            for channel in channels:
                if channel in self.connections:
                    self.connections[channel].add(websocket)
                    
        logger.info(f"WebSocket connected to channels: {channels}")
        return True
    
    async def disconnect(self, websocket: WebSocket):
        """Remove connection from all channels."""
        async with self._lock:
            for channel in self.connections.values():
                channel.discard(websocket)
        logger.info("WebSocket disconnected")
    
    async def broadcast_to_channel(self, channel: str, data: dict):
        """Broadcast message to all connections in a channel."""
        message = {
            'channel': channel,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Send to specific channel and 'all' channel
        targets = self.connections.get(channel, set()) | self.connections.get('all', set())
        
        disconnected = set()
        for connection in targets:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected
        if disconnected:
            async with self._lock:
                for channel_set in self.connections.values():
                    channel_set -= disconnected
    
    async def send_personal(self, websocket: WebSocket, data: dict):
        """Send message to specific connection."""
        try:
            await websocket.send_json({
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
    
    def get_connection_count(self) -> Dict[str, int]:
        """Get count of connections per channel."""
        return {channel: len(conns) for channel, conns in self.connections.items()}


# Global connection manager
ws_manager = ConnectionManager()


# Broadcast functions for different data types
async def broadcast_price_update(prices: dict):
    """Broadcast price updates to subscribers."""
    await ws_manager.broadcast_to_channel('prices', {
        'type': 'price_update',
        'prices': prices,
    })


async def broadcast_signal(signal: dict):
    """Broadcast AI trading signal."""
    await ws_manager.broadcast_to_channel('signals', {
        'type': 'ai_signal',
        'signal': signal,
    })


async def broadcast_training_progress(progress: dict):
    """Broadcast training progress updates."""
    await ws_manager.broadcast_to_channel('training', {
        'type': 'training_progress',
        'progress': progress,
    })


async def broadcast_portfolio_update(portfolio: dict):
    """Broadcast portfolio changes."""
    await ws_manager.broadcast_to_channel('portfolio', {
        'type': 'portfolio_update',
        'portfolio': portfolio,
    })


async def broadcast_alert(alert: dict):
    """Broadcast alert notification."""
    await ws_manager.broadcast_to_channel('alerts', {
        'type': 'alert',
        'alert': alert,
    })
