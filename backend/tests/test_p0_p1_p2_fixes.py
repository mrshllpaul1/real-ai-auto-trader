"""
Test P0, P1, P2 fixes for AI Crypto Trading App
- P0: scikit-learn removed (deployment blocker)
- P1: News API returns real data (not simulated)
- P2: Market Historical Data is reliable
"""
import pytest
import requests
import os
import subprocess

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestP0DeploymentBlocker:
    """P0: Verify scikit-learn is removed from codebase"""
    
    def test_no_sklearn_in_requirements(self):
        """Verify scikit-learn is not in requirements.txt"""
        with open('/app/backend/requirements.txt', 'r') as f:
            content = f.read().lower()
        
        assert 'scikit-learn' not in content, "scikit-learn found in requirements.txt"
        assert 'sklearn' not in content, "sklearn found in requirements.txt"
        assert 'scipy' not in content, "scipy found in requirements.txt"
        print("PASS: No scikit-learn/sklearn/scipy in requirements.txt")
    
    def test_no_sklearn_imports_in_code(self):
        """Verify no sklearn imports in backend code"""
        result = subprocess.run(
            ['grep', '-r', 'sklearn', '/app/backend/'],
            capture_output=True,
            text=True
        )
        # grep returns 1 if no matches found (which is what we want)
        assert result.returncode == 1, f"sklearn imports found: {result.stdout}"
        print("PASS: No sklearn imports in backend code")
    
    def test_no_scikit_learn_imports_in_code(self):
        """Verify no scikit-learn imports in backend code"""
        result = subprocess.run(
            ['grep', '-r', 'scikit-learn', '/app/backend/'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1, f"scikit-learn imports found: {result.stdout}"
        print("PASS: No scikit-learn imports in backend code")


class TestP1NewsAPI:
    """P1: Verify News API returns real data"""
    
    def test_news_api_returns_data(self):
        """Verify /api/news/all returns news articles"""
        response = requests.get(f"{BASE_URL}/api/news/all", timeout=30)
        
        assert response.status_code == 200, f"News API returned {response.status_code}"
        
        data = response.json()
        assert 'news' in data, "Response missing 'news' field"
        assert len(data['news']) > 0, "No news articles returned"
        print(f"PASS: News API returned {len(data['news'])} articles")
    
    def test_news_api_returns_real_data_not_simulated(self):
        """Verify news articles have aggregator='free_crypto_news', NOT 'simulated'"""
        response = requests.get(f"{BASE_URL}/api/news/all", timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that at least some articles are from free_crypto_news
        free_crypto_news_count = sum(
            1 for article in data['news'] 
            if article.get('aggregator') == 'free_crypto_news'
        )
        
        simulated_count = sum(
            1 for article in data['news'] 
            if article.get('aggregator') == 'simulated'
        )
        
        assert free_crypto_news_count > 0, "No articles from free_crypto_news aggregator"
        assert simulated_count == 0, f"Found {simulated_count} simulated articles - should be 0"
        print(f"PASS: {free_crypto_news_count} articles from free_crypto_news, 0 simulated")
    
    def test_news_articles_have_required_fields(self):
        """Verify news articles have required fields"""
        response = requests.get(f"{BASE_URL}/api/news/all", timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['title', 'source', 'url', 'aggregator']
        
        for article in data['news'][:5]:  # Check first 5 articles
            for field in required_fields:
                assert field in article, f"Article missing '{field}' field"
                assert article[field], f"Article has empty '{field}' field"
        
        print("PASS: News articles have all required fields")


class TestP2MarketHistoricalData:
    """P2: Verify Market Historical Data is reliable"""
    
    def test_bitcoin_historical_data(self):
        """Verify /api/market/historical/bitcoin returns data"""
        response = requests.get(
            f"{BASE_URL}/api/market/historical/bitcoin?days=7",
            timeout=30
        )
        
        assert response.status_code == 200, f"Bitcoin historical API returned {response.status_code}"
        
        data = response.json()
        assert 'prices' in data, "Response missing 'prices' field"
        assert len(data['prices']) > 0, "No price data returned"
        assert data['coin_id'] == 'bitcoin', "Wrong coin_id"
        
        # Verify price is in realistic range (around $95,000 for Bitcoin)
        latest_price = data['prices'][-1][1]
        assert 50000 < latest_price < 200000, f"Bitcoin price {latest_price} seems unrealistic"
        
        print(f"PASS: Bitcoin historical data returned {len(data['prices'])} data points, latest price: ${latest_price:,.2f}")
    
    def test_ethereum_historical_data(self):
        """Verify /api/market/historical/ethereum returns data"""
        response = requests.get(
            f"{BASE_URL}/api/market/historical/ethereum?days=7",
            timeout=30
        )
        
        assert response.status_code == 200, f"Ethereum historical API returned {response.status_code}"
        
        data = response.json()
        assert 'prices' in data, "Response missing 'prices' field"
        assert len(data['prices']) > 0, "No price data returned"
        assert data['coin_id'] == 'ethereum', "Wrong coin_id"
        
        # Verify price is in realistic range (around $3,500 for Ethereum)
        latest_price = data['prices'][-1][1]
        assert 1000 < latest_price < 10000, f"Ethereum price {latest_price} seems unrealistic"
        
        print(f"PASS: Ethereum historical data returned {len(data['prices'])} data points, latest price: ${latest_price:,.2f}")
    
    def test_historical_data_has_market_caps_and_volumes(self):
        """Verify historical data includes market caps and volumes"""
        response = requests.get(
            f"{BASE_URL}/api/market/historical/bitcoin?days=7",
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'market_caps' in data, "Response missing 'market_caps' field"
        assert 'total_volumes' in data, "Response missing 'total_volumes' field"
        assert len(data['market_caps']) > 0, "No market cap data"
        assert len(data['total_volumes']) > 0, "No volume data"
        
        print("PASS: Historical data includes market caps and volumes")


class TestBackendHealth:
    """Verify backend is operational"""
    
    def test_health_check(self):
        """Verify /api/ returns operational status"""
        response = requests.get(f"{BASE_URL}/api/", timeout=10)
        
        assert response.status_code == 200, f"Health check returned {response.status_code}"
        
        data = response.json()
        assert data.get('status') == 'operational', f"Status is not operational: {data.get('status')}"
        
        print("PASS: Backend health check - operational")
    
    def test_api_features_listed(self):
        """Verify API features are listed in health response"""
        response = requests.get(f"{BASE_URL}/api/", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'features' in data, "Response missing 'features' field"
        assert len(data['features']) > 0, "No features listed"
        
        print(f"PASS: API lists {len(data['features'])} features")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
