"""
WebSocket Handler for Real-Time Copy Trading Notifications
Provides instant trade signal notifications to connected copiers
"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CopyTradingWebSocketManager:
    """
    Manages WebSocket connections for real-time copy trading notifications
    """
    
    def __init__(self):
        # Map of trader_id -> set of WebSocket connections (copiers)
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of websocket -> copier_id for tracking
        self.copier_connections: Dict[WebSocket, str] = {}
        
    async def connect(self, websocket: WebSocket, copier_id: str, trader_ids: list):
        """
        Connect a copier to receive signals from specified traders
        
        Args:
            websocket: WebSocket connection
            copier_id: ID of the copier
            trader_ids: List of trader IDs to follow
        """
        await websocket.accept()
        
        # Store copier mapping
        self.copier_connections[websocket] = copier_id
        
        # Subscribe to traders
        for trader_id in trader_ids:
            if trader_id not in self.active_connections:
                self.active_connections[trader_id] = set()
            self.active_connections[trader_id].add(websocket)
        
        logger.info(f"Copier {copier_id} connected, following {len(trader_ids)} traders")
        
        # Send confirmation
        await websocket.send_json({
            "type": "connection_confirmed",
            "copier_id": copier_id,
            "following_traders": trader_ids,
            "connected_at": datetime.now(timezone.utc).isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a copier's WebSocket
        """
        copier_id = self.copier_connections.get(websocket)
        
        # Remove from all trader subscriptions
        for trader_id, connections in self.active_connections.items():
            connections.discard(websocket)
        
        # Clean up empty sets
        self.active_connections = {
            tid: conns for tid, conns in self.active_connections.items() 
            if conns
        }
        
        # Remove copier mapping
        if websocket in self.copier_connections:
            del self.copier_connections[websocket]
        
        if copier_id:
            logger.info(f"Copier {copier_id} disconnected")
    
    async def broadcast_trade_signal(
        self,
        trader_id: str,
        signal: Dict
    ):
        """
        Broadcast a trade signal to all copiers following this trader
        
        Args:
            trader_id: ID of the trader making the trade
            signal: Trade signal data
        """
        if trader_id not in self.active_connections:
            logger.debug(f"No active connections for trader {trader_id}")
            return
        
        connections = self.active_connections[trader_id].copy()
        
        message = {
            "type": "trade_signal",
            "trader_id": trader_id,
            "signal": signal,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        disconnected = []
        
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(websocket)
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            self.disconnect(ws)
        
        logger.info(f"Broadcast signal from {trader_id} to {len(connections) - len(disconnected)} copiers")
    
    async def send_notification(
        self,
        copier_id: str,
        notification: Dict
    ):
        """
        Send a notification to a specific copier
        
        Args:
            copier_id: ID of the copier
            notification: Notification data
        """
        # Find websocket for this copier
        target_ws = None
        for ws, cid in self.copier_connections.items():
            if cid == copier_id:
                target_ws = ws
                break
        
        if not target_ws:
            logger.debug(f"Copier {copier_id} not connected")
            return
        
        message = {
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await target_ws.send_json(message)
        except Exception as e:
            logger.error(f"Error sending notification to {copier_id}: {e}")
            self.disconnect(target_ws)
    
    async def broadcast_market_update(
        self,
        update: Dict
    ):
        """
        Broadcast a market update to all connected copiers
        
        Args:
            update: Market update data
        """
        message = {
            "type": "market_update",
            "update": update,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Get all unique websockets
        all_ws = set()
        for connections in self.active_connections.values():
            all_ws.update(connections)
        
        disconnected = []
        
        for websocket in all_ws:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting market update: {e}")
                disconnected.append(websocket)
        
        # Clean up
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_connection_stats(self) -> Dict:
        """
        Get statistics about active connections
        """
        total_connections = len(self.copier_connections)
        traders_with_copiers = len(self.active_connections)
        
        trader_copier_counts = {
            trader_id: len(connections)
            for trader_id, connections in self.active_connections.items()
        }
        
        return {
            "total_copiers_connected": total_connections,
            "traders_with_active_copiers": traders_with_copiers,
            "copiers_per_trader": trader_copier_counts,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global manager instance
ws_manager = CopyTradingWebSocketManager()


async def handle_copy_trading_websocket(
    websocket: WebSocket,
    copier_id: str,
    trader_ids: str  # Comma-separated list
):
    """
    Handle WebSocket connection for copy trading
    
    Args:
        websocket: WebSocket connection
        copier_id: ID of the copier
        trader_ids: Comma-separated trader IDs to follow
    """
    trader_list = [tid.strip() for tid in trader_ids.split(',') if tid.strip()]
    
    try:
        await ws_manager.connect(websocket, copier_id, trader_list)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle ping/pong
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                # Handle subscription updates
                elif data.get("type") == "update_subscriptions":
                    new_traders = data.get("trader_ids", [])
                    # Disconnect and reconnect with new subscriptions
                    ws_manager.disconnect(websocket)
                    await ws_manager.connect(websocket, copier_id, new_traders)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"Error handling websocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"Copier {copier_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for copier {copier_id}: {e}")
    finally:
        ws_manager.disconnect(websocket)


def get_websocket_manager() -> CopyTradingWebSocketManager:
    """Get the global WebSocket manager instance"""
    return ws_manager
