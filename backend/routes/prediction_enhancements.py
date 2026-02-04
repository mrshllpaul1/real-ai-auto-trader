"""
Prediction Enhancements API Routes
Unified endpoint for all 8 prediction enhancements
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

router = APIRouter(prefix="/predictions", tags=["Prediction Enhancements"])
logger = logging.getLogger(__name__)

# Service instances
_db = None
_order_book = None
_on_chain = None
_social_sentiment = None
_transformer = None
_rl_agent = None
_cross_asset = None
_advanced_ta = None


def set_dependencies(db, order_book=None, on_chain=None, social_sentiment=None,
                     transformer=None, rl_agent=None, cross_asset=None, advanced_ta=None):
    """Set dependencies for all prediction services"""
    global _db, _order_book, _on_chain, _social_sentiment
    global _transformer, _rl_agent, _cross_asset, _advanced_ta
    
    _db = db
    _order_book = order_book
    _on_chain = on_chain
    _social_sentiment = social_sentiment
    _transformer = transformer
    _rl_agent = rl_agent
    _cross_asset = cross_asset
    _advanced_ta = advanced_ta


class TrainRequest(BaseModel):
    symbols: Optional[List[str]] = None
    episodes: Optional[int] = 100


# ============ Enhancement #1: Order Book Analysis ============

@router.get("/order-book/{symbol}")
async def analyze_order_book(symbol: str):
    """
    Enhancement #1: Order Book Depth Analysis
    - Bid/Ask spread analysis
    - Order book imbalance
    - Support/Resistance wall detection
    """
    if not _order_book:
        raise HTTPException(status_code=503, detail="Order book analyzer not initialized")
    
    return await _order_book.analyze_order_book(symbol)


@router.get("/order-book/{symbol}/history")
async def get_order_book_history(symbol: str, hours: int = 24):
    """Get historical order book imbalance data"""
    if not _order_book:
        raise HTTPException(status_code=503, detail="Order book analyzer not initialized")
    
    return await _order_book.get_historical_imbalance(symbol, hours)


# ============ Enhancement #2: On-Chain Analytics ============

@router.get("/on-chain/{symbol}")
async def get_on_chain_metrics(symbol: str):
    """
    Enhancement #2: On-Chain Analytics
    - Active addresses
    - NVT ratio
    - Exchange flows
    - Whale movements
    - MVRV ratio
    """
    if not _on_chain:
        raise HTTPException(status_code=503, detail="On-chain analytics not initialized")
    
    return await _on_chain.get_on_chain_metrics(symbol)


@router.get("/on-chain/{symbol}/history")
async def get_on_chain_history(symbol: str, days: int = 7):
    """Get historical on-chain metrics"""
    if not _on_chain:
        raise HTTPException(status_code=503, detail="On-chain analytics not initialized")
    
    return await _on_chain.get_historical_metrics(symbol, days)


# ============ Enhancement #3: Social Sentiment ============

@router.get("/social/{symbol}")
async def get_social_sentiment(symbol: str):
    """
    Enhancement #3: Social Sentiment Pipeline
    - Twitter/X sentiment
    - Reddit sentiment
    - FOMO/Fear detection
    - Hype cycle analysis
    - Influencer tracking
    """
    if not _social_sentiment:
        raise HTTPException(status_code=503, detail="Social sentiment not initialized")
    
    return await _social_sentiment.analyze_social_sentiment(symbol)


@router.get("/social/trending")
async def get_trending_coins(limit: int = 10):
    """Get trending coins based on social activity"""
    if not _social_sentiment:
        raise HTTPException(status_code=503, detail="Social sentiment not initialized")
    
    return await _social_sentiment.get_trending_coins(limit)


# ============ Enhancement #4: Transformer Predictor ============

@router.post("/transformer/train")
async def train_transformer(request: TrainRequest):
    """
    Enhancement #4: Train Transformer Model
    - GPT-style attention mechanism
    - Multi-head self-attention
    - Long-range dependency capture
    """
    if not _transformer:
        raise HTTPException(status_code=503, detail="Transformer predictor not initialized")
    
    return await _transformer.train(request.symbols)


@router.get("/transformer/predict/{symbol}")
async def transformer_predict(symbol: str):
    """Get Transformer model prediction for symbol"""
    if not _transformer:
        raise HTTPException(status_code=503, detail="Transformer predictor not initialized")
    
    return await _transformer.predict(symbol)


@router.get("/transformer/status")
async def transformer_status():
    """Get Transformer model status"""
    if not _transformer:
        return {"initialized": False}
    
    return {
        "initialized": True,
        "is_trained": _transformer.is_trained,
        "last_trained": _transformer.last_trained.isoformat() if _transformer.last_trained else None,
        "config": _transformer.config
    }


# ============ Enhancement #5: RL Trading Agent ============

@router.post("/rl-agent/train")
async def train_rl_agent(request: TrainRequest):
    """
    Enhancement #5: Train Reinforcement Learning Agent
    - DQN-based trading agent
    - Learns optimal entry/exit timing
    - Maximizes portfolio returns
    """
    if not _rl_agent:
        raise HTTPException(status_code=503, detail="RL agent not initialized")
    
    episodes = request.episodes or 100
    return await _rl_agent.train(episodes=episodes, symbols=request.symbols)


@router.get("/rl-agent/signal/{symbol}")
async def rl_agent_signal(symbol: str):
    """Get RL agent trading signal for symbol"""
    if not _rl_agent:
        raise HTTPException(status_code=503, detail="RL agent not initialized")
    
    return await _rl_agent.get_signal(symbol)


@router.get("/rl-agent/status")
async def rl_agent_status():
    """Get RL agent training status"""
    if not _rl_agent:
        return {"initialized": False}
    
    summary = _rl_agent.get_training_summary()
    return {
        "initialized": True,
        **summary
    }


# ============ Enhancement #6: Cross-Asset Correlation ============

@router.get("/cross-asset/{symbol}")
async def get_cross_asset_correlation(symbol: str):
    """
    Enhancement #6: Cross-Asset Correlation Analysis
    - BTC dominance impact
    - DXY correlation
    - S&P 500 / Nasdaq correlation
    - Gold correlation
    - Risk regime detection
    """
    if not _cross_asset:
        raise HTTPException(status_code=503, detail="Cross-asset correlation not initialized")
    
    return await _cross_asset.analyze_correlations(symbol)


@router.get("/cross-asset/matrix")
async def get_correlation_matrix():
    """Get full correlation matrix for major assets"""
    if not _cross_asset:
        raise HTTPException(status_code=503, detail="Cross-asset correlation not initialized")
    
    return await _cross_asset.get_correlation_matrix()


# ============ Enhancement #7 & #8: Advanced Technical Analysis ============

@router.get("/advanced-ta/{symbol}")
async def get_advanced_technical(symbol: str):
    """
    Enhancement #7 & #8: Advanced Technical Analysis
    - Volatility regime detection
    - ATR percentile ranking
    - RSI/Price divergence
    - Volume/Price divergence
    - MACD divergence
    - Multi-timeframe confirmation
    """
    if not _advanced_ta:
        raise HTTPException(status_code=503, detail="Advanced TA not initialized")
    
    return await _advanced_ta.analyze(symbol)


# ============ Unified Comprehensive Analysis ============

@router.get("/comprehensive/{symbol}")
async def get_comprehensive_analysis(symbol: str):
    """
    Get comprehensive analysis combining all 8 enhancements
    Returns unified trading signal from all prediction models
    """
    results = {
        'symbol': symbol,
        'timestamp': datetime.utcnow().isoformat(),
        'enhancements': {}
    }
    
    # Collect all available analyses
    analyses = []
    
    if _order_book:
        try:
            results['enhancements']['order_book'] = await _order_book.analyze_order_book(symbol)
            analyses.append(('order_book', results['enhancements']['order_book'].get('signal', {}).get('score', 50)))
        except Exception as e:
            logger.warning(f"Order book analysis failed: {e}")
    
    if _on_chain:
        try:
            results['enhancements']['on_chain'] = await _on_chain.get_on_chain_metrics(symbol)
            analyses.append(('on_chain', results['enhancements']['on_chain'].get('signal', {}).get('score', 50)))
        except Exception as e:
            logger.warning(f"On-chain analysis failed: {e}")
    
    if _social_sentiment:
        try:
            results['enhancements']['social'] = await _social_sentiment.analyze_social_sentiment(symbol)
            analyses.append(('social', results['enhancements']['social'].get('signal', {}).get('score', 50)))
        except Exception as e:
            logger.warning(f"Social sentiment analysis failed: {e}")
    
    if _transformer and _transformer.is_trained:
        try:
            pred = await _transformer.predict(symbol)
            results['enhancements']['transformer'] = pred
            # Convert prediction to score
            if pred.get('prediction') == 'up':
                analyses.append(('transformer', 50 + pred.get('confidence', 0) / 2))
            elif pred.get('prediction') == 'down':
                analyses.append(('transformer', 50 - pred.get('confidence', 0) / 2))
            else:
                analyses.append(('transformer', 50))
        except Exception as e:
            logger.warning(f"Transformer prediction failed: {e}")
    
    if _rl_agent and _rl_agent.is_trained:
        try:
            signal = await _rl_agent.get_signal(symbol)
            results['enhancements']['rl_agent'] = signal
            if signal.get('signal') == 'buy':
                analyses.append(('rl_agent', 50 + signal.get('confidence', 0) / 2))
            elif signal.get('signal') == 'sell':
                analyses.append(('rl_agent', 50 - signal.get('confidence', 0) / 2))
            else:
                analyses.append(('rl_agent', 50))
        except Exception as e:
            logger.warning(f"RL agent signal failed: {e}")
    
    if _cross_asset:
        try:
            results['enhancements']['cross_asset'] = await _cross_asset.analyze_correlations(symbol)
            analyses.append(('cross_asset', results['enhancements']['cross_asset'].get('signal', {}).get('score', 50)))
        except Exception as e:
            logger.warning(f"Cross-asset analysis failed: {e}")
    
    if _advanced_ta:
        try:
            results['enhancements']['advanced_ta'] = await _advanced_ta.analyze(symbol)
            analyses.append(('advanced_ta', results['enhancements']['advanced_ta'].get('signal', {}).get('score', 50)))
        except Exception as e:
            logger.warning(f"Advanced TA failed: {e}")
    
    # Calculate composite score
    if analyses:
        weights = {
            'order_book': 0.10,
            'on_chain': 0.15,
            'social': 0.10,
            'transformer': 0.20,
            'rl_agent': 0.15,
            'cross_asset': 0.15,
            'advanced_ta': 0.15
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for name, score in analyses:
            weight = weights.get(name, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        composite_score = weighted_sum / total_weight if total_weight > 0 else 50
        
        # Determine signal
        if composite_score >= 70:
            signal = 'strong_buy'
        elif composite_score >= 60:
            signal = 'buy'
        elif composite_score <= 30:
            signal = 'strong_sell'
        elif composite_score <= 40:
            signal = 'sell'
        else:
            signal = 'neutral'
        
        results['composite'] = {
            'signal': signal,
            'score': round(composite_score, 2),
            'confidence': round(abs(composite_score - 50) * 2, 2),
            'models_used': len(analyses),
            'breakdown': {name: round(score, 2) for name, score in analyses}
        }
    else:
        results['composite'] = {
            'signal': 'neutral',
            'score': 50,
            'confidence': 0,
            'models_used': 0,
            'error': 'No prediction models available'
        }
    
    return results


# ============ Service Status ============

@router.get("/status")
async def get_prediction_services_status():
    """Get status of all prediction enhancement services"""
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'order_book_analyzer': _order_book is not None,
            'on_chain_analytics': _on_chain is not None,
            'social_sentiment': _social_sentiment is not None,
            'transformer_predictor': {
                'initialized': _transformer is not None,
                'trained': _transformer.is_trained if _transformer else False
            },
            'rl_trading_agent': {
                'initialized': _rl_agent is not None,
                'trained': _rl_agent.is_trained if _rl_agent else False
            },
            'cross_asset_correlation': _cross_asset is not None,
            'advanced_technical_analysis': _advanced_ta is not None
        },
        'enhancements': [
            '#1 Order Book Depth Analysis',
            '#2 On-Chain Analytics',
            '#3 Social Sentiment Pipeline',
            '#4 Transformer Architecture',
            '#5 Reinforcement Learning Agent',
            '#6 Cross-Asset Correlation',
            '#7 Volatility Regime Detection',
            '#8 Momentum Divergence Signals'
        ]
    }
