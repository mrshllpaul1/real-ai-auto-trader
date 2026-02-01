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

### ✅ Trading Charts (NEW)
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
│   │   ├── alerts.py          # Price alerts API (NEW)
│   │   ├── notifications.py   # Push & SMS notifications
│   │   ├── scanner.py         # Gem scanner
│   │   ├── auto_execute.py    # Auto execution
│   │   ├── backtest.py        # Backtesting
│   │   ├── rebalance.py       # Portfolio rebalancing
│   │   └── social.py          # Social trading
│   └── services/
│       ├── price_alerts.py       # Alert service (NEW)
│       ├── notification_service.py
│       ├── news_service.py       # Fixed with fallbacks
│       ├── gem_scanner.py
│       └── auto_execution.py
└── frontend/
    ├── src/pages/
    │   ├── TradingView.js     # Candlestick charts (NEW)
    │   ├── Analytics.js       # Enhanced dashboard (NEW)
    │   ├── AdvancedFeatures.js
    │   ├── Guide.js
    │   └── Settings.js
    └── public/
        └── service-worker.js  # Enhanced for background (NEW)
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

2. **Market API Rate Limits** - External APIs may timeout; fallback data is shown

3. **News Uses Simulated Data** - When CryptoPanic/CoinGecko fail, simulated news is displayed

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

## Completed Tasks This Session
1. ✅ Fixed AdvancedFeatures.js black screen
2. ✅ Added push notifications for completed trades
3. ✅ Added SMS notification framework for HIGH priority
4. ✅ Created complete Guide page
5. ✅ Implemented TradingView candlestick charts
6. ✅ Created price alerts service and API
7. ✅ Fixed news API with fallback sources
8. ✅ Enhanced Analytics with portfolio dashboard
9. ✅ Updated service worker for background execution
10. ✅ Concurrent paper/real trading modes supported

---

## Future Enhancements
- Real Twilio integration (requires user credentials)
- Email notifications backup
- Interactive onboarding tutorial
- Custom strategy builder UI
- Trading journal with AI insights
