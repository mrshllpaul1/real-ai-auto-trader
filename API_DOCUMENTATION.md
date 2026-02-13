# AI Crypto Trading Platform - Public API Documentation

**Version:** 1.0.0  
**Base URL:** `https://cryptoai-enhance.preview.emergentagent.com/api`  
**Documentation:** `/api/docs` (Swagger UI)  
**OpenAPI Spec:** `/api/openapi.json`

---

## Quick Start

### 1. Create an API Key

```bash
curl -X POST "https://cryptoai-enhance.preview.emergentagent.com/api/api-keys/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Trading Bot",
    "tier": "free",
    "scopes": ["read", "trade"]
  }'
```

**Response:**
```json
{
  "api_key": "sk-abcd1234...",
  "key_id": "key_xyz789",
  "name": "My Trading Bot",
  "tier": "free",
  "scopes": ["read", "trade"],
  "rate_limit_per_day": 100,
  "created_at": "2026-02-09T18:00:00Z"
}
```

**⚠️ Important:** Save the `api_key` - it's only shown once!

### 2. Make Your First API Call

```bash
curl -X GET "https://cryptoai-enhance.preview.emergentagent.com/api/portfolio/summary" \
  -H "X-API-Key: sk-your_api_key_here"
```

---

## Authentication

All API requests require authentication via API key in the header:

```
X-API-Key: your_api_key_here
```

### API Key Scopes

- **read**: View portfolio, market data, and analytics (read-only)
- **trade**: Execute trades and manage orders (requires `read`)
- **admin**: Full access to all features

---

## Rate Limiting

API requests are rate-limited based on your subscription tier:

| Tier | Requests/Day | Price |
|------|--------------|-------|
| Free | 100 | $0 |
| Pro | 10,000 | $29/month |
| Enterprise | Unlimited | $299/month |

### Rate Limit Headers

Every response includes rate limit info:

```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9,847
X-RateLimit-Reset: 1644451200
```

### Rate Limit Exceeded

When you exceed your limit:

```json
{
  "detail": "Rate limit exceeded. Limit: 100 requests/day. Resets in 8 hours."
}
```

Status Code: `429 Too Many Requests`

---

## Key Endpoints

### Portfolio Management

#### Get Portfolio Summary
```http
GET /api/portfolio/summary?user_id={user_id}
```

**Response:**
```json
{
  "total_value": 12450.50,
  "total_cost": 10000.00,
  "profit_loss": 2450.50,
  "profit_loss_percent": 24.51,
  "assets": 15,
  "last_updated": "2026-02-09T18:00:00Z"
}
```

#### Get Holdings
```http
GET /api/kraken/portfolio?user_id={user_id}
```

### Trading

#### Execute Trade
```http
POST /api/trading/execute
```

**Request:**
```json
{
  "user_id": "user123",
  "symbol": "BTC",
  "action": "buy",
  "amount": 0.5,
  "order_type": "market"
}
```

**Requires:** `trade` scope

### AI Features

#### Get AI Recommendations
```http
GET /api/enhanced-ai/recommendations?coins=BTC,ETH&exposure=50
```

**Response:**
```json
{
  "recommendations": [
    {
      "coin": "BTC",
      "action": "STRONG_BUY",
      "confidence": 87.5,
      "entry_price": 52340,
      "target_price": 58000,
      "stop_loss": 48000
    }
  ]
}
```

#### Start Tethys AI
```http
POST /api/tethys-train/start
```

**Requires:** `admin` scope

### Event Triggers

#### Create Trigger
```http
POST /api/triggers/create
```

**Request:**
```json
{
  "trigger_id": "btc_surge",
  "name": "Bitcoin Surge Alert",
  "keywords": ["bitcoin", "btc", "surge"],
  "coins": ["BTC"],
  "action": "alert",
  "enabled": true
}
```

### Market Data

#### Get Coin Price
```http
GET /api/market/coin/{symbol}
```

#### Get Market Sentiment
```http
GET /api/sentiment/market
```

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### Common Status Codes

| Code | Meaning |
|------|----------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized (invalid API key) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

---

## SDKs

### Python SDK

```python
import requests

class TradingAPI:
    def __init__(self, api_key):
        self.base_url = "https://cryptoai-enhance.preview.emergentagent.com/api"
        self.headers = {"X-API-Key": api_key}
    
    def get_portfolio(self, user_id):
        response = requests.get(
            f"{self.base_url}/portfolio/summary",
            params={"user_id": user_id},
            headers=self.headers
        )
        return response.json()
    
    def execute_trade(self, user_id, symbol, action, amount):
        response = requests.post(
            f"{self.base_url}/trading/execute",
            json={
                "user_id": user_id,
                "symbol": symbol,
                "action": action,
                "amount": amount,
                "order_type": "market"
            },
            headers=self.headers
        )
        return response.json()

# Usage
api = TradingAPI("sk-your_api_key")
portfolio = api.get_portfolio("user123")
print(portfolio)
```

### JavaScript/Node.js SDK

```javascript
const axios = require('axios');

class TradingAPI {
  constructor(apiKey) {
    this.baseURL = 'https://cryptoai-enhance.preview.emergentagent.com/api';
    this.apiKey = apiKey;
  }

  async getPortfolio(userId) {
    const response = await axios.get(`${this.baseURL}/portfolio/summary`, {
      params: { user_id: userId },
      headers: { 'X-API-Key': this.apiKey }
    });
    return response.data;
  }

  async executeTrade(userId, symbol, action, amount) {
    const response = await axios.post(
      `${this.baseURL}/trading/execute`,
      {
        user_id: userId,
        symbol: symbol,
        action: action,
        amount: amount,
        order_type: 'market'
      },
      { headers: { 'X-API-Key': this.apiKey } }
    );
    return response.data;
  }
}

// Usage
const api = new TradingAPI('sk-your_api_key');
const portfolio = await api.getPortfolio('user123');
console.log(portfolio);
```

---

## Webhooks (Coming Soon)

Receive real-time notifications for:
- Trade executions
- Trigger activations
- Portfolio milestones
- Price alerts

---

## Best Practices

### Security

1. **Never expose API keys** in client-side code
2. **Use environment variables** to store keys
3. **Rotate keys regularly** (every 90 days)
4. **Use separate keys** for production and development
5. **Revoke unused keys** immediately

### Performance

1. **Cache responses** when appropriate
2. **Batch requests** to reduce API calls
3. **Use webhooks** instead of polling
4. **Respect rate limits** - implement exponential backoff

### Error Handling

```python
import time

def make_api_call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited - wait and retry
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## API Status & Uptime

Monitor API status: https://status.emergentagent.com

---

## Support

- **Documentation:** https://docs.emergentagent.com
- **Email:** support@emergentagent.com
- **Discord:** https://discord.gg/emergent
- **GitHub Issues:** https://github.com/emergent/trading-api/issues

---

## Changelog

### v1.0.0 (2026-02-09)
- Initial public API release
- API key management
- Portfolio endpoints
- Trading endpoints
- AI recommendation endpoints
- Event trigger management
- Market data endpoints
- Rate limiting by tier
- OpenAPI 3.0 documentation

---

*Last updated: February 9, 2026*
