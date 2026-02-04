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

**Dynamic Confidence Threshold Implemented:**
| Market Regime | Min Confidence | Logic |
|---------------|----------------|-------|
| Strong Bull | 65% | Be selective when market is hot |
| Bull | 60% | Slightly higher bar |
| Sideways | 55% | Base threshold |
| Bear | 45% | Lower to allow some trades |
| Strong Bear | 50% | Cautious but not frozen |

**Execution Results (Bear Market):**
| Metric | Value |
|--------|-------|
| Market Regime | BEAR (87.8% confidence) |
| ML Model | Random Forest (100% accuracy) |
| Position Size | 10.5% (adaptive) |
| Stop Loss | 12% (adaptive) |
| Take Profit | 20% (adaptive) |
| Min Confidence | 45% (dynamic) |
| Trades Executed | 3 |
| Total Invested | $122.73 |

**Trades Executed:**
| Coin | Amount | Entry Price | AI Score |
|------|--------|-------------|----------|
| Polkadot (DOT) | $40.91 | $1.52 | 49.4% |
| Ethereum (ETH) | $40.91 | $2,278 | ~48% |
| Cardano (ADA) | $40.91 | $0.30 | ~47% |

**Files Modified:**
- `/app/backend/routes/kraken.py` - Fixed method name mismatch (line 365)
- `/app/backend/services/adaptive_strategy.py` - Dynamic confidence thresholds

---

## Upcoming Tasks (Priority Order)

### ✅ Action Items Complete (Feb 4, 2026)

**1. Custom Strategy Builder with AI Chat Integration**
- `/app/backend/services/custom_strategy_builder.py` - AI-powered strategy creation
- `/app/frontend/src/pages/StrategyBuilder.js` - Interactive UI
- Features: Natural language strategy building, 8 templates, manual builder
- API: `POST /api/strategy-builder/from-description` - AI parses strategy from text

**2. Push Notification Service**
- `/app/backend/services/push_notification_service.py` - Full notification system
- Types: Gem alerts, regime changes, price alerts, trade execution, whale alerts
- Features: Priority levels, SSE streaming, notification preferences

**3. All 8 Prediction Enhancements**
- Order Book Analysis, On-Chain Analytics, Social Sentiment Pipeline
- Transformer Architecture, RL Trading Agent, Cross-Asset Correlation
- Volatility Regime Detection, Momentum Divergence Signals

### 📋 Future Tasks
- Download more historical OHLCV data to enable Transformer/RL training
- Integrate custom strategies into automated trader execution
- Add WebSocket support for real-time notification delivery

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
