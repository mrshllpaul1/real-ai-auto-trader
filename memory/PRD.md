# AI Crypto Trading Platform - PRD

## Original Problem Statement
Build a real money AI crypto auto trading app named "Tethys" with aggressive growth strategy. Turn $500 into $100,000.

---

## Session Update - Feb 9, 2026 (Latest)

### ✅ Major Features Added

| Feature | Description | Status |
|---------|-------------|--------|
| **Options Trading** | Full options chain, Greeks calculation, strategies | ✅ Complete |
| **Backtest Engine** | Test strategies on historical data | ✅ Complete |
| **Exchange Update** | Replaced KuCoin with Crypto.com (US-friendly) | ✅ Complete |

---

### Options Trading (`/options-trading`)
- **Option Chain**: View calls/puts with bid/ask, delta, open interest
- **Greeks Calculation**: Black-Scholes model (Delta, Gamma, Theta, Vega, Rho)
- **Place Orders**: Buy calls/puts with strike selection
- **Positions Management**: View P&L, Greeks, days to expiry
- **6 Strategies**: Long Call, Long Put, Bull Call Spread, Bear Put Spread, Straddle, Iron Condor

**API Endpoints:**
- `GET /api/options/chain/{symbol}` - Full option chain
- `POST /api/options/calculate-greeks` - Greeks calculation
- `POST /api/options/order` - Place option order
- `GET /api/options/positions` - User positions
- `GET /api/options/strategies` - Available strategies

---

### Backtest Engine (`/backtest-engine`)
- **4 Strategies**: Momentum, Mean Reversion, Trend Following, ML-Based
- **3 Templates**: BTC Momentum 30D, Multi-Coin Mean Reversion, ETH Trend Following
- **Configuration**: Symbol, dates, capital, position size, stop loss, take profit
- **Metrics**: Total return, win rate, max drawdown, Sharpe ratio, profit factor
- **Equity Curve**: Visual chart of portfolio growth
- **Trade History**: Detailed trade log with P&L

**API Endpoints:**
- `POST /api/backtest-engine/run` - Start backtest
- `GET /api/backtest-engine/status/{id}` - Check progress
- `GET /api/backtest-engine/results/{id}` - Get results
- `GET /api/backtest-engine/strategies` - Available strategies
- `GET /api/backtest-engine/templates` - Quick templates

---

### Exchange Configuration Update
Replaced KuCoin (not US-friendly) with Crypto.com:

| Exchange | Purpose | Status |
|----------|---------|--------|
| **Kraken** | Primary trading | ✅ Available |
| **Binance** | Largest by volume | ✅ Available |
| **Crypto.com** | Best for arbitrage (US-friendly, 0.075% fees) | ✅ NEW |

---

## Previously Implemented Features

### P2 Features (from previous session)
- ✅ Copy Trading - Follow top traders
- ✅ Market Maker Mode - Provide liquidity
- ✅ Dashboard Customization - Widgets, themes, preferences

### P1 Features
- ✅ Multi-Exchange Support (3 exchanges)
- ✅ ML Caching System
- ✅ Toast Notifications
- ✅ Public API with Swagger

### P0 Core Features
- ✅ Kraken Integration
- ✅ Command Center
- ✅ AI Command Center
- ✅ Growth Engine ($500→$100K)
- ✅ Master Orchestrator
- ✅ Spot Trading
- ✅ Portfolio Dashboard

---

## Current Navigation Structure

```
Sidebar:
├── Command Center
├── AI Center
├── AI Budget
├── Spot Trading
├── Positions
├── Portfolio
├── Copy Trading
├── Market Maker
├── Options (NEW)
├── Backtest Engine (NEW)
├── Event Triggers
├── Trigger Stats
├── Adaptive AI
├── AI Training
├── Model Performance
├── Event Timeline
├── Journal
├── Gem Scanner
├── Gem Backtester
├── ML vs DL Gems
├── Auto Execute
├── Advanced
├── AI Strategies
├── Auto Trading
├── Trading
├── Analytics
├── AI Learning
├── Learning Loop
├── Ensemble AI
├── News & Intel
├── Customize
├── Guide
├── Setup
└── Settings
```

---

## Key Files Created This Session

| File | Purpose |
|------|---------|
| `/app/backend/routes/options_trading.py` | Options trading API with Black-Scholes |
| `/app/backend/routes/backtest_engine.py` | Backtesting engine API |
| `/app/frontend/src/pages/OptionsTrading.jsx` | Options trading UI |
| `/app/frontend/src/pages/BacktestEngine.jsx` | Backtesting UI |

---

## Future Tasks (Remaining)

### P1 - Upcoming
- MetaMask Wallet Integration
- Telegram Notifications
- Mobile PWA
- DeFi Yield Farming

### P2+ - Backlog
- Advanced order types (Trailing Stop, OCO)
- Strategy marketplace
- Subscription tiers & referral program

---

## Technical Notes

### Options Pricing
Using Black-Scholes model with:
- 65% implied volatility for crypto
- 5% risk-free rate
- Greeks: Delta, Gamma, Theta, Vega, Rho

### Backtesting Strategies
1. **Momentum**: Buy positive momentum, sell negative
2. **Mean Reversion**: Trade Z-score extremes
3. **Trend Following**: MA crossover signals
4. **ML-Based**: Machine learning predictions

---

## Known Limitations

- Options prices are simulated (not connected to real options exchange)
- Backtest uses simulated price data with random walk
- Heavy ML operations disabled by default (lightweight mode)

---

*Last Updated: February 9, 2026*
