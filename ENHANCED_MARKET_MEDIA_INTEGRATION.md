# Enhanced Market Media Integration

Comprehensive guide to market media and news integration.

## 📰 Media Sources

### News Aggregators
| Source | Type | Update Frequency | Coverage |
|--------|------|------------------|----------|
| CryptoPanic | Aggregator | Real-time | Global |
| CoinDesk | News | Real-time | Global |
| CoinTelegraph | News | Real-time | Global |
| The Block | News | Hourly | Institutional |
| Decrypt | News | Hourly | Consumer |

### Social Media
| Platform | Data Type | API Access |
|----------|-----------|------------|
| Twitter/X | Mentions, trends | v2 API |
| Reddit | r/cryptocurrency, r/bitcoin | PRAW |
| Telegram | Channel messages | Bot API |
| Discord | Server activity | Webhook |

### On-Chain Data
| Provider | Metrics | Update |
|----------|---------|--------|
| Glassnode | Whale activity | Real-time |
| Santiment | Social volume | Hourly |
| IntoTheBlock | Holder stats | Daily |

## 🔗 Integration Architecture

### Data Flow
```
Media Sources
    ↓
API Fetchers (Rate Limited)
    ↓
Normalization Layer
    ↓
Sentiment Analysis
    ↓
MongoDB Storage
    ↓
Redis Cache
    ↓
Frontend Display
```

### Fetcher Configuration
```python
MEDIA_FETCHERS = {
    'cryptopanic': {
        'interval': 60,  # seconds
        'max_items': 50,
        'categories': ['news', 'media']
    },
    'twitter': {
        'interval': 300,
        'keywords': ['bitcoin', 'ethereum', 'crypto'],
        'min_followers': 1000
    },
    'reddit': {
        'interval': 600,
        'subreddits': ['cryptocurrency', 'bitcoin', 'ethereum'],
        'min_score': 100
    }
}
```

## 📊 Sentiment Analysis

### Processing Pipeline
```python
def analyze_media_item(item):
    # 1. Extract text
    text = extract_text(item)
    
    # 2. Keyword analysis
    keyword_score = analyze_keywords(text)
    
    # 3. LLM analysis (for important items)
    if item['importance'] >= 'high':
        llm_score = llm_sentiment(text)
    else:
        llm_score = None
    
    # 4. Combine scores
    final_score = combine_scores(keyword_score, llm_score)
    
    return {
        'score': final_score,
        'label': score_to_label(final_score),
        'keywords': extract_keywords(text)
    }
```

### Sentiment Labels
| Score Range | Label | Color |
|-------------|-------|-------|
| 0.8 - 1.0 | Very Bullish | 🟢 Green |
| 0.6 - 0.8 | Bullish | 🟢 Light Green |
| 0.4 - 0.6 | Neutral | 🟡 Yellow |
| 0.2 - 0.4 | Bearish | 🔴 Light Red |
| 0.0 - 0.2 | Very Bearish | 🔴 Red |

## 📡 API Endpoints

### Get News Feed
```bash
GET /api/media/news?limit=20&sentiment=all
```

### Get Trending Topics
```bash
GET /api/media/trending
```

### Get Social Mentions
```bash
GET /api/media/social/{coin_id}
```

### Get Media Sentiment
```bash
GET /api/media/sentiment?timeframe=24h
```

## 🎨 UI Components

### News Feed Widget
```jsx
<NewsFeed
    sources={['cryptopanic', 'twitter']}
    sentiment={['bullish', 'neutral']}
    coins={['BTC', 'ETH']}
    limit={10}
    onItemClick={handleNewsClick}
/>
```

### Sentiment Gauge
```jsx
<SentimentGauge
    score={0.65}
    label="Bullish"
    trend="up"
    change={0.05}
/>
```

### Trending Topics
```jsx
<TrendingTopics
    topics={trendingTopics}
    onTopicClick={handleTopicClick}
/>
```

## 🔔 Alerts

### Alert Configuration
```python
MEDIA_ALERTS = {
    'breaking_news': {
        'keywords': ['hack', 'sec', 'etf', 'ban', 'regulation'],
        'notify': ['app', 'email']
    },
    'sentiment_shift': {
        'threshold': 0.2,  # 20% change
        'timeframe': '1h'
    },
    'whale_alert': {
        'min_value': 1000000,  # $1M
        'notify': ['app']
    }
}
```

## 📈 Historical Analysis

### Correlation with Price
```python
def analyze_media_price_correlation(coin_id, days=30):
    media_sentiment = get_historical_sentiment(coin_id, days)
    price_data = get_historical_price(coin_id, days)
    
    correlation = calculate_correlation(
        media_sentiment['scores'],
        price_data['returns']
    )
    
    return {
        'correlation': correlation,
        'lag_hours': find_optimal_lag(media_sentiment, price_data),
        'predictive_power': assess_predictive_power()
    }
```

## ✅ Enhancements Implemented

- [x] Multi-source news aggregation
- [x] Social media integration
- [x] Real-time sentiment analysis
- [x] LLM-enhanced analysis
- [x] Trending topics detection
- [x] Alert system
- [x] Historical correlation
- [x] UI components
- [x] Caching layer

---

**Status**: Enhanced ✅
**Last Updated**: February 2026
