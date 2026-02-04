# AI Crypto Trading Platform - Product Requirements Document

## Original Problem Statement
Build a real money AI crypto auto trading app that learns and develops optimal weekly trading strategies. Ultimate goal: Turn $500 into $100,000.

## Core Requirements
- AI trained on REAL historical crypto market data
- Continuously learning from trading performance
- Ability to search for "hidden gems" with 10-100x potential
- Support both real-money and paper trading with budget controls
- Kraken exchange integration for live trading
- Dynamic coin universe - AI can discover and add new coins
- Deep Learning AI - LSTM price prediction, sentiment analysis, pattern recognition

---

## Session 28 - Complete (Feb 4, 2026)

### ✅ All Tasks Completed

**1. RL Agent Training Timeout Fix (P0)**
- Refactored to use `ThreadPoolExecutor` for non-blocking training
- Backend remains responsive during long training sessions

**2. Prediction Signals in Auto-Trader (P1)**
- Added `get_prediction_signals()` combining all 8 prediction services
- Enhanced weekly rebalance: 60% AI trainer + 40% prediction signals
- Tested: ETH composite score 46.77, signal "hold", 5 models used

**3. Training Dashboard UI**
- Real-time stats, service badges, training cards
- Progress bars, result stats, WebSocket live updates

**4. Training History Service (NEW)**
- Records all model training sessions with results
- API endpoints for history and stats
- Integrated with RL agent training

**5. Training Scheduler Service (NEW)**
- Automatic model training at scheduled times
- Cron-based and interval-based scheduling
- 5 preset schedules available
- API for managing schedules
- UI for adding, toggling, and deleting schedules

**6. Server Modularization (Partial)**
- Created modular initialization files in `/app/backend/config/` and `/app/backend/init/`

---

## New Features This Session

### Training Scheduler
**Service:** `/app/backend/services/training_scheduler.py`
**Routes:** `/app/backend/routes/training_scheduler.py`

**API Endpoints:**
- `GET /api/training-scheduler/` - List all schedules
- `POST /api/training-scheduler/` - Create schedule
- `DELETE /api/training-scheduler/{id}` - Delete schedule
- `POST /api/training-scheduler/{id}/toggle` - Enable/disable
- `POST /api/training-scheduler/{id}/run-now` - Manual trigger
- `GET /api/training-scheduler/presets/list` - Get preset schedules

**Presets:**
- Daily RL Agent (2 AM) - 100 episodes
- Daily Transformer (3 AM)
- Weekly Full Training (Sunday 1 AM) - 200 episodes
- Every 6 Hours - 50 episodes
- Every 12 Hours (Transformer)

**Supported Model Types:**
- `rl_agent` - Reinforcement Learning Trading Agent
- `transformer` - Transformer Predictor
- `regime` - Market Regime Predictor

---

## System Architecture

### Backend Services
```
/app/backend/
├── config/                      # Configuration modules
│   ├── app_config.py
│   ├── database.py
│   └── websocket.py
├── init/                        # Service initialization modules
│   ├── core_services.py
│   ├── prediction_services.py
│   └── scheduler_services.py
├── services/
│   ├── training_scheduler.py    # NEW: Automatic training scheduling
│   ├── training_history.py      # Training session tracking
│   ├── automated_trader.py      # + prediction signals integration
│   ├── rl_trading_agent.py      # + history service integration
│   └── ... (40+ other services)
├── routes/
│   ├── training_scheduler.py    # NEW: Scheduler API
│   ├── training_history.py      # History API
│   └── ... (20+ other routes)
└── server.py                    # ~700 lines (to be modularized)
```

### Key API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/training-scheduler/` | GET/POST | Manage training schedules |
| `/api/training-history/recent` | GET | Recent training sessions |
| `/api/predictions/rl-agent/train` | POST | Start RL training (background) |
| `/api/kraken/auto-trader/prediction-signals/{symbol}` | GET | Get prediction signals |
| `/ws/training` | WebSocket | Real-time training updates |

### 8 Prediction Enhancement Services
| # | Service | Status |
|---|---------|--------|
| 1 | Order Book Analysis | ✅ Active |
| 2 | On-Chain Analytics | ✅ Active |
| 3 | Social Sentiment | ✅ Active |
| 4 | Transformer Predictor | ⏳ Needs Training |
| 5 | RL Trading Agent | ⏳ Needs Training |
| 6 | Cross-Asset Correlation | ✅ Active |
| 7 | Volatility Regime | ✅ Active |
| 8 | Momentum Divergence | ✅ Active |

---

## Frontend Pages
- `/` - Dashboard
- `/trading` - Trading Interface
- `/portfolio` - Portfolio View
- `/training` - AI Training Dashboard (with Scheduler & History)
- `/strategy-builder` - Custom Strategy Builder
- `/enhanced-ai` - AI Brain
- `/backtesting` - Backtesting
- ... (15+ more pages)

---

## 📋 Upcoming Tasks

### P1: Full Server Modularization
- Migrate server.py to use the new init modules
- Break down 700+ line file into manageable pieces

### P2: Train Models
- Use the scheduler or manual training to get all models trained
- RL Agent: `/api/predictions/rl-agent/train` (background)
- Transformer: `/api/predictions/transformer/train`

### P3: Test Weekly Rebalance with Predictions
- Execute `/api/kraken/auto-trader/execute-weekly` in paper mode
- Verify prediction signals affect coin selection

---

## Future/Backlog Tasks
- Training comparison dashboard (compare results across sessions)
- Model export/import functionality
- Push notifications (Web Push API)
- Deeper Twitter/Reddit sentiment integration
- Model performance analytics dashboard

---

## Data & Integrations
- **Kraken API** - Live trading, portfolio
- **CoinDesk/CryptoCompare** - News, OHLCV data
- **CoinGecko** - Market data
- **Emergent LLM Key** - AI chat
- **TensorFlow/Keras/Scikit-learn** - ML/DL models
- **APScheduler** - Background job scheduling

---

## Current Status
- **Budget:** $500 allocated (isolated)
- **Real Trading:** Enabled
- **Active Schedules:** 1 (daily RL at 2 AM)
- **Models:** 5/8 trained
- **All Services:** Operational
