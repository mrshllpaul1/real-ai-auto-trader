"""
WebSocket Routes
===============
WebSocket endpoints for real-time communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List, Optional
import asyncio
import json
from services.websocket_manager import ws_manager, broadcast_price_update
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ws", tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    channels: Optional[str] = Query(default="all")
):
    """
    WebSocket endpoint for real-time updates.
    
    Query params:
    - channels: Comma-separated list of channels to subscribe to
      Options: prices, portfolio, signals, training, alerts, all
    
    Example: /api/ws/connect?channels=prices,signals
    """
    channel_list = [c.strip() for c in channels.split(',')] if channels else ['all']
    
    await ws_manager.connect(websocket, channel_list)
    
    try:
        # Send initial connection confirmation
        await ws_manager.send_personal(websocket, {
            'type': 'connected',
            'channels': channel_list,
            'message': 'Successfully connected to WebSocket'
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # Ping timeout
                )
                
                # Handle client messages
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, message)
                except json.JSONDecodeError:
                    await ws_manager.send_personal(websocket, {
                        'type': 'error',
                        'message': 'Invalid JSON'
                    })
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({'type': 'ping'})
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle incoming messages from client."""
    msg_type = message.get('type')
    
    if msg_type == 'pong':
        # Client responded to ping
        pass
    
    elif msg_type == 'subscribe':
        # Subscribe to additional channels
        channels = message.get('channels', [])
        for channel in channels:
            if channel in ws_manager.connections:
                ws_manager.connections[channel].add(websocket)
        await ws_manager.send_personal(websocket, {
            'type': 'subscribed',
            'channels': channels
        })
    
    elif msg_type == 'unsubscribe':
        # Unsubscribe from channels
        channels = message.get('channels', [])
        for channel in channels:
            if channel in ws_manager.connections:
                ws_manager.connections[channel].discard(websocket)
        await ws_manager.send_personal(websocket, {
            'type': 'unsubscribed',
            'channels': channels
        })
    
    else:
        await ws_manager.send_personal(websocket, {
            'type': 'error',
            'message': f'Unknown message type: {msg_type}'
        })


@router.get("/status")
async def get_websocket_status():
    """Get WebSocket connection statistics."""
    return {
        'status': 'ok',
        'connections': ws_manager.get_connection_count()
    }
