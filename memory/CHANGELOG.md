# AI Crypto Trading Platform - Changelog

## [Session 5] - Feb 3, 2026

### Fixed
- **Trading Mode Persistence Bug (P0)** - Fixed `TradingView.js` to use global `useTradingMode()` context instead of local `useState('paper')`. Mode now persists correctly when navigating between pages.

### Added
- **News Filters Page** - New `/news-filters` route with:
  - Search functionality
  - Coin filter dropdown (BTC, ETH, SOL, etc.)
  - News tabs (Trending, Hot, Bullish, Bearish, Important)
  - Market Sentiment Overview
  - Coin-specific AI sentiment analysis
  - 60-second auto-refresh

### Tested
- 5/5 frontend tests passed for trading mode persistence
- Verified on mobile (375x812) and desktop (1920x1080) viewports

---

## [Session 4] - Feb 2, 2026

### Added
- **Trading Mode Context** - Global React Context (`TradingModeContext.js`) for centralized trading mode state
- **Sidebar Mode Indicator** - Persistent visual indicator showing REAL/PAPER mode
- **CryptoPanic Integration** - Full API wrapper with trending, bullish, bearish news endpoints
- **AI Training on Full Universe** - Trained AI on 79 coins with sentiment data
- **Real Auto-Trading Activation** - Configured and enabled real-money auto-trading

### Fixed
- Refactored all trading-related components to use global context
- Fixed Analytics.js to show real portfolio data
- Rewrote `cryptopanic_service.py` to use direct HTTP calls (library incompatible with free tier)

---

## [Session 3] - Feb 2, 2026

### Added
- AI Confidence Threshold slider
- AI Decision Visualization dashboard
- Expanded Pytest coverage (30+ tests)
- Dynamic Coin Universe Manager
- AI Auto-Discovery system
- Push Notifications with vibration patterns

### Fixed
- Removed ALL simulated data from services
- Kraken real money trading enabled with budget controls
