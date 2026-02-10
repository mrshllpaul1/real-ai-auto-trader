# Enhanced Historical Market and Media Data Integration

## Overview

This document describes the enhanced historical market and media data integration system, which provides comprehensive sentiment tracking, multi-source market data validation, and advanced news-price correlation analysis.

## New Services

### 1. Historical Sentiment Tracker

**File**: `backend/services/historical_sentiment_tracker.py`

Provides persistent storage and analysis of sentiment data over time.

#### Features

- **Persistent Storage**: Store sentiment readings with timestamps for historical analysis
- **Daily Snapshots**: Aggregate daily sentiment data for efficient querying
- **Trend Analysis**: Calculate sentiment trends with momentum and volatility metrics
- **Multi-Coin Support**: Track sentiment for unlimited cryptocurrencies
- **Efficient Querying**: Indexed database queries for fast retrieval

#### Key Methods

```python
# Store a sentiment reading
await sentiment_tracker.store_sentiment(
    coin_id='bitcoin',
    sentiment_data={
        'score': 75,
        'label': 'bullish',
        'confidence': 80,
        # ... other fields
    },
    metadata={'price': 97000, 'volume': 50000000000}
)

# Get sentiment history
history = await sentiment_tracker.get_coin_sentiment_history(
    coin_id='bitcoin',
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 2, 1),
    limit=100
)

# Create daily snapshots
snapshot_result = await sentiment_tracker.create_daily_snapshot()

# Get daily snapshots
snapshots = await sentiment_tracker.get_daily_snapshots(
    coin_id='bitcoin',
    start_date='2025-01-01',
    end_date='2025-02-01'
)

# Analyze sentiment trend
trend = await sentiment_tracker.get_sentiment_trend(
    coin_id='bitcoin',
    days=30
)
```

#### Database Collections

- **historical_sentiment**: Individual sentiment readings
- **daily_sentiment_snapshots**: Daily aggregated snapshots

---

### 2. Enhanced Market Data Integrator

**File**: `backend/services/enhanced_market_data_integrator.py`

Provides multi-source price validation with quality scoring and anomaly detection.

#### Features

- **Multi-Source Validation**: Cross-validate prices from CoinGecko, CoinMarketCap, and CoinStats
- **Data Quality Scoring**: Calculate quality metrics based on source agreement
- **Anomaly Detection**: Identify price discrepancies across sources
- **Intelligent Failover**: Automatically switch to backup sources on failure
- **Source Monitoring**: Track availability and response times

#### Key Methods

```python
# Get validated price from multiple sources
price_data = await market_integrator.get_validated_price(
    coin_id='bitcoin',
    validate=True  # Enable multi-source validation
)

# Response includes:
{
    'price_usd': 97000,
    'price_change_24h': 2.5,
    'source': 'coinmarketcap',
    'validated': True,
    'quality_score': 0.95,
    'sources_checked': 3,
    'validation': {
        'avg_price': 97000,
        'price_variance': 0.001,
        'anomalies_detected': 0
    }
}

# Get data quality report
report = await market_integrator.get_data_quality_report()

# Get source status
status = market_integrator.get_source_status()
```

#### Data Sources

| Source | Priority | Use Case |
|--------|----------|----------|
| CoinMarketCap | 1 | Institutional-grade data, accurate market cap |
| CoinGecko | 2 | Community-driven, comprehensive historical data |
| CoinStats | 3 | Additional validation, portfolio tracking |

---

### 3. Enhanced Correlation Service

**File**: `backend/services/enhanced_correlation_service.py`

Analyzes correlations between news sentiment and price movements.

#### Features

- **Multi-Timeframe Analysis**: Analyze impact across 15min, 1h, 4h, and 24h windows
- **Sentiment Alignment**: Detect if price moves align with sentiment direction
- **Lagged Impact Detection**: Identify time delays between news and price reaction
- **Market vs Coin Impact**: Distinguish coin-specific from market-wide events
- **Batch Processing**: Analyze multiple news events efficiently

#### Key Methods

```python
# Analyze news impact
impact = await correlation_service.analyze_news_impact(
    coin_id='bitcoin',
    news_timestamp=datetime(2025, 2, 1, 10, 0),
    news_sentiment={
        'score': 70,
        'label': 'bullish',
        'confidence': 80
    }
)

# Response includes:
{
    'coin_id': 'bitcoin',
    'overall_impact': 'moderate_positive',
    'confidence': 0.75,
    'timeframe_analysis': {
        '1h': {
            'price_change_pct': 2.3,
            'alignment': True,
            'significant': True
        },
        # ... other timeframes
    }
}

# Detect lagged impact
lag_analysis = await correlation_service.detect_lagged_impact(
    coin_id='bitcoin',
    news_timestamp=datetime(2025, 2, 1, 10, 0),
    max_lag_hours=24
)

# Compare market vs coin impact
comparison = await correlation_service.compare_market_vs_coin_impact(
    coin_id='ethereum',
    news_timestamp=datetime(2025, 2, 1, 10, 0),
    market_proxy='bitcoin'
)

# Get correlation summary
summary = await correlation_service.get_correlation_summary(
    coin_id='bitcoin',
    days=30
)
```

