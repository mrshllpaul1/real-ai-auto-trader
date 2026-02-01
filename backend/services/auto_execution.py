import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

class AutoExecutionEngine:
    """
    Automatic trade execution engine that executes trades
    when HIGH priority gems are detected matching risk profile
    """
    
    def __init__(self, db, scanner, ai_engine, kraken_service=None, notification_service=None):
        self.db = db
        self.scanner = scanner
        self.ai_engine = ai_engine
        self.kraken_service = kraken_service
        self.notification_service = notification_service
        self.is_running = False
        self.execution_interval = 60  # Check every 60 seconds
        
        # Default risk profile
        self.risk_profile = {
            'enabled': False,
            'mode': 'paper',  # 'paper' or 'live'
            'min_score': 60,  # Minimum score to trade
            'min_alert_level': 'HIGH',
            'max_position_size_usd': 100,
            'max_daily_trades': 5,
            'max_open_positions': 3,
            'stop_loss_pct': 10,
            'take_profit_pct': 50,
            'allowed_signals': ['MACD_BULLISH', 'BOLLINGER_SQUEEZE', 'OVERSOLD_ACCUMULATION', 
                               'DEEP_VALUE', 'TREND_REVERSAL', 'EXTREME_VOLUME'],
            'blacklisted_coins': [],
            'preferred_coins': []
        }
        
        # Tracking
        self.daily_trades = 0
        self.last_trade_reset = datetime.now().date()
        self.open_positions = []
    
    async def load_risk_profile(self, user_id: str = 'default'):
        """Load user's risk profile from database"""
        profile = await self.db.risk_profiles.find_one({'user_id': user_id}, {'_id': 0})
        if profile:
            self.risk_profile.update(profile)
            print(f"✅ Loaded risk profile for {user_id}")
        return self.risk_profile
    
    async def save_risk_profile(self, user_id: str = 'default'):
        """Save risk profile to database"""
        self.risk_profile['user_id'] = user_id
        self.risk_profile['updated_at'] = datetime.now().isoformat()
        
        await self.db.risk_profiles.update_one(
            {'user_id': user_id},
            {'$set': self.risk_profile},
            upsert=True
        )
        return self.risk_profile
    
    async def update_risk_profile(self, user_id: str, updates: Dict[str, Any]):
        """Update specific risk profile settings"""
        await self.load_risk_profile(user_id)
        self.risk_profile.update(updates)
        return await self.save_risk_profile(user_id)
    
    def reset_daily_limits(self):
        """Reset daily trade limits if new day"""
        today = datetime.now().date()
        if today > self.last_trade_reset:
            self.daily_trades = 0
            self.last_trade_reset = today
            print("📅 Daily trade limits reset")
    
    async def load_open_positions(self):
        """Load current open positions"""
        positions = await self.db.auto_positions.find(
            {'status': 'OPEN'},
            {'_id': 0}
        ).to_list(100)
        self.open_positions = positions
        return positions
    
    def check_trade_allowed(self, gem: Dict[str, Any]) -> tuple[bool, str]:
        """Check if a trade is allowed based on risk profile"""
        self.reset_daily_limits()
        
        # Check if auto-execution is enabled
        if not self.risk_profile.get('enabled', False):
            return False, "Auto-execution disabled"
        
        # Check daily trade limit
        if self.daily_trades >= self.risk_profile.get('max_daily_trades', 5):
            return False, "Daily trade limit reached"
        
        # Check open positions limit
        if len(self.open_positions) >= self.risk_profile.get('max_open_positions', 3):
            return False, "Max open positions reached"
        
        # Check minimum score
        min_score = self.risk_profile.get('min_score', 60)
        if gem.get('match_score', 0) < min_score:
            return False, f"Score {gem.get('match_score')} below minimum {min_score}"
        
        # Check alert level
        alert_level = gem.get('alert_level', 'LOW')
        min_level = self.risk_profile.get('min_alert_level', 'HIGH')
        levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        if levels.get(alert_level, 0) < levels.get(min_level, 3):
            return False, f"Alert level {alert_level} below minimum {min_level}"
        
        # Check blacklist
        coin_id = gem.get('coin_id', '')
        if coin_id in self.risk_profile.get('blacklisted_coins', []):
            return False, f"{coin_id} is blacklisted"
        
        # Check if already have position in this coin
        for pos in self.open_positions:
            if pos.get('coin_id') == coin_id:
                return False, f"Already have open position in {coin_id}"
        
        # Check signals match allowed signals
        gem_signals = [s.get('signal') if isinstance(s, dict) else s 
                      for s in gem.get('matching_signals', [])]
        allowed = self.risk_profile.get('allowed_signals', [])
        if allowed and not any(s in allowed for s in gem_signals):
            return False, "No matching allowed signals"
        
        return True, "Trade allowed"
    
    async def execute_trade(self, gem: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade for a detected gem"""
        trade_id = str(uuid.uuid4())[:8]
        
        # Calculate position size
        max_size = self.risk_profile.get('max_position_size_usd', 100)
        price = gem.get('current_price', 0)
        
        if price <= 0:
            return {'success': False, 'error': 'Invalid price'}
        
        # Adjust size based on AI score and learned weights
        adjusted_score = self.ai_engine.get_adjusted_score(
            gem.get('match_score', 0),
            gem.get('matching_signals', [])
        )
        size_multiplier = min(1.0, adjusted_score / 80)  # Full size at 80+ score
        position_size = max_size * size_multiplier
        amount = position_size / price
        
        # Calculate stop loss and take profit
        stop_loss_pct = self.risk_profile.get('stop_loss_pct', 10)
        take_profit_pct = self.risk_profile.get('take_profit_pct', 50)
        stop_loss_price = price * (1 - stop_loss_pct / 100)
        take_profit_price = price * (1 + take_profit_pct / 100)
        
        trade_mode = self.risk_profile.get('mode', 'paper')
        
        # Create position record
        position = {
            'trade_id': trade_id,
            'coin_id': gem.get('coin_id'),
            'symbol': gem.get('symbol'),
            'action': 'BUY',
            'entry_price': price,
            'amount': amount,
            'position_size_usd': position_size,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'signals': gem.get('matching_signals', []),
            'match_score': gem.get('match_score', 0),
            'adjusted_score': adjusted_score,
            'alert_level': gem.get('alert_level'),
            'mode': trade_mode,
            'status': 'OPEN',
            'opened_at': datetime.now().isoformat(),
            'closed_at': None,
            'exit_price': None,
            'profit_pct': None,
            'close_reason': None
        }
        
        # Execute on Kraken if live mode
        if trade_mode == 'live' and self.kraken_service:
            try:
                # Real Kraken order would go here
                # result = await self.kraken_service.create_order(...)
                position['kraken_order_id'] = f"SIMULATED_{trade_id}"
            except Exception as e:
                return {'success': False, 'error': f'Kraken error: {str(e)}'}
        
        # Save position
        await self.db.auto_positions.insert_one(dict(position))
        self.open_positions.append(position)
        self.daily_trades += 1
        
        # Record for AI learning
        await self.ai_engine.record_trade(position)
        
        # Send push notification for trade opened
        if self.notification_service:
            await self.notification_service.notify_trade_completed(position)
        
        print(f"🚀 AUTO-EXECUTED: {trade_mode.upper()} BUY {position['symbol']}")
        print(f"   Price: ${price:.4f} | Size: ${position_size:.2f}")
        print(f"   Stop Loss: ${stop_loss_price:.4f} | Take Profit: ${take_profit_price:.4f}")
        print(f"   Score: {gem.get('match_score')} → {adjusted_score} (AI adjusted)")
        
        return {
            'success': True,
            'trade_id': trade_id,
            'position': position
        }
    
    async def check_positions(self, current_prices: Dict[str, float]):
        """Check open positions for stop loss / take profit"""
        await self.load_open_positions()
        
        for position in self.open_positions:
            coin_id = position.get('coin_id')
            current_price = current_prices.get(coin_id, 0)
            
            if current_price <= 0:
                continue
            
            entry_price = position.get('entry_price', 0)
            stop_loss = position.get('stop_loss_price', 0)
            take_profit = position.get('take_profit_price', 0)
            
            close_reason = None
            
            # Check stop loss
            if current_price <= stop_loss:
                close_reason = 'STOP_LOSS'
            # Check take profit
            elif current_price >= take_profit:
                close_reason = 'TAKE_PROFIT'
            
            if close_reason:
                await self.close_position(position['trade_id'], current_price, close_reason)
    
    async def close_position(self, trade_id: str, exit_price: float, reason: str):
        """Close an open position"""
        position = await self.db.auto_positions.find_one({'trade_id': trade_id})
        if not position:
            return None
        
        entry_price = position.get('entry_price', 0)
        profit_pct = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        # Update position
        await self.db.auto_positions.update_one(
            {'trade_id': trade_id},
            {'$set': {
                'status': 'CLOSED',
                'exit_price': exit_price,
                'profit_pct': profit_pct,
                'close_reason': reason,
                'closed_at': datetime.now().isoformat()
            }}
        )
        
        # Update AI learning
        await self.ai_engine.close_trade(trade_id, exit_price, reason)
        
        # Remove from open positions
        self.open_positions = [p for p in self.open_positions if p.get('trade_id') != trade_id]
        
        # Send push notification for trade closed
        if self.notification_service:
            closed_position = {
                **position,
                'exit_price': exit_price,
                'profit_pct': profit_pct,
                'close_reason': reason
            }
            await self.notification_service.notify_trade_completed(closed_position)
        
        emoji = "✅" if profit_pct > 0 else "❌"
        print(f"{emoji} CLOSED: {position.get('symbol')} | {reason}")
        print(f"   Entry: ${entry_price:.4f} → Exit: ${exit_price:.4f}")
        print(f"   Profit: {profit_pct:+.2f}%")
        
        return {'profit_pct': profit_pct, 'reason': reason}
    
    async def scan_and_execute(self):
        """Perform a scan and execute trades on HIGH gems"""
        # Get current alerts
        alerts = await self.scanner.scan_market()
        
        if not alerts:
            return {'executed': 0, 'reason': 'No alerts'}
        
        executed_trades = []
        
        for gem in alerts:
            # Check if trade is allowed
            allowed, reason = self.check_trade_allowed(gem)
            
            if allowed:
                result = await self.execute_trade(gem)
                if result.get('success'):
                    executed_trades.append(result)
            else:
                if gem.get('alert_level') == 'HIGH':
                    print(f"⏭️ Skipped {gem.get('symbol')}: {reason}")
        
        # Check existing positions
        if self.open_positions and alerts:
            prices = {a['coin_id']: a['current_price'] for a in alerts}
            await self.check_positions(prices)
        
        return {
            'executed': len(executed_trades),
            'trades': executed_trades,
            'open_positions': len(self.open_positions),
            'daily_trades_used': self.daily_trades
        }
    
    async def start_auto_execution(self, interval: int = 60):
        """Start continuous auto-execution loop"""
        self.is_running = True
        print("="*60)
        print("🤖 AUTO-EXECUTION ENGINE STARTED")
        print("="*60)
        print(f"Mode: {self.risk_profile.get('mode', 'paper').upper()}")
        print(f"Min Score: {self.risk_profile.get('min_score', 60)}")
        print(f"Max Position: ${self.risk_profile.get('max_position_size_usd', 100)}")
        print(f"Max Daily Trades: {self.risk_profile.get('max_daily_trades', 5)}")
        print("="*60)
        
        while self.is_running:
            try:
                await self.scan_and_execute()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"Auto-execution error: {e}")
                await asyncio.sleep(30)
    
    def stop_auto_execution(self):
        """Stop auto-execution"""
        self.is_running = False
        print("🛑 Auto-execution stopped")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current auto-execution status"""
        await self.load_open_positions()
        
        # Get trade history
        recent_trades = await self.db.auto_positions.find(
            {},
            {'_id': 0}
        ).sort('opened_at', -1).limit(10).to_list(10)
        
        # Calculate stats
        all_trades = await self.db.auto_positions.find({'status': 'CLOSED'}, {'_id': 0}).to_list(1000)
        total_profit = sum(t.get('profit_pct', 0) for t in all_trades)
        wins = sum(1 for t in all_trades if t.get('profit_pct', 0) > 0)
        
        return {
            'running': self.is_running,
            'enabled': self.risk_profile.get('enabled', False),
            'mode': self.risk_profile.get('mode', 'paper'),
            'daily_trades_used': self.daily_trades,
            'daily_trades_limit': self.risk_profile.get('max_daily_trades', 5),
            'open_positions': len(self.open_positions),
            'open_positions_details': self.open_positions,
            'total_closed_trades': len(all_trades),
            'total_profit_pct': total_profit,
            'win_rate': (wins / len(all_trades) * 100) if all_trades else 0,
            'recent_trades': recent_trades,
            'risk_profile': self.risk_profile
        }
    
    async def get_positions(self, status: str = None) -> List[Dict[str, Any]]:
        """Get positions filtered by status"""
        query = {}
        if status:
            query['status'] = status
        
        positions = await self.db.auto_positions.find(
            query,
            {'_id': 0}
        ).sort('opened_at', -1).to_list(100)
        
        return positions
