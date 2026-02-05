"""
Kraken WebSocket Order Book Service
====================================
Real-time Level 2 order book data via Kraken WebSocket API.

Features:
- Live order book streaming (bids/asks)
- Order book state management
- Configurable depth (10, 25, 100, 500, 1000 levels)
- Automatic reconnection
- Order book features for RL (spread, imbalance, depth)

WebSocket: wss://ws.kraken.com/v2
"""

import logging
import asyncio
import json
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from collections import deque
import websockets
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class OrderBookLevel:
    """Single price level in order book"""
    price: float
    quantity: float
    timestamp: float = 0.0


@dataclass
class OrderBook:
    """Order book state for a trading pair"""
    symbol: str
    bids: Dict[float, OrderBookLevel] = field(default_factory=dict)  # price -> level
    asks: Dict[float, OrderBookLevel] = field(default_factory=dict)
    last_update: float = 0.0
    snapshot_received: bool = False
    
    def get_best_bid(self) -> Optional[OrderBookLevel]:
        """Get best (highest) bid"""
        if not self.bids:
            return None
        best_price = max(self.bids.keys())
        return self.bids[best_price]
    
    def get_best_ask(self) -> Optional[OrderBookLevel]:
        """Get best (lowest) ask"""
        if not self.asks:
            return None
        best_price = min(self.asks.keys())
        return self.asks[best_price]
    
    def get_spread(self) -> float:
        """Get bid-ask spread"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return best_ask.price - best_bid.price
        return 0.0
    
    def get_mid_price(self) -> float:
        """Get mid-market price"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return (best_bid.price + best_ask.price) / 2
        return 0.0
    
    def get_imbalance(self, levels: int = 5) -> float:
        """
        Calculate order book imbalance.
        Positive = more bid volume (bullish pressure)
        Negative = more ask volume (bearish pressure)
        """
        sorted_bids = sorted(self.bids.keys(), reverse=True)[:levels]
        sorted_asks = sorted(self.asks.keys())[:levels]
        
        bid_volume = sum(self.bids[p].quantity for p in sorted_bids)
        ask_volume = sum(self.asks[p].quantity for p in sorted_asks)
        
        total = bid_volume + ask_volume
        if total == 0:
            return 0.0
        
        return (bid_volume - ask_volume) / total
    
    def get_depth(self, levels: int = 10) -> Dict[str, float]:
        """Get order book depth metrics"""
        sorted_bids = sorted(self.bids.keys(), reverse=True)[:levels]
        sorted_asks = sorted(self.asks.keys())[:levels]
        
        bid_depth = sum(self.bids[p].quantity * self.bids[p].price for p in sorted_bids)
        ask_depth = sum(self.asks[p].quantity * self.asks[p].price for p in sorted_asks)
        
        return {
            'bid_depth_usd': bid_depth,
            'ask_depth_usd': ask_depth,
            'total_depth_usd': bid_depth + ask_depth,
            'bid_levels': len(sorted_bids),
            'ask_levels': len(sorted_asks)
        }
    
    def get_vwap(self, side: str, depth_usd: float = 10000) -> float:
        """Calculate VWAP for executing a certain USD amount"""
        if side == 'buy':
            levels = sorted(self.asks.items())
        else:
            levels = sorted(self.bids.items(), reverse=True)
        
        total_value = 0.0
        total_qty = 0.0
        remaining = depth_usd
        
        for price, level in levels:
            level_value = level.quantity * price
            if level_value >= remaining:
                qty_needed = remaining / price
                total_value += qty_needed * price
                total_qty += qty_needed
                break
            else:
                total_value += level_value
                total_qty += level.quantity
                remaining -= level_value
        
        return total_value / total_qty if total_qty > 0 else 0.0
    
    def to_features(self, levels: int = 10) -> np.ndarray:
        """
        Convert order book to feature vector for RL.
        
        Features (per level):
        - bid_price, bid_qty, ask_price, ask_qty
        
        Aggregate features:
        - spread, mid_price, imbalance, bid_depth, ask_depth
        """
        sorted_bids = sorted(self.bids.keys(), reverse=True)[:levels]
        sorted_asks = sorted(self.asks.keys())[:levels]
        
        mid = self.get_mid_price() or 1.0
        
        features = []
        
        # Per-level features (normalized by mid price)
        for i in range(levels):
            if i < len(sorted_bids):
                bid = self.bids[sorted_bids[i]]
                features.extend([
                    (bid.price - mid) / mid,  # Normalized price distance
                    bid.quantity
                ])
            else:
                features.extend([0.0, 0.0])
            
            if i < len(sorted_asks):
                ask = self.asks[sorted_asks[i]]
                features.extend([
                    (ask.price - mid) / mid,
                    ask.quantity
                ])
            else:
                features.extend([0.0, 0.0])
        
        # Aggregate features
        spread = self.get_spread()
        imbalance = self.get_imbalance(levels)
        depth = self.get_depth(levels)
        
        features.extend([
            spread / mid if mid > 0 else 0,  # Relative spread
            imbalance,
            np.log1p(depth['bid_depth_usd']),
            np.log1p(depth['ask_depth_usd']),
            np.log1p(depth['total_depth_usd'])
        ])
        
        return np.array(features, dtype=np.float32)


