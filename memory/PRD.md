# AI Crypto Trading Platform - Product Requirements Document

## Original Problem Statement
Build a real money AI crypto auto trading app that learns and develops optimal weekly trading strategies. Ultimate goal: Turn $500 into $100,000.

## Core Requirements
- AI trained on REAL historical crypto market data (NEVER simulated)
- Continuously learning from trading performance week-by-week
- Ability to search for "hidden gems" with 10-100x potential
- Support both real-money and paper trading with budget controls
- Kraken exchange integration for live trading
- **Dynamic coin universe** - AI can discover and add new coins

---

## What's Been Implemented (Feb 2, 2026 - Session 4)

### ✅ AI Retrained with Sentiment Parameters (Feb 2, 2026)
- [x] **Updated AI Weekly Trainer** with sentiment integration:
  - Sentiment weight: **12%** of selection criteria
  - Momentum: 18%, Volume: 18%, Trend: 18%
  - Volatility: 13%, Historical: 13%, Category: 8%
- [x] **Enhanced portfolio selection** - Now uses sentiment to boost/penalize candidates
- [x] **New signal weights** - Added `bullish_news` and `bearish_news` signals
- [x] **Sentiment accuracy tracking** - Tracks bullish/bearish prediction accuracy
- [x] **New API endpoints**:
  - `GET /api/training/ai-weights` - View current AI weights
  - `POST /api/training/update-weights` - Manually adjust weights
- [x] **Training stats**: 578 weeks trained, meme category top performer (77.4 score)
- [x] **GPT-5.2 active** - Using Emergent LLM for real-time sentiment analysis

### ✅ CryptoPanic News Feed Integration (Feb 2, 2026)
- [x] **Installed cryptopanic library** - `pip install cryptopanic==0.1.0`
- [x] **Enhanced sentiment service** - Uses CryptoPanic library for news fetching
- [x] **Additional data extraction**:
  - Panic score
  - Vote sentiment (bullish/bearish from community votes)
  - Currencies mentioned in news
  - Trending/rising/hot news filters
- [x] **New API endpoints**:
  - `GET /api/sentiment/trending` - Trending/rising news
  - `GET /api/sentiment/news/bullish` - Bullish news filter
  - `GET /api/sentiment/news/bearish` - Bearish news filter
- [x] **Frontend component** - CryptoNewsFeed with Trending/Bullish/Bearish tabs
- [x] **CryptoPanic attribution** - Proper credit to data source

**Setup Required:** Register at `cryptopanic.com/developers/api/` (free tier) and add `CRYPTOPANIC_API_KEY` to `/app/backend/.env`

### ✅ AI News Sentiment Analysis (Feb 2, 2026)
- [x] **Comprehensive sentiment service** (`ai_news_sentiment.py`) - Analyzes news for all coins
- [x] **LLM-powered analysis** - Uses GPT-5.2 via Emergent LLM Key for sentiment scoring
- [x] **News sources** - CryptoPanic API + CoinGecko status updates
- [x] **Sentiment scoring** - 0-100 scale with bullish/bearish/neutral labels
- [x] **Market sentiment** - Weighted average of top coins (BTC, ETH, BNB, SOL, XRP)
- [x] **Integrated into:**
  - **Gem Finder** - 15% weight in gem scoring
  - **AI Discovery** - 15% weight in discovery scoring  
  - **Growth Engine** - Position sizing adjusted by sentiment
  - **Training** - Sentiment influences coin selection
- [x] **API endpoints:**
  - `GET /api/sentiment/coin/{coin_id}` - Individual coin sentiment
  - `POST /api/sentiment/batch` - Batch sentiment for multiple coins
  - `GET /api/sentiment/market` - Overall market sentiment
  - `GET /api/sentiment/history/{coin_id}` - Historical sentiment
- [x] **Frontend component** - MarketSentimentPanel on Growth Dashboard
- [x] **Caching** - 1-hour cache to avoid API spam

