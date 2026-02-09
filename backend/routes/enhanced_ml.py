"""
Enhanced Prediction API Routes
Exposes advanced ML prediction capabilities including:
- Predictions with uncertainty quantification
- Multi-timeframe ensemble predictions
- Prediction explainability
- Online learning updates
- Model performance monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np
import logging

from services.enhanced_prediction_engine import EnhancedPredictionEngine
from services.online_learning_engine import OnlineLearningEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml/enhanced", tags=["Enhanced ML Predictions"])


# Pydantic models for request/response
class PredictionRequest(BaseModel):
    coin_symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH)")
    model_predictions: List[Dict[str, Any]] = Field(
        ..., 
        description="List of predictions from different models"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class MultiTimeframeRequest(BaseModel):
    coin_symbol: str
    price_data_by_timeframe: Dict[str, List[float]] = Field(
        ..., 
        description="Price data for each timeframe, e.g., {'5m': [...], '1h': [...]}"
    )


class OnlineUpdateRequest(BaseModel):
    coin_symbol: str
    features: List[List[float]] = Field(..., description="Feature matrix as list of lists")
    labels: List[float] = Field(..., description="Target labels")
    market_volatility: float = Field(0.02, description="Current market volatility")


class OnlinePredictionRequest(BaseModel):
    coin_symbol: str
    features: List[List[float]] = Field(..., description="Feature matrix")
    return_probabilities: bool = Field(True, description="Return probability distribution")


class OutcomeUpdateRequest(BaseModel):
    prediction_id: str
    actual_outcome: str = Field(..., description="Actual market movement (bullish/bearish/neutral)")
    was_correct: bool
    actual_price_change: Optional[float] = None


# Dependency to get database
async def get_db():
    from server import db
    return db


# Initialize engines (will be set on app startup)
enhanced_engine: Optional[EnhancedPredictionEngine] = None
online_engine: Optional[OnlineLearningEngine] = None


def init_engines(db):
    """Initialize ML engines with database connection"""
    global enhanced_engine, online_engine
    enhanced_engine = EnhancedPredictionEngine(db)
    online_engine = OnlineLearningEngine(db)
    logger.info("✅ Enhanced ML engines initialized")


@router.post("/predict/with-uncertainty")
async def predict_with_uncertainty(
    request: PredictionRequest,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate prediction with uncertainty quantification.
    
    Includes:
    - Ensemble variance
    - Confidence intervals
    - Model agreement metrics
    - Historical performance calibration
    """
    try:
        if enhanced_engine is None:
            init_engines(db)
        
        result = await enhanced_engine.predict_with_uncertainty(
            coin_symbol=request.coin_symbol,
            model_predictions=request.model_predictions,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error in predict_with_uncertainty: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/multi-timeframe")
async def predict_multi_timeframe(
    request: MultiTimeframeRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate predictions across multiple timeframes and aggregate.
    
    Detects timeframe divergences which may signal reversals.
    """
    try:
        if enhanced_engine is None:
            init_engines(db)
        
        # Define a simple prediction function for each timeframe
        async def simple_prediction(symbol, prices, timeframe):
            """Simple moving average based prediction"""
            if len(prices) < 20:
                return {'signal': 'neutral', 'confidence': 0, 'prediction': 0.0}
            
            # Calculate short and long moving averages
            short_ma = np.mean(prices[-10:])
            long_ma = np.mean(prices[-20:])
            
            # Generate signal
            if short_ma > long_ma * 1.02:
                signal = 'bullish'
                confidence = min(80, (short_ma / long_ma - 1) * 1000)
            elif short_ma < long_ma * 0.98:
                signal = 'bearish'
                confidence = min(80, (1 - short_ma / long_ma) * 1000)
            else:
                signal = 'neutral'
                confidence = 40
            
            prediction = (short_ma / long_ma - 1) * 100  # Percentage change
            
            return {
                'signal': signal,
                'confidence': confidence,
                'prediction': prediction,
                'timeframe': timeframe
            }
        
        result = await enhanced_engine.predict_multi_timeframe(
            coin_symbol=request.coin_symbol,
            price_data_by_timeframe=request.price_data_by_timeframe,
            prediction_function=simple_prediction
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error in predict_multi_timeframe: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain/{prediction_id}")
async def explain_prediction(
    prediction_id: str,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get explainability report for a specific prediction.
    
    Returns:
    - Key factors influencing the prediction
    - Model contributions
    - Uncertainty sources
    """
    try:
        if enhanced_engine is None:
            init_engines(db)
        
        from bson import ObjectId
        
        # Fetch the prediction
        prediction = await db.enhanced_predictions.find_one({'_id': ObjectId(prediction_id)})
        
        if not prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        explanation = await enhanced_engine.explain_prediction(prediction)
        
        return {
            "success": True,
            "data": explanation
        }
        
    except Exception as e:
        logger.error(f"Error in explain_prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/online/update")
async def online_learning_update(
    request: OnlineUpdateRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update model with new data using online learning.
    
    Enables real-time model adaptation without waiting for batch retraining.
    """
    try:
        if online_engine is None:
            init_engines(db)
        
        # Convert lists to numpy arrays
        features = np.array(request.features)
        labels = np.array(request.labels)
        
        # Perform online update in background
        result = await online_engine.update_model_online(
            coin_symbol=request.coin_symbol,
            features=features,
            labels=labels,
            market_volatility=request.market_volatility
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error in online_learning_update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/online/predict")
async def online_learning_predict(
    request: OnlinePredictionRequest,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Make prediction using online learning model.
    
    Returns most up-to-date prediction incorporating recent market data.
    """
    try:
        if online_engine is None:
            init_engines(db)
        
        # Convert to numpy array
        features = np.array(request.features)
        
        result = await online_engine.predict_online(
            coin_symbol=request.coin_symbol,
            features=features,
            return_probabilities=request.return_probabilities
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error in online_learning_predict: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/online/status/{coin_symbol}")
async def get_online_model_status(
    coin_symbol: str,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get status of online learning model for a coin.
    
    Includes:
    - Training status
    - Performance metrics
    - Learning rate
    - Drift detection status
    """
    try:
        if online_engine is None:
            init_engines(db)
        
        status = await online_engine.get_model_status(coin_symbol)
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Error in get_online_model_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/online/reset/{coin_symbol}")
async def reset_online_model(
    coin_symbol: str,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reset online learning model (useful after major regime change).
    """
    try:
        if online_engine is None:
            init_engines(db)
        
        await online_engine.reset_model(coin_symbol)
        
        return {
            "success": True,
            "message": f"Online learning model reset for {coin_symbol}"
        }
        
    except Exception as e:
        logger.error(f"Error in reset_online_model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outcome/update")
async def update_prediction_outcome(
    request: OutcomeUpdateRequest,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update a prediction with its actual outcome.
    
    Used for calibration learning and model performance tracking.
    """
    try:
        if enhanced_engine is None:
            init_engines(db)
        
        await enhanced_engine.update_prediction_outcome(
            prediction_id=request.prediction_id,
            actual_outcome=request.actual_outcome,
            was_correct=request.was_correct,
            actual_price_change=request.actual_price_change
        )
        
        return {
            "success": True,
            "message": "Prediction outcome updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in update_prediction_outcome: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/summary")
async def get_performance_summary(
    coin_symbol: Optional[str] = None,
    days: int = 30,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get performance summary of enhanced predictions.
    
    Includes accuracy, calibration, and uncertainty metrics.
    """
    try:
        from datetime import timedelta
        
        # Build query
        query = {'outcome_verified': True}
        if coin_symbol:
            query['coin'] = coin_symbol
        
        # Time filter
        start_date = datetime.now() - timedelta(days=days)
        query['created_at'] = {'$gte': start_date}
        
        # Aggregate performance metrics
        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': None,
                'total': {'$sum': 1},
                'correct': {'$sum': {'$cond': ['$was_correct', 1, 0]}},
                'avg_confidence': {'$avg': '$confidence'},
                'avg_uncertainty': {'$avg': '$uncertainty.variance'}
            }}
        ]
        
        if enhanced_engine is None:
            init_engines(db)
        
        result = await db.enhanced_predictions.aggregate(pipeline).to_list(1)
        
        if result:
            data = result[0]
            accuracy = data['correct'] / data['total'] if data['total'] > 0 else 0
            
            summary = {
                'total_predictions': data['total'],
                'correct_predictions': data['correct'],
                'accuracy': accuracy,
                'avg_confidence': data.get('avg_confidence', 0),
                'avg_uncertainty': data.get('avg_uncertainty', 0),
                'calibration_score': abs(accuracy - data.get('avg_confidence', 0) / 100),
                'period_days': days,
                'coin': coin_symbol or 'all'
            }
        else:
            summary = {
                'total_predictions': 0,
                'message': 'No predictions found for the specified period'
            }
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error in get_performance_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for enhanced ML services"""
    return {
        "status": "healthy",
        "enhanced_engine_initialized": enhanced_engine is not None,
        "online_engine_initialized": online_engine is not None,
        "timestamp": datetime.now().isoformat()
    }
