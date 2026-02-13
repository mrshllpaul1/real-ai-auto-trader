import hashlib
import hmac
import base64
import urllib.parse
import time
from httpx import AsyncClient
from typing import Dict, Any, Optional
import json

# Import circuit breaker for API protection
try:
    from utils.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

class KrakenAuthenticator:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = "https://api.kraken.com"
        # Initialize circuit breaker for Kraken API protection
        if CIRCUIT_BREAKER_AVAILABLE:
            self._circuit_breaker = get_circuit_breaker(
                "kraken_auth",
                failure_threshold=3,
                recovery_timeout=30
            )
        
    def _get_nonce(self) -> str:
        return str(int(time.time() * 1000))
    
    def _get_signature(self, urlpath: str, data: Dict[str, Any], nonce: str) -> str:
        """Generate HMAC-SHA512 signature for Kraken API request"""
        postdata = urllib.parse.urlencode(data)
        encoded = (nonce + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        
        mac = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        )
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()
    
    async def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Internal method to make the actual API request"""
        nonce = self._get_nonce()
        params['nonce'] = nonce
        urlpath = f"/0/private/{endpoint}"
        
        signature = self._get_signature(urlpath, params, nonce)
        
        headers = {
            "API-Key": self.api_key,
            "API-Sign": signature,
            "User-Agent": "CryptoTradingBot/1.0"
        }
        
        async with AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.api_url}{urlpath}",
                data=params,
                headers=headers
            )
            result = response.json()
            if result.get("error") and len(result["error"]) > 0:
                raise Exception(f"Kraken API error: {result['error']}")
            return result
    
    async def request(
        self,
        endpoint: str,
        method: str = "POST",
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Kraken API with circuit breaker protection"""
        if params is None:
            params = {}
        
        # Use circuit breaker if available
        if CIRCUIT_BREAKER_AVAILABLE:
            try:
                return await self._circuit_breaker.call(
                    self._make_request,
                    endpoint,
                    params
                )
            except CircuitBreakerOpenError as e:
                # Return error response when circuit is open
                return {"error": [f"Service temporarily unavailable: {e}"]}
        else:
            return await self._make_request(endpoint, params)

