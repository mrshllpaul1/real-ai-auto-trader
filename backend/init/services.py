"""
Service Initialization
Complete modular initialization of all backend services
"""

import os
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Global service references
_services: Dict[str, Any] = {}
_initialized = False


def get_service(name: str) -> Any:
    """Get a service by name"""
    return _services.get(name)


def get_all_services() -> Dict[str, Any]:
    """Get all initialized services"""
    return _services


async def initialize_all_services(db):
    """Initialize all services - called after startup"""
    global _initialized, _services
    
    if _initialized:
        return _services
    
    logger.info("🚀 Initializing services...")
    
    try:
        # Initialize in phases for proper dependency order
        await _init_phase1_core(db)
        await _init_phase2_trading(db)
        await _init_phase3_ai(db)
        await _init_phase4_automation(db)
        await _init_phase5_predictions(db)
        await _init_phase6_scheduling(db)
        await _init_phase7_wire_dependencies(db)
        
        _initialized = True
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Service initialization error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    return _services


async def _init_phase1_core(db):
    """Phase 1: Core services (no dependencies)"""
    from services.market_data_service import MarketDataService
    from services.news_service import CryptoNewsAggregator
    from services.kraken_service import KrakenAuthenticator, KrakenTradeService, set_kraken_service
    from services.dynamic_coin_universe import DynamicCoinUniverseManager, set_universe_manager
    from services.ai_news_sentiment import AINewsSentimentService, set_sentiment_service
    from services.cryptopanic_service import CryptoPanicService, set_cryptopanic_service
    from services.ai_coin_discovery import AICoinDiscoveryService, set_discovery_service
    
    # Market & News
    _services['market'] = MarketDataService()
    _services['news'] = CryptoNewsAggregator()
    
    # Kraken (optional)
    kraken_api_key = os.getenv('KRAKEN_API_KEY')
    kraken_api_secret = os.getenv('KRAKEN_API_SECRET')
    if kraken_api_key and kraken_api_secret:
        kraken_auth = KrakenAuthenticator(kraken_api_key, kraken_api_secret)
        _services['kraken'] = KrakenTradeService(kraken_auth)
        logger.info("✅ Kraken service initialized")
    else:
        _services['kraken'] = None
        logger.warning("⚠️ Kraken service not initialized - missing API keys")
    
    # Dynamic Coin Universe
    universe_manager = DynamicCoinUniverseManager(db)
    await universe_manager.initialize()
    set_universe_manager(universe_manager)
    _services['universe'] = universe_manager
    
    # AI Sentiment Service
    sentiment_service = AINewsSentimentService(db)
    set_sentiment_service(sentiment_service)
    _services['ai_sentiment'] = sentiment_service
    
    # CryptoPanic Service
    cryptopanic_service = CryptoPanicService()
    set_cryptopanic_service(cryptopanic_service)
    _services['cryptopanic'] = cryptopanic_service
    
    # AI Discovery Service
    discovery_service = AICoinDiscoveryService(db, universe_manager)
    set_discovery_service(discovery_service)
    _services['discovery'] = discovery_service
    
    logger.info("✅ Phase 1: Core services initialized")


async def _init_phase2_trading(db):
    """Phase 2: Trading services"""
    from services.alert_service import AlertService
    from services.budget_manager import BudgetManager
    from services.trading_journal import TradingJournalService
    from services.isolated_portfolio import get_isolated_portfolio
    from services.historical_trainer import HistoricalTrainer
    from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
    
    _services['alerts'] = AlertService(db)
    _services['budget'] = BudgetManager(db)
    _services['journal'] = TradingJournalService(db)
    _services['isolated_portfolio'] = get_isolated_portfolio(db, _services['kraken'])
    _services['historical_trainer'] = HistoricalTrainer(db)
    _services['enhanced_trainer'] = EnhancedHistoricalTrainer(db)
    
    logger.info("✅ Phase 2: Trading services initialized")


