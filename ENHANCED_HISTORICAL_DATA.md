# Enhanced Historical Market and Media Data

## Overview

This enhancement provides a comprehensive, unified system for managing historical market data and crypto news with advanced correlation analysis. The system consolidates multiple data sources, ensures data quality, and provides actionable trading signals based on news-price correlations.

## Key Features

### 1. **Unified Historical Data Management**
- **Multi-Source Aggregation**: Automatically consolidates data from CoinDesk, Kraken, and CoinGecko
- **Source Prioritization**: Uses the most reliable source available with automatic fallback
- **Persistent Storage**: MongoDB-backed storage for complete historical datasets
- **Quality Validation**: Automatic detection of gaps, outliers, and data quality issues

### 2. **News Aggregation & Persistence**
- **Multi-Source News**: Combines CryptoPanic and other news sources
- **Deduplication**: Intelligent deduplication prevents duplicate news items
- **Sentiment Analysis**: Multi-source sentiment aggregation with weighted scoring
- **Historical Archive**: Persistent storage enables backtesting with historical news

### 3. **News-Market Correlation Analysis**
- **Predictive Signals**: Identifies which news types actually move markets
- **Multiple Time Lags**: Analyzes correlations at 1h, 4h, 24h, and 1-week intervals
- **Statistical Significance**: Includes p-values and confidence intervals
- **Trading Signals**: Generates actionable bullish/bearish/neutral signals

## API Endpoints

### Historical OHLCV Data

#### GET `/api/enhanced-historical/ohlcv/{symbol}`

Get unified historical OHLCV data with automatic source fallback.

**Parameters:**
- `symbol` (path): Coin symbol (BTC, ETH, SOL, etc.)
- `quote` (query, default: USD): Quote currency
- `start_date` (query, optional): Start date in ISO format
- `end_date` (query, optional): End date in ISO format
- `interval` (query, default: daily): Timeframe (daily, hourly, 4h, weekly)
- `force_refresh` (query, default: false): Skip cache and fetch fresh data

**Example:**
```bash
curl "http://localhost:8001/api/enhanced-historical/ohlcv/BTC?start_date=2024-01-01&end_date=2024-12-31"
```

**Response:**
```json
{
  "symbol": "BTC",
  "quote": "USD",
  "interval": "daily",
  "data": [
    {
      "timestamp": 1704067200,
      "date": "2024-01-01",
      "open": 42000.0,
      "high": 43000.0,
      "low": 41500.0,
      "close": 42500.0,
      "volume": 1000000000
    }
  ],
  "count": 365,
  "source": "coindesk",
  "earliest_date": "2024-01-01",
  "latest_date": "2024-12-31",
  "quality_summary": {
    "total_candles": 365,
    "candles_with_issues": 2,
    "quality_score": 99.5
  }
}
```

---

### Data Quality Monitoring

#### GET `/api/enhanced-historical/quality/{symbol}`

Get comprehensive quality report for historical data.

**Parameters:**
- `symbol` (path): Coin symbol
- `quote` (query, default: USD): Quote currency
- `interval` (query, default: daily): Timeframe

**Example:**
```bash
curl "http://localhost:8001/api/enhanced-historical/quality/BTC"
```

**Response:**
```json
{
  "symbol": "BTC",
  "quote": "USD",
  "interval": "daily",
  "total_candles": 5000,
  "date_range": {
    "earliest": "2010-07-18T00:00:00+00:00",
    "latest": "2024-02-09T00:00:00+00:00"
  },
  "gaps": {
    "count": 3,
    "details": [
      {
        "gap_start": "2023-12-25T00:00:00+00:00",
        "gap_end": "2023-12-27T00:00:00+00:00",
        "gap_duration_days": 2.0,
        "missing_candles": 1
      }
    ]
  },
  "quality_issues": {
    "total": 15,
    "by_type": {
      "high_price_deviation": 10,
      "zero_volume": 5
    }
  },
  "sources": {
    "coindesk": 4500,
    "kraken": 300,
    "coingecko": 200
  },
  "quality_score": 99.7
}
```

---

#### GET `/api/enhanced-historical/gaps/{symbol}`

Identify specific gaps in historical data.

**Example:**
```bash
curl "http://localhost:8001/api/enhanced-historical/gaps/ETH"
```

---

### News & Sentiment

#### GET `/api/enhanced-historical/news`

Get crypto news with filtering and sentiment analysis.

**Parameters:**
- `coins` (query, optional): Comma-separated coin symbols (e.g., "BTC,ETH,SOL")
- `start_date` (query, optional): Filter news after this date
- `end_date` (query, optional): Filter news before this date
- `sentiment` (query, optional): Filter by sentiment ("bullish", "bearish", "neutral")
- `limit` (query, default: 50, max: 200): Max results
- `skip` (query, default: 0): Skip results for pagination

