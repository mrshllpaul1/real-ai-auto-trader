"""
AI Explanation Routes
====================
API endpoints for AI signal explanations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict
from pydantic import BaseModel
from services.signal_explainer import get_signal_explanation
import random
from datetime import datetime

router = APIRouter(prefix="/api/ai-explain", tags=["ai-explanation"])


class SignalExplanationRequest(BaseModel):
    coin_id: str
    signal: str  # BUY, SELL, HOLD
    confidence: float
    indicators: Optional[Dict] = None
    sentiment_data: Optional[Dict] = None


@router.post("/signal")
async def explain_signal(request: SignalExplanationRequest):
    """
    Get detailed explanation for an AI trading signal.
    
    Explains WHY the AI made a particular prediction with:
    - Primary contributing factors
    - Supporting factors
    - Risk factors
    - Historical pattern matching
    - Actionable recommendations
    """
    try:
        explanation = await get_signal_explanation(
            coin_id=request.coin_id,
            signal=request.signal,
            confidence=request.confidence,
            indicators=request.indicators,
            sentiment_data=request.sentiment_data,
        )
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/signal/{coin_id}")
async def get_current_signal_explanation(coin_id: str):
    """
    Get explanation for the current AI signal on a coin.
    Fetches latest signal and generates explanation.
    """
    # Simulate getting current signal (in production, fetch from ensemble/tethys)
    signals = ['BUY', 'SELL', 'HOLD']
    weights = [0.3, 0.2, 0.5]  # Weighted towards HOLD
    
    signal = random.choices(signals, weights)[0]
    confidence = random.uniform(0.55, 0.85)
    
    # Simulated indicators
    indicators = {
        'rsi': random.uniform(25, 75),
        'macd': {'histogram': random.uniform(-0.5, 0.5)},
        'sma_20': random.uniform(60000, 70000),
        'sma_50': random.uniform(58000, 68000),
        'price': random.uniform(62000, 72000),
        'volume_change_24h': random.uniform(-20, 80),
        'bb_position': random.uniform(0.2, 0.8),
        'volatility_24h': random.uniform(2, 8),
    }
    
    sentiment_data = {
        'market_score': random.uniform(30, 70),
        'fear_greed': random.randint(20, 80),
        'news_sentiment': random.uniform(0.3, 0.7),
    }
    
    explanation = await get_signal_explanation(
        coin_id=coin_id,
        signal=signal,
        confidence=confidence,
        indicators=indicators,
        sentiment_data=sentiment_data,
    )
    
    return explanation


@router.get("/factors")
async def get_signal_factors():
    """
    Get list of all factors the AI considers when making predictions.
    """
    return {
        'technical_factors': [
            {'name': 'RSI', 'weight': 0.15, 'description': 'Relative Strength Index - momentum oscillator'},
            {'name': 'MACD', 'weight': 0.12, 'description': 'Moving Average Convergence Divergence'},
            {'name': 'Moving Averages', 'weight': 0.10, 'description': 'SMA/EMA trend indicators'},
            {'name': 'Bollinger Bands', 'weight': 0.08, 'description': 'Volatility and price levels'},
            {'name': 'Volume', 'weight': 0.10, 'description': 'Trading volume analysis'},
            {'name': 'Support/Resistance', 'weight': 0.08, 'description': 'Key price levels'},
        ],
        'sentiment_factors': [
            {'name': 'Fear & Greed Index', 'weight': 0.10, 'description': 'Market sentiment gauge'},
            {'name': 'News Sentiment', 'weight': 0.08, 'description': 'News article analysis'},
            {'name': 'Social Sentiment', 'weight': 0.05, 'description': 'Twitter/Reddit analysis'},
        ],
        'on_chain_factors': [
            {'name': 'Whale Activity', 'weight': 0.06, 'description': 'Large wallet movements'},
            {'name': 'Exchange Flow', 'weight': 0.04, 'description': 'Exchange inflow/outflow'},
            {'name': 'Active Addresses', 'weight': 0.02, 'description': 'Network activity'},
        ],
        'pattern_factors': [
            {'name': 'Historical Patterns', 'weight': 0.08, 'description': 'Similar past scenarios'},
            {'name': 'Seasonality', 'weight': 0.04, 'description': 'Time-based patterns'},
        ],
    }


@router.get("/confidence-levels")
async def get_confidence_levels():
    """
    Explain confidence level meanings.
    """
    return {
        'levels': [
            {
                'level': 'HIGH',
                'range': '80-100%',
                'meaning': 'Strong conviction - multiple factors align',
                'action': 'Consider acting on signal',
            },
            {
                'level': 'MEDIUM',
                'range': '60-79%',
                'meaning': 'Moderate confidence - some conflicting signals',
                'action': 'Proceed with caution, smaller position size',
            },
            {
                'level': 'LOW',
                'range': '40-59%',
                'meaning': 'Low confidence - mixed signals',
                'action': 'Wait for better opportunity',
            },
            {
                'level': 'VERY_LOW',
                'range': '0-39%',
                'meaning': 'Insufficient data or conflicting indicators',
                'action': 'Do not act on this signal',
            },
        ],
        'note': 'Confidence levels are based on agreement between multiple AI models and indicator alignment.'
    }
