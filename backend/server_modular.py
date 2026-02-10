"""
AI Crypto Trading API Server
Main entry point - modularized version

This file coordinates service initialization by delegating to specialized init modules.
"""

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
import os
import logging
import asyncio

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'crypto_trading_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="AI Crypto Trading API",
    description="Real money AI-powered cryptocurrency auto trading platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root_health():
    """Root health check"""
    return {"status": "ok", "service": "ai-crypto-trading"}

# API Router
api_router = APIRouter(prefix="/api")

@api_router.get("/health")
async def api_health_check():
    """API health check endpoint"""
    try:
        await client.admin.command('ping')
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "healthy", "database": db_status, "version": "1.0.0"}

@api_router.get("/")
async def root():
    return {
        "message": "AI Crypto Trading API",
        "status": "operational",
        "features": ["AI-powered trading", "Paper & Real trading", "Growth Engine"]
    }

# =============================================================================
# WEBSOCKET MANAGER
# =============================================================================

from config.websocket import ws_manager

@app.websocket("/ws/training")
async def websocket_training_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time training status updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                from services.background_tasks import get_task_manager
                task_manager = get_task_manager()
                
                if task_manager:
                    active_tasks = await task_manager.get_active_tasks()
                    await websocket.send_json({
                        "type": "training_update",
                        "timestamp": asyncio.get_event_loop().time(),
                        "tasks": active_tasks
                    })
            except Exception as e:
                logger.debug(f"WebSocket training update error: {e}")
            
            await asyncio.sleep(3)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# =============================================================================
# ROUTE IMPORTS
# =============================================================================

from routes import auth, trading, ai, portfolio, news, analytics
from routes import gems, risk, notifications, alerts, social, email
from routes import ai_portfolio, ai_selection, deep_learning, ai_chat
from routes import ai_universe, ai_universe_expand, kraken, ai_discovery
from routes import sentiment, cryptopanic, historical, continuous_learning
from routes import event_triggers, event_timeline, weekly_expansion
from routes import regime, gem_backtester, coin_sentiment, isolated_portfolio
from routes import gem_ml_dl, paper_trading, enhanced_ai, stop_loss
from routes import portfolio_viz, background_tasks as bg_tasks
from routes import prediction_enhancements, strategy_builder as strategy_builder_routes
from routes import ohlcv_data as ohlcv_routes
from routes import training_history as training_history_routes
from routes import training_scheduler as training_scheduler_routes
from routes import ml_optimization