**Example:**
```bash
curl "http://localhost:8001/api/enhanced-historical/news?coins=BTC,ETH&sentiment=bullish&limit=10"
```

**Response:**
```json
{
  "news": [
    {
      "id": "abc123...",
      "title": "Bitcoin Surges Past $45,000 Amid ETF Optimism",
      "url": "https://example.com/article",
      "published_at": "2024-02-09T12:00:00+00:00",
      "coins": ["BTC"],
      "sentiment": 0.75,
      "sentiment_label": "bullish",
      "source": "cryptopanic",
      "metadata": {
        "domain": "coindesk.com",
        "kind": "news"
      }
    }
  ],
  "count": 10,
  "total": 150,
  "has_more": true
}
```

---

#### POST `/api/enhanced-historical/news/fetch`

Fetch fresh news from all sources and store in database.

**Parameters:**
- `coins` (query, optional): Comma-separated coin symbols
- `limit` (query, default: 50): Max news items per source
- `force_refresh` (query, default: false): Force refresh

**Example:**
```bash
curl -X POST "http://localhost:8001/api/enhanced-historical/news/fetch?coins=BTC,ETH&limit=100"
```

**Response:**
```json
{
  "fetched": 87,
  "stored": 75,
  "by_source": {
    "cryptopanic": 50,
    "news_service": 37
  },
  "timestamp": "2024-02-09T12:00:00+00:00"
}
```

---

#### GET `/api/enhanced-historical/news/sentiment/{coin}`

Get sentiment summary for a coin over time.

**Parameters:**
- `coin` (path): Coin symbol
- `days` (query, default: 7, max: 90): Number of days to analyze

**Example:**
```bash
curl "http://localhost:8001/api/enhanced-historical/news/sentiment/BTC?days=7"
```

**Response:**
```json
{
  "coin": "BTC",
  "period_days": 7,
  "news_count": 45,
  "sentiment": "bullish",
  "score": 0.42,
  "distribution": {
    "bullish": 25,
    "bearish": 10,
    "neutral": 10
  },
  "latest_news": [
    {
      "title": "Bitcoin ETF Sees Record Inflows",
      "published_at": "2024-02-09T10:00:00+00:00",
      "sentiment": 0.8
    }
  ]
}
```

---

### News-Market Correlation

#### POST `/api/enhanced-historical/correlation/analyze/{coin}`

Analyze correlation between news sentiment and price movements.

**Parameters:**
- `coin` (path): Coin symbol
- `start_date` (query, optional): Start date (default: 30 days ago)
- `end_date` (query, optional): End date (default: now)

**Example:**
```bash
curl -X POST "http://localhost:8001/api/enhanced-historical/correlation/analyze/BTC"
```

**Response:**
```json
{
  "coin": "BTC",
  "period": {
    "start": "2024-01-10T00:00:00+00:00",
    "end": "2024-02-09T00:00:00+00:00"
  },
  "news_count": 120,
  "price_points": 720,
  "correlations": {
    "1h": {
      "correlation": 0.45,
      "p_value": 0.012,
      "sample_size": 120,
      "is_significant": true
    },
    "4h": {
      "correlation": 0.62,
      "p_value": 0.003,
      "sample_size": 115,
      "is_significant": true
    },
    "24h": {
      "correlation": 0.38,
      "p_value": 0.045,
      "sample_size": 100,
      "is_significant": true
    },
    "168h": {
      "correlation": 0.22,
      "p_value": 0.156,
      "sample_size": 80,
      "is_significant": false
    }
  },
  "significant_lags": [
    {
      "lag_period": "4h",
      "correlation": 0.62,
      "p_value": 0.003,
      "sample_size": 115
    },
    {
      "lag_period": "1h",
      "correlation": 0.45,
      "p_value": 0.012,
      "sample_size": 120
    }
  ],
  "insights": [
    "Strong positive correlation (0.62) found at 4h lag. Positive news sentiment tends to predict price increases.",
    "News sentiment is most predictive within 4h timeframe. Consider using this window for trading signals."
  ],
  "analyzed_at": "2024-02-09T12:00:00+00:00"
}
```

---

#### GET `/api/enhanced-historical/correlation/history/{coin}`

Get historical correlation analyses.

**Parameters:**
- `coin` (path): Coin symbol
- `limit` (query, default: 10, max: 50): Max results

---

#### GET `/api/enhanced-historical/signals/{coin}`

Get current predictive trading signals based on news-price correlations.

**Parameters:**
- `coin` (path): Coin symbol
- `recent_hours` (query, default: 24, max: 168): Hours of recent news to analyze

