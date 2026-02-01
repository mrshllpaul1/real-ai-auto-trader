# AI Crypto Auto Trading Platform

A real-money AI-powered cryptocurrency auto trading application with hybrid strategy generation (ML + rule-based indicators), paper trading simulation, and comprehensive risk management.

## 🚀 Features

### ✨ Core Features
- **AI-Powered Strategy Generation**: Weekly strategy recommendations using GPT-5.2 and technical analysis
- **Hybrid Trading Engine**: Combines machine learning with rule-based indicators (RSI, MACD, Bollinger Bands, Moving Averages)
- **Paper & Real Trading**: Test strategies risk-free with paper trading before going live
- **Real-Time Market Data**: Live cryptocurrency prices from CoinGecko/CoinStats
- **Kraken Integration**: Execute real trades on Kraken exchange
- **Risk Management**: Configurable stop-loss, take-profit, and position sizing
- **Performance Analytics**: Track portfolio performance, win rates, and P/L
- **Beautiful UI**: Dark theme with glassmorphism effects and smooth animations

### 📊 Key Functionalities
1. **Dashboard**: Real-time portfolio overview with active strategies
2. **AI Strategy Selector**: View and activate AI-recommended trading strategies
3. **Trading View**: Live price charts and manual trade execution
4. **Analytics**: Performance metrics, trade history, and P/L graphs
5. **Settings**: API credentials and risk management configuration

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **AI/ML**: 
  - OpenAI GPT-5.2 (via Emergent LLM Key)
  - TA-Lib for technical indicators
  - Scikit-learn for ML patterns
- **APIs**:
  - Kraken Exchange API
  - CoinGecko API (market data)
  - CoinMarketCap API support

### Frontend
- **Framework**: React 19
- **UI Library**: Shadcn/ui
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Animations**: Framer Motion
- **Fonts**: Chivo (headings), JetBrains Mono (data), Inter (body)

## 📋 Prerequisites

- **Kraken API Keys** (for real trading)
  - Get from: https://www.kraken.com
  - Required permissions: Query Funds, Create & Modify Orders, Cancel/Close Orders
  - ⚠️ Never enable "Withdraw" permission

- **Emergent LLM Key** (already included)
  - Used for AI strategy generation
  - Pre-configured in the application

## 🚀 Getting Started

### 1. Configure API Credentials

Navigate to **Settings** → **API Credentials** tab:
1. Enter your Kraken API Key
2. Enter your Kraken API Secret
3. Click "Save Credentials"

### 2. Set Risk Parameters

Go to **Settings** → **Risk Management** tab:
- **Max Investment Per Trade**: Maximum USD per trade
- **Stop Loss %**: Automatic stop-loss percentage
- **Take Profit %**: Target profit percentage
- **Max Daily Trades**: Limit trades per day
- **Max Portfolio Allocation**: Max % per coin
- **Risk Level**: Low/Medium/High

### 3. Generate AI Strategies

Navigate to **AI Strategies**:
1. Click "Generate New" button
2. AI will analyze Bitcoin, Ethereum, and Solana
3. Review confidence scores and recommendations
4. Activate your preferred strategy

### 4. Start Trading

**Paper Trading** (Recommended First):
- Toggle to "Paper Trading" mode
- Execute trades without real money
- Test strategies risk-free

**Real Trading**:
- Ensure API credentials are configured
- Toggle to "Real Trading" mode
- Execute actual trades on Kraken

## 📊 How It Works

### AI Strategy Engine (Hybrid Approach)

1. **Technical Analysis**:
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Bollinger Bands
   - Moving Averages (SMA, EMA)
   - ADX (Average Directional Index)

2. **ML Pattern Recognition**:
   - Analyzes historical price patterns
   - Identifies trends and reversals
   - Calculates confidence scores

3. **LLM Analysis**:
   - GPT-5.2 analyzes market conditions
   - Provides strategy recommendations
   - Explains key factors and reasoning
   - Suggests entry/exit points

### Risk Management

- **Position Sizing**: Limits investment per trade
- **Stop Loss**: Automatically exits losing trades
- **Take Profit**: Locks in gains at target levels
- **Daily Limits**: Prevents overtrading
- **Diversification**: Limits exposure per coin

## 🎨 Design System

- **Theme**: Electric & Neon (Dark Mode)
- **Primary Color**: Electric Green (#00FF94) - Profit/Buy signals
- **Secondary Color**: Cyber Purple (#9D00FF) - AI features
- **Accent Color**: Volt Blue (#007AFF) - Info/Charts
- **Destructive**: Hot Pink (#FF0055) - Loss/Sell signals
- **Background**: Deep Obsidian (#050505)

## 🔐 Security

- **API Credentials**: Encrypted with Fernet before storage
- **Environment Variables**: Sensitive data in .env files
- **No Client-Side Keys**: API keys never exposed to frontend
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: Pydantic models validate all inputs

## 🎯 Trading Modes

### Paper Trading
- Simulated trades with virtual money
- Test strategies risk-free
- Track performance without risk
- Practice before going live

### Real Trading
- Actual trades on Kraken exchange
- Real money at stake
- Automated strategy execution
- Full risk management enabled

## 📈 Performance Tracking

- **Portfolio Value**: Real-time net worth
- **Profit/Loss**: Total gains/losses
- **Win Rate**: Percentage of profitable trades
- **Trade History**: Complete transaction log
- **Charts**: Visual performance metrics

## 🚨 Important Notes

1. **Start with Paper Trading**: Always test strategies with paper trading first
2. **Risk Management**: Configure risk settings before real trading
3. **API Keys**: Keep your Kraken API keys secure
4. **Market Risk**: Cryptocurrency trading involves significant risk
5. **No Guarantees**: Past performance doesn't guarantee future results

## 💡 Tips for Best Results

1. **Diversify**: Don't put all capital in one coin
2. **Use Stop Losses**: Protect against large losses
3. **Review Strategies**: Check AI recommendations carefully
4. **Monitor Performance**: Track your trades regularly
5. **Start Small**: Begin with small amounts when going live

## 🔄 Weekly Strategy Updates

The AI generates new strategies weekly based on:
- Historical market data (past year)
- Current market conditions
- Technical indicators
- News sentiment (when available)
- Risk-adjusted returns

## ⚖️ Disclaimer

This software is for educational purposes. Cryptocurrency trading involves substantial risk of loss. Only trade with money you can afford to lose. The developers are not responsible for any financial losses incurred through use of this application.

---

**Made with Emergent** 🚀
