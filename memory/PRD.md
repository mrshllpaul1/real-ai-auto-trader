# AI Crypto Trading Platform - Product Requirements Document

## Original Problem Statement
Build a real money AI crypto auto trading app that learns and develops optimal weekly trading strategies.

## Core Requirements
- AI trained on historical crypto market and news data
- Continuously learning from trading performance
- Ability to search for "hidden gems" with 10-100x potential
- Support both real-money and paper trading simultaneously
- PWA capable of running tasks in background on mobile

---

## What's Been Implemented (Feb 2, 2026)

### ✅ Adaptive AI Coin Selection Engine (NEW - Feb 2, 2026)
- [x] **Dynamic coin selection** - AI selects best 5 coins weekly based on market conditions
- [x] **Multi-factor analysis** - Momentum, Volatility, Volume, Trend, Sentiment scoring
- [x] **Market condition adaptation** - Different strategies for bullish/bearish/neutral markets
- [x] **Weekly simulation** - Fixed $10k/week capital (no unrealistic compounding)
- [x] **Real historical data** - 5,124 records from 14 coins via CoinGecko API
- [x] **Frontend UI** - Interactive coin selection with detailed score breakdown
- [x] **Simulation results display** - Win rate, P/L, best/worst week, annual breakdown

### ✅ Deployment Ready (P0 - FIXED)
- [x] Removed scikit-learn dependency for deployment compatibility
- [x] Removed scipy dependency
- [x] Application now deployable to Emergent platform

### ✅ Core AI & Trading
- [x] AI training pipeline with hidden gems detection (10x-100x potential)
- [x] Real-time market scanner for opportunity detection
- [x] Auto-execution engine for paper trading
- [x] Self-improving AI that learns from trade outcomes
- [x] Signal weight optimization based on performance

### ✅ Advanced Features
- [x] **Backtesting Interface** - Test strategies against historical data
- [x] **Portfolio Rebalancing** - Automated rebalancing to target allocations
- [x] **Social Trading** - Leaderboard of top traders

### ✅ Notification System
- [x] **Push Notifications** - In-app notifications for completed trades
- [x] **Notification Center** - Bell icon in sidebar with dropdown
- [x] **SMS Integration (Twilio)** - Framework ready, requires user credentials
- [x] **Settings UI** - Configure notification preferences

### ✅ Documentation
- [x] **Complete Guide Page** - Comprehensive how-to for all features

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
│   │   ├── alerts.py           # Price alerts API
│   │   ├── notifications.py    # Push & SMS notifications
│   │   ├── scanner.py          # Gem scanner
│   │   ├── auto_execute.py     # Auto execution
│   │   ├── backtest.py         # Backtesting
│   │   ├── rebalance.py        # Portfolio rebalancing
│   │   └── social.py           # Social trading
│   └── services/
│       ├── growth_engine.py       # Aggressive Growth Engine
│       ├── scheduler_service.py   # APScheduler service (Autopilot)
│       ├── price_alerts.py        # Alert service
│       ├── notification_service.py
│       ├── news_service.py        # Fixed with fallbacks
│       ├── gem_scanner.py
│       └── auto_execution.py
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── GrowthDashboard.js  # $500→$100k Dashboard
    │   │   ├── TradingView.js      # Candlestick charts
    │   │   ├── Analytics.js        # Enhanced dashboard
    │   │   ├── AdvancedFeatures.js
    │   │   ├── Guide.js
    │   │   └── Settings.js
    │   └── components/
    │       └── AutopilotControl.js  # Scheduler UI
    └── public/
        └── service-worker.js   # Enhanced for background
```

---

## API Endpoints

### Alerts (NEW)
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
   - Current portfolio value display with progress bar
   - Goal progress tracking ($500 → $100,000)
   - Stats grid (Win Rate, Total P/L, Moonshots, Open Positions)
   - Open positions list with entry prices and stop-losses
   - Paper/Real mode toggle
2. ✅ **P1 COMPLETED**: Scheduled Execution (Autopilot Mode)
   - SchedulerService using APScheduler for automated trading
   - Growth Position Monitor (hourly monitoring)
   - Weekly Automated Trading (Mondays at 8 AM UTC)
   - Daily Profit Compounding (midnight UTC)
   - Start/Stop scheduler controls
3. ✅ **P2 COMPLETED**: Real Money Trading with Budget Protection
   - BudgetManager service - only uses allocated funds
   - NEVER touches other user assets
   - Budget allocation/release tracking
   - Real trading enable/disable toggle
4. ✅ **P2 COMPLETED**: User-Guided Tutorial
   - 6-step interactive onboarding flow
   - Covers budget setup, Kraken connection, AI training, autopilot
   - Accessible via Tutorial button in header
5. ✅ **P3 COMPLETED**: AI Decision Visualization
   - Shows WHY AI chose specific coins
   - Factor breakdown (momentum, volume, trend, sentiment, volatility)
   - Confidence scores and reasoning text
6. ✅ **P3 COMPLETED**: Fixed `/api/learning/record-outcome` endpoint
   - Now accepts query parameters correctly
   - Works even without existing strategy/trade records
7. ✅ **P3 COMPLETED**: Pytest tests for critical services
   - Budget Manager tests
   - Scheduler Service tests
   - Growth Engine tests
   - API endpoint tests
8. ✅ All Growth APIs working
9. ✅ All Scheduler APIs working
10. ✅ All Budget APIs working

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
- Trading journal with AI insights

---

## Test Reports
- `/app/test_reports/iteration_3.json` - Latest test results (Feb 2, 2026)
- `/app/backend/tests/test_services.py` - Unit tests for critical services