**Example:**
```bash
curl "http://localhost:8001/api/enhanced-historical/signals/BTC?recent_hours=24"
```

**Response:**
```json
{
  "coin": "BTC",
  "signal": "bullish",
  "confidence": 0.756,
  "recent_sentiment": 0.65,
  "sentiment_label": "bullish",
  "news_count": 15,
  "correlation": 0.62,
  "optimal_lag": "4h",
  "reason": "Bullish signal with 75.6% confidence. Recent news sentiment is positive (0.65), and historical correlation is positive (0.62)."
}
```

---

### Multi-Coin Queries

#### GET `/api/enhanced-historical/multi-coin`

Get historical data for multiple coins in parallel.

**Parameters:**
- `symbols` (query): Comma-separated coin symbols (max 10)
- `quote` (query, default: USD): Quote currency
- `days` (query, default: 30, max: 365): Number of days
- `interval` (query, default: daily): Timeframe

**Example:**
```bash
curl "http://localhost:8001/api/enhanced-historical/multi-coin?symbols=BTC,ETH,SOL&days=90"
```

---

### Health Check

#### GET `/api/enhanced-historical/health`

Check health status of historical data system.

**Example:**
```bash
curl "http://localhost:8001/api/enhanced-historical/health"
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "data_freshness": {
    "BTC": {
      "latest_date": "2024-02-09",
      "age_hours": 2.5,
      "is_fresh": true
    },
    "ETH": {
      "latest_date": "2024-02-09",
      "age_hours": 2.5,
      "is_fresh": true
    }
  },
  "timestamp": "2024-02-09T12:00:00+00:00"
}
```

---

## Data Models

### OHLCV Candle
```python
{
  "timestamp": int,          # Unix timestamp (seconds)
  "date": str,              # ISO date string
  "open": float,            # Opening price
  "high": float,            # Highest price
  "low": float,             # Lowest price
  "close": float,           # Closing price
  "volume": float           # Trading volume
}
```

### News Item
```python
{
  "news_id": str,           # Unique hash ID
  "source": str,            # Source name
  "title": str,             # Article title
  "url": str,               # Article URL
  "published_at": datetime, # Publication time
  "coins": List[str],       # Mentioned coins
  "sentiment": {
    "final": float,         # Final weighted score (-1 to 1)
    "vote_based": float,    # Vote-based score
    "ai_based": float       # AI-based score
  },
  "metadata": dict          # Additional metadata
}
```

---

## Use Cases

### 1. **AI Training with Quality Data**
```python
# Get high-quality historical data for training
data = await manager.get_historical_ohlcv(
    symbol="BTC",
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2024, 1, 1)
)

# Check quality before training
quality = await manager.get_quality_report("BTC")
if quality["quality_score"] > 95:
    train_model(data)
```

### 2. **News-Based Trading Signals**
```python
# Get predictive signals
signals = await correlation_analyzer.get_predictive_signals("BTC")

if signals["signal"] == "bullish" and signals["confidence"] > 0.7:
    execute_buy_order("BTC")
```

### 3. **Data Quality Monitoring**
```python
# Monitor data freshness
health = await enhanced_historical.health_check()

for coin, status in health["data_freshness"].items():
    if not status["is_fresh"]:
        trigger_data_refresh(coin)
```

---

## Benefits

1. **Improved AI Training**: Quality-validated data leads to better model performance
2. **Predictive Signals**: News-price correlations provide actionable trading signals
3. **Data Reliability**: Multi-source fallback ensures continuous data availability
4. **Historical Analysis**: Persistent news storage enables backtesting with sentiment data
5. **Quality Monitoring**: Automatic detection of data issues prevents bad training data

---

## Technical Details

### Database Collections

- `historical_ohlcv`: OHLCV candles with quality metadata
- `crypto_news`: News articles with sentiment scores
- `news_market_correlations`: Correlation analysis results

### Indexes
- `(symbol, interval, timestamp)` on historical_ohlcv
- `(news_id)` unique on crypto_news
- `(coins, published_at)` on crypto_news
- `(sentiment.final)` on crypto_news

### Caching Strategy
- Historical data: Database persistence (long-term)
- News data: Database persistence with deduplication
- Correlation results: Stored for historical tracking

---

## Future Enhancements

1. **Real-time WebSocket updates** for live data streaming
2. **More data sources** (Messari, CryptoCompare)
3. **Advanced correlation models** (Granger causality, VAR)
4. **Sentiment breakdown by source** type (Twitter, Reddit, News)
5. **Cross-coin correlation** analysis
6. **Automated data quality alerts**

---

## Support

For issues or questions:
- Check API documentation: http://localhost:8001/api/docs
- Review logs for error details
- Verify database connectivity with health endpoint
