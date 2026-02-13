"""
Multi-Exchange Arbitrage Service
================================
Detect and execute arbitrage opportunities across multiple exchanges.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class ExchangePrice:
    """Price data from an exchange"""
    exchange: str
    symbol: str
    bid: float
    ask: float
    last: float
    volume_24h: float
    timestamp: str


@dataclass
class ArbitrageOpportunity:
    """Detected arbitrage opportunity"""
    id: str
    symbol: str
    buy_exchange: str
    buy_price: float
    sell_exchange: str
    sell_price: float
    spread: float
    spread_pct: float
    potential_profit: float
    volume_available: float
    timestamp: str
    status: str = 'detected'


class MultiExchangeArbitrage:
    """
    Multi-exchange arbitrage detection and execution.
    
    Supported exchanges:
    - Kraken (active)
    - Binance (framework)
    - Coinbase (framework)
    
    Features:
    - Real-time price monitoring
    - Spread calculation
    - Opportunity detection
    - Risk-adjusted execution
    """
    
    # Minimum spread to consider (accounts for fees)
    MIN_SPREAD_PCT = 0.5  # 0.5%
    
    # Exchange fee estimates
    EXCHANGE_FEES = {
        'kraken': 0.26,  # 0.26% taker fee
        'binance': 0.10,  # 0.10% with BNB
        'coinbase': 0.60,  # 0.60% taker fee
    }
    
    # Common trading pairs
    TRACKED_PAIRS = [
        'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'ADA/USD',
        'DOGE/USD', 'DOT/USD', 'AVAX/USD', 'LINK/USD', 'MATIC/USD'
    ]
    
    def __init__(self, db, kraken_service=None):
        self.db = db
        self.kraken = kraken_service
        self.prices: Dict[str, Dict[str, ExchangePrice]] = {}
        self.opportunities: List[ArbitrageOpportunity] = []
        self.is_monitoring = False
        self._monitor_task = None
        self.settings = {
            'min_spread_pct': self.MIN_SPREAD_PCT,
            'min_profit_usd': 10.0,
            'max_trade_size_usd': 1000.0,
            'auto_execute': False,
            'enabled_exchanges': ['kraken']
        }
        logger.info("✅ Multi-Exchange Arbitrage Service initialized")
    
    async def start_monitoring(self):
        """Start price monitoring across exchanges"""
        if self.is_monitoring:
            return {'status': 'already_running'}
        
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("📊 Arbitrage monitoring started")
        return {'status': 'started'}
    
    async def stop_monitoring(self):
        """Stop price monitoring"""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        logger.info("📊 Arbitrage monitoring stopped")
        return {'status': 'stopped'}
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._fetch_all_prices()
                await self._detect_opportunities()
                await asyncio.sleep(5)  # Check every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(10)
    
    async def _fetch_all_prices(self):
        """Fetch prices from all enabled exchanges"""
        tasks = []
        
        if 'kraken' in self.settings['enabled_exchanges']:
            tasks.append(self._fetch_kraken_prices())
        if 'binance' in self.settings['enabled_exchanges']:
            tasks.append(self._fetch_binance_prices())
        if 'coinbase' in self.settings['enabled_exchanges']:
            tasks.append(self._fetch_coinbase_prices())
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fetch_kraken_prices(self):
        """Fetch prices from Kraken"""
        try:
            if not self.kraken:
                return
            
            # Map common symbols to Kraken format
            kraken_pairs = {
                'BTC/USD': 'XXBTZUSD',
                'ETH/USD': 'XETHZUSD',
                'SOL/USD': 'SOLUSD',
                'XRP/USD': 'XXRPZUSD',
                'ADA/USD': 'ADAUSD',
                'DOGE/USD': 'XDGUSD',
                'DOT/USD': 'DOTUSD',
                'AVAX/USD': 'AVAXUSD',
                'LINK/USD': 'LINKUSD',
                'MATIC/USD': 'MATICUSD'
            }
            
            for symbol, kraken_symbol in kraken_pairs.items():
                try:
                    ticker = await self.kraken.get_ticker(kraken_symbol)
                    if ticker:
                        price = ExchangePrice(
                            exchange='kraken',
                            symbol=symbol,
                            bid=float(ticker.get('b', [0])[0]),
                            ask=float(ticker.get('a', [0])[0]),
                            last=float(ticker.get('c', [0])[0]),
                            volume_24h=float(ticker.get('v', [0, 0])[1]),
                            timestamp=datetime.now(timezone.utc).isoformat()
                        )
                        
                        if symbol not in self.prices:
                            self.prices[symbol] = {}
                        self.prices[symbol]['kraken'] = price
                except Exception as e:
                    logger.debug(f"Kraken {symbol} error: {e}")
                    
        except Exception as e:
            logger.error(f"Kraken price fetch error: {e}")
    
    async def _fetch_binance_prices(self):
        """Fetch prices from Binance (public API)"""
        try:
            async with aiohttp.ClientSession() as session:
                # Binance uses BTCUSDT format
                binance_pairs = {
                    'BTC/USD': 'BTCUSDT',
                    'ETH/USD': 'ETHUSDT',
                    'SOL/USD': 'SOLUSDT',
                    'XRP/USD': 'XRPUSDT',
                    'ADA/USD': 'ADAUSDT',
                    'DOGE/USD': 'DOGEUSDT',
                    'DOT/USD': 'DOTUSDT',
                    'AVAX/USD': 'AVAXUSDT',
                    'LINK/USD': 'LINKUSDT',
                    'MATIC/USD': 'MATICUSDT'
                }
                
                for symbol, binance_symbol in binance_pairs.items():
                    try:
                        url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={binance_symbol}"
                        async with session.get(url, timeout=5) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                
                                # Get 24h volume
                                vol_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
                                async with session.get(vol_url, timeout=5) as vol_resp:
                                    vol_data = await vol_resp.json() if vol_resp.status == 200 else {}
                                
                                price = ExchangePrice(
                                    exchange='binance',
                                    symbol=symbol,
                                    bid=float(data.get('bidPrice', 0)),
                                    ask=float(data.get('askPrice', 0)),
                                    last=float(vol_data.get('lastPrice', data.get('bidPrice', 0))),
                                    volume_24h=float(vol_data.get('volume', 0)),
                                    timestamp=datetime.now(timezone.utc).isoformat()
                                )
                                
                                if symbol not in self.prices:
                                    self.prices[symbol] = {}
                                self.prices[symbol]['binance'] = price
                    except Exception as e:
                        logger.debug(f"Binance {symbol} error: {e}")
                        
        except Exception as e:
            logger.error(f"Binance price fetch error: {e}")
    
    async def _fetch_coinbase_prices(self):
        """Fetch prices from Coinbase (public API)"""
        try:
            async with aiohttp.ClientSession() as session:
                # Coinbase uses BTC-USD format
                coinbase_pairs = {
                    'BTC/USD': 'BTC-USD',
                    'ETH/USD': 'ETH-USD',
                    'SOL/USD': 'SOL-USD',
                    'XRP/USD': 'XRP-USD',
                    'ADA/USD': 'ADA-USD',
                    'DOGE/USD': 'DOGE-USD',
                    'DOT/USD': 'DOT-USD',
                    'AVAX/USD': 'AVAX-USD',
                    'LINK/USD': 'LINK-USD',
                    'MATIC/USD': 'MATIC-USD'
                }
                
                for symbol, cb_symbol in coinbase_pairs.items():
                    try:
                        url = f"https://api.exchange.coinbase.com/products/{cb_symbol}/ticker"
                        async with session.get(url, timeout=5) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                
                                price = ExchangePrice(
                                    exchange='coinbase',
                                    symbol=symbol,
                                    bid=float(data.get('bid', 0)),
                                    ask=float(data.get('ask', 0)),
                                    last=float(data.get('price', 0)),
                                    volume_24h=float(data.get('volume', 0)),
                                    timestamp=datetime.now(timezone.utc).isoformat()
                                )
                                
                                if symbol not in self.prices:
                                    self.prices[symbol] = {}
                                self.prices[symbol]['coinbase'] = price
                    except Exception as e:
                        logger.debug(f"Coinbase {symbol} error: {e}")
                        
        except Exception as e:
            logger.error(f"Coinbase price fetch error: {e}")
    
    async def _detect_opportunities(self):
        """Detect arbitrage opportunities from current prices"""
        new_opportunities = []
        
        for symbol, exchanges in self.prices.items():
            if len(exchanges) < 2:
                continue
            
            exchange_list = list(exchanges.items())
            
            # Compare all exchange pairs
            for i, (ex1_name, ex1_price) in enumerate(exchange_list):
                for ex2_name, ex2_price in exchange_list[i+1:]:
                    # Check if we can buy on ex1 and sell on ex2
                    spread1 = ex2_price.bid - ex1_price.ask
                    spread1_pct = (spread1 / ex1_price.ask) * 100 if ex1_price.ask > 0 else 0
                    
                    # Check if we can buy on ex2 and sell on ex1
                    spread2 = ex1_price.bid - ex2_price.ask
                    spread2_pct = (spread2 / ex2_price.ask) * 100 if ex2_price.ask > 0 else 0
                    
                    # Account for fees
                    total_fees = self.EXCHANGE_FEES.get(ex1_name, 0.5) + self.EXCHANGE_FEES.get(ex2_name, 0.5)
                    
                    # Check direction 1: buy ex1, sell ex2
                    net_spread1_pct = spread1_pct - total_fees
                    if net_spread1_pct >= self.settings['min_spread_pct']:
                        volume = min(ex1_price.volume_24h, ex2_price.volume_24h) * 0.01  # 1% of volume
                        potential_profit = volume * ex1_price.ask * (net_spread1_pct / 100)
                        
                        if potential_profit >= self.settings['min_profit_usd']:
                            opp = ArbitrageOpportunity(
                                id=f"{symbol}_{ex1_name}_{ex2_name}_{datetime.now().timestamp()}",
                                symbol=symbol,
                                buy_exchange=ex1_name,
                                buy_price=ex1_price.ask,
                                sell_exchange=ex2_name,
                                sell_price=ex2_price.bid,
                                spread=spread1,
                                spread_pct=net_spread1_pct,
                                potential_profit=potential_profit,
                                volume_available=volume,
                                timestamp=datetime.now(timezone.utc).isoformat()
                            )
                            new_opportunities.append(opp)
                    
                    # Check direction 2: buy ex2, sell ex1
                    net_spread2_pct = spread2_pct - total_fees
                    if net_spread2_pct >= self.settings['min_spread_pct']:
                        volume = min(ex1_price.volume_24h, ex2_price.volume_24h) * 0.01
                        potential_profit = volume * ex2_price.ask * (net_spread2_pct / 100)
                        
                        if potential_profit >= self.settings['min_profit_usd']:
                            opp = ArbitrageOpportunity(
                                id=f"{symbol}_{ex2_name}_{ex1_name}_{datetime.now().timestamp()}",
                                symbol=symbol,
                                buy_exchange=ex2_name,
                                buy_price=ex2_price.ask,
                                sell_exchange=ex1_name,
                                sell_price=ex1_price.bid,
                                spread=spread2,
                                spread_pct=net_spread2_pct,
                                potential_profit=potential_profit,
                                volume_available=volume,
                                timestamp=datetime.now(timezone.utc).isoformat()
                            )
                            new_opportunities.append(opp)
        
        # Update opportunities list
        if new_opportunities:
            self.opportunities = sorted(
                new_opportunities, 
                key=lambda x: x.potential_profit, 
                reverse=True
            )[:20]  # Keep top 20
            
            # Store in database
            for opp in new_opportunities[:5]:  # Store top 5
                await self.db.arbitrage_opportunities.insert_one(asdict(opp))
            
            logger.info(f"⚡ Found {len(new_opportunities)} arbitrage opportunities")
    
    async def execute_arbitrage(self, opportunity_id: str) -> Dict[str, Any]:
        """Execute an arbitrage trade"""
        opp = next((o for o in self.opportunities if o.id == opportunity_id), None)
        
        if not opp:
            return {'status': 'error', 'message': 'Opportunity not found or expired'}
        
        # For now, return simulation result
        # In production, would execute actual trades
        result = {
            'status': 'simulated',
            'opportunity': asdict(opp),
            'message': 'Arbitrage execution simulated (live trading requires exchange API keys)',
            'estimated_profit': opp.potential_profit,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log the attempt
        await self.db.arbitrage_executions.insert_one({
            **result,
            'opportunity_id': opportunity_id
        })
        
        return result
    
    async def get_prices(self) -> Dict[str, Any]:
        """Get current prices from all exchanges"""
        result = {}
        for symbol, exchanges in self.prices.items():
            result[symbol] = {
                ex: asdict(price) for ex, price in exchanges.items()
            }
        return result
    
    async def get_opportunities(self) -> List[Dict]:
        """Get current arbitrage opportunities"""
        return [asdict(opp) for opp in self.opportunities]
    
    async def get_settings(self) -> Dict[str, Any]:
        """Get current settings"""
        return self.settings
    
    async def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update arbitrage settings"""
        self.settings.update(settings)
        return self.settings
    
    async def get_history(self, limit: int = 50) -> List[Dict]:
        """Get arbitrage opportunity history"""
        cursor = self.db.arbitrage_opportunities.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(limit)
        return await cursor.to_list(limit)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'is_monitoring': self.is_monitoring,
            'tracked_pairs': len(self.prices),
            'active_opportunities': len(self.opportunities),
            'enabled_exchanges': self.settings['enabled_exchanges'],
            'settings': self.settings
        }


# Singleton
_arbitrage_service: Optional[MultiExchangeArbitrage] = None


def get_arbitrage_service(db=None, kraken=None) -> Optional[MultiExchangeArbitrage]:
    """Get or create the arbitrage service"""
    global _arbitrage_service
    if _arbitrage_service is None and db is not None:
        _arbitrage_service = MultiExchangeArbitrage(db, kraken)
    return _arbitrage_service
