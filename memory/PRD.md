# AI Crypto Auto Trading - Product Requirements Document

## Overview
A real-money AI crypto auto trading application that learns and develops optimal weekly trading strategies for automated trading on Kraken exchange.

## Core Features

### 1. AI Training & Learning System
- **Historical Training**: AI trained on 16+ years of crypto market data (2009-present)
- **Hidden Gems Detection**: Identifies coins with 10-100x potential based on historical patterns
- **Pattern Recognition**: Identifies trading patterns including:
  - Oversold/Overbought Reversals
  - Bullish/Bearish Continuations
  - Golden Cross patterns
  - Deep value opportunities
  - Volume accumulation signals
- **Continuous Learning**: Learns from trading performance to improve strategies

### 2. Market Intelligence
- **Multi-Source Data**: CoinGecko, CoinMarketCap, CoinStats integration
- **News Aggregation**: CryptoPanic API integration for crypto news
- **Sentiment Analysis**: AI-powered news sentiment analysis using GPT-5.2
- **Real-time Prices**: Live cryptocurrency price tracking

### 3. Auto Trading
- **Dual Mode**: Paper trading + Real money trading simultaneously
- **Kraken Integration**: Full trading integration with Kraken exchange
- **Risk Management**: Configurable stop-loss, take-profit, position sizing
- **Background Execution**: PWA support for mobile background trading
- **Portfolio Allocation**: Dedicated AI trading portfolio separate from main assets

### 4. User Interface
- **Dashboard**: Real-time portfolio overview and performance metrics
- **AI Strategies**: View generated strategies with confidence scores
- **Analytics**: Trading performance charts and statistics
- **Settings**: Configure trading parameters and API keys

## Technical Stack
- **Frontend**: React, Tailwind CSS, Shadcn/UI, Recharts
- **Backend**: FastAPI, Python
- **Database**: MongoDB
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **Exchange**: Kraken API

## API Keys Required (Configured)
- Kraken API Key & Secret
- CoinMarketCap API Key
- CoinStats API Key
- Emergent LLM Key (for AI analysis)

## Current Status

### Completed Features ✅
1. **Frontend Fixed**: Black screen issue resolved (syntax errors in JSX files)
2. **Backend Services**: All trading, market, strategy, and learning services operational
3. **Historical Training**: Full training pipeline with hidden gems detection
4. **AI Integration**: GPT-5.2 for pattern analysis and sentiment analysis
5. **Portfolio Allocation**: Dedicated AI trading portfolio management
6. **PWA Setup**: Service worker configured for mobile background execution

### Training Results (Latest)
- **Coins Trained**: Bitcoin, Ethereum, Solana, Cardano
- **Total Patterns Found**: 10,974
- **Hidden Gems Detected**: 5,382
- **Pattern Success Rate**: 59.4%

### Known Limitations
- News API returns 0 articles (CryptoPanic free tier limitation)
- Training uses synthetic historical data (production would use real historical data from exchanges)

## API Endpoints

### Training
- `POST /api/training/train` - Start AI training with hidden gems detection
- `GET /api/training/status` - Get training status and statistics
- `GET /api/training/hidden-gems` - Get detected hidden gem patterns
- `GET /api/training/patterns/{coin_id}` - Get historical patterns for a coin
- `GET /api/training/gem-signals` - Get most effective entry signals

### Trading
- `POST /api/trading/execute` - Execute a trade
- `GET /api/trading/portfolio/{user_id}` - Get user portfolio
- `GET /api/trading/history/{user_id}` - Get trade history

### Auto Trading
- `POST /api/auto-trading/start` - Start auto trading
- `POST /api/auto-trading/stop` - Stop auto trading
- `GET /api/auto-trading/status` - Get auto trading status

### Market Data
- `GET /api/market/prices` - Get current crypto prices
- `GET /api/market/historical/{coin_id}` - Get historical price data

## Next Steps / Backlog

### Priority 1 (P1)
- Implement candlestick charts using TradingView Lightweight Charts
- Connect to real historical data APIs for training
- Fix news API integration (consider alternative sources)

### Priority 2 (P2)
- Add more cryptocurrencies to training
- Implement notification system for trades
- Add trade confirmation dialogs

### Priority 3 (P3)
- Advanced charting with indicators
- Mobile app optimization
- Performance dashboard with detailed analytics

---
*Last Updated: February 2026*
