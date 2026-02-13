"""
Core Services Initialization Module
Handles initialization of fundamental trading services
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def init_core_services(db: AsyncIOMotorDatabase) -> dict:
    """
    Initialize core trading services
    
    Args:
        db: MongoDB database connection
        
    Returns:
        Dictionary of initialized services
    """
    services = {}
    
    # Kraken Service
    from services.kraken_service import get_kraken_service
    services['kraken'] = get_kraken_service()
    logger.info("✅ Kraken service initialized")
    
    # AI Trainer
    from services.ai_trainer import AITrainer
    services['ai_trainer'] = AITrainer(db)
    logger.info("✅ AI Trainer initialized")
    
    # Alert Service
    from services.alert_service import get_alert_service
    services['alert_service'] = get_alert_service(db)
    logger.info("✅ Alert Service initialized")
    
    # Gem Finder (Legacy)
    from services.gem_finder import get_gem_finder
    services['gem_finder'] = get_gem_finder(db, services['kraken'])
    logger.info("✅ Gem Finder initialized")
    
    # Portfolio Manager
    from services.isolated_portfolio import get_isolated_portfolio
    services['isolated_portfolio'] = get_isolated_portfolio(db, services['kraken'])
    logger.info("✅ Isolated Portfolio Manager initialized")
    
    # Growth Engine
    from services.growth_engine import GrowthEngine
    services['growth_engine'] = GrowthEngine(
        db=db,
        kraken_service=services['kraken'],
        ai_trainer=services['ai_trainer'],
        alert_service=services['alert_service']
    )
    logger.info("✅ Growth Engine initialized")
    
    # Automated Trader
    from services.automated_trader import AutomatedWeeklyTrader
    services['automated_trader'] = AutomatedWeeklyTrader(
        db=db,
        kraken_service=services['kraken'],
        ai_trainer=services['ai_trainer'],
        gem_finder=services['gem_finder'],
        alert_service=services['alert_service'],
        isolated_portfolio=services['isolated_portfolio']
    )
    logger.info("✅ Automated Weekly Trader initialized")
    
    # Budget Manager
    from services.budget_manager import BudgetManager
    services['budget_manager'] = BudgetManager(db)
    services['growth_engine'].budget_manager = services['budget_manager']
    logger.info("✅ Budget Manager initialized")
    
    # Trading Journal
    from services.trading_journal import TradingJournalService
    services['journal_service'] = TradingJournalService(db)
    logger.info("✅ Trading Journal initialized")
    
    return services


async def init_ai_services(db: AsyncIOMotorDatabase, core_services: dict) -> dict:
    """
    Initialize AI and ML services
    
    Args:
        db: MongoDB database connection
        core_services: Dictionary of core services
        
    Returns:
        Dictionary of AI services
    """
    services = {}
    
    # Adaptive Strategy Engine
    from services.adaptive_strategy import get_adaptive_strategy
    services['adaptive_strategy'] = get_adaptive_strategy(
        db, core_services['kraken'], core_services['alert_service']
    )
    logger.info("✅ Adaptive Strategy Engine initialized")
    
    # Performance Tracker
    from services.performance_tracker import get_performance_tracker
    services['performance_tracker'] = get_performance_tracker(db)
    logger.info("✅ Performance Tracker initialized")
    
    # Regime Predictor
    from services.regime_predictor import get_regime_predictor
    services['regime_predictor'] = get_regime_predictor(db)
    logger.info("✅ Regime Prediction Engine initialized")
    
    # Enhanced AI Engine
    from services.enhanced_ai_engine import get_enhanced_ai
    services['enhanced_ai'] = get_enhanced_ai(db)
    logger.info("✅ Enhanced AI Engine initialized")
    
    # Paper Trading Simulator
    from services.paper_trading_simulator import get_paper_trader
    services['paper_trader'] = get_paper_trader(
        db, services['enhanced_ai'], services['regime_predictor']
    )
    logger.info("✅ Paper Trading Simulator initialized")
    
    # Gem ML/DL Prediction Engine
    from services.gem_ml_dl_predictor import get_gem_prediction_engine
    services['gem_ml_dl'] = get_gem_prediction_engine(db)
    logger.info("✅ Gem ML/DL Prediction Engine initialized")
    
    # Update automated trader with AI services
    automated_trader = core_services['automated_trader']
    automated_trader.adaptive_strategy = services['adaptive_strategy']
    automated_trader.regime_predictor = services['regime_predictor']
    automated_trader.performance_tracker = services['performance_tracker']
    automated_trader.gem_ml_dl = services['gem_ml_dl']
    logger.info("✅ Automated Trader updated with AI services")
    
    return services


async def init_data_services(db: AsyncIOMotorDatabase) -> dict:
    """
    Initialize data and external API services
    
    Args:
        db: MongoDB database connection
        
    Returns:
        Dictionary of data services
    """
    services = {}
    
    # CoinDesk News Service
    from services.coindesk_service import get_coindesk_service, get_cryptocompare_service
    services['coindesk'] = get_coindesk_service()
    logger.info("✅ CoinDesk News service initialized")
    
    # CryptoCompare Service
    services['cryptocompare'] = get_cryptocompare_service()
    logger.info("✅ CryptoCompare service initialized")
    
    # Historical Data Downloader
    from services.historical_data_downloader import get_historical_downloader
    services['historical_downloader'] = get_historical_downloader(db)
    logger.info("✅ Historical Data Downloader initialized")
    
    # AI Learning Loop
    from services.ai_learning_loop import get_learning_loop_service
    services['learning_loop'] = get_learning_loop_service(db)
    logger.info("✅ AI Learning Loop service initialized")
    
    # Event Correlation Engine
    from services.event_correlation_engine import get_correlation_engine
    services['correlation_engine'] = get_correlation_engine(
        db, services['coindesk'], services['cryptocompare']
    )
    logger.info("✅ Event Correlation Engine initialized")
    
    # Historical Events Database
    from services.historical_events_db import get_historical_events_db
    services['events_db'] = get_historical_events_db(
        db, services['coindesk'], services['correlation_engine']
    )
    logger.info("✅ Historical Events Database initialized")
    
    # Social Sentiment Scraper
    from services.social_sentiment import get_sentiment_scraper
    services['sentiment_scraper'] = get_sentiment_scraper(db)
    logger.info("✅ Social Sentiment Scraper initialized")
    
    # OHLCV Data Manager
    from services.ohlcv_data_manager import get_ohlcv_manager
    services['ohlcv_manager'] = get_ohlcv_manager(db)
    await services['ohlcv_manager'].ensure_indexes()
    logger.info("✅ OHLCV Data Manager initialized")
    
    return services
