# Historical Media Data Enhancement

## Overview

The Historical Media Data enhancement adds persistent storage and analysis capabilities for news, social media, and sentiment data. This enables:

1. **Long-term historical analysis** of news and sentiment trends
2. **News-price correlation** to understand how news impacts cryptocurrency prices
3. **ML model training** on combined news+price datasets
4. **Backtesting with news context** to improve strategy development

## Architecture

### Services

#### 1. HistoricalMediaService
**Location:** `backend/services/historical_media_service.py`

Core service for archiving and managing historical media data.

**Features:**
- Persistent news archival in MongoDB
- Batch processing with deduplication
- Efficient time-series queries
- Sentiment extraction and scoring
- Market-moving news detection
- Statistics and analytics

**Database Collections:**
- `news_archive` - Historical news articles
- `sentiment_history` - Time-series sentiment data
- `news_price_correlations` - News-price relationships
- `media_events` - Major market events

#### 2. NewsPriceCorrelationService
**Location:** `backend/services/news_price_correlation.py`

Analyzes correlations between news events and price movements.

**Features:**
- Price impact analysis at multiple time windows (1h, 4h, 12h, 24h)
- Correlation strength calculation (0-1 scale)
- Volume change tracking
- ML dataset generation
- Batch correlation analysis

## API Endpoints

### News Archive Endpoints

#### Get Service Status
```http
GET /api/historical-media/status
```

Returns service status and statistics.

**Response:**
```json
{
  "status": "operational",
  "statistics": {
    "total_articles": 5420,
    "sentiment_breakdown": {
      "positive": 2100,
      "neutral": 2320,
      "negative": 1000
    },
    "market_moving_count": 145
  }
}
```

#### Archive News Batch
```http
POST /api/historical-media/archive/news
Content-Type: application/json

{
  "source": "cryptopanic",
  "articles": [...]
}
```

Archives a batch of news articles.

#### Query Historical News
```http
GET /api/historical-media/news/historical?coin=BTC&days=30&sentiment=positive&limit=100
```

**Query Parameters:**
- `coin` - Filter by cryptocurrency symbol (optional)
- `days` - Number of days to look back (default: 30)
- `sentiment` - Filter by sentiment (positive/negative/neutral)
- `impact_min` - Minimum impact score (0-100)
- `limit` - Maximum results (default: 100)
- `skip` - Pagination offset (default: 0)

**Response:**
```json
{
  "articles": [...],
  "count": 45,
  "total_count": 234,
  "pagination": {
    "has_more": true
  }
}
```

#### Get News Timeline
```http
GET /api/historical-media/news/timeline/BTC?days=7
```

Returns chronological news events for a specific cryptocurrency, perfect for overlaying on price charts.

**Response:**
```json
{
  "coin_symbol": "BTC",
  "timeline": {
    "2024-01-15": [
      {
        "title": "SEC Approves Bitcoin ETF",
        "sentiment": "positive",
        "impact": true,
        "published_at": "2024-01-15T10:30:00Z"
      }
    ]
  },
  "total_events": 42
}
```

### Correlation Analysis Endpoints

#### Analyze News-Price Correlation
```http
POST /api/historical-media/correlations/analyze/BTC?days=7
```

Analyzes correlation between news and price movements for a cryptocurrency.

**Response:**
```json
{
  "status": "completed",
  "coin_symbol": "BTC",
  "analyzed_count": 56,
  "correlated_count": 34,
  "correlation_rate": 60.7
}
```

#### Get Correlation Records
```http
GET /api/historical-media/correlations/list?coin=BTC&days=30&min_correlation=0.5
```

**Response:**
```json
{
  "correlations": [
    {
      "article_id": "...",
      "coin_symbol": "BTC",
      "sentiment_score": 75,
      "price_changes": {
        "1h": 2.3,
        "4h": 3.8,
        "24h": 5.1
      },
      "correlation_strength": 0.82
    }
  ],
  "count": 23
}
```

#### Get Correlation Statistics
```http
GET /api/historical-media/correlations/statistics?coin=BTC&days=30
```

**Response:**
```json
{
  "statistics": {
    "total_analyzed": 156,
    "correlated_count": 94,
    "correlation_rate": 60.3,
    "avg_correlation_strength": 0.543,
    "max_correlation_strength": 0.923
  }
}
```

#### Generate ML Training Dataset
```http
GET /api/historical-media/correlations/ml-dataset/BTC?days=365&min_correlation=0.3
```

Generates a complete ML training dataset with features and labels.

**Response:**
```json
{
  "coin_symbol": "BTC",
  "dataset": [
    {
      "features": {
        "sentiment_score": 75,
        "is_market_moving": 1,
        "price_before": 45000,
        "hour_of_day": 14,
        "day_of_week": 2
      },
      "labels": {
        "1h": 2.3,
        "4h": 3.8,
        "12h": 4.2,
        "24h": 5.1
      },
      "correlation_strength": 0.82
    }
  ],
  "sample_count": 1234,
  "features": ["sentiment_score", "is_market_moving", "price_before", "hour_of_day", "day_of_week"],
  "labels": ["1h", "4h", "12h", "24h"]
}
```

