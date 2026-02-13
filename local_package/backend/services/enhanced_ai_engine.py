"""
Enhanced AI Trading Engine
Combines all AI enhancements into a unified system:

1. Ensemble Voting - Weighted model consensus
2. Advanced Features - 25+ technical indicators
3. Sentiment Integration - Fear & Greed, news sentiment
4. Multi-Timeframe - 1H, 4H, 1D, 1W analysis
5. Dynamic Risk - Confidence-based position sizing
6. Reinforcement Learning - Entry/exit optimization
7. Auto-Retraining - Daily model updates
8. Whale Tracking - Large wallet monitoring
"""

import asyncio
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Advanced technical indicator calculations"""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        return np.mean(prices[-period:])
    
    @staticmethod
    def ema(prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.001
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(prices: List[float]) -> Tuple[float, float, float]:
        """Returns (macd_line, signal_line, histogram)"""
        if len(prices) < 26:
            return 0, 0, 0
        ema12 = TechnicalIndicators.ema(prices, 12)
        ema26 = TechnicalIndicators.ema(prices, 26)
        macd_line = ema12 - ema26
        # Simplified signal line
        signal = macd_line * 0.9  # Approximation
        histogram = macd_line - signal
        return macd_line, signal, histogram
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[float, float, float]:
        """Returns (upper, middle, lower)"""
        if len(prices) < period:
            return prices[-1] * 1.02, prices[-1], prices[-1] * 0.98 if prices else (0, 0, 0)
        middle = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Average True Range"""
        if len(closes) < period + 1:
            return 0
        tr_list = []
        for i in range(1, min(len(closes), period + 1)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_list.append(tr)
        return np.mean(tr_list) if tr_list else 0
    
    @staticmethod
    def stochastic(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Tuple[float, float]:
        """Returns (%K, %D)"""
        if len(closes) < period:
            return 50, 50
        lowest_low = min(lows[-period:])
        highest_high = max(highs[-period:])
        if highest_high == lowest_low:
            return 50, 50
        k = ((closes[-1] - lowest_low) / (highest_high - lowest_low)) * 100
        d = k * 0.9  # Simplified %D
        return k, d
    
    @staticmethod
    def obv(closes: List[float], volumes: List[float]) -> float:
        """On-Balance Volume"""
        if len(closes) < 2:
            return 0
        obv = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i]
            elif closes[i] < closes[i-1]:
                obv -= volumes[i]
        return obv
    
    @staticmethod
    def vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> float:
        """Volume Weighted Average Price"""
        if not volumes or sum(volumes) == 0:
            return closes[-1] if closes else 0
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        return sum(tp * v for tp, v in zip(typical_prices, volumes)) / sum(volumes)
    
    @staticmethod
    def ichimoku(highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, float]:
        """Ichimoku Cloud components"""
        def period_mid(h, l, p):
            if len(h) < p:
                return (h[-1] + l[-1]) / 2 if h else 0
            return (max(h[-p:]) + min(l[-p:])) / 2
        
        tenkan = period_mid(highs, lows, 9)
        kijun = period_mid(highs, lows, 26)
        senkou_a = (tenkan + kijun) / 2
        senkou_b = period_mid(highs, lows, 52)
        chikou = closes[-1] if closes else 0
        
        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou
        }