---

### 4. Daily Sentiment Snapshot Scheduler

**File**: `backend/services/daily_snapshot_scheduler.py`

Background task that automatically creates daily sentiment snapshots at midnight UTC.

#### Features

- **Automated Snapshots**: Runs daily at midnight UTC
- **Error Recovery**: Retries on failure with exponential backoff
- **Graceful Shutdown**: Properly cancels on server shutdown

#### Usage

```python
# Automatically started during server initialization
# See backend/init/services.py Phase 7

# Manual control:
from services.daily_snapshot_scheduler import DailySentimentSnapshotTask

task = DailySentimentSnapshotTask(sentiment_tracker)
task.start()  # Start scheduler
task.stop()   # Stop scheduler
```

---

## API Endpoints

### Base URL: `/api/data-integration`

All endpoints are automatically registered and available after server startup.

### Sentiment Endpoints

#### `GET /data-integration/sentiment/status`
Get service status and statistics

**Response:**
```json
{
  "status": "operational",
  "service": "historical_sentiment_tracker",
  "statistics": {
    "total_sentiment_records": 1250,
    "total_daily_snapshots": 45,
    "unique_coins_tracked": 25,
    "coins": ["bitcoin", "ethereum", ...]
  }
}
```

#### `POST /data-integration/sentiment/store`
Store a sentiment reading

**Request:**
```json
{
  "coin_id": "bitcoin",
  "sentiment_data": {
    "score": 75,
    "label": "bullish",
    "confidence": 80,
    "summary": "Strong bullish sentiment",
    "key_factors": ["ETF approval", "Institutional buying"]
  },
  "metadata": {
    "price": 97000,
    "volume": 50000000000
  }
}
```

#### `GET /data-integration/sentiment/history/{coin_id}`
Get sentiment history for a coin

**Query Parameters:**
- `start_date`: ISO date string (optional)
- `end_date`: ISO date string (optional)
- `limit`: Max records (default: 100)

**Example:**
```
GET /api/data-integration/sentiment/history/bitcoin?limit=50
```

#### `POST /data-integration/sentiment/snapshot/create`
Create daily sentiment snapshots

**Request:**
```json
{
  "date": "2025-02-01"  // Optional, defaults to today
}
```

#### `GET /data-integration/sentiment/snapshots`
Get daily sentiment snapshots

**Query Parameters:**
- `coin_id`: Filter by coin (optional)
- `start_date`: ISO date (optional)
- `end_date`: ISO date (optional)
- `limit`: Max snapshots (default: 365)

#### `GET /data-integration/sentiment/trend/{coin_id}`
Analyze sentiment trend over time

**Query Parameters:**
- `days`: Number of days to analyze (default: 30)

**Response:**
```json
{
  "coin_id": "bitcoin",
  "trend_direction": "rising",
  "momentum": 2.5,
  "volatility": 8.3,
  "score_range": {
    "min": 45,
    "max": 75,
    "avg": 62
  },
  "snapshots": [...]
}
```

---

### Market Data Endpoints

#### `GET /data-integration/market/validated-price/{coin_id}`
Get multi-source validated price

**Query Parameters:**
- `validate`: Enable validation (default: true)

**Response:**
```json
{
  "coin_id": "bitcoin",
  "price_usd": 97000,
  "price_change_24h": 2.5,
  "market_cap": 1900000000000,
  "volume_24h": 50000000000,
  "source": "coinmarketcap",
  "validated": true,
  "quality_score": 0.95,
  "sources_checked": 3,
  "validation": {
    "avg_price": 97000,
    "price_variance": 0.001,
    "anomalies_detected": 0,
    "anomalies": null
  }
}
```

#### `GET /data-integration/market/quality-report`
Get comprehensive data quality report

**Response:**
```json
{
  "timestamp": "2025-02-01T10:00:00Z",
  "sources": {
    "coinmarketcap": {
      "available": true,
      "priority": 1,
      "success_rate": 0.98,
      "avg_response_time": 0.345,
      "total_failures": 2
    },
    "coingecko": {
      "available": true,
      "priority": 2,
      "success_rate": 0.95,
      "avg_response_time": 0.892,
      "total_failures": 5
    }
  }
}
```

#### `GET /data-integration/market/source-status`
Get current status of all data sources

---

### Correlation Endpoints

#### `GET /data-integration/market/news-correlation/{coin_id}`
Analyze news-price correlation

**Query Parameters:**
- `news_timestamp`: ISO timestamp
- `lookback_hours`: Hours before news (default: 4)
- `lookahead_hours`: Hours after news (default: 4)

---

### Combined Analysis

#### `GET /data-integration/combined/sentiment-and-price/{coin_id}`
Get combined sentiment and price analysis

**Response:**
```json
{
  "coin_id": "bitcoin",
  "timestamp": "2025-02-01T10:00:00Z",
  "market_data": {
    "price_usd": 97000,
    "validated": true,
    "quality_score": 0.95
  },
  "sentiment_data": {
    "avg_score": 65,
    "overall_label": "bullish",
    "total_news": 150
  },
  "sentiment_trend": {
    "trend_direction": "rising",
    "momentum": 2.5
  }
}
```

