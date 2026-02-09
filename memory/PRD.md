# AI Crypto Trading Platform - PRD

## Original Problem Statement
Build a real money AI crypto auto trading app named "Tethys" with aggressive growth strategy. Turn $500 into $100,000.

---

## Session Update - Feb 9, 2026 (Latest)

### ✅ P0 Features COMPLETED

| Feature | Description | Status |
|---------|-------------|--------|
| **Advanced Orders** | Trailing Stop, DCA Bot, OCO, Iceberg orders | ✅ Complete |
| **DeFi Wallet** | MetaMask integration, multi-chain support | ✅ Complete |
| **Yield Farming** | 10 DeFi protocols with APY tracking | ✅ Complete |
| **Perpetual Futures** | Leverage trading up to 100x, 6 markets | ✅ Complete |
| **News Sentiment** | AI-powered market sentiment analysis | ✅ Complete |
| **Portfolio Risk Analyzer** | Unified risk dashboard with VaR & stress tests | ✅ Complete |

### ✅ P1 Features COMPLETED

| Feature | Description | Status |
|---------|-------------|--------|
| **Telegram Notifications** | Trading alerts via Telegram bot | ✅ Complete |
| **Portfolio Rebalancing** | AI-powered allocation suggestions with 7 templates | ✅ Complete |

---

### Advanced Orders (`/advanced-orders`)
- **Trailing Stop**: Auto-adjusting stop losses that follow price
- **DCA Bots**: Dollar-cost averaging automation
- **OCO Orders**: One-Cancels-Other (Take Profit + Stop Loss)
- **Iceberg Orders**: Large order execution without market impact

**API Endpoints:**
- `GET /api/advanced-orders/summary` - Order counts
- `POST /api/advanced-orders/trailing-stop/create` - Create trailing stop
- `POST /api/advanced-orders/dca/create` - Create DCA bot
- `POST /api/advanced-orders/oco/create` - Create OCO order

---

### DeFi Wallet (`/defi-wallet`)
- **MetaMask Connect**: Browser extension integration
- **Multi-Chain**: Ethereum, BSC, Polygon, Arbitrum, Optimism, Base
- **Portfolio View**: Token balances, DeFi positions, NFTs
- **Transaction History**: Recent activity tracking

**API Endpoints:**
- `GET /api/defi-wallet/supported` - Supported chains & protocols
- `POST /api/defi-wallet/connect` - Register wallet
- `GET /api/defi-wallet/balances/{address}` - Token balances
- `GET /api/defi-wallet/positions/{address}` - DeFi positions

---

### Yield Farming (`/yield-farming`)
- **10 Protocols**: Lido, Aave, Curve, Yearn, GMX, Uniswap, etc.
- **APY Tracking**: Real-time yield rates with breakdown
- **Risk Levels**: Low/Medium/High classification
- **IL Calculator**: Impermanent loss estimation tool

**API Endpoints:**
- `GET /api/yield-farming/opportunities` - Available vaults
- `POST /api/yield-farming/deposit` - Deposit to vault
- `GET /api/yield-farming/positions` - User positions

---

### Perpetual Futures (`/perpetuals`)
- **6 Markets**: BTC-PERP, ETH-PERP, SOL-PERP, ARB-PERP, DOGE-PERP, LINK-PERP
- **Leverage**: Up to 100x on BTC, configurable per market
- **Funding Rates**: 8-hour funding with predictions
- **Position Calculator**: PnL/ROE/liquidation estimates

**API Endpoints:**
- `GET /api/perpetuals/markets` - Available markets
- `POST /api/perpetuals/position/open` - Open position
- `POST /api/perpetuals/position/close` - Close position
- `GET /api/perpetuals/funding-rates` - Funding rates

---

### News Sentiment (`/news-sentiment`)
- **Market Sentiment**: Overall crypto market score (0-100)
- **Coin Analysis**: Individual coin sentiment with AI insights
- **News Feed**: Trending, bullish, and bearish news
- **Data Sources**: CryptoPanic API, CoinDesk API

**API Endpoints:**
- `GET /api/sentiment/market` - Market sentiment
- `GET /api/sentiment/coin/{coin_id}` - Coin-specific analysis
- `GET /api/sentiment/trending` - Trending news

---

### Portfolio Risk Analyzer (`/risk-analyzer`)
- **Unified Risk Score**: 0-100 score combining all position types
- **Risk Breakdown**: Perpetuals (leverage, liquidation), Yield (IL, protocol risk), Options (Greeks)
- **Value at Risk (VaR)**: 95% and 99% VaR with Expected Shortfall
- **Stress Testing**: Market Crash, Flash Crash, Bull Run, Black Swan scenarios
- **Exposure Analysis**: By asset and position type with concentration alerts
- **Smart Recommendations**: AI-powered risk reduction suggestions

