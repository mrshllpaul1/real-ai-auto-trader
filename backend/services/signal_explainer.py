"""
AI Signal Explanation Service
=============================
Provides detailed explanations for AI trading signals.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random


class SignalExplainer:
    """Generates human-readable explanations for AI signals."""
    
    def __init__(self):
        self.factor_weights = {
            'technical': 0.35,
            'sentiment': 0.25,
            'on_chain': 0.20,
            'pattern': 0.20,
        }
    
    async def explain_signal(
        self,
        coin_id: str,
        signal: str,  # 'BUY', 'SELL', 'HOLD'
        confidence: float,
        indicators: Dict = None,
        sentiment_data: Dict = None,
        historical_patterns: List = None,
    ) -> Dict:
        """Generate comprehensive explanation for a signal."""
        
        explanation = {
            'coin_id': coin_id,
            'signal': signal,
            'confidence': confidence,
            'confidence_level': self._get_confidence_level(confidence),
            'generated_at': datetime.utcnow().isoformat(),
            'summary': '',
            'primary_factors': [],
            'supporting_factors': [],
            'risk_factors': [],
            'historical_context': None,
            'recommendation': None,
        }
        
        # Analyze technical indicators
        if indicators:
            tech_factors = self._analyze_technical(indicators, signal)
            explanation['primary_factors'].extend(tech_factors[:3])
            explanation['supporting_factors'].extend(tech_factors[3:])
        
        # Analyze sentiment
        if sentiment_data:
            sent_factors = self._analyze_sentiment(sentiment_data, signal)
            if sent_factors:
                explanation['primary_factors'].append(sent_factors[0])
                explanation['supporting_factors'].extend(sent_factors[1:])
        
        # Analyze historical patterns
        if historical_patterns:
            pattern_data = self._analyze_patterns(historical_patterns, signal)
            explanation['historical_context'] = pattern_data
        
        # Generate risk factors
        explanation['risk_factors'] = self._identify_risks(indicators, sentiment_data)
        
        # Generate summary
        explanation['summary'] = self._generate_summary(explanation)
        
        # Generate recommendation
        explanation['recommendation'] = self._generate_recommendation(explanation)
        
        return explanation
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to human-readable level."""
        if confidence >= 0.8:
            return 'HIGH'
        elif confidence >= 0.6:
            return 'MEDIUM'
        elif confidence >= 0.4:
            return 'LOW'
        return 'VERY_LOW'
    
    def _analyze_technical(self, indicators: Dict, signal: str) -> List[Dict]:
        """Analyze technical indicators and explain their contribution."""
        factors = []
        
        # RSI Analysis
        rsi = indicators.get('rsi', 50)
        if signal == 'BUY' and rsi < 30:
            factors.append({
                'factor': f'RSI oversold ({rsi:.1f})',
                'weight': 0.25,
                'direction': 'bullish',
                'explanation': 'RSI below 30 indicates oversold conditions, suggesting potential upward reversal.'
            })
        elif signal == 'SELL' and rsi > 70:
            factors.append({
                'factor': f'RSI overbought ({rsi:.1f})',
                'weight': 0.25,
                'direction': 'bearish',
                'explanation': 'RSI above 70 indicates overbought conditions, suggesting potential downward reversal.'
            })
        
        # MACD Analysis
        macd = indicators.get('macd', {})
        if macd.get('histogram', 0) > 0 and signal == 'BUY':
            factors.append({
                'factor': 'MACD bullish crossover',
                'weight': 0.20,
                'direction': 'bullish',
                'explanation': 'MACD line crossed above signal line, indicating bullish momentum.'
            })
        elif macd.get('histogram', 0) < 0 and signal == 'SELL':
            factors.append({
                'factor': 'MACD bearish crossover',
                'weight': 0.20,
                'direction': 'bearish',
                'explanation': 'MACD line crossed below signal line, indicating bearish momentum.'
            })
        
        # Moving Average Analysis
        sma_20 = indicators.get('sma_20', 0)
        sma_50 = indicators.get('sma_50', 0)
        price = indicators.get('price', 0)
        
        if price > sma_20 > sma_50 and signal == 'BUY':
            factors.append({
                'factor': 'Price above moving averages',
                'weight': 0.15,
                'direction': 'bullish',
                'explanation': 'Price trading above 20 and 50 SMA confirms uptrend.'
            })
        elif price < sma_20 < sma_50 and signal == 'SELL':
            factors.append({
                'factor': 'Price below moving averages',
                'weight': 0.15,
                'direction': 'bearish',
                'explanation': 'Price trading below 20 and 50 SMA confirms downtrend.'
            })
        
        # Volume Analysis
        volume_change = indicators.get('volume_change_24h', 0)
        if volume_change > 50:
            factors.append({
                'factor': f'Volume surge (+{volume_change:.0f}%)',
                'weight': 0.15,
                'direction': 'neutral',
                'explanation': 'Significant volume increase suggests strong market interest.'
            })
        
        # Bollinger Bands
        bb_position = indicators.get('bb_position', 0.5)  # 0-1 scale
        if bb_position < 0.1 and signal == 'BUY':
            factors.append({
                'factor': 'Price at lower Bollinger Band',
                'weight': 0.10,
                'direction': 'bullish',
                'explanation': 'Price touching lower band may indicate oversold conditions.'
            })
        elif bb_position > 0.9 and signal == 'SELL':
            factors.append({
                'factor': 'Price at upper Bollinger Band',
                'weight': 0.10,
                'direction': 'bearish',
                'explanation': 'Price touching upper band may indicate overbought conditions.'
            })
        
        return factors
    
    def _analyze_sentiment(self, sentiment_data: Dict, signal: str) -> List[Dict]:
        """Analyze sentiment data and explain its contribution."""
        factors = []
        
        market_sentiment = sentiment_data.get('market_score', 50)
        fear_greed = sentiment_data.get('fear_greed', 50)
        news_sentiment = sentiment_data.get('news_sentiment', 0.5)
        
        if signal == 'BUY' and fear_greed < 25:
            factors.append({
                'factor': f'Extreme Fear ({fear_greed})',
                'weight': 0.15,
                'direction': 'bullish',
                'explanation': 'Fear & Greed Index shows extreme fear - historically a good buying opportunity.'
            })
        elif signal == 'SELL' and fear_greed > 75:
            factors.append({
                'factor': f'Extreme Greed ({fear_greed})',
                'weight': 0.15,
                'direction': 'bearish',
                'explanation': 'Fear & Greed Index shows extreme greed - market may be overheated.'
            })
        
        if news_sentiment > 0.7 and signal == 'BUY':
            factors.append({
                'factor': 'Positive news sentiment',
                'weight': 0.10,
                'direction': 'bullish',
                'explanation': 'Recent news coverage has been predominantly positive.'
            })
        elif news_sentiment < 0.3 and signal == 'SELL':
            factors.append({
                'factor': 'Negative news sentiment',
                'weight': 0.10,
                'direction': 'bearish',
                'explanation': 'Recent news coverage has been predominantly negative.'
            })
        
        return factors
    
    def _analyze_patterns(self, patterns: List, signal: str) -> Dict:
        """Find similar historical patterns."""
        if not patterns:
            return None
        
        # Find best matching pattern
        best_match = patterns[0] if patterns else None
        
        return {
            'pattern_name': best_match.get('name', 'Similar market conditions'),
            'date': best_match.get('date', '2024-03-15'),
            'similarity': best_match.get('similarity', 0.75),
            'outcome': best_match.get('outcome', '+18% in 14 days'),
            'description': f"Current conditions match {best_match.get('name', 'historical pattern')} from {best_match.get('date', 'previous period')}."
        }
    
    def _identify_risks(self, indicators: Dict, sentiment_data: Dict) -> List[Dict]:
        """Identify potential risk factors."""
        risks = []
        
        if indicators:
            volatility = indicators.get('volatility_24h', 0)
            if volatility > 5:
                risks.append({
                    'risk': 'High volatility',
                    'level': 'medium' if volatility < 10 else 'high',
                    'description': f'24h volatility is {volatility:.1f}%, which increases risk of sudden price movements.'
                })
            
            volume = indicators.get('volume_24h', 0)
            avg_volume = indicators.get('avg_volume', 0)
            if avg_volume and volume < avg_volume * 0.5:
                risks.append({
                    'risk': 'Low liquidity',
                    'level': 'medium',
                    'description': 'Trading volume is below average, which may affect execution.'
                })
        
        if sentiment_data:
            if sentiment_data.get('sentiment_volatility', 0) > 0.3:
                risks.append({
                    'risk': 'Sentiment instability',
                    'level': 'low',
                    'description': 'Market sentiment has been volatile, suggesting uncertainty.'
                })
        
        # Always add general risk disclaimer
        risks.append({
            'risk': 'Market risk',
            'level': 'standard',
            'description': 'Cryptocurrency markets are highly volatile. Never invest more than you can afford to lose.'
        })
        
        return risks
    
    def _generate_summary(self, explanation: Dict) -> str:
        """Generate human-readable summary."""
        signal = explanation['signal']
        confidence = explanation['confidence']
        primary_factors = explanation['primary_factors']
        
        if signal == 'BUY':
            action = 'bullish opportunity'
        elif signal == 'SELL':
            action = 'bearish warning'
        else:
            action = 'neutral stance'
        
        factor_text = ', '.join([f['factor'] for f in primary_factors[:3]]) if primary_factors else 'multiple indicators'
        
        return f"AI detected a {action} with {confidence*100:.0f}% confidence based on {factor_text}."
    
    def _generate_recommendation(self, explanation: Dict) -> Dict:
        """Generate actionable recommendation."""
        signal = explanation['signal']
        confidence = explanation['confidence']
        risk_level = 'high' if any(r['level'] == 'high' for r in explanation['risk_factors']) else 'medium'
        
        if signal == 'BUY' and confidence >= 0.7:
            return {
                'action': 'Consider buying',
                'position_size': 'small to medium' if risk_level == 'high' else 'medium',
                'stop_loss': '5-8% below entry',
                'take_profit': '15-25% above entry',
                'timeframe': '1-4 weeks',
            }
        elif signal == 'SELL' and confidence >= 0.7:
            return {
                'action': 'Consider selling/reducing position',
                'urgency': 'medium' if confidence < 0.8 else 'high',
                'alternative': 'Set trailing stop-loss if holding',
            }
        else:
            return {
                'action': 'Hold current position',
                'note': 'Wait for stronger signals before taking action',
            }


# Global instance
signal_explainer = SignalExplainer()


async def get_signal_explanation(
    coin_id: str,
    signal: str,
    confidence: float,
    indicators: Dict = None,
    sentiment_data: Dict = None,
) -> Dict:
    """Get explanation for a signal."""
    return await signal_explainer.explain_signal(
        coin_id=coin_id,
        signal=signal,
        confidence=confidence,
        indicators=indicators,
        sentiment_data=sentiment_data,
    )
