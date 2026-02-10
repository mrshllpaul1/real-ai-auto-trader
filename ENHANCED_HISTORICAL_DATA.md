# Enhanced Historical Market Data

## Overview

The Enhanced Historical Market Data system provides advanced features for storing, analyzing, and querying historical cryptocurrency market data with significant improvements over the basic implementation.

## ✨ Key Enhancements

### 1. **Extended Data Retention**

Dramatically increased retention periods for intraday data to enable comprehensive backtesting and analysis:

| Timeframe | Previous | Enhanced | Improvement |
|-----------|----------|----------|-------------|
| **1h** | 180 days (6 months) | **730 days (2 years)** | +305% |
| **4h** | 365 days (1 year) | **1095 days (3 years)** | +200% |
| **1m** | 7 days | **30 days** | +329% |
| **5m** | 14 days | **60 days** | +329% |
| **15m** | 30 days | **90 days** | +200% |
| **30m** | 60 days | **180 days** | +200% |
| **1D** | 3650 days (10 years) | **3650 days** | Same |
| **1W** | 3650 days (10 years) | **3650 days** | Same |

**Benefits:**
- Full strategy backtesting on short timeframes (1h, 4h)
- Better ML model training with 2-3 years of hourly data
- Long-term pattern analysis on intraday data

### 2. **Enhanced OHLCV Metrics**

Each candle is automatically enriched with advanced technical metrics:

#### Price Metrics
- `price_range`: High - Low (volatility measure)
- `price_change`: Close - Open (absolute change)
- `price_change_pct`: Percentage change
- `body_size`: Absolute body size
- `upper_wick`: Distance from top of body to high
- `lower_wick`: Distance from bottom of body to low
- `volatility`: Intraday range as % of close

#### Pattern Recognition
- `is_bullish`: Bullish candle (close > open)
- `is_doji`: Doji pattern (small body)
- `is_hammer`: Hammer pattern (long lower wick)
- `is_shooting_star`: Shooting star pattern (long upper wick)

#### Quality Metrics
- `quality_score`: Data quality score (0-100)
- Automatic validation of OHLC relationships
- Detection of anomalies and data issues

### 3. **Volume Profile Analysis**

Calculate volume distribution across price levels for any time period:

```python
# Features:
- Point of Control (POC): Price level with highest volume
- Value Area: Range containing 70% of volume
- Volume distribution across 50 price bins
- Total volume analysis
```

**Use Cases:**
- Identify key support/resistance levels
- Find areas of high liquidity
- Detect institutional accumulation zones
- Plan entry/exit points

### 4. **Data Quality Scoring**

Automatic quality validation with scoring (0-100):

#### Quality Checks:
- ✅ Field completeness (all OHLCV fields present)
- ✅ Consistency (high ≥ low, OHLC relationships valid)
- ✅ Reasonableness (no zero prices, realistic volatility)
- ✅ Volume validation (non-zero volume)
- ✅ Anomaly detection (extreme price movements >50%)

#### Quality Distribution:
- **Excellent (90-100)**: Production-ready, highly reliable
- **Good (80-89)**: Minor issues, generally reliable
- **Fair (70-79)**: Some issues, consider re-download
- **Poor (<70)**: Significant issues, re-download recommended

#### Quality Reports:
- Gap detection (missing candles)
- Zero-volume candle count
- Low-quality candle distribution
- Actionable recommendations

### 5. **Historical Event Markers**

Link market movements to real-world events:

#### Event Types:
- `news`: Major news announcements
- `regulatory`: Regulatory changes
- `technical`: Technical events (hard forks, upgrades)
- `whale_movement`: Large transactions
- `market_event`: Market-wide events

#### Features:
- Timestamp-based event storage
- Impact scoring (0-1 scale)
- Symbol-specific or global events
- Rich metadata support
- Source attribution

**Use Cases:**
- Understand price action context
- Analyze event-driven price movements
- Train event-aware ML models
- Generate event-based alerts

## 🚀 API Endpoints

### Service Status
```http
GET /api/enhanced-historical/status
```
Returns service operational status and statistics.

### Store Enhanced OHLCV
```http
POST /api/enhanced-historical/store-ohlcv
Content-Type: application/json

{
  "symbol": "BTC",
  "timeframe": "1h",
  "candles": [
    {
      "timestamp": 1707523200,
      "datetime": "2024-02-10T00:00:00Z",
      "date": "2024-02-10",
      "open": 43000.0,
      "high": 43500.0,
      "low": 42800.0,
      "close": 43200.0,
      "volume": 1000.5,
      "vwap": 43100.0,
      "trade_count": 150
    }
  ],
  "source": "kraken"
}
```

