import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime
import talib as ta
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
from dotenv import load_dotenv

load_dotenv()

class StrategyEngine:
    def __init__(self):
        self.llm_api_key = os.getenv('EMERGENT_LLM_KEY')
    
    def calculate_technical_indicators(self, prices: List[List]) -> Dict[str, Any]:
        """Calculate technical indicators from price data"""
        if not prices or len(prices) < 30:
            return {}
        
        # CoinGecko returns [[timestamp, price], ...] format
        # Convert to DataFrame with just timestamp and close price
        if len(prices[0]) == 2:
            # Data is [timestamp, price] format from CoinGecko
            df = pd.DataFrame(prices, columns=['timestamp', 'close'])
            df['close'] = df['close'].astype(float)
            # Create synthetic OHLV from close price (since we only have close)
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 1000000  # Placeholder volume
        else:
            # Full OHLCV data
            df = pd.DataFrame(prices, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        
        close_prices = df['close'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        
        # Calculate indicators
        indicators = {}
        
        try:
            # RSI (Relative Strength Index)
            indicators['rsi'] = float(ta.RSI(close_prices, timeperiod=14)[-1])
            
            # MACD
            macd, signal, hist = ta.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['macd'] = float(macd[-1]) if not np.isnan(macd[-1]) else 0
            indicators['macd_signal'] = float(signal[-1]) if not np.isnan(signal[-1]) else 0
            indicators['macd_histogram'] = float(hist[-1]) if not np.isnan(hist[-1]) else 0
            
            # Bollinger Bands
            upper, middle, lower = ta.BBANDS(close_prices, timeperiod=20)
            indicators['bb_upper'] = float(upper[-1]) if not np.isnan(upper[-1]) else 0
            indicators['bb_middle'] = float(middle[-1]) if not np.isnan(middle[-1]) else 0
            indicators['bb_lower'] = float(lower[-1]) if not np.isnan(lower[-1]) else 0
            
            # Moving Averages
            indicators['sma_20'] = float(ta.SMA(close_prices, timeperiod=20)[-1])
            indicators['sma_50'] = float(ta.SMA(close_prices, timeperiod=50)[-1]) if len(close_prices) >= 50 else 0
            indicators['ema_12'] = float(ta.EMA(close_prices, timeperiod=12)[-1])
            indicators['ema_26'] = float(ta.EMA(close_prices, timeperiod=26)[-1])
            
            # ADX (Average Directional Index)
            adx = ta.ADX(high_prices, low_prices, close_prices, timeperiod=14)
            indicators['adx'] = float(adx[-1]) if not np.isnan(adx[-1]) else 0
            
            # Current price
            indicators['current_price'] = float(close_prices[-1])
            
        except Exception as e:
            print(f"Error calculating indicators: {str(e)}")
        
        return indicators
    
    def generate_rule_based_signals(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals based on technical indicators"""
        if not indicators:
            return {"signal": "HOLD", "confidence": 0, "reasons": []}
        
        signals = []
        reasons = []
        
        # RSI Analysis
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            signals.append('BUY')
            reasons.append(f"RSI oversold at {rsi:.2f}")
        elif rsi > 70:
            signals.append('SELL')
            reasons.append(f"RSI overbought at {rsi:.2f}")
        
        # MACD Analysis
        if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
            signals.append('BUY')
            reasons.append("MACD bullish crossover")
        elif indicators.get('macd', 0) < indicators.get('macd_signal', 0):
            signals.append('SELL')
            reasons.append("MACD bearish crossover")
        
        # Moving Average Analysis
        current_price = indicators.get('current_price', 0)
        sma_20 = indicators.get('sma_20', 0)
        sma_50 = indicators.get('sma_50', 0)
        
        if current_price > sma_20 and sma_20 > sma_50:
            signals.append('BUY')
            reasons.append("Price above moving averages (bullish trend)")
        elif current_price < sma_20 and sma_20 < sma_50:
            signals.append('SELL')
            reasons.append("Price below moving averages (bearish trend)")
        
        # Bollinger Bands
        bb_lower = indicators.get('bb_lower', 0)
        bb_upper = indicators.get('bb_upper', 0)
        
        if current_price < bb_lower:
            signals.append('BUY')
            reasons.append("Price below lower Bollinger Band")
        elif current_price > bb_upper:
            signals.append('SELL')
            reasons.append("Price above upper Bollinger Band")
        
        # Determine final signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count:
            signal = 'BUY'
            confidence = (buy_count / len(signals)) * 100 if signals else 0
        elif sell_count > buy_count:
            signal = 'SELL'
            confidence = (sell_count / len(signals)) * 100 if signals else 0
        else:
            signal = 'HOLD'
            confidence = 50
        
        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "reasons": reasons,
            "indicators": indicators
        }
    
    async def generate_ai_strategy(
        self,
        coin_id: str,
        technical_analysis: Dict[str, Any],
        market_data: Dict[str, Any],
        news_sentiment: Dict[str, Any] = None,
        learning_data: Dict[str, Any] = None,
        historical_patterns: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered strategy recommendation using LLM with news and learning integration"""
        try:
            chat = LlmChat(
                api_key=self.llm_api_key,
                session_id=f"strategy_{coin_id}_{datetime.now().timestamp()}",
                system_message="You are an expert cryptocurrency trading analyst with machine learning capabilities and access to comprehensive market intelligence. You learn from past predictions, analyze news sentiment, and use 16+ years of historical patterns. Provide concise, actionable trading strategies based on multi-source analysis."
            ).with_model("openai", "gpt-5.2")
            
            # Include learning insights in the prompt
            learning_context = ""
            if learning_data and learning_data.get('has_learning_data'):
                metrics = learning_data.get('overall_metrics', {})
                recent = learning_data.get('recent_performance', {})
                learning_context = f"""

LEARNING INSIGHTS (AI has learned from {metrics.get('total_predictions', 0)} past predictions):
- Historical Accuracy: {metrics.get('accuracy', 0):.1f}%
- Learned Confidence Adjustment: {metrics.get('learned_confidence', 0):.1f}%
- Recent Performance Trend: {recent.get('trend', 'unknown')}
- Learning Status: {learning_data.get('learning_status', 'initializing')}
- Recent Accuracy: {recent.get('accuracy', 0):.1f}%

The AI has been learning and improving. Use this historical performance data to refine your recommendation.
"""
            
            # Include news sentiment analysis
            news_context = ""
            if news_sentiment:
                sentiment = news_sentiment.get('sentiment', 'neutral')
                confidence = news_sentiment.get('confidence', 0)
                headlines = news_sentiment.get('recent_headlines', [])
                news_context = f"""

NEWS SENTIMENT ANALYSIS:
- Overall Sentiment: {sentiment.upper()} (Confidence: {confidence:.1f}%)
- Recent Headlines:
{chr(10).join([f"  • {h}" for h in headlines[:5]])}
- AI Analysis: {news_sentiment.get('ai_analysis', 'No analysis available')[:200]}...

News sentiment provides market psychology context. Factor this into risk assessment.
"""
            
            # Include historical patterns
            historical_context = ""
            if historical_patterns:
                success_rate = sum(1 for p in historical_patterns if p.get('success')) / len(historical_patterns) * 100
                avg_return = sum(p.get('return', 0) for p in historical_patterns) / len(historical_patterns) * 100
                historical_context = f"""

HISTORICAL PATTERN ANALYSIS (Trained on data from 2009-2025):
- Found {len(historical_patterns)} similar historical patterns
- Historical Success Rate: {success_rate:.1f}%
- Average Return: {avg_return:+.2f}%
- Most Similar Pattern: {historical_patterns[0].get('pattern_type', 'N/A')} (similarity: {historical_patterns[0].get('similarity_score', 0)*100:.1f}%)

These patterns show what happened in similar market conditions over 16+ years of crypto history.
"""
            
            prompt = f"""
Analyze the following data for {coin_id.upper()} and provide a trading strategy recommendation:

Technical Analysis:
- Signal: {technical_analysis.get('signal')}
- Confidence: {technical_analysis.get('confidence')}%
- Key Reasons: {', '.join(technical_analysis.get('reasons', []))}
- RSI: {technical_analysis.get('indicators', {}).get('rsi', 'N/A')}
- MACD: {technical_analysis.get('indicators', {}).get('macd', 'N/A')}
- Current Price: ${technical_analysis.get('indicators', {}).get('current_price', 'N/A')}

Market Data:
- 24h Change: {market_data.get('price_change_24h', 'N/A')}%
- 24h Volume: ${market_data.get('volume_24h', 'N/A')}
- Market Cap: ${market_data.get('market_cap', 'N/A')}
{learning_context}
{news_context}
{historical_context}
Provide:
1. Recommended Action (BUY/SELL/HOLD)
2. Entry Price Range
3. Stop Loss Level
4. Take Profit Targets (3 levels)
5. Risk Assessment (Low/Medium/High)
6. Key Factors (3-5 bullet points explaining your recommendation, including news and historical insights)
7. Time Horizon (Short/Medium/Long term)
8. Learning & News-Adjusted Confidence (considering historical accuracy, news sentiment, and 16 years of patterns)

Keep response concise and structured.
"""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Adjust confidence based on learning and news
            final_confidence = technical_analysis.get('confidence')
            if learning_data and learning_data.get('has_learning_data'):
                learned_conf = learning_data.get('overall_metrics', {}).get('learned_confidence', final_confidence)
                final_confidence = (final_confidence * 0.5) + (learned_conf * 0.5)  # Blend original and learned
            
            # Adjust for news sentiment
            if news_sentiment:
                sentiment = news_sentiment.get('sentiment')
                if sentiment == 'positive' and technical_analysis.get('signal') == 'BUY':
                    final_confidence *= 1.1  # Boost confidence
                elif sentiment == 'negative' and technical_analysis.get('signal') == 'SELL':
                    final_confidence *= 1.1
                elif sentiment == 'positive' and technical_analysis.get('signal') == 'SELL':
                    final_confidence *= 0.9  # Reduce confidence (conflicting signals)
                elif sentiment == 'negative' and technical_analysis.get('signal') == 'BUY':
                    final_confidence *= 0.9
            
            final_confidence = min(100, max(0, final_confidence))  # Clamp to 0-100
            
            return {
                "strategy_id": f"strat_{coin_id}_{int(datetime.now().timestamp())}",
                "coin_id": coin_id,
                "ai_recommendation": response,
                "technical_signal": technical_analysis.get('signal'),
                "confidence_score": final_confidence,
                "learning_enhanced": learning_data is not None and learning_data.get('has_learning_data', False),
                "news_integrated": news_sentiment is not None,
                "historical_patterns_used": len(historical_patterns) if historical_patterns else 0,
                "learning_data": learning_data,
                "news_sentiment": news_sentiment,
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
        except Exception as e:
            return {
                "error": str(e),
                "fallback_recommendation": technical_analysis.get('signal'),
                "confidence_score": technical_analysis.get('confidence')
            }
    
    async def generate_weekly_strategies(
        self,
        coin_pairs: List[str],
        historical_data: Dict[str, Any],
        learning_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate weekly strategy recommendations for multiple coins with learning integration"""
        strategies = []
        
        for coin in coin_pairs:
            try:
                # Get historical prices for the coin
                coin_data = historical_data.get(coin, {}).get('prices', [])
                
                if coin_data:
                    # Calculate technical indicators
                    indicators = self.calculate_technical_indicators(coin_data)
                    
                    # Generate rule-based signals
                    technical_analysis = self.generate_rule_based_signals(indicators)
                    
                    # Get market data
                    market_data = historical_data.get(coin, {})
                    
                    # Generate AI strategy with learning data
                    ai_strategy = await self.generate_ai_strategy(
                        coin,
                        technical_analysis,
                        market_data,
                        learning_data=learning_data
                    )
                    
                    strategies.append(ai_strategy)
            except Exception as e:
                print(f"Error generating strategy for {coin}: {str(e)}")
                continue
        
        # Sort strategies by confidence score
        strategies.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        return strategies