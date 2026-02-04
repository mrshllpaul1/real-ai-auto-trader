"""
Service Initialization
Modular initialization of all backend services
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
        await _init_phase5_scheduling(db)
        
        _initialized = True
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Service initialization error: {e}")
        raise
    
    return _services


async def _init_phase1_core(db):
    """Phase 1: Core services (no dependencies)"""
    from services.market_data_service import MarketDataService
    from services.news_service import CryptoNewsAggregator
    from services.kraken_service import KrakenAuthenticator, KrakenTradeService
    
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
    from services.dynamic_coin_universe import DynamicCoinUniverseManager, set_universe_manager
    universe_manager = DynamicCoinUniverseManager(db)
    await universe_manager.initialize()
    set_universe_manager(universe_manager)
    _services['universe'] = universe_manager
    logger.info("✅ Phase 1: Core services initialized")


async def _init_phase2_trading(db):
    """Phase 2: Trading services"""
    from services.alert_service import AlertService
    from services.budget_manager import BudgetManager
    from services.trading_journal import TradingJournalService
    from services.isolated_portfolio import get_isolated_portfolio
    
    _services['alerts'] = AlertService(db)
    _services['budget'] = BudgetManager(db)
    _services['journal'] = TradingJournalService(db)
    _services['isolated_portfolio'] = get_isolated_portfolio(db, _services['kraken'])
    
    logger.info("✅ Phase 2: Trading services initialized")


async def _init_phase3_ai(db):
    """Phase 3: AI and ML services"""
    from services.ai_portfolio_manager import AIPortfolioManager
    from services.adaptive_coin_selector import AdaptiveCoinSelector
    from services.gem_finder import HiddenGemFinder
    from services.ai_weekly_trainer import AIWeeklyTrainer
    from services.deep_learning_ai import get_deep_learning_ai
    from services.ensemble_ai import get_ensemble_predictor, get_universe_optimizer
    from services.regime_predictor import get_regime_predictor
    from services.performance_tracker import get_performance_tracker
    from services.enhanced_ai_engine import get_enhanced_ai
    
    market = _services['market']
    news = _services['news']
    kraken = _services['kraken']
    
    # AI Services
    _services['ai_portfolio'] = AIPortfolioManager(db=db, kraken_service=kraken, market_service=market, news_service=news)
    _services['coin_selector'] = AdaptiveCoinSelector(db, market, news)
    _services['gem_finder'] = HiddenGemFinder(db)
    _services['ai_trainer'] = AIWeeklyTrainer(db)
    
    # Deep Learning
    deep_ai = get_deep_learning_ai(db)
    _services['deep_ai'] = deep_ai
    
    # Ensemble & Optimizer
    ensemble_predictor = get_ensemble_predictor(db, market, deep_ai)
    universe_optimizer = get_universe_optimizer(db, market, ensemble_predictor, deep_ai)
    _services['ensemble'] = ensemble_predictor
    _services['universe_optimizer'] = universe_optimizer
    
    # Performance & Regime
    _services['performance'] = get_performance_tracker(db)
    _services['regime'] = get_regime_predictor(db)
    
    # Enhanced AI
    _services['enhanced_ai'] = get_enhanced_ai(db)
    
    logger.info("✅ Phase 3: AI services initialized")


async def _init_phase4_automation(db):
    """Phase 4: Automation services"""
    from services.automated_trader import AutomatedWeeklyTrader
    from services.growth_engine import AggressiveGrowthEngine
    from services.stop_loss_automation import get_stop_loss_automation
    from services.gem_ml_dl_predictor import get_gem_prediction_engine
    from services.background_tasks import get_task_manager
    
    kraken = _services['kraken']
    ai_trainer = _services['ai_trainer']
    gem_finder = _services['gem_finder']
    alerts = _services['alerts']
    isolated = _services['isolated_portfolio']
    regime = _services['regime']
    performance = _services['performance']
    
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
    growth_engine.budget_manager = _services['budget']
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
    
    logger.info("✅ Phase 4: Automation services initialized")


async def _init_phase5_scheduling(db):
    """Phase 5: Scheduling and continuous learning"""
    from services.scheduler_service import SchedulerService
    from services.training_scheduler import get_training_scheduler
    from services.training_history import get_training_history_service
    from services.learning_service import init_learning_service
    
    auto_trader = _services['auto_trader']
    growth_engine = _services['growth_engine']
    alerts = _services['alerts']
    stop_loss = _services['stop_loss']
    regime = _services['regime']
    
    # Scheduler Service
    scheduler = SchedulerService(
        db=db, growth_engine=growth_engine,
        automated_trader=auto_trader, alert_service=alerts
    )
    scheduler.set_stop_loss_automation(stop_loss)
    _services['scheduler'] = scheduler
    
    # Training History
    training_history = get_training_history_service(db)
    await training_history.ensure_indexes()
    _services['training_history'] = training_history
    
    # Training Scheduler
    training_scheduler = get_training_scheduler(db)
    _services['training_scheduler'] = training_scheduler
    
    # Learning Service
    from services.transformer_predictor import get_transformer_predictor
    from services.rl_trading_agent import get_rl_agent
    
    transformer = get_transformer_predictor(db)
    rl_agent = get_rl_agent(db)
    
    _services['transformer'] = transformer
    _services['rl_agent'] = rl_agent
    
    learning_service = init_learning_service(
        db,
        transformer_predictor=transformer,
        rl_agent=rl_agent,
        regime_predictor=regime,
        model_persistence=None
    )
    _services['learning'] = learning_service
    
    logger.info("✅ Phase 5: Scheduling services initialized")


def is_initialized() -> bool:
    """Check if services are initialized"""
    return _initialized
