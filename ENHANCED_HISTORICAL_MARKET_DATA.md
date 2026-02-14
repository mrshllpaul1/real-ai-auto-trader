# Enhanced Historical Market Data

Improvements to historical market data collection and analysis.

## 📊 Data Sources

### Primary Sources
| Source | Data Type | History | Update |
|--------|-----------|---------|--------|
| CryptoCompare | OHLCV | 2010+ | Real-time |
| CoinGecko | Prices | 2014+ | 5 min |
| Kraken | Trades | 2013+ | Real-time |

### Data Coverage
- **Timeframes**: 1m, 5m, 15m, 1h, 4h, 1D, 1W
- **Coins**: 500+ cryptocurrencies
- **Metrics**: OHLCV, market cap, volume, supply

## 🔄 Data Pipeline

### Collection
```python
DATA_COLLECTION_CONFIG = {
    'sources': ['cryptocompare', 'coingecko'],
    'timeframes': ['1h', '4h', '1D'],
    'history_days': 365 * 5,  # 5 years
    'coins': 'top_200_by_market_cap'
}
```

### Processing
1. **Fetch**: API calls with rate limiting
2. **Validate**: Check for gaps, outliers
3. **Normalize**: Consistent format
4. **Store**: MongoDB with indexes
5. **Cache**: Redis for frequent access

### Quality Checks
- Gap detection and filling
- Outlier detection (>3 std dev)
- Volume spike verification
- Price consistency checks

## 📈 Analysis Features

### Technical Indicators
```python
INDICATORS = [
    'SMA_20', 'SMA_50', 'SMA_200',
    'EMA_12', 'EMA_26',
    'RSI_14',
    'MACD',
    'Bollinger_Bands',
    'ATR_14',
    'OBV'
]
```

### Pattern Detection
- Head and shoulders
- Double top/bottom
- Bull/bear flags
- Support/resistance levels

### Correlation Analysis
- BTC correlation
- Sector correlations
- Cross-asset analysis

## 📡 API Endpoints

### Download Historical Data
```bash
POST /api/historical-data/download/start
{"coins": ["BTC", "ETH"], "days": 365}
```

### Get OHLCV Data
```bash
GET /api/historical-data/ohlcv/{symbol}?timeframe=1D&limit=365
```

### Get Indicators
```bash
GET /api/historical-data/indicators/{symbol}?indicators=RSI,MACD,SMA
```

### Get Patterns
```bash
GET /api/historical-data/patterns/{symbol}
```

## 🗄️ Storage

### MongoDB Collections
```javascript
COLLECTIONS = {
  'ohlcv_1h': { indexes: ['symbol', 'timestamp'] },
  'ohlcv_4h': { indexes: ['symbol', 'timestamp'] },
  'ohlcv_1d': { indexes: ['symbol', 'timestamp'] },
  'indicators': { indexes: ['symbol', 'timestamp', 'indicator'] },
  'patterns': { indexes: ['symbol', 'detected_at'] }
}
```

### Data Retention
| Timeframe | Retention |
|-----------|----------|
| 1 minute | 7 days |
| 1 hour | 1 year |
| 4 hour | 3 years |
| 1 day | 10 years |

## 📅 Backtesting Integration

### Strategy Testing
```python
BACKTEST_CONFIG = {
    'start_date': '2020-01-01',
    'end_date': '2026-02-14',
    'initial_capital': 10000,
    'commission': 0.001,
    'slippage': 0.0005
}
```

### Metrics Calculated
- Total return
- Sharpe ratio
- Max drawdown
- Win rate
- Profit factor

## ✅ Enhancements Implemented

- [x] 5-year historical data
- [x] Multiple timeframes
- [x] 500+ coins supported
- [x] Technical indicators
- [x] Pattern detection
- [x] Backtesting integration
- [x] Data quality checks
- [x] Efficient caching

---

**Status**: Enhanced ✅
**Last Updated**: February 2026