async def _init_phase3_ai(db):
    """Phase 3: AI and ML services"""
    from services.ai_portfolio_manager import AIPortfolioManager
    from services.adaptive_coin_selector import AdaptiveCoinSelector
    from services.weekly_simulation import WeeklySimulationRunner
    from services.gem_finder import HiddenGemFinder
    from services.ai_weekly_trainer import AIWeeklyTrainer
    from services.ensemble_ai import get_ensemble_predictor, get_universe_optimizer
    from services.regime_predictor import get_regime_predictor
    from services.performance_tracker import get_performance_tracker
    from services.enhanced_ai_engine import get_enhanced_ai
    from services.ai_chat_service import AIChatService
    from services.ai_universe_expander import get_universe_expander
    from services.hidden_gem_predictor import get_gem_predictor
    from services.social_sentiment import get_sentiment_scraper
    from services.gem_backtester import get_gem_backtester
    
    market = _services['market']
    news = _services['news']
    kraken = _services['kraken']
    
    # AI Services
    _services['ai_portfolio'] = AIPortfolioManager(db=db, kraken_service=kraken, market_service=market, news_service=news)
    _services['coin_selector'] = AdaptiveCoinSelector(db, market, news)
    _services['simulation_runner'] = WeeklySimulationRunner(db)
    _services['gem_finder'] = HiddenGemFinder(db)
    _services['ai_trainer'] = AIWeeklyTrainer(db)
    
    # Ensemble & Optimizer (use Rainbow DQN from Tethys instead of deprecated deep_learning)
    from services.rainbow_dqn import get_rainbow_agent
    rainbow_agent = get_rainbow_agent()
    _services['rainbow_agent'] = rainbow_agent
    
    ensemble_predictor = get_ensemble_predictor(db, market, rainbow_agent)
    universe_optimizer = get_universe_optimizer(db, market, ensemble_predictor, rainbow_agent)
    _services['ensemble'] = ensemble_predictor
    _services['universe_optimizer'] = universe_optimizer
    
    # Performance & Regime
    _services['performance'] = get_performance_tracker(db)
    _services['regime'] = get_regime_predictor(db)
    
    # Enhanced AI
    _services['enhanced_ai'] = get_enhanced_ai(db)
    
    # AI Chat Service
    chat_service = AIChatService(db, market, news)
    _services['chat'] = chat_service
    
    # Universe Expander
    universe_expander = get_universe_expander(db, market)
    _services['universe_expander'] = universe_expander
    
    # Hidden Gem Predictor (use rainbow_agent instead of deep_ai)
    hidden_gem_predictor = get_gem_predictor(db, market, rainbow_agent)
    _services['gem_predictor'] = hidden_gem_predictor
    
    # Social Sentiment
    sentiment_scraper = get_sentiment_scraper(db)
    _services['sentiment_scraper'] = sentiment_scraper
    
    # Gem Backtester
    gem_backtester = get_gem_backtester(db, hidden_gem_predictor)
    _services['gem_backtester'] = gem_backtester
    
    logger.info("✅ Phase 3: AI services initialized")


