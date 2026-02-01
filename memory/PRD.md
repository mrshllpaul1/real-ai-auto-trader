# AI Crypto Trading Platform - Product Requirements Document

## Original Problem Statement
Build a real money AI crypto auto trading app that learns and develops optimal weekly trading strategies.

## Core Requirements
- AI trained on historical crypto market and news data since January 2009
- Continuously learning from trading performance
- Ability to search for "hidden gems" with 10-100x potential
- Support both real-money and paper trading simultaneously
- PWA capable of running tasks in background on mobile

## Integrations
- **Exchange:** Kraken (real and paper trading)
- **Market Data:** CoinStats, CoinMarketCap, CoinGecko
- **News Data:** CryptoPanic
- **AI:** Emergent LLM Key (GPT-5.2)
- **SMS:** Twilio (requires user credentials)

---

## What's Been Implemented

### Completed Features (as of Feb 1, 2026)

#### Core AI & Trading
- [x] AI training pipeline with hidden gems detection (10x-100x potential)
- [x] Real-time market scanner for opportunity detection
- [x] Auto-execution engine for paper trading
- [x] Self-improving AI that learns from trade outcomes
- [x] Signal weight optimization based on performance

#### Advanced Features
- [x] **Backtesting Interface** - Test strategies against historical data
- [x] **Portfolio Rebalancing** - Automated rebalancing to target allocations
- [x] **Social Trading** - Leaderboard of top traders

#### Notification System
- [x] **Push Notifications** - In-app notifications for completed trades
- [x] **Notification Center** - Bell icon in sidebar with dropdown
- [x] **SMS Integration (Twilio)** - Framework ready, requires user credentials
- [x] **Settings UI** - Configure notification preferences

#### Documentation
- [x] **Complete Guide Page** - Comprehensive how-to for all features
  - Quick Start (3 steps)
  - Hidden Gem Scanner guide
  - Auto Execution Engine setup
  - Backtesting Strategies tutorial
  - Portfolio Rebalancing how-to
  - Social Trading explanation
  - Notifications setup
  - AI Learning explanation
  - Settings configuration
  - Tips & Best Practices

#### Infrastructure
- [x] FastAPI backend with MongoDB
- [x] React frontend with Tailwind CSS
- [x] PWA service worker for background execution
- [x] Kraken API integration

---

## Current Architecture

```
/app/
├── backend/
│   ├── routes/
│   │   ├── auth.py, trading.py, strategies.py
│   │   ├── scanner.py - Gem scanner endpoints
│   │   ├── auto_execute.py - Auto execution endpoints
│   │   ├── backtest.py - Backtesting endpoints
│   │   ├── rebalance.py - Rebalancing endpoints
│   │   ├── social.py - Social trading endpoints
│   │   └── notifications.py - Push/SMS notifications
│   └── services/
│       ├── gem_scanner.py - Real-time market scanner
│       ├── auto_execution.py - Trade execution engine
│       ├── backtesting.py - Strategy backtesting
│       ├── portfolio_rebalancer.py - Portfolio management
│       ├── social_trading.py - Leaderboard & following
│       ├── notification_service.py - Push & SMS service
│       └── self_improving_ai.py - Learning engine
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Sidebar.js - Main navigation
    │   │   ├── NotificationCenter.js - Bell & dropdown
    │   │   └── ui/ - Shadcn components
    │   └── pages/
    │       ├── Dashboard.js - Main dashboard
    │       ├── GemScanner.js - Hidden gem alerts
    │       ├── AutoExecution.js - Auto trading control
    │       ├── AdvancedFeatures.js - Backtest/Rebalance/Social
    │       └── Settings.js - API & Notification settings
    └── public/service-worker.js - PWA support
```

---

## API Endpoints

### Notifications
- `GET /api/notifications/` - Get unread notifications
- `POST /api/notifications/test-push` - Test push notification
- `POST /api/notifications/test-sms` - Test SMS (requires Twilio)
- `GET/POST /api/notifications/settings` - Notification preferences

### Backtesting
- `POST /api/backtest/run` - Run backtest with strategy

### Rebalancing  
- `GET /api/rebalance/calculate/{user_id}` - Get trades needed
- `POST /api/rebalance/execute/{user_id}` - Execute rebalance

### Social
- `GET /api/social/leaderboard` - Top traders

---

## Prioritized Backlog

### P0 - Critical (User Requested)
- [x] Fix Advanced Features black screen ✅
- [x] Push notifications for completed trades ✅
- [x] SMS notifications for high priority trades ✅

### P1 - High Priority
- [ ] Trading charts with TradingView Lightweight Charts
- [ ] Price alerts when scanner detects HIGH gems
- [ ] Fix news API returning empty results

### P2 - Medium Priority
- [ ] Concurrent paper + real-money trading modes
- [ ] Mobile background execution verification
- [ ] Improved API rate limiting handling

### P3 - Future Enhancements
- [ ] Portfolio performance analytics
- [ ] Custom strategy builder
- [ ] Trading journal with AI insights

---

## Known Issues

1. **SMS Requires Credentials** - User must configure Twilio credentials in `.env`:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`

2. **News API Empty** - CryptoPanic free tier may be rate limited

3. **CoinGecko Rate Limiting** - Using CoinMarketCap as primary data source

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

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://smartcrypto-34.preview.emergentagent.com
```

---

## Testing Status
- Backend: 92% pass rate
- Frontend: 100% pass rate
- Test reports: `/app/test_reports/iteration_1.json`
