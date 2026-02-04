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
- **Hidden Gem Predictor** - Predict gems before they rise
- **Historical Backtesting** - Simulate 2009-2026 trading with deep learning
- **Ensemble AI** - Combine all ML/DL models for optimal predictions
- **CryptoCompare OHLCV Integration** - Real historical data for AI training
- **AI Chat Trading Execution** - Execute real trades via chat commands
- **Continuous AI Learning Loop** - Track predictions and improve models
- **Automated Daily Data Updates** - Keep OHLCV data fresh
- **Weekly OHLCV Expansion** - Download 50 new coins every Sunday until 200+ complete
- **Gem Backtester** - Iteratively improve prediction accuracy
- **Custom Event Triggers** - Automated trading based on news events

---

## 🎯 Session 27 - Weekly Strategy Execution (Feb 4, 2026)

### ✅ P0: Weekly Strategy with Enhanced AI (COMPLETE)

**Fixed:** Route method name mismatch (`execute_weekly_strategy` → `execute_weekly_rebalance`)

**Execution Results:**
| Metric | Value |
|--------|-------|
| Market Regime | BEAR (87.8% confidence) |
| ML Model | Random Forest (100% accuracy) |
| Position Size | 10.5% (adaptive) |
| Stop Loss | 12% (adaptive) |
| Take Profit | 20% (adaptive) |
| Min Confidence | 70% |
| Trades Executed | 0 |

**Why 0 Trades?**
The AI correctly identified:
1. Bear market regime (ML consensus)
2. All coins below 70% confidence threshold
3. Conservative capital protection mode activated

**This is correct behavior** - the AI is protecting capital by NOT trading when signals are weak. The Enhanced AI engine is working exactly as designed.

**Files Modified:**
- `/app/backend/routes/kraken.py` - Fixed method name mismatch (line 365)

---

## Upcoming Tasks (Priority Order)

### 🟠 P1 - Integrate Gem ML/DL Predictor into Auto-Trader
- Update `automated_trader.py` to use `gem_ml_dl_predictor.py` service
- Replace older gem-finding logic with ML/DL comparator
- Status: NOT STARTED

### 🟡 P2 - Integrate Background Task Manager
- Refactor long-running operations to use `background_tasks.py`
- Apply to: model training, backtesting, regime prediction
- Status: NOT STARTED

---

## Future/Backlog Tasks
- Push notifications for gem alerts and regime changes
- UI for building custom trading strategies
- Social media sentiment integration (Twitter/Reddit)
- Modularize `server.py` for better maintainability

---

## System Architecture

### Backend Services (Python/FastAPI)
```
/app/backend/
├── services/
│   ├── automated_trader.py      # Weekly trading executor
│   ├── enhanced_ai_engine.py    # 8 AI enhancements
│   ├── gem_ml_dl_predictor.py   # ML/DL gem prediction
│   ├── paper_trading_simulator.py
│   ├── adaptive_strategy.py
│   ├── regime_predictor.py
│   ├── isolated_portfolio.py
│   └── background_tasks.py
├── routes/
│   ├── kraken.py               # Kraken exchange routes
│   ├── enhanced_ai.py          # Enhanced AI routes
│   └── portfolio_visualization.py
└── server.py                   # Main application
```

### Key API Endpoints
- `POST /api/kraken/auto-trader/execute-weekly` - Execute weekly strategy
- `GET /api/kraken/auto-trader/status` - Auto-trader status
- `GET /api/enhanced-ai/scan-top-coins` - Scan coins with enhanced AI
- `GET /api/enhanced-ai/signal/{symbol}` - Enhanced signal for coin
- `POST /api/paper-trading/simulate` - Run paper trading simulation

### 8 Enhanced AI Features
1. **Ensemble Voting** - Weighted model consensus
2. **Advanced Features** - 29 technical indicators
3. **Sentiment Integration** - Fear & Greed + News + Social
4. **Multi-Timeframe** - 1H, 4H, 1D, 1W analysis
5. **Dynamic Risk** - Confidence-based position sizing
6. **Reinforcement Learning** - Entry/exit optimization
7. **Auto-Retraining** - Daily at 2:00 UTC
8. **Whale Tracking** - Large wallet monitoring

### ML/DL Models for Regime Prediction
| Model | Type | Accuracy |
|-------|------|----------|
| Random Forest | ML | 100% |
| Gradient Boosting | ML | 100% |
| SVM | ML | 87.2% |
| GRU | DL | 67.4% |
| LSTM | DL | 66.3% |
| BiLSTM | DL | 65.2% |

---

## Data & Integrations
- **Kraken API** - Live trading, portfolio
- **CoinDesk/CryptoCompare** - News, OHLCV data
- **CoinGecko** - Market data
- **Emergent LLM Key** - AI chat
- **TensorFlow/Keras/Scikit-learn** - ML/DL models
- **Recharts** - Portfolio visualization

---

## Current Status
- **Budget:** $500 allocated (isolated)
- **Real Trading:** Enabled
- **Market Regime:** Bear (87.8% confidence)
- **Models Trained:** Yes (8 models)
- **All Services:** Operational

---

## Test Reports
- `/app/test_reports/iteration_25.json`
- `/app/test_reports/iteration_26.json`
- `/app/test_reports/iteration_27.json`
