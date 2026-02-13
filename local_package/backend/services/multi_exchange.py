"""
Multi-Exchange Support
=======================
Unified interface for trading across multiple exchanges:
- Kraken (existing)
- Binance
- Coinbase

Provides unified portfolio view and cross-exchange arbitrage detection.
"""

import os
import hmac
import hashlib
import time
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


class ExchangeInterface(ABC):
    """Abstract base class for exchange interfaces"""
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, float]:
        """Get account balances"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current price for a symbol"""
        pass
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict:
        """Get order book"""
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Dict:
        """Place an order"""
        pass
    
    @abstractmethod
    async def get_open_orders(self) -> List[Dict]:
        """Get open orders"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        pass


class BinanceExchange(ExchangeInterface):
    """Binance exchange interface"""
    
    BASE_URL = "https://api.binance.com"
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.name = "binance"
        
    def _sign_request(self, params: Dict) -> str:
        """Sign request with HMAC SHA256"""
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        signed: bool = False
    ) -> Dict:
        """Make API request"""
        params = params or {}
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key} if self.api_key else {}
        
        if signed and self.api_secret:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign_request(params)
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=params, headers=headers) as resp:
                    return await resp.json()
            elif method == "POST":
                async with session.post(url, params=params, headers=headers) as resp:
                    return await resp.json()
            elif method == "DELETE":
                async with session.delete(url, params=params, headers=headers) as resp:
                    return await resp.json()
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balances"""
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            data = await self._request("GET", "/api/v3/account", signed=True)
            balances = {}
            for asset in data.get("balances", []):
                free = float(asset.get("free", 0))
                locked = float(asset.get("locked", 0))
                total = free + locked
                if total > 0:
                    balances[asset["asset"]] = {
                        "total": total,
                        "free": free,
                        "locked": locked
                    }
            return balances
        except Exception as e:
            logger.error(f"Binance balance error: {e}")
            return {"error": str(e)}
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current price"""
        try:
            # Convert symbol format (BTC/USD -> BTCUSDT)
            binance_symbol = symbol.replace("/", "").replace("USD", "USDT")
            data = await self._request("GET", "/api/v3/ticker/24hr", {"symbol": binance_symbol})
            return {
                "symbol": symbol,
                "price": float(data.get("lastPrice", 0)),
                "bid": float(data.get("bidPrice", 0)),
                "ask": float(data.get("askPrice", 0)),
                "volume": float(data.get("volume", 0)),
                "change_24h": float(data.get("priceChangePercent", 0)),
                "exchange": self.name
            }
        except Exception as e:
            logger.error(f"Binance ticker error: {e}")
            return {"error": str(e)}
    
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict:
        """Get order book"""
        try:
            binance_symbol = symbol.replace("/", "").replace("USD", "USDT")
            data = await self._request("GET", "/api/v3/depth", {
                "symbol": binance_symbol,
                "limit": depth
            })
            return {
                "symbol": symbol,
                "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
                "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
                "exchange": self.name
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Dict:
        """Place an order"""
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            binance_symbol = symbol.replace("/", "").replace("USD", "USDT")
            params = {
                "symbol": binance_symbol,
                "side": side.upper(),
                "type": order_type.upper(),
                "quantity": quantity
            }
            if price and order_type.upper() == "LIMIT":
                params["price"] = price
                params["timeInForce"] = "GTC"
            
            data = await self._request("POST", "/api/v3/order", params, signed=True)
            return {
                "order_id": data.get("orderId"),
                "symbol": symbol,
                "status": data.get("status"),
                "exchange": self.name
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_open_orders(self) -> List[Dict]:
        """Get open orders"""
        if not self.api_key:
            return []
        
        try:
            data = await self._request("GET", "/api/v3/openOrders", signed=True)
            return [
                {
                    "order_id": o.get("orderId"),
                    "symbol": o.get("symbol"),
                    "side": o.get("side"),
                    "price": float(o.get("price", 0)),
                    "quantity": float(o.get("origQty", 0)),
                    "filled": float(o.get("executedQty", 0)),
                    "exchange": self.name
                }
                for o in data
            ]
        except Exception as e:
            return []
    
    async def cancel_order(self, order_id: str, symbol: str = None) -> Dict:
        """Cancel an order"""
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            params = {"orderId": order_id}
            if symbol:
                params["symbol"] = symbol.replace("/", "").replace("USD", "USDT")
            data = await self._request("DELETE", "/api/v3/order", params, signed=True)
            return {"status": "cancelled", "order_id": order_id}
        except Exception as e:
            return {"error": str(e)}


class CoinbaseExchange(ExchangeInterface):
    """Coinbase Advanced Trade interface"""
    
    BASE_URL = "https://api.coinbase.com"
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.getenv("COINBASE_API_KEY")
        self.api_secret = api_secret or os.getenv("COINBASE_API_SECRET")
        self.name = "coinbase"
    
    def _sign_request(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Sign request for Coinbase"""
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        body: Dict = None
    ) -> Dict:
        """Make API request"""
        url = f"{self.BASE_URL}{endpoint}"
        timestamp = str(int(time.time()))
        
        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
        
        body_str = ""
        if body:
            import json
            body_str = json.dumps(body)
        
        if self.api_secret:
            headers["CB-ACCESS-SIGN"] = self._sign_request(
                timestamp, method, endpoint, body_str
            )
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=params, headers=headers) as resp:
                    return await resp.json()
            elif method == "POST":
                async with session.post(url, json=body, headers=headers) as resp:
                    return await resp.json()
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balances"""
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            data = await self._request("GET", "/api/v3/brokerage/accounts")
            balances = {}
            for account in data.get("accounts", []):
                currency = account.get("currency")
                available = float(account.get("available_balance", {}).get("value", 0))
                hold = float(account.get("hold", {}).get("value", 0))
                if available + hold > 0:
                    balances[currency] = {
                        "total": available + hold,
                        "free": available,
                        "locked": hold
                    }
            return balances
        except Exception as e:
            logger.error(f"Coinbase balance error: {e}")
            return {"error": str(e)}
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current price"""
        try:
            # Convert symbol format (BTC/USD -> BTC-USD)
            coinbase_symbol = symbol.replace("/", "-")
            data = await self._request("GET", f"/api/v3/brokerage/products/{coinbase_symbol}/ticker")
            return {
                "symbol": symbol,
                "price": float(data.get("price", 0)),
                "bid": float(data.get("best_bid", 0)),
                "ask": float(data.get("best_ask", 0)),
                "volume": float(data.get("volume_24h", 0)),
                "exchange": self.name
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict:
        """Get order book"""
        try:
            coinbase_symbol = symbol.replace("/", "-")
            data = await self._request("GET", f"/api/v3/brokerage/products/{coinbase_symbol}/book", {
                "limit": depth
            })
            return {
                "symbol": symbol,
                "bids": [[float(b["price"]), float(b["size"])] for b in data.get("bids", [])],
                "asks": [[float(a["price"]), float(a["size"])] for a in data.get("asks", [])],
                "exchange": self.name
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Dict:
        """Place an order"""
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            coinbase_symbol = symbol.replace("/", "-")
            order_config = {}
            
            if order_type.upper() == "MARKET":
                order_config["market_market_ioc"] = {"quote_size": str(quantity)}
            else:
                order_config["limit_limit_gtc"] = {
                    "base_size": str(quantity),
                    "limit_price": str(price)
                }
            
            body = {
                "client_order_id": f"order_{int(time.time() * 1000)}",
                "product_id": coinbase_symbol,
                "side": side.upper(),
                "order_configuration": order_config
            }
            
            data = await self._request("POST", "/api/v3/brokerage/orders", body=body)
            return {
                "order_id": data.get("order_id"),
                "symbol": symbol,
                "status": data.get("status"),
                "exchange": self.name
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_open_orders(self) -> List[Dict]:
        """Get open orders"""
        if not self.api_key:
            return []
        
        try:
            data = await self._request("GET", "/api/v3/brokerage/orders/historical/batch", {
                "order_status": "OPEN"
            })
            return [
                {
                    "order_id": o.get("order_id"),
                    "symbol": o.get("product_id"),
                    "side": o.get("side"),
                    "price": float(o.get("average_filled_price", 0)),
                    "quantity": float(o.get("base_size", 0)),
                    "exchange": self.name
                }
                for o in data.get("orders", [])
            ]
        except Exception as e:
            return []
    
    async def cancel_order(self, order_id: str, symbol: str = None) -> Dict:
        """Cancel an order"""
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            data = await self._request("POST", "/api/v3/brokerage/orders/batch_cancel", body={
                "order_ids": [order_id]
            })
            return {"status": "cancelled", "order_id": order_id}
        except Exception as e:
            return {"error": str(e)}


class MultiExchangeManager:
    """
    Unified manager for multiple exchanges.
    Provides consolidated portfolio view and cross-exchange operations.
    """
    
    def __init__(self, db=None):
        self.db = db
        
        # Initialize exchanges
        self.exchanges: Dict[str, ExchangeInterface] = {}
        
        # Try to initialize Binance
        if os.getenv("BINANCE_API_KEY"):
            self.exchanges["binance"] = BinanceExchange()
            logger.info("✅ Binance exchange initialized")
        
        # Try to initialize Coinbase
        if os.getenv("COINBASE_API_KEY"):
            self.exchanges["coinbase"] = CoinbaseExchange()
            logger.info("✅ Coinbase exchange initialized")
        
        # Kraken is handled separately by existing service
        
        logger.info(f"📊 Multi-Exchange Manager: {len(self.exchanges)} exchanges configured")
    
    def get_available_exchanges(self) -> List[str]:
        """Get list of available exchanges"""
        return list(self.exchanges.keys())
    
    async def get_unified_balance(self) -> Dict:
        """Get consolidated balance across all exchanges"""
        unified = {
            "total_usd_value": 0,
            "exchanges": {},
            "by_asset": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Get balances from each exchange
        for name, exchange in self.exchanges.items():
            try:
                balance = await exchange.get_balance()
                if "error" not in balance:
                    unified["exchanges"][name] = balance
                    
                    # Aggregate by asset
                    for asset, amounts in balance.items():
                        if asset not in unified["by_asset"]:
                            unified["by_asset"][asset] = {
                                "total": 0,
                                "by_exchange": {}
                            }
                        
                        if isinstance(amounts, dict):
                            total = amounts.get("total", 0)
                        else:
                            total = amounts
                        
                        unified["by_asset"][asset]["total"] += total
                        unified["by_asset"][asset]["by_exchange"][name] = total
            except Exception as e:
                logger.error(f"Error getting {name} balance: {e}")
                unified["exchanges"][name] = {"error": str(e)}
        
        return unified
    
    async def get_best_price(self, symbol: str) -> Dict:
        """Get best price across all exchanges for a symbol"""
        prices = {}
        
        for name, exchange in self.exchanges.items():
            try:
                ticker = await exchange.get_ticker(symbol)
                if "error" not in ticker:
                    prices[name] = ticker
            except Exception as e:
                logger.warning(f"Error getting {name} price for {symbol}: {e}")
        
        if not prices:
            return {"error": "No prices available"}
        
        # Find best bid (highest) and best ask (lowest)
        best_bid = max(prices.values(), key=lambda x: x.get("bid", 0))
        best_ask = min(prices.values(), key=lambda x: x.get("ask", float("inf")))
        
        return {
            "symbol": symbol,
            "prices": prices,
            "best_bid": {
                "price": best_bid.get("bid"),
                "exchange": best_bid.get("exchange")
            },
            "best_ask": {
                "price": best_ask.get("ask"),
                "exchange": best_ask.get("exchange")
            },
            "spread_pct": ((best_ask.get("ask", 0) - best_bid.get("bid", 0)) / best_bid.get("bid", 1)) * 100 if best_bid.get("bid") else 0,
            "arbitrage_opportunity": best_bid.get("bid", 0) > best_ask.get("ask", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def detect_arbitrage(self, symbols: List[str] = None) -> List[Dict]:
        """Detect arbitrage opportunities across exchanges"""
        symbols = symbols or ["BTC/USD", "ETH/USD", "SOL/USD"]
        opportunities = []
        
        for symbol in symbols:
            price_data = await self.get_best_price(symbol)
            
            if price_data.get("arbitrage_opportunity"):
                opportunities.append({
                    "symbol": symbol,
                    "buy_exchange": price_data["best_ask"]["exchange"],
                    "buy_price": price_data["best_ask"]["price"],
                    "sell_exchange": price_data["best_bid"]["exchange"],
                    "sell_price": price_data["best_bid"]["price"],
                    "profit_pct": ((price_data["best_bid"]["price"] - price_data["best_ask"]["price"]) / price_data["best_ask"]["price"]) * 100,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        return opportunities
    
    async def smart_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET"
    ) -> Dict:
        """
        Place order on the best exchange for the given trade.
        """
        # Get best price
        price_data = await self.get_best_price(symbol)
        
        if "error" in price_data:
            return price_data
        
        # Determine best exchange based on side
        if side.upper() == "BUY":
            best_exchange = price_data["best_ask"]["exchange"]
        else:
            best_exchange = price_data["best_bid"]["exchange"]
        
        if best_exchange not in self.exchanges:
            return {"error": f"Exchange {best_exchange} not available"}
        
        exchange = self.exchanges[best_exchange]
        
        # Place order
        result = await exchange.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity
        )
        
        result["selected_exchange"] = best_exchange
        result["selection_reason"] = f"Best {'ask' if side.upper() == 'BUY' else 'bid'} price"
        
        return result
    
    def get_status(self) -> Dict:
        """Get manager status"""
        return {
            "exchanges_configured": list(self.exchanges.keys()),
            "exchanges_count": len(self.exchanges),
            "supported_exchanges": ["kraken", "binance", "coinbase"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_multi_exchange: Optional[MultiExchangeManager] = None


def get_multi_exchange_manager(db=None) -> MultiExchangeManager:
    """Get or create multi-exchange manager singleton"""
    global _multi_exchange
    if _multi_exchange is None:
        _multi_exchange = MultiExchangeManager(db)
    return _multi_exchange
