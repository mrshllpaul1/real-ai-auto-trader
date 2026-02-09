from fastapi import FastAPI, APIRouter, Response
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import logging
from health import check_database_connection

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - Use environment variable (Emergent provides this in deployment)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'crypto_trading_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# API version constant
API_VERSION = "1.0.0"

# Create the main app
app = FastAPI(
    title="AI Crypto Trading API",
    description="Real money AI-powered cryptocurrency auto trading platform",
    version=API_VERSION
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Health check endpoints - Must respond fast
@app.get("/health")
async def health_check(response: Response):
    """Health check endpoint for deployment"""
    db_status = await check_database_connection(client)
    _apply_health_status(response, db_status["status"])
    return {"status": db_status["status"], "database": db_status["database"], "version": API_VERSION}

@app.get("/")
async def root_health():
    """Root health check"""
    return {"status": "ok", "service": "ai-crypto-trading"}

# Create API router
api_router = APIRouter(prefix="/api")

@api_router.get("/health")
async def api_health_check(response: Response):
    """API health check endpoint"""
    db_status = await check_database_connection(client)
    _apply_health_status(response, db_status["status"])
    return {"status": db_status["status"], "database": db_status["database"], "version": API_VERSION}

@api_router.get("/")
async def root():
    return {
        "message": "AI Crypto Trading API",
        "status": "operational",
        "features": ["AI-powered trading", "Paper & Real trading", "Growth Engine"]
    }

# Import routes
from routes import auth, trading, strategies, market, risk, learning, news, training
from routes import auto_trading, allocation, scanner, auto_execute, backtest, rebalance
from routes import social, notifications, alerts, email, ai_portfolio, ai_selection
from routes import gems, auto_trade, growth, scheduler, budget, journal, ai_decisions

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


def _apply_health_status(response: Response, status: str):
    """Set HTTP status code based on health status string (expected: 'healthy' or 'unhealthy')."""
    if status not in {"healthy", "unhealthy"}:
        logger.warning("Unexpected health status value: %s", status)
    response.status_code = 200 if status == "healthy" else 503


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
        from services.social_sentiment import SocialSentimentAnalyzer
        from services.automated_trader import AutomatedWeeklyTrader
        from services.growth_engine import AggressiveGrowthEngine
        from services.scheduler_service import SchedulerService
        from services.budget_manager import BudgetManager
        from services.trading_journal import TradingJournalService
        from services.historical_trainer import HistoricalTrainer
        from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
        
        # Initialize base services
        market_service = MarketDataService()
        news_service = CryptoNewsAggregator()
        
        # Kraken service (optional)
        kraken_api_key = os.getenv('KRAKEN_API_KEY')
        kraken_api_secret = os.getenv('KRAKEN_API_SECRET')
        kraken_service = None
        if kraken_api_key and kraken_api_secret:
            kraken_auth = KrakenAuthenticator(kraken_api_key, kraken_api_secret)
            kraken_service = KrakenTradeService(kraken_auth)
            logger.info("✅ Kraken service initialized")
        
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
        
        # AI Trainer
        ai_trainer = AIWeeklyTrainer(db)
        
        # Alert Service
        alert_service = AlertService(db)
        
        # Sentiment Analyzer
        sentiment_analyzer = SocialSentimentAnalyzer(db)
        
        # Automated Trader
        automated_trader = AutomatedWeeklyTrader(
            db=db, kraken_service=kraken_service, ai_trainer=ai_trainer,
            gem_finder=gem_finder, alert_service=alert_service
        )
        auto_trade.set_dependencies(db, automated_trader, alert_service, sentiment_analyzer)
        
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
        
        # Start scheduler
        await scheduler_service.start()
        
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
