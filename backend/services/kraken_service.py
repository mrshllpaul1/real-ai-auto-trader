import hashlib
import hmac
import base64
import urllib.parse
import time
from httpx import AsyncClient
from typing import Dict, Any, Optional
import json

class KrakenAuthenticator:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = "https://api.kraken.com"
        
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
    
    async def request(
        self,
        endpoint: str,
        method: str = "POST",
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Kraken API"""
        if params is None:
            params = {}
        
        nonce = self._get_nonce()
        params['nonce'] = nonce
        urlpath = f"/0/private/{endpoint}"
        
        signature = self._get_signature(urlpath, params, nonce)
        
        headers = {
            "API-Key": self.api_key,
            "API-Sign": signature,
            "User-Agent": "CryptoTradingBot/1.0"
        }
        
        async with AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}{urlpath}",
                data=params,
                headers=headers
            )
            return response.json()

class KrakenTradeService:
    def __init__(self, authenticator: KrakenAuthenticator):
        self.auth = authenticator
        self.api_url = "https://api.kraken.com"
    
    async def get_balance(self) -> Dict[str, float]:
        """Retrieve all account balances"""
        response = await self.auth.request("Balance")
        if response.get("error"):
            raise Exception(f"Kraken API error: {response['error']}")
        return response.get("result", {})
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Alias for get_balance"""
        return await self.get_balance()
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker for a single trading pair (public endpoint)"""
        async with AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/0/public/Ticker",
                params={"pair": symbol}
            )
            data = response.json()
            if data.get("error"):
                return None
            result = data.get("result", {})
            # Return the first (and only) ticker
            for key, ticker in result.items():
                return ticker
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

class KrakenMarketService:
    def __init__(self):
        self.api_url = "https://api.kraken.com"
    
    async def get_ticker(self, pairs: list) -> Dict[str, Any]:
        """Get ticker information for specified trading pairs"""
        params = {"pair": ",".join(pairs)}
        async with AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/0/public/Ticker",
                params=params,
                headers={"User-Agent": "CryptoTradingBot/1.0"}
            )
            data = response.json()
            if data.get("error"):
                raise Exception(f"Kraken API error: {data['error']}")
            return data.get("result", {})
    
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
        async with AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/0/public/OHLC",
                params=params,
                headers={"User-Agent": "CryptoTradingBot/1.0"}
            )
            data = response.json()
            if data.get("error"):
                raise Exception(f"Kraken API error: {data['error']}")
            return data.get("result", {})