### ✅ AI Auto-Discovery (Feb 2, 2026)
- [x] **Proactive coin scanning** - Fetches trending, new, and top gaining coins from CoinGecko
- [x] **Multi-factor scoring** - Analyzes market cap, volume, momentum, community, and development
- [x] **Auto-add to universe** - Coins scoring above threshold are automatically added
- [x] **Approval workflow** - Optional "require approval" mode to review before adding
- [x] **Daily limits** - Configurable max daily additions to prevent spam
- [x] **Scheduled scans** - Runs daily at 10 AM via scheduler
- [x] **Push notifications** - Alerts when AI discovers new coins
- [x] **API endpoints**:
  - `GET /api/ai-discovery/stats` - Discovery statistics
  - `POST /api/ai-discovery/scan` - Run manual scan
  - `GET /api/ai-discovery/pending` - Pending approvals
  - `POST /api/ai-discovery/approve/{coin_id}` - Approve discovery
  - `POST /api/ai-discovery/reject/{coin_id}` - Reject discovery
  - `GET/POST /api/ai-discovery/settings` - Manage settings
- [x] **Frontend component** - AIDiscoveryPanel on Growth Dashboard

### ✅ Push Notifications with Vibration (Feb 2, 2026)
- [x] **Removed SMS/Twilio** - No longer using SMS notifications
- [x] **Push notifications with vibration patterns**:
  - Critical: `[200, 100, 200, 100, 200, 100, 400]` - Long urgent pattern
  - High: `[200, 100, 200, 100, 400]` - Medium urgent pattern
  - Normal: `[200, 100, 200]` - Standard pattern
  - Low: `[100]` - Subtle single vibration
- [x] **Updated notification service** - Now stores vibration patterns in DB
- [x] **Updated service worker** - Handles vibration patterns for PWA
- [x] **Updated Settings UI** - New "Enable Vibration" toggle, removed SMS section
- [x] **Test Push button** - Replaced "Test SMS" button

### ✅ Dynamic Coin Universe (Feb 2, 2026)
- [x] **Database-backed coin universe** - Coins stored in MongoDB for persistence
- [x] **AI coin discovery** - AI can add new coins to the universe
- [x] **Complete CRUD API** - Add, view, update, deactivate coins
- [x] **Category management** - 15 categories including 'discovered' for AI finds
- [x] **Gem candidate expansion** - Dynamic gems include AI-discovered coins
- [x] **Scheduler integration** - Retraining uses dynamic universe
- [x] **Frontend component** - CoinUniverseManager on Growth Dashboard
- [x] **New API endpoints**:
  - `GET /api/ai-universe/stats` - Universe statistics
  - `GET /api/ai-universe/coins` - All active coins
  - `GET /api/ai-universe/coins/gems` - Gem candidates
  - `GET /api/ai-universe/coins/discovered` - AI-discovered coins
  - `POST /api/ai-universe/coins/ai-discover` - Add new coin via AI
  - `DELETE /api/ai-universe/coin/{coin_id}` - Deactivate coin
  - `GET /api/ai-universe/categories` - List categories
- [x] **Test coverage**: 14 tests, 100% pass rate
- [x] **Current universe**: 78 coins (77 base + 1 AI-discovered 'kaspa')

---

## What's Been Implemented (Feb 2, 2026 - Session 3)

### ✅ AI Confidence Threshold (NEW - Feb 2, 2026)
- [x] **Adjustable threshold** - Set minimum AI confidence for real trades (0-100%)
- [x] **Smart fallback** - Low confidence trades execute as paper-only
- [x] **Backend API**: `/api/budget/confidence-threshold`, `/api/budget/confidence-check`
- [x] **Frontend slider** - Visual control in Budget Protection card
- [x] **Integration with Growth Engine** - Trades below threshold auto-downgraded to paper

### ✅ AI Decision Visualization (NEW - Feb 2, 2026)
- [x] **Complete transparency dashboard** - See WHY AI makes each decision
- [x] **Factor performance analysis** - Momentum, Volume, Trend success rates
- [x] **Hidden gem candidates** - AI-identified 10x+ potential coins
- [x] **Detailed coin explanations** - Click any coin for full AI reasoning
- [x] **New API endpoints**: `/api/ai-decisions/recent`, `/api/ai-decisions/explain/{coin_id}`, `/api/ai-decisions/factors`

### ✅ Expanded Pytest Coverage (NEW - Feb 2, 2026)
- [x] **30+ unit tests** for critical services
- [x] Tests for: GrowthEngine, AutomatedTrader, AIWeeklyTrainer, AIPortfolioManager
- [x] Integration tests for all major API endpoints
- [x] Test files: `/app/backend/tests/test_services.py`, `/app/backend/tests/test_extended_services.py`