Automatically calculates and stores enhanced metrics.

### Calculate Volume Profile
```http
GET /api/enhanced-historical/volume-profile/{symbol}/{timeframe}?days=7

# Example:
GET /api/enhanced-historical/volume-profile/BTC/1h?days=7
```

Returns volume distribution, POC, and value area.

**Response:**
```json
{
  "symbol": "BTC",
  "timeframe": "1h",
  "total_volume": 125000.5,
  "poc": {
    "price": 43250.0,
    "volume": 12500.3
  },
  "value_area": {
    "high": 43800.0,
    "low": 42700.0,
    "range": 1100.0
  },
  "volume_profile": {
    "42700.00": 5000.2,
    "42800.00": 7500.1,
    ...
  }
}
```

### Add Historical Event
```http
POST /api/enhanced-historical/events/add
Content-Type: application/json

{
  "symbol": "BTC",  # or "GLOBAL" for market-wide
  "timestamp": "2024-02-10T12:00:00Z",
  "event_type": "news",
  "title": "SEC Approves Bitcoin ETF",
  "description": "Major regulatory milestone for crypto adoption",
  "impact_score": 0.9,
  "source": "official",
  "metadata": {
    "url": "https://...",
    "category": "regulatory"
  }
}
```

### Get Historical Events
```http
GET /api/enhanced-historical/events/{symbol}?days=30&event_types=news,regulatory

# Example:
GET /api/enhanced-historical/events/BTC?days=30&event_types=news
```

Returns historical events for analysis.

### Get Data Quality Report
```http
GET /api/enhanced-historical/quality-report/{symbol}/{timeframe}?days=30

# Example:
GET /api/enhanced-historical/quality-report/BTC/1h?days=30
```

**Response:**
```json
{
  "symbol": "BTC",
  "timeframe": "1h",
  "summary": {
    "total_candles": 720,
    "average_quality_score": 94.5,
    "low_quality_candles": 12,
    "zero_volume_candles": 3,
    "data_gaps": 2
  },
  "quality_distribution": {
    "excellent (90-100)": 680,
    "good (80-89)": 28,
    "fair (70-79)": 10,
    "poor (<70)": 2
  },
  "gaps": [
    {
      "from": "2024-02-05T10:00:00Z",
      "to": "2024-02-05T12:00:00Z",
      "gap_seconds": 7200,
      "missing_candles": 1
    }
  ],
  "recommendation": "Excellent data quality. Suitable for all trading strategies."
}
```

### Get Statistics
```http
GET /api/enhanced-historical/stats
```

Returns comprehensive service statistics.

### Get Retention Periods
```http
GET /api/enhanced-historical/retention-periods
```

Returns extended retention configuration.

### Get Features List
```http
GET /api/enhanced-historical/features
```

Returns list of all enhanced features and benefits.

## 💡 Usage Examples

### Example 1: Store Enriched Historical Data
```python
import requests
from datetime import datetime, timezone

# Fetch candles from source
candles = fetch_from_kraken("BTC", "1h")

# Store with automatic enhancements
response = requests.post(
    "http://localhost:8001/api/enhanced-historical/store-ohlcv",
    json={
        "symbol": "BTC",
        "timeframe": "1h",
        "candles": candles,
        "source": "kraken"
    }
)

# Each candle now has:
# - Quality score
# - Volatility metrics
# - Pattern detection
# - Body/wick analysis
```

### Example 2: Analyze Volume Profile
```python
# Get volume profile for last 7 days
response = requests.get(
    "http://localhost:8001/api/enhanced-historical/volume-profile/BTC/1h?days=7"
)

profile = response.json()

# Find Point of Control
poc_price = profile["poc"]["price"]
print(f"POC at ${poc_price:.2f} - highest volume level")

# Find Value Area
va_high = profile["value_area"]["high"]
va_low = profile["value_area"]["low"]
print(f"Value Area: ${va_low:.2f} - ${va_high:.2f}")

# This area contains 70% of volume - likely support/resistance
```

