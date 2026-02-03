"""
Deep Learning AI API Routes
Provides endpoints for advanced AI trading predictions using neural networks.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/deep-learning", tags=["Deep Learning AI"])

# Dependencies
_db = None
_deep_ai = None
_market_service = None

def set_dependencies(db, market_service=None):
    """Set dependencies from server.py"""
    global _db, _deep_ai, _market_service
    _db = db
    _market_service = market_service
    
    from services.deep_learning_ai import get_deep_learning_ai
    _deep_ai = get_deep_learning_ai(db)


class TrainRequest(BaseModel):
    coin_id: str
    days: int = 90


class PredictRequest(BaseModel):
    coin_id: str
    include_sentiment: bool = True
    include_patterns: bool = True


class SentimentRequest(BaseModel):
    texts: List[str]


class SignalRequest(BaseModel):
    coin_ids: List[str] = ["bitcoin", "ethereum", "solana"]


@router.get("/status")
async def get_ai_status():
    """Get status of all deep learning models"""
    if not _deep_ai:
        raise HTTPException(status_code=503, detail="Deep Learning AI not initialized")
    
    status = await _deep_ai.get_model_status()
    return {
        "status": "operational",
        "models": status,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/train/{coin_id}")
async def train_model(coin_id: str, days: int = 90):
    """Train the LSTM model on historical price data for a specific coin"""
    if not _deep_ai or not _market_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Fetch historical data
        hist_data = await _market_service.get_historical_data(coin_id, days=days)
        prices = [p[1] for p in hist_data.get('prices', [])]
        
        if len(prices) < 100:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough historical data. Got {len(prices)} prices, need at least 100"
            )
        
        # Train the model
        result = await _deep_ai.train_on_coin(coin_id, prices)
        
        return {
            "success": True,
            "coin_id": coin_id,
            "training_result": result,
            "prices_used": len(prices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/{coin_id}")
async def predict_price(coin_id: str, include_news: bool = True):
    """Get AI price prediction for a coin"""
    if not _deep_ai or not _market_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Fetch recent prices
        hist_data = await _market_service.get_historical_data(coin_id, days=90)
        prices = [p[1] for p in hist_data.get('prices', [])]
        
        if len(prices) < 60:
            raise HTTPException(status_code=400, detail="Not enough price data")
        
        # Get news if requested
        news = []
        if include_news:
            try:
                from services.news_service import CryptoNewsAggregator
                news_service = CryptoNewsAggregator()
                news = await news_service.get_free_crypto_news(limit=20)
            except:
                pass
        
        # Get current price
        current = await _market_service.get_coin_price([coin_id])
        current_price = current.get(coin_id, {}).get('current_price', prices[-1])
        
        # Generate signal
        signal = await _deep_ai.generate_deep_signal(
            coin_id=coin_id,
            prices=prices,
            news=news,
            current_price=current_price
        )
        
        return signal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-sentiment")
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment of provided texts"""
    if not _deep_ai:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        news_items = [{"title": text} for text in request.texts]
        result = await _deep_ai.sentiment_analyzer.analyze_news_batch(news_items)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-patterns/{coin_id}")