---

## Integration with Existing Services

### AI News Sentiment Service

The `AINewsSentimentService` automatically stores sentiment data in the historical tracker:

```python
# In ai_news_sentiment.py
sentiment_service = AINewsSentimentService(db, historical_tracker=sentiment_tracker)

# When sentiment is analyzed, it's automatically stored
sentiment = await sentiment_service.get_coin_sentiment('bitcoin', 'BTC')
# ^ This now stores in historical_sentiment collection
```

### Market Data Service

Enhanced market data integrator complements the existing `MarketDataService`:

```python
# Existing service for basic data
market_service = MarketDataService()
price = await market_service.get_coin_price(['bitcoin'])

# Enhanced service for validated data
market_integrator = EnhancedMarketDataIntegrator()
validated_price = await market_integrator.get_validated_price('bitcoin', validate=True)
```

---

## Configuration

### Environment Variables

No new environment variables required. Uses existing API keys:

- `COINMARKETCAP_API_KEY`: Already configured
- `COINSTATS_API_KEY`: Already configured
- CoinGecko: Free tier (no key required)

### Database Indexes

Indexes are automatically created on initialization:

```python
# historical_sentiment collection
- (coin_id, timestamp) compound index
- timestamp index

# daily_sentiment_snapshots collection
- (coin_id, date) unique compound index
- date index
```

---

## Scheduled Tasks

### Daily Sentiment Snapshot

**Schedule**: Every day at midnight UTC  
**Action**: Creates aggregated daily snapshots for all tracked coins  
**Startup**: Automatically started in Phase 7 initialization  

---

## Monitoring and Logging

All services log important events:

```
✅ Historical sentiment tracker initialized
✅ Enhanced market data integrator initialized
✅ Enhanced correlation service initialized
✅ Daily Sentiment Snapshot Scheduler started
```

Use the status endpoints to monitor service health:

```bash
# Check sentiment tracker status
curl http://localhost:8001/api/data-integration/sentiment/status

# Check market data quality
curl http://localhost:8001/api/data-integration/market/quality-report

# Overall health check
curl http://localhost:8001/api/data-integration/health
```

---

## Best Practices

### For Sentiment Analysis

1. **Batch Processing**: Use `get_batch_sentiment()` for multiple coins
2. **Caching**: Sentiment is cached for 1 hour by default
3. **Daily Snapshots**: Query snapshots for historical analysis (more efficient)
4. **Cleanup**: Old detailed records are kept for 90 days by default

### For Price Validation

1. **Enable Validation**: Set `validate=True` for critical trading decisions
2. **Quality Threshold**: Data with quality_score < 0.7 may be unreliable
3. **Check Anomalies**: Review anomaly reports for price discrepancies
4. **Failover**: Service automatically handles source failures

### For Correlation Analysis

1. **Multi-Timeframe**: Always analyze multiple timeframes (15min - 24h)
2. **Confidence Score**: Consider confidence >= 0.7 as reliable
3. **Alignment**: Check if price direction matches sentiment
4. **Lag Detection**: Some news takes hours to impact price

---

## Performance Considerations

### Database Queries

- Indexed queries are fast (< 10ms)
- Daily snapshots reduce query load for historical data
- Batch operations process multiple coins efficiently

### API Rate Limits

- CoinMarketCap: 333 calls/day (basic plan)
- CoinStats: 500 calls/day (free tier)
- CoinGecko: 50 calls/minute (free tier)

Services automatically handle rate limits with caching and failover.

### Memory Usage

- In-memory cache for recent sentiment (< 1MB)
- Database for historical data
- Automatic cleanup of old records

---

## Troubleshooting

### Issue: No sentiment data available

**Solution**: Ensure sentiment analysis is running for the coins you need:
```python
sentiment = await ai_sentiment_service.get_coin_sentiment('bitcoin', 'BTC')
```

### Issue: All market data sources failing

**Solution**: Check API keys in `.env`:
```bash
COINMARKETCAP_API_KEY=your_key_here
COINSTATS_API_KEY=your_key_here
```

### Issue: Daily snapshots not being created

**Solution**: Check scheduler is running:
```bash
curl http://localhost:8001/api/data-integration/sentiment/status
```

### Issue: Correlation analysis returns "insufficient_data"

**Solution**: Ensure historical OHLCV data is available:
```bash
curl http://localhost:8001/api/historical-data/stats
```

---

## Future Enhancements

Planned improvements:

1. **Real-time Streaming**: WebSocket updates for sentiment changes
2. **ML-Based Correlation**: Machine learning models for better correlation detection
3. **More Data Sources**: Messari, Glassnode, CryptoQuant
4. **On-Chain Integration**: Whale tracking and exchange flows
5. **Social Media**: Twitter/X API integration for real-time sentiment

---

## Support

For issues or questions:
- Check server logs for error messages
- Use health check endpoints for diagnostics
- Review API documentation at `/api/docs`

---

*Last Updated: 2025-02-10*
*Version: 1.0*