class KrakenTradeService:
    def __init__(self, authenticator: KrakenAuthenticator):
        self.auth = authenticator
        self.api_url = "https://api.kraken.com"
        self._api_timeout = 10.0  # 10 second timeout for all API calls
        # Circuit breaker for public API calls
        if CIRCUIT_BREAKER_AVAILABLE:
            self._public_circuit_breaker = get_circuit_breaker(
                "kraken_public",
                failure_threshold=5,
                recovery_timeout=20
            )
    
    async def get_balance(self) -> Dict[str, float]:
        """Retrieve all account balances"""
        response = await self.auth.request("Balance")
        if response.get("error"):
            raise Exception(f"Kraken API error: {response['error']}")
        return response.get("result", {})
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Alias for get_balance"""
        return await self.get_balance()
    
    async def _fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Internal method to fetch ticker data"""
        async with AsyncClient(timeout=self._api_timeout) as client:
            response = await client.get(
                f"{self.api_url}/0/public/Ticker",
                params={"pair": symbol}
            )
            data = response.json()
            if data.get("error") and len(data["error"]) > 0:
                raise Exception(f"Kraken API error: {data['error']}")
            result = data.get("result", {})
            for key, ticker in result.items():
                return ticker
            return None
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker for a single trading pair (public endpoint) with circuit breaker"""
        try:
            if CIRCUIT_BREAKER_AVAILABLE:
                return await self._public_circuit_breaker.call(
                    self._fetch_ticker,
                    symbol
                )
            else:
                return await self._fetch_ticker(symbol)
        except CircuitBreakerOpenError:
            print(f"Kraken public API circuit breaker open for {symbol}")
            return None
        except Exception as e:
            print(f"Kraken ticker error for {symbol}: {e}")
            return None
    
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        volume: float,
        price: float = None
    ) -> Dict[str, Any]:
        """Create a new order"""
        params = {
            "pair": symbol,
            "type": side.lower(),
            "ordertype": order_type.lower(),
            "volume": str(volume)
        }
        
        if price and order_type.lower() != 'market':
            params["price"] = str(price)
        
        response = await self.auth.request("AddOrder", params=params)
        if response.get("error"):
            print(f"Kraken order error: {response['error']}")
            return None
        return response.get("result", {})
    
    async def get_open_orders(self) -> Dict[str, Any]:
        """Retrieve all account balances"""
        response = await self.auth.request("Balance")
        if response.get("error"):
            raise Exception(f"Kraken API error: {response['error']}")
        return response.get("result", {})
    
    async def get_open_orders(self) -> Dict[str, Any]:
        """Retrieve all open orders"""
        response = await self.auth.request("OpenOrders")
        if response.get("error"):
            raise Exception(f"Kraken API error: {response['error']}")
        return response.get("result", {})
    
    async def place_order(
        self,
        pair: str,
        side: str,
        ordertype: str,
        price: str,
        volume: str,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Place a new order"""
        params = {
            "pair": pair,
            "type": side,
            "ordertype": ordertype,
            "price": price,
            "volume": volume
        }
        
        if client_order_id:
            params["cl_ord_id"] = client_order_id
        
        response = await self.auth.request("AddOrder", params=params)
        if response.get("error"):
            raise Exception(f"Kraken API error: {response['error']}")
        return response.get("result", {})
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an open order"""
        response = await self.auth.request("CancelOrder", params={"txid": order_id})
        if response.get("error"):
            raise Exception(f"Kraken API error: {response['error']}")
        return response.get("result", {})
    
    async def get_trades_history(self, start: int = None, end: int = None, ofs: int = 0) -> Dict[str, Any]:
        """Get trade history from Kraken
        
        Args:
            start: Starting unix timestamp (optional)
            end: Ending unix timestamp (optional)
            ofs: Result offset for pagination
            
        Returns:
            Dict with 'trades' containing trade history and 'count' for total
        """
        params = {"ofs": ofs}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
            
        response = await self.auth.request("TradesHistory", params=params)
        if response.get("error"):
            print(f"Kraken trades history error: {response['error']}")
            return {"trades": {}, "count": 0}
        return response.get("result", {"trades": {}, "count": 0})
    
    async def get_closed_orders(self, start: int = None, end: int = None, ofs: int = 0) -> Dict[str, Any]:
        """Get closed orders history from Kraken
        
        Args:
            start: Starting unix timestamp (optional)
            end: Ending unix timestamp (optional)
            ofs: Result offset for pagination
            
        Returns:
            Dict with 'closed' containing closed orders
        """
        params = {"ofs": ofs}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
            
        response = await self.auth.request("ClosedOrders", params=params)
        if response.get("error"):
            print(f"Kraken closed orders error: {response['error']}")
            return {"closed": {}}
        return response.get("result", {"closed": {}})
    
    async def get_tickers_batch(self, pairs: list) -> Dict[str, Any]:
        """Get ticker information for multiple trading pairs in one request (public endpoint)"""
        if not pairs:
            return {}
        
        params = {"pair": ",".join(pairs)}
        try:
            async with AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_url}/0/public/Ticker",
                    params=params,
                    headers={"User-Agent": "CryptoTradingBot/1.0"}
                )
                data = response.json()
                # Kraken returns partial results even with errors for some pairs
                # Only fail completely if no results at all
                result = data.get("result", {})
                if data.get("error") and not result:
                    print(f"Kraken batch ticker error: {data['error']}")
                    return {}
                return result
        except Exception as e:
            print(f"Kraken batch ticker timeout/error: {e}")
            return {}

class KrakenMarketService:
    def __init__(self):
        self.api_url = "https://api.kraken.com"
        self._api_timeout = 10.0
    
    async def get_ticker(self, pairs: list) -> Dict[str, Any]:
        """Get ticker information for specified trading pairs"""
        params = {"pair": ",".join(pairs)}
        try:
            async with AsyncClient(timeout=self._api_timeout) as client:
                response = await client.get(
                    f"{self.api_url}/0/public/Ticker",
                    params=params,
                    headers={"User-Agent": "CryptoTradingBot/1.0"}
                )
                data = response.json()
                if data.get("error"):
                    raise Exception(f"Kraken API error: {data['error']}")
                return data.get("result", {})
        except Exception as e:
            print(f"Kraken ticker error: {e}")
            return {}
    
    async def get_ohlc(
        self,
        pair: str,
        interval: int = 60
    ) -> Dict[str, Any]:
        """Get OHLC (candlestick) data for a trading pair"""
        params = {
            "pair": pair,
            "interval": interval
        }
        try:
            async with AsyncClient(timeout=self._api_timeout) as client:
                response = await client.get(
                    f"{self.api_url}/0/public/OHLC",
                    params=params,
                    headers={"User-Agent": "CryptoTradingBot/1.0"}
                )
                data = response.json()
                if data.get("error"):
                    raise Exception(f"Kraken API error: {data['error']}")
                return data.get("result", {})
        except Exception as e:
            print(f"Kraken OHLC error: {e}")
            return {}


# Singleton instance for Kraken Trade Service
_kraken_service: Optional[KrakenTradeService] = None


def get_kraken_service() -> Optional[KrakenTradeService]:
    """Get the singleton Kraken Trade Service instance"""
    return _kraken_service


def set_kraken_service(service: KrakenTradeService):
    """Set the singleton Kraken Trade Service instance"""
    global _kraken_service
    _kraken_service = service