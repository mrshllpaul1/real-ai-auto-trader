"""
SRDDQN Kraken Execution Integration
===================================
Connects SRDDQN agent signals to real Kraken trading execution.
"""

import logging
import asyncio
import hmac
import hashlib
import base64
import urllib.parse
import time
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import os
import aiohttp

logger = logging.getLogger(__name__)


class KrakenExecutor:
    """
    Executes SRDDQN signals on Kraken exchange.
    
    Features:
    - Real order placement
    - Order status tracking
    - Position management
    - Risk controls
    """
    
    BASE_URL = "https://api.kraken.com"
    
    def __init__(self, db):
        self.db = db
        self.api_key = os.environ.get('KRAKEN_API_KEY', '')
        self.api_secret = os.environ.get('KRAKEN_API_SECRET', '')
        
        # Trading state
        self.open_orders = {}
        self.positions = {}
        self.daily_volume = 0
        self.last_trade_time = None
        
        # Risk limits
        self.max_order_size_usd = 500  # Max single order
        self.max_daily_volume_usd = 2000
        self.min_order_interval_seconds = 60
        
        # Symbol mapping
        self.symbol_map = {
            'BTC': 'XXBTZUSD',
            'ETH': 'XETHZUSD',
            'SOL': 'SOLUSD',
            'ADA': 'ADAUSD',
            'DOT': 'DOTUSD',
            'LINK': 'LINKUSD',
            'AVAX': 'AVAXUSD',
            'MATIC': 'MATICUSD'
        }
        
    def _get_kraken_signature(self, urlpath: str, data: Dict, nonce: str) -> str:
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(nonce) + postdata).encode()
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
        data: Dict = None, 
        private: bool = False
    ) -> Dict:
        """Make request to Kraken API"""
        url = f"{self.BASE_URL}{endpoint}"
        
        headers = {}
        if private:
            nonce = str(int(time.time() * 1000))
            data = data or {}
            data['nonce'] = nonce
            
            headers['API-Key'] = self.api_key
            headers['API-Sign'] = self._get_kraken_signature(endpoint, data, nonce)
        
        try:
            async with aiohttp.ClientSession() as session:
                if private or data:
                    async with session.post(url, data=data, headers=headers) as response:
                        result = await response.json()
                else:
                    async with session.get(url) as response:
                        result = await response.json()
                
                if result.get('error') and len(result['error']) > 0:
                    logger.error(f"Kraken API error: {result['error']}")
                    return {'error': result['error']}
                
                return result.get('result', {})
                
        except Exception as e:
            logger.error(f"Kraken request error: {e}")
            return {'error': str(e)}
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        result = await self._make_request('/0/private/Balance', private=True)
        
        if 'error' in result:
            return {}
        
        balances = {}
        for asset, amount in result.items():
            # Clean asset names
            clean_name = asset.replace('X', '').replace('Z', '')
            balances[clean_name] = float(amount)
        
        return balances
    
    async def get_ticker(self, symbol: str = 'BTC') -> Dict[str, Any]:
        """Get current ticker data"""
        pair = self.symbol_map.get(symbol, 'XXBTZUSD')
        result = await self._make_request(f'/0/public/Ticker?pair={pair}')
        
        if 'error' in result:
            return {}
        
        ticker_data = list(result.values())[0] if result else {}
        
        return {
            'symbol': symbol,
            'ask': float(ticker_data.get('a', [0])[0]),
            'bid': float(ticker_data.get('b', [0])[0]),
            'last': float(ticker_data.get('c', [0])[0]),
            'volume': float(ticker_data.get('v', [0, 0])[1]),
            'high': float(ticker_data.get('h', [0, 0])[1]),
            'low': float(ticker_data.get('l', [0, 0])[1])
        }
    
    async def check_risk_limits(
        self,
        order_size_usd: float,
        symbol: str
    ) -> Tuple[bool, str]:
        """Check if order passes risk limits"""
        # Check max order size
        if order_size_usd > self.max_order_size_usd:
            return False, f"Order size ${order_size_usd:.2f} exceeds max ${self.max_order_size_usd}"
        
        # Check daily volume
        if self.daily_volume + order_size_usd > self.max_daily_volume_usd:
            return False, f"Would exceed daily volume limit ${self.max_daily_volume_usd}"
        
        # Check trade interval
        if self.last_trade_time:
            elapsed = (datetime.utcnow() - self.last_trade_time).total_seconds()
            if elapsed < self.min_order_interval_seconds:
                return False, f"Min interval not met ({elapsed:.0f}s < {self.min_order_interval_seconds}s)"
        
        return True, "Risk checks passed"
    
    async def execute_signal(
        self,
        signal: Dict[str, Any],
        portfolio_value: float = 10000
    ) -> Dict[str, Any]:
        """Execute SRDDQN trading signal"""
        signal_type = signal.get('signal', 'hold')
        symbol = signal.get('symbol', 'BTC')
        confidence = signal.get('confidence', 0)
        position = signal.get('position', 0)
        
        # Skip hold signals
        if signal_type == 'hold' or abs(position) < 0.1:
            return {
                'executed': False,
                'reason': 'Hold signal or low position size'
            }
        
        # Skip low confidence
        if confidence < 0.6:
            return {
                'executed': False,
                'reason': f'Low confidence ({confidence:.2f} < 0.6)'
            }
        
        # Calculate order size
        base_pct = 0.05  # 5% base
        if signal_type in ['strong_buy', 'strong_sell']:
            base_pct = 0.08  # 8% for strong signals
        
        order_value_usd = portfolio_value * base_pct * confidence
        
        # Apply risk limits
        allowed, reason = await self.check_risk_limits(order_value_usd, symbol)
        if not allowed:
            return {
                'executed': False,
                'reason': f'Risk limit: {reason}'
            }
        
        # Get current price
        ticker = await self.get_ticker(symbol)
        if not ticker or 'last' not in ticker:
            return {
                'executed': False,
                'reason': 'Could not get ticker data'
            }
        
        current_price = ticker['last']
        order_volume = order_value_usd / current_price
        
        # Determine order side
        if signal_type in ['buy', 'strong_buy']:
            side = 'buy'
        else:
            side = 'sell'
        
        # Place order
        result = await self.place_order(
            symbol=symbol,
            side=side,
            volume=order_volume,
            order_type='market'
        )
        
        if result.get('executed'):
            # Update tracking
            self.daily_volume += order_value_usd
            self.last_trade_time = datetime.utcnow()
            
            # Store in DB
            await self.db.srddqn_kraken_trades.insert_one({
                'signal': signal,
                'execution': result,
                'order_value_usd': order_value_usd,
                'created_at': datetime.utcnow()
            })
        
        return result
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        order_type: str = 'market',
        price: float = None
    ) -> Dict[str, Any]:
        """Place order on Kraken"""
        pair = self.symbol_map.get(symbol, 'XXBTZUSD')
        
        data = {
            'pair': pair,
            'type': side,
            'ordertype': order_type,
            'volume': f"{volume:.8f}"
        }
        
        if order_type == 'limit' and price:
            data['price'] = f"{price:.2f}"
        
        # Validate mode (only place real orders if we have keys)
        if not self.api_key or not self.api_secret:
            logger.warning("No Kraken API keys - simulating order")
            return {
                'executed': True,
                'simulated': True,
                'order_id': f"SIM_{int(time.time())}",
                'symbol': symbol,
                'side': side,
                'volume': volume,
                'order_type': order_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        result = await self._make_request('/0/private/AddOrder', data, private=True)
        
        if 'error' in result:
            return {
                'executed': False,
                'error': result['error']
            }
        
        order_ids = result.get('txid', [])
        
        return {
            'executed': True,
            'simulated': False,
            'order_id': order_ids[0] if order_ids else None,
            'symbol': symbol,
            'side': side,
            'volume': volume,
            'order_type': order_type,
            'description': result.get('descr', {}),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_open_orders(self) -> Dict[str, Any]:
        """Get open orders"""
        result = await self._make_request('/0/private/OpenOrders', private=True)
        
        if 'error' in result:
            return {}
        
        return result.get('open', {})
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        result = await self._make_request(
            '/0/private/CancelOrder',
            {'txid': order_id},
            private=True
        )
        
        return 'error' not in result
    
    async def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get trade history"""
        result = await self._make_request(
            '/0/private/TradesHistory',
            {'trades': True},
            private=True
        )
        
        if 'error' in result:
            return []
        
        trades = result.get('trades', {})
        
        trade_list = []
        for tid, trade in list(trades.items())[:limit]:
            trade_list.append({
                'id': tid,
                'pair': trade.get('pair'),
                'type': trade.get('type'),
                'price': float(trade.get('price', 0)),
                'volume': float(trade.get('vol', 0)),
                'cost': float(trade.get('cost', 0)),
                'time': datetime.fromtimestamp(trade.get('time', 0)).isoformat()
            })
        
        return trade_list
    
    def reset_daily_limits(self):
        """Reset daily trading limits"""
        self.daily_volume = 0
        logger.info("Daily trading limits reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get executor status"""
        return {
            'has_api_keys': bool(self.api_key and self.api_secret),
            'daily_volume_usd': self.daily_volume,
            'max_daily_volume_usd': self.max_daily_volume_usd,
            'max_order_size_usd': self.max_order_size_usd,
            'min_order_interval_seconds': self.min_order_interval_seconds,
            'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None,
            'supported_symbols': list(self.symbol_map.keys())
        }


# Singleton
_executor = None

def get_kraken_executor(db=None) -> KrakenExecutor:
    global _executor
    if _executor is None and db is not None:
        _executor = KrakenExecutor(db)
    return _executor


async def initialize_kraken_executor(db) -> KrakenExecutor:
    """Initialize Kraken executor"""
    global _executor
    _executor = KrakenExecutor(db)
    logger.info("Kraken Executor initialized")
    return _executor
