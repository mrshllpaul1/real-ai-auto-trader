# Historical Market Data Updates

Guide to updating and maintaining historical market data.

## 🔄 Update Schedule

### Automatic Updates
| Data Type | Frequency | Time |
|-----------|-----------|------|
| 1-minute OHLCV | Every 1 min | Continuous |
| Hourly OHLCV | Every hour | :00 |
| Daily OHLCV | Daily | 00:05 UTC |
| Market Cap | Daily | 00:10 UTC |
| Indicators | Hourly | :05 |

### Manual Updates
```bash
# Update specific coin
POST /api/historical-data/update/{symbol}

# Bulk update
POST /api/historical-data/update/bulk
{"symbols": ["BTC", "ETH", "SOL"], "days": 30}

# Full refresh
POST /api/historical-data/refresh/all
```

## 📊 Data Sources

### Primary Sources
```python
DATA_SOURCES = {
    'ohlcv': {
        'primary': 'cryptocompare',
        'fallback': 'coingecko',
        'tertiary': 'kraken'
    },
    'market_cap': {
        'primary': 'coingecko',
        'fallback': 'coinmarketcap'
    },
    'volume': {
        'primary': 'cryptocompare',
        'fallback': 'coingecko'
    }
}
```

### Failover Logic
```python
async def fetch_ohlcv(symbol, timeframe):
    for source in DATA_SOURCES['ohlcv'].values():
        try:
            data = await fetch_from_source(source, symbol, timeframe)
            if validate_data(data):
                return data
        except Exception as e:
            logger.warning(f"Source {source} failed: {e}")
            continue
    raise DataFetchError("All sources failed")
```

## 🛠️ Update Process

### Step 1: Fetch New Data
```python
async def update_historical_data(symbol, days=1):
    # Determine last update time
    last_update = await get_last_update_time(symbol)
    
    # Fetch new data
    new_data = await fetch_ohlcv(
        symbol,
        start=last_update,
        end=datetime.utcnow()
    )
    
    return new_data
```

### Step 2: Validate Data
```python
def validate_data(data):
    checks = [
        check_no_gaps(data),
        check_no_outliers(data),
        check_volume_consistency(data),
        check_price_continuity(data)
    ]
    return all(checks)
```

### Step 3: Store Data
```python
async def store_data(data, symbol, timeframe):
    collection = f"ohlcv_{timeframe}"
    
    # Upsert to handle duplicates
    for candle in data:
        await db[collection].update_one(
            {'symbol': symbol, 'timestamp': candle['timestamp']},
            {'$set': candle},
            upsert=True
        )
```

### Step 4: Update Indicators
```python
async def update_indicators(symbol):
    # Fetch recent data
    data = await get_ohlcv(symbol, days=200)
    
    # Calculate indicators
    indicators = calculate_all_indicators(data)
    
    # Store
    await store_indicators(symbol, indicators)
```

## 📈 Data Quality

### Gap Detection
```python
def detect_gaps(data, timeframe):
    expected_interval = TIMEFRAME_INTERVALS[timeframe]
    gaps = []
    
    for i in range(1, len(data)):
        actual_interval = data[i]['timestamp'] - data[i-1]['timestamp']
        if actual_interval > expected_interval * 1.5:
            gaps.append({
                'start': data[i-1]['timestamp'],
                'end': data[i]['timestamp'],
                'missing_candles': actual_interval // expected_interval - 1
            })
    
    return gaps
```

### Gap Filling
```python
async def fill_gaps(symbol, gaps):
    for gap in gaps:
        # Try alternative sources
        filled_data = await fetch_from_alternative_sources(
            symbol,
            gap['start'],
            gap['end']
        )
        
        if filled_data:
            await store_data(filled_data, symbol)
        else:
            # Interpolate if no source available
            interpolated = interpolate_candles(gap)
            await store_data(interpolated, symbol, interpolated=True)
```

## 📡 API Endpoints

### Check Update Status
```bash
GET /api/historical-data/status
```

Response:
```json
{
  "last_update": "2026-02-14T12:00:00Z",
  "symbols_updated": 500,
  "gaps_detected": 3,
  "gaps_filled": 2,
  "next_update": "2026-02-14T13:00:00Z"
}
```

### Trigger Manual Update
```bash
POST /api/historical-data/update
{
  "symbols": ["BTC", "ETH"],
  "timeframes": ["1h", "1D"],
  "days": 7
}
```

### Get Update History
```bash
GET /api/historical-data/update-history?limit=10
```

## ⚙️ Configuration

### Update Settings
```python
UPDATE_CONFIG = {
    'batch_size': 50,           # Symbols per batch
    'rate_limit': 10,           # Requests per second
    'timeout': 30,              # Seconds
    'retry_attempts': 3,
    'gap_fill_enabled': True,
    'validate_on_insert': True
}
```

### Retention Policy
```python
RETENTION_POLICY = {
    '1m': 7,      # days
    '5m': 30,
    '1h': 365,
    '4h': 730,    # 2 years
    '1D': 3650    # 10 years
}
```

## 🔔 Monitoring

### Alerts
```python
UPDATE_ALERTS = {
    'update_failed': {
        'consecutive_failures': 3,
        'notify': ['email', 'slack']
    },
    'gap_detected': {
        'min_gap_hours': 4,
        'notify': ['app']
    },
    'data_quality': {
        'outlier_threshold': 5,  # std deviations
        'notify': ['app']
    }
}
```

## ✅ Update Features Implemented

- [x] Automatic scheduled updates
- [x] Multi-source failover
- [x] Data validation
- [x] Gap detection and filling
- [x] Indicator recalculation
- [x] Manual update triggers
- [x] Update history tracking
- [x] Alert system
- [x] Retention management

---

**Status**: Updated ✅
**Last Updated**: February 2026
