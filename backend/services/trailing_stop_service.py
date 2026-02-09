"""
Trailing Stop-Loss Service
==========================
Dynamic stop-loss that follows price up to lock in profits.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TrailingStop:
    """A trailing stop-loss order"""
    id: str
    user_id: str
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    current_price: float
    highest_price: float  # Highest price since entry (for longs)
    lowest_price: float   # Lowest price since entry (for shorts)
    trail_pct: float      # Trailing percentage
    stop_price: float     # Current stop price
    quantity: float
    status: str           # 'active', 'triggered', 'cancelled'
    created_at: str
    updated_at: str
    triggered_at: Optional[str] = None
    pnl_usd: Optional[float] = None
    pnl_pct: Optional[float] = None


class TrailingStopService:
    """
    Trailing stop-loss service for dynamic profit protection.
    
    Features:
    - Create trailing stops with custom percentages
    - Auto-adjust stop price as price moves favorably
    - Trigger execution when price reverses
    - Support for both long and short positions
    """
    
    def __init__(self, db, kraken_service=None, market_service=None):
        self.db = db
        self.kraken = kraken_service
        self.market = market_service
        self.active_stops: Dict[str, TrailingStop] = {}
        self.is_monitoring = False
        self._monitor_task = None
        self.settings = {
            'default_trail_pct': 5.0,
            'min_trail_pct': 1.0,
            'max_trail_pct': 25.0,
            'check_interval_sec': 10,
            'auto_execute': True
        }
        logger.info("✅ Trailing Stop Service initialized")
    
    async def create_trailing_stop(
        self,
        user_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        trail_pct: float = None
    ) -> Dict[str, Any]:
        """Create a new trailing stop-loss"""
        trail_pct = trail_pct or self.settings['default_trail_pct']
        
        # Validate
        if trail_pct < self.settings['min_trail_pct'] or trail_pct > self.settings['max_trail_pct']:
            return {
                'status': 'error',
                'message': f"Trail percentage must be between {self.settings['min_trail_pct']}% and {self.settings['max_trail_pct']}%"
            }
        
        # Get current price
        current_price = await self._get_price(symbol)
        if not current_price:
            return {'status': 'error', 'message': f'Could not get price for {symbol}'}
        
        # Calculate initial stop price
        if side == 'long':
            stop_price = current_price * (1 - trail_pct / 100)
            highest_price = current_price
            lowest_price = current_price
        else:  # short
            stop_price = current_price * (1 + trail_pct / 100)
            highest_price = current_price
            lowest_price = current_price
        
        stop_id = f"TS_{symbol}_{user_id}_{datetime.now().timestamp()}"
        
        trailing_stop = TrailingStop(
            id=stop_id,
            user_id=user_id,
            symbol=symbol.upper(),
            side=side,
            entry_price=entry_price,
            current_price=current_price,
            highest_price=highest_price,
            lowest_price=lowest_price,
            trail_pct=trail_pct,
            stop_price=stop_price,
            quantity=quantity,
            status='active',
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Store
        self.active_stops[stop_id] = trailing_stop
        await self.db.trailing_stops.insert_one(asdict(trailing_stop))
        
        logger.info(f"📈 Trailing stop created: {symbol} @ {trail_pct}% trail")
        
        return {
            'status': 'success',
            'trailing_stop': asdict(trailing_stop)
        }
    
    async def update_trailing_stop(
        self,
        stop_id: str,
        trail_pct: float = None,
        quantity: float = None
    ) -> Dict[str, Any]:
        """Update an existing trailing stop"""
        stop = self.active_stops.get(stop_id)
        if not stop:
            return {'status': 'error', 'message': 'Trailing stop not found'}
        
        if stop.status != 'active':
            return {'status': 'error', 'message': 'Trailing stop is not active'}
        
        if trail_pct is not None:
            if trail_pct < self.settings['min_trail_pct'] or trail_pct > self.settings['max_trail_pct']:
                return {'status': 'error', 'message': 'Invalid trail percentage'}
            stop.trail_pct = trail_pct
            # Recalculate stop price
            if stop.side == 'long':
                stop.stop_price = stop.highest_price * (1 - trail_pct / 100)
            else:
                stop.stop_price = stop.lowest_price * (1 + trail_pct / 100)
        
        if quantity is not None:
            stop.quantity = quantity
        
        stop.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Update database
        await self.db.trailing_stops.update_one(
            {'id': stop_id},
            {'$set': asdict(stop)}
        )
        
        return {'status': 'success', 'trailing_stop': asdict(stop)}
    
    async def cancel_trailing_stop(self, stop_id: str) -> Dict[str, Any]:
        """Cancel a trailing stop"""
        stop = self.active_stops.get(stop_id)
        if not stop:
            return {'status': 'error', 'message': 'Trailing stop not found'}
        
        stop.status = 'cancelled'
        stop.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Update database
        await self.db.trailing_stops.update_one(
            {'id': stop_id},
            {'$set': {'status': 'cancelled', 'updated_at': stop.updated_at}}
        )
        
        # Remove from active
        del self.active_stops[stop_id]
        
        return {'status': 'success', 'message': 'Trailing stop cancelled'}
    
    async def start_monitoring(self):
        """Start price monitoring for trailing stops"""
        if self.is_monitoring:
            return {'status': 'already_running'}
        
        # Load active stops from database
        cursor = self.db.trailing_stops.find({'status': 'active'})
        async for doc in cursor:
            stop = TrailingStop(**{k: v for k, v in doc.items() if k != '_id'})
            self.active_stops[stop.id] = stop
        
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info(f"📊 Trailing stop monitoring started ({len(self.active_stops)} active)")
        return {'status': 'started', 'active_stops': len(self.active_stops)}
    
    async def stop_monitoring(self):
        """Stop price monitoring"""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        
        return {'status': 'stopped'}
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._check_all_stops()
                await asyncio.sleep(self.settings['check_interval_sec'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(30)
    
    async def _check_all_stops(self):
        """Check all active trailing stops"""
        for stop_id, stop in list(self.active_stops.items()):
            try:
                await self._check_stop(stop)
            except Exception as e:
                logger.error(f"Error checking stop {stop_id}: {e}")
    
    async def _check_stop(self, stop: TrailingStop):
        """Check and update a single trailing stop"""
        current_price = await self._get_price(stop.symbol)
        if not current_price:
            return
        
        stop.current_price = current_price
        stop.updated_at = datetime.now(timezone.utc).isoformat()
        
        triggered = False
        
        if stop.side == 'long':
            # Update highest price
            if current_price > stop.highest_price:
                stop.highest_price = current_price
                stop.stop_price = current_price * (1 - stop.trail_pct / 100)
                logger.debug(f"📈 {stop.symbol} new high: ${current_price:.2f}, stop moved to ${stop.stop_price:.2f}")
            
            # Check if triggered
            if current_price <= stop.stop_price:
                triggered = True
        else:  # short
            # Update lowest price
            if current_price < stop.lowest_price:
                stop.lowest_price = current_price
                stop.stop_price = current_price * (1 + stop.trail_pct / 100)
            
            # Check if triggered
            if current_price >= stop.stop_price:
                triggered = True
        
        if triggered:
            await self._trigger_stop(stop)
        else:
            # Update database
            await self.db.trailing_stops.update_one(
                {'id': stop.id},
                {'$set': {
                    'current_price': stop.current_price,
                    'highest_price': stop.highest_price,
                    'lowest_price': stop.lowest_price,
                    'stop_price': stop.stop_price,
                    'updated_at': stop.updated_at
                }}
            )
    
    async def _trigger_stop(self, stop: TrailingStop):
        """Handle triggered trailing stop"""
        stop.status = 'triggered'
        stop.triggered_at = datetime.now(timezone.utc).isoformat()
        
        # Calculate P&L
        if stop.side == 'long':
            stop.pnl_usd = (stop.current_price - stop.entry_price) * stop.quantity
            stop.pnl_pct = ((stop.current_price - stop.entry_price) / stop.entry_price) * 100
        else:
            stop.pnl_usd = (stop.entry_price - stop.current_price) * stop.quantity
            stop.pnl_pct = ((stop.entry_price - stop.current_price) / stop.entry_price) * 100
        
        logger.info(f"🛑 Trailing stop triggered: {stop.symbol} @ ${stop.current_price:.2f} (P&L: ${stop.pnl_usd:+.2f})")
        
        # Execute sell if auto_execute enabled
        if self.settings['auto_execute'] and self.kraken:
            try:
                # Place market sell order
                await self._execute_stop(stop)
            except Exception as e:
                logger.error(f"Failed to execute trailing stop: {e}")
        
        # Update database
        await self.db.trailing_stops.update_one(
            {'id': stop.id},
            {'$set': asdict(stop)}
        )
        
        # Remove from active
        if stop.id in self.active_stops:
            del self.active_stops[stop.id]
        
        # Log to history
        await self.db.trailing_stop_history.insert_one({
            **asdict(stop),
            'logged_at': datetime.now(timezone.utc).isoformat()
        })
    
    async def _execute_stop(self, stop: TrailingStop):
        """Execute the stop-loss trade"""
        if not self.kraken:
            return
        
        try:
            pair = f"{stop.symbol}USD"
            order_type = 'market'
            side = 'sell' if stop.side == 'long' else 'buy'
            
            result = await self.kraken.place_order(
                pair=pair,
                type=side,
                ordertype=order_type,
                volume=stop.quantity
            )
            
            logger.info(f"✅ Trailing stop executed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Execute stop error: {e}")
            raise
    
    async def _get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            if self.market:
                return await self.market.get_price(symbol)
            
            if self.kraken:
                pair = f"X{symbol}ZUSD" if symbol in ['BTC', 'ETH', 'XRP'] else f"{symbol}USD"
                ticker = await self.kraken.get_ticker(pair)
                if ticker:
                    return float(ticker.get('c', [0])[0])
            
            return None
        except:
            return None
    
    async def get_active_stops(self, user_id: str = None) -> List[Dict]:
        """Get all active trailing stops"""
        stops = list(self.active_stops.values())
        if user_id:
            stops = [s for s in stops if s.user_id == user_id]
        return [asdict(s) for s in stops]
    
    async def get_history(self, user_id: str = None, limit: int = 50) -> List[Dict]:
        """Get trailing stop history"""
        query = {}
        if user_id:
            query['user_id'] = user_id
        
        cursor = self.db.trailing_stop_history.find(
            query, {'_id': 0}
        ).sort('triggered_at', -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'is_monitoring': self.is_monitoring,
            'active_stops': len(self.active_stops),
            'settings': self.settings
        }


# Singleton
_trailing_service: Optional[TrailingStopService] = None


def get_trailing_stop_service(db=None, kraken=None, market=None) -> Optional[TrailingStopService]:
    """Get or create the trailing stop service"""
    global _trailing_service
    if _trailing_service is None and db is not None:
        _trailing_service = TrailingStopService(db, kraken, market)
    return _trailing_service