async def detect_patterns(coin_id: str, window_days: int = 30):
    """Detect chart patterns for a coin"""
    if not _deep_ai or not _market_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        hist_data = await _market_service.get_historical_data(coin_id, days=window_days)
        prices = [p[1] for p in hist_data.get('prices', [])]
        
        if len(prices) < 20:
            raise HTTPException(status_code=400, detail="Not enough price data")
        
        patterns = _deep_ai.pattern_recognizer.detect_patterns_rule_based(prices)
        
        return {
            "coin_id": coin_id,
            "window_days": window_days,
            "prices_analyzed": len(prices),
            "patterns": patterns
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-signal")
async def get_multi_coin_signals(request: SignalRequest):
    """Get AI signals for multiple coins"""
    if not _deep_ai or not _market_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        signals = []
        
        for coin_id in request.coin_ids[:5]:  # Limit to 5 coins
            try:
                hist_data = await _market_service.get_historical_data(coin_id, days=60)
                prices = [p[1] for p in hist_data.get('prices', [])]
                
                if len(prices) >= 30:
                    signal = await _deep_ai.generate_deep_signal(
                        coin_id=coin_id,
                        prices=prices,
                        news=None,  # Skip news for bulk
                        current_price=prices[-1]
                    )
                    signals.append(signal)
            except Exception as e:
                signals.append({
                    "coin_id": coin_id,
                    "error": str(e),
                    "final_signal": "ERROR"
                })
        
        # Sort by confidence
        signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return {
            "signals": signals,
            "count": len(signals),
            "timestamp": datetime.now().isoformat(),
            "top_pick": signals[0] if signals else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lstm/info")
async def get_lstm_info():
    """Get information about the LSTM model"""
    if not _deep_ai:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    predictor = _deep_ai.price_predictor
    
    return {
        "model_type": "LSTM (Long Short-Term Memory)",
        "architecture": {
            "layers": ["LSTM(128)", "LSTM(64)", "LSTM(32)", "Dense(32)", "Dense(16)", "Dense(output)"],
            "sequence_length": predictor.sequence_length,
            "prediction_horizon": predictor.prediction_horizon
        },
        "training_status": {
            "is_trained": predictor.is_trained,
            "model_params": predictor.model.count_params() if predictor.model else 0
        },
        "capabilities": [
            "Multi-day price prediction",
            "Trend direction forecasting",
            "Confidence scoring"
        ]
    }


class PreLaunchAnalysisRequest(BaseModel):
    coin_name: str
    category: Optional[str] = "privacy"
    description: Optional[str] = ""
    similar_coins: Optional[List[str]] = None


class ImprovedPredictionRequest(BaseModel):
    coin_id: str
    target_accuracy: Optional[float] = 0.55


@router.post("/analyze-prelaunch")
async def analyze_prelaunch_coin(request: PreLaunchAnalysisRequest):
    """
    Analyze a pre-launch cryptocurrency.
    
    Since pre-launch coins don't have price history, this uses:
    - Comparable coin analysis
    - Category performance trends
    - AI-powered opinion generation
    
    Categories: privacy, defi, layer2, ai, gaming, infrastructure, general
    """
    if not _deep_ai:
        raise HTTPException(status_code=503, detail="Deep Learning AI not initialized")
    
    result = await _deep_ai.analyze_prelaunch_coin(
        coin_name=request.coin_name,
        coin_description=request.description,
        similar_coins=request.similar_coins,
        category=request.category
    )
    
    return result


@router.post("/improved-prediction/{coin_id}")
async def get_improved_prediction(coin_id: str, target_accuracy: float = 0.55):
    """
    Get improved prediction with target accuracy above 55%.
    
    Uses ensemble of:
    - LSTM neural network
    - Technical analysis
    - Pattern recognition
    - Trend analysis
    
    Returns accuracy estimate and whether target is met.
    """
    if not _deep_ai:
        raise HTTPException(status_code=503, detail="Deep Learning AI not initialized")
    
    if not _market_service:
        raise HTTPException(status_code=503, detail="Market service not available")
    
    # Get price data
    hist_data = await _market_service.get_historical_data(coin_id, days=90)
    if not hist_data or not hist_data.get('prices'):
        raise HTTPException(status_code=404, detail=f"No price data for {coin_id}")
    
    prices = [p[1] for p in hist_data['prices']]
    
    result = await _deep_ai.get_improved_prediction(
        coin_id=coin_id,
        prices=prices,
        target_accuracy=target_accuracy
    )
    
    return result


@router.get("/prelaunch-categories")
async def get_prelaunch_categories():
    """Get available categories for pre-launch coin analysis"""
    return {
        "categories": [
            {"id": "privacy", "name": "Privacy Coins", "potential_score": 75, "examples": ["Monero", "Zcash", "ZKP"]},
            {"id": "defi", "name": "DeFi", "potential_score": 70, "examples": ["Uniswap", "Aave", "Curve"]},
            {"id": "layer2", "name": "Layer 2 Solutions", "potential_score": 80, "examples": ["Polygon", "Arbitrum", "Optimism"]},
            {"id": "ai", "name": "AI & Machine Learning", "potential_score": 85, "examples": ["Fetch.ai", "SingularityNET"]},
            {"id": "gaming", "name": "Gaming & Metaverse", "potential_score": 65, "examples": ["Axie", "Sandbox", "Gala"]},
            {"id": "infrastructure", "name": "Infrastructure", "potential_score": 75, "examples": ["Chainlink", "The Graph"]},
            {"id": "general", "name": "General Purpose", "potential_score": 50, "examples": ["Bitcoin", "Ethereum"]}
        ]
    }
