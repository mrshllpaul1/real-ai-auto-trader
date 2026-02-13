import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

class SelfImprovingAI:
    """
    Self-improving AI that constantly learns from trades and market conditions
    Adjusts strategies, signal weights, and risk parameters based on performance
    """
    
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.learning_interval = 3600  # Learn every hour
        self.llm_api_key = os.getenv('EMERGENT_LLM_KEY')
        
        # Signal effectiveness weights (learned from performance)
        self.signal_weights = {
            'MACD_BULLISH': 1.0,
            'BOLLINGER_SQUEEZE': 1.0,
            'OVERSOLD_ACCUMULATION': 1.0,
            'DEEP_VALUE': 1.0,
            'TREND_REVERSAL': 1.0,
            'EXTREME_VOLUME': 1.0
        }
        
        # Performance tracking
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'total_profit_pct': 0,
            'avg_hold_time_hours': 0,
            'best_signal': None,
            'worst_signal': None
        }
    
    async def initialize(self):
        """Load learned weights from database"""
        weights = await self.db.ai_learned_weights.find_one({}, {'_id': 0})
        if weights:
            self.signal_weights = weights.get('signal_weights', self.signal_weights)
            self.performance_metrics = weights.get('performance_metrics', self.performance_metrics)
            print("✅ AI loaded learned weights from previous sessions")
        else:
            print("🆕 AI starting with default weights")
    
    async def record_trade(self, trade_data: Dict[str, Any]):
        """Record a trade for learning"""
        trade_record = {
            'trade_id': trade_data.get('trade_id'),
            'coin_id': trade_data.get('coin_id'),
            'symbol': trade_data.get('symbol'),
            'action': trade_data.get('action'),  # BUY or SELL
            'entry_price': trade_data.get('entry_price'),
            'amount': trade_data.get('amount'),
            'signals_triggered': trade_data.get('signals', []),
            'match_score': trade_data.get('match_score', 0),
            'alert_level': trade_data.get('alert_level'),
            'timestamp': datetime.now(),
            'status': 'OPEN',
            'exit_price': None,
            'profit_pct': None,
            'lessons_learned': []
        }
        
        await self.db.ai_trade_history.insert_one(trade_record)
        return trade_record
    
    async def close_trade(self, trade_id: str, exit_price: float, reason: str = 'manual'):
        """Close a trade and calculate profit"""
        trade = await self.db.ai_trade_history.find_one({'trade_id': trade_id})
        if not trade:
            return None
        
        entry_price = trade['entry_price']
        profit_pct = ((exit_price - entry_price) / entry_price) * 100
        
        hold_time = (datetime.now() - trade['timestamp']).total_seconds() / 3600
        
        await self.db.ai_trade_history.update_one(
            {'trade_id': trade_id},
            {'$set': {
                'exit_price': exit_price,
                'profit_pct': profit_pct,
                'status': 'CLOSED',
                'closed_at': datetime.now(),
                'close_reason': reason,
                'hold_time_hours': hold_time
            }}
        )
        
        # Trigger learning from this trade
        await self.learn_from_trade(trade_id)
        
        return {'profit_pct': profit_pct, 'hold_time_hours': hold_time}
    
    async def learn_from_trade(self, trade_id: str):
        """Learn from a completed trade - adjust signal weights"""
        trade = await self.db.ai_trade_history.find_one({'trade_id': trade_id}, {'_id': 0})
        if not trade or trade.get('status') != 'CLOSED':
            return
        
        profit_pct = trade.get('profit_pct', 0)
        signals = trade.get('signals_triggered', [])
        
        # Adjust signal weights based on outcome
        for signal in signals:
            signal_name = signal.get('signal') if isinstance(signal, dict) else signal
            if signal_name in self.signal_weights:
                # Positive trade increases weight, negative decreases
                adjustment = 0.01 * (profit_pct / 10)  # Small adjustments
                adjustment = max(-0.1, min(0.1, adjustment))  # Cap at ±10%
                
                self.signal_weights[signal_name] = max(0.1, min(2.0, 
                    self.signal_weights[signal_name] + adjustment
                ))
        
        # Update performance metrics
        self.performance_metrics['total_trades'] += 1
        if profit_pct > 0:
            self.performance_metrics['winning_trades'] += 1
        self.performance_metrics['total_profit_pct'] += profit_pct
        
        # Save learned weights
        await self.save_learned_weights()
        
        print(f"🧠 AI learned from trade: {profit_pct:+.2f}% | Adjusted {len(signals)} signal weights")
    
    async def save_learned_weights(self):
        """Save learned weights to database"""
        await self.db.ai_learned_weights.delete_many({})
        await self.db.ai_learned_weights.insert_one({
            'signal_weights': self.signal_weights,
            'performance_metrics': self.performance_metrics,
            'updated_at': datetime.now().isoformat()
        })
    
    async def analyze_performance(self) -> Dict[str, Any]:
        """Analyze overall AI performance and generate insights"""
        # Get all closed trades
        trades = await self.db.ai_trade_history.find(
            {'status': 'CLOSED'},
            {'_id': 0}
        ).to_list(1000)
        
        if not trades:
            return {'message': 'No completed trades to analyze'}
        
        # Calculate metrics by signal
        signal_performance = {}
        for trade in trades:
            profit = trade.get('profit_pct', 0)
            for signal in trade.get('signals_triggered', []):
                signal_name = signal.get('signal') if isinstance(signal, dict) else signal
                if signal_name not in signal_performance:
                    signal_performance[signal_name] = {'trades': 0, 'wins': 0, 'total_profit': 0}
                signal_performance[signal_name]['trades'] += 1
                signal_performance[signal_name]['total_profit'] += profit
                if profit > 0:
                    signal_performance[signal_name]['wins'] += 1
        
        # Calculate win rates
        for signal, stats in signal_performance.items():
            stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            stats['avg_profit'] = stats['total_profit'] / stats['trades'] if stats['trades'] > 0 else 0
        
        # Find best and worst signals
        sorted_signals = sorted(signal_performance.items(), key=lambda x: x[1]['avg_profit'], reverse=True)
        
        return {
            'total_trades': len(trades),
            'winning_trades': sum(1 for t in trades if t.get('profit_pct', 0) > 0),
            'win_rate': sum(1 for t in trades if t.get('profit_pct', 0) > 0) / len(trades) * 100,
            'total_profit': sum(t.get('profit_pct', 0) for t in trades),
            'avg_profit_per_trade': sum(t.get('profit_pct', 0) for t in trades) / len(trades),
            'signal_performance': signal_performance,
            'best_signal': sorted_signals[0] if sorted_signals else None,
            'worst_signal': sorted_signals[-1] if sorted_signals else None,
            'current_weights': self.signal_weights,
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def generate_ai_insights(self) -> Dict[str, Any]:
        """Use LLM to generate strategic insights from performance data"""
        try:
            if not self.llm_api_key:
                return {'insights': 'AI insights unavailable - no API key'}
            
            performance = await self.analyze_performance()
            
            chat = LlmChat(
                api_key=self.llm_api_key,
                session_id=f"ai_insights_{datetime.now().timestamp()}",
                system_message="You are an expert crypto trading AI analyst. Analyze performance data and provide actionable insights for improving trading strategies."
            ).with_model("openai", "gpt-5.2")
            
            prompt = f"""
Analyze my crypto trading AI's performance:

OVERALL STATS:
- Total Trades: {performance.get('total_trades', 0)}
- Win Rate: {performance.get('win_rate', 0):.1f}%
- Total Profit: {performance.get('total_profit', 0):.2f}%
- Avg Profit/Trade: {performance.get('avg_profit_per_trade', 0):.2f}%

SIGNAL PERFORMANCE:
{performance.get('signal_performance', {})}

CURRENT SIGNAL WEIGHTS:
{self.signal_weights}

Provide:
1. What's working well?
2. What needs improvement?
3. Specific adjustments to signal weights
4. Risk management suggestions
5. New patterns to look for

Be concise and actionable.
"""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Store insights
            await self.db.ai_insights.insert_one({
                'insights': response,
                'performance_snapshot': performance,
                'generated_at': datetime.now()
            })
            
            return {
                'insights': response,
                'performance': performance,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def optimize_strategy(self):
        """Automatically optimize strategy based on performance"""
        performance = await self.analyze_performance()
        
        if performance.get('total_trades', 0) < 5:
            return {'message': 'Need more trades for optimization'}
        
        optimizations = []
        
        # Boost winning signals
        signal_perf = performance.get('signal_performance', {})
        for signal, stats in signal_perf.items():
            if stats['win_rate'] > 70 and stats['trades'] >= 3:
                old_weight = self.signal_weights.get(signal, 1.0)
                self.signal_weights[signal] = min(2.0, old_weight * 1.1)
                optimizations.append(f"Boosted {signal} weight to {self.signal_weights[signal]:.2f}")
            elif stats['win_rate'] < 40 and stats['trades'] >= 3:
                old_weight = self.signal_weights.get(signal, 1.0)
                self.signal_weights[signal] = max(0.3, old_weight * 0.9)
                optimizations.append(f"Reduced {signal} weight to {self.signal_weights[signal]:.2f}")
        
        await self.save_learned_weights()
        
        return {
            'optimizations_made': optimizations,
            'new_weights': self.signal_weights,
            'optimized_at': datetime.now().isoformat()
        }
    
    async def continuous_learning_loop(self):
        """Background loop for continuous self-improvement"""
        self.is_running = True
        print("🧠 AI continuous learning started")
        
        while self.is_running:
            try:
                # Analyze and optimize every hour
                await self.optimize_strategy()
                
                # Generate insights every 4 hours
                if datetime.now().hour % 4 == 0:
                    await self.generate_ai_insights()
                
                await asyncio.sleep(self.learning_interval)
            except Exception as e:
                print(f"Learning loop error: {e}")
                await asyncio.sleep(300)
    
    def stop_learning(self):
        """Stop the learning loop"""
        self.is_running = False
        print("🛑 AI learning stopped")
    
    def get_adjusted_score(self, base_score: int, signals: List[Dict]) -> int:
        """Get score adjusted by learned signal weights"""
        if not signals:
            return base_score
        
        total_weight = 0
        for signal in signals:
            signal_name = signal.get('signal') if isinstance(signal, dict) else signal
            weight = self.signal_weights.get(signal_name, 1.0)
            total_weight += weight
        
        avg_weight = total_weight / len(signals) if signals else 1.0
        adjusted_score = int(base_score * avg_weight)
        
        return min(100, adjusted_score)
    
    async def get_learning_status(self) -> Dict[str, Any]:
        """Get current AI learning status"""
        return {
            'is_learning': self.is_running,
            'signal_weights': self.signal_weights,
            'performance_metrics': self.performance_metrics,
            'last_optimization': await self.db.ai_learned_weights.find_one({}, {'_id': 0, 'updated_at': 1})
        }
