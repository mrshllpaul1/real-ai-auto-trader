import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
from services.kraken_service import KrakenAuthenticator, KrakenTradeService
from services.trading_engine import TradingEngine
from services.strategy_engine import StrategyEngine
from services.market_data_service import MarketDataService
from services.risk_manager import RiskManager
from services.learning_engine import AILearningEngine
from services.news_service import CryptoNewsAggregator
from services.historical_trainer import HistoricalTrainer
from dotenv import load_dotenv

load_dotenv()

class AutoTradingScheduler:
    """
    Automated trading scheduler that runs continuously in the background.
    Executes both paper and real trades simultaneously based on AI strategies.
    """
    
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.strategy_engine = StrategyEngine()
        self.market_service = MarketDataService()
        self.news_service = CryptoNewsAggregator()
        self.historical_trainer = HistoricalTrainer(db)
        self.learning_engine = AILearningEngine(db)
        self.risk_manager = RiskManager(db)
        self.trading_engine = TradingEngine(db)
        
        # Portfolio allocation manager for isolated trading
        from services.portfolio_allocation_manager import PortfolioAllocationManager
        self.allocation_manager = PortfolioAllocationManager(db)
        
        # Initialize Kraken for real trading
        self.kraken_api_key = os.getenv('KRAKEN_API_KEY')
        self.kraken_api_secret = os.getenv('KRAKEN_API_SECRET')
        
        if self.kraken_api_key and self.kraken_api_secret:
            self.kraken_auth = KrakenAuthenticator(self.kraken_api_key, self.kraken_api_secret)
            self.kraken_trade = KrakenTradeService(self.kraken_auth)
            self.real_trading_enabled = True
        else:
            self.real_trading_enabled = False
        
        print(f"🤖 Auto Trading Scheduler initialized")
        print(f"💰 Portfolio Isolation: ENABLED ✓")
        print(f"📊 Real Trading: {'ENABLED ✓' if self.real_trading_enabled else 'DISABLED (Configure Kraken API keys)'}")
    
    async def start(self):
        """Start the auto-trading scheduler"""
        if self.is_running:
            print("⚠️ Auto-trading is already running")
            return
        
        self.is_running = True
        print("🚀 Starting auto-trading scheduler...")
        print("🔄 Running in background mode")
        print("📱 Mobile-compatible with keep-alive")
        
        # Start background tasks
        await asyncio.gather(
            self.strategy_execution_loop(),
            self.monitoring_loop(),
            self.learning_update_loop()
        )
    
    async def stop(self):
        """Stop the auto-trading scheduler"""
        self.is_running = False
        print("🛑 Auto-trading scheduler stopped")
    
    async def strategy_execution_loop(self):
        """Main loop for executing trading strategies"""
        while self.is_running:
            try:
                print(f"\n{'='*60}")
                print(f"🔄 Auto-Trading Cycle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                # Get active users with auto-trading enabled
                auto_trade_configs = await self.db.auto_trade_config.find(
                    {'enabled': True}
                ).to_list(100)
                
                if not auto_trade_configs:
                    print("⚠️ No active auto-trading configurations found")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                for config in auto_trade_configs:
                    await self.execute_user_strategies(config)
                
                # Wait for next cycle (configurable, default 15 minutes)
                wait_time = 900  # 15 minutes
                print(f"\n⏰ Next cycle in {wait_time//60} minutes...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                print(f"❌ Error in strategy execution loop: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def execute_user_strategies(self, config: Dict[str, Any]):
        """Execute strategies for a specific user"""
        user_id = config['user_id']
        print(f"\n👤 Processing strategies for user: {user_id}")
        
        # Get user's active strategies
        strategies = await self.db.strategies.find(
            {'user_id': user_id, 'status': 'active'}
        ).sort('confidence_score', -1).limit(3).to_list(3)
        
        if not strategies:
            print(f"  ⚠️ No active strategies found")
            return
        
        print(f"  📊 Found {len(strategies)} active strategies")
        
        for strategy in strategies:
            await self.execute_strategy(user_id, strategy, config)
    
    async def execute_strategy(
        self,
        user_id: str,
        strategy: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """Execute a single strategy in both paper and real modes with allocation protection"""
        coin_id = strategy['coin_id']
        signal = strategy['technical_signal']
        confidence = strategy['confidence_score']
        
        print(f"\n  💎 {coin_id.upper()}: {signal} (Confidence: {confidence:.1f}%)")
        
        # Check if confidence meets threshold
        min_confidence = config.get('min_confidence', 70)
        if confidence < min_confidence:
            print(f"    ⏭️ Skipped: Confidence {confidence:.1f}% < {min_confidence}%")
            return
        
        # Get current price
        try:
            price_data = await self.market_service.get_coin_price([coin_id])
            current_price = price_data.get(coin_id, {}).get('price_usd', 0)
            
            if not current_price:
                print(f"    ❌ Could not fetch current price")
                return
            
            # Calculate trade amount
            trade_amount = config.get('amount_per_trade', 100)  # USD
            
            # Execute PAPER trade
            if config.get('paper_trading_enabled', True):
                paper_result = await self.trading_engine.execute_trade(
                    user_id=user_id,
                    strategy_id=strategy['strategy_id'],
                    coin_pair=f"{coin_id.upper()}/USD",
                    action=signal,
                    amount=trade_amount,
                    price=current_price,
                    mode='paper'
                )
                
                if paper_result.get('status') == 'executed':
                    print(f"    ✅ Paper Trade: {signal} ${trade_amount} @ ${current_price:.2f}")
                else:
                    print(f"    ❌ Paper Trade Failed: {paper_result.get('error', 'Unknown')}")
            
            # Execute REAL trade with ALLOCATION PROTECTION
            if config.get('real_trading_enabled', False) and self.real_trading_enabled:
                # CRITICAL: Validate against allocated funds
                asset_symbol = coin_id.upper()[:3]  # BTC, ETH, SOL
                
                allocation_check = await self.allocation_manager.validate_trade_allocation(
                    user_id,
                    asset_symbol if signal == 'SELL' else 'USD',
                    trade_amount,
                    signal.lower()
                )
                
                if not allocation_check.get('valid'):
                    print(f"    🛡️ ALLOCATION PROTECTION: {allocation_check.get('reason')}")
                    print(f"    ℹ️  Bot can only trade with allocated funds")
                    return
                
                # Additional risk validation for real trades
                risk_check = await self.risk_manager.validate_trade(
                    user_id,
                    trade_amount,
                    f"{coin_id.upper()}/USD"
                )
                
                if not risk_check.get('valid'):
                    print(f"    ⚠️ Real Trade Blocked: {risk_check.get('reason')}")
                else:
                    real_result = await self.trading_engine.execute_trade(
                        user_id=user_id,
                        strategy_id=strategy['strategy_id'],
                        coin_pair=f"{coin_id.upper()}USD",  # Kraken format
                        action=signal,
                        amount=trade_amount / current_price,  # Convert to coin amount
                        price=current_price,
                        mode='real'
                    )
                    
                    if real_result.get('status') == 'executed':
                        print(f"    💰 REAL Trade: {signal} ${trade_amount} @ ${current_price:.2f}")
                        print(f"    🛡️ Using ALLOCATED funds only (Other Kraken assets untouched)")
                        
                        # Record in bot portfolio
                        await self.allocation_manager.record_trade(
                            user_id,
                            {
                                'asset': asset_symbol,
                                'action': signal,
                                'amount': trade_amount,
                                'price': current_price,
                                'trade_id': real_result.get('trade_id')
                            }
                        )
                        
                        # Record for learning
                        await self.learning_engine.record_strategy_outcome(
                            strategy_id=strategy['strategy_id'],
                            predicted_action=signal,
                            actual_outcome=signal,
                            profit_loss=0,  # Will be calculated later
                            confidence_score=confidence
                        )
                    else:
                        print(f"    ❌ REAL Trade Failed: {real_result.get('error', 'Unknown')}")
        
        except Exception as e:
            print(f"    ❌ Error executing strategy: {str(e)}")
    
    async def monitoring_loop(self):
        """Monitor open positions and execute stop-loss/take-profit"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Get all open trades
                open_trades = await self.db.trades.find(
                    {'status': 'executed'}
                ).to_list(1000)
                
                for trade in open_trades:
                    await self.monitor_trade(trade)
                
            except Exception as e:
                print(f"⚠️ Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def monitor_trade(self, trade: Dict[str, Any]):
        """Monitor a single trade for stop-loss/take-profit"""
        try:
            coin_pair = trade['coin_pair']
            coin_id = coin_pair.split('/')[0].lower()
            entry_price = trade['price']
            action = trade['action']
            user_id = trade['user_id']
            
            # Get current price
            price_data = await self.market_service.get_coin_price([coin_id])
            current_price = price_data.get(coin_id, {}).get('price_usd', 0)
            
            if not current_price:
                return
            
            # Get risk settings
            risk_settings = await self.risk_manager.get_risk_settings(user_id)
            stop_loss_pct = risk_settings.get('stop_loss_percentage', 5)
            take_profit_pct = risk_settings.get('take_profit_percentage', 15)
            
            # Calculate P/L percentage
            if action == 'BUY':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:  # SELL
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Check stop-loss
            if pnl_pct <= -stop_loss_pct:
                print(f"🛑 Stop-Loss triggered for {coin_id.upper()}: {pnl_pct:.2f}%")
                await self.close_position(trade, current_price, 'stop_loss')
            
            # Check take-profit
            elif pnl_pct >= take_profit_pct:
                print(f"🎯 Take-Profit triggered for {coin_id.upper()}: {pnl_pct:.2f}%")
                await self.close_position(trade, current_price, 'take_profit')
        
        except Exception as e:
            print(f"⚠️ Error monitoring trade: {str(e)}")
    
    async def close_position(
        self,
        trade: Dict[str, Any],
        exit_price: float,
        reason: str
    ):
        """Close an open position"""
        # Mark trade as closed
        await self.db.trades.update_one(
            {'trade_id': trade['trade_id']},
            {'$set': {
                'status': 'closed',
                'exit_price': exit_price,
                'close_reason': reason,
                'closed_at': datetime.now().isoformat()
            }}
        )
        
        # Calculate final P/L
        entry_price = trade['price']
        action = trade['action']
        amount = trade['amount']
        
        if action == 'BUY':
            profit_loss = (exit_price - entry_price) * amount
        else:
            profit_loss = (entry_price - exit_price) * amount
        
        print(f"  💵 P/L: ${profit_loss:+.2f}")
    
    async def learning_update_loop(self):
        """Periodic learning updates"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                print("\n🧠 Running learning update...")
                await self.learning_engine.continuous_learning_update()
                print("✅ Learning update complete\n")
                
            except Exception as e:
                print(f"⚠️ Error in learning loop: {str(e)}")
                await asyncio.sleep(3600)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current auto-trading status"""
        return {
            'running': self.is_running,
            'real_trading_enabled': self.real_trading_enabled,
            'timestamp': datetime.now().isoformat()
        }
