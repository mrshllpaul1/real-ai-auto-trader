"""
Tests for Enhanced Historical Market and Media Data Integration
Tests the new services: HistoricalSentimentTracker, EnhancedMarketDataIntegrator, and EnhancedCorrelationService
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# Import services to test
from backend.services.historical_sentiment_tracker import HistoricalSentimentTracker
from backend.services.enhanced_market_data_integrator import EnhancedMarketDataIntegrator
from backend.services.enhanced_correlation_service import EnhancedCorrelationService


# Test configuration
TEST_DB_URL = "mongodb://localhost:27017"
TEST_DB_NAME = "test_trading_db"


@pytest.fixture
async def test_db():
    """Create a test database connection"""
    client = AsyncIOMotorClient(TEST_DB_URL)
    db = client[TEST_DB_NAME]
    
    yield db
    
    # Cleanup
    await client.drop_database(TEST_DB_NAME)
    client.close()


@pytest.fixture
async def sentiment_tracker(test_db):
    """Create a sentiment tracker instance"""
    tracker = HistoricalSentimentTracker(test_db)
    await tracker.initialize_indexes()
    return tracker


@pytest.fixture
def market_integrator():
    """Create a market integrator instance"""
    return EnhancedMarketDataIntegrator()


@pytest.fixture
async def correlation_service(test_db, sentiment_tracker, market_integrator):
    """Create a correlation service instance"""
    return EnhancedCorrelationService(test_db, sentiment_tracker, market_integrator)


# === Historical Sentiment Tracker Tests ===

@pytest.mark.asyncio
async def test_store_sentiment(sentiment_tracker):
    """Test storing sentiment data"""
    sentiment_data = {
        'coin_id': 'bitcoin',
        'symbol': 'BTC',
        'score': 75,
        'label': 'bullish',
        'confidence': 80,
        'summary': 'Positive market sentiment',
        'key_factors': ['Institutional adoption', 'Strong technicals'],
        'bullish_signals': ['ETF approval'],
        'bearish_signals': [],
        'news_count': 5
    }
    
    result = await sentiment_tracker.store_sentiment(
        coin_id='bitcoin',
        sentiment_data=sentiment_data,
        metadata={'test': True}
    )
    
    assert result is not None
    assert '_id' in result
    assert result['coin_id'] == 'bitcoin'
    assert result['score'] == 75
    assert result['label'] == 'bullish'


@pytest.mark.asyncio
async def test_get_sentiment_history(sentiment_tracker):
    """Test retrieving sentiment history"""
    # Store multiple sentiment readings
    for i in range(5):
        sentiment_data = {
            'coin_id': 'ethereum',
            'symbol': 'ETH',
            'score': 50 + i * 5,
            'label': 'neutral',
            'confidence': 70,
            'summary': f'Test reading {i}',
            'key_factors': [],
            'bullish_signals': [],
            'bearish_signals': [],
            'news_count': 3
        }
        await sentiment_tracker.store_sentiment('ethereum', sentiment_data)
    
    # Retrieve history
    history = await sentiment_tracker.get_coin_sentiment_history(
        coin_id='ethereum',
        limit=10
    )
    
    assert len(history) == 5
    assert history[0]['coin_id'] == 'ethereum'
    # Results should be in descending order by timestamp
    assert history[0]['score'] >= history[-1]['score']


@pytest.mark.asyncio
async def test_create_daily_snapshot(sentiment_tracker):
    """Test creating daily sentiment snapshots"""
    # Store some sentiment data for today
    today = datetime.utcnow().date().isoformat()
    
    for coin_id in ['bitcoin', 'ethereum', 'solana']:
        sentiment_data = {
            'coin_id': coin_id,
            'symbol': coin_id.upper()[:3],
            'score': 60 if coin_id == 'bitcoin' else 55,
            'label': 'neutral',
            'confidence': 70,
            'summary': f'Test for {coin_id}',
            'key_factors': ['Factor 1', 'Factor 2'],
            'bullish_signals': ['Signal 1'],
            'bearish_signals': [],
            'news_count': 5
        }
        await sentiment_tracker.store_sentiment(coin_id, sentiment_data)
    
    # Create snapshot
    result = await sentiment_tracker.create_daily_snapshot(date=today)
    
    assert result['status'] == 'success'
    assert result['snapshots_created'] >= 3
    assert result['date'] == today


@pytest.mark.asyncio
async def test_get_sentiment_trend(sentiment_tracker):
    """Test sentiment trend analysis"""
    # Store sentiment data over multiple days
    coin_id = 'bitcoin'
    base_date = datetime.utcnow().date()
    
    for days_ago in range(10, 0, -1):
        date = (base_date - timedelta(days=days_ago)).isoformat()
        sentiment_data = {
            'coin_id': coin_id,
            'symbol': 'BTC',
            'score': 50 + days_ago,  # Increasing score over time
            'label': 'neutral',
            'confidence': 70,
            'summary': f'Day {days_ago}',
            'key_factors': [],
            'bullish_signals': [],
            'bearish_signals': [],
            'news_count': 3
        }
        await sentiment_tracker.store_sentiment(coin_id, sentiment_data)
        
        # Create snapshot for each day
        await sentiment_tracker.create_daily_snapshot(date=date)
    
    # Get trend analysis
    trend = await sentiment_tracker.get_sentiment_trend(
        coin_id=coin_id,
        days=10
    )
    
    assert trend['coin_id'] == coin_id
    assert trend['trend_direction'] in ['rising', 'falling', 'stable']
    assert 'momentum' in trend
    assert 'volatility' in trend
    assert len(trend['snapshots']) > 0


# === Enhanced Market Data Integrator Tests ===

@pytest.mark.asyncio
async def test_get_validated_price(market_integrator):
    """Test multi-source price validation"""
    result = await market_integrator.get_validated_price(
        coin_id='bitcoin',
        validate=True
    )
    
    # Should return price data (or error if all sources fail)
    assert 'coin_id' in result or 'error' in result
    
    if 'price_usd' in result:
        assert result['price_usd'] > 0
        assert 'validated' in result
        assert 'quality_score' in result


@pytest.mark.asyncio
async def test_get_data_quality_report(market_integrator):
    """Test data quality reporting"""
    report = await market_integrator.get_data_quality_report()
    
    assert 'timestamp' in report
    assert 'sources' in report
    assert isinstance(report['sources'], dict)
    
    # Check that sources have expected fields
    for source_name, source_data in report['sources'].items():
        assert 'available' in source_data
        assert 'priority' in source_data
        assert 'success_rate' in source_data


@pytest.mark.asyncio
async def test_source_status(market_integrator):
    """Test source status retrieval"""
    status = market_integrator.get_source_status()
    
    assert 'sources' in status
    assert 'quality_threshold' in status
    assert 'divergence_threshold' in status
    
    # Check each source has expected fields
    for source_name, source_config in status['sources'].items():
        assert 'priority' in source_config
        assert 'available' in source_config
        assert 'failures' in source_config


# === Enhanced Correlation Service Tests ===

@pytest.mark.asyncio
async def test_analyze_news_impact_structure(correlation_service):
    """Test news impact analysis structure"""
    news_timestamp = datetime.utcnow() - timedelta(hours=2)
    news_sentiment = {
        'score': 70,
        'label': 'bullish',
        'confidence': 75
    }
    
    result = await correlation_service.analyze_news_impact(
        coin_id='bitcoin',
        news_timestamp=news_timestamp,
        news_sentiment=news_sentiment
    )
    
    # Check structure
    assert 'coin_id' in result
    assert 'news_timestamp' in result
    assert 'sentiment_score' in result
    assert 'timeframe_analysis' in result
    assert 'overall_impact' in result
    assert 'confidence' in result
    
    # Check timeframes are analyzed
    timeframes = result['timeframe_analysis']
    assert '0.25h' in timeframes
    assert '1h' in timeframes
    assert '4h' in timeframes
    assert '24h' in timeframes


@pytest.mark.asyncio
async def test_get_correlation_summary(correlation_service, sentiment_tracker):
    """Test correlation summary generation"""
    # Store some test sentiment data
    coin_id = 'ethereum'
    for i in range(5):
        sentiment_data = {
            'coin_id': coin_id,
            'symbol': 'ETH',
            'score': 60 + i * 2,
            'label': 'neutral',
            'confidence': 70,
            'summary': f'Test {i}',
            'key_factors': [],
            'bullish_signals': [],
            'bearish_signals': [],
            'news_count': 3
        }
        await sentiment_tracker.store_sentiment(coin_id, sentiment_data)
    
    summary = await correlation_service.get_correlation_summary(
        coin_id=coin_id,
        days=30
    )
    
    assert 'coin_id' in summary
    assert 'period_days' in summary
    assert summary['period_days'] == 30


# === Integration Tests ===

@pytest.mark.asyncio
async def test_full_integration_flow(sentiment_tracker, market_integrator, correlation_service):
    """Test complete integration flow"""
    coin_id = 'bitcoin'
    
    # 1. Get validated price
    price_data = await market_integrator.get_validated_price(coin_id, validate=False)
    
    # 2. Store sentiment
    sentiment_data = {
        'coin_id': coin_id,
        'symbol': 'BTC',
        'score': 65,
        'label': 'bullish',
        'confidence': 75,
        'summary': 'Integration test',
        'key_factors': ['Test factor'],
        'bullish_signals': [],
        'bearish_signals': [],
        'news_count': 5
    }
    
    stored = await sentiment_tracker.store_sentiment(
        coin_id=coin_id,
        sentiment_data=sentiment_data,
        metadata={'price': price_data.get('price_usd')}
    )
    
    assert stored is not None
    
    # 3. Create daily snapshot
    today = datetime.utcnow().date().isoformat()
    snapshot_result = await sentiment_tracker.create_daily_snapshot(date=today)
    assert snapshot_result['status'] == 'success'
    
    # 4. Get sentiment history
    history = await sentiment_tracker.get_coin_sentiment_history(coin_id, limit=10)
    assert len(history) > 0
    
    # 5. Analyze correlation (structure test only, no real price data)
    news_timestamp = datetime.utcnow() - timedelta(hours=1)
    correlation = await correlation_service.analyze_news_impact(
        coin_id=coin_id,
        news_timestamp=news_timestamp,
        news_sentiment=sentiment_data
    )
    
    assert 'overall_impact' in correlation


@pytest.mark.asyncio
async def test_storage_stats(sentiment_tracker):
    """Test storage statistics"""
    # Store data for multiple coins
    for coin_id in ['bitcoin', 'ethereum', 'solana']:
        sentiment_data = {
            'coin_id': coin_id,
            'symbol': coin_id.upper()[:3],
            'score': 55,
            'label': 'neutral',
            'confidence': 70,
            'summary': 'Test',
            'key_factors': [],
            'bullish_signals': [],
            'bearish_signals': [],
            'news_count': 3
        }
        await sentiment_tracker.store_sentiment(coin_id, sentiment_data)
    
    stats = await sentiment_tracker.get_storage_stats()
    
    assert stats['total_sentiment_records'] >= 3
    assert stats['unique_coins_tracked'] >= 3
    assert 'bitcoin' in stats['coins']
    assert 'ethereum' in stats['coins']
    assert 'solana' in stats['coins']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