### ✅ Removed ALL Simulated Data (P1 COMPLETE - Feb 2, 2026)
- [x] **enhanced_historical_trainer.py** - Rewritten to use Twelve Data API only
- [x] **historical_trainer.py** - Rewritten to use real data only
- [x] **market_data_service.py** - Returns error instead of fake data
- [x] **news_service.py** - Returns empty list instead of fake news
- [x] **Data source: REAL_MARKET_DATA_ONLY** verified across all services

### ✅ Kraken Real Money Trading (ENABLED - Feb 2, 2026)
- [x] Kraken API keys configured and verified
- [x] Account balance confirmed: ~$1,000+ (USD + BTC + ETH + SOL)
- [x] Budget allocation: $500 protected limit
- [x] Real trading enabled with budget controls

### ✅ AI Training Complete (Feb 2, 2026)
- [x] **60,635 historical price records** from Twelve Data API
- [x] **2,035 trading patterns** identified
- [x] **201 hidden gems** found (172 are 3x+, 62 are 10x+)
- [x] **58.8% pattern success rate**

### ✅ Adaptive AI Coin Selection Engine
- [x] **Dynamic coin selection** - AI selects best 5 coins weekly
- [x] **Multi-factor analysis** - Momentum, Volatility, Volume, Trend, Sentiment
- [x] **Market condition adaptation** - Different strategies for market conditions

### ✅ News API (P1 - FIXED)
- [x] **Free Crypto News API** - Primary source, no API key required
- [x] **Real-time News** - Returns 50 actual news articles
- [x] **Multiple Sources** - CryptoPanic, CoinMarketCap as fallbacks
- [x] **Intelligent Fallback** - Simulated news only as last resort
- [x] **Sentiment Analysis** - Automatic sentiment inference from titles

### ✅ Market Data Service (P2 - FIXED)
- [x] **Caching Layer** - Reduces API calls, improves performance
- [x] **Timeout Handling** - 20s timeout with graceful degradation
- [x] **Fallback Data** - Generated realistic data when API unavailable
- [x] **Async Execution** - Non-blocking API calls via thread pool

### ✅ Trading Charts
- [x] **TradingView Lightweight Charts** - Professional candlestick charts
- [x] **Multiple Chart Types** - Candlestick, Line, Area
- [x] **Multiple Timeframes** - 1D, 7D, 30D, 90D, 1Y
- [x] **Coin Selector** - BTC, ETH, SOL, ADA, DOT, AVAX

### ✅ Price Alerts (NEW)
- [x] **Price Alert Service** - Create alerts for price thresholds
- [x] **Alert API** - CRUD operations for alerts
- [x] **Gem Alerts** - Auto-alerts for HIGH priority scanner gems
- [x] **SMS for HIGH Priority** - Text notifications for critical alerts

### ✅ News API Fix (NEW)
- [x] **Multiple Sources** - CryptoPanic, CoinGecko, CoinMarketCap
- [x] **Fallback System** - Simulated news when APIs fail
- [x] **Always Returns Data** - No more empty responses

### ✅ Concurrent Trading Modes (NEW)
- [x] **Paper + Real Trading** - Both modes supported simultaneously
- [x] **Mode Toggle UI** - Switch between paper and real in Auto Trading

### ✅ Enhanced Service Worker (NEW)
- [x] **Background Tasks** - 5-minute periodic checks
- [x] **Push Notifications** - Browser push for trade updates
- [x] **Gem Scanner Checks** - Background monitoring for HIGH alerts
- [x] **Alert Checking** - Periodic notification polling

### ✅ Portfolio Analytics Dashboard (NEW)
- [x] **Key Metrics** - Portfolio Value, P/L, Win Rate, Total Trades
- [x] **Performance Charts** - Cumulative returns, Trade-by-trade P/L
- [x] **Allocation View** - Pie chart with holdings breakdown
- [x] **AI Stats Tab** - Signal performance, execution status
- [x] **Trade History Tab** - Recent transactions list

---

## Architecture

