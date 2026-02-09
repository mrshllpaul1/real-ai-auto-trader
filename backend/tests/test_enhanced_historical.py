"""
Tests for Enhanced Historical Data Services
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock


class TestHistoricalDataManager:
    """Test HistoricalDataManager functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.historical_ohlcv = Mock()
        db.historical_ohlcv.find = Mock()
        db.historical_ohlcv.update_one = AsyncMock()
        return db
    
    def test_source_priority(self, mock_db):
        """Test that source priority is correctly defined"""
        from services.historical_data_manager import HistoricalDataManager
        
        manager = HistoricalDataManager(mock_db)
        
        assert manager.source_priority['coindesk'] == 3
        assert manager.source_priority['kraken'] == 2
        assert manager.source_priority['coingecko'] == 1
    
    def test_convert_kraken_format(self, mock_db):
        """Test Kraken format conversion"""
        from services.historical_data_manager import HistoricalDataManager
        
        manager = HistoricalDataManager(mock_db)
        
        kraken_data = {
            "prices": [
                [1704067200000, 42000.0],  # Jan 1, 2024
                [1704153600000, 42500.0],  # Jan 2, 2024
            ],
            "total_volumes": [
                [1704067200000, 1000000000],
                [1704153600000, 1100000000]
            ]
        }
        
        result = manager._convert_kraken_format(kraken_data)
        
        assert len(result) == 2
        assert result[0]['timestamp'] == 1704067200
        assert result[0]['close'] == 42000.0
        assert result[0]['volume'] == 1000000000
    
    def test_is_data_complete(self, mock_db):
        """Test data completeness check"""
        from services.historical_data_manager import HistoricalDataManager
        
        manager = HistoricalDataManager(mock_db)
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 10, tzinfo=timezone.utc)
        
        # Complete data
        complete_data = [
            {"timestamp": int(start_date.timestamp())},
            {"timestamp": int(end_date.timestamp())}
        ]
        
        assert manager._is_data_complete(complete_data, start_date, end_date)
        
        # Incomplete data (missing end)
        incomplete_data = [
            {"timestamp": int(start_date.timestamp())},
            {"timestamp": int((start_date + timedelta(days=1)).timestamp())}
        ]
        
        assert not manager._is_data_complete(incomplete_data, start_date, end_date)