class KrakenOrderBookWebSocket:
    """
    Kraken WebSocket client for real-time order book data.
    
    Uses WebSocket v2 API: wss://ws.kraken.com/v2
    """
    
    def __init__(
        self,
        symbols: List[str] = None,
        depth: int = 25,
        on_update: Optional[Callable] = None
    ):
        self.ws_url = "wss://ws.kraken.com/v2"
        self.symbols = symbols or ["BTC/USD", "ETH/USD"]
        self.depth = depth
        self.on_update = on_update
        
        # Order books
        self.order_books: Dict[str, OrderBook] = {}
        for symbol in self.symbols:
            self.order_books[symbol] = OrderBook(symbol=symbol)
        
        # Connection state
        self.ws = None
        self.connected = False
        self.running = False
        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 60.0
        
        # History for features
        self.feature_history: Dict[str, deque] = {
            symbol: deque(maxlen=168)  # 1 week of hourly snapshots
            for symbol in self.symbols
        }
        
        # Stats
        self.message_count = 0
        self.last_message_time = None
        self.errors = []
        
    async def connect(self):
        """Connect to Kraken WebSocket"""
        try:
            self.ws = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            self.connected = True
            self.reconnect_delay = 1.0
            logger.info(f"Connected to Kraken WebSocket: {self.ws_url}")
            
            # Subscribe to order book
            await self._subscribe()
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            self.connected = False
            raise
    
    async def _subscribe(self):
        """Subscribe to order book channel"""
        subscribe_msg = {
            "method": "subscribe",
            "params": {
                "channel": "book",
                "symbol": self.symbols,
                "depth": self.depth
            }
        }
        
        await self.ws.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to order book: {self.symbols}, depth={self.depth}")
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            self.message_count += 1
            self.last_message_time = datetime.utcnow()
            
            # Skip system messages
            if isinstance(data, dict):
                if data.get("channel") == "status":
                    logger.debug(f"Status: {data}")
                    return
                if data.get("method") in ["subscribe", "unsubscribe"]:
                    logger.info(f"Subscription response: {data}")
                    return
                if data.get("channel") == "heartbeat":
                    return
            
            # Process book updates
            if isinstance(data, dict) and data.get("channel") == "book":
                await self._process_book_message(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            self.errors.append(str(e))
    
    async def _process_book_message(self, data: Dict):
        """Process order book snapshot or update"""
        msg_type = data.get("type")
        book_data = data.get("data", [])
        
        if not book_data:
            return
        
        for item in book_data:
            symbol = item.get("symbol")
            if not symbol or symbol not in self.order_books:
                continue
            
            book = self.order_books[symbol]
            
            if msg_type == "snapshot":
                # Clear and rebuild
                book.bids.clear()
                book.asks.clear()
                book.snapshot_received = True
                logger.info(f"Received order book snapshot for {symbol}")
            
            # Process bids
            for bid in item.get("bids", []):
                price = float(bid.get("price", 0))
                qty = float(bid.get("qty", 0))
                
                if qty == 0:
                    book.bids.pop(price, None)
                else:
                    book.bids[price] = OrderBookLevel(price=price, quantity=qty)
            
            # Process asks
            for ask in item.get("asks", []):
                price = float(ask.get("price", 0))
                qty = float(ask.get("qty", 0))
                
                if qty == 0:
                    book.asks.pop(price, None)
                else:
                    book.asks[price] = OrderBookLevel(price=price, quantity=qty)
            
            book.last_update = datetime.utcnow().timestamp()
            
            # Callback
            if self.on_update:
                await self.on_update(symbol, book)
    
    async def run(self):
        """Main run loop with auto-reconnect"""
        self.running = True
        
        while self.running:
            try:
                if not self.connected:
                    await self.connect()
                
                async for message in self.ws:
                    if not self.running:
                        break
                    await self._handle_message(message)
                    
            except websockets.ConnectionClosed as e:
                logger.warning(f"WebSocket closed: {e}")
                self.connected = False
                
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.connected = False
            
            if self.running and not self.connected:
                logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(
                    self.reconnect_delay * 2,
                    self.max_reconnect_delay
                )
    
    async def stop(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws:
            await self.ws.close()
        self.connected = False
        logger.info("WebSocket stopped")
    
    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get order book for symbol"""
        return self.order_books.get(symbol)
    
    def get_features(self, symbol: str, levels: int = 10) -> np.ndarray:
        """Get order book features for RL"""
        book = self.order_books.get(symbol)
        if book and book.snapshot_received:
            return book.to_features(levels)
        return np.zeros(levels * 4 + 5, dtype=np.float32)
    
    def get_feature_history(self, symbol: str) -> np.ndarray:
        """Get historical feature sequence for transformer"""
        history = self.feature_history.get(symbol)
        if history and len(history) > 0:
            return np.array(list(history))
        return np.array([])
    
    def snapshot_features(self, symbol: str, levels: int = 10):
        """Take a snapshot of current features for history"""
        features = self.get_features(symbol, levels)
        if symbol in self.feature_history:
            self.feature_history[symbol].append(features)
    
    def get_status(self) -> Dict[str, Any]:
        """Get WebSocket status"""
        return {
            "connected": self.connected,
            "running": self.running,
            "symbols": self.symbols,
            "depth": self.depth,
            "message_count": self.message_count,
            "last_message": self.last_message_time.isoformat() if self.last_message_time else None,
            "order_books": {
                symbol: {
                    "snapshot_received": book.snapshot_received,
                    "bid_levels": len(book.bids),
                    "ask_levels": len(book.asks),
                    "best_bid": book.get_best_bid().price if book.get_best_bid() else None,
                    "best_ask": book.get_best_ask().price if book.get_best_ask() else None,
                    "spread": book.get_spread(),
                    "imbalance": book.get_imbalance()
                }
                for symbol, book in self.order_books.items()
            },
            "errors": self.errors[-5:]  # Last 5 errors
        }


# =============================================================================
# ORDER BOOK FEATURE EXTRACTOR FOR RL
# =============================================================================

class OrderBookFeatureExtractor:
    """
    Extract RL-ready features from order book data.
    Designed for 168-timestep (1 week) transformer input.
    """
    
    def __init__(
        self,
        symbols: List[str] = None,
        levels: int = 10,
        sequence_length: int = 168
    ):
        self.symbols = symbols or ["BTC/USD"]
        self.levels = levels
        self.sequence_length = sequence_length
        
        # Feature dimensions
        self.per_level_features = 4  # bid_price, bid_qty, ask_price, ask_qty
        self.aggregate_features = 5  # spread, imbalance, bid_depth, ask_depth, total_depth
        self.features_per_book = levels * self.per_level_features + self.aggregate_features
        
        # History buffers
        self.history: Dict[str, deque] = {
            symbol: deque(maxlen=sequence_length)
            for symbol in self.symbols
        }
    
    def add_snapshot(self, symbol: str, order_book: OrderBook):
        """Add order book snapshot to history"""
        if symbol in self.history:
            features = order_book.to_features(self.levels)
            self.history[symbol].append(features)
    
    def get_sequence(self, symbol: str) -> np.ndarray:
        """
        Get feature sequence for transformer input.
        Shape: (sequence_length, features_per_book)
        """
        if symbol not in self.history:
            return np.zeros((self.sequence_length, self.features_per_book), dtype=np.float32)
        
        history = list(self.history[symbol])
        
        if len(history) < self.sequence_length:
            # Pad with zeros at the beginning
            padding = np.zeros(
                (self.sequence_length - len(history), self.features_per_book),
                dtype=np.float32
            )
            if history:
                return np.vstack([padding, np.array(history)])
            return padding
        
        return np.array(history[-self.sequence_length:], dtype=np.float32)
    
    def get_multi_symbol_sequence(self) -> np.ndarray:
        """
        Get combined sequence for all symbols.
        Shape: (sequence_length, num_symbols * features_per_book)
        """
        sequences = [self.get_sequence(symbol) for symbol in self.symbols]
        return np.concatenate(sequences, axis=1)
    
    @property
    def feature_dim(self) -> int:
        """Total feature dimension per timestep"""
        return len(self.symbols) * self.features_per_book


# =============================================================================
# SINGLETON & INITIALIZATION
# =============================================================================

_order_book_ws: Optional[KrakenOrderBookWebSocket] = None
_feature_extractor: Optional[OrderBookFeatureExtractor] = None

async def initialize_order_book_service(
    symbols: List[str] = None,
    depth: int = 25
) -> KrakenOrderBookWebSocket:
    """Initialize and start order book WebSocket"""
    global _order_book_ws, _feature_extractor
    
    symbols = symbols or ["BTC/USD", "ETH/USD", "SOL/USD"]
    
    _feature_extractor = OrderBookFeatureExtractor(
        symbols=symbols,
        levels=10,
        sequence_length=168
    )
    
    async def on_book_update(symbol: str, book: OrderBook):
        """Callback when order book updates"""
        if _feature_extractor:
            _feature_extractor.add_snapshot(symbol, book)
    
    _order_book_ws = KrakenOrderBookWebSocket(
        symbols=symbols,
        depth=depth,
        on_update=on_book_update
    )
    
    # Start in background
    asyncio.create_task(_order_book_ws.run())
    
    logger.info(f"Order book service initialized for {symbols}")
    return _order_book_ws


def get_order_book_service() -> Optional[KrakenOrderBookWebSocket]:
    """Get order book WebSocket instance"""
    return _order_book_ws


def get_feature_extractor() -> Optional[OrderBookFeatureExtractor]:
    """Get feature extractor instance"""
    return _feature_extractor
