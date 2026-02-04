"""
Automated Weekly Trading Executor
Connects AI coin selection + gem finder to live Kraken trading.
Executes trades automatically based on AI recommendations.
Now integrated with Adaptive Strategy Engine for real-time adjustments.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()


class AutomatedWeeklyTrader:
    """
    Automated trading system that:
    1. Uses trained AI to select 10 coins + 1 gem weekly
    2. Executes trades on Kraken
    3. Manages positions with stop-loss/take-profit
    4. Sends alerts on significant events
    5. Adapts strategy based on market regime (via Adaptive Strategy Engine)
    """
    
    def __init__(self, db, kraken_service, ai_trainer, gem_finder, alert_service=None, adaptive_strategy=None):
        self.db = db
        self.kraken = kraken_service
        self.ai_trainer = ai_trainer
        self.gem_finder = gem_finder
        self.alert_service = alert_service
        self.adaptive_strategy = adaptive_strategy  # NEW: Adaptive strategy engine
        
        # Base position sizing (can be overridden by adaptive strategy)
        self.config = {
            'main_position_pct': 9,      # 9% per main coin (10 coins = 90%)
            'gem_position_pct': 10,      # 10% for gem
            'stop_loss_main': 15,        # 15% stop loss
            'stop_loss_gem': 25,         # 25% for gem (higher risk tolerance)
            'take_profit_main': 30,      # 30% take profit
            'take_profit_gem': 100,      # 100% for gem (looking for 2x+)
            'max_slippage': 1.0,         # 1% max slippage
        }
        
        # Kraken symbol mapping
        self.kraken_symbols = {
            'bitcoin': 'XXBTZUSD',
            'ethereum': 'XETHZUSD',
            'litecoin': 'XLTCZUSD',
            'ripple': 'XXRPZUSD',
            'cardano': 'ADAUSD',
            'solana': 'SOLUSD',
            'polkadot': 'DOTUSD',
            'dogecoin': 'XDGUSD',
            'chainlink': 'LINKUSD',
            'avalanche': 'AVAXUSD',
            'cosmos': 'ATOMUSD',
            'stellar': 'XXLMZUSD',
            'monero': 'XXMRZUSD',
            'uniswap': 'UNIUSD',
            'aave': 'AAVEUSD',
            'matic': 'MATICUSD',
            'polygon': 'MATICUSD',
            'shiba-inu': 'SHIBUSD',
            'pepe': 'PEPEUSD',
            'fetch-ai': 'FETUSD',
            'the-sandbox': 'SANDUSD',
            'decentraland': 'MANAUSD',
            'gala': 'GALAUSD',
            'injective': 'INJUSD',
            'sui': 'SUIUSD',
            'aptos': 'APTUSD',
            'arbitrum': 'ARBUSD',
            'optimism': 'OPUSD',
            'sei': 'SEIUSD',
            'celestia': 'TIAUSD',
        }
    
    async def get_portfolio_balance(self) -> float:
        """Get available trading balance from Kraken"""
        try:
            balance = await self.kraken.get_balance()
            usd_balance = float(balance.get('ZUSD', 0))
            return usd_balance
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0
    
    async def get_adaptive_params(self) -> Dict[str, Any]:
        """
        Get current adaptive strategy parameters.
        Falls back to base config if adaptive strategy not available.
        """
        if self.adaptive_strategy:
            try:
                # Detect current regime and adapt
                await self.adaptive_strategy.detect_market_regime()
                result = await self.adaptive_strategy.adapt_strategy()
                
                return {
                    'regime': result.get('regime', 'sideways'),
                    'max_position_pct': result['adapted_params'].get('max_position_pct', self.config['main_position_pct']),
                    'stop_loss': result['adapted_params'].get('stop_loss_pct', self.config['stop_loss_main']),
                    'take_profit': result['adapted_params'].get('take_profit_pct', self.config['take_profit_main']),
                    'min_confidence': result['adapted_params'].get('min_confidence', 60),
                    'max_exposure': result['adapted_params'].get('max_total_exposure', 90),
                    'preferred_assets': result.get('preferred_assets', []),
                    'is_adaptive': True
                }
            except Exception as e:
                print(f"  ⚠️ Adaptive strategy error: {e}, using base config")
        
        # Fallback to base config
        return {
            'regime': 'unknown',
            'max_position_pct': self.config['main_position_pct'],
            'stop_loss': self.config['stop_loss_main'],
            'take_profit': self.config['take_profit_main'],
            'min_confidence': 60,
            'max_exposure': 90,
            'preferred_assets': [],
            'is_adaptive': False
        }
    
    async def execute_weekly_rebalance(self, paper_trade: bool = True) -> Dict[str, Any]:
        """
        Execute weekly portfolio rebalance based on AI selection.
        NOW WITH ADAPTIVE STRATEGY: Automatically adjusts position sizes,
        stop-losses, and take-profits based on current market regime.
        
        Args:
            paper_trade: If True, simulate trades. If False, execute real trades.
            
        Returns:
            Execution results
        """
        print(f"\n{'='*60}")
        print(f"🤖 AUTOMATED WEEKLY REBALANCE - {'PAPER' if paper_trade else 'REAL'}")
        print(f"{'='*60}")
        print(f"Time: {datetime.now().isoformat()}")
        
        # Get adaptive strategy parameters
        adaptive_params = await self.get_adaptive_params()
        regime = adaptive_params['regime']
        is_adaptive = adaptive_params['is_adaptive']
        
        print(f"📊 Market Regime: {regime.upper()}" + (" (Adaptive)" if is_adaptive else " (Base)"))
        print(f"   Position Size: {adaptive_params['max_position_pct']:.1f}%")
        print(f"   Stop Loss: {adaptive_params['stop_loss']:.1f}%")
        print(f"   Take Profit: {adaptive_params['take_profit']:.1f}%")
        print(f"   Min Confidence: {adaptive_params['min_confidence']:.0f}%")
        
        # Get available balance
        if not paper_trade:
            balance = await self.get_portfolio_balance()
            if balance < 100:
                return {'success': False, 'error': 'Insufficient balance', 'balance': balance}
        else:
            balance = 10000  # Paper trade with $10k
        
        print(f"\nAvailable Balance: ${balance:,.2f}")
        
        # Apply max exposure limit from adaptive strategy
        max_deployable = balance * (adaptive_params['max_exposure'] / 100)
        print(f"Max Deployable ({adaptive_params['max_exposure']:.0f}%): ${max_deployable:,.2f}")
        
        # Get AI selections
        portfolio = await self.ai_trainer.select_portfolio(datetime.now())
        
        if not portfolio.get('main_coins'):
            return {'success': False, 'error': 'AI selection failed'}
        
        # Filter coins by minimum confidence if adaptive
        if is_adaptive:
            min_conf = adaptive_params['min_confidence']
            original_count = len(portfolio['main_coins'])
            portfolio['main_coins'] = [
                c for c in portfolio['main_coins'] 
                if c.get('total_score', 0) >= min_conf
            ]
            if len(portfolio['main_coins']) < original_count:
                print(f"   Filtered out {original_count - len(portfolio['main_coins'])} coins below {min_conf}% confidence")
        
        # Get gem
        gems = await self.gem_finder.find_gems(datetime.now(), max_gems=1)
        gem = gems[0] if gems else None
        
        print(f"\nSelected {len(portfolio['main_coins'])} main coins + {1 if gem else 0} gem")
        
        # Calculate position sizes using adaptive parameters
        # Distribute evenly across selected coins, respecting max exposure
        num_positions = len(portfolio['main_coins']) + (1 if gem else 0)
        position_pct = min(adaptive_params['max_position_pct'], adaptive_params['max_exposure'] / num_positions) if num_positions > 0 else 0
        
        main_position_size = balance * (position_pct / 100)
        gem_position_size = balance * (min(adaptive_params['max_position_pct'] * 1.1, 15) / 100)  # Gem gets slightly more
        
        print(f"Position Size per Coin: ${main_position_size:.2f} ({position_pct:.1f}%)")
        
        trades = []
        
        # Use adaptive stop-loss and take-profit
        stop_loss = adaptive_params['stop_loss']
        take_profit = adaptive_params['take_profit']
        gem_stop_loss = min(stop_loss * 1.5, 25)  # Gems get wider stops
        gem_take_profit = max(take_profit * 2, 100)  # Gems target higher returns
        
        # Execute main coin trades
        for coin_data in portfolio['main_coins']:
            coin_id = coin_data['coin_id']
            kraken_symbol = self.kraken_symbols.get(coin_id)
            
            if not kraken_symbol:
                print(f"  ⚠️ {coin_id}: No Kraken symbol")
                continue
            
            trade_result = await self._execute_trade(
                coin_id=coin_id,
                symbol=kraken_symbol,
                amount_usd=main_position_size,
                stop_loss_pct=stop_loss,  # Adaptive stop loss
                take_profit_pct=take_profit,  # Adaptive take profit
                paper_trade=paper_trade,
                is_gem=False,
                ai_score=coin_data['total_score']
            )
            
            if trade_result:
                trade_result['regime'] = regime
                trade_result['adaptive_params'] = adaptive_params
                trades.append(trade_result)
        
        # Execute gem trade
        if gem:
            kraken_symbol = self.kraken_symbols.get(gem['coin_id'])
            
            if kraken_symbol:
                gem_trade = await self._execute_trade(
                    coin_id=gem['coin_id'],
                    symbol=kraken_symbol,
                    amount_usd=gem_position_size,
                    stop_loss_pct=self.config['stop_loss_gem'],
                    take_profit_pct=self.config['take_profit_gem'],
                    paper_trade=paper_trade,
                    is_gem=True,
                    ai_score=gem['total_score']
                )
                
                if gem_trade:
                    trades.append(gem_trade)
        
        # Store execution record
        execution = {
            'timestamp': datetime.now().isoformat(),
            'paper_trade': paper_trade,
            'balance': balance,
            'trades': trades,
            'total_trades': len(trades),
            'main_coins': len([t for t in trades if not t.get('is_gem')]),
            'gems': len([t for t in trades if t.get('is_gem')]),
            'total_invested': sum(t.get('amount_usd', 0) for t in trades)
        }
        
        # Store execution record (exclude _id from response)
        execution_doc = dict(execution)
        await self.db.weekly_executions.insert_one(execution_doc)
        
        # Remove _id for response
        execution.pop('_id', None)
        
        # Send alert
        if self.alert_service and not paper_trade:
            await self._send_execution_alert(execution)
        
        print(f"\n{'='*60}")
        print(f"✅ Executed {len(trades)} trades")
        print(f"Total Invested: ${execution['total_invested']:,.2f}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'execution': execution
        }
    
    async def _execute_trade(
        self,
        coin_id: str,
        symbol: str,
        amount_usd: float,
        stop_loss_pct: float,
        take_profit_pct: float,
        paper_trade: bool,
        is_gem: bool,
        ai_score: float
    ) -> Optional[Dict]:
        """Execute a single trade"""
        try:
            # Get current price
            ticker = await self.kraken.get_ticker(symbol)
            if not ticker:
                print(f"  ❌ {coin_id}: Failed to get price")
                return None
            
            current_price = float(ticker.get('c', [0])[0])
            if current_price <= 0:
                return None
            
            # Calculate quantity
            quantity = amount_usd / current_price
            
            # Calculate stop/take profit prices
            stop_price = current_price * (1 - stop_loss_pct / 100)
            take_profit_price = current_price * (1 + take_profit_pct / 100)
            
            trade_record = {
                'coin_id': coin_id,
                'symbol': symbol,
                'side': 'buy',
                'amount_usd': round(amount_usd, 2),
                'quantity': quantity,
                'entry_price': current_price,
                'stop_loss_price': round(stop_price, 6),
                'take_profit_price': round(take_profit_price, 6),
                'is_gem': is_gem,
                'ai_score': ai_score,
                'paper_trade': paper_trade,
                'status': 'EXECUTED' if not paper_trade else 'PAPER',
                'executed_at': datetime.now().isoformat()
            }
            
            if not paper_trade:
                # Execute real trade on Kraken
                order = await self.kraken.create_order(
                    symbol=symbol,
                    side='buy',
                    order_type='market',
                    volume=quantity
                )
                
                if order:
                    trade_record['order_id'] = order.get('txid', [''])[0]
                    trade_record['status'] = 'FILLED'
                    print(f"  ✅ {coin_id}: Bought ${amount_usd:.2f} @ ${current_price:.4f}")
                else:
                    trade_record['status'] = 'FAILED'
                    print(f"  ❌ {coin_id}: Order failed")
            else:
                print(f"  📝 {coin_id}: Paper trade ${amount_usd:.2f} @ ${current_price:.4f} {'💎' if is_gem else ''}")
            
            # Store position (copy to avoid ObjectId issues)
            position_doc = dict(trade_record)
            await self.db.active_positions.insert_one(position_doc)
            
            return trade_record
            
        except Exception as e:
            print(f"  ❌ {coin_id}: Error - {e}")
            return None
    
    async def check_positions(self) -> Dict[str, Any]:
        """Check all active positions for stop-loss/take-profit triggers"""
        positions = await self.db.active_positions.find(
            {'status': {'$in': ['EXECUTED', 'PAPER', 'FILLED']}}
        ).to_list(100)
        
        triggered = []
        
        for pos in positions:
            symbol = pos.get('symbol')
            if not symbol:
                continue
            
            try:
                ticker = await self.kraken.get_ticker(symbol)
                if not ticker:
                    continue
                
                current_price = float(ticker.get('c', [0])[0])
                entry_price = pos.get('entry_price', 0)
                
                if entry_price <= 0:
                    continue
                
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                # Check stop loss
                if current_price <= pos.get('stop_loss_price', 0):
                    await self._close_position(pos, current_price, 'STOP_LOSS')
                    triggered.append({
                        'coin_id': pos['coin_id'],
                        'reason': 'STOP_LOSS',
                        'pnl_pct': round(pnl_pct, 2)
                    })
                
                # Check take profit
                elif current_price >= pos.get('take_profit_price', float('inf')):
                    await self._close_position(pos, current_price, 'TAKE_PROFIT')
                    triggered.append({
                        'coin_id': pos['coin_id'],
                        'reason': 'TAKE_PROFIT',
                        'pnl_pct': round(pnl_pct, 2)
                    })
                    
            except Exception as e:
                print(f"Error checking {pos.get('coin_id')}: {e}")
        
        return {
            'positions_checked': len(positions),
            'triggered': triggered
        }
    
    async def _close_position(self, position: Dict, exit_price: float, reason: str):
        """Close a position"""
        entry_price = position.get('entry_price', 0)
        pnl_pct = (exit_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
        pnl_usd = position.get('amount_usd', 0) * (pnl_pct / 100)
        
        # Update position
        await self.db.active_positions.update_one(
            {'_id': position['_id']},
            {'$set': {
                'status': 'CLOSED',
                'exit_price': exit_price,
                'exit_reason': reason,
                'pnl_pct': round(pnl_pct, 2),
                'pnl_usd': round(pnl_usd, 2),
                'closed_at': datetime.now().isoformat()
            }}
        )
        
        # Record for learning
        await self.db.trade_outcomes.insert_one({
            'coin_id': position['coin_id'],
            'is_gem': position.get('is_gem', False),
            'ai_score': position.get('ai_score', 0),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_pct': round(pnl_pct, 2),
            'pnl_usd': round(pnl_usd, 2),
            'reason': reason,
            'closed_at': datetime.now().isoformat()
        })
        
        # Send alert
        if self.alert_service:
            await self._send_position_alert(position, exit_price, reason, pnl_pct)
    
    async def _send_execution_alert(self, execution: Dict):
        """Send alert for weekly execution"""
        if not self.alert_service:
            return
        
        message = f"""
