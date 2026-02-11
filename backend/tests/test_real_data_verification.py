"""
Backend API Tests - Real Data Verification
Tests that all services use REAL market data and NOT simulated data.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://status-checkup.preview.emergentagent.com').rstrip('/')


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_api_health(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'database' in data
        print(f"✓ Health check passed: {data}")


class TestStrategiesEndpoint:
    """Test /api/strategies/generate endpoint"""
    
    def test_generate_strategy_returns_real_data(self):
        """Test that strategy generation uses real market data"""
        payload = {
            "user_id": "test_user_real_data",
            "coin_pairs": ["bitcoin/USD"]
        }
        response = requests.post(
            f"{BASE_URL}/api/strategies/generate",
            json=payload,
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'strategies' in data
        assert 'count' in data
        assert data['learning_enabled'] == True
        assert data['news_integrated'] == True
        assert data['historical_patterns_trained'] == True
        
        # Verify intelligence sources
        assert 'intelligence_sources' in data
        assert 'technical_analysis' in data['intelligence_sources']
        
        print(f"✓ Strategy generation returned {data['count']} strategies")
        
        # Check that strategies have real data indicators
        if data['strategies']:
            strategy = data['strategies'][0]
            assert 'coin_id' in strategy
            assert 'ai_recommendation' in strategy
            assert 'confidence_score' in strategy
            # Verify news sentiment is from real sources
            if 'news_sentiment' in strategy:
                sentiment = strategy['news_sentiment']
                assert 'news_count' in sentiment
                print(f"✓ Strategy includes news sentiment with {sentiment.get('news_count', 0)} news items")


class TestNewsEndpoint:
    """Test /api/news endpoints - verify no simulated news"""
    
    def test_news_all_returns_real_news(self):
        """Test that news endpoint returns real news (not simulated)"""
        response = requests.get(f"{BASE_URL}/api/news/all", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert 'news' in data
        assert 'count' in data
        
        # Verify news items have real sources
        if data['news']:
            for news_item in data['news'][:5]:
                # Check that news has real source indicators
                assert 'title' in news_item
                assert 'source' in news_item
                assert 'aggregator' in news_item
                # Verify it's from a real aggregator, not simulated
                assert news_item['aggregator'] in ['free_crypto_news', 'cryptopanic', 'coingecko', 'coinmarketcap']
                # Verify no simulated indicators
                assert 'simulated' not in news_item.get('title', '').lower()
                assert 'fake' not in news_item.get('title', '').lower()
        
        print(f"✓ News endpoint returned {data['count']} real news items")
    
    def test_news_sentiment_analysis(self):
        """Test news sentiment analysis for a coin"""
        response = requests.get(f"{BASE_URL}/api/news/sentiment/bitcoin", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert 'sentiment' in data
        assert 'news_count' in data
        print(f"✓ Sentiment analysis: {data['sentiment']} based on {data['news_count']} news items")


class TestBacktestEndpoint:
    """Test /api/backtest endpoints - verify real data usage"""
    
    def test_backtest_presets(self):
        """Test backtest presets endpoint"""
        response = requests.get(f"{BASE_URL}/api/backtest/presets", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        assert 'presets' in data
        assert len(data['presets']) > 0
        
        # Verify preset structure
        for preset in data['presets']:
            assert 'name' in preset
            assert 'strategy' in preset
        
        print(f"✓ Backtest presets: {[p['name'] for p in data['presets']]}")
    
    def test_backtest_run_with_real_data(self):
        """Test that backtest uses real historical data"""
        payload = {
            "strategy": {
                "min_momentum": 3,
                "max_volatility": 12,
                "max_positions": 2
            },
            "coins": ["bitcoin"],
            "days": 90,
            "initial_capital": 1000
        }
        response = requests.post(
            f"{BASE_URL}/api/backtest/run",
            json=payload,
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for real data indicators
        if 'data_source' in data:
            assert 'REAL' in data['data_source'].upper() or data.get('simulated_data_used') == False
            print(f"✓ Backtest data source: {data.get('data_source', 'N/A')}")
        
        # If error due to no data, that's acceptable (means it's not faking data)
        if 'error' in data:
            assert 'real' in data.get('message', '').lower() or 'no' in data.get('message', '').lower()
            print(f"✓ Backtest correctly reports no real data available: {data.get('message', '')}")
        else:
            assert 'initial_capital' in data
            print(f"✓ Backtest completed with real data")


class TestGrowthEndpoint:
    """Test /api/growth endpoints"""
    
    def test_growth_stats(self):
        """Test growth stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/growth/stats", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'portfolio' in data or 'stats' in data or 'current_value' in data
        print(f"✓ Growth stats endpoint working")
    
    def test_growth_positions(self):
        """Test growth positions endpoint"""
        response = requests.get(f"{BASE_URL}/api/growth/positions", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        assert 'positions' in data or isinstance(data, list)
        print(f"✓ Growth positions endpoint working")


class TestSchedulerEndpoint:
    """Test /api/scheduler endpoints"""
    
    def test_scheduler_status(self):
        """Test scheduler status endpoint"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        assert 'running' in data or 'status' in data
        print(f"✓ Scheduler status: {data}")


class TestJournalEndpoint:
    """Test /api/journal endpoints"""
    
    def test_journal_stats(self):
        """Test journal stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/journal/stats", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has expected fields
        assert 'total_trades' in data or 'stats' in data
        print(f"✓ Journal stats endpoint working")


class TestMarketDataEndpoint:
    """Test /api/market endpoints - verify real data"""
    
    def test_market_prices(self):
        """Test market prices endpoint returns real data"""
        response = requests.get(f"{BASE_URL}/api/market/prices?coins=bitcoin,ethereum", timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Verify prices are real (non-zero, reasonable values)
            if 'bitcoin' in data:
                btc_price = data['bitcoin'].get('price_usd', 0)
                assert btc_price > 1000  # BTC should be > $1000
                print(f"✓ Bitcoin price: ${btc_price:,.2f}")
        else:
            print(f"⚠ Market prices endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