# =============================================================================
# REGISTER ROUTES
# =============================================================================

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(trading.router, prefix="/trading", tags=["Trading"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Analysis"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(news.router, prefix="/news", tags=["News"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(social.router, prefix="/social", tags=["Social"])
api_router.include_router(email.router, prefix="/email", tags=["Email"])
api_router.include_router(ai_portfolio.router, prefix="/ai-portfolio", tags=["AI Portfolio"])
api_router.include_router(ai_selection.router, prefix="/ai-selection", tags=["AI Selection"])
api_router.include_router(deep_learning.router, prefix="/deep-learning", tags=["Deep Learning"])
api_router.include_router(ai_chat.router, prefix="/ai-chat", tags=["AI Chat"])
api_router.include_router(ai_universe.router, prefix="/ai-universe", tags=["AI Universe"])
api_router.include_router(ai_universe_expand.router, prefix="/ai-universe-expand", tags=["AI Universe Expander"])
api_router.include_router(kraken.router, prefix="/kraken", tags=["Kraken Exchange"])
api_router.include_router(ai_discovery.router, prefix="/ai-discovery", tags=["AI Discovery"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["Sentiment"])
api_router.include_router(cryptopanic.router, prefix="/cryptopanic", tags=["CryptoPanic"])
api_router.include_router(historical.router, prefix="/historical", tags=["Historical Data"])
api_router.include_router(continuous_learning.router, prefix="/continuous-learning", tags=["Continuous Learning"])
api_router.include_router(event_triggers.router, prefix="/event-triggers", tags=["Event Triggers"])
api_router.include_router(event_timeline.router, prefix="/event-timeline", tags=["Event Timeline"])
api_router.include_router(weekly_expansion.router, prefix="/weekly-expansion", tags=["Weekly Expansion"])
api_router.include_router(regime.router, prefix="/regime", tags=["Market Regime"])
api_router.include_router(gem_backtester.router, prefix="/gem-backtester", tags=["Gem Backtester"])
api_router.include_router(coin_sentiment.router, prefix="/coin-sentiment", tags=["Coin Sentiment"])
api_router.include_router(isolated_portfolio.router, prefix="/isolated-portfolio", tags=["Isolated Portfolio"])
api_router.include_router(gems.router, tags=["Gem Finder"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk Management"])
api_router.include_router(gem_ml_dl.router, tags=["Gem ML/DL"])
api_router.include_router(paper_trading.router, tags=["Paper Trading"])
api_router.include_router(enhanced_ai.router, tags=["Enhanced AI"])
api_router.include_router(stop_loss.router, tags=["Stop Loss"])
api_router.include_router(portfolio_viz.router, tags=["Portfolio Visualization"])
api_router.include_router(bg_tasks.router, prefix="/tasks", tags=["Background Tasks"])
api_router.include_router(prediction_enhancements.router, prefix="/predictions", tags=["Prediction Enhancements"])
api_router.include_router(strategy_builder_routes.router, tags=["Custom Strategy Builder"])
api_router.include_router(ohlcv_routes.router, tags=["OHLCV Data"])
api_router.include_router(training_history_routes.router, tags=["Training History"])
api_router.include_router(training_scheduler_routes.router, tags=["Training Scheduler"])

# Include the router
app.include_router(api_router)

# =============================================================================
# SERVICE INITIALIZATION
# =============================================================================

_services_initialized = False
kraken_service = None  # Global reference for trading routes


async def initialize_services():
    """Initialize all services - called after startup"""
    global _services_initialized, kraken_service
    if _services_initialized:
        return
    
    logger.info("🚀 Initializing services...")
    
    try:
        # =====================================================================
        # PHASE 1: Core Infrastructure
        # =====================================================================
        
        from services.market_data_service import MarketDataService
        from services.news_service import CryptoNewsAggregator
        from services.kraken_service import KrakenAuthenticator, KrakenTradeService
        
        market_service = MarketDataService()
        news_service = CryptoNewsAggregator()
        
        # Initialize Kraken Service
        auth = KrakenAuthenticator()
        kraken_service = KrakenTradeService(auth)
        logger.info("✅ Kraken Service initialized")
        
        # =====================================================================
        # PHASE 2: Dynamic Universe & Discovery
        # =====================================================================
        
        from services.dynamic_coin_universe import DynamicCoinUniverseManager, set_universe_manager
        from services.ai_coin_discovery import AICoinDiscoveryService, set_discovery_service
        from services.ai_news_sentiment import AINewsSentimentService, set_sentiment_service
        
        universe_manager = DynamicCoinUniverseManager(db)
        await universe_manager.initialize()
        set_universe_manager(universe_manager)
        ai_universe.set_dependencies(universe_manager)
        logger.info("✅ Dynamic Coin Universe initialized")
        
        sentiment_service = AINewsSentimentService(db)
        set_sentiment_service(sentiment_service)
        sentiment.set_dependencies(sentiment_service)
        logger.info("✅ AI Sentiment Service initialized")
        
        discovery_service = AICoinDiscoveryService(db, universe_manager)
        set_discovery_service(discovery_service)
        ai_discovery.set_dependencies(discovery_service)
        logger.info("✅ AI Discovery Service initialized")
        
        # =====================================================================
        # PHASE 3: News & External Services
        # =====================================================================
        
        from services.cryptopanic_service import CryptoPanicService, set_cryptopanic_service
        
        cryptopanic_service = CryptoPanicService()
        set_cryptopanic_service(cryptopanic_service)
        cryptopanic.set_dependencies(cryptopanic_service, news_service)
        logger.info("✅ CryptoPanic Service initialized")
        
        # =====================================================================
        # PHASE 4: AI Services
        # =====================================================================
        
        deep_learning.set_dependencies(db, market_service)
        logger.info("✅ Deep Learning AI initialized")
        
        from services.ai_chat_service import AIChatService
        chat_service = AIChatService(db, market_service, news_service)
        ai_chat.set_dependencies(db, chat_service)
        logger.info("✅ AI Chat Service initialized")
        
        from services.ai_universe_expander import get_universe_expander
        universe_expander = get_universe_expander(db, market_service)
        ai_universe_expand.set_dependencies(db, market_service, universe_expander)
        logger.info("✅ AI Universe Expander initialized")
        
        # =====================================================================
        # PHASE 5: Trading Services
        # =====================================================================
        
        from services.ai_trainer import AITrainer
        from services.gem_finder import HiddenGemFinder
        from services.alert_service import AlertService
        from services.automated_trader import AutomatedWeeklyTrader
        from services.growth_engine import AggressiveGrowthEngine
        from services.budget_manager import BudgetManager
        from services.trading_journal import TradingJournalService
        
        ai_trainer = AITrainer(db)
        await ai_trainer.ensure_initialized()
        logger.info("✅ AI Trainer initialized")
        
        gem_finder = HiddenGemFinder(db, kraken_service)
        alert_service = AlertService(db)
        budget_manager = BudgetManager(db)
        journal_service = TradingJournalService(db)
        
        growth_engine = AggressiveGrowthEngine(
            db=db,
            kraken_service=kraken_service,
            ai_trainer=ai_trainer,
            alert_service=alert_service
        )
        growth_engine.budget_manager = budget_manager
        logger.info("✅ Growth Engine initialized")
        
        # Initialize Isolated Portfolio
        from services.isolated_portfolio import get_isolated_portfolio
        isolated_portfolio_service = get_isolated_portfolio(db, kraken_service)
        isolated_portfolio.set_dependencies(isolated_portfolio_service)
        logger.info("✅ Isolated Portfolio Manager initialized")
        
        # Initialize Automated Trader
        automated_trader = AutomatedWeeklyTrader(
            db=db,
            kraken_service=kraken_service,
            ai_trainer=ai_trainer,
            gem_finder=gem_finder,
            alert_service=alert_service,
            isolated_portfolio=isolated_portfolio_service
        )
        logger.info("✅ Automated Weekly Trader initialized")
        
        # =====================================================================
        # PHASE 6: ML/DL Services
        # =====================================================================
        
        from services.adaptive_strategy import get_adaptive_strategy
        from services.performance_tracker import get_performance_tracker
        from services.regime_predictor import get_regime_predictor
        from services.enhanced_ai_engine import get_enhanced_ai
        from services.gem_ml_dl_predictor import get_gem_prediction_engine
        
        adaptive_strategy = get_adaptive_strategy(db, kraken_service, alert_service)
        performance_tracker = get_performance_tracker(db)
        regime_pred = get_regime_predictor(db)
        enhanced_ai = get_enhanced_ai(db)
        gem_ml_dl = get_gem_prediction_engine(db)
        
        # Update automated trader with ML services
        automated_trader.adaptive_strategy = adaptive_strategy
        automated_trader.regime_predictor = regime_pred
        automated_trader.performance_tracker = performance_tracker
        automated_trader.gem_ml_dl = gem_ml_dl
        logger.info("✅ ML/DL Services initialized")
        
        # =====================================================================
        # PHASE 7: Background Tasks & Scheduler
        # =====================================================================
        
        from services.background_tasks import get_task_manager
        from services.scheduler_service import SchedulerService
        from services.historical_trainer import HistoricalTrainer
        from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
        
        task_manager = get_task_manager(db)
        bg_tasks.set_dependencies(db, task_manager)
        automated_trader.task_manager = task_manager
        logger.info("✅ Background Task Manager initialized")
        
        historical_trainer = HistoricalTrainer(db)
        enhanced_trainer = EnhancedHistoricalTrainer(db)
        
        scheduler_service = SchedulerService(
            db=db,
            growth_engine=growth_engine,
            automated_trader=automated_trader,
            alert_service=alert_service
        )
        scheduler_service.set_trainers(historical_trainer, enhanced_trainer)
        logger.info("✅ Scheduler Service initialized")
        
        # Stop-Loss Automation
        from services.stop_loss_automation import get_stop_loss_automation
        stop_loss_service = get_stop_loss_automation(
            db=db,
            kraken_service=kraken_service,
            isolated_portfolio=isolated_portfolio_service,
            alert_service=alert_service
        )
        scheduler_service.set_stop_loss_automation(stop_loss_service)
        await scheduler_service.add_stop_loss_job(interval_minutes=5)
        stop_loss.set_dependencies(stop_loss_service, isolated_portfolio_service)
        logger.info("✅ Stop-Loss Automation initialized")
        
        # =====================================================================
        # PHASE 8: Prediction Enhancement Services
        # =====================================================================
        
        from services.order_book_analyzer import get_order_book_analyzer
        from services.on_chain_analytics import get_on_chain_analytics
        from services.social_sentiment_pipeline import get_social_sentiment
        from services.transformer_predictor import get_transformer_predictor
        from services.rl_trading_agent import get_rl_agent
        from services.cross_asset_correlation import get_cross_asset_correlation
        from services.advanced_technical_analysis import get_advanced_ta
        
        order_book_analyzer = get_order_book_analyzer(db)
        on_chain_analytics = get_on_chain_analytics(db)
        social_sentiment_service = get_social_sentiment(db)
        transformer_predictor = get_transformer_predictor(db)
        rl_trading_agent = get_rl_agent(db)
        cross_asset_correlation = get_cross_asset_correlation(db)
        advanced_ta = get_advanced_ta(db)
        
        # Inject task manager into RL agent
        rl_trading_agent.set_task_manager(task_manager)
        
        # Set prediction enhancement dependencies
        prediction_enhancements.set_dependencies(
            order_book=order_book_analyzer,
            on_chain=on_chain_analytics,
            social_sentiment=social_sentiment_service,
            transformer=transformer_predictor,
            rl_agent=rl_trading_agent,
            cross_asset=cross_asset_correlation,
            advanced_ta=advanced_ta
        )
        logger.info("✅ Prediction Enhancements initialized (8 services)")
        
        # Inject prediction services into automated trader
        automated_trader.prediction_services = {
            'order_book': order_book_analyzer,
            'on_chain': on_chain_analytics,
            'social': social_sentiment_service,
            'transformer': transformer_predictor,
            'rl_agent': rl_trading_agent,
            'cross_asset': cross_asset_correlation,
            'advanced_ta': advanced_ta
        }
        logger.info("✅ Automated Trader updated with Prediction Services")
        
        # =====================================================================
        # PHASE 9: Additional Services
        # =====================================================================
        
        from services.paper_trading_simulator import get_paper_trader
        paper_trader = get_paper_trader(db, enhanced_ai, regime_pred)
        paper_trading.set_dependencies(paper_trader)
        logger.info("✅ Paper Trading Simulator initialized")
        
        from services.portfolio_visualization import get_portfolio_viz
        portfolio_viz_service = get_portfolio_viz(db, kraken_service, isolated_portfolio_service)
        portfolio_viz.set_dependencies(portfolio_viz_service)
        logger.info("✅ Portfolio Visualization initialized")
        
        from services.custom_strategy_builder import get_strategy_builder
        strategy_builder = get_strategy_builder(db)
        strategy_builder_routes.set_dependencies(strategy_builder, chat_service)
        logger.info("✅ Custom Strategy Builder initialized")
        
        from services.ohlcv_data_manager import get_ohlcv_manager
        ohlcv_manager = get_ohlcv_manager(db)
        await ohlcv_manager.ensure_indexes()
        ohlcv_routes.set_dependencies(ohlcv_manager)
        logger.info("✅ OHLCV Data Manager initialized")
        
        # Push Notification Service
        from services.push_notification_service import get_push_service
        push_notification = get_push_service(db)
        automated_trader.notification_service = push_notification
        logger.info("✅ Push Notification Service initialized")
        
        # =====================================================================
        # PHASE 10: Training History & Scheduler
        # =====================================================================
        
        from services.training_history import get_training_history_service
        training_history = get_training_history_service(db)
        await training_history.ensure_indexes()
        training_history_routes.set_dependencies(training_history)
        rl_trading_agent.set_history_service(training_history)
        logger.info("✅ Training History Service initialized")
        
        from services.training_scheduler import get_training_scheduler
        training_scheduler = get_training_scheduler(db)
        
        # Register trainers
        async def train_rl(episodes=100, **kwargs):
            return await rl_trading_agent.train_background(episodes=episodes)
        
        async def train_transformer(**kwargs):
            return await transformer_predictor.train()
        
        async def train_regime(**kwargs):
            return await regime_pred.train_models()
        
        training_scheduler.register_trainer("rl_agent", train_rl)
        training_scheduler.register_trainer("transformer", train_transformer)
        training_scheduler.register_trainer("regime", train_regime)
        
        await training_scheduler.start()
        training_scheduler_routes.set_dependencies(training_scheduler)
        logger.info("✅ Training Scheduler initialized (3 trainers)")
        
        # =====================================================================
        # PHASE 11: Set Route Dependencies & Start Scheduler
        # =====================================================================
        
        # Set Kraken route dependencies
        kraken.set_dependencies(
            kraken_service=kraken_service,
            ai_trainer=ai_trainer,
            gem_finder=gem_finder,
            growth_engine=growth_engine,
            automated_trader=automated_trader,
            alert_service=alert_service
        )
        
        # Set other route dependencies
        enhanced_ai.set_dependencies(enhanced_ai, performance_tracker)
        regime.set_dependencies(regime_pred, adaptive_strategy)
        gem_ml_dl.set_dependencies(gem_ml_dl)
        
        # Start scheduler
        await scheduler_service.start()
        await scheduler_service.add_portfolio_snapshot_job(interval_hours=6)
        logger.info("✅ Portfolio Snapshots enabled (every 6 hours)")
        
        await scheduler_service.add_auto_retrain_job(hour=2, minute=0)
        logger.info("✅ Auto-Retrain enabled (daily at 2:00 UTC)")
        
        _services_initialized = True
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        raise


# =============================================================================
# STARTUP / SHUTDOWN EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("\n" + "="*50)
    logger.info("🚀 AI Crypto Trading Platform Starting...")
    logger.info("="*50 + "\n")
    
    # Delay initialization to allow health checks to pass first
    asyncio.create_task(delayed_init())


async def delayed_init():
    """Initialize services after startup completes"""
    await asyncio.sleep(1)
    await initialize_services()


@app.on_event("shutdown")
async def shutdown_db_client():
    """Cleanup on shutdown"""
    client.close()
    logger.info("Database connection closed")