async def _init_phase4_automation(db):
    """Phase 4: Automation services"""
    from services.automated_trader import AutomatedWeeklyTrader
    from services.growth_engine import AggressiveGrowthEngine
    from services.stop_loss_automation import get_stop_loss_automation
    from services.gem_ml_dl_predictor import get_gem_prediction_engine
    from services.background_tasks import get_task_manager
    from services.paper_trading_simulator import get_paper_trader
    from services.adaptive_strategy import get_adaptive_strategy
    from services.push_notification_service import get_notification_service
    
    kraken = _services['kraken']
    ai_trainer = _services['ai_trainer']
    gem_finder = _services['gem_finder']
    alerts = _services['alerts']
    isolated = _services['isolated_portfolio']
    regime = _services['regime']
    performance = _services['performance']
    enhanced_ai = _services['enhanced_ai']
    budget = _services['budget']
    
    # Background Task Manager
    task_manager = get_task_manager(db)
    _services['task_manager'] = task_manager
    
    # Automated Trader
    automated_trader = AutomatedWeeklyTrader(
        db=db, kraken_service=kraken, ai_trainer=ai_trainer,
        gem_finder=gem_finder, alert_service=alerts,
        isolated_portfolio=isolated
    )
    automated_trader.regime_predictor = regime
    automated_trader.performance_tracker = performance
    automated_trader.task_manager = task_manager
    _services['auto_trader'] = automated_trader
    
    # Growth Engine
    growth_engine = AggressiveGrowthEngine(
        db=db, kraken_service=kraken, gem_finder=gem_finder,
        ai_trainer=ai_trainer, alert_service=alerts
    )
    growth_engine.budget_manager = budget
    _services['growth_engine'] = growth_engine
    
    # Stop-Loss
    stop_loss = get_stop_loss_automation(
        db=db, kraken_service=kraken,
        isolated_portfolio=isolated, alert_service=alerts
    )
    _services['stop_loss'] = stop_loss
    
    # ML/DL Gem Predictor
    gem_ml_dl = get_gem_prediction_engine(db)
    _services['gem_ml_dl'] = gem_ml_dl
    automated_trader.gem_ml_dl = gem_ml_dl
    
    # Paper Trader
    paper_trader = get_paper_trader(db, enhanced_ai, regime)
    _services['paper_trader'] = paper_trader
    
    # Adaptive Strategy
    adaptive_strategy = get_adaptive_strategy(db, kraken, alerts)
    _services['adaptive_strategy'] = adaptive_strategy
    automated_trader.adaptive_strategy = adaptive_strategy
    
    # Push Notification
    push_notification = get_notification_service(db)
    _services['push_notification'] = push_notification
    automated_trader.notification_service = push_notification
    
    logger.info("✅ Phase 4: Automation services initialized")


async def _init_phase5_predictions(db):
    """Phase 5: Deep RL Trading Engine + Prediction Services"""
    from services.order_book_analyzer import get_order_book_analyzer
    from services.on_chain_analytics import get_on_chain_analytics
    from services.social_sentiment_pipeline import get_social_sentiment
    from services.transformer_predictor import get_transformer_predictor
    from services.rl_trading_agent import get_rl_agent
    from services.cross_asset_correlation import get_cross_asset_correlation
    from services.advanced_technical_analysis import get_advanced_ta
    from services.deep_rl_trading_engine import get_drl_engine, initialize_drl_engine
    from services.trading_intelligence_engine import initialize_trading_intelligence
    
    task_manager = _services['task_manager']
    
    # Initialize Deep RL Trading Engine (replaces traditional ML)
    drl_engine = await initialize_drl_engine(db)
    _services['drl_engine'] = drl_engine
    logger.info("✅ Deep RL Trading Engine initialized")
    
    # Initialize Trading Intelligence Engine (XGBoost/LightGBM + FinRL)
    trading_intelligence = await initialize_trading_intelligence(db)
    _services['trading_intelligence'] = trading_intelligence
    logger.info("✅ Trading Intelligence Engine initialized")
    
    # Initialize SB3 Trading Agent Manager (Stable-Baselines3)
    try:
        from services.sb3_trading_agents import initialize_sb3_manager
        sb3_manager = await initialize_sb3_manager(db)
        _services['sb3_manager'] = sb3_manager
        logger.info("✅ SB3 Trading Agent Manager initialized")
    except Exception as e:
        logger.warning(f"⚠️ SB3 Manager initialization failed: {e}")
        _services['sb3_manager'] = None
    
    # Initialize SRDDQN Manager (Self-Rewarding Double DQN)
    try:
        from services.srddqn_agent import initialize_srddqn_manager
        srddqn_manager = await initialize_srddqn_manager(db)
        _services['srddqn_manager'] = srddqn_manager
        logger.info("✅ SRDDQN Manager initialized")
    except Exception as e:
        logger.warning(f"⚠️ SRDDQN Manager initialization failed: {e}")
        _services['srddqn_manager'] = None
    
    order_book = get_order_book_analyzer(db)
    on_chain = get_on_chain_analytics(db)
    social_sentiment = get_social_sentiment(db)
    transformer = get_transformer_predictor(db)
    rl_agent = get_rl_agent(db)
    cross_asset = get_cross_asset_correlation(db)
    advanced_ta = get_advanced_ta(db)
    
    # Inject task manager into RL agent
    rl_agent.set_task_manager(task_manager)
    
    _services['order_book'] = order_book
    _services['on_chain'] = on_chain
    _services['social_pipeline'] = social_sentiment
    _services['transformer'] = transformer
    _services['rl_agent'] = rl_agent
    _services['cross_asset'] = cross_asset
    _services['advanced_ta'] = advanced_ta
    
    # Bundle prediction services
    _services['prediction_services'] = {
        'order_book': order_book,
        'on_chain': on_chain,
        'social': social_sentiment,
        'transformer': transformer,
        'rl_agent': rl_agent,
        'cross_asset': cross_asset,
        'advanced_ta': advanced_ta
    }
    
    # Inject into automated trader
    auto_trader = _services['auto_trader']
    auto_trader.prediction_services = _services['prediction_services']
    
    logger.info("✅ Phase 5: Prediction Enhancement services initialized (8 models)")


