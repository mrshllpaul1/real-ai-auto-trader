"""
Performance Tracking & Regime Prediction API Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/performance", tags=["Performance & Prediction"])

# Global references
db = None
performance_tracker = None
regime_predictor = None


def set_dependencies(database, perf_tracker, reg_predictor):
    """Set dependencies from main app"""
    global db, performance_tracker, regime_predictor
    db = database
    performance_tracker = perf_tracker
    regime_predictor = reg_predictor


class TradeOutcomeRequest(BaseModel):
    trade_id: str
    coin_id: str
    entry_price: float
    exit_price: float
    position_size: float
    regime_at_entry: str
    regime_at_exit: str
    hold_hours: float
    exit_reason: str
    strategy_params: Dict[str, float] = {}


class RegimePredictionRequest(BaseModel):
    symbol: str = "BTC"
    use_model: Optional[str] = None


# ==================== PERFORMANCE TRACKING ====================

@router.get("/trading")
async def get_trading_performance(days: int = 30):
    """
    Get comprehensive trading performance metrics.
    
    Includes:
    - Win rate, total P&L, Sharpe ratio
    - Performance by regime
    - Best/worst trades
    """
    if not performance_tracker:
        raise HTTPException(status_code=503, detail="Performance tracker not initialized")
    
    return await performance_tracker.get_trading_performance(days)


@router.get("/regime-accuracy")
async def get_regime_prediction_accuracy(days: int = 30):
    """
    Get regime prediction accuracy metrics.
    
    Includes:
    - Overall accuracy
    - Accuracy by model
    - Best performing model
    """
    if not performance_tracker:
        raise HTTPException(status_code=503, detail="Performance tracker not initialized")
    
    return await performance_tracker.get_regime_prediction_accuracy(days)


@router.get("/parameters")
async def get_parameter_effectiveness(days: int = 30):
    """
    Analyze which strategy parameters performed best.
    
    Analyzes:
    - Stop loss effectiveness
    - Position size impact
    - Regime-specific performance
    """
    if not performance_tracker:
        raise HTTPException(status_code=503, detail="Performance tracker not initialized")
    
    return await performance_tracker.get_parameter_effectiveness(days)


@router.get("/suggestions")
async def get_parameter_suggestions():
    """
    Get AI-powered parameter adjustment suggestions.
    
    Based on:
    - Recent performance
    - Regime prediction accuracy
    - Win rate trends
    """
    if not performance_tracker:
        raise HTTPException(status_code=503, detail="Performance tracker not initialized")
    
    return await performance_tracker.suggest_parameter_adjustments()


@router.post("/record-trade")
async def record_trade_outcome(request: TradeOutcomeRequest):
    """Record a completed trade outcome"""
    if not performance_tracker:
        raise HTTPException(status_code=503, detail="Performance tracker not initialized")
    
    return await performance_tracker.record_trade_outcome(
        trade_id=request.trade_id,
        coin_id=request.coin_id,
        entry_price=request.entry_price,
        exit_price=request.exit_price,
        position_size=request.position_size,
        regime_at_entry=request.regime_at_entry,
        regime_at_exit=request.regime_at_exit,
        hold_hours=request.hold_hours,
        exit_reason=request.exit_reason,
        strategy_params=request.strategy_params
    )


# ==================== REGIME PREDICTION ====================

@router.post("/regime/train")
async def train_regime_models(symbol: str = "BTC"):
    """
    Train all regime prediction models (ML + DL).
    
    Models trained:
    - Random Forest (ML)
    - Gradient Boosting (ML)
    - SVM (ML)
    - LSTM (DL)
    - GRU (DL)
    
    Returns accuracy for each model and selects the best.
    """
    if not regime_predictor:
        raise HTTPException(status_code=503, detail="Regime predictor not initialized")
    
    return await regime_predictor.train_models(symbol)


@router.post("/regime/predict")
async def predict_regime(request: RegimePredictionRequest):
    """
    Predict current market regime using best model.
    
    Returns:
    - Predicted regime
    - Confidence score
    - All model predictions for comparison
    """
    if not regime_predictor:
        raise HTTPException(status_code=503, detail="Regime predictor not initialized")
    
    return await regime_predictor.predict_regime(
        symbol=request.symbol,
        use_model=request.use_model
    )


@router.get("/regime/compare")
async def compare_models():
    """
    Compare all trained models' performance.
    
    Returns:
    - Model ranking by accuracy
    - Best ML model
    - Best DL model
    """
    if not regime_predictor:
        raise HTTPException(status_code=503, detail="Regime predictor not initialized")
    
    return await regime_predictor.compare_models()


@router.get("/regime/history")
async def get_training_history(limit: int = 10):
    """Get model training history"""
    if not regime_predictor:
        raise HTTPException(status_code=503, detail="Regime predictor not initialized")
    
    return await regime_predictor.get_training_history(limit)


# ==================== COMBINED DASHBOARD ====================

@router.get("/dashboard")
async def get_performance_dashboard():
    """
    Get complete performance dashboard.
    
    Combines:
    - Trading metrics (7d, 30d)
    - Regime prediction accuracy
    - Model comparison
    - Parameter suggestions
    """
    if not performance_tracker or not regime_predictor:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        perf_7d = await performance_tracker.get_trading_performance(7)
        perf_30d = await performance_tracker.get_trading_performance(30)
        regime_acc = await performance_tracker.get_regime_prediction_accuracy(30)
        model_compare = await regime_predictor.compare_models()
        suggestions = await performance_tracker.suggest_parameter_adjustments()
        
        return {
            'trading_performance': {
                '7_day': {
                    'win_rate': perf_7d.get('win_rate'),
                    'trades': perf_7d.get('total_trades'),
                    'pnl': perf_7d.get('total_pnl_usd')
                },
                '30_day': {
                    'win_rate': perf_30d.get('win_rate'),
                    'trades': perf_30d.get('total_trades'),
                    'pnl': perf_30d.get('total_pnl_usd'),
                    'sharpe': perf_30d.get('sharpe_ratio'),
                    'profit_factor': perf_30d.get('profit_factor')
                }
            },
            'regime_prediction': {
                'accuracy': regime_acc.get('overall_accuracy'),
                'best_model': regime_acc.get('best_model'),
                'total_predictions': regime_acc.get('total_predictions')
            },
            'model_comparison': model_compare,
            'suggestions': suggestions.get('suggestions', []),
            'recommended_adjustments': suggestions.get('adjustments', {}),
            'generated_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Some metrics unavailable'
        }


@router.get("/regime/ml-vs-dl")
async def compare_ml_vs_dl():
    """
    Comprehensive comparison of Machine Learning vs Deep Learning models.
    
    Returns:
    - ML models: Random Forest, Gradient Boosting, SVM
    - DL models: LSTM, GRU, BiLSTM, CNN-LSTM, Attention
    - Side-by-side accuracy comparison
    - Best in each category
    - Recommendation
    """
    if not regime_predictor:
        raise HTTPException(status_code=503, detail="Regime predictor not initialized")
    
    model_accuracy = regime_predictor.model_accuracy
    model_metadata = regime_predictor.model_metadata
    
    ml_models = []
    dl_models = []
    
    for model_name, accuracy in model_accuracy.items():
        metadata = model_metadata.get(model_name, {})
        model_info = {
            'name': model_name,
            'accuracy': round(accuracy, 2),  # accuracy already stored as percentage
            'type': metadata.get('type', 'Unknown'),
            'category': metadata.get('category', 'Unknown'),
            'description': metadata.get('description', ''),
            'is_best': model_name == regime_predictor.best_model
        }
        
        if metadata.get('type') == 'ML':
            ml_models.append(model_info)
        elif metadata.get('type') == 'DL':
            dl_models.append(model_info)
    
    # Sort by accuracy
    ml_models.sort(key=lambda x: x['accuracy'], reverse=True)
    dl_models.sort(key=lambda x: x['accuracy'], reverse=True)
    
    best_ml = ml_models[0] if ml_models else None
    best_dl = dl_models[0] if dl_models else None
    
    # Determine winner
    winner = None
    if best_ml and best_dl:
        winner = 'ML' if best_ml['accuracy'] > best_dl['accuracy'] else 'DL'
    
    return {
        'ml_models': ml_models,
        'dl_models': dl_models,
        'summary': {
            'total_ml_models': len(ml_models),
            'total_dl_models': len(dl_models),
            'best_ml': best_ml,
            'best_dl': best_dl,
            'overall_best': regime_predictor.best_model,
            'winner': winner,
            'ml_avg_accuracy': round(sum(m['accuracy'] for m in ml_models) / len(ml_models), 2) if ml_models else 0,
            'dl_avg_accuracy': round(sum(m['accuracy'] for m in dl_models) / len(dl_models), 2) if dl_models else 0
        },
        'recommendation': f"Use {regime_predictor.best_model} ({winner}) for regime prediction - highest accuracy at {model_accuracy.get(regime_predictor.best_model, 0) * 100:.1f}%",
        'trained': regime_predictor.is_trained,
        'timestamp': datetime.utcnow().isoformat()
    }


@router.get("/regime/models")
async def get_all_models():
    """Get detailed information about all available models"""
    if not regime_predictor:
        raise HTTPException(status_code=503, detail="Regime predictor not initialized")
    
    models = []
    for model_name in regime_predictor.models.keys():
        metadata = regime_predictor.model_metadata.get(model_name, {})
        accuracy = regime_predictor.model_accuracy.get(model_name)
        
        models.append({
            'name': model_name,
            'type': metadata.get('type', 'Unknown'),
            'category': metadata.get('category', 'Unknown'),
            'description': metadata.get('description', ''),
            'accuracy': round(accuracy * 100, 2) if accuracy else None,
            'is_trained': accuracy is not None,
            'is_best': model_name == regime_predictor.best_model
        })
    
    return {
        'models': models,
        'total': len(models),
        'ml_count': len([m for m in models if m['type'] == 'ML']),
        'dl_count': len([m for m in models if m['type'] == 'DL']),
        'best_model': regime_predictor.best_model,
        'is_trained': regime_predictor.is_trained
    }
