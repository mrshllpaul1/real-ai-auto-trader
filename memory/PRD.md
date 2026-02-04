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
- **Deep Learning AI** - LSTM price prediction, sentiment analysis, pattern recognition
- **AI Command Center** - Execute actions across the app via natural language
- **Mobile Optimized** - Galaxy S22 support with landscape mode

---

## Session 28 - Complete (Feb 4, 2026)

### ✅ P0: RL Agent Training Timeout Fix (COMPLETE)
- Refactored to use `ThreadPoolExecutor` for non-blocking training
- Added background task manager integration with progress tracking
- Backend remains responsive during training

### ✅ P1: Prediction Signals in Auto-Trader (COMPLETE)
- Added `get_prediction_signals()` combining all 8 prediction services
- Enhanced weekly rebalance: 60% AI trainer + 40% prediction signals
- New endpoint: `GET /api/kraken/auto-trader/prediction-signals/{symbol}`

### ✅ Training Dashboard UI (COMPLETE)
- Route: `/training` with full training management UI
- Real-time stats, service badges, training cards
- Progress bars, result stats, WebSocket live updates
- Added Training History section with collapsible view

### ✅ Training History Service (NEW)
- Records all model training sessions with results
- Tracks success rates, durations, and performance metrics
- API endpoints for history and stats
- Integrated with RL agent training

**New Files:**
- `/app/backend/services/training_history.py`
- `/app/backend/routes/training_history.py`

**New Endpoints:**
- `GET /api/training-history/` - Get history with filters
- `GET /api/training-history/recent` - Get 10 most recent sessions
- `GET /api/training-history/stats` - Overall statistics
- `GET /api/training-history/stats/{model_type}` - Model-specific stats

### ✅ Server Modularization (PARTIAL)
Created modular initialization files for future refactoring:
- `/app/backend/config/app_config.py` - App creation, middleware
- `/app/backend/config/database.py` - MongoDB connection
- `/app/backend/config/websocket.py` - WebSocket manager
- `/app/backend/init/core_services.py` - Core service initialization
- `/app/backend/init/prediction_services.py` - Prediction services
- `/app/backend/init/scheduler_services.py` - Scheduler services

**Note:** These modules are created but server.py still uses inline initialization. Full migration would require careful testing.

---

## 📋 Upcoming Tasks

### P1: Complete RL Agent Training
- Training is in progress (30 episodes)
- After completion, all 8 prediction services will be fully operational

### P2: Full Server.py Modularization
- Migrate server.py to use the new init modules
- Break down the 650+ line file into manageable pieces

### P3: Media Data Training
- Verify social sentiment pipeline uses media/news data
- Train models on media data

---

## Future/Backlog Tasks
- Push notifications (Web Push API)
- Deeper Twitter/Reddit sentiment integration
- Training comparison dashboard (compare results across sessions)
- Model export/import functionality

---

## System Architecture

### Backend Services (Python/FastAPI)
```
/app/backend/
├── config/                      # NEW: Configuration modules
│   ├── app_config.py
│   ├── database.py
│   └── websocket.py
├── init/                        # NEW: Service initialization modules
│   ├── core_services.py
│   ├── prediction_services.py
│   └── scheduler_services.py
├── services/
│   ├── training_history.py      # NEW: Training history tracking
│   ├── automated_trader.py      # MODIFIED: + prediction signals
│   ├── rl_trading_agent.py      # MODIFIED: + history service
│   ├── background_tasks.py
│   └── ... (other services)
├── routes/
│   ├── training_history.py      # NEW: Training history API
│   ├── kraken.py
│   └── ...
└── server.py
```

### Key API Endpoints
- `POST /api/predictions/rl-agent/train` - Start RL training (background)
- `GET /api/predictions/rl-agent/training-status` - Check training progress
- `GET /api/kraken/auto-trader/prediction-signals/{symbol}` - Get prediction signals
- `GET /api/training-history/recent` - Recent training sessions
- `GET /api/training-history/stats` - Training statistics
- `WS /ws/training` - WebSocket for real-time updates

### 8 Prediction Enhancement Services
| # | Service | Status |
|---|---------|--------|
| 1 | Order Book Analysis | ✅ Active |
| 2 | On-Chain Analytics | ✅ Active |
| 3 | Social Sentiment | ✅ Active |
| 4 | Transformer Predictor | ✅ Trained |
| 5 | RL Trading Agent | ⏳ Training |
| 6 | Cross-Asset Correlation | ✅ Active |
| 7 | Volatility Regime | ✅ Active |
| 8 | Momentum Divergence | ✅ Active |

---

## Frontend Pages
- `/` - Dashboard
- `/trading` - Trading Interface
- `/portfolio` - Portfolio View
- `/training` - AI Training Dashboard (with History)
- `/strategy-builder` - Custom Strategy Builder
- `/enhanced-ai` - AI Brain
- `/backtesting` - Backtesting
- ... (many more)

---

## Data & Integrations
- **Kraken API** - Live trading, portfolio
- **CoinDesk/CryptoCompare** - News, OHLCV data
- **CoinGecko** - Market data
- **Emergent LLM Key** - AI chat
- **TensorFlow/Keras/Scikit-learn** - ML/DL models

---

## Current Status
- **Budget:** $500 allocated (isolated)
- **Real Trading:** Enabled
- **Models:** 7/8 active, 1 training
- **All Services:** Operational

---

## Test Reports
- `/app/test_reports/iteration_*.json`
