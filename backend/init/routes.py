"""
Route Registration
Centralizes all API route imports and registration
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)


def register_routes(api_router: APIRouter):
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
    
    # Include routers
    api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
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
    api_router.include_router(deep_learning.router, tags=["Deep Learning AI"])
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
    api_router.include_router(srddqn_routes.router, tags=["SRDDQN Agent"])
    api_router.include_router(srddqn_pipeline_routes.router, tags=["SRDDQN Pipeline"])
    api_router.include_router(srddqn_trading_routes.router, tags=["SRDDQN Live Trading"])
    api_router.include_router(kraken_exec_routes.router, tags=["Kraken Execution"])
    api_router.include_router(rainbow_routes.router, tags=["Rainbow DQN"])
    api_router.include_router(tethys_routes.router, tags=["Tethys Safety"])
    api_router.include_router(tethys_trading_routes.router, tags=["Tethys Trading"])
    api_router.include_router(tethys_train_routes.router, tags=["Tethys Training"])
    
    logger.info("✅ All routes registered")
    
    return api_router
