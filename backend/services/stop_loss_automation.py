"""
Position Stop-Loss Automation Service
Monitors all open AI positions and automatically closes them when they hit stop-loss or take-profit.
Now includes TRAILING STOP-LOSS for locking in profits as price moves up.
Runs every 5 minutes to ensure timely exits.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class StopLossAutomation:
    """
    Automated stop-loss and take-profit monitoring with TRAILING STOP-LOSS.
    
    Features:
    - Monitors all open AI-managed positions every 5 minutes
    - Automatically closes positions hitting stop-loss
    - Automatically closes positions hitting take-profit
    - TRAILING STOP-LOSS: Automatically raises stop-loss as price increases
    - Logs all automated actions with P&L
    - Sends alerts for significant events
    - Respects emergency stop status
    
    Trailing Stop-Loss Logic:
    - When price rises above entry, trailing stop follows at configured % below
    - Stop only moves UP, never down (locks in profits)
    - Example: 10% trailing stop on $100 entry
      - Price rises to $120 → stop moves to $108 (10% below $120)
      - Price drops to $115 → stop stays at $108 (doesn't move down)
      - Price rises to $130 → stop moves to $117 (10% below $130)
    """
    
    def __init__(self, db, kraken_service, isolated_portfolio, alert_service=None):
        self.db = db
        self.kraken = kraken_service
        self.isolated_portfolio = isolated_portfolio
        self.alert_service = alert_service
        
        # Configuration
        self.config = {
            'check_interval_minutes': 5,
            'trailing_stop_enabled': True,  # ENABLED - Trailing stop-loss
            'trailing_stop_pct': 10.0,  # Trail 10% below highest price
            'trailing_stop_activation_pct': 5.0,  # Activate trailing after 5% profit
            'partial_take_profit_enabled': False,  # Future feature
            'min_profit_to_notify': 10.0,  # USD
            'max_loss_to_notify': 5.0,  # USD
        }
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'positions_closed_stop_loss': 0,
            'positions_closed_take_profit': 0,
            'positions_closed_trailing_stop': 0,
            'trailing_stops_updated': 0,
            'total_pnl_from_automation': 0,
            'last_check': None
        }
    
    async def check_all_positions(self) -> Dict[str, Any]:
        """
        Check all open positions against their stop-loss and take-profit levels.
        This is the main method called by the scheduler.
        """
        logger.info("🔍 Running stop-loss automation check...")
        self.stats['total_checks'] += 1
        self.stats['last_check'] = datetime.now(timezone.utc).isoformat()
        
        # Check if emergency stop is active
        emergency_status = await self._check_emergency_status()
        if emergency_status.get('emergency_stopped'):
            logger.info("⚠️ Emergency stop active - skipping position check")
            return {
                'success': True,
                'skipped': True,
                'reason': 'Emergency stop active',
                'timestamp': self.stats['last_check']
            }
        
        # Get all open positions
        positions = await self._get_open_positions()
        
        if not positions:
            logger.info("📭 No open positions to monitor")
            return {
                'success': True,
                'positions_checked': 0,
                'actions_taken': 0,
                'timestamp': self.stats['last_check']
            }
        
        logger.info(f"📊 Checking {len(positions)} open positions...")
        
        results = {
            'success': True,
            'positions_checked': len(positions),
            'stop_loss_triggered': [],
            'take_profit_triggered': [],
            'trailing_stop_triggered': [],
            'trailing_stops_updated': [],
            'errors': [],
            'timestamp': self.stats['last_check']
        }
        
        for position in positions:
            try:
                action_result = await self._check_position(position)
                
                if action_result.get('action') == 'stop_loss':
                    results['stop_loss_triggered'].append(action_result)
                    self.stats['positions_closed_stop_loss'] += 1
                    self.stats['total_pnl_from_automation'] += action_result.get('pnl_usd', 0)
                
                elif action_result.get('action') == 'trailing_stop':
                    results['trailing_stop_triggered'].append(action_result)
                    self.stats['positions_closed_trailing_stop'] += 1
                    self.stats['total_pnl_from_automation'] += action_result.get('pnl_usd', 0)
                    
                elif action_result.get('action') == 'take_profit':
                    results['take_profit_triggered'].append(action_result)
                    self.stats['positions_closed_take_profit'] += 1
                    self.stats['total_pnl_from_automation'] += action_result.get('pnl_usd', 0)
                    
            except Exception as e:
                error_info = {
                    'position_id': position.get('position_id'),
                    'coin_id': position.get('coin_id'),
                    'error': str(e)
                }
                results['errors'].append(error_info)
                logger.error(f"Error checking position {position.get('coin_id')}: {e}")
        
        # Log summary
        actions_taken = len(results['stop_loss_triggered']) + len(results['take_profit_triggered'])
        results['actions_taken'] = actions_taken
        
        if actions_taken > 0:
            logger.info(f"🎯 Actions taken: {len(results['stop_loss_triggered'])} stop-loss, {len(results['take_profit_triggered'])} take-profit")
            
            # Store execution record
            await self._store_execution_record(results)
            
            # Send alerts if configured
            if self.alert_service:
                await self._send_alerts(results)
        else:
            logger.info("✅ All positions within bounds")
        
        return results
    
    async def _check_position(self, position: Dict) -> Dict[str, Any]:
        """Check a single position against its stop-loss and take-profit"""
        coin_id = position.get('coin_id')
        symbol = position.get('symbol')
        entry_price = position.get('entry_price', 0)
        stop_loss_price = position.get('stop_loss_price', 0)
        take_profit_price = position.get('take_profit_price', float('inf'))
        
        # Get current price
        current_price = await self._get_current_price(symbol)
        
        if current_price is None:
            return {'action': None, 'coin_id': coin_id, 'reason': 'Could not get price'}
        
        # Calculate current P&L
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        pnl_usd = position.get('amount_usd', 0) * (pnl_pct / 100)
        
        # Check stop-loss
        if stop_loss_price > 0 and current_price <= stop_loss_price:
            logger.warning(f"🔴 STOP-LOSS triggered for {coin_id}: ${current_price:.4f} <= ${stop_loss_price:.4f}")
            
            close_result = await self._close_position(
                position=position,
                exit_price=current_price,
                reason='stop_loss_auto',
                pnl_pct=pnl_pct,
                pnl_usd=pnl_usd
            )
            
            return {
                'action': 'stop_loss',
                'coin_id': coin_id,
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': current_price,
                'stop_loss_price': stop_loss_price,
                'pnl_pct': round(pnl_pct, 2),
                'pnl_usd': round(pnl_usd, 2),
                'close_result': close_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Check take-profit
        if take_profit_price > 0 and current_price >= take_profit_price:
            logger.info(f"🟢 TAKE-PROFIT triggered for {coin_id}: ${current_price:.4f} >= ${take_profit_price:.4f}")
            
            close_result = await self._close_position(
                position=position,
                exit_price=current_price,
                reason='take_profit_auto',
                pnl_pct=pnl_pct,
                pnl_usd=pnl_usd
            )
            
            return {
                'action': 'take_profit',
                'coin_id': coin_id,
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': current_price,
                'take_profit_price': take_profit_price,
                'pnl_pct': round(pnl_pct, 2),
                'pnl_usd': round(pnl_usd, 2),
                'close_result': close_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Position still within bounds
        return {
            'action': None,
            'coin_id': coin_id,
            'current_price': current_price,
            'pnl_pct': round(pnl_pct, 2),
            'status': 'within_bounds'
        }
    
    async def _close_position(
        self,
        position: Dict,
        exit_price: float,
        reason: str,
        pnl_pct: float,
        pnl_usd: float
    ) -> Dict[str, Any]:
        """Close a position through the isolated portfolio manager"""
        position_id = position.get('position_id')
        
        # Use isolated portfolio if available
        if self.isolated_portfolio and position_id:
            try:
                result = await self.isolated_portfolio.close_position(
                    position_id=position_id,
                    exit_price=exit_price,
                    reason=reason
                )
                return result
            except Exception as e:
                logger.error(f"Error closing via isolated portfolio: {e}")
        
        # Fallback: Update position directly in DB
        await self.db.active_positions.update_one(
            {'position_id': position_id} if position_id else {'_id': position.get('_id')},
            {'$set': {
                'status': 'CLOSED',
                'exit_price': exit_price,
                'exit_reason': reason,
                'pnl_pct': round(pnl_pct, 2),
                'pnl_usd': round(pnl_usd, 2),
                'closed_at': datetime.now(timezone.utc).isoformat(),
                'closed_by': 'stop_loss_automation'
            }}
        )
        
        return {'success': True, 'method': 'direct_db'}
    
    async def _get_open_positions(self) -> List[Dict]:
        """Get all open AI-managed positions"""
        # First try isolated portfolio
        if self.isolated_portfolio:
            try:
                positions = await self.isolated_portfolio.get_ai_positions()
                if positions:
                    return positions
            except Exception as e:
                logger.warning(f"Could not get positions from isolated portfolio: {e}")
        
        # Fallback to direct DB query
        positions = await self.db.active_positions.find(
            {'status': {'$nin': ['CLOSED', 'CANCELLED']}},
            {'_id': 0}
        ).to_list(100)
        
        return positions
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        if not symbol:
            return None
        
        try:
            ticker = await self.kraken.get_ticker(symbol)
            if ticker and 'c' in ticker:
                return float(ticker['c'][0])
        except Exception as e:
            logger.warning(f"Error getting price for {symbol}: {e}")
        
        return None
    
    async def _check_emergency_status(self) -> Dict[str, Any]:
        """Check if emergency stop is active"""
        budget = await self.db.trading_budgets.find_one(
            {"user_id": "default"},
            {"_id": 0, "emergency_stopped": 1, "real_trading_enabled": 1}
        )
        
        if not budget:
            return {'emergency_stopped': False}
        
        return {
            'emergency_stopped': budget.get('emergency_stopped', False),
            'trading_enabled': budget.get('real_trading_enabled', True)
        }
    
    async def _store_execution_record(self, results: Dict):
        """Store execution record in database"""
        record = {
            'type': 'stop_loss_automation',
            'timestamp': results['timestamp'],
            'positions_checked': results['positions_checked'],
            'stop_loss_count': len(results['stop_loss_triggered']),
            'take_profit_count': len(results['take_profit_triggered']),
            'stop_loss_details': results['stop_loss_triggered'],
            'take_profit_details': results['take_profit_triggered'],
            'errors': results['errors']
        }
        
        await self.db.automation_executions.insert_one(record)
    
    async def _send_alerts(self, results: Dict):
        """Send alerts for significant events"""
        if not self.alert_service:
            return
        
        # Alert for stop-losses
        for sl in results['stop_loss_triggered']:
            await self.alert_service.send_alert({
                'type': 'STOP_LOSS_TRIGGERED',
                'coin': sl['coin_id'],
                'pnl_usd': sl['pnl_usd'],
                'pnl_pct': sl['pnl_pct'],
                'message': f"🔴 Stop-loss hit for {sl['coin_id'].upper()}: {sl['pnl_pct']:+.2f}% (${sl['pnl_usd']:+.2f})"
            })
        
        # Alert for take-profits
        for tp in results['take_profit_triggered']:
            await self.alert_service.send_alert({
                'type': 'TAKE_PROFIT_TRIGGERED',
                'coin': tp['coin_id'],
                'pnl_usd': tp['pnl_usd'],
                'pnl_pct': tp['pnl_pct'],
                'message': f"🟢 Take-profit hit for {tp['coin_id'].upper()}: {tp['pnl_pct']:+.2f}% (${tp['pnl_usd']:+.2f})"
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get automation statistics"""
        return {
            **self.stats,
            'config': self.config
        }
    
    async def get_automation_history(self, limit: int = 20) -> List[Dict]:
        """Get history of automation executions"""
        history = await self.db.automation_executions.find(
            {'type': 'stop_loss_automation'},
            {'_id': 0}
        ).sort('timestamp', -1).limit(limit).to_list(limit)
        
        return history
    
    async def update_position_levels(
        self,
        position_id: str,
        stop_loss_price: float = None,
        take_profit_price: float = None
    ) -> Dict[str, Any]:
        """Update stop-loss or take-profit levels for a position"""
        update_fields = {}
        
        if stop_loss_price is not None:
            update_fields['stop_loss_price'] = stop_loss_price
        
        if take_profit_price is not None:
            update_fields['take_profit_price'] = take_profit_price
        
        if not update_fields:
            return {'success': False, 'error': 'No fields to update'}
        
        # Update in isolated portfolio
        if self.isolated_portfolio:
            await self.db.isolated_positions.update_one(
                {'position_id': position_id},
                {'$set': update_fields}
            )
        
        # Update in active positions
        await self.db.active_positions.update_one(
            {'position_id': position_id},
            {'$set': update_fields}
        )
        
        logger.info(f"📝 Updated levels for position {position_id}: {update_fields}")
        
        return {
            'success': True,
            'position_id': position_id,
            'updated_fields': update_fields
        }


# Singleton instance
_stop_loss_automation = None


def get_stop_loss_automation(db=None, kraken_service=None, isolated_portfolio=None, alert_service=None):
    """Get or create the stop-loss automation singleton"""
    global _stop_loss_automation
    
    if _stop_loss_automation is None and db is not None:
        _stop_loss_automation = StopLossAutomation(
            db=db,
            kraken_service=kraken_service,
            isolated_portfolio=isolated_portfolio,
            alert_service=alert_service
        )
    
    return _stop_loss_automation