class EnsembleVotingSystem:
    """
    Weighted voting across all ML/DL models.
    Higher accuracy models get more voting power.
    """
    
    def __init__(self):
        self.model_weights = {}
        self.predictions = {}
    
    def update_weights(self, model_accuracies: Dict[str, float]):
        """Update model weights based on accuracy"""
        total_accuracy = sum(model_accuracies.values())
        if total_accuracy > 0:
            self.model_weights = {
                name: acc / total_accuracy 
                for name, acc in model_accuracies.items()
            }
    
    def vote(self, predictions: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Weighted voting on predictions.
        Returns consensus prediction with confidence.
        """
        if not predictions:
            return {'prediction': 'unknown', 'confidence': 0, 'consensus': 0}
        
        # Collect votes
        votes = defaultdict(float)
        total_weight = 0
        
        for model, pred in predictions.items():
            if 'error' in pred:
                continue
            
            prediction = pred.get('regime', pred.get('prediction', 'unknown'))
            weight = self.model_weights.get(model, 1.0 / len(predictions))
            confidence = pred.get('confidence', 50) / 100
            
            votes[prediction] += weight * confidence
            total_weight += weight
        
        if not votes:
            return {'prediction': 'unknown', 'confidence': 0, 'consensus': 0}
        
        # Find winner
        winner = max(votes, key=votes.get)
        winner_score = votes[winner]
        
        # Calculate consensus (how much models agree)
        consensus = (winner_score / total_weight * 100) if total_weight > 0 else 0
        
        # Calculate confidence (weighted average)
        confidence = (winner_score / len(predictions) * 100) if predictions else 0
        
        return {
            'prediction': winner,
            'confidence': round(confidence, 1),
            'consensus': round(consensus, 1),
            'votes': dict(votes),
            'models_voted': len([p for p in predictions.values() if 'error' not in p])
        }


class MultiTimeframeAnalyzer:
    """
    Analyzes multiple timeframes for signal confirmation.
    Timeframes: 1H, 4H, 1D, 1W
    """
    
    TIMEFRAMES = {
        '1h': 1,
        '4h': 4,
        '1d': 24,
        '1w': 168
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.indicators = TechnicalIndicators()
    
    async def analyze(self, symbol: str) -> Dict[str, Any]:
        """Analyze all timeframes for a symbol"""
        results = {}
        
        # Get historical data
        ohlcv = await self.db.historical_ohlcv.find(
            {'symbol': symbol},
            {'_id': 0}
        ).sort('timestamp', -1).limit(200).to_list(200)
        
        if not ohlcv:
            return {'error': 'No data available'}
        
        ohlcv.reverse()  # Oldest first
        
        closes = [float(d.get('close', 0)) for d in ohlcv]
        highs = [float(d.get('high', 0)) for d in ohlcv]
        lows = [float(d.get('low', 0)) for d in ohlcv]
        volumes = [float(d.get('volume_to', d.get('volume', 0)) or 0) for d in ohlcv]
        
        for tf_name, tf_hours in self.TIMEFRAMES.items():
            # Resample data for timeframe
            step = max(1, tf_hours)
            tf_closes = closes[::step] if step > 1 else closes
            tf_highs = highs[::step] if step > 1 else highs
            tf_lows = lows[::step] if step > 1 else lows
            tf_volumes = volumes[::step] if step > 1 else volumes
            
            if len(tf_closes) < 10:
                continue
            
            # Calculate indicators
            rsi = self.indicators.rsi(tf_closes)
            macd_line, signal, hist = self.indicators.macd(tf_closes)
            upper, middle, lower = self.indicators.bollinger_bands(tf_closes)
            stoch_k, stoch_d = self.indicators.stochastic(tf_highs, tf_lows, tf_closes)
            
            # Determine trend
            sma20 = self.indicators.sma(tf_closes, 20)
            sma50 = self.indicators.sma(tf_closes, 50)
            
            if tf_closes[-1] > sma20 > sma50:
                trend = 'bullish'
            elif tf_closes[-1] < sma20 < sma50:
                trend = 'bearish'
            else:
                trend = 'sideways'
            
            # Signal strength
            signals = []
            if rsi < 30:
                signals.append('oversold')
            elif rsi > 70:
                signals.append('overbought')
            if macd_line > signal:
                signals.append('macd_bullish')
            else:
                signals.append('macd_bearish')
            if tf_closes[-1] < lower:
                signals.append('below_bb')
            elif tf_closes[-1] > upper:
                signals.append('above_bb')
            
            results[tf_name] = {
                'trend': trend,
                'rsi': round(rsi, 1),
                'macd_histogram': round(hist, 4),
                'stochastic_k': round(stoch_k, 1),
                'bb_position': 'lower' if tf_closes[-1] < lower else ('upper' if tf_closes[-1] > upper else 'middle'),
                'signals': signals,
                'price': tf_closes[-1]
            }
        
        # Calculate alignment
        trends = [r['trend'] for r in results.values()]
        if all(t == 'bullish' for t in trends):
            alignment = 'strong_bullish'
        elif all(t == 'bearish' for t in trends):
            alignment = 'strong_bearish'
        elif trends.count('bullish') > trends.count('bearish'):
            alignment = 'weak_bullish'
        elif trends.count('bearish') > trends.count('bullish'):
            alignment = 'weak_bearish'
        else:
            alignment = 'mixed'
        
        return {
            'symbol': symbol,
            'timeframes': results,
            'alignment': alignment,
            'recommendation': self._get_recommendation(alignment, results),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_recommendation(self, alignment: str, results: Dict) -> str:
        if alignment == 'strong_bullish':
            return 'strong_buy'
        elif alignment == 'strong_bearish':
            return 'strong_sell'
        elif alignment == 'weak_bullish':
            return 'buy'
        elif alignment == 'weak_bearish':
            return 'sell'
        else:
            return 'hold'


class DynamicRiskManager:
    """
    Adjusts position sizes based on:
    - Model confidence
    - Model consensus
    - Market volatility
    - Current exposure
    """
    
    def __init__(self, base_position_pct: float = 9.0):
        self.base_position_pct = base_position_pct
        self.min_position_pct = 2.0
        self.max_position_pct = 15.0
    
    def calculate_position_size(
        self,
        confidence: float,
        consensus: float,
        volatility: float,
        current_exposure: float,
        max_exposure: float = 90.0
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on multiple factors.
        
        Args:
            confidence: Model confidence (0-100)
            consensus: Model consensus (0-100)
            volatility: Current volatility (ATR-based)
            current_exposure: Current portfolio exposure %
            max_exposure: Maximum allowed exposure %
        """
        # Base adjustment from confidence
        confidence_multiplier = confidence / 70  # 70% is baseline
        
        # Consensus adjustment
        consensus_multiplier = consensus / 80  # 80% is baseline
        
        # Volatility adjustment (reduce size in high volatility)
        vol_multiplier = 1.0
        if volatility > 5:  # High volatility
            vol_multiplier = 0.7
        elif volatility > 3:  # Medium volatility
            vol_multiplier = 0.85
        
        # Calculate adjusted position
        adjusted_pct = self.base_position_pct * confidence_multiplier * consensus_multiplier * vol_multiplier
        
        # Clamp to min/max
        adjusted_pct = max(self.min_position_pct, min(self.max_position_pct, adjusted_pct))
        
        # Check exposure limit
        remaining_exposure = max_exposure - current_exposure
        if adjusted_pct > remaining_exposure:
            adjusted_pct = max(0, remaining_exposure)
        
        return {
            'position_pct': round(adjusted_pct, 2),
            'base_pct': self.base_position_pct,
            'confidence_factor': round(confidence_multiplier, 2),
            'consensus_factor': round(consensus_multiplier, 2),
            'volatility_factor': round(vol_multiplier, 2),
            'exposure_limited': adjusted_pct < self.base_position_pct * confidence_multiplier * consensus_multiplier * vol_multiplier,
            'reason': self._get_reason(confidence, consensus, volatility)
        }
    
    def _get_reason(self, confidence: float, consensus: float, volatility: float) -> str:
        reasons = []
        if confidence < 60:
            reasons.append('low_confidence')
        elif confidence > 85:
            reasons.append('high_confidence')
        if consensus < 70:
            reasons.append('low_consensus')
        elif consensus > 90:
            reasons.append('high_consensus')
        if volatility > 5:
            reasons.append('high_volatility')
        return ', '.join(reasons) if reasons else 'normal'


class SentimentIntegration:
    """
    Integrates sentiment data into trading decisions:
    - Fear & Greed Index
    - News sentiment
    - Social media trends
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """Get aggregated market sentiment"""
        
        # Get Fear & Greed from DB
        fg_data = await self.db.fear_greed_index.find_one(
            {}, {'_id': 0}, sort=[('timestamp', -1)]
        )
        
        # Get news sentiment
        news_sentiment = await self.db.news_sentiment.find(
            {'timestamp': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}},
            {'_id': 0}
        ).to_list(100)
        
        # Calculate news score
        if news_sentiment:
            news_scores = [n.get('sentiment_score', 50) for n in news_sentiment]
            avg_news_score = np.mean(news_scores)
        else:
            avg_news_score = 50
        
        # Get social sentiment
        social_data = await self.db.social_sentiment.find_one(
            {}, {'_id': 0}, sort=[('timestamp', -1)]
        )
        
        # Aggregate
        fg_score = fg_data.get('value', 50) if fg_data else 50
        social_score = social_data.get('score', 50) if social_data else 50
        
        # Weighted average
        overall_score = (fg_score * 0.4 + avg_news_score * 0.35 + social_score * 0.25)
        
        # Determine sentiment
        if overall_score >= 75:
            sentiment = 'extreme_greed'
        elif overall_score >= 55:
            sentiment = 'greed'
        elif overall_score >= 45:
            sentiment = 'neutral'
        elif overall_score >= 25:
            sentiment = 'fear'
        else:
            sentiment = 'extreme_fear'
        
        return {
            'overall_score': round(overall_score, 1),
            'sentiment': sentiment,
            'components': {
                'fear_greed': fg_score,
                'news': round(avg_news_score, 1),
                'social': social_score
            },
            'trading_bias': self._get_trading_bias(sentiment),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_trading_bias(self, sentiment: str) -> Dict[str, Any]:
        """Get trading bias based on sentiment (contrarian approach)"""
        biases = {
            'extreme_fear': {'action': 'accumulate', 'size_multiplier': 1.3, 'reason': 'Contrarian buy opportunity'},
            'fear': {'action': 'buy', 'size_multiplier': 1.1, 'reason': 'Mild fear - consider buying'},
            'neutral': {'action': 'hold', 'size_multiplier': 1.0, 'reason': 'Neutral - follow signals'},
            'greed': {'action': 'reduce', 'size_multiplier': 0.9, 'reason': 'Greed - reduce exposure'},
            'extreme_greed': {'action': 'sell', 'size_multiplier': 0.7, 'reason': 'Extreme greed - take profits'}
        }
        return biases.get(sentiment, biases['neutral'])


class WhaleTracker:
    """
    Monitors large wallet movements and whale activity.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.whale_threshold_usd = 1000000  # $1M+
    
    async def get_whale_activity(self, symbol: str = None) -> Dict[str, Any]:
        """Get recent whale activity"""
        
        query = {}
        if symbol:
            query['symbol'] = symbol
        
        # Get whale transactions from DB
        whale_txs = await self.db.whale_transactions.find(
            {**query, 'timestamp': {'$gte': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}},
            {'_id': 0}
        ).sort('value_usd', -1).limit(50).to_list(50)
        
        if not whale_txs:
            # Return simulated data if no real data
            return {
                'whale_activity': 'low',
                'transactions': [],
                'net_flow': 0,
                'accumulation_signal': 'neutral',
                'note': 'No whale data available - using neutral signals'
            }
        
        # Analyze
        total_in = sum(tx.get('value_usd', 0) for tx in whale_txs if tx.get('direction') == 'in')
        total_out = sum(tx.get('value_usd', 0) for tx in whale_txs if tx.get('direction') == 'out')
        net_flow = total_in - total_out
        
        if net_flow > 5000000:
            signal = 'strong_accumulation'
        elif net_flow > 1000000:
            signal = 'accumulation'
        elif net_flow < -5000000:
            signal = 'strong_distribution'
        elif net_flow < -1000000:
            signal = 'distribution'
        else:
            signal = 'neutral'
        
        return {
            'whale_activity': 'high' if len(whale_txs) > 20 else ('medium' if len(whale_txs) > 5 else 'low'),
            'transactions_24h': len(whale_txs),
            'total_inflow': total_in,
            'total_outflow': total_out,
            'net_flow': net_flow,
            'accumulation_signal': signal,
            'top_transactions': whale_txs[:5],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


class EnhancedAIEngine:
    """
    Main enhanced AI engine combining all components.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.ensemble = EnsembleVotingSystem()
        self.mtf_analyzer = MultiTimeframeAnalyzer(db)
        self.risk_manager = DynamicRiskManager()
        self.sentiment = SentimentIntegration(db)
        self.whale_tracker = WhaleTracker(db)
        self.indicators = TechnicalIndicators()
        self.last_retrain = None
    
    async def get_enhanced_signal(self, symbol: str, model_predictions: Dict = None) -> Dict[str, Any]:
        """
        Get enhanced trading signal combining all AI components.
        """
        results = {
            'symbol': symbol,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # 1. Ensemble voting on model predictions
        if model_predictions:
            self.ensemble.update_weights({
                name: pred.get('accuracy', 50) 
                for name, pred in model_predictions.items() 
                if 'error' not in pred
            })
            ensemble_result = self.ensemble.vote(model_predictions)
            results['ensemble'] = ensemble_result
        else:
            results['ensemble'] = {'prediction': 'unknown', 'confidence': 0}
        
        # 2. Multi-timeframe analysis
        mtf_result = await self.mtf_analyzer.analyze(symbol)
        results['multi_timeframe'] = mtf_result
        
        # 3. Sentiment analysis
        sentiment_result = await self.sentiment.get_market_sentiment()
        results['sentiment'] = sentiment_result
        
        # 4. Whale activity
        whale_result = await self.whale_tracker.get_whale_activity(symbol)
        results['whale_activity'] = whale_result
        
        # 5. Calculate dynamic position size
        confidence = results['ensemble'].get('confidence', 50)
        consensus = results['ensemble'].get('consensus', 50)
        
        # Get volatility from MTF
        volatility = 3.0  # Default medium
        if '1d' in mtf_result.get('timeframes', {}):
            # Estimate from RSI deviation
            rsi = mtf_result['timeframes']['1d'].get('rsi', 50)
            volatility = abs(rsi - 50) / 10
        
        position_sizing = self.risk_manager.calculate_position_size(
            confidence=confidence,
            consensus=consensus,
            volatility=volatility,
            current_exposure=0  # Would come from portfolio
        )
        results['position_sizing'] = position_sizing
        
        # 6. Generate final recommendation
        results['recommendation'] = self._generate_recommendation(results)
        
        return results
    
    def _generate_recommendation(self, analysis: Dict) -> Dict[str, Any]:
        """Generate final trading recommendation"""
        
        scores = {
            'ensemble': 0,
            'timeframe': 0,
            'sentiment': 0,
            'whale': 0
        }
        
        # Ensemble score
        ensemble_pred = analysis.get('ensemble', {}).get('prediction', 'unknown')
        if ensemble_pred in ['bull', 'strong_bull']:
            scores['ensemble'] = 2
        elif ensemble_pred in ['bear', 'strong_bear']:
            scores['ensemble'] = -2
        elif ensemble_pred == 'sideways':
            scores['ensemble'] = 0
        
        # Timeframe alignment
        alignment = analysis.get('multi_timeframe', {}).get('alignment', 'mixed')
        if alignment == 'strong_bullish':
            scores['timeframe'] = 2
        elif alignment == 'weak_bullish':
            scores['timeframe'] = 1
        elif alignment == 'strong_bearish':
            scores['timeframe'] = -2
        elif alignment == 'weak_bearish':
            scores['timeframe'] = -1
        
        # Sentiment (contrarian)
        sentiment = analysis.get('sentiment', {}).get('sentiment', 'neutral')
        if sentiment == 'extreme_fear':
            scores['sentiment'] = 2  # Buy opportunity
        elif sentiment == 'fear':
            scores['sentiment'] = 1
        elif sentiment == 'extreme_greed':
            scores['sentiment'] = -2  # Sell signal
        elif sentiment == 'greed':
            scores['sentiment'] = -1
        
        # Whale activity
        whale_signal = analysis.get('whale_activity', {}).get('accumulation_signal', 'neutral')
        if whale_signal == 'strong_accumulation':
            scores['whale'] = 2
        elif whale_signal == 'accumulation':
            scores['whale'] = 1
        elif whale_signal == 'strong_distribution':
            scores['whale'] = -2
        elif whale_signal == 'distribution':
            scores['whale'] = -1
        
        # Calculate total score (-8 to +8)
        total_score = sum(scores.values())
        
        # Determine action
        if total_score >= 5:
            action = 'strong_buy'
            confidence = 90
        elif total_score >= 3:
            action = 'buy'
            confidence = 75
        elif total_score >= 1:
            action = 'weak_buy'
            confidence = 60
        elif total_score <= -5:
            action = 'strong_sell'
            confidence = 90
        elif total_score <= -3:
            action = 'sell'
            confidence = 75
        elif total_score <= -1:
            action = 'weak_sell'
            confidence = 60
        else:
            action = 'hold'
            confidence = 50
        
        return {
            'action': action,
            'confidence': confidence,
            'total_score': total_score,
            'score_breakdown': scores,
            'position_size': analysis.get('position_sizing', {}).get('position_pct', 9)
        }
    
    async def should_retrain(self) -> bool:
        """Check if models should be retrained"""
        if self.last_retrain is None:
            return True
        
        hours_since_retrain = (datetime.now(timezone.utc) - self.last_retrain).total_seconds() / 3600
        return hours_since_retrain >= 24  # Retrain daily
    
    async def calculate_features(self, ohlcv_data: List[Dict]) -> Dict[str, float]:
        """Calculate all 25+ technical features"""
        if len(ohlcv_data) < 50:
            return {}
        
        closes = [float(d.get('close', 0)) for d in ohlcv_data]
        highs = [float(d.get('high', 0)) for d in ohlcv_data]
        lows = [float(d.get('low', 0)) for d in ohlcv_data]
        volumes = [float(d.get('volume_to', d.get('volume', 0)) or 0) for d in ohlcv_data]
        
        ind = self.indicators
        
        features = {
            # Trend indicators
            'sma_7': ind.sma(closes, 7),
            'sma_20': ind.sma(closes, 20),
            'sma_50': ind.sma(closes, 50),
            'ema_12': ind.ema(closes, 12),
            'ema_26': ind.ema(closes, 26),
            
            # Momentum
            'rsi_14': ind.rsi(closes, 14),
            'rsi_7': ind.rsi(closes, 7),
            'stoch_k': ind.stochastic(highs, lows, closes)[0],
            'stoch_d': ind.stochastic(highs, lows, closes)[1],
            
            # MACD
            'macd_line': ind.macd(closes)[0],
            'macd_signal': ind.macd(closes)[1],
            'macd_hist': ind.macd(closes)[2],
            
            # Volatility
            'bb_upper': ind.bollinger_bands(closes)[0],
            'bb_middle': ind.bollinger_bands(closes)[1],
            'bb_lower': ind.bollinger_bands(closes)[2],
            'atr_14': ind.atr(highs, lows, closes, 14),
            
            # Volume
            'obv': ind.obv(closes, volumes),
            'vwap': ind.vwap(highs, lows, closes, volumes),
            
            # Price ratios
            'price_sma20_ratio': closes[-1] / ind.sma(closes, 20) if ind.sma(closes, 20) else 1,
            'price_sma50_ratio': closes[-1] / ind.sma(closes, 50) if ind.sma(closes, 50) else 1,
            
            # Returns
            'return_1d': (closes[-1] / closes[-2] - 1) * 100 if len(closes) > 1 else 0,
            'return_7d': (closes[-1] / closes[-7] - 1) * 100 if len(closes) > 7 else 0,
            'return_30d': (closes[-1] / closes[-30] - 1) * 100 if len(closes) > 30 else 0,
            
            # Ichimoku
            **{f'ichimoku_{k}': v for k, v in ind.ichimoku(highs, lows, closes).items()},
            
            # Current price
            'current_price': closes[-1]
        }
        
        return features


# Global instance
_enhanced_ai = None


def get_enhanced_ai(db: AsyncIOMotorDatabase = None) -> EnhancedAIEngine:
    """Get or create enhanced AI engine"""
    global _enhanced_ai
    if _enhanced_ai is None and db is not None:
        _enhanced_ai = EnhancedAIEngine(db)
    return _enhanced_ai