```
/app/
├── backend/
│   ├── routes/
│   │   ├── growth.py           # Growth Engine API ($500→$100k)
│   │   ├── scheduler.py        # Scheduler/Autopilot API
│   │   ├── ai_universe.py      # Dynamic Coin Universe API (NEW)
│   │   ├── alerts.py           # Price alerts API
│   │   ├── notifications.py    # Push & SMS notifications
│   │   ├── scanner.py          # Gem scanner
│   │   ├── auto_execute.py     # Auto execution
│   │   ├── backtest.py         # Backtesting
│   │   ├── rebalance.py        # Portfolio rebalancing
│   │   └── social.py           # Social trading
│   └── services/
│       ├── dynamic_coin_universe.py # Dynamic Coin Universe Manager (NEW)
│       ├── growth_engine.py       # Aggressive Growth Engine
│       ├── scheduler_service.py   # APScheduler service (uses dynamic universe)
│       ├── gem_finder.py          # Updated to use dynamic universe
│       ├── ai_weekly_trainer.py   # Updated to use dynamic universe
│       ├── price_alerts.py        # Alert service
│       ├── notification_service.py
│       ├── news_service.py        # Fixed with fallbacks
│       ├── gem_scanner.py
│       └── auto_execution.py
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── GrowthDashboard.js  # $500→$100k Dashboard (includes CoinUniverseManager)
    │   │   ├── TradingView.js      # Candlestick charts
    │   │   ├── Analytics.js        # Enhanced dashboard
    │   │   ├── AdvancedFeatures.js
    │   │   ├── Guide.js
    │   │   └── Settings.js
    │   └── components/
    │       ├── CoinUniverseManager.js # Dynamic Coin Universe UI (NEW)
    │       └── AutopilotControl.js    # Scheduler UI
    └── public/
        └── service-worker.js   # Enhanced for background
```

---

## API Endpoints

### AI Universe (NEW)
- `GET /api/ai-universe/stats` - Get universe statistics
- `GET /api/ai-universe/coins` - Get all active coins
- `GET /api/ai-universe/coins/gems` - Get gem candidates
- `GET /api/ai-universe/coins/discovered` - Get AI-discovered coins
- `POST /api/ai-universe/coins/ai-discover` - Add coin via AI discovery
- `DELETE /api/ai-universe/coin/{coin_id}` - Deactivate coin
- `GET /api/ai-universe/categories` - Get all categories
- `GET /api/ai-universe/coins/category/{category}` - Get coins by category

### Alerts
- `POST /api/alerts/create` - Create price alert
- `GET /api/alerts/` - Get user alerts
- `DELETE /api/alerts/{alert_id}` - Delete alert
- `POST /api/alerts/check` - Check alerts against prices

### Notifications
- `GET /api/notifications/` - Get unread notifications
- `POST /api/notifications/test-push` - Test push
- `POST /api/notifications/test-sms` - Test SMS
- `GET/POST /api/notifications/settings`

---

## Known Limitations

1. **SMS Requires Twilio Credentials** - User must add to `.env`:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`

2. **Email Requires Resend API Key** - Add via /setup page:
   - `RESEND_API_KEY`

3. **CoinGecko Rate Limits** - Free tier has rate limits; caching and fallback mitigate this

---

## Environment Variables

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=crypto_trading_db
EMERGENT_LLM_KEY=sk-emergent-xxx
KRAKEN_API_KEY=xxx
KRAKEN_API_SECRET=xxx
COINMARKETCAP_API_KEY=xxx
COINSTATS_API_KEY=xxx
USER_PHONE_NUMBER=2104412761
TWILIO_ACCOUNT_SID=       # User must provide
TWILIO_AUTH_TOKEN=        # User must provide
TWILIO_PHONE_NUMBER=      # User must provide
```

---

## Completed Tasks This Session (Feb 2, 2026)
1. ✅ **P0 COMPLETED**: Growth Dashboard UI fully implemented
2. ✅ **P1 COMPLETED**: Scheduled Execution (Autopilot Mode)
3. ✅ **P2 COMPLETED**: Real Money Trading with Budget Protection
4. ✅ **P2 COMPLETED**: User-Guided Tutorial
5. ✅ **P3 COMPLETED**: AI Decision Visualization
6. ✅ **P3 COMPLETED**: Fixed `/api/learning/record-outcome` endpoint
7. ✅ **P3 COMPLETED**: Pytest tests for critical services
8. ✅ **NEW**: Trading Journal with AI Insights
   - Trade log with all entries
   - Daily/period performance stats
   - AI confidence accuracy analysis
   - Gem vs Regular trade comparison
   - Key AI insights generation