class TestNewsAggregator:
    """Test NewsAggregator functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.crypto_news = Mock()
        db.crypto_news.update_one = AsyncMock()
        db.crypto_news.find = Mock()
        db.crypto_news.count_documents = AsyncMock(return_value=10)
        db.crypto_news.create_index = AsyncMock()
        return db
    
    def test_source_weights(self, mock_db):
        """Test that source weights are correctly defined"""
        from services.news_aggregator import NewsAggregator
        
        aggregator = NewsAggregator(mock_db)
        
        assert aggregator.source_weights['cryptopanic'] == 1.0
        assert aggregator.source_weights['coindesk'] == 0.9
        assert aggregator.source_weights['social'] == 0.5
    
    def test_calculate_sentiment_from_votes(self, mock_db):
        """Test sentiment calculation from votes"""
        from services.news_aggregator import NewsAggregator
        
        aggregator = NewsAggregator(mock_db)
        
        # Positive sentiment
        votes = {"positive": 10, "negative": 2, "liked": 5, "disliked": 1}
        sentiment = aggregator._calculate_sentiment_from_votes(votes)
        assert sentiment > 0
        assert -1 <= sentiment <= 1
        
        # Negative sentiment
        votes = {"positive": 2, "negative": 10, "liked": 1, "disliked": 5}
        sentiment = aggregator._calculate_sentiment_from_votes(votes)
        assert sentiment < 0
        
        # Neutral (no votes)
        votes = {}
        sentiment = aggregator._calculate_sentiment_from_votes(votes)
        assert sentiment == 0.0
    
    def test_get_sentiment_label(self, mock_db):
        """Test sentiment label generation"""
        from services.news_aggregator import NewsAggregator
        
        aggregator = NewsAggregator(mock_db)
        
        assert aggregator._get_sentiment_label(0.5) == "bullish"
        assert aggregator._get_sentiment_label(-0.5) == "bearish"
        assert aggregator._get_sentiment_label(0.1) == "neutral"
    
    def test_generate_news_id(self, mock_db):
        """Test news ID generation is consistent"""
        from services.news_aggregator import NewsAggregator
        
        aggregator = NewsAggregator(mock_db)
        
        url1 = "https://example.com/article1"
        url2 = "https://example.com/article2"
        
        id1a = aggregator._generate_news_id(url1)
        id1b = aggregator._generate_news_id(url1)
        id2 = aggregator._generate_news_id(url2)
        
        # Same URL should produce same ID
        assert id1a == id1b
        # Different URLs should produce different IDs
        assert id1a != id2


class TestNewsMarketCorrelation:
    """Test NewsMarketCorrelationAnalyzer functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.crypto_news = Mock()
        db.historical_ohlcv = Mock()
        db.news_market_correlations = Mock()
        db.news_market_correlations.update_one = AsyncMock()
        return db
    
    def test_find_closest_price(self, mock_db):
        """Test finding closest price to timestamp"""
        from services.news_market_correlation import NewsMarketCorrelationAnalyzer
        
        analyzer = NewsMarketCorrelationAnalyzer(mock_db)
        
        price_data = [
            {"timestamp": 1000, "close": 100.0},
            {"timestamp": 2000, "close": 200.0},
            {"timestamp": 3000, "close": 300.0}
        ]
        
        # Exact match
        price = analyzer._find_closest_price(price_data, 2000)
        assert price == 200.0
        
        # Close match
        price = analyzer._find_closest_price(price_data, 1900)
        assert price == 200.0
        
        # Out of tolerance
        price = analyzer._find_closest_price(price_data, 10000, max_tolerance=100)
        assert price is None
    
    def test_identify_significant_correlations(self, mock_db):
        """Test identification of significant correlations"""
        from services.news_market_correlation import NewsMarketCorrelationAnalyzer
        
        analyzer = NewsMarketCorrelationAnalyzer(mock_db)
        
        correlations = {
            "1h": {"correlation": 0.7, "p_value": 0.01, "is_significant": True, "sample_size": 50},
            "4h": {"correlation": 0.3, "p_value": 0.08, "is_significant": False, "sample_size": 45},
            "24h": {"correlation": -0.6, "p_value": 0.02, "is_significant": True, "sample_size": 40}
        }
        
        significant = analyzer._identify_significant_correlations(correlations)
        
        assert len(significant) == 2  # Only significant ones
        assert significant[0]["correlation"] == 0.7  # Strongest first
        assert significant[1]["correlation"] == -0.6
    
    def test_generate_signal_reason(self, mock_db):
        """Test signal reason generation"""
        from services.news_market_correlation import NewsMarketCorrelationAnalyzer
        
        analyzer = NewsMarketCorrelationAnalyzer(mock_db)
        
        # Bullish signal
        reason = analyzer._generate_signal_reason("bullish", 0.8, 0.5, 0.7)
        assert "bullish" in reason.lower()
        assert "confidence" in reason.lower()
        
        # Neutral signal
        reason = analyzer._generate_signal_reason("neutral", 0.2, 0.1, 0.1)
        assert "neutral" in reason.lower()


def test_imports():
    """Test that all modules can be imported"""
    try:
        from services.historical_data_manager import HistoricalDataManager, get_historical_data_manager
        from services.news_aggregator import NewsAggregator, get_news_aggregator
        from services.news_market_correlation import NewsMarketCorrelationAnalyzer, get_correlation_analyzer
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    print("Running enhanced historical data tests...")
    print("\n✅ All test cases defined successfully")
    print("\nNote: Run with pytest to execute all tests:")
    print("  pytest backend/tests/test_enhanced_historical.py")