### Example 3: Track Historical Events
```python
# Add event marker
requests.post(
    "http://localhost:8001/api/enhanced-historical/events/add",
    json={
        "symbol": "BTC",
        "timestamp": "2024-02-10T14:30:00Z",
        "event_type": "news",
        "title": "Fed Rate Decision",
        "description": "Federal Reserve holds rates steady",
        "impact_score": 0.8,
        "source": "fed",
        "metadata": {"decision": "hold", "rate": 5.5}
    }
)

# Later, analyze price movements around events
events = requests.get(
    "http://localhost:8001/api/enhanced-historical/events/BTC?days=30&event_types=news"
).json()

for event in events["events"]:
    # Correlate event time with price movement
    analyze_price_impact(event)
```

### Example 4: Monitor Data Quality
```python
# Get quality report
report = requests.get(
    "http://localhost:8001/api/enhanced-historical/quality-report/BTC/1h?days=7"
).json()

avg_quality = report["summary"]["average_quality_score"]

if avg_quality < 80:
    print(f"⚠️  Data quality low ({avg_quality:.1f}%)")
    print(f"Recommendation: {report['recommendation']}")
    
    # Check for gaps
    if report["summary"]["data_gaps"] > 0:
        print(f"Found {report['summary']['data_gaps']} data gaps")
        # Trigger re-download
        backfill_missing_data()
else:
    print(f"✅ Data quality excellent ({avg_quality:.1f}%)")
```

## 🎯 Benefits Summary

### For Trading Strategies
- ✅ Full backtesting on 1h/4h timeframes (2-3 years of data)
- ✅ Volume profile for support/resistance identification
- ✅ Pattern recognition built into every candle
- ✅ Event-aware strategy development

### For ML/AI Models
- ✅ Rich feature set with enhanced metrics
- ✅ Quality-scored data for reliable training
- ✅ Historical context with event markers
- ✅ 2-3x more training data for intraday models

### For Risk Management
- ✅ Data quality validation before trading
- ✅ Gap detection prevents strategy failures
- ✅ Volume profile for liquidity analysis
- ✅ Historical event impact analysis

### For Analysis
- ✅ Comprehensive candle analysis
- ✅ Pattern detection automation
- ✅ Event-driven price movement studies
- ✅ Long-term trend analysis on short timeframes

## 🔧 Technical Details

### Database Collections
- `enhanced_ohlcv`: Enhanced OHLCV candles
- `historical_events`: Event markers
- `volume_profile`: Calculated volume profiles
- `data_quality`: Quality reports

### Indexes
- `(symbol, timeframe, timestamp)`: Primary query index
- `(symbol, quality_score)`: Quality filtering
- `(symbol, timestamp)`: Event queries
- `timestamp`: Time-range queries

### Performance
- Batch operations with MongoDB `bulk_write`
- Upsert logic prevents duplicates
- Efficient aggregation pipelines
- Caching for frequently accessed data

## 📊 Comparison with Basic Implementation

| Feature | Basic | Enhanced |
|---------|-------|----------|
| 1h retention | 6 months | **2 years** |
| 4h retention | 1 year | **3 years** |
| Metrics per candle | 8 | **20+** |
| Pattern detection | ❌ | ✅ |
| Quality scoring | ❌ | ✅ |
| Volume profile | ❌ | ✅ |
| Event markers | ❌ | ✅ |
| Gap detection | ❌ | ✅ |

## 🚀 Getting Started

1. **Service automatically initializes** with the backend
2. **Start storing enhanced data**:
   ```python
   POST /api/enhanced-historical/store-ohlcv
   ```
3. **Monitor quality**:
   ```python
   GET /api/enhanced-historical/quality-report/BTC/1h
   ```
4. **Analyze volume**:
   ```python
   GET /api/enhanced-historical/volume-profile/BTC/1h?days=7
   ```
5. **Add event context**:
   ```python
   POST /api/enhanced-historical/events/add
   ```

## 📝 Notes

- Enhanced storage uses more disk space (~2x) due to additional metrics
- Quality scoring adds minimal processing overhead (<5ms per candle)
- Volume profile calculation is computationally intensive - use sparingly
- Event markers are optional but highly recommended for context

## 🆘 Support

For issues or questions:
- Check `/api/enhanced-historical/status` for service health
- Review quality reports for data issues
- Consult feature documentation at `/api/enhanced-historical/features`

---

**Version:** 1.0  
**Last Updated:** February 10, 2026  
**Status:** ✅ Operational