9. ✅ All Growth APIs working
10. ✅ All Scheduler APIs working
11. ✅ All Budget APIs working
12. ✅ All Journal APIs working

## Previous Session (Feb 2, 2026 - Earlier)
1. ✅ **P0 FIXED**: Removed scikit-learn/scipy - App now deployable
2. ✅ **P1 FIXED**: News API returns real data from free-crypto-news API
3. ✅ **P2 FIXED**: Market data with caching, timeouts, and fallbacks
4. ✅ Updated .gitignore to allow .env files for deployment
5. ✅ Created comprehensive test suite for all fixes
6. ✅ Verified all 11 backend tests pass
7. ✅ **AI PORTFOLIO MANAGER**: Created autonomous AI trading system
   - AI develops its own portfolio allocation strategy
   - Analyzes market conditions and news sentiment
   - Executes real money trades on Kraken
   - Auto-rebalances portfolio based on AI analysis
8. ✅ Created AI Portfolio frontend component for Auto Trading page
9. ✅ Fixed N+1 database queries in social trading service
10. ✅ Added query limits to prevent unbounded queries

## Previous Session Tasks (Feb 1, 2026)
1. ✅ Fixed AdvancedFeatures.js black screen
2. ✅ Added push notifications for completed trades
3. ✅ Added SMS notification framework for HIGH priority
4. ✅ Created complete Guide page
5. ✅ Implemented TradingView candlestick charts
6. ✅ Created price alerts service and API
7. ✅ Enhanced Analytics with portfolio dashboard
8. ✅ Updated service worker for background execution
9. ✅ Made app mobile-responsive
10. ✅ Created Setup page for API key management

---

## Future Enhancements
- Twilio SMS notifications (requires user credentials)
- Email notifications with Resend (requires user API key)
- Custom strategy builder UI

---

## New Routes Added
- `/journal` - Trading Journal with AI Insights

## Test Reports
- `/app/test_reports/iteration_3.json` - Latest test results (Feb 2, 2026)
- `/app/backend/tests/test_services.py` - Unit tests for critical services

---

## Session 3: Removed All Simulated Data (Feb 2, 2026)

### ✅ P1 COMPLETED: No Simulated Data Policy Enforced

The user's strict requirement that "this program will never use simulated market data under any circumstances" has been fully implemented:

**Files Fixed:**
1. **`/app/backend/services/enhanced_historical_trainer.py`** - REWRITTEN
   - Removed all `np.random` synthetic data generation
   - Now fetches REAL data from Twelve Data API
   - Falls back to database cache
   - Returns empty DataFrame if no real data available (NEVER fakes it)

2. **`/app/backend/services/historical_trainer.py`** - REWRITTEN  
   - Removed all synthetic price/volume generation
   - Integrated with Twelve Data service for real market data
   - Returns empty DataFrame if no real data available

3. **`/app/backend/services/market_data_service.py`** - FIXED
   - Removed fallback that generated fake historical data
   - Now returns error indicator when API unavailable
   - Never generates simulated prices

4. **`/app/backend/services/news_service.py`** - FIXED
   - Removed `_get_simulated_news()` function
   - Returns empty list when all news APIs fail
   - Never generates fake news articles

**Data Sources (Real Only):**
- Twelve Data API for historical OHLCV data
- CoinGecko for current prices and market data
- CryptoPanic for news
- CoinMarketCap for trending data

**Important:** The `simulate_week()` and `_simulate_trade()` methods in `ai_weekly_trainer.py` are LEGITIMATE - they simulate paper trades using REAL historical price data, not simulated market data.

---

## New Features Added (Feb 2, 2026 - Session 2)
1. ✅ **Trading Journal with AI Insights**
   - Track all trades with timestamps and AI reasoning
   - Daily/weekly/monthly performance summaries
   - AI confidence accuracy analysis
   - Gem vs Regular trade comparison
   - Factor performance breakdown
   - New route: `/journal`
   - New APIs: `/api/journal/entries`, `/api/journal/stats`, `/api/journal/ai-insights`, `/api/journal/daily`

