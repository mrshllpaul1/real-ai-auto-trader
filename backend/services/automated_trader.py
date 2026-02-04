"""
Automated Weekly Trading Executor
Connects AI coin selection + gem finder to live Kraken trading.
Executes trades automatically based on AI recommendations.
Now integrated with Adaptive Strategy Engine, ML Regime Prediction, and Budget Isolation.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class AutomatedWeeklyTrader:
    """
    Automated trading system that:
    1. Uses trained AI to select 10 coins + 1 gem weekly
    2. Executes trades on Kraken ONLY within isolated budget
    3. Manages positions with stop-loss/take-profit
    4. Sends alerts on significant events
    5. Adapts strategy based on market regime (via Adaptive Strategy Engine)
    6. Uses ML/DL models to predict market regimes
    7. BUDGET ISOLATION: Only trades with allocated funds, never touches main portfolio
    8. ENHANCED AI: Uses ensemble voting, multi-timeframe, sentiment, and dynamic risk
    9. GEM ML/DL: Uses advanced ML/DL models for gem prediction
    10. PREDICTION ENHANCEMENTS: 8 advanced prediction signals integrated
    """
    
    def __init__(self, db, kraken_service, ai_trainer, gem_finder, alert_service=None, 
                 adaptive_strategy=None, regime_predictor=None, performance_tracker=None,
                 isolated_portfolio=None, enhanced_ai=None, gem_ml_dl_predictor=None,
                 background_task_manager=None, prediction_services=None):
        self.db = db
        self.kraken = kraken_service
        self.ai_trainer = ai_trainer
        self.gem_finder = gem_finder  # Legacy gem finder
        self.alert_service = alert_service
        self.adaptive_strategy = adaptive_strategy
        self.regime_predictor = regime_predictor  # ML/DL regime prediction
        self.performance_tracker = performance_tracker  # Performance tracking
        self.isolated_portfolio = isolated_portfolio  # Budget isolation manager
        self.enhanced_ai = enhanced_ai  # Enhanced AI engine
        self.gem_ml_dl = gem_ml_dl_predictor  # Advanced ML/DL gem predictor (P1)
        self.task_manager = background_task_manager  # Background task manager (P2)
        self.custom_strategies = []  # Active custom strategies
        self.notification_service = None  # Push notifications
        
        # Prediction Enhancement Services (8 services)
        self.prediction_services = prediction_services or {}
        
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
    
    async def get_portfolio_balance(self, use_isolated: bool = True) -> Dict[str, Any]:
        """
        Get available trading balance.
        
        BUDGET ISOLATION: By default, returns ONLY the isolated AI trading budget.
        The AI trader never has direct access to the main Kraken portfolio.
        
        Args:
            use_isolated: If True (default), use isolated budget. If False, use Kraken directly (paper trade only).
            
        Returns:
            Dict with balance info and isolation status
        """
        if use_isolated and self.isolated_portfolio:
            try:
                budget_status = await self.isolated_portfolio.get_budget_status()
                
                if not budget_status.get('allocated'):
                    logger.warning("⚠️ No budget allocated for AI trading. AI trading is disabled.")
                    return {
                        'balance': 0,
                        'isolated': True,
                        'allocated': False,
                        'real_trading_enabled': False,
                        'message': 'No budget allocated. Please set a trading budget first.'
                    }
                
                return {
                    'balance': budget_status.get('cash_available', 0),
                    'isolated': True,
                    'allocated': True,
                    'real_trading_enabled': budget_status.get('real_trading_enabled', False),
                    'total_value': budget_status.get('current_value', 0),
                    'positions_value': budget_status.get('positions_value', 0),
                    'initial_budget': budget_status.get('initial_budget', 0),
                    'total_pnl': budget_status.get('total_pnl', 0)
                }
            except Exception as e:
                logger.error(f"Error getting isolated budget: {e}")
                return {
                    'balance': 0,
                    'isolated': True,
                    'allocated': False,
                    'error': str(e)
                }
        
        # Fallback to Kraken balance (paper trade only)
        try:
            balance = await self.kraken.get_balance()
            usd_balance = float(balance.get('ZUSD', 0))
            return {
                'balance': usd_balance,
                'isolated': False,
                'allocated': True,
                'real_trading_enabled': False,  # Direct Kraken access is paper-only
                'message': 'Using Kraken balance directly (paper trade only)'
            }
        except Exception as e:
            logger.error(f"Error getting Kraken balance: {e}")
            return {'balance': 0, 'isolated': False, 'error': str(e)}
    
    async def get_adaptive_params(self) -> Dict[str, Any]:
        """
        Get current adaptive strategy parameters.
        Uses ML/DL regime prediction if available, falls back to adaptive strategy.
        """
        regime = 'unknown'
        ml_prediction = None
        
        # Try ML/DL regime prediction first (more accurate)
        if self.regime_predictor:
            try:
                ml_prediction = await self.regime_predictor.predict_regime('BTC')
                if ml_prediction and 'predicted_regime' in ml_prediction:
                    regime = ml_prediction['predicted_regime']
                    print(f"  🤖 ML Regime Prediction: {regime} ({ml_prediction.get('confidence', 0):.1f}% confidence)")
                    print(f"     Model: {ml_prediction.get('model_used')} ({ml_prediction.get('model_accuracy', 0):.1f}% accuracy)")
            except Exception as e:
                print(f"  ⚠️ ML prediction error: {e}")
        
        # Use adaptive strategy with ML-detected regime
        if self.adaptive_strategy:
            try:
                # If ML prediction available, use it to inform adaptive strategy
                if regime != 'unknown':
                    # Map regime to adaptive strategy format
                    from services.adaptive_strategy import MarketRegime
                    regime_map = {
                        'strong_bull': MarketRegime.STRONG_BULL,
                        'bull': MarketRegime.BULL,
                        'sideways': MarketRegime.SIDEWAYS,
                        'bear': MarketRegime.BEAR,
                        'strong_bear': MarketRegime.STRONG_BEAR,
                        'high_volatility': MarketRegime.HIGH_VOLATILITY,
                        'accumulation': MarketRegime.ACCUMULATION
                    }
                    detected_regime = regime_map.get(regime)
                    if detected_regime:
                        self.adaptive_strategy.current_regime = detected_regime
                
                result = await self.adaptive_strategy.adapt_strategy()
                
                return {
                    'regime': regime if regime != 'unknown' else result.get('regime', 'sideways'),
                    'max_position_pct': result['adapted_params'].get('max_position_pct', self.config['main_position_pct']),
                    'stop_loss': result['adapted_params'].get('stop_loss_pct', self.config['stop_loss_main']),
                    'take_profit': result['adapted_params'].get('take_profit_pct', self.config['take_profit_main']),
                    'min_confidence': result['adapted_params'].get('min_confidence', 60),
                    'max_exposure': result['adapted_params'].get('max_total_exposure', 90),
                    'preferred_assets': result.get('preferred_assets', []),
                    'is_adaptive': True,
                    'ml_prediction': ml_prediction
                }
            except Exception as e:
                print(f"  ⚠️ Adaptive strategy error: {e}, using base config")
        
        # Fallback to base config
        return {
            'regime': regime if regime != 'unknown' else 'sideways',
            'max_position_pct': self.config['main_position_pct'],
            'stop_loss': self.config['stop_loss_main'],
            'take_profit': self.config['take_profit_main'],
            'min_confidence': 60,
            'max_exposure': 90,
            'preferred_assets': [],
            'is_adaptive': False,
            'ml_prediction': ml_prediction
        }
    
    async def _find_best_gem(self, paper_trade: bool = True) -> Optional[Dict]:
        """
        Find the best gem using ML/DL predictor (P1 integration).
        Falls back to legacy gem finder if ML/DL predictor is unavailable.
        
        Returns:
            Best gem candidate with coin_id, total_score, and prediction details
        """
        # Try ML/DL gem predictor first (more advanced)
        if self.gem_ml_dl and self.gem_ml_dl.is_trained:
            try:
                logger.info("  🔮 Using ML/DL Gem Predictor...")
                
                # Scan for gems using ML/DL models
                gem_candidates = await self.gem_ml_dl.scan_for_gems()
                
                if gem_candidates:
                    # Filter to only tradeable gems (have Kraken symbol)
                    tradeable_gems = [
                        g for g in gem_candidates 
                        if g['symbol'].lower() in self.kraken_symbols or g['coin_id'].lower() in self.kraken_symbols
                    ]
                    
                    # Filter to high-potential gems
                    high_potential = [
                        g for g in tradeable_gems 
                        if g['prediction'] in ['moonshot', 'high_potential', 'likely_gem', 'potential']
                    ]
                    
                    if high_potential:
                        best_gem = high_potential[0]  # Already sorted by gem_score
                        logger.info(f"  💎 ML/DL Gem: {best_gem['symbol']} ({best_gem['prediction']}, score: {best_gem['gem_score']})")
                        
                        return {
                            'coin_id': best_gem['coin_id'].lower(),
                            'symbol': best_gem['symbol'],
                            'total_score': best_gem['gem_score'],
                            'prediction': best_gem['prediction'],
                            'confidence': best_gem['confidence'],
                            'ml_vote': best_gem.get('ml_vote'),
                            'dl_vote': best_gem.get('dl_vote'),
                            'source': 'ml_dl_predictor'
                        }
                    else:
                        logger.info("  📊 No high-potential gems found by ML/DL predictor")
                        
            except Exception as e:
                logger.warning(f"  ⚠️ ML/DL gem prediction failed: {e}, falling back to legacy")
        
        # Fallback to legacy gem finder
        try:
            logger.info("  🔍 Using legacy gem finder...")
            gems = await self.gem_finder.find_gems(datetime.now(), max_gems=1)
            if gems:
                gem = gems[0]
                gem['source'] = 'legacy_gem_finder'
                logger.info(f"  💎 Legacy Gem: {gem.get('coin_id', 'unknown')} (score: {gem.get('total_score', 0)})")
                return gem
        except Exception as e:
            logger.warning(f"  ⚠️ Legacy gem finder failed: {e}")
        
        return None
    
    async def execute_weekly_rebalance(self, paper_trade: bool = True) -> Dict[str, Any]:
        """
        Execute weekly portfolio rebalance based on AI selection.
        NOW WITH ADAPTIVE STRATEGY: Automatically adjusts position sizes,
        stop-losses, and take-profits based on current market regime.
        
        BUDGET ISOLATION: All trades use ONLY the isolated AI trading budget.
        Your main Kraken portfolio is NEVER touched.
        
        Args:
            paper_trade: If True, simulate trades. If False, execute real trades.
            
        Returns:
            Execution results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 AUTOMATED WEEKLY REBALANCE - {'PAPER' if paper_trade else 'REAL'}")
        logger.info(f"{'='*60}")
        logger.info(f"Time: {datetime.now().isoformat()}")
        
        # Get adaptive strategy parameters
        adaptive_params = await self.get_adaptive_params()
        regime = adaptive_params['regime']
        is_adaptive = adaptive_params['is_adaptive']
        
        logger.info(f"📊 Market Regime: {regime.upper()}" + (" (Adaptive)" if is_adaptive else " (Base)"))
        logger.info(f"   Position Size: {adaptive_params['max_position_pct']:.1f}%")
        logger.info(f"   Stop Loss: {adaptive_params['stop_loss']:.1f}%")
        logger.info(f"   Take Profit: {adaptive_params['take_profit']:.1f}%")
        logger.info(f"   Min Confidence: {adaptive_params['min_confidence']:.0f}%")
        
        # Get available balance from ISOLATED PORTFOLIO
        balance_info = await self.get_portfolio_balance(use_isolated=True)
        
        # Check if budget is allocated
        if not balance_info.get('allocated'):
            return {
                'success': False, 
                'error': 'No trading budget allocated. Please set a budget using /api/isolated-portfolio/set-budget',
                'isolation_status': 'NO_BUDGET'
            }
        
        # For real trading, verify budget isolation is enabled
        if not paper_trade:
            if not balance_info.get('real_trading_enabled'):
                return {
                    'success': False,
                    'error': 'Real trading is disabled. Enable it when setting budget.',
                    'isolation_status': 'REAL_TRADING_DISABLED'
                }
            
            balance = balance_info['balance']
            if balance < 100:
                return {
                    'success': False, 
                    'error': f'Insufficient isolated budget: ${balance:.2f}. Need at least $100.',
                    'balance': balance,
                    'isolation_status': 'INSUFFICIENT_BUDGET'
                }
        else:
            # Paper trade uses either isolated budget or simulated $10k
            balance = balance_info['balance'] if balance_info.get('allocated') else 10000
        
        logger.info(f"\n💰 Budget Status (ISOLATED):")
        logger.info(f"   Available Balance: ${balance:,.2f}")
        logger.info(f"   Real Trading: {balance_info.get('real_trading_enabled', False)}")
        if balance_info.get('total_pnl') is not None:
            logger.info(f"   Total P&L: ${balance_info.get('total_pnl', 0):,.2f}")
        
        # Apply max exposure limit from adaptive strategy
        max_deployable = balance * (adaptive_params['max_exposure'] / 100)
        logger.info(f"   Max Deployable ({adaptive_params['max_exposure']:.0f}%): ${max_deployable:,.2f}")
        
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
                logger.info(f"   Filtered out {original_count - len(portfolio['main_coins'])} coins below {min_conf}% confidence")
        
        # Get gem using ML/DL predictor (P1) if available, fallback to legacy
        gem = await self._find_best_gem(paper_trade)
        
        logger.info(f"\nSelected {len(portfolio['main_coins'])} main coins + {1 if gem else 0} gem")
        
        # Calculate position sizes using adaptive parameters
        # Distribute evenly across selected coins, respecting max exposure
        num_positions = len(portfolio['main_coins']) + (1 if gem else 0)
        position_pct = min(adaptive_params['max_position_pct'], adaptive_params['max_exposure'] / num_positions) if num_positions > 0 else 0
        
        main_position_size = balance * (position_pct / 100)
        gem_position_size = balance * (min(adaptive_params['max_position_pct'] * 1.1, 15) / 100)  # Gem gets slightly more
        
        logger.info(f"Position Size per Coin: ${main_position_size:.2f} ({position_pct:.1f}%)")
        
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
                logger.warning(f"  ⚠️ {coin_id}: No Kraken symbol")
                continue
            
            trade_result = await self._execute_isolated_trade(
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
            kraken_symbol = self.kraken_symbols.get(gem['coin_id'])
            
            if kraken_symbol:
                gem_trade = await self._execute_isolated_trade(
                    coin_id=gem['coin_id'],
                    symbol=kraken_symbol,
                    amount_usd=gem_position_size,
                    stop_loss_pct=gem_stop_loss,  # Adaptive gem stop loss
                    take_profit_pct=gem_take_profit,  # Adaptive gem take profit
                    paper_trade=paper_trade,
                    is_gem=True,
                    ai_score=gem['total_score']
                )
                
                if gem_trade:
                    gem_trade['regime'] = regime
                    gem_trade['adaptive_params'] = adaptive_params
                    trades.append(gem_trade)
        
        # Store execution record
        execution = {
            'timestamp': datetime.now().isoformat(),
            'paper_trade': paper_trade,
            'balance': balance,
            'regime': regime,
            'adaptive_params': adaptive_params,
            'trades': trades,
            'total_trades': len(trades),
            'main_coins': len([t for t in trades if not t.get('is_gem')]),
            'gems': len([t for t in trades if t.get('is_gem')]),
            'total_invested': sum(t.get('amount_usd', 0) for t in trades),
            'budget_isolated': True,
            'initial_budget': balance_info.get('initial_budget', 0)
        }
        
        # Store execution record (exclude _id from response)
        execution_doc = dict(execution)
        await self.db.weekly_executions.insert_one(execution_doc)
        
        # Remove _id for response
        execution.pop('_id', None)
        
        # Send alert
        if self.alert_service and not paper_trade:
            await self._send_execution_alert(execution)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Executed {len(trades)} trades")
        logger.info(f"Total Invested: ${execution['total_invested']:,.2f}")
        logger.info(f"Budget Isolation: ACTIVE ✓")
        logger.info(f"{'='*60}\n")
        
        return {
            'success': True,
            'execution': execution,
            'isolation_status': 'ACTIVE'
        }
    
    async def _execute_isolated_trade(
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
        """
        Execute a single trade using the ISOLATED PORTFOLIO.
        This ensures trades ONLY use allocated AI budget, never the main portfolio.
        """
        try:
            # Get current price
            ticker = await self.kraken.get_ticker(symbol)
            if not ticker:
                logger.warning(f"  ❌ {coin_id}: Failed to get price")
                return None
            
            current_price = float(ticker.get('c', [0])[0])
            if current_price <= 0:
                return None
            
            # Calculate quantity
            quantity = amount_usd / current_price
            
            # Calculate stop/take profit prices
            stop_price = current_price * (1 - stop_loss_pct / 100)
            take_profit_price = current_price * (1 + take_profit_pct / 100)
            
            # For real trades, use isolated portfolio
            if not paper_trade and self.isolated_portfolio:
                # Check if trade is allowed within budget
                can_trade = await self.isolated_portfolio.can_trade(amount_usd)
                
                if not can_trade.get('allowed'):
                    logger.warning(f"  ⚠️ {coin_id}: Budget constraint - {can_trade.get('reason')}")
                    return {
                        'coin_id': coin_id,
                        'symbol': symbol,
                        'status': 'BUDGET_EXCEEDED',
                        'reason': can_trade.get('reason'),
                        'available': can_trade.get('available', 0)
                    }
                
                # Execute real trade on Kraken
                order = await self.kraken.create_order(
                    symbol=symbol,
                    side='buy',
                    order_type='market',
                    volume=quantity
                )
                
                if order:
                    order_id = order.get('txid', [''])[0]
                    
                    # Record position in isolated portfolio
                    position_result = await self.isolated_portfolio.open_position(
                        coin_id=coin_id,
                        symbol=symbol,
                        amount_usd=amount_usd,
                        entry_price=current_price,
                        quantity=quantity,
                        position_type='gem' if is_gem else 'main'
                    )
                    
                    if position_result.get('success'):
                        logger.info(f"  ✅ {coin_id}: Bought ${amount_usd:.2f} @ ${current_price:.4f} (Isolated) {'💎' if is_gem else ''}")
                        return {
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
                            'paper_trade': False,
                            'status': 'FILLED',
                            'order_id': order_id,
                            'position_id': position_result['position']['position_id'],
                            'budget_isolated': True,
                            'remaining_budget': position_result.get('remaining_budget', 0),
                            'executed_at': datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"  ❌ {coin_id}: Failed to record position: {position_result.get('error')}")
                else:
                    logger.error(f"  ❌ {coin_id}: Order failed")
                    return None
            
            # Paper trade - just record the trade
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
                'paper_trade': True,
                'status': 'PAPER',
                'budget_isolated': True,
                'executed_at': datetime.now().isoformat()
            }
            
            logger.info(f"  📝 {coin_id}: Paper trade ${amount_usd:.2f} @ ${current_price:.4f} {'💎' if is_gem else ''}")
            
            # Store position (copy to avoid ObjectId issues)
            position_doc = dict(trade_record)
            await self.db.active_positions.insert_one(position_doc)
            
            return trade_record
            
        except Exception as e:
            logger.error(f"  ❌ {coin_id}: Error - {e}")
            return None
    
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
        """Close a position - updates both DB and isolated portfolio if applicable"""
        entry_price = position.get('entry_price', 0)
        pnl_pct = (exit_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
        pnl_usd = position.get('amount_usd', 0) * (pnl_pct / 100)
        
        # If this is an isolated portfolio position, close it there too
        position_id = position.get('position_id')
        if position_id and self.isolated_portfolio and position.get('budget_isolated'):
            try:
                close_result = await self.isolated_portfolio.close_position(
                    position_id=position_id,
                    exit_price=exit_price,
                    reason=reason
                )
                if close_result.get('success'):
                    logger.info(f"📉 Closed isolated position: {position.get('coin_id')} - {reason} ({pnl_pct:+.2f}%)")
            except Exception as e:
                logger.error(f"Error closing isolated position: {e}")
        
        # Update position in DB
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

    # P2: Background Task Integration Methods
    
    async def train_models_background(self) -> Dict[str, Any]:
        """
        Train AI models in background (non-blocking).
        Uses BackgroundTaskManager if available.
        
        Returns:
            task_id for tracking or direct result if no task manager
        """
        if self.task_manager:
            from services.background_tasks import TaskType
            
            async def train_all_models(progress_callback=None, **kwargs):
                results = {}
                
                # Train regime predictor
                if self.regime_predictor:
                    if progress_callback:
                        progress_callback(10, "Training regime prediction models...")
                    results['regime'] = await self.regime_predictor.train_all_models()
                
                # Train gem ML/DL models
                if self.gem_ml_dl:
                    if progress_callback:
                        progress_callback(50, "Training gem ML/DL models...")
                    results['gem_ml_dl'] = await self.gem_ml_dl.train_models()
                
                if progress_callback:
                    progress_callback(100, "All models trained")
                
                return results
            
            task_id = await self.task_manager.submit_task(
                task_type=TaskType.MODEL_TRAINING,
                task_func=train_all_models,
                task_name="train_all_ai_models",
                timeout=900  # 15 minutes
            )
            
            return {'task_id': task_id, 'status': 'submitted', 'message': 'Model training started in background'}
        
        # Fallback to synchronous training
        results = {}
        if self.regime_predictor:
            results['regime'] = await self.regime_predictor.train_all_models()
        if self.gem_ml_dl:
            results['gem_ml_dl'] = await self.gem_ml_dl.train_models()
        
        return {'status': 'completed', 'results': results}
    
    async def scan_gems_background(self, coins: List[str] = None) -> Dict[str, Any]:
        """
        Scan for gems in background (non-blocking).
        
        Args:
            coins: List of coins to scan (uses default if None)
            
        Returns:
            task_id for tracking or direct result if no task manager
        """
        if self.task_manager and self.gem_ml_dl:
            from services.background_tasks import TaskType
            
            async def scan_wrapper(progress_callback=None, **kwargs):
                if progress_callback:
                    progress_callback(20, "Scanning coins for gems...")
                
                results = await self.gem_ml_dl.scan_for_gems(coins)
                
                if progress_callback:
                    progress_callback(100, f"Scanned {len(results)} coins")
                
                return results
            
            task_id = await self.task_manager.submit_task(
                task_type=TaskType.GEM_SCAN,
                task_func=scan_wrapper,
                task_name="gem_scan",
                timeout=120
            )
            
            return {'task_id': task_id, 'status': 'submitted', 'message': 'Gem scan started in background'}
        
        # Fallback to synchronous scan
        if self.gem_ml_dl:
            results = await self.gem_ml_dl.scan_for_gems(coins)
            return {'status': 'completed', 'gems': results}
        
        return {'error': 'Gem ML/DL predictor not available'}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all integrated services"""
        return {
            'ai_trainer': self.ai_trainer is not None,
            'gem_finder_legacy': self.gem_finder is not None,
            'gem_ml_dl': self.gem_ml_dl is not None and getattr(self.gem_ml_dl, 'is_trained', False),
            'adaptive_strategy': self.adaptive_strategy is not None,
            'regime_predictor': self.regime_predictor is not None,
            'performance_tracker': self.performance_tracker is not None,
            'isolated_portfolio': self.isolated_portfolio is not None,
            'enhanced_ai': self.enhanced_ai is not None,
            'background_task_manager': self.task_manager is not None,
            'kraken_connected': self.kraken is not None,
            'custom_strategies': len(self.custom_strategies),
            'notification_service': self.notification_service is not None
        }
    
    # Custom Strategy Integration
    
    async def load_active_strategies(self):
        """Load all active custom strategies from database"""
        try:
            cursor = self.db.custom_strategies.find({'status': 'active'})
            self.custom_strategies = await cursor.to_list(length=50)
            logger.info(f"Loaded {len(self.custom_strategies)} active custom strategies")
            return len(self.custom_strategies)
        except Exception as e:
            logger.error(f"Failed to load custom strategies: {e}")
            return 0
    
    async def execute_custom_strategies(self, paper_trade: bool = True) -> Dict[str, Any]:
        """
        Execute all active custom strategies
        
        Args:
            paper_trade: If True, simulates trades without real execution
            
        Returns:
            Execution results for all strategies
        """
        if not self.custom_strategies:
            await self.load_active_strategies()
        
        if not self.custom_strategies:
            return {'message': 'No active custom strategies', 'trades': []}
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'strategies_executed': 0,
            'signals_generated': 0,
            'trades_executed': 0,
            'results': []
        }
        
        for strategy in self.custom_strategies:
            try:
                strategy_result = await self._execute_single_strategy(strategy, paper_trade)
                results['results'].append(strategy_result)
                results['strategies_executed'] += 1
                
                if strategy_result.get('signal'):
                    results['signals_generated'] += 1
                
                if strategy_result.get('trade_executed'):
                    results['trades_executed'] += 1
                    
            except Exception as e:
                logger.error(f"Strategy {strategy.get('name')} execution failed: {e}")
                results['results'].append({
                    'strategy_name': strategy.get('name'),
                    'error': str(e)
                })
        
        return results
    
    async def _execute_single_strategy(self, strategy: Dict, paper_trade: bool) -> Dict[str, Any]:
        """Execute a single custom strategy"""
        strategy_name = strategy.get('name', 'Unknown')
        coins = strategy.get('coins', ['BTC', 'ETH'])
        
        result = {
            'strategy_name': strategy_name,
            'timestamp': datetime.now().isoformat(),
            'coins_checked': [],
            'signal': None,
            'trade_executed': False
        }
        
        # Get current market data for each coin
        for coin in coins[:5]:  # Limit to 5 coins per strategy
            try:
                signal = await self._evaluate_strategy_conditions(strategy, coin)
                result['coins_checked'].append({
                    'coin': coin,
                    'signal': signal
                })
                
                if signal in ['buy', 'sell']:
                    result['signal'] = signal
                    result['signal_coin'] = coin
                    
                    # Execute trade if conditions met
                    if signal == 'buy':
                        trade_result = await self._execute_strategy_trade(
                            strategy, coin, 'buy', paper_trade
                        )
                        if trade_result.get('success'):
                            result['trade_executed'] = True
                            result['trade'] = trade_result
                            
                            # Send notification
                            await self._send_strategy_notification(
                                strategy_name, 'entry', coin, 
                                trade_result.get('confidence', 0)
                            )
                            
            except Exception as e:
                logger.warning(f"Error evaluating {coin} for {strategy_name}: {e}")
        
        return result
    
    async def _evaluate_strategy_conditions(self, strategy: Dict, coin: str) -> str:
        """
        Evaluate entry/exit conditions for a strategy
        
        Returns:
            'buy', 'sell', or 'hold'
        """
        entry_conditions = strategy.get('entry_conditions', [])
        exit_conditions = strategy.get('exit_conditions', [])
        
        # Get current indicators for the coin
        indicators = await self._get_coin_indicators(coin)
        
        if not indicators:
            return 'hold'
        
        # Check entry conditions
        entry_met = all(
            self._check_condition(cond, indicators) 
            for cond in entry_conditions
        ) if entry_conditions else False
        
        # Check exit conditions
        exit_met = all(
            self._check_condition(cond, indicators)
            for cond in exit_conditions
        ) if exit_conditions else False
        
        # Check if we have an existing position
        has_position = await self._has_position(coin)
        
        if has_position and exit_met:
            return 'sell'
        elif not has_position and entry_met:
            return 'buy'
        
        return 'hold'
    
    async def _get_coin_indicators(self, coin: str) -> Dict[str, Any]:
        """Get current indicator values for a coin"""
        try:
            # Try to get from enhanced AI if available
            if self.enhanced_ai:
                signal = await self.enhanced_ai.get_enhanced_signal(coin)
                if signal and 'indicators' in signal:
                    return signal['indicators']
            
            # Fallback: Generate basic indicators from recent prices
            ohlcv = await self.db.ohlcv_data.find(
                {'symbol': coin.upper()}
            ).sort('timestamp', -1).limit(50).to_list(length=50)
            
            if len(ohlcv) < 14:
                return {}
            
            closes = [float(d['close']) for d in reversed(ohlcv)]
            
            # Calculate basic indicators
            import numpy as np
            
            # RSI
            deltas = np.diff(closes)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.abs(np.where(deltas < 0, deltas, 0))
            avg_gain = np.mean(gains[-14:])
            avg_loss = np.mean(losses[-14:])
            rs = avg_gain / (avg_loss + 0.0001)
            rsi = 100 - (100 / (1 + rs))
            
            # Moving averages
            sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else closes[-1]
            sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else closes[-1]
            
            # Price change
            price_change_24h = ((closes[-1] - closes[-24]) / closes[-24] * 100) if len(closes) >= 24 else 0
            
            return {
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'price': closes[-1],
                'price_change_24h': price_change_24h,
                'volume': ohlcv[0].get('volume', 0)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get indicators for {coin}: {e}")
            return {}
    
    def _check_condition(self, condition: Dict, indicators: Dict) -> bool:
        """Check if a single condition is met"""
        indicator = condition.get('indicator', '')
        operator = condition.get('operator', '>')
        value = condition.get('value')
        
        if indicator not in indicators:
            return False
        
        current_value = indicators[indicator]
        
        # Handle comparison with another indicator
        if isinstance(value, str) and value in indicators:
            target_value = indicators[value]
        else:
            try:
                target_value = float(value)
            except (ValueError, TypeError):
                return False
        
        # Evaluate condition
        if operator == '>':
            return current_value > target_value
        elif operator == '<':
            return current_value < target_value
        elif operator == '>=':
            return current_value >= target_value
        elif operator == '<=':
            return current_value <= target_value
        elif operator == '==':
            return abs(current_value - target_value) < 0.001
        elif operator == '!=':
            return abs(current_value - target_value) >= 0.001
        
        return False
    
    async def _has_position(self, coin: str) -> bool:
        """Check if we have an existing position in a coin"""
        try:
            position = await self.db.positions.find_one({
                'coin_id': coin.lower(),
                'status': 'open'
            })
            return position is not None
        except:
            return False
    
    async def _execute_strategy_trade(
        self, 
        strategy: Dict, 
        coin: str, 
        action: str,
        paper_trade: bool
    ) -> Dict[str, Any]:
        """Execute a trade based on strategy signal"""
        risk_params = strategy.get('risk_params', {})
        position_size_pct = risk_params.get('position_size_pct', 10)
        stop_loss_pct = risk_params.get('stop_loss_pct', 10)
        take_profit_pct = risk_params.get('take_profit_pct', 30)
        
        # Get balance
        balance = 500  # Default
        if self.isolated_portfolio:
            budget_status = await self.isolated_portfolio.get_budget_status()
            balance = budget_status.get('available', 500)
        
        amount = balance * (position_size_pct / 100)
        
        # Get Kraken symbol
        kraken_symbol = self.kraken_symbols.get(coin.lower())
        if not kraken_symbol:
            return {'success': False, 'error': f'No Kraken symbol for {coin}'}
        
        # Execute trade
        trade_result = await self._execute_isolated_trade(
            coin_id=coin.lower(),
            symbol=kraken_symbol,
            amount_usd=amount,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            paper_trade=paper_trade,
            is_gem=False,
            ai_score=70  # Custom strategy default score
        )
        
        if trade_result:
            trade_result['strategy'] = strategy.get('name')
            trade_result['confidence'] = 75  # Custom strategy confidence
        
        return trade_result or {'success': False}
    
    async def _send_strategy_notification(
        self, 
        strategy_name: str, 
        signal_type: str, 
        coin: str, 
        confidence: float
    ):
        """Send notification for strategy signal"""
        if self.notification_service:
            try:
                await self.notification_service.send_strategy_signal(
                    strategy_name=strategy_name,
                    signal_type=signal_type,
                    coin_symbol=coin,
                    confidence=confidence
                )
            except Exception as e:
                logger.warning(f"Failed to send strategy notification: {e}")

