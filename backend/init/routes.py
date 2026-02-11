"""
Route Registration
Centralizes all API route imports and registration
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)


def register_routes(api_router: APIRouter, db=None):
    """Register all API routes with the router"""
    
    # Import routes
    from routes import auth, trading, strategies, market, risk, learning, news, training
    from routes import auto_trading, allocation, scanner, auto_execute, backtest, rebalance
    from routes import social, notifications, alerts, email, ai_portfolio, ai_selection
    from routes import gems, auto_trade, growth, scheduler, budget, journal, ai_decisions
    from routes import ai_universe, ai_discovery, sentiment, cryptopanic, ai_chat
    from routes import ai_universe_expand, gem_predictor, simulation, ensemble, coindesk
    from routes import gem_predictor as gem_predictor_routes
    from routes import historical_data, ai_learning_loop, events, event_triggers
    from routes import kraken_universe, coindesk_universe
    from routes import adaptive_strategy, performance, social_sentiment, isolated_portfolio
    from routes import stop_loss_automation as stop_loss_routes
    from routes import gem_ml_dl
    from routes import portfolio_visualization
    from routes import background_tasks as bg_tasks
    from routes import kraken as kraken_routes
    from routes import enhanced_ai as enhanced_ai_routes
    from routes import paper_trading as paper_trading_routes
    from routes import prediction_enhancements
    from routes import strategy_builder as strategy_builder_routes
    from routes import ohlcv_data as ohlcv_routes
    from routes import api_keys  # API Key Management
    from routes import cache  # ML Cache Management
    from routes import training_history as training_history_routes
    from routes import training_scheduler as training_scheduler_routes
    from routes import model_persistence as model_persistence_routes
    from routes import spot_trading as spot_trading_routes
    from routes import drl_engine as drl_engine_routes
    from routes import trading_intelligence as trading_intelligence_routes
    from routes import sb3_agents as sb3_agents_routes
    from routes import kraken_exec as kraken_exec_routes
    from routes import rainbow as rainbow_routes
    from routes import tethys as tethys_routes
    from routes import tethys_trading as tethys_trading_routes
    from routes import tethys_train as tethys_train_routes
    from routes import advanced_ai as advanced_ai_routes
    from routes import master_orchestrator as master_routes
    from routes import upgrades as upgrades_routes
    from routes import onchain_data as onchain_data_routes
    from routes import whale_alerts as whale_alerts_routes
    from routes import copy_trading as copy_trading_routes
    from routes import market_maker as market_maker_routes
    from routes import dashboard_customization as dashboard_routes
    from routes import options_trading as options_routes
    from routes import backtest_engine as backtest_engine_routes
    from routes import advanced_orders as advanced_orders_routes
    from routes import defi_wallet as defi_wallet_routes
    from routes import yield_farming as yield_farming_routes
    from routes import perpetual_futures as perpetual_futures_routes
    from routes import risk_analyzer as risk_analyzer_routes
    from routes import telegram_notifications as telegram_routes
    from routes import portfolio_rebalance as rebalance_routes
    from routes import enhanced_data as enhanced_data_routes
    from routes import mtf_training as mtf_training_routes
    from routes import kraken_expansion as kraken_expansion_routes
    from routes import enhanced_mtf_training as enhanced_mtf_training_routes
    from routes import performance_dashboard as performance_dashboard_routes
    from routes import ml_optimization as ml_optimization_routes
    from routes import ml_monitoring as ml_monitoring_routes
    from routes import training_progress as training_progress_routes
    
    # Include routers
    api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    api_router.include_router(api_keys.router)  # API Key Management - uses own prefix
    api_router.include_router(cache.router)  # ML Cache Management
    api_router.include_router(trading.router, prefix="/trading", tags=["Trading"])
    api_router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
    api_router.include_router(market.router, prefix="/market", tags=["Market Data"])
    api_router.include_router(risk.router, prefix="/risk", tags=["Risk Management"])
    api_router.include_router(learning.router, prefix="/learning", tags=["AI Learning"])
    api_router.include_router(news.router, prefix="/news", tags=["Crypto News"])
    api_router.include_router(training.router, prefix="/training", tags=["Historical Training"])
    api_router.include_router(auto_trading.router, prefix="/auto-trading", tags=["Auto Trading"])
    api_router.include_router(allocation.router, prefix="/allocation", tags=["Portfolio Allocation"])
    api_router.include_router(scanner.router, prefix="/scanner", tags=["Hidden Gem Scanner"])
    api_router.include_router(auto_execute.router, prefix="/auto-exec", tags=["Auto Execution"])
    api_router.include_router(backtest.router, prefix="/backtest", tags=["Backtesting"])
    api_router.include_router(rebalance.router, prefix="/rebalance", tags=["Portfolio Rebalancing"])
    api_router.include_router(social.router, prefix="/social", tags=["Social Trading"])
    api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
    api_router.include_router(alerts.router, prefix="/alerts", tags=["Price Alerts"])
    api_router.include_router(email.router, prefix="/email", tags=["Email Notifications"])
    api_router.include_router(ai_portfolio.router, prefix="/ai-portfolio", tags=["AI Portfolio Manager"])
    api_router.include_router(ai_selection.router, tags=["AI Coin Selection"])
    api_router.include_router(gems.router, tags=["Gem Finder"])
    api_router.include_router(auto_trade.router, tags=["Automated Trading"])
    api_router.include_router(growth.router, tags=["Growth Engine"])
    api_router.include_router(scheduler.router, tags=["Scheduler"])
    api_router.include_router(budget.router, tags=["Budget Management"])
    api_router.include_router(journal.router, tags=["Trading Journal"])
    api_router.include_router(ai_decisions.router, prefix="/ai-decisions", tags=["AI Decisions"])
    api_router.include_router(ai_universe.router, tags=["AI Universe"])
    api_router.include_router(ai_discovery.router, tags=["AI Discovery"])
    api_router.include_router(sentiment.router, tags=["Sentiment Analysis"])
    api_router.include_router(cryptopanic.router, tags=["Crypto News"])
    api_router.include_router(ai_chat.router, tags=["AI Chat"])
    api_router.include_router(ai_universe_expand.router, tags=["AI Universe Expansion"])
    api_router.include_router(gem_predictor.router, tags=["Hidden Gem Predictor"])
    api_router.include_router(simulation.router, tags=["Historical Simulation"])
    api_router.include_router(ensemble.router, tags=["Ensemble AI"])
    api_router.include_router(coindesk.router, tags=["CoinDesk News"])
    api_router.include_router(historical_data.router, tags=["Historical Data"])
    api_router.include_router(ai_learning_loop.router, tags=["AI Learning Loop"])
    api_router.include_router(events.router, tags=["Events"])
    api_router.include_router(event_triggers.router, tags=["Event Triggers"])
    api_router.include_router(kraken_universe.router, tags=["Kraken Universe"])
    api_router.include_router(coindesk_universe.router, tags=["CoinDesk Universe"])
    api_router.include_router(adaptive_strategy.router, tags=["Adaptive Strategy"])
    api_router.include_router(performance.router, tags=["Performance & Prediction"])
    api_router.include_router(social_sentiment.router, tags=["Social Sentiment"])
    api_router.include_router(isolated_portfolio.router, tags=["Isolated Portfolio"])
    api_router.include_router(stop_loss_routes.router, tags=["Stop-Loss Automation"])
    api_router.include_router(gem_ml_dl.router, tags=["Gem ML/DL Prediction"])
    api_router.include_router(portfolio_visualization.router, tags=["Portfolio Visualization"])
    api_router.include_router(bg_tasks.router, tags=["Background Tasks"])
    api_router.include_router(kraken_routes.router, tags=["Kraken Trading"])
    api_router.include_router(enhanced_ai_routes.router, tags=["Enhanced AI"])
    api_router.include_router(paper_trading_routes.router, tags=["Paper Trading"])
    api_router.include_router(prediction_enhancements.router, tags=["Prediction Enhancements"])
    api_router.include_router(strategy_builder_routes.router, tags=["Custom Strategy Builder"])
    api_router.include_router(ohlcv_routes.router, tags=["OHLCV Data"])
    api_router.include_router(training_history_routes.router, tags=["Training History"])
    api_router.include_router(training_scheduler_routes.router, tags=["Training Scheduler"])
    api_router.include_router(model_persistence_routes.router, tags=["Model Persistence"])
    api_router.include_router(spot_trading_routes.router, tags=["Spot Trading"])
    api_router.include_router(drl_engine_routes.router, tags=["Deep RL Engine"])
    api_router.include_router(trading_intelligence_routes.router, tags=["Trading Intelligence"])
    api_router.include_router(sb3_agents_routes.router, tags=["SB3 Trading Agents"])
    api_router.include_router(kraken_exec_routes.router, tags=["Kraken Execution"])
    api_router.include_router(rainbow_routes.router, tags=["Rainbow DQN"])
    api_router.include_router(tethys_routes.router, tags=["Tethys Safety"])
    api_router.include_router(tethys_trading_routes.router, tags=["Tethys Trading"])
    api_router.include_router(tethys_train_routes.router, tags=["Tethys Training"])
    api_router.include_router(advanced_ai_routes.router, tags=["Advanced AI"])
    api_router.include_router(master_routes.router, tags=["Master Orchestrator"])
    api_router.include_router(upgrades_routes.router, tags=["Upgrades"])
    api_router.include_router(copy_trading_routes.router, tags=["Copy Trading"])
    api_router.include_router(market_maker_routes.router, tags=["Market Maker"])
    api_router.include_router(dashboard_routes.router, tags=["Dashboard Customization"])
    api_router.include_router(options_routes.router, tags=["Options Trading"])
    api_router.include_router(backtest_engine_routes.router, tags=["Backtesting Engine"])
    api_router.include_router(advanced_orders_routes.router, tags=["Advanced Orders"])
    api_router.include_router(defi_wallet_routes.router, tags=["DeFi Wallet"])
    api_router.include_router(yield_farming_routes.router, tags=["Yield Farming"])
    api_router.include_router(perpetual_futures_routes.router, tags=["Perpetual Futures"])
    api_router.include_router(risk_analyzer_routes.router, tags=["Risk Analyzer"])
    api_router.include_router(telegram_routes.router, tags=["Telegram Notifications"])
    api_router.include_router(rebalance_routes.router, tags=["Portfolio Rebalancing"])
    api_router.include_router(enhanced_data_routes.router, tags=["Enhanced Data Services"])
    api_router.include_router(mtf_training_routes.router, tags=["MTF Training"])
    api_router.include_router(kraken_expansion_routes.router, tags=["Kraken Data Expansion"])
    api_router.include_router(enhanced_mtf_training_routes.router, tags=["Enhanced MTF Training"])
    api_router.include_router(ml_optimization_routes.router, tags=["ML Optimization & A/B Testing"])
    api_router.include_router(ml_monitoring_routes.router, tags=["ML Monitoring & Analytics"])
    api_router.include_router(onchain_data_routes.router, tags=["On-Chain Data"])
    api_router.include_router(whale_alerts_routes.router, tags=["Whale Alerts & Backtesting"])
    api_router.include_router(performance_dashboard_routes.router, tags=["Performance Dashboard"])
    
    # Yearly Adaptive Backtest
    from routes import yearly_backtest as yearly_backtest_routes
    api_router.include_router(yearly_backtest_routes.router, tags=["Yearly Adaptive Backtest"])
    yearly_backtest_routes.set_db(db)
    
    # AI Teaching Service
    from routes import ai_teaching as ai_teaching_routes
    api_router.include_router(ai_teaching_routes.router, tags=["AI Teaching"])
    ai_teaching_routes.set_dependencies(db)
    
    # Weekly Selection Scheduler
    from routes import weekly_scheduler as weekly_scheduler_routes
    api_router.include_router(weekly_scheduler_routes.router, tags=["Weekly Scheduler"])
    
    # Integrations (Blockchain API, Social Trading)
    from routes import integrations as integrations_routes
    api_router.include_router(integrations_routes.router, tags=["Integrations"])
    integrations_routes.set_db(db)
    
    # Training Progress Monitoring
    api_router.include_router(training_progress_routes.router, tags=["Training Progress"])
    
    # Model Retrain Scheduler
    from routes import model_retrain_scheduler as retrain_scheduler_routes
    api_router.include_router(retrain_scheduler_routes.router, tags=["Model Retrain Scheduler"])
    retrain_scheduler_routes.set_dependencies(db)
    
    # Model Benchmarking
    from routes import model_benchmarking as model_benchmark_routes
    api_router.include_router(model_benchmark_routes.router, tags=["Model Benchmarking"])
    model_benchmark_routes.init_router(db)
    
    # Entry Price Management
    from routes import entry_prices as entry_prices_routes
    api_router.include_router(entry_prices_routes.router, tags=["Entry Price Management"])
    entry_prices_routes.init_router(db)
    
    # ============================================
    # NEW ENHANCEMENT ROUTES (P0, P1, Quick Wins)
    # ============================================
    
    # Export (CSV, PDF reports)
    from routes import export as export_routes
    api_router.include_router(export_routes.router, tags=["Export"])
    export_routes.set_db(db)
    
    # Achievement Badges
    from routes import achievements as achievements_routes
    api_router.include_router(achievements_routes.router, tags=["Achievements"])
    achievements_routes.set_db(db)
    
    # Event Countdown
    from routes import event_countdown as event_countdown_routes
    api_router.include_router(event_countdown_routes.router, tags=["Event Countdown"])
    event_countdown_routes.set_db(db)
    
    # Sound Settings
    from routes import sound_settings as sound_settings_routes
    api_router.include_router(sound_settings_routes.router, tags=["Sound Settings"])
    sound_settings_routes.set_db(db)
    
    # Portfolio Sharing
    from routes import portfolio_share as portfolio_share_routes
    api_router.include_router(portfolio_share_routes.router, tags=["Portfolio Sharing"])
    portfolio_share_routes.set_db(db)
    
    # Push Notifications
    from routes import push_notifications as push_notifications_routes
    api_router.include_router(push_notifications_routes.router, tags=["Push Notifications"])
    push_notifications_routes.set_db(db)
    
    # Paper Trading Leaderboard
    from routes import paper_leaderboard as paper_leaderboard_routes
    api_router.include_router(paper_leaderboard_routes.router, tags=["Paper Trading Leaderboard"])
    paper_leaderboard_routes.set_db(db)
    
    # Strategy Marketplace
    from routes import strategy_marketplace as marketplace_routes
    api_router.include_router(marketplace_routes.router, tags=["Strategy Marketplace"])
    marketplace_routes.set_db(db)
    
    # Social Trading (Enhanced)
    from routes import social_trading as social_trading_routes
    api_router.include_router(social_trading_routes.router, tags=["Social Trading Enhanced"])
    social_trading_routes.set_db(db)
    
    # Tax Reporting
    from routes import tax_reporting as tax_routes
    api_router.include_router(tax_routes.router, tags=["Tax Reporting"])
    tax_routes.set_db(db)
    
    # Email Digest
    from routes import email_digest as email_digest_routes
    api_router.include_router(email_digest_routes.router, tags=["Email Digest"])
    email_digest_routes.set_db(db)
    
    logger.info("✅ All routes registered (including new enhancements)")
    
    return api_router
