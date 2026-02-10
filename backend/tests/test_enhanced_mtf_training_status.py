import pytest
from unittest.mock import AsyncMock, MagicMock

from services.enhanced_mtf_training_service import EnhancedMTFTrainingService


def _mock_db(training_doc=None, model_doc=None):
    """Create a minimal mock db with required collections"""
    training_collection = MagicMock()
    training_collection.find_one = AsyncMock(return_value=training_doc)
    
    model_collection = MagicMock()
    model_collection.find_one = AsyncMock(return_value=model_doc)
    
    sentiment_cache = MagicMock()
    mtf_predictions = MagicMock()
    
    collections = {
        "enhanced_mtf_training": training_collection,
        "enhanced_mtf_models": model_collection,
        "sentiment_cache": sentiment_cache,
        "mtf_predictions": mtf_predictions,
        "kraken_coin_universe": MagicMock()
    }
    
    db = MagicMock()
    db.__getitem__.side_effect = lambda name: collections[name]
    return db, training_collection, model_collection


@pytest.mark.asyncio
async def test_get_training_status_uses_latest_history_when_idle():
    """Status should include last completed training info when memory is empty"""
    training_doc = {
        "training_id": "TEST123",
        "status": "completed",
        "completed_at": "2024-01-01T00:00:00Z",
        "symbols_trained": 42,
        "accuracy": 0.87,
        "mode": "sentiment_only",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    db, training_collection, model_collection = _mock_db(training_doc=training_doc, model_doc=None)
    service = EnhancedMTFTrainingService(db)
    
    status = await service.get_training_status()
    
    assert status["status"] == "completed"
    assert status["training_id"] == training_doc["training_id"]
    assert status["last_trained"] == training_doc["completed_at"]
    assert status["coins_trained"] == training_doc["symbols_trained"]
    assert status["accuracy"] == training_doc["accuracy"]
    assert status["mode"] == training_doc["mode"]
    
    # Ensure history lookup was attempted
    training_collection.find_one.assert_awaited()
    model_collection.find_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_training_status_preserves_live_training():
    """Live training progress should not be overridden by history"""
    db, training_collection, model_collection = _mock_db(training_doc=None, model_doc=None)
    service = EnhancedMTFTrainingService(db)
    
    service._training_status = {
        "status": "training",
        "training_id": "LIVE123",
        "progress": 45,
        "current_phase": "extracting_features"
    }
    
    status = await service.get_training_status()
    
    assert status["status"] == "training"
    assert status["training_id"] == "LIVE123"
    assert status["progress"] == 45
    assert status["current_phase"] == "extracting_features"
    
    # No history/model lookups when actively training
    training_collection.find_one.assert_not_awaited()
    model_collection.find_one.assert_not_awaited()