## Usage Examples

### 1. Archive Latest News

```python
# Fetch and archive latest news automatically
import httpx

response = await httpx.post(
    "http://localhost:8001/api/historical-media/archive/live-news",
    params={"sources": "all", "limit_per_source": 50}
)
```

### 2. Query Historical News for Backtesting

```python
# Get all positive sentiment BTC news from last 30 days
response = await httpx.get(
    "http://localhost:8001/api/historical-media/news/historical",
    params={
        "coin": "BTC",
        "days": 30,
        "sentiment": "positive",
        "impact_min": 50,
        "limit": 100
    }
)

articles = response.json()["articles"]
```

### 3. Analyze News-Price Correlation

```python
# Analyze correlation for Bitcoin over last 7 days
response = await httpx.post(
    "http://localhost:8001/api/historical-media/correlations/analyze/BTC",
    params={"days": 7}
)

# Get results
stats = response.json()
print(f"Correlation rate: {stats['correlation_rate']}%")
```

### 4. Generate ML Training Dataset

```python
# Get training data for BTC with last year of correlations
response = await httpx.get(
    "http://localhost:8001/api/historical-media/correlations/ml-dataset/BTC",
    params={"days": 365, "min_correlation": 0.3}
)

dataset = response.json()["dataset"]

# Use for model training
for sample in dataset:
    features = sample["features"]
    labels = sample["labels"]
    # Train your model...
```

## Database Schema

### news_archive Collection
```javascript
{
  article_id: String,           // Unique identifier
  title: String,                // Article title
  description: String,          // Article description
  url: String,                  // Source URL
  source: String,               // Source name (cryptopanic, etc)
  published_at: Date,           // Publication timestamp
  fetched_at: Date,             // When archived
  sentiment: String,            // positive/negative/neutral
  sentiment_score: Number,      // 0-100
  currencies: [String],         // Affected coins
  impact_keywords: [String],    // High-impact keywords
  is_market_moving: Boolean,    // Impact flag
  indexed_at: Date              // Index timestamp
}
```

### news_price_correlations Collection
```javascript
{
  article_id: String,           // Reference to news_archive
  coin_symbol: String,          // Cryptocurrency symbol
  published_at: Date,           // News timestamp
  sentiment_score: Number,      // 0-100
  price_before: Number,         // Price before news
  price_changes: {              // Price changes at various windows
    "1h": Number,
    "4h": Number,
    "12h": Number,
    "24h": Number
  },
  volume_changes: {             // Volume changes
    "1h": Number,
    "4h": Number
  },
  correlation_strength: Number, // 0-1
  is_correlated: Boolean,       // Strong correlation flag
  analyzed_at: Date             // Analysis timestamp
}
```

## Indexes

All collections have optimized indexes for efficient queries:

```javascript
// news_archive indexes
db.news_archive.createIndex({"published_at": -1})
db.news_archive.createIndex({"currencies": 1, "published_at": -1})
db.news_archive.createIndex({"sentiment_score": -1})
db.news_archive.createIndex({"source": 1, "article_id": 1}, {unique: true})

// news_price_correlations indexes
db.news_price_correlations.createIndex({"published_at": -1})
db.news_price_correlations.createIndex({"coin_symbol": 1, "published_at": -1})
db.news_price_correlations.createIndex({"is_correlated": 1, "correlation_strength": -1})
```

## Integration with ML Models

The generated datasets can be directly used for training ML models:

```python
from services.news_price_correlation import NewsPriceCorrelationService

# Get training data
dataset = await correlation_service.generate_ml_training_dataset(
    coin_symbol="BTC",
    days=365,
    min_correlation=0.3
)

# Prepare features and labels
X = [sample["features"] for sample in dataset]
y = [sample["labels"]["24h"] for sample in dataset]  # Predict 24h price change

# Train model
model.fit(X, y)
```

## Monitoring and Maintenance

### Check Archive Statistics
```http
GET /api/historical-media/statistics?days=30
```

### Initialize Database Indexes
```http
POST /api/historical-media/initialize-indexes
```

### Clean Up Old Data
```http
DELETE /api/historical-media/news/cleanup?days_to_keep=730
```

Removes news older than specified days (default: 2 years).

## Benefits

1. **Historical Context**: Understand how news affected prices in the past
2. **ML Training**: Train models on news+price relationships
3. **Backtesting**: Test strategies with historical news context
4. **Pattern Recognition**: Identify recurring news-driven patterns
5. **Risk Management**: Anticipate price reactions to similar news
6. **Alpha Generation**: Use news sentiment as a trading signal

## Future Enhancements

- Real-time correlation monitoring
- Advanced NLP for news categorization
- Multi-coin impact analysis
- Social media sentiment integration
- Event clustering and pattern detection
- Predictive models for news impact

## Support

For questions or issues, contact the development team or file an issue in the repository.