async def _init_phase6_scheduling(db):
    """Phase 6: Scheduling and continuous learning"""
    from services.scheduler_service import SchedulerService
    from services.training_scheduler import get_training_scheduler
    from services.training_history import get_training_history_service
    from services.learning_service import init_learning_service
    from services.ohlcv_data_manager import get_ohlcv_manager
    from services.coindesk_service import get_coindesk_service, get_cryptocompare_service
    from services.historical_data_downloader import get_historical_downloader
    from services.ai_learning_loop import get_learning_loop_service
    from services.event_correlation_engine import get_correlation_engine
    from services.historical_events_db import get_historical_events_db
    from services.event_triggers import get_event_trigger_service
    from services.kraken_universe import get_kraken_universe
    from services.coindesk_universe import get_coindesk_universe
    from services.custom_strategy_builder import get_strategy_builder
    
    auto_trader = _services['auto_trader']
    growth_engine = _services['growth_engine']
    alerts = _services['alerts']
    stop_loss = _services['stop_loss']
    regime = _services['regime']
    transformer = _services['transformer']
    rl_agent = _services['rl_agent']
    kraken = _services['kraken']
    historical_trainer = _services['historical_trainer']
    enhanced_trainer = _services['enhanced_trainer']
    chat = _services['chat']
    
    # Scheduler Service
    scheduler_service = SchedulerService(
        db=db, growth_engine=growth_engine,
        automated_trader=auto_trader, alert_service=alerts
    )
    scheduler_service.set_stop_loss_automation(stop_loss)
    scheduler_service.set_trainers(historical_trainer, enhanced_trainer)
    _services['scheduler'] = scheduler_service
    
    # Training History
    training_history = get_training_history_service(db)
    await training_history.ensure_indexes()
    _services['training_history'] = training_history
    rl_agent.set_history_service(training_history)
    
    # Training Scheduler
    training_scheduler = get_training_scheduler(db)
    _services['training_scheduler'] = training_scheduler
    
    # Register trainers for schedulable models
    async def train_rl(episodes=100, **kwargs):
        return await rl_agent.train_background(episodes=episodes)
    
    async def train_transformer(**kwargs):
        return await transformer.train()
    
    async def train_regime(**kwargs):
        return await regime.train_models()
    
    training_scheduler.register_trainer("rl_agent", train_rl)
    training_scheduler.register_trainer("transformer", train_transformer)
    training_scheduler.register_trainer("regime", train_regime)
    
    # Learning Service
    learning_service = init_learning_service(
        db,
        transformer_predictor=transformer,
        rl_agent=rl_agent,
        regime_predictor=regime,
        model_persistence=None
    )
    _services['learning'] = learning_service
    
    # OHLCV Manager
    ohlcv_manager = get_ohlcv_manager(db)
    await ohlcv_manager.ensure_indexes()
    _services['ohlcv'] = ohlcv_manager
    
    # CoinDesk Services
    coindesk_service = get_coindesk_service()
    cryptocompare_service = get_cryptocompare_service()
    _services['coindesk'] = coindesk_service
    _services['cryptocompare'] = cryptocompare_service
    
    # Historical Data Downloader
    historical_downloader = get_historical_downloader(db)
    _services['historical_downloader'] = historical_downloader
    
    # Learning Loop
    learning_loop = get_learning_loop_service(db)
    _services['learning_loop'] = learning_loop
    
    # Event Correlation Engine
    correlation_engine = get_correlation_engine(db, coindesk_service, cryptocompare_service)
    events_db = get_historical_events_db(db, coindesk_service, correlation_engine)
    _services['correlation_engine'] = correlation_engine
    _services['events_db'] = events_db
    
    # Event Triggers
    trigger_service = get_event_trigger_service(
        db=db, coindesk_service=coindesk_service,
        correlation_engine=correlation_engine,
        kraken_service=kraken, alert_service=alerts
    )
    _services['trigger_service'] = trigger_service
    
    # Universe Services
    kraken_universe = get_kraken_universe(db)
    coindesk_universe = get_coindesk_universe(db)
    _services['kraken_universe'] = kraken_universe
    _services['coindesk_universe'] = coindesk_universe
    
    # Strategy Builder
    strategy_builder = get_strategy_builder(db, chat)
    _services['strategy_builder'] = strategy_builder
    
    logger.info("✅ Phase 6: Scheduling and data services initialized")


