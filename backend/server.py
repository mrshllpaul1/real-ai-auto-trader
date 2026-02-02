from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from routes import auth, trading, strategies, market, risk, learning, news, training, auto_trading, allocation, scanner, auto_execute, backtest, rebalance, social, notifications, alerts, email, ai_portfolio


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="AI Crypto Trading API",
    description="Real money AI-powered cryptocurrency auto trading platform",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check
@api_router.get("/")
async def root():
    return {
        "message": "AI Crypto Trading API",
        "status": "operational",
        "features": [
            "AI-powered strategy generation",
            "Paper & Real trading",
            "Risk management",
            "Real-time market data",
            "Portfolio analytics"
        ]
    }

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
api_router.include_router(auto_execute.router, prefix="/auto-exec", tags=["Auto Execution & AI Learning"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["Backtesting"])
api_router.include_router(rebalance.router, prefix="/rebalance", tags=["Portfolio Rebalancing"])
api_router.include_router(social.router, prefix="/social", tags=["Social Trading"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Price Alerts"])
api_router.include_router(email.router, prefix="/email", tags=["Email Notifications"])
api_router.include_router(ai_portfolio.router, prefix="/ai-portfolio", tags=["AI Portfolio Manager"])

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize AI Portfolio Manager
from services.ai_portfolio_manager import AIPortfolioManager
from services.market_data_service import MarketDataService
from services.news_service import CryptoNewsAggregator
from services.kraken_service import KrakenAuthenticator, KrakenTradeService

# Set up services for AI Portfolio Manager
market_service = MarketDataService()
news_service = CryptoNewsAggregator()

# Initialize Kraken if credentials available
kraken_api_key = os.getenv('KRAKEN_API_KEY')
kraken_api_secret = os.getenv('KRAKEN_API_SECRET')
kraken_service = None

if kraken_api_key and kraken_api_secret:
    kraken_auth = KrakenAuthenticator(kraken_api_key, kraken_api_secret)
    kraken_service = KrakenTradeService(kraken_auth)
    logger.info("✅ Kraken service initialized for real trading")
else:
    logger.warning("⚠️ Kraken credentials not found - real trading disabled")

# Initialize AI Portfolio Manager
ai_portfolio_mgr = AIPortfolioManager(
    db=db,
    kraken_service=kraken_service,
    market_service=market_service,
    news_service=news_service
)

# Inject into routes
ai_portfolio.ai_portfolio_manager = ai_portfolio_mgr
logger.info("🤖 AI Portfolio Manager initialized")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()