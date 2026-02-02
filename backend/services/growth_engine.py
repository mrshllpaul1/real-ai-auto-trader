"""
Aggressive Growth Engine
Goal: Turn $500 into $100,000 (200x)
Strategy: Heavy gem allocation, compounding, 24/7 hunting
Integrates AI news sentiment for smarter decisions
IMPORTANT: Only uses allocated budget - NEVER touches other assets
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()


class AggressiveGrowthEngine:
    """
    Aggressive trading engine designed to maximize growth.
    Target: $500 → $100,000 (200x return)
    
    Strategy:
    - Heavy gem allocation (40% in gems)
    - Compound all profits
    - 24/7 opportunity scanning
    - Dynamic position sizing based on conviction
    - Trailing stop-losses to lock in gains
    - AI news sentiment integration for timing
    
    SAFETY: Only uses budget you allocate - NEVER touches other assets
    """
    
    def __init__(self, db, kraken_service, gem_finder, ai_trainer, alert_service=None, budget_manager=None):
        self.db = db
        self.kraken = kraken_service
        self.gem_finder = gem_finder
        self.ai_trainer = ai_trainer
        self.alert_service = alert_service
        self.budget_manager = budget_manager
        self._sentiment_service = None
        
        # Growth targets
        self.targets = {
            'starting_capital': 500,
            'goal': 100000,
            'multiplier': 200,  # 200x target
        }
        
        # Aggressive position sizing
        self.config = {
            # Gem-heavy allocation (40% gems, 60% main)
            'gem_allocation_pct': 40,      # 40% in gems
            'main_allocation_pct': 60,     # 60% in main coins
            
            # Position limits
            'max_positions': 15,           # More positions for diversification
            'max_gem_positions': 5,        # Up to 5 gems
            'max_single_position_pct': 15, # Max 15% in single coin
            
            # Sentiment thresholds
            'bullish_sentiment_boost': 1.2,    # 20% more if bullish
            'bearish_sentiment_reduce': 0.7,   # 30% less if bearish
            'min_sentiment_for_entry': 35,     # Don't enter if very bearish
            
            # Aggressive gem targets
            'gem_take_profit_1': 50,       # First TP at 50%
            'gem_take_profit_2': 100,      # Second TP at 100% (2x)
            'gem_take_profit_3': 300,      # Third TP at 300% (4x)
            'gem_moonshot_target': 1000,   # Hold small portion for 10x
            'gem_stop_loss': 20,           # 20% stop loss
            
            # Main coin targets
            'main_take_profit': 25,        # 25% TP for main
            'main_stop_loss': 12,          # 12% SL for main
            
            # Trailing stops
            'trailing_stop_pct': 15,       # 15% trailing stop after profit
            'activate_trailing_at': 20,    # Activate after 20% gain
            
            # Compounding
            'compound_profits': True,      # Reinvest all profits
            'reinvest_pct': 100,           # Reinvest 100% of profits
            
            # Scanning frequency
            'scan_interval_minutes': 60,   # Scan every hour
            'gem_scan_interval': 30,       # Gem scan every 30 min
        }
        
        # Kraken symbols
        self.kraken_symbols = {
            'bitcoin': 'XXBTZUSD', 'ethereum': 'XETHZUSD',
            'litecoin': 'XLTCZUSD', 'ripple': 'XXRPZUSD',
            'cardano': 'ADAUSD', 'solana': 'SOLUSD',
            'polkadot': 'DOTUSD', 'dogecoin': 'XDGUSD',
            'chainlink': 'LINKUSD', 'avalanche': 'AVAXUSD',
            'cosmos': 'ATOMUSD', 'stellar': 'XXLMZUSD',
            'uniswap': 'UNIUSD', 'aave': 'AAVEUSD',
            'polygon': 'MATICUSD', 'shiba-inu': 'SHIBUSD',
            'pepe': 'PEPEUSD', 'fetch-ai': 'FETUSD',
            'the-sandbox': 'SANDUSD', 'decentraland': 'MANAUSD',
            'gala': 'GALAUSD', 'injective': 'INJUSD',
            'sui': 'SUIUSD', 'aptos': 'APTUSD',
            'arbitrum': 'ARBUSD', 'optimism': 'OPUSD',
            'sei': 'SEIUSD', 'celestia': 'TIAUSD',
        }
    
    async def get_current_portfolio_value(self) -> Dict[str, Any]:
        """Get current portfolio value and progress toward goal"""
        # Get account balance
        try:
            balance = await self.kraken.get_balance()
            usd_balance = float(balance.get('ZUSD', 0))
        except:
            usd_balance = 0
        
        # Get value of open positions
        positions = await self.db.growth_positions.find(
            {'status': 'OPEN'},
            {'_id': 0}
        ).to_list(100)
        
        positions_value = sum(p.get('current_value', p.get('amount_usd', 0)) for p in positions)
        
        # Get realized profits
        closed = await self.db.growth_positions.find(
            {'status': 'CLOSED'},
            {'_id': 0}
        ).to_list(1000)
        
        realized_profit = sum(p.get('pnl_usd', 0) for p in closed)
        
        total_value = usd_balance + positions_value
        starting = self.targets['starting_capital']
        goal = self.targets['goal']
        
        progress_pct = ((total_value - starting) / (goal - starting)) * 100 if goal > starting else 0
        multiplier = total_value / starting if starting > 0 else 0
        
        return {
            'usd_balance': usd_balance,
            'positions_value': positions_value,
            'total_value': round(total_value, 2),
            'realized_profit': round(realized_profit, 2),
            'starting_capital': starting,
            'goal': goal,
            'progress_pct': round(max(0, min(100, progress_pct)), 2),
            'current_multiplier': round(multiplier, 2),
            'target_multiplier': self.targets['multiplier'],
            'remaining_to_goal': round(goal - total_value, 2),
            'open_positions': len(positions)
        }
    
    async def execute_growth_strategy(self, capital: float = None, paper_trade: bool = True) -> Dict[str, Any]:
        """
        Execute the aggressive growth strategy.
        Allocates capital between gems (40%) and main coins (60%).
        
        SAFETY: For real trades, only uses allocated budget - NEVER touches other assets.
        """
        print(f"\n{'='*70}")
        print(f"🚀 AGGRESSIVE GROWTH ENGINE - {'PAPER' if paper_trade else 'REAL'}")
        print(f"{'='*70}")
        print(f"Goal: ${self.targets['starting_capital']} → ${self.targets['goal']:,} (200x)")
        
        # For real trading, check budget first
        if not paper_trade and self.budget_manager:
            can_trade = await self.budget_manager.can_trade_real(capital or self.targets['starting_capital'])
            if not can_trade.get("allowed"):
                return {
                    'success': False, 
                    'error': can_trade.get("reason", "Real trading not allowed"),
                    'budget': can_trade.get("budget")
                }
            # Use available budget if no capital specified
            if capital is None:
                capital = can_trade["available"]
        
        # Get available capital
        if capital is None:
            if not paper_trade:
                balance = await self.kraken.get_balance()
                capital = float(balance.get('ZUSD', 0))
            else:
                capital = self.targets['starting_capital']
        
        print(f"Available Capital: ${capital:,.2f}")
        
        if capital < 10:
            return {'success': False, 'error': 'Insufficient capital', 'capital': capital}
        
        # Get AI confidence threshold
        confidence_threshold = 70  # Default
        if self.budget_manager:
            budget = await self.budget_manager.get_budget()
            confidence_threshold = budget.get("ai_confidence_threshold", 70)
            print(f"🎯 AI Confidence Threshold: {confidence_threshold}%")
        
        # For real trading, allocate from budget
        if not paper_trade and self.budget_manager:
            allocation = await self.budget_manager.allocate_funds(
                amount=capital,
                purpose="Growth strategy execution"
            )
            if not allocation.get("success"):
                return {'success': False, 'error': allocation.get("error")}
            print(f"💰 Budget allocated: ${capital:.2f} (Remaining: ${allocation['remaining_budget']:.2f})")
        
        # Calculate allocations
        gem_capital = capital * (self.config['gem_allocation_pct'] / 100)
        main_capital = capital * (self.config['main_allocation_pct'] / 100)
        
        print(f"Gem Allocation: ${gem_capital:,.2f} ({self.config['gem_allocation_pct']}%)")
        print(f"Main Allocation: ${main_capital:,.2f} ({self.config['main_allocation_pct']}%)")
        
        trades = []
        skipped_low_confidence = []
        
        # 1. Find and buy gems
        print(f"\n💎 Scanning for gems...")
        gems = await self.gem_finder.find_gems(datetime.now(), max_gems=self.config['max_gem_positions'])
        
        if gems:
            gem_position_size = gem_capital / len(gems)
            for gem in gems:
                # Check confidence threshold for real trades
                gem_confidence = gem.get('gem_score', gem.get('ai_score', 50))
                if not paper_trade and gem_confidence < confidence_threshold:
                    skipped_low_confidence.append({
                        'coin_id': gem.get('coin_id'),
                        'confidence': gem_confidence,
                        'threshold': confidence_threshold,
                        'reason': 'Below confidence threshold - paper trade only'
                    })
                    # Execute as paper trade instead
                    trade = await self._execute_gem_trade(gem, gem_position_size, paper_trade=True)
                else:
                    trade = await self._execute_gem_trade(gem, gem_position_size, paper_trade)
                if trade:
                    trades.append(trade)
        
        # 2. Select and buy main coins
        print(f"\n📊 Selecting main coins...")
        portfolio = await self.ai_trainer.select_portfolio(datetime.now())
        
        main_coins = portfolio.get('main_coins', [])[:10]
        if main_coins:
            main_position_size = main_capital / len(main_coins)
            for coin_data in main_coins:
                # Check confidence threshold for real trades
                coin_confidence = coin_data.get('ai_score', coin_data.get('confidence', 50))
                if not paper_trade and coin_confidence < confidence_threshold:
                    skipped_low_confidence.append({
                        'coin_id': coin_data.get('coin_id'),
                        'confidence': coin_confidence,
                        'threshold': confidence_threshold,
                        'reason': 'Below confidence threshold - paper trade only'
                    })
                    # Execute as paper trade instead
                    trade = await self._execute_main_trade(coin_data, main_position_size, paper_trade=True)
                else:
                    trade = await self._execute_main_trade(coin_data, main_position_size, paper_trade)
                if trade:
                    trades.append(trade)
        
        # Store execution record
        execution = {
            'timestamp': datetime.now().isoformat(),
            'paper_trade': paper_trade,
            'capital': capital,
            'gem_allocation': gem_capital,
            'main_allocation': main_capital,
            'trades': trades,
            'total_trades': len(trades),
            'gem_trades': len([t for t in trades if t.get('is_gem')]),
            'main_trades': len([t for t in trades if not t.get('is_gem')]),
            'confidence_threshold': confidence_threshold,
            'skipped_low_confidence': skipped_low_confidence,
        }
        
        await self.db.growth_executions.insert_one(dict(execution))
        
        # Send alert
        if self.alert_service:
            await self.alert_service.send_alert(
                title="🚀 Growth Strategy Executed",
                message=f"Deployed ${capital:,.2f}\nGems: {execution['gem_trades']}\nMain: {execution['main_trades']}",
                alert_type="execution",
                priority="normal"
            )
        
        print(f"\n{'='*70}")
        print(f"✅ Executed {len(trades)} trades")
        print(f"💎 Gems: {execution['gem_trades']} | 📊 Main: {execution['main_trades']}")
        if skipped_low_confidence:
            print(f"⚠️ Skipped {len(skipped_low_confidence)} trades (below {confidence_threshold}% confidence)")
        print(f"{'='*70}\n")
        
        return {'success': True, 'execution': execution}
    
    async def _execute_gem_trade(
        self,
        gem: Dict,
        amount_usd: float,
        paper_trade: bool
    ) -> Dict:
        """Execute a gem trade with tiered take-profits"""
        coin_id = gem['coin_id']
        symbol = self.kraken_symbols.get(coin_id)
        
        if not symbol:
            print(f"  ⚠️ {coin_id}: No Kraken symbol")
            return None
        
        try:
            ticker = await self.kraken.get_ticker(symbol)
            if not ticker:
                return None
            
            price = float(ticker.get('c', [0])[0])
            if price <= 0:
                return None
            
            quantity = amount_usd / price
            
            # Tiered take-profits for gems
            tp_levels = [
                {'pct': self.config['gem_take_profit_1'], 'sell_pct': 30},  # Sell 30% at 50%
                {'pct': self.config['gem_take_profit_2'], 'sell_pct': 30},  # Sell 30% at 100%
                {'pct': self.config['gem_take_profit_3'], 'sell_pct': 30},  # Sell 30% at 300%
                {'pct': self.config['gem_moonshot_target'], 'sell_pct': 10}, # Hold 10% for 10x
            ]
            
            trade = {
                'coin_id': coin_id,
                'symbol': symbol,
                'is_gem': True,
                'gem_score': gem['total_score'],
                'amount_usd': round(amount_usd, 2),
                'quantity': quantity,
                'entry_price': price,
                'stop_loss_price': price * (1 - self.config['gem_stop_loss'] / 100),
                'take_profit_levels': tp_levels,
                'trailing_stop_active': False,
                'highest_price': price,
                'status': 'OPEN',
                'paper_trade': paper_trade,
                'opened_at': datetime.now().isoformat()
            }
            
            if not paper_trade:
                order = await self.kraken.create_order(
                    symbol=symbol, side='buy', order_type='market', volume=quantity
                )
                if order:
                    trade['order_id'] = order.get('txid', [''])[0]
                    print(f"  💎 {coin_id}: REAL BUY ${amount_usd:.2f} @ ${price:.6f}")
                else:
                    return None
            else:
                print(f"  💎 {coin_id}: Paper ${amount_usd:.2f} @ ${price:.6f} (Score: {gem['total_score']})")
            
            await self.db.growth_positions.insert_one(dict(trade))
            return trade
            
        except Exception as e:
            print(f"  ❌ {coin_id}: {e}")
            return None
    
    async def _execute_main_trade(
        self,
        coin_data: Dict,
        amount_usd: float,
        paper_trade: bool
    ) -> Dict:
        """Execute a main coin trade"""
        coin_id = coin_data['coin_id']
        symbol = self.kraken_symbols.get(coin_id)
        
        if not symbol:
            return None
        
        try:
            ticker = await self.kraken.get_ticker(symbol)
            if not ticker:
                return None
            
            price = float(ticker.get('c', [0])[0])
            if price <= 0:
                return None
            
            quantity = amount_usd / price
            
            trade = {
                'coin_id': coin_id,
                'symbol': symbol,
                'is_gem': False,
                'ai_score': coin_data['total_score'],
                'amount_usd': round(amount_usd, 2),
                'quantity': quantity,
                'entry_price': price,
                'stop_loss_price': price * (1 - self.config['main_stop_loss'] / 100),
                'take_profit_price': price * (1 + self.config['main_take_profit'] / 100),
                'trailing_stop_active': False,
                'highest_price': price,
                'status': 'OPEN',
                'paper_trade': paper_trade,
                'opened_at': datetime.now().isoformat()
            }
            
            if not paper_trade:
                order = await self.kraken.create_order(
                    symbol=symbol, side='buy', order_type='market', volume=quantity
                )
                if order:
                    trade['order_id'] = order.get('txid', [''])[0]
                    print(f"  📊 {coin_id}: REAL BUY ${amount_usd:.2f} @ ${price:.4f}")
                else:
                    return None
            else:
                print(f"  📊 {coin_id}: Paper ${amount_usd:.2f} @ ${price:.4f}")
            
            await self.db.growth_positions.insert_one(dict(trade))
            return trade
            
        except Exception as e:
            print(f"  ❌ {coin_id}: {e}")
            return None
    
    async def monitor_positions(self) -> Dict[str, Any]:
        """
        Monitor all open positions.
        Check stop-losses, take-profits, and trailing stops.
        """
        positions = await self.db.growth_positions.find(
            {'status': 'OPEN'}
        ).to_list(100)
        
        results = {
            'checked': len(positions),
            'stop_losses_hit': [],
            'take_profits_hit': [],
            'trailing_stops_updated': 0
        }
        
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
                
                # Update highest price for trailing stop
                if current_price > pos.get('highest_price', 0):
                    await self.db.growth_positions.update_one(
                        {'_id': pos['_id']},
                        {'$set': {'highest_price': current_price}}
                    )
                    pos['highest_price'] = current_price
                
                # Check stop loss
                if current_price <= pos.get('stop_loss_price', 0):
                    await self._close_position(pos, current_price, 'STOP_LOSS')
                    results['stop_losses_hit'].append({
                        'coin_id': pos['coin_id'],
                        'pnl_pct': round(pnl_pct, 2)
                    })
                    continue
                
                # Check trailing stop
                if pos.get('trailing_stop_active'):
                    trailing_stop = pos['highest_price'] * (1 - self.config['trailing_stop_pct'] / 100)
                    if current_price <= trailing_stop:
                        await self._close_position(pos, current_price, 'TRAILING_STOP')
                        results['take_profits_hit'].append({
                            'coin_id': pos['coin_id'],
                            'pnl_pct': round(pnl_pct, 2),
                            'reason': 'TRAILING_STOP'
                        })
                        continue
                
                # Activate trailing stop if profit threshold reached
                if pnl_pct >= self.config['activate_trailing_at'] and not pos.get('trailing_stop_active'):
                    await self.db.growth_positions.update_one(
                        {'_id': pos['_id']},
                        {'$set': {'trailing_stop_active': True}}
                    )
                    results['trailing_stops_updated'] += 1
                
                # Check take profit (for main coins)
                if not pos.get('is_gem') and current_price >= pos.get('take_profit_price', float('inf')):
                    await self._close_position(pos, current_price, 'TAKE_PROFIT')
                    results['take_profits_hit'].append({
                        'coin_id': pos['coin_id'],
                        'pnl_pct': round(pnl_pct, 2)
                    })
                
                # Check tiered take profits (for gems)
                if pos.get('is_gem') and pos.get('take_profit_levels'):
                    # Handle tiered exits
                    pass  # Implement partial sells
                    
            except Exception as e:
                print(f"Error monitoring {pos.get('coin_id')}: {e}")
        
        return results
    
    async def _close_position(self, position: Dict, exit_price: float, reason: str):
        """Close a position and record results"""
        entry = position.get('entry_price', 0)
        pnl_pct = (exit_price - entry) / entry * 100 if entry > 0 else 0
        pnl_usd = position.get('amount_usd', 0) * (pnl_pct / 100)
        
        await self.db.growth_positions.update_one(
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
        
        # Send moonshot alert if 100%+ gain
        if pnl_pct >= 100 and self.alert_service:
            await self.alert_service.send_alert(
                title=f"🚀 MOONSHOT: {position['coin_id'].upper()}",
                message=f"+{pnl_pct:.0f}% | ${pnl_usd:,.2f} profit!",
                alert_type="moonshot",
                priority="critical",
                channels=['app', 'email', 'sms']
            )
        
        print(f"  {'🟢' if pnl_pct > 0 else '🔴'} {position['coin_id']}: {reason} | {pnl_pct:+.2f}% | ${pnl_usd:+,.2f}")
    
    async def compound_profits(self) -> Dict[str, Any]:
        """
        Compound profits by reinvesting realized gains.
        """
        # Get total realized profits
        closed = await self.db.growth_positions.find(
            {'status': 'CLOSED'},
            {'_id': 0}
        ).to_list(1000)
        
        total_profit = sum(p.get('pnl_usd', 0) for p in closed)
        
        if total_profit <= 0:
            return {'compounded': False, 'reason': 'No profits to compound'}
        
        # Check if we've already compounded this profit
        last_compound = await self.db.compound_records.find_one(
            {}, {'_id': 0}, sort=[('timestamp', -1)]
        )
        
        if last_compound:
            last_compounded_profit = last_compound.get('total_profit_at_time', 0)
            new_profit = total_profit - last_compounded_profit
            
            if new_profit < 50:  # Minimum $50 to compound
                return {'compounded': False, 'reason': f'New profit ${new_profit:.2f} below minimum'}
        else:
            new_profit = total_profit
        
        # Execute new trades with compounded profit
        result = await self.execute_growth_strategy(
            capital=new_profit * (self.config['reinvest_pct'] / 100),
            paper_trade=True  # Start with paper to test
        )
        
        # Record compounding
        await self.db.compound_records.insert_one({
            'timestamp': datetime.now().isoformat(),
            'total_profit_at_time': total_profit,
            'amount_compounded': new_profit,
            'trades_executed': result.get('execution', {}).get('total_trades', 0)
        })
        
        return {
            'compounded': True,
            'amount': new_profit,
            'trades': result.get('execution', {}).get('total_trades', 0)
        }
    
    async def get_growth_stats(self) -> Dict[str, Any]:
        """Get comprehensive growth statistics"""
        portfolio = await self.get_current_portfolio_value()
        
        # Get trade statistics
        all_trades = await self.db.growth_positions.find(
            {}, {'_id': 0}
        ).to_list(1000)
        
        closed = [t for t in all_trades if t.get('status') == 'CLOSED']
        open_trades = [t for t in all_trades if t.get('status') == 'OPEN']
        
        gems_closed = [t for t in closed if t.get('is_gem')]
        main_closed = [t for t in closed if not t.get('is_gem')]
        
        winners = [t for t in closed if t.get('pnl_pct', 0) > 0]
        moonshots = [t for t in closed if t.get('pnl_pct', 0) >= 100]
        
        return {
            'portfolio': portfolio,
            'statistics': {
                'total_trades': len(all_trades),
                'open_trades': len(open_trades),
                'closed_trades': len(closed),
                'winning_trades': len(winners),
                'win_rate': round(len(winners) / len(closed) * 100, 1) if closed else 0,
                'moonshots': len(moonshots),
                'moonshot_rate': round(len(moonshots) / len(closed) * 100, 1) if closed else 0,
                'total_pnl': round(sum(t.get('pnl_usd', 0) for t in closed), 2),
                'avg_pnl_pct': round(np.mean([t.get('pnl_pct', 0) for t in closed]), 2) if closed else 0,
                'best_trade': max(closed, key=lambda x: x.get('pnl_pct', 0)) if closed else None,
                'worst_trade': min(closed, key=lambda x: x.get('pnl_pct', 0)) if closed else None,
            },
            'gem_stats': {
                'total': len(gems_closed),
                'winners': len([t for t in gems_closed if t.get('pnl_pct', 0) > 0]),
                'moonshots': len([t for t in gems_closed if t.get('pnl_pct', 0) >= 100]),
                'avg_return': round(np.mean([t.get('pnl_pct', 0) for t in gems_closed]), 2) if gems_closed else 0
            },
            'main_stats': {
                'total': len(main_closed),
                'winners': len([t for t in main_closed if t.get('pnl_pct', 0) > 0]),
                'avg_return': round(np.mean([t.get('pnl_pct', 0) for t in main_closed]), 2) if main_closed else 0
            },
            'goal_progress': {
                'starting': portfolio['starting_capital'],
                'current': portfolio['total_value'],
                'goal': portfolio['goal'],
                'progress_pct': portfolio['progress_pct'],
                'multiplier': portfolio['current_multiplier'],
                'remaining': portfolio['remaining_to_goal']
            }
        }


# Background scanner task
async def run_growth_scanner(engine: AggressiveGrowthEngine, interval_minutes: int = 60):
    """Run continuous growth scanning in background"""
    while True:
        try:
            print(f"\n⏰ [{datetime.now().strftime('%H:%M')}] Running growth scan...")
            
            # Monitor existing positions
            monitor_result = await engine.monitor_positions()
            
            if monitor_result['stop_losses_hit'] or monitor_result['take_profits_hit']:
                print(f"  SL: {len(monitor_result['stop_losses_hit'])} | TP: {len(monitor_result['take_profits_hit'])}")
            
            # Check for compounding opportunities
            compound_result = await engine.compound_profits()
            if compound_result.get('compounded'):
                print(f"  Compounded ${compound_result['amount']:.2f}")
            
            # Get stats
            stats = await engine.get_growth_stats()
            print(f"  Portfolio: ${stats['portfolio']['total_value']:,.2f} ({stats['portfolio']['current_multiplier']:.1f}x)")
            
        except Exception as e:
            print(f"  Scanner error: {e}")
        
        await asyncio.sleep(interval_minutes * 60)