🤖 Weekly Rebalance Complete

Trades: {execution['total_trades']}
Main Coins: {execution['main_coins']}
Gems: {execution['gems']}
Total Invested: ${execution['total_invested']:,.2f}

Time: {execution['timestamp']}
        """
        
        await self.alert_service.send_alert(
            title="Weekly Rebalance",
            message=message,
            alert_type="execution"
        )
    
    async def _send_position_alert(self, position: Dict, exit_price: float, reason: str, pnl_pct: float):
        """Send alert for position close"""
        if not self.alert_service:
            return
        
        emoji = "🟢" if pnl_pct > 0 else "🔴"
        gem_emoji = "💎" if position.get('is_gem') else ""
        
        message = f"""
{emoji} Position Closed {gem_emoji}

Coin: {position['coin_id']}
Reason: {reason}
P/L: {pnl_pct:+.2f}%

Entry: ${position.get('entry_price', 0):.4f}
Exit: ${exit_price:.4f}
        """
        
        await self.alert_service.send_alert(
            title=f"{reason}: {position['coin_id']}",
            message=message,
            alert_type="position_close"
        )
    
    async def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """Get recent execution history"""
        executions = await self.db.weekly_executions.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(limit).to_list(limit)
        
        return executions
    
    async def get_active_positions(self) -> List[Dict]:
        """Get all active positions"""
        positions = await self.db.active_positions.find(
            {'status': {'$in': ['EXECUTED', 'PAPER', 'FILLED']}},
            {'_id': 0}
        ).to_list(100)
        
        return positions
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall trading performance summary"""
        # Get closed positions
        closed = await self.db.active_positions.find(
            {'status': 'CLOSED'},
            {'_id': 0}
        ).to_list(1000)
        
        if not closed:
            return {'message': 'No closed trades yet'}
        
        total_pnl = sum(p.get('pnl_usd', 0) for p in closed)
        winning = [p for p in closed if p.get('pnl_pct', 0) > 0]
        gems = [p for p in closed if p.get('is_gem')]
        gem_winners = [p for p in gems if p.get('pnl_pct', 0) > 0]
        
        return {
            'total_trades': len(closed),
            'winning_trades': len(winning),
            'win_rate': round(len(winning) / len(closed) * 100, 1),
            'total_pnl_usd': round(total_pnl, 2),
            'avg_pnl_pct': round(sum(p.get('pnl_pct', 0) for p in closed) / len(closed), 2),
            'gem_trades': len(gems),
            'gem_win_rate': round(len(gem_winners) / len(gems) * 100, 1) if gems else 0,
            'best_trade': max(closed, key=lambda x: x.get('pnl_pct', 0)),
            'worst_trade': min(closed, key=lambda x: x.get('pnl_pct', 0))
        }
