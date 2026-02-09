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
            'partial_take_profit_enabled': True,  # ENABLED - Partial take profit
            'partial_tp_pct': 50.0,  # Close 50% of position at first TP
            'partial_tp_levels': [  # Multiple take-profit levels
                {'pct_of_position': 50, 'at_profit_pct': 30},   # Close 50% at 30% profit
                {'pct_of_position': 25, 'at_profit_pct': 50},   # Close 25% at 50% profit
                {'pct_of_position': 25, 'at_profit_pct': 100},  # Close remaining 25% at 100% profit
            ],
            'move_stop_to_breakeven': True,  # After first partial TP, move stop to entry
            'min_profit_to_notify': 10.0,  # USD
            'max_loss_to_notify': 5.0,  # USD
        }
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'positions_closed_stop_loss': 0,
            'positions_closed_take_profit': 0,
            'positions_closed_trailing_stop': 0,
            'partial_take_profits': 0,
            'trailing_stops_updated': 0,
            'total_pnl_from_automation': 0,
            'last_check': None
        }
    
    async def check_all_positions(self) -> Dict[str, Any]:
        """
        Check all open positions against their stop-loss, take-profit, and partial TP levels.
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
            'partial_take_profits': [],
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
                
                elif action_result.get('action') == 'partial_take_profit':
                    results['partial_take_profits'].append(action_result)
                    self.stats['partial_take_profits'] += 1
                    self.stats['total_pnl_from_automation'] += action_result.get('realized_pnl_usd', 0)
                    
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
        actions_taken = (len(results['stop_loss_triggered']) + len(results['take_profit_triggered']) + 
                        len(results['trailing_stop_triggered']) + len(results['partial_take_profits']))
        results['actions_taken'] = actions_taken
        
        if actions_taken > 0 or len(results['trailing_stops_updated']) > 0:
            logger.info(f"🎯 Actions: SL:{len(results['stop_loss_triggered'])} TP:{len(results['take_profit_triggered'])} Partial:{len(results['partial_take_profits'])} Trailing:{len(results['trailing_stop_triggered'])}")
            
            # Store execution record
            await self._store_execution_record(results)
            
            # Send alerts if configured
            if self.alert_service:
                await self._send_alerts(results)
        else:
            logger.info("✅ All positions within bounds")
        
        return results
    
    async def _check_position(self, position: Dict) -> Dict[str, Any]:
        """Check a single position against its stop-loss, take-profit, partial TP, and trailing stop"""
        coin_id = position.get('coin_id')
        symbol = position.get('symbol')
        entry_price = position.get('entry_price', 0)
        stop_loss_price = position.get('stop_loss_price', 0)
        take_profit_price = position.get('take_profit_price', float('inf'))
        highest_price = position.get('highest_price', entry_price)  # Track highest for trailing
        trailing_stop_price = position.get('trailing_stop_price', 0)  # Current trailing stop level
        
        # Get current price
        current_price = await self._get_current_price(symbol)
        
        if current_price is None:
            return {'action': None, 'coin_id': coin_id, 'reason': 'Could not get price'}
        
        # Calculate current P&L
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        pnl_usd = position.get('amount_usd', 0) * (pnl_pct / 100)
        
        # TRAILING STOP-LOSS LOGIC
        if self.config['trailing_stop_enabled'] and entry_price > 0:
            trailing_result = await self._update_trailing_stop(
                position=position,
                current_price=current_price,
                entry_price=entry_price,
                highest_price=highest_price,
                trailing_stop_price=trailing_stop_price,
                pnl_pct=pnl_pct,
                pnl_usd=pnl_usd
            )
            
            if trailing_result.get('action') == 'trailing_stop':
                return trailing_result
            elif trailing_result.get('updated'):
                # Trailing stop was updated but not triggered
                pass  # Continue with other checks
        
        # Check regular stop-loss (only if not using trailing or trailing not yet active)
        effective_stop = trailing_stop_price if trailing_stop_price > 0 else stop_loss_price
        
        if effective_stop > 0 and current_price <= effective_stop:
            is_trailing = trailing_stop_price > 0 and trailing_stop_price >= stop_loss_price
            action_type = 'trailing_stop' if is_trailing else 'stop_loss'
            
            logger.warning(f"🔴 {action_type.upper()} triggered for {coin_id}: ${current_price:.4f} <= ${effective_stop:.4f}")
            
            close_result = await self._close_position(
                position=position,
                exit_price=current_price,
                reason=f'{action_type}_auto',
                pnl_pct=pnl_pct,
                pnl_usd=pnl_usd
            )
            
            return {
                'action': action_type,
                'coin_id': coin_id,
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': current_price,
                'stop_price': effective_stop,
                'highest_price': highest_price,
                'pnl_pct': round(pnl_pct, 2),
                'pnl_usd': round(pnl_usd, 2),
                'close_result': close_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Check stop-loss (legacy - for positions without trailing)
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
        
        # PARTIAL TAKE PROFIT LOGIC
        if self.config['partial_take_profit_enabled'] and pnl_pct > 0:
            partial_result = await self._check_partial_take_profit(
                position=position,
                current_price=current_price,
                entry_price=entry_price,
                pnl_pct=pnl_pct
            )
            
            if partial_result.get('action') == 'partial_take_profit':
                return partial_result
        
        # Check take-profit (full close)
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
    
    async def _check_partial_take_profit(
        self,
        position: Dict,
        current_price: float,
        entry_price: float,
        pnl_pct: float
    ) -> Dict[str, Any]:
        """
        Check if position qualifies for partial take profit.
        
        Logic:
        1. Check each TP level in order
        2. If profit exceeds level and that level hasn't been taken yet, close that portion
        3. Update position with remaining quantity
        4. Optionally move stop-loss to breakeven after first partial TP
        
        Example with default levels:
        - At 30% profit: Close 50% of position
        - At 50% profit: Close 25% of remaining
        - At 100% profit: Close final 25%
        """
        coin_id = position.get('coin_id')
        position_id = position.get('position_id')
        symbol = position.get('symbol')
        amount_usd = position.get('amount_usd', 0)
        quantity = position.get('quantity', 0)
        partial_tp_taken = position.get('partial_tp_taken', [])  # List of levels already taken
        
        tp_levels = self.config['partial_tp_levels']
        
        for i, level in enumerate(tp_levels):
            level_id = f"level_{i}"
            target_profit_pct = level['at_profit_pct']
            close_pct = level['pct_of_position']
            
            # Skip if this level already taken
            if level_id in partial_tp_taken:
                continue
            
            # Check if we've reached this level
            if pnl_pct >= target_profit_pct:
                # Calculate how much to close
                close_quantity = quantity * (close_pct / 100)
                close_amount_usd = amount_usd * (close_pct / 100)
                realized_pnl = close_amount_usd * (pnl_pct / 100)
                
                remaining_quantity = quantity - close_quantity
                remaining_amount_usd = amount_usd - close_amount_usd
                
                logger.info(f"💰 PARTIAL TP {level_id} for {coin_id}: Closing {close_pct}% at {pnl_pct:.1f}% profit (+${realized_pnl:.2f})")
                
                # Update position
                update_fields = {
                    'quantity': remaining_quantity,
                    'amount_usd': remaining_amount_usd,
                    'partial_tp_taken': partial_tp_taken + [level_id],
                    f'partial_tp_{level_id}': {
                        'closed_at': datetime.now(timezone.utc).isoformat(),
                        'close_pct': close_pct,
                        'close_price': current_price,
                        'realized_pnl': realized_pnl,
                        'profit_pct': pnl_pct
                    }
                }
                
                # Move stop to breakeven after first partial TP
                if i == 0 and self.config['move_stop_to_breakeven']:
                    update_fields['stop_loss_price'] = entry_price
                    update_fields['stop_moved_to_breakeven'] = True
                    logger.info(f"  📍 Stop-loss moved to breakeven: ${entry_price:.4f}")
                
                # Update in database
                if position_id:
                    await self.db.active_positions.update_one(
                        {'position_id': position_id},
                        {'$set': update_fields}
                    )
                    
                    await self.db.isolated_positions.update_one(
                        {'position_id': position_id},
                        {'$set': update_fields}
                    )
                
                # Record partial TP transaction
                await self.db.ai_transactions.insert_one({
                    'type': 'partial_take_profit',
                    'position_id': position_id,
                    'coin_id': coin_id,
                    'symbol': symbol,
                    'level': level_id,
                    'close_pct': close_pct,
                    'close_quantity': close_quantity,
                    'close_amount_usd': close_amount_usd,
                    'close_price': current_price,
                    'entry_price': entry_price,
                    'profit_pct': pnl_pct,
                    'realized_pnl_usd': realized_pnl,
                    'remaining_quantity': remaining_quantity,
                    'remaining_amount_usd': remaining_amount_usd,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                return {
                    'action': 'partial_take_profit',
                    'coin_id': coin_id,
                    'symbol': symbol,
                    'level': level_id,
                    'close_pct': close_pct,
                    'close_price': current_price,
                    'entry_price': entry_price,
                    'profit_pct': round(pnl_pct, 2),
                    'realized_pnl_usd': round(realized_pnl, 2),
                    'remaining_pct': round(100 - sum(l['pct_of_position'] for l in tp_levels[:i+1]), 0),
                    'remaining_quantity': remaining_quantity,
                    'remaining_amount_usd': round(remaining_amount_usd, 2),
                    'stop_moved_to_breakeven': i == 0 and self.config['move_stop_to_breakeven'],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
        
        # No partial TP triggered
        return {'action': None}
    
    async def _update_trailing_stop(
        self,
        position: Dict,
        current_price: float,
        entry_price: float,
        highest_price: float,
        trailing_stop_price: float,
        pnl_pct: float,
        pnl_usd: float
    ) -> Dict[str, Any]:
        """
        Update trailing stop-loss for a position.
        
        Logic:
        1. Only activate trailing stop after position is in profit by activation_pct
        2. Track highest price reached
        3. Set trailing stop at trailing_stop_pct below highest price
        4. Trailing stop only moves UP, never down
        """
        coin_id = position.get('coin_id')
        position_id = position.get('position_id')
        activation_pct = self.config['trailing_stop_activation_pct']
        trail_pct = self.config['trailing_stop_pct']
        
        # Check if trailing stop should be activated
        if pnl_pct < activation_pct:
            # Not yet in enough profit to activate trailing stop
            return {'action': None, 'updated': False, 'reason': 'Below activation threshold'}
        
        # Update highest price if current is higher
        new_highest = max(highest_price, current_price)
        
        # Calculate new trailing stop level
        new_trailing_stop = new_highest * (1 - trail_pct / 100)
        
        # Trailing stop only moves UP
        if new_trailing_stop > trailing_stop_price:
            # Update position with new trailing stop and highest price
            update_fields = {
                'highest_price': new_highest,
                'trailing_stop_price': new_trailing_stop,
                'trailing_stop_updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Update in database
            if position_id:
                await self.db.active_positions.update_one(
                    {'position_id': position_id},
                    {'$set': update_fields}
                )
                
                # Also update in isolated positions if exists
                await self.db.isolated_positions.update_one(
                    {'position_id': position_id},
                    {'$set': update_fields}
                )
            
            self.stats['trailing_stops_updated'] += 1
            
            logger.info(f"📈 {coin_id}: Trailing stop updated ${trailing_stop_price:.4f} → ${new_trailing_stop:.4f} (highest: ${new_highest:.4f})")
            
            return {
                'action': None,
                'updated': True,
                'coin_id': coin_id,
                'old_trailing_stop': trailing_stop_price,
                'new_trailing_stop': new_trailing_stop,
                'highest_price': new_highest,
                'current_price': current_price,
                'pnl_pct': round(pnl_pct, 2)
            }
        
        # Check if current price hit the trailing stop
        if trailing_stop_price > 0 and current_price <= trailing_stop_price:
            logger.warning(f"🟡 TRAILING STOP triggered for {coin_id}: ${current_price:.4f} <= ${trailing_stop_price:.4f}")
            
            close_result = await self._close_position(
                position=position,
                exit_price=current_price,
                reason='trailing_stop_auto',
                pnl_pct=pnl_pct,
                pnl_usd=pnl_usd
            )
            
            return {
                'action': 'trailing_stop',
                'coin_id': coin_id,
                'symbol': position.get('symbol'),
                'entry_price': entry_price,
                'exit_price': current_price,
                'trailing_stop_price': trailing_stop_price,
                'highest_price': highest_price,
                'pnl_pct': round(pnl_pct, 2),
                'pnl_usd': round(pnl_usd, 2),
                'close_result': close_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        return {'action': None, 'updated': False}
    
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
            await self.alert_service.send_alert(
                title="🔴 Stop-Loss Triggered",
                message=f"Stop-loss hit for {sl['coin_id'].upper()}: {sl['pnl_pct']:+.2f}% (${sl['pnl_usd']:+.2f})",
                alert_type="stop_loss",
                priority="high"
            )
        
        # Alert for take-profits
        for tp in results['take_profit_triggered']:
            await self.alert_service.send_alert(
                title="🟢 Take-Profit Triggered",
                message=f"Take-profit hit for {tp['coin_id'].upper()}: {tp['pnl_pct']:+.2f}% (${tp['pnl_usd']:+.2f})",
                alert_type="take_profit",
                priority="high"
            )
    
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
