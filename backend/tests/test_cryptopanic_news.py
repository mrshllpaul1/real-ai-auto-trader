"""
CryptoPanic News API Tests
Tests all news endpoints for the CryptoPanic integration.
Endpoints tested:
- /api/news/status - Service availability
- /api/news/trending - Trending news
- /api/news/hot - Hot news
- /api/news/bullish - Bullish sentiment news
- /api/news/bearish - Bearish sentiment news
- /api/news/important - Important news
- /api/news/coin/{symbol} - News for specific coin
- /api/news/sentiment/{symbol} - AI sentiment analysis
- /api/news/market-overview - Market sentiment overview
- /api/news/coins (POST) - Multi-coin news
- /api/news/clear-cache (POST) - Clear cache
"""

import pytest
import requests
import os
import time

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCryptoPanicNewsAPI:
    """Test suite for CryptoPanic News API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    # ==================== Service Status ====================
    def test_news_status_endpoint(self):
        """Test /api/news/status - Check CryptoPanic service availability"""
        response = self.session.get(f"{BASE_URL}/api/news/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "available" in data, "Response should contain 'available' field"
        assert data["available"] == True, f"Service should be available, got: {data}"
        assert "message" in data, "Response should contain 'message' field"
        print(f"✅ Status endpoint: {data}")
    
    # ==================== Trending News ====================
    def test_trending_news_endpoint(self):
        """Test /api/news/trending - Get trending crypto news"""
        response = self.session.get(f"{BASE_URL}/api/news/trending")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "filter" in data, "Response should contain 'filter' field"
        assert data["filter"] == "trending", f"Filter should be 'trending', got: {data['filter']}"
        assert "news" in data, "Response should contain 'news' field"
        assert "count" in data, "Response should contain 'count' field"
        assert isinstance(data["news"], list), "News should be a list"
        
        # Verify news item structure (if any news returned)
        if len(data["news"]) > 0:
            news_item = data["news"][0]
            assert "title" in news_item, "News item should have 'title'"
            assert "kind" in news_item, "News item should have 'kind'"
            print(f"✅ Trending news: {data['count']} items, first title: {news_item['title'][:50]}...")
        else:
            print(f"✅ Trending news: 0 items (may be rate limited or no trending news)")
    
    def test_trending_news_with_limit(self):
        """Test /api/news/trending with custom limit"""
        response = self.session.get(f"{BASE_URL}/api/news/trending?limit=5")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["count"] <= 5, f"Count should be <= 5, got: {data['count']}"
        print(f"✅ Trending news with limit=5: {data['count']} items")
    
    # ==================== Hot News ====================
    def test_hot_news_endpoint(self):
        """Test /api/news/hot - Get hot crypto news"""
        response = self.session.get(f"{BASE_URL}/api/news/hot")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["filter"] == "hot", f"Filter should be 'hot', got: {data['filter']}"
        assert "news" in data, "Response should contain 'news' field"
        assert isinstance(data["news"], list), "News should be a list"
        print(f"✅ Hot news: {data['count']} items")
    
    # ==================== Bullish News ====================
    def test_bullish_news_endpoint(self):
        """Test /api/news/bullish - Get bullish sentiment news"""
        response = self.session.get(f"{BASE_URL}/api/news/bullish")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["filter"] == "bullish", f"Filter should be 'bullish', got: {data['filter']}"
        assert "news" in data, "Response should contain 'news' field"
        print(f"✅ Bullish news: {data['count']} items")
    
    # ==================== Bearish News ====================
    def test_bearish_news_endpoint(self):
        """Test /api/news/bearish - Get bearish sentiment news"""
        response = self.session.get(f"{BASE_URL}/api/news/bearish")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["filter"] == "bearish", f"Filter should be 'bearish', got: {data['filter']}"
        assert "news" in data, "Response should contain 'news' field"
        print(f"✅ Bearish news: {data['count']} items")
    
    # ==================== Important News ====================
    def test_important_news_endpoint(self):
        """Test /api/news/important - Get important news"""
        response = self.session.get(f"{BASE_URL}/api/news/important")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["filter"] == "important", f"Filter should be 'important', got: {data['filter']}"
        assert "news" in data, "Response should contain 'news' field"
        print(f"✅ Important news: {data['count']} items")
    
    # ==================== Coin-Specific News ====================
    def test_coin_news_btc(self):
        """Test /api/news/coin/BTC - Get news for Bitcoin"""
        response = self.session.get(f"{BASE_URL}/api/news/coin/BTC")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["symbol"] == "BTC", f"Symbol should be 'BTC', got: {data['symbol']}"
        assert "news" in data, "Response should contain 'news' field"
        assert "filter" in data, "Response should contain 'filter' field"
        print(f"✅ BTC news: {data['count']} items, filter: {data['filter']}")
    
    def test_coin_news_eth(self):
        """Test /api/news/coin/ETH - Get news for Ethereum"""
        response = self.session.get(f"{BASE_URL}/api/news/coin/ETH")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["symbol"] == "ETH", f"Symbol should be 'ETH', got: {data['symbol']}"
        assert "news" in data, "Response should contain 'news' field"
        print(f"✅ ETH news: {data['count']} items")
    
    def test_coin_news_with_filter(self):
        """Test /api/news/coin/{symbol} with different filters"""
        filters = ["hot", "rising", "bullish", "bearish", "important"]
        
        for filter_type in filters:
            response = self.session.get(f"{BASE_URL}/api/news/coin/BTC?filter={filter_type}")
            
            assert response.status_code == 200, f"Expected 200 for filter={filter_type}, got {response.status_code}"
            
            data = response.json()
            assert data["filter"] == filter_type, f"Filter should be '{filter_type}', got: {data['filter']}"
            print(f"✅ BTC news with filter={filter_type}: {data['count']} items")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
    
    def test_coin_news_lowercase_symbol(self):
        """Test /api/news/coin/{symbol} with lowercase symbol"""
        response = self.session.get(f"{BASE_URL}/api/news/coin/btc")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Symbol should be uppercased in response
        assert data["symbol"] == "BTC", f"Symbol should be 'BTC', got: {data['symbol']}"
        print(f"✅ Lowercase symbol handled correctly")
    
    # ==================== Sentiment Analysis ====================
    # Note: /api/news/sentiment/{symbol} is handled by the AI sentiment service (news.py)
    # which provides AI-powered analysis with confidence scores and detailed analysis
    def test_sentiment_analysis_eth(self):
        """Test /api/news/sentiment/ETH - Get AI sentiment analysis for Ethereum"""
        response = self.session.get(f"{BASE_URL}/api/news/sentiment/ETH")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # AI sentiment service returns: sentiment, confidence, ai_analysis, news_count, analyzed_at, recent_headlines
        assert "sentiment" in data, "Response should contain 'sentiment'"
        assert "confidence" in data, "Response should contain 'confidence'"
        assert "analyzed_at" in data, "Response should contain 'analyzed_at'"
        assert "news_count" in data, "Response should contain 'news_count'"
        
        # Validate sentiment value
        valid_sentiments = ['bullish', 'bearish', 'neutral', 'positive', 'negative']
        assert data["sentiment"].lower() in valid_sentiments, f"Invalid sentiment: {data['sentiment']}"
        
        # Validate confidence range (0-100)
        assert 0 <= data["confidence"] <= 100, f"Confidence should be 0-100, got: {data['confidence']}"
        
        print(f"✅ ETH sentiment: {data['sentiment']}, confidence={data['confidence']}")
        print(f"   News count: {data['news_count']}")
        if data.get("recent_headlines"):
            print(f"   Recent headlines: {data['recent_headlines'][:2]}")
    
    def test_sentiment_analysis_btc(self):
        """Test /api/news/sentiment/BTC - Get AI sentiment analysis for Bitcoin"""
        response = self.session.get(f"{BASE_URL}/api/news/sentiment/BTC")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # AI sentiment service returns: sentiment, confidence, ai_analysis, news_count, analyzed_at
        assert "sentiment" in data, "Response should contain 'sentiment'"
        assert "confidence" in data, "Response should contain 'confidence'"
        assert "analyzed_at" in data, "Response should contain 'analyzed_at'"
        
        print(f"✅ BTC sentiment: {data['sentiment']}, confidence={data['confidence']}")
    
    # ==================== Market Overview ====================
    def test_market_overview_endpoint(self):
        """Test /api/news/market-overview - Get overall market sentiment"""
        response = self.session.get(f"{BASE_URL}/api/news/market-overview")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "market_sentiment_score" in data, "Response should contain 'market_sentiment_score'"
        assert "market_sentiment_label" in data, "Response should contain 'market_sentiment_label'"
        assert "trending_news_count" in data, "Response should contain 'trending_news_count'"
        assert "bullish_news_count" in data, "Response should contain 'bullish_news_count'"
        assert "bearish_news_count" in data, "Response should contain 'bearish_news_count'"
        assert "important_news_count" in data, "Response should contain 'important_news_count'"
        assert "top_currencies" in data, "Response should contain 'top_currencies'"
        assert "analyzed_at" in data, "Response should contain 'analyzed_at'"
        
        # Validate sentiment score range
        assert 0 <= data["market_sentiment_score"] <= 100, f"Market sentiment should be 0-100, got: {data['market_sentiment_score']}"
        
        # Validate sentiment label
        valid_labels = ['bullish', 'neutral', 'bearish']
        assert data["market_sentiment_label"] in valid_labels, f"Invalid market sentiment label: {data['market_sentiment_label']}"
        
        print(f"✅ Market overview: sentiment={data['market_sentiment_score']}, label={data['market_sentiment_label']}")
        print(f"   Trending: {data['trending_news_count']}, Bullish: {data['bullish_news_count']}, Bearish: {data['bearish_news_count']}")
        if data.get("top_currencies"):
            print(f"   Top currencies: {[c['symbol'] for c in data['top_currencies'][:5]]}")
    
    # ==================== Multi-Coin News ====================
    def test_multi_coin_news_endpoint(self):
        """Test /api/news/coins (POST) - Get news for multiple coins"""
        payload = {
            "symbols": ["BTC", "ETH"],
            "limit": 20
        }
        
        response = self.session.post(f"{BASE_URL}/api/news/coins", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "symbols" in data, "Response should contain 'symbols'"
        assert "news_by_symbol" in data, "Response should contain 'news_by_symbol'"
        assert "total_count" in data, "Response should contain 'total_count'"
        
        # Verify symbols are uppercased
        assert "BTC" in data["symbols"], "BTC should be in symbols"
        assert "ETH" in data["symbols"], "ETH should be in symbols"
        
        # Verify news_by_symbol structure
        assert isinstance(data["news_by_symbol"], dict), "news_by_symbol should be a dict"
        
        print(f"✅ Multi-coin news: total={data['total_count']}")
        for symbol, news in data["news_by_symbol"].items():
            print(f"   {symbol}: {len(news)} items")
    
    def test_multi_coin_news_lowercase_symbols(self):
        """Test /api/news/coins with lowercase symbols"""
        payload = {
            "symbols": ["btc", "eth", "sol"],
            "limit": 15
        }
        
        response = self.session.post(f"{BASE_URL}/api/news/coins", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Symbols should be uppercased
        assert "BTC" in data["symbols"], "BTC should be uppercased"
        assert "ETH" in data["symbols"], "ETH should be uppercased"
        assert "SOL" in data["symbols"], "SOL should be uppercased"
        print(f"✅ Lowercase symbols handled correctly")
    
    def test_multi_coin_news_max_symbols_limit(self):
        """Test /api/news/coins with more than 10 symbols (should fail)"""
        payload = {
            "symbols": ["BTC", "ETH", "SOL", "ADA", "DOT", "LINK", "AVAX", "MATIC", "UNI", "ATOM", "XRP"],
            "limit": 30
        }
        
        response = self.session.post(f"{BASE_URL}/api/news/coins", json=payload)
        
        assert response.status_code == 400, f"Expected 400 for >10 symbols, got {response.status_code}"
        print(f"✅ Max symbols limit enforced correctly")
    
    # ==================== Clear Cache ====================
    def test_clear_cache_endpoint(self):
        """Test /api/news/clear-cache (POST) - Clear news cache"""
        response = self.session.post(f"{BASE_URL}/api/news/clear-cache")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain 'message'"
        assert "cleared" in data["message"].lower() or "success" in data["message"].lower(), \
            f"Message should indicate cache cleared: {data['message']}"
        print(f"✅ Cache cleared: {data['message']}")
    
    # ==================== Edge Cases ====================
    def test_invalid_filter_parameter(self):
        """Test /api/news/coin/{symbol} with invalid filter"""
        response = self.session.get(f"{BASE_URL}/api/news/coin/BTC?filter=invalid_filter")
        
        # Should return 422 (validation error) for invalid filter
        assert response.status_code == 422, f"Expected 422 for invalid filter, got {response.status_code}"
        print(f"✅ Invalid filter parameter handled correctly")
    
    def test_limit_exceeds_max(self):
        """Test endpoints with limit exceeding maximum (50)"""
        response = self.session.get(f"{BASE_URL}/api/news/trending?limit=100")
        
        # Should return 422 (validation error) for limit > 50
        assert response.status_code == 422, f"Expected 422 for limit > 50, got {response.status_code}"
        print(f"✅ Max limit validation working correctly")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