**API Endpoints:**
- `GET /api/risk-analyzer/overview` - Full risk analysis
- `GET /api/risk-analyzer/exposure` - Exposure breakdown
- `GET /api/risk-analyzer/var` - Value at Risk calculation
- `POST /api/risk-analyzer/stress-test` - Run stress scenarios
- `GET /api/risk-analyzer/correlations` - Asset correlation matrix

---

### Telegram Notifications (`/telegram`) ⭐ P1
- **Bot Integration**: Connect Telegram bot for real-time alerts
- **Alert Types**: Trade executions, price alerts, risk warnings, portfolio updates
- **Price Alerts**: Create alerts when price goes above/below target
- **Daily Summary**: Automated daily trading summary reports
- **Notification History**: Track all sent notifications

**API Endpoints:**
- `GET /api/telegram/status` - Integration status
- `POST /api/telegram/config` - Save notification preferences
- `POST /api/telegram/test` - Test connection
- `POST /api/telegram/price-alert/create` - Create price alert
- `GET /api/telegram/price-alerts` - List price alerts
- `POST /api/telegram/notify/daily-summary` - Send daily summary

**Note:** Requires `TELEGRAM_BOT_TOKEN` environment variable

---

### Portfolio Rebalancing (`/rebalance`) ⭐ P1
- **Current Analysis**: Pie chart showing allocation breakdown
- **AI Suggestions**: Risk-based automatic allocation recommendations
- **7 Templates**: Conservative, Balanced, Growth, BTC Maximalist, ETH Focused, DeFi Yield, Alt Season
- **Drift Detection**: Alert when portfolio drifts from target
- **Execute Trades**: One-click rebalancing execution

**API Endpoints:**
- `GET /api/rebalance/analyze` - Current portfolio analysis
- `POST /api/rebalance/suggest` - AI-powered suggestions
- `GET /api/rebalance/templates` - Allocation templates
- `GET /api/rebalance/drift` - Check portfolio drift
- `POST /api/rebalance/execute` - Execute rebalancing trades

---

## Previously Implemented Features

### Options Trading & Backtesting (Previous Session)

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
├── Options
├── Backtest Engine
├── Advanced Orders ⭐
├── DeFi Wallet ⭐
├── Yield Farming ⭐
├── Perpetuals ⭐
├── News Sentiment ⭐
├── Risk Analyzer ⭐
├── Rebalance ⭐
├── Telegram ⭐
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

⭐ = Added this session
```

---

## Key Files Created This Session

| File | Purpose |
|------|---------|
| `/app/backend/routes/advanced_orders.py` | Advanced order types API |
| `/app/backend/routes/defi_wallet.py` | DeFi wallet integration API |
| `/app/backend/routes/yield_farming.py` | Yield farming API |
| `/app/backend/routes/perpetual_futures.py` | Perpetual futures trading API |
| `/app/frontend/src/pages/AdvancedOrders.jsx` | Advanced orders UI |
| `/app/frontend/src/pages/DeFiWallet.jsx` | DeFi wallet UI with MetaMask |
| `/app/frontend/src/pages/YieldFarming.jsx` | Yield farming dashboard |
| `/app/frontend/src/pages/PerpetualFutures.jsx` | Perpetuals trading UI |
| `/app/frontend/src/pages/NewsSentiment.jsx` | News sentiment dashboard |
| `/app/backend/routes/risk_analyzer.py` | Portfolio risk analyzer API |
| `/app/frontend/src/pages/RiskAnalyzer.jsx` | Risk analyzer dashboard |

---

## Future Tasks (Remaining)

### P1 - Upcoming
- Telegram Notifications Bot
- Mobile PWA
- Real exchange API connections (replace mock data)

### P2+ - Backlog
- Strategy marketplace
- Subscription tiers & referral program
- Social trading features
- Multi-language support

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
- **New P0 features use MOCK data**: Advanced Orders, DeFi Wallet positions, Yield Farming, Perpetual Futures
- MetaMask integration requires browser extension for real wallet connection
- News Sentiment uses real CryptoPanic/CoinDesk APIs

---

## Testing Status

| Feature | Backend Tests | Frontend Tests | Status |
|---------|--------------|----------------|--------|
| Advanced Orders | 7 endpoints | Page + Modal | ✅ Pass |
| DeFi Wallet | 6 endpoints | Page + Connect | ✅ Pass |
| Yield Farming | 6 endpoints | Page + Deposit | ✅ Pass |
| Perpetual Futures | 6 endpoints | Page + Trade | ✅ Pass |
| News Sentiment | 4 endpoints | Page + Tabs | ✅ Pass |

Test Report: `/app/test_reports/iteration_40.json`

---

*Last Updated: February 9, 2026*