async def _init_phase7_wire_dependencies(db):
    """Phase 7: Wire up route dependencies and start schedulers"""
    from routes import ai_universe, sentiment, cryptopanic, ai_discovery
    from routes import ai_chat, ai_universe_expand, gem_predictor, simulation, ensemble
    from routes import coindesk, historical_data, ai_learning_loop, events, event_triggers
    from routes import kraken_universe, coindesk_universe, adaptive_strategy, performance
    from routes import social_sentiment, isolated_portfolio, stop_loss_automation
    from routes import gem_ml_dl, portfolio_visualization, background_tasks
    from routes import kraken as kraken_routes, enhanced_ai as enhanced_ai_routes
    from routes import paper_trading as paper_trading_routes, prediction_enhancements
    from routes import strategy_builder as strategy_builder_routes, ohlcv_data as ohlcv_routes
    from routes import training_history as training_history_routes
    from routes import training_scheduler as training_scheduler_routes
    from routes import spot_trading as spot_trading_routes
    from routes import ai_selection, gems, auto_trade, growth, scheduler as scheduler_routes
    from routes import budget as budget_routes, journal as journal_routes
    from routes.learning import set_learning_service
    from routes import gem_predictor as gem_predictor_routes
    
    # Wire route dependencies
    ai_universe.set_dependencies(_services['universe'])
    sentiment.set_dependencies(_services['ai_sentiment'])
    cryptopanic.set_dependencies(_services['cryptopanic'], _services['news'])
    ai_discovery.set_dependencies(_services['discovery'])
    ai_chat.set_dependencies(db, _services['chat'])
    ai_chat.set_kraken_service(_services['kraken'])
    ai_chat.set_gem_predictor(_services['gem_predictor'])
    ai_universe_expand.set_dependencies(db, _services['market'], _services['universe_expander'])
    gem_predictor.set_dependencies(db, _services['gem_predictor'])
    gem_predictor_routes.set_backtester(_services['gem_backtester'])
    simulation.set_dependencies(db, _services['market'])
    ensemble.set_dependencies(db, _services['market'], _services['ensemble'], _services['universe_optimizer'], _services['rainbow_agent'])
    coindesk.set_dependencies(_services['coindesk'])
    historical_data.set_dependencies(db, _services['historical_downloader'], _services['cryptocompare'])
    ai_learning_loop.set_dependencies(db, _services['learning_loop'])
    events.set_dependencies(db, _services['correlation_engine'], _services['events_db'])
    event_triggers.set_dependencies(db, _services['trigger_service'])
    kraken_universe.set_dependencies(_services['kraken_universe'])
    coindesk_universe.set_dependencies(_services['coindesk_universe'])
    adaptive_strategy.set_dependencies(db, _services['adaptive_strategy'])
    performance.set_dependencies(db, _services['performance'], _services['regime'])
    social_sentiment.set_dependencies(db, _services['sentiment_scraper'])
    isolated_portfolio.set_dependencies(db, _services['isolated_portfolio'])
    stop_loss_automation.set_dependencies(db, _services['stop_loss'])
    gem_ml_dl.set_dependencies(db, _services['gem_ml_dl'])
    portfolio_visualization.set_dependencies(db, _services['isolated_portfolio'])
    portfolio_visualization.set_scheduler(_services['scheduler'])
    background_tasks.set_dependencies(db, _services['task_manager'])
    kraken_routes.set_dependencies(db, _services['kraken'], _services['isolated_portfolio'], _services['auto_trader'])
    enhanced_ai_routes.set_dependencies(db, _services['enhanced_ai'], _services['regime'])
    paper_trading_routes.set_dependencies(db, _services['paper_trader'])
    prediction_enhancements.set_dependencies(
        db=db,
        order_book=_services['order_book'],
        on_chain=_services['on_chain'],
        social_sentiment=_services['social_pipeline'],
        transformer=_services['transformer'],
        rl_agent=_services['rl_agent'],
        cross_asset=_services['cross_asset'],
        advanced_ta=_services['advanced_ta']
    )
    strategy_builder_routes.set_dependencies(db, _services['strategy_builder'])
    ohlcv_routes.set_dependencies(_services['ohlcv'])
    training_history_routes.set_dependencies(_services['training_history'])
    training_scheduler_routes.set_dependencies(_services['training_scheduler'])
    spot_trading_routes.set_dependencies(
        db, _services['kraken'], _services['isolated_portfolio'], _services['auto_trader'],
        prediction_services=_services['prediction_services']
    )
    ai_selection.set_dependencies(db, _services['coin_selector'], _services['simulation_runner'])
    gems.set_dependencies(db, _services['gem_finder'])
    auto_trade.set_dependencies(db, _services['auto_trader'], _services['alerts'], _services['sentiment_scraper'])
    growth.set_dependencies(db, _services['growth_engine'])
    scheduler_routes.set_dependencies(_services['scheduler'])
    budget_routes.set_dependencies(_services['budget'])
    journal_routes.set_dependencies(_services['journal'])
    set_learning_service(_services['learning'])
    
    # Wire DRL Engine routes
    from routes import drl_engine as drl_engine_routes
    drl_engine_routes.set_dependencies(db, _services.get('drl_engine'))
    
    # Wire Trading Intelligence routes
    from routes import trading_intelligence as trading_intelligence_routes
    trading_intelligence_routes.set_dependencies(db, _services.get('trading_intelligence'))
    
    # Wire SB3 Agents routes
    from routes import sb3_agents as sb3_agents_routes
    sb3_agents_routes.set_dependencies(db, _services.get('sb3_manager'))
    
    # Wire Kraken Execution routes
    from routes import kraken_exec as kraken_exec_routes
    kraken_exec_routes.set_dependencies(db)
    
    # Wire Tethys Safety routes
    from routes import tethys as tethys_routes
    tethys_routes.set_db(db)
    logger.info("✅ Tethys Safety System wired")
    
    # Wire Tethys Trading routes
    from routes import tethys_trading as tethys_trading_routes
    tethys_trading_routes.set_db(db)
    logger.info("✅ Tethys Trading System wired")
    
    # Wire Advanced AI routes
    from routes import advanced_ai as advanced_ai_routes
    advanced_ai_routes.set_db(db)
    logger.info("✅ Advanced AI System wired")
    
    # Wire Master Orchestrator routes
    from routes import master_orchestrator as master_routes
    master_routes.set_db(db)
    logger.info("✅ Master Orchestrator wired")
    
    # Start schedulers
    await _services['training_scheduler'].start()
    logger.info("✅ Training Scheduler started")
    
    await _services['scheduler'].start()
    logger.info("✅ Scheduler Service started")
    
    # Add scheduled jobs
    await _services['scheduler'].add_stop_loss_job(interval_minutes=5)
    await _services['scheduler'].add_portfolio_snapshot_job(interval_hours=6)
    await _services['scheduler'].add_auto_retrain_job(hour=2)
    
    logger.info("✅ Phase 7: Routes wired and schedulers started")


def is_initialized() -> bool:
    """Check if services are initialized"""
    return _initialized
