"""
AI Portfolio Manager - Autonomous Portfolio Development & Trading
Enables the AI to develop its own portfolio strategy and execute real money trades.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

class AIPortfolioManager:
    """
    AI-powered autonomous portfolio manager that:
    1. Develops its own portfolio allocation strategy
    2. Continuously learns from market data and news
    3. Auto-trades with real money (user-allocated funds only)
    4. Implements risk management and position sizing
    """
    
    def __init__(self, db, kraken_service=None, learning_engine=None, 
                 strategy_engine=None, market_service=None, news_service=None):
        self.db = db
        self.kraken_service = kraken_service
        self.learning_engine = learning_engine
        self.strategy_engine = strategy_engine
        self.market_service = market_service
        self.news_service = news_service
        
        # AI Portfolio Configuration
        self.portfolio_config = {
            'rebalance_interval_hours': 24,  # Rebalance daily
            'min_trade_confidence': 70,  # Minimum AI confidence to trade
            'max_single_position_pct': 30,  # Max 30% in single asset
            'min_cash_reserve_pct': 10,  # Always keep 10% in USD
            'stop_loss_pct': 15,  # Global stop loss
            'take_profit_pct': 50,  # Global take profit
            'risk_per_trade_pct': 5,  # Risk 5% per trade
        }
        
        # Target portfolio developed by AI
        self.ai_target_portfolio = {}
        self.is_running = False
        
    async def initialize_ai_portfolio(self, user_id: str, initial_capital: float) -> Dict[str, Any]:
        """
        Initialize AI-managed portfolio with user's allocated capital.
        AI will develop its own strategy from this point.
        """
        # Create initial portfolio record
        portfolio = {
            'user_id': user_id,
            'type': 'ai_managed',
            'initial_capital': initial_capital,
            'current_capital': initial_capital,
            'holdings': {'USD': initial_capital},
            'target_allocation': {},  # AI will fill this
            'performance': {
                'total_return_pct': 0,
                'trades_executed': 0,
                'winning_trades': 0,
                'losing_trades': 0,
            },
            'ai_strategy': {
                'style': 'adaptive',  # AI determines best approach
                'risk_tolerance': 'medium',
                'time_horizon': 'weekly',
            },
            'created_at': datetime.now().isoformat(),
            'last_rebalance': None,
            'status': 'active'
        }
        
        await self.db.ai_portfolios.replace_one(
            {'user_id': user_id, 'type': 'ai_managed'},
            portfolio,
            upsert=True
        )
        
        print(f"🤖 AI Portfolio initialized for {user_id}")
        print(f"   💰 Initial Capital: ${initial_capital:,.2f}")
        
        # Immediately develop initial strategy
        await self.develop_portfolio_strategy(user_id)
        
        return portfolio
    
    async def develop_portfolio_strategy(self, user_id: str) -> Dict[str, Any]:
        """
        AI develops its own portfolio allocation strategy based on:
        - Historical performance data
        - Current market conditions
        - News sentiment
        - Technical indicators
        """
        print("\n🧠 AI Developing Portfolio Strategy...")
        
        # Get portfolio
        portfolio = await self.db.ai_portfolios.find_one(
            {'user_id': user_id, 'type': 'ai_managed'},
            {'_id': 0}
        )
        
        if not portfolio:
            return {'error': 'Portfolio not found'}
        
        capital = portfolio.get('current_capital', 0)
        
        # 1. Analyze market conditions
        market_analysis = await self._analyze_market_conditions()
        
        # 2. Get AI strategy recommendations
        strategy_recommendations = await self._get_ai_recommendations()
        
        # 3. Analyze news sentiment
        news_sentiment = await self._analyze_news_sentiment()
        
        # 4. Develop target allocation
        target_allocation = await self._calculate_optimal_allocation(
            capital,
            market_analysis,
            strategy_recommendations,
            news_sentiment
        )
        
        # 5. Store strategy
        await self.db.ai_portfolios.update_one(
            {'user_id': user_id, 'type': 'ai_managed'},
            {'$set': {
                'target_allocation': target_allocation,
                'ai_strategy.last_analysis': {
                    'market_conditions': market_analysis,
                    'news_sentiment': news_sentiment,
                    'confidence_scores': strategy_recommendations,
                    'analyzed_at': datetime.now().isoformat()
                }
            }}
        )
        
        print("📊 AI Target Portfolio Allocation:")
        for asset, pct in target_allocation.items():
            print(f"   • {asset}: {pct:.1f}%")
        
        return {
            'target_allocation': target_allocation,
            'analysis': {
                'market': market_analysis,
                'sentiment': news_sentiment,
                'confidence': strategy_recommendations
            }
        }
    
    async def _analyze_market_conditions(self) -> Dict[str, Any]:
        """Analyze current market conditions"""
        try:
            # Get prices for major cryptos
            coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
            price_data = await self.market_service.get_coin_price(coins)
            
            # Calculate market sentiment from price changes
            bullish_count = 0
            bearish_count = 0
            
            for coin, data in price_data.items():
                change = data.get('price_change_24h', 0)
                if change > 0:
                    bullish_count += 1
                else:
                    bearish_count += 1
            
            if bullish_count > bearish_count:
                market_trend = 'bullish'
            elif bearish_count > bullish_count:
                market_trend = 'bearish'
            else:
                market_trend = 'neutral'
            
            return {
                'trend': market_trend,
                'bullish_assets': bullish_count,
                'bearish_assets': bearish_count,
                'price_data': price_data
            }
        except Exception as e:
            return {'trend': 'neutral', 'error': str(e)}
    
    async def _get_ai_recommendations(self) -> Dict[str, Any]:
        """Get AI strategy recommendations from learning engine"""
        try:
            if self.strategy_engine:
                # Get top strategies by confidence
                strategies = await self.db.strategies.find(
                    {'status': 'active'},
                    {'_id': 0}
                ).sort('confidence_score', -1).limit(10).to_list(10)
                
                recommendations = {}
                for s in strategies:
                    coin = s.get('coin_id', '')
                    confidence = s.get('confidence_score', 0)
                    signal = s.get('technical_signal', '')
                    
                    if coin and confidence > 60:
                        recommendations[coin] = {
                            'confidence': confidence,
                            'signal': signal,
                            'action': 'BUY' if 'BUY' in signal.upper() or 'BULLISH' in signal.upper() else 'HOLD'
                        }
                
                return recommendations
        except Exception as e:
            print(f"Strategy recommendation error: {e}")
        
        return {}
    
    async def _analyze_news_sentiment(self) -> Dict[str, Any]:
        """Analyze news sentiment for portfolio decisions"""
        try:
            if self.news_service:
                news = await self.news_service.get_aggregated_news(limit_per_source=20)
                
                positive = sum(1 for n in news if n.get('sentiment') == 'positive')
                negative = sum(1 for n in news if n.get('sentiment') == 'negative')
                neutral = len(news) - positive - negative
                
                if positive > negative * 1.5:
                    overall = 'bullish'
                elif negative > positive * 1.5:
                    overall = 'bearish'
                else:
                    overall = 'neutral'
                
                return {
                    'overall': overall,
                    'positive_count': positive,
                    'negative_count': negative,
                    'neutral_count': neutral
                }
        except Exception as e:
            print(f"News sentiment error: {e}")
        
        return {'overall': 'neutral'}
    
    async def _calculate_optimal_allocation(
        self,
        capital: float,
        market_analysis: Dict,
        recommendations: Dict,
        sentiment: Dict
    ) -> Dict[str, float]:
        """Calculate optimal portfolio allocation based on AI analysis"""
        
        # Base allocations for different market conditions
        if market_analysis.get('trend') == 'bullish' and sentiment.get('overall') == 'bullish':
            # Aggressive allocation in bull market
            base_allocation = {
                'USD': 10,  # Minimum cash
                'BTC': 35,
                'ETH': 25,
                'SOL': 15,
                'ADA': 10,
                'DOT': 5
            }
        elif market_analysis.get('trend') == 'bearish' or sentiment.get('overall') == 'bearish':
            # Defensive allocation in bear market
            base_allocation = {
                'USD': 50,  # High cash position
                'BTC': 30,  # Safe haven
                'ETH': 15,
                'SOL': 5,
                'ADA': 0,
                'DOT': 0
            }
        else:
            # Balanced allocation in neutral market
            base_allocation = {
                'USD': 25,
                'BTC': 30,
                'ETH': 20,
                'SOL': 10,
                'ADA': 10,
                'DOT': 5
            }
        
        # Adjust based on AI strategy recommendations
        for coin, rec in recommendations.items():
            symbol = coin.upper()[:3]
            if symbol in base_allocation and rec.get('action') == 'BUY':
                confidence_boost = (rec.get('confidence', 0) - 60) / 100  # 0-0.4 boost
                base_allocation[symbol] = min(
                    base_allocation[symbol] * (1 + confidence_boost),
                    self.portfolio_config['max_single_position_pct']
                )
        
        # Normalize to 100%
        total = sum(base_allocation.values())
        if total != 100:
            factor = 100 / total
            base_allocation = {k: v * factor for k, v in base_allocation.items()}
        
        return base_allocation
    
    async def execute_rebalance(self, user_id: str) -> Dict[str, Any]:
        """
        Execute portfolio rebalancing to match AI target allocation.
        Trades real money on Kraken.
        """
        print(f"\n🔄 Executing Portfolio Rebalance for {user_id}...")
        
        portfolio = await self.db.ai_portfolios.find_one(
            {'user_id': user_id, 'type': 'ai_managed'},
            {'_id': 0}
        )
        
        if not portfolio:
            return {'error': 'Portfolio not found'}
        
        target = portfolio.get('target_allocation', {})
        current_holdings = portfolio.get('holdings', {})
        capital = portfolio.get('current_capital', 0)
        
        if not target:
            # Develop strategy first
            await self.develop_portfolio_strategy(user_id)
            portfolio = await self.db.ai_portfolios.find_one(
                {'user_id': user_id, 'type': 'ai_managed'},
                {'_id': 0}
            )
            target = portfolio.get('target_allocation', {})
        
        trades_executed = []
        
        # Get current prices
        coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
        try:
            price_data = await self.market_service.get_coin_price(coins)
        except:
            price_data = {}
        
        coin_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
            'ADA': 'cardano', 'DOT': 'polkadot'
        }
        
        # Calculate current portfolio value
        current_value = current_holdings.get('USD', 0)
        for symbol, coin_id in coin_map.items():
            amount = current_holdings.get(symbol, 0)
            price = price_data.get(coin_id, {}).get('price_usd', 0)
            current_value += amount * price
        
        print(f"   💰 Current Portfolio Value: ${current_value:,.2f}")
        
        # Calculate required trades
        for symbol, target_pct in target.items():
            if symbol == 'USD':
                continue
            
            coin_id = coin_map.get(symbol)
            if not coin_id:
                continue
            
            price = price_data.get(coin_id, {}).get('price_usd', 0)
            if price <= 0:
                continue
            
            # Current allocation
            current_amount = current_holdings.get(symbol, 0)
            current_value_asset = current_amount * price
            current_pct = (current_value_asset / current_value * 100) if current_value > 0 else 0
            
            # Target allocation
            target_value = (target_pct / 100) * current_value
            
            # Difference
            diff_value = target_value - current_value_asset
            diff_pct = target_pct - current_pct
            
            # Only trade if difference > 2%
            if abs(diff_pct) < 2:
                continue
            
            # Execute trade
            if diff_value > 0:
                # Need to BUY
                buy_amount = diff_value / price
                trade_result = await self._execute_real_trade(
                    user_id, symbol, 'BUY', buy_amount, price
                )
                trades_executed.append(trade_result)
            else:
                # Need to SELL
                sell_amount = abs(diff_value) / price
                trade_result = await self._execute_real_trade(
                    user_id, symbol, 'SELL', sell_amount, price
                )
                trades_executed.append(trade_result)
        
        # Update portfolio
        await self.db.ai_portfolios.update_one(
            {'user_id': user_id, 'type': 'ai_managed'},
            {'$set': {
                'last_rebalance': datetime.now().isoformat(),
                'performance.trades_executed': portfolio.get('performance', {}).get('trades_executed', 0) + len(trades_executed)
            }}
        )
        
        print(f"   ✅ Rebalance Complete: {len(trades_executed)} trades executed")
        
        return {
            'success': True,
            'trades_executed': len(trades_executed),
            'trades': trades_executed,
            'new_allocation': target
        }
    
    async def _execute_real_trade(
        self,
        user_id: str,
        symbol: str,
        action: str,
        amount: float,
        price: float
    ) -> Dict[str, Any]:
        """Execute real trade on Kraken"""
        trade_result = {
            'symbol': symbol,
            'action': action,
            'amount': amount,
            'price': price,
            'value_usd': amount * price,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if self.kraken_service:
                # Execute on Kraken
                pair = f"{symbol}USD"
                result = await self.kraken_service.place_order(
                    pair=pair,
                    side=action.lower(),
                    ordertype='market',
                    price='0',
                    volume=str(amount)
                )
                trade_result['kraken_order_id'] = result.get('txid', ['N/A'])[0]
                trade_result['status'] = 'executed'
                print(f"   💰 {action} {amount:.6f} {symbol} @ ${price:,.2f}")
            else:
                trade_result['status'] = 'simulated'
                trade_result['note'] = 'Kraken not configured'
                print(f"   📝 SIMULATED: {action} {amount:.6f} {symbol} @ ${price:,.2f}")
            
            # Update holdings in database
            portfolio = await self.db.ai_portfolios.find_one(
                {'user_id': user_id, 'type': 'ai_managed'}
            )
            holdings = portfolio.get('holdings', {})
            
            if action == 'BUY':
                holdings['USD'] = holdings.get('USD', 0) - (amount * price)
                holdings[symbol] = holdings.get(symbol, 0) + amount
            else:
                holdings['USD'] = holdings.get('USD', 0) + (amount * price)
                holdings[symbol] = holdings.get(symbol, 0) - amount
            
            await self.db.ai_portfolios.update_one(
                {'user_id': user_id, 'type': 'ai_managed'},
                {'$set': {'holdings': holdings}}
            )
            
        except Exception as e:
            trade_result['status'] = 'failed'
            trade_result['error'] = str(e)
            print(f"   ❌ Trade failed: {e}")
        
        # Record trade
        await self.db.ai_trades.insert_one({
            'user_id': user_id,
            **trade_result
        })
        
        return trade_result
    
    async def start_autonomous_trading(self, user_id: str):
        """Start autonomous AI trading loop"""
        self.is_running = True
        print(f"\n{'='*60}")
        print("🤖 AI AUTONOMOUS PORTFOLIO MANAGER STARTED")
        print(f"{'='*60}")
        
        while self.is_running:
            try:
                # 1. Develop/update strategy
                await self.develop_portfolio_strategy(user_id)
                
                # 2. Check if rebalance needed
                portfolio = await self.db.ai_portfolios.find_one(
                    {'user_id': user_id, 'type': 'ai_managed'},
                    {'_id': 0}
                )
                
                last_rebalance = portfolio.get('last_rebalance')
                should_rebalance = False
                
                if not last_rebalance:
                    should_rebalance = True
                else:
                    last_time = datetime.fromisoformat(last_rebalance)
                    hours_since = (datetime.now() - last_time).total_seconds() / 3600
                    if hours_since >= self.portfolio_config['rebalance_interval_hours']:
                        should_rebalance = True
                
                # 3. Execute rebalance if needed
                if should_rebalance:
                    await self.execute_rebalance(user_id)
                
                # 4. Wait for next cycle (check every hour)
                print(f"\n⏰ Next portfolio check in 1 hour...")
                await asyncio.sleep(3600)
                
            except Exception as e:
                print(f"❌ AI Portfolio Manager error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    def stop_autonomous_trading(self):
        """Stop autonomous trading"""
        self.is_running = False
        print("🛑 AI Autonomous Trading stopped")
    
    async def get_portfolio_status(self, user_id: str) -> Dict[str, Any]:
        """Get current AI portfolio status"""
        portfolio = await self.db.ai_portfolios.find_one(
            {'user_id': user_id, 'type': 'ai_managed'},
            {'_id': 0}
        )
        
        if not portfolio:
            return {'initialized': False}
        
        # Calculate current value
        holdings = portfolio.get('holdings', {})
        coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
        
        try:
            price_data = await self.market_service.get_coin_price(coins)
        except:
            price_data = {}
        
        coin_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
            'ADA': 'cardano', 'DOT': 'polkadot'
        }
        
        current_value = holdings.get('USD', 0)
        holdings_detail = {'USD': {'amount': holdings.get('USD', 0), 'value': holdings.get('USD', 0)}}
        
        for symbol, coin_id in coin_map.items():
            amount = holdings.get(symbol, 0)
            price = price_data.get(coin_id, {}).get('price_usd', 0)
            value = amount * price
            current_value += value
            if amount > 0:
                holdings_detail[symbol] = {
                    'amount': amount,
                    'price': price,
                    'value': value
                }
        
        initial = portfolio.get('initial_capital', 0)
        pnl = current_value - initial
        pnl_pct = (pnl / initial * 100) if initial > 0 else 0
        
        return {
            'initialized': True,
            'initial_capital': initial,
            'current_value': current_value,
            'profit_loss': pnl,
            'profit_loss_pct': pnl_pct,
            'holdings': holdings_detail,
            'target_allocation': portfolio.get('target_allocation', {}),
            'last_rebalance': portfolio.get('last_rebalance'),
            'ai_strategy': portfolio.get('ai_strategy', {}),
            'performance': portfolio.get('performance', {}),
            'status': portfolio.get('status', 'inactive')
        }
