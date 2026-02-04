from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import logging
import asyncio
import json

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - Use environment variable (Emergent provides this in deployment)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'crypto_trading_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Global service reference for trading routes
kraken_service = None

# Create the main app
app = FastAPI(
    title="AI Crypto Trading API",
    description="Real money AI-powered cryptocurrency auto trading platform",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Health check endpoints - Must respond fast
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root_health():
    """Root health check"""
    return {"status": "ok", "service": "ai-crypto-trading"}

# Create API router
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


# WebSocket Connection Manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

ws_manager = ConnectionManager()


@app.websocket("/ws/training")
async def websocket_training_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time training status updates.
    Sends updates every 3 seconds for active training tasks.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Get active tasks from task manager
            try:
                from services.background_tasks import get_task_manager
                task_manager = get_task_manager()
                
                if task_manager:
                    active_tasks = await task_manager.get_active_tasks()
                    
                    # Send update to this client
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


# Import routes
from routes import auth, trading, strategies, market, risk, learning, news, training
from routes import auto_trading, allocation, scanner, auto_execute, backtest, rebalance
from routes import social, notifications, alerts, email, ai_portfolio, ai_selection
from routes import gems, auto_trade, growth, scheduler, budget, journal, ai_decisions
from routes import ai_universe, ai_discovery, sentiment, cryptopanic, deep_learning, ai_chat
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

# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service references (initialized lazily)
_services_initialized = False


async def initialize_services():
    """Initialize all services - called after startup"""
    global _services_initialized
    if _services_initialized:
        return
    
    logger.info("🚀 Initializing services...")
    
    try:
        # Import services
        from services.ai_portfolio_manager import AIPortfolioManager
        from services.market_data_service import MarketDataService
        from services.news_service import CryptoNewsAggregator
        from services.kraken_service import KrakenAuthenticator, KrakenTradeService
        from services.adaptive_coin_selector import AdaptiveCoinSelector
        from services.weekly_simulation import WeeklySimulationRunner
        from services.gem_finder import HiddenGemFinder
        from services.ai_weekly_trainer import AIWeeklyTrainer
        from services.alert_service import AlertService
        from services.social_sentiment import get_sentiment_scraper
        from services.automated_trader import AutomatedWeeklyTrader
        from services.growth_engine import AggressiveGrowthEngine
        from services.scheduler_service import SchedulerService
        from services.budget_manager import BudgetManager
        from services.trading_journal import TradingJournalService
        from services.historical_trainer import HistoricalTrainer
        from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
        from services.dynamic_coin_universe import DynamicCoinUniverseManager, set_universe_manager
        from services.ai_coin_discovery import AICoinDiscoveryService, set_discovery_service
        from services.ai_news_sentiment import AINewsSentimentService, set_sentiment_service
        
        # Initialize Dynamic Coin Universe (FIRST - other services depend on it)
        universe_manager = DynamicCoinUniverseManager(db)
        await universe_manager.initialize()
        set_universe_manager(universe_manager)
        ai_universe.set_dependencies(universe_manager)
        logger.info("✅ Dynamic Coin Universe initialized")
        
        # Initialize AI Sentiment Service
        sentiment_service = AINewsSentimentService(db)
        set_sentiment_service(sentiment_service)
        sentiment.set_dependencies(sentiment_service)
        logger.info("✅ AI Sentiment Service initialized")
        
        # Initialize CryptoPanic Service
        from services.cryptopanic_service import CryptoPanicService, set_cryptopanic_service
        cryptopanic_service = CryptoPanicService()
        set_cryptopanic_service(cryptopanic_service)
        
        # Initialize news aggregator for fallback
        news_aggregator = CryptoNewsAggregator()
        
        # Pass both to cryptopanic routes (with fallback support)
        cryptopanic.set_dependencies(cryptopanic_service, news_aggregator)
        logger.info("✅ CryptoPanic Service initialized with fallback")
        
        # Initialize AI Discovery Service
        discovery_service = AICoinDiscoveryService(db, universe_manager)
        set_discovery_service(discovery_service)
        ai_discovery.set_dependencies(discovery_service)
        logger.info("✅ AI Discovery Service initialized")
        
        # Initialize base services
        market_service = MarketDataService()
        news_service = CryptoNewsAggregator()
        
        # Initialize Deep Learning AI
        deep_learning.set_dependencies(db, market_service)
        logger.info("✅ Deep Learning AI initialized")
        
        # Initialize AI Chat Service
        from services.ai_chat_service import AIChatService
        chat_service = AIChatService(db, market_service, news_service)
        ai_chat.set_dependencies(db, chat_service)
        logger.info("✅ AI Chat Service initialized")
        
        # Initialize AI Universe Expander
        from services.ai_universe_expander import get_universe_expander
        universe_expander = get_universe_expander(db, market_service)
        ai_universe_expand.set_dependencies(db, market_service, universe_expander)
        logger.info("✅ AI Universe Expander initialized")
        
        # Initialize Hidden Gem Predictor
        from services.hidden_gem_predictor import get_gem_predictor
        from services.deep_learning_ai import get_deep_learning_ai
        deep_ai = get_deep_learning_ai(db)
        hidden_gem_predictor = get_gem_predictor(db, market_service, deep_ai)
        gem_predictor.set_dependencies(db, hidden_gem_predictor)
        ai_chat.set_gem_predictor(hidden_gem_predictor)
        logger.info("✅ Hidden Gem Predictor initialized")
        
        # Initialize Historical Simulation
        simulation.set_dependencies(db, market_service)
        logger.info("✅ Historical Simulation initialized")
        
        # Initialize Ensemble AI & Universe Optimizer
        from services.ensemble_ai import get_ensemble_predictor, get_universe_optimizer
        ensemble_predictor = get_ensemble_predictor(db, market_service, deep_ai)
        universe_optimizer = get_universe_optimizer(db, market_service, ensemble_predictor, deep_ai)
        ensemble.set_dependencies(db, market_service, ensemble_predictor, universe_optimizer, deep_ai)
        logger.info("✅ Ensemble AI & Universe Optimizer initialized")
        
        # Kraken service (optional)
        global kraken_service
        kraken_api_key = os.getenv('KRAKEN_API_KEY')
        kraken_api_secret = os.getenv('KRAKEN_API_SECRET')
        if kraken_api_key and kraken_api_secret:
            kraken_auth = KrakenAuthenticator(kraken_api_key, kraken_api_secret)
            kraken_service = KrakenTradeService(kraken_auth)
            logger.info("✅ Kraken service initialized")
            # Set Kraken service for AI Chat trading
            ai_chat.set_kraken_service(kraken_service)
        else:
            kraken_service = None
            logger.warning("⚠️ Kraken service not initialized - missing API keys")
        
        # AI Portfolio Manager
        ai_portfolio_mgr = AIPortfolioManager(db=db, kraken_service=kraken_service, market_service=market_service, news_service=news_service)
        ai_portfolio.ai_portfolio_manager = ai_portfolio_mgr
        
        # AI Coin Selection
        coin_selector = AdaptiveCoinSelector(db, market_service, news_service)
        simulation_runner = WeeklySimulationRunner(db)
        ai_selection.set_dependencies(db, coin_selector, simulation_runner)
        
        # Gem Finder
        gem_finder = HiddenGemFinder(db)
        gems.set_dependencies(db, gem_finder)
        
        # Gem Backtester
        from services.gem_backtester import get_gem_backtester
        gem_backtester = get_gem_backtester(db, gem_predictor)
        gem_predictor_routes.set_backtester(gem_backtester)
        logger.info("✅ Gem Backtester initialized")
        
        # AI Trainer
        ai_trainer = AIWeeklyTrainer(db)
        
        # Alert Service
        alert_service = AlertService(db)
        
        # Sentiment Analyzer (use new scraper)
        sentiment_analyzer = get_sentiment_scraper(db)
        
        # Isolated Portfolio Manager (initialize BEFORE automated trader)
        from services.isolated_portfolio import get_isolated_portfolio
        isolated_portfolio_mgr = get_isolated_portfolio(db, kraken_service)
        isolated_portfolio.set_dependencies(db, isolated_portfolio_mgr)
        logger.info("✅ Isolated Portfolio Manager initialized")
        
        # Automated Trader - now with budget isolation
        automated_trader = AutomatedWeeklyTrader(
            db=db, kraken_service=kraken_service, ai_trainer=ai_trainer,
            gem_finder=gem_finder, alert_service=alert_service,
            isolated_portfolio=isolated_portfolio_mgr
        )
        auto_trade.set_dependencies(db, automated_trader, alert_service, sentiment_analyzer)
        
        # Kraken Routes
        kraken_routes.set_dependencies(db, kraken_service, isolated_portfolio_mgr, automated_trader)
        logger.info("✅ Kraken Routes initialized")
        
        # Growth Engine
        growth_engine = AggressiveGrowthEngine(
            db=db, kraken_service=kraken_service, gem_finder=gem_finder,
            ai_trainer=ai_trainer, alert_service=alert_service
        )
        growth.set_dependencies(db, growth_engine)
        
        # Scheduler
        scheduler_service = SchedulerService(
            db=db, growth_engine=growth_engine,
            automated_trader=automated_trader, alert_service=alert_service
        )
        
        # Add trainers for weekly retraining
        historical_trainer = HistoricalTrainer(db)
        enhanced_trainer = EnhancedHistoricalTrainer(db)
        scheduler_service.set_trainers(historical_trainer, enhanced_trainer)
        
        scheduler.set_dependencies(scheduler_service)
        
        # Budget Manager
        budget_manager = BudgetManager(db)
        budget.set_dependencies(budget_manager)
        growth_engine.budget_manager = budget_manager
        
        # Trading Journal
        journal_service = TradingJournalService(db)
        journal.set_dependencies(journal_service)
        
        # CoinDesk News Service
        from services.coindesk_service import get_coindesk_service, get_cryptocompare_service
        coindesk_service = get_coindesk_service()
        coindesk.set_dependencies(coindesk_service)
        logger.info("✅ CoinDesk News service initialized")
        
        # CryptoCompare Historical Data Service
        cryptocompare_service = get_cryptocompare_service()
        from services.historical_data_downloader import get_historical_downloader
        historical_downloader = get_historical_downloader(db)
        historical_data.set_dependencies(db, historical_downloader, cryptocompare_service)
        logger.info("✅ CryptoCompare Historical Data service initialized")
        
        # AI Learning Loop Service
        from services.ai_learning_loop import get_learning_loop_service
        learning_loop_service = get_learning_loop_service(db)
        ai_learning_loop.set_dependencies(db, learning_loop_service)
        logger.info("✅ AI Learning Loop service initialized")
        
        # Event Correlation Engine & Historical Events Database
        from services.event_correlation_engine import get_correlation_engine
        from services.historical_events_db import get_historical_events_db
        correlation_engine = get_correlation_engine(db, coindesk_service, cryptocompare_service)
        events_db = get_historical_events_db(db, coindesk_service, correlation_engine)
        events.set_dependencies(db, correlation_engine, events_db)
        logger.info("✅ Event Correlation Engine initialized")
        logger.info("✅ Historical Events Database initialized")
        
        # Event Triggers Service for Automated Trading
        from services.event_triggers import get_event_trigger_service
        trigger_service = get_event_trigger_service(
            db=db,
            coindesk_service=coindesk_service,
            correlation_engine=correlation_engine,
            kraken_service=kraken_service,
            alert_service=alert_service
        )
        event_triggers.set_dependencies(db, trigger_service)
        logger.info("✅ Event Trigger Service initialized")
        
        # Kraken Universe Service
        from services.kraken_universe import get_kraken_universe
        kraken_universe_service = get_kraken_universe(db)
        kraken_universe.set_dependencies(kraken_universe_service)
        logger.info("✅ Kraken Universe Service initialized")
        
        # CoinDesk Universe Service
        from services.coindesk_universe import get_coindesk_universe
        coindesk_universe_service = get_coindesk_universe(db)
        coindesk_universe.set_dependencies(coindesk_universe_service)
        logger.info("✅ CoinDesk Universe Service initialized")
        
        # Adaptive Strategy Engine
        from services.adaptive_strategy import get_adaptive_strategy
        adaptive_strategy_engine = get_adaptive_strategy(db, kraken_service, alert_service)
        adaptive_strategy.set_dependencies(db, adaptive_strategy_engine)
        logger.info("✅ Adaptive Strategy Engine initialized")
        
        # Performance Tracker & Regime Predictor
        from services.performance_tracker import get_performance_tracker
        from services.regime_predictor import get_regime_predictor
        perf_tracker = get_performance_tracker(db)
        regime_pred = get_regime_predictor(db)
        performance.set_dependencies(db, perf_tracker, regime_pred)
        logger.info("✅ Performance Tracker initialized")
        logger.info("✅ Regime Prediction Engine initialized")
        
        # Update automated trader with adaptive strategy and regime predictor
        automated_trader.adaptive_strategy = adaptive_strategy_engine
        automated_trader.regime_predictor = regime_pred
        automated_trader.performance_tracker = perf_tracker
        logger.info("✅ Automated Trader updated with adaptive strategy & ML regime prediction")
        
        # Enhanced AI Engine
        from services.enhanced_ai_engine import get_enhanced_ai
        enhanced_ai = get_enhanced_ai(db)
        enhanced_ai_routes.set_dependencies(db, enhanced_ai, regime_pred)
        logger.info("✅ Enhanced AI Engine initialized (Ensemble + MTF + Sentiment + Whale + Risk)")
        
        # Paper Trading Simulator
        from services.paper_trading_simulator import get_paper_trader
        paper_trader = get_paper_trader(db, enhanced_ai, regime_pred)
        paper_trading_routes.set_dependencies(db, paper_trader)
        logger.info("✅ Paper Trading Simulator initialized")
        
        # Social Sentiment Scraper
        from services.social_sentiment import get_sentiment_scraper
        sentiment_scraper = get_sentiment_scraper(db)
        social_sentiment.set_dependencies(db, sentiment_scraper)
        logger.info("✅ Social Sentiment Scraper initialized")
        
        # Stop-Loss Automation
        from services.stop_loss_automation import get_stop_loss_automation
        stop_loss_automation = get_stop_loss_automation(
            db=db,
            kraken_service=kraken_service,
            isolated_portfolio=isolated_portfolio_mgr,
            alert_service=alert_service
        )
        stop_loss_routes.set_dependencies(db, stop_loss_automation)
        scheduler_service.set_stop_loss_automation(stop_loss_automation)
        
        # Add stop-loss check job (every 5 minutes)
        await scheduler_service.add_stop_loss_job(interval_minutes=5)
        logger.info("✅ Stop-Loss Automation initialized (checking every 5 minutes)")
        
        # Gem ML/DL Prediction Engine
        from services.gem_ml_dl_predictor import get_gem_prediction_engine
        gem_ml_dl_engine = get_gem_prediction_engine(db)
        gem_ml_dl.set_dependencies(db, gem_ml_dl_engine)
        logger.info("✅ Gem ML/DL Prediction Engine initialized")
        
        # Portfolio Visualization
        portfolio_visualization.set_dependencies(db, isolated_portfolio_mgr)
        portfolio_visualization.set_scheduler(scheduler_service)
        logger.info("✅ Portfolio Visualization initialized")
        
        # Background Task Manager
        from services.background_tasks import get_task_manager
        task_manager = get_task_manager(db)
        bg_tasks.set_dependencies(db, task_manager)
        logger.info("✅ Background Task Manager initialized")
        
        # P1 & P2: Inject ML/DL gem predictor and task manager into automated trader
        automated_trader.gem_ml_dl = gem_ml_dl_engine
        automated_trader.task_manager = task_manager
        logger.info("✅ Automated Trader updated with ML/DL Gem Predictor & Background Task Manager")
        
        # Initialize Prediction Enhancement Services (All 8 enhancements)
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
        
        # Inject task manager into RL agent for background training
        rl_trading_agent.set_task_manager(task_manager)
        
        # Set dependencies for prediction enhancements route
        prediction_enhancements.set_dependencies(
            db=db,
            order_book=order_book_analyzer,
            on_chain=on_chain_analytics,
            social_sentiment=social_sentiment_service,
            transformer=transformer_predictor,
            rl_agent=rl_trading_agent,
            cross_asset=cross_asset_correlation,
            advanced_ta=advanced_ta
        )
        logger.info("✅ Prediction Enhancements initialized (8 services)")
        
        # Inject prediction services into automated trader for enhanced coin selection
        automated_trader.prediction_services = {
            'order_book': order_book_analyzer,
            'on_chain': on_chain_analytics,
            'social': social_sentiment_service,
            'transformer': transformer_predictor,
            'rl_agent': rl_trading_agent,
            'cross_asset': cross_asset_correlation,
            'advanced_ta': advanced_ta
        }
        logger.info("✅ Automated Trader updated with Prediction Enhancement Services")
        
        # Initialize Custom Strategy Builder with AI Chat integration
        from services.custom_strategy_builder import get_strategy_builder
        strategy_builder = get_strategy_builder(db, chat_service)  # Use chat_service instance
        strategy_builder_routes.set_dependencies(db, strategy_builder)
        logger.info("✅ Custom Strategy Builder initialized (AI-assisted)")
        
        # Initialize Push Notification Service
        from services.push_notification_service import get_notification_service
        push_notification = get_notification_service(db)
        automated_trader.notification_service = push_notification
        logger.info("✅ Push Notification Service initialized")
        
        # Initialize OHLCV Data Manager
        from services.ohlcv_data_manager import get_ohlcv_manager
        ohlcv_manager = get_ohlcv_manager(db)
        await ohlcv_manager.ensure_indexes()
        ohlcv_routes.set_dependencies(ohlcv_manager)
        logger.info("✅ OHLCV Data Manager initialized")
        
        # Initialize Training History Service
        from services.training_history import get_training_history_service
        training_history = get_training_history_service(db)
        await training_history.ensure_indexes()
        training_history_routes.set_dependencies(training_history)
        
        # Inject history service into RL agent
        rl_trading_agent.set_history_service(training_history)
        logger.info("✅ Training History Service initialized")
        
        # Initialize Training Scheduler
        from services.training_scheduler import get_training_scheduler
        training_scheduler = get_training_scheduler(db)
        
        # Register trainers for schedulable models
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
        logger.info("✅ Training Scheduler initialized (3 trainers registered)")
        
        # Start scheduler
        await scheduler_service.start()
        
        # Add automatic portfolio snapshot job (every 6 hours)
        await scheduler_service.add_portfolio_snapshot_job(interval_hours=6)
        logger.info("✅ Automatic Portfolio Snapshots enabled (every 6 hours)")
        
        # Add auto-retrain job (daily at 2 AM UTC)
        await scheduler_service.add_auto_retrain_job(hour=2)
        logger.info("✅ Auto-Retrain Models enabled (daily at 2:00 UTC)")
        
        _services_initialized = True
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Service initialization error: {e}")


@app.on_event("startup")
async def startup_event():
    """Fast startup - defer heavy initialization"""
    logger.info("🚀 Application starting...")
    # Initialize services in background after a short delay
    import asyncio
    asyncio.create_task(delayed_init())


async def delayed_init():
    """Initialize services after startup completes"""
    import asyncio
    await asyncio.sleep(2)  # Let health check pass first
    await initialize_services()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
