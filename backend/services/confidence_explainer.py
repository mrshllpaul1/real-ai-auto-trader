"""
ML Model Confidence Explanation Service
========================================
Provides human-readable explanations for why AI models have certain confidence levels.
Implements SHAP-like feature importance and natural language explanations.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class FeatureContribution:
    """Represents a single feature's contribution to the prediction"""
    name: str
    value: float
    contribution: float  # -1 to 1 scale
    direction: str  # "bullish", "bearish", "neutral"
    explanation: str
    importance: float  # 0 to 1


class ConfidenceExplainer:
    """
    Explains AI model confidence levels with feature attributions and natural language.
    """
    
    # Feature importance weights (learned from model analysis)
    FEATURE_WEIGHTS = {
        "technical": {
            "rsi": 0.15,
            "macd": 0.12,
            "bollinger": 0.10,
            "sma_crossover": 0.08,
            "volume_trend": 0.10,
            "price_momentum": 0.12,
            "volatility": 0.08,
        },
        "sentiment": {
            "news_score": 0.18,
            "social_volume": 0.12,
            "fear_greed": 0.15,
            "whale_activity": 0.10,
        },
        "on_chain": {
            "exchange_flow": 0.12,
            "active_addresses": 0.10,
            "transaction_volume": 0.08,
            "holder_distribution": 0.10,
        },
        "market_structure": {
            "order_book_imbalance": 0.15,
            "bid_ask_spread": 0.08,
            "liquidity_depth": 0.10,
            "cross_asset_correlation": 0.07,
        }
    }
    
    # Thresholds for interpretation
    THRESHOLDS = {
        "rsi": {"oversold": 30, "overbought": 70},
        "fear_greed": {"extreme_fear": 25, "extreme_greed": 75},
        "volume_change": {"significant": 1.5, "extreme": 3.0},
        "volatility": {"low": 0.02, "high": 0.05},
    }
    
    def __init__(self, db=None):
        self.db = db
        logger.info("🔍 Confidence Explainer Service initialized")
    
    def explain_confidence(
        self,
        symbol: str,
        confidence: float,
        signal: str,
        features: Dict[str, Any],
        model_outputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive explanation for model confidence.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC")
            confidence: Model confidence score (0-1)
            signal: The predicted signal ("buy", "sell", "hold")
            features: Input features used by the model
            model_outputs: Optional detailed model outputs
            
        Returns:
            Dict with explanation, feature contributions, and recommendations
        """
        # Calculate feature contributions
        contributions = self._calculate_contributions(features, signal)
        
        # Generate natural language explanation
        explanation = self._generate_explanation(
            symbol, confidence, signal, contributions
        )
        
        # Identify key drivers
        key_drivers = self._identify_key_drivers(contributions)
        
        # Generate confidence breakdown
        breakdown = self._generate_confidence_breakdown(
            confidence, signal, contributions
        )
        
        # Calculate agreement score (how many indicators agree)
        agreement = self._calculate_agreement(contributions, signal)
        
        # Generate actionable insights
        insights = self._generate_insights(
            symbol, confidence, signal, contributions, agreement
        )
        
        # Risk assessment
        risk_factors = self._assess_risk_factors(features, contributions)
        
        return {
            "symbol": symbol,
            "confidence": round(confidence, 3),
            "signal": signal,
            "explanation": explanation,
            "summary": self._generate_summary(confidence, signal, key_drivers),
            "key_drivers": key_drivers,
            "breakdown": breakdown,
            "contributions": [
                {
                    "category": cat,
                    "features": [
                        {
                            "name": c.name,
                            "value": round(c.value, 4) if isinstance(c.value, float) else c.value,
                            "contribution": round(c.contribution, 3),
                            "direction": c.direction,
                            "explanation": c.explanation,
                            "importance": round(c.importance, 3)
                        }
                        for c in contribs
                    ]
                }
                for cat, contribs in contributions.items()
            ],
            "agreement_score": round(agreement, 2),
            "insights": insights,
            "risk_factors": risk_factors,
            "confidence_level": self._classify_confidence(confidence),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_contributions(
        self,
        features: Dict[str, Any],
        signal: str
    ) -> Dict[str, List[FeatureContribution]]:
        """Calculate contribution of each feature to the prediction"""
        contributions = {}
        
        # Technical indicators
        technical = []
        
        # RSI
        rsi = features.get("rsi", 50)
        rsi_contrib = self._rsi_contribution(rsi, signal)
        technical.append(rsi_contrib)
        
        # MACD
        macd = features.get("macd", {})
        macd_contrib = self._macd_contribution(macd, signal)
        technical.append(macd_contrib)
        
        # Bollinger Bands
        bb = features.get("bollinger", {})
        bb_contrib = self._bollinger_contribution(bb, features.get("price", 0), signal)
        technical.append(bb_contrib)
        
        # Volume trend
        vol = features.get("volume_change", 0)
        vol_contrib = self._volume_contribution(vol, signal)
        technical.append(vol_contrib)
        
        # Price momentum
        momentum = features.get("momentum", 0)
        mom_contrib = self._momentum_contribution(momentum, signal)
        technical.append(mom_contrib)
        
        contributions["technical"] = technical
        
        # Sentiment indicators
        sentiment = []
        
        # News sentiment
        news = features.get("news_sentiment", 0.5)
        news_contrib = self._news_contribution(news, signal)
        sentiment.append(news_contrib)
        
        # Fear & Greed
        fg = features.get("fear_greed", 50)
        fg_contrib = self._fear_greed_contribution(fg, signal)
        sentiment.append(fg_contrib)
        
        # Social volume
        social = features.get("social_volume_change", 0)
        social_contrib = self._social_contribution(social, signal)
        sentiment.append(social_contrib)
        
        contributions["sentiment"] = sentiment
        
        # On-chain metrics
        onchain = []
        
        # Exchange flow
        exchange_flow = features.get("exchange_flow", 0)
        flow_contrib = self._exchange_flow_contribution(exchange_flow, signal)
        onchain.append(flow_contrib)
        
        # Active addresses
        addresses = features.get("active_addresses_change", 0)
        addr_contrib = self._address_contribution(addresses, signal)
        onchain.append(addr_contrib)
        
        contributions["on_chain"] = onchain
        
        # Market structure
        market = []
        
        # Order book imbalance
        ob_imbalance = features.get("order_book_imbalance", 0)
        ob_contrib = self._order_book_contribution(ob_imbalance, signal)
        market.append(ob_contrib)
        
        # Spread
        spread = features.get("spread", 0)
        spread_contrib = self._spread_contribution(spread, signal)
        market.append(spread_contrib)
        
        contributions["market_structure"] = market
        
        return contributions
    
    def _rsi_contribution(self, rsi: float, signal: str) -> FeatureContribution:
        """Calculate RSI contribution to prediction"""
        oversold = self.THRESHOLDS["rsi"]["oversold"]
        overbought = self.THRESHOLDS["rsi"]["overbought"]
        
        if rsi <= oversold:
            direction = "bullish"
            contribution = (oversold - rsi) / oversold * 0.8
            explanation = f"RSI at {rsi:.0f} indicates oversold conditions, suggesting potential price reversal upward"
        elif rsi >= overbought:
            direction = "bearish"
            contribution = -(rsi - overbought) / (100 - overbought) * 0.8
            explanation = f"RSI at {rsi:.0f} indicates overbought conditions, suggesting potential price reversal downward"
        else:
            direction = "neutral"
            # Slight bias towards middle
            contribution = (50 - rsi) / 100 * 0.2
            explanation = f"RSI at {rsi:.0f} is in neutral territory, neither overbought nor oversold"
        
        # Adjust contribution based on signal alignment
        if (direction == "bullish" and signal == "sell") or (direction == "bearish" and signal == "buy"):
            contribution *= -0.5  # Conflicting signal reduces confidence
        
        return FeatureContribution(
            name="RSI",
            value=rsi,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["technical"]["rsi"]
        )
    
    def _macd_contribution(self, macd: Dict, signal: str) -> FeatureContribution:
        """Calculate MACD contribution"""
        macd_line = macd.get("macd", 0)
        signal_line = macd.get("signal", 0)
        histogram = macd.get("histogram", macd_line - signal_line)
        
        if histogram > 0:
            direction = "bullish"
            contribution = min(histogram / 100, 0.5)  # Normalize
            explanation = f"MACD histogram positive ({histogram:.2f}), indicating bullish momentum"
        elif histogram < 0:
            direction = "bearish"
            contribution = max(histogram / 100, -0.5)
            explanation = f"MACD histogram negative ({histogram:.2f}), indicating bearish momentum"
        else:
            direction = "neutral"
            contribution = 0
            explanation = "MACD at crossover point, momentum indeterminate"
        
        return FeatureContribution(
            name="MACD",
            value=histogram,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["technical"]["macd"]
        )
    
    def _bollinger_contribution(self, bb: Dict, price: float, signal: str) -> FeatureContribution:
        """Calculate Bollinger Bands contribution"""
        upper = bb.get("upper", price * 1.02)
        lower = bb.get("lower", price * 0.98)
        middle = bb.get("middle", price)
        
        if price <= lower:
            direction = "bullish"
            pct_below = (lower - price) / lower * 100
            contribution = min(pct_below / 5, 0.6)
            explanation = f"Price below lower Bollinger Band ({pct_below:.1f}% below), potential bounce expected"
        elif price >= upper:
            direction = "bearish"
            pct_above = (price - upper) / upper * 100
            contribution = -min(pct_above / 5, 0.6)
            explanation = f"Price above upper Bollinger Band ({pct_above:.1f}% above), potential pullback expected"
        else:
            # Position within bands
            band_width = upper - lower
            position = (price - lower) / band_width if band_width > 0 else 0.5
            direction = "bullish" if position < 0.4 else ("bearish" if position > 0.6 else "neutral")
            contribution = (0.5 - position) * 0.3
            explanation = f"Price within Bollinger Bands at {position*100:.0f}% position"
        
        return FeatureContribution(
            name="Bollinger Bands",
            value=price,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["technical"]["bollinger"]
        )
    
    def _volume_contribution(self, volume_change: float, signal: str) -> FeatureContribution:
        """Calculate volume trend contribution"""
        significant = self.THRESHOLDS["volume_change"]["significant"]
        extreme = self.THRESHOLDS["volume_change"]["extreme"]
        
        if volume_change >= extreme:
            direction = "bullish" if signal == "buy" else "bearish"
            contribution = 0.5 if signal in ["buy", "sell"] else 0.2
            explanation = f"Volume surge ({volume_change:.1f}x normal), confirming strong market interest"
        elif volume_change >= significant:
            direction = "neutral"
            contribution = 0.2
            explanation = f"Above-average volume ({volume_change:.1f}x), indicating increased activity"
        elif volume_change < 0.5:
            direction = "neutral"
            contribution = -0.1
            explanation = f"Low volume ({volume_change:.1f}x), suggesting weak conviction in price moves"
        else:
            direction = "neutral"
            contribution = 0
            explanation = f"Normal volume levels ({volume_change:.1f}x)"
        
        return FeatureContribution(
            name="Volume Trend",
            value=volume_change,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["technical"]["volume_trend"]
        )
    
    def _momentum_contribution(self, momentum: float, signal: str) -> FeatureContribution:
        """Calculate price momentum contribution"""
        if momentum > 0.05:
            direction = "bullish"
            contribution = min(momentum * 5, 0.6)
            explanation = f"Strong positive momentum ({momentum*100:.1f}%), price trending upward"
        elif momentum < -0.05:
            direction = "bearish"
            contribution = max(momentum * 5, -0.6)
            explanation = f"Strong negative momentum ({momentum*100:.1f}%), price trending downward"
        else:
            direction = "neutral"
            contribution = momentum * 2
            explanation = f"Weak momentum ({momentum*100:.1f}%), no clear directional bias"
        
        return FeatureContribution(
            name="Price Momentum",
            value=momentum,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["technical"]["price_momentum"]
        )
    
    def _news_contribution(self, sentiment: float, signal: str) -> FeatureContribution:
        """Calculate news sentiment contribution"""
        if sentiment >= 0.7:
            direction = "bullish"
            contribution = (sentiment - 0.5) * 1.2
            explanation = f"Positive news sentiment ({sentiment:.0%}), market narrative is bullish"
        elif sentiment <= 0.3:
            direction = "bearish"
            contribution = (sentiment - 0.5) * 1.2
            explanation = f"Negative news sentiment ({sentiment:.0%}), market narrative is bearish"
        else:
            direction = "neutral"
            contribution = (sentiment - 0.5) * 0.5
            explanation = f"Mixed news sentiment ({sentiment:.0%}), no strong narrative"
        
        return FeatureContribution(
            name="News Sentiment",
            value=sentiment,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["sentiment"]["news_score"]
        )
    
    def _fear_greed_contribution(self, index: float, signal: str) -> FeatureContribution:
        """Calculate Fear & Greed Index contribution"""
        extreme_fear = self.THRESHOLDS["fear_greed"]["extreme_fear"]
        extreme_greed = self.THRESHOLDS["fear_greed"]["extreme_greed"]
        
        if index <= extreme_fear:
            direction = "bullish"  # Contrarian indicator
            contribution = (extreme_fear - index) / extreme_fear * 0.6
            explanation = f"Extreme fear ({index:.0f}), historically a buying opportunity"
        elif index >= extreme_greed:
            direction = "bearish"  # Contrarian indicator
            contribution = -(index - extreme_greed) / (100 - extreme_greed) * 0.6
            explanation = f"Extreme greed ({index:.0f}), historically precedes corrections"
        else:
            direction = "neutral"
            contribution = (50 - index) / 100 * 0.2
            explanation = f"Fear & Greed at {index:.0f}, market sentiment balanced"
        
        return FeatureContribution(
            name="Fear & Greed Index",
            value=index,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["sentiment"]["fear_greed"]
        )
    
    def _social_contribution(self, volume_change: float, signal: str) -> FeatureContribution:
        """Calculate social media volume contribution"""
        if volume_change > 2.0:
            direction = "bullish" if signal == "buy" else ("bearish" if signal == "sell" else "neutral")
            contribution = min(volume_change / 5, 0.4)
            explanation = f"High social media activity ({volume_change:.1f}x), increased market attention"
        elif volume_change < 0.5:
            direction = "neutral"
            contribution = -0.1
            explanation = f"Low social activity ({volume_change:.1f}x), reduced market interest"
        else:
            direction = "neutral"
            contribution = 0.05
            explanation = f"Normal social volume ({volume_change:.1f}x)"
        
        return FeatureContribution(
            name="Social Volume",
            value=volume_change,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["sentiment"]["social_volume"]
        )
    
    def _exchange_flow_contribution(self, flow: float, signal: str) -> FeatureContribution:
        """Calculate exchange flow contribution"""
        if flow < -0.05:
            direction = "bullish"
            contribution = abs(flow) * 3
            explanation = f"Net outflow from exchanges ({flow*100:.1f}%), reducing sell pressure"
        elif flow > 0.05:
            direction = "bearish"
            contribution = -flow * 3
            explanation = f"Net inflow to exchanges ({flow*100:.1f}%), potential sell pressure"
        else:
            direction = "neutral"
            contribution = 0
            explanation = f"Balanced exchange flows ({flow*100:.1f}%)"
        
        return FeatureContribution(
            name="Exchange Flow",
            value=flow,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["on_chain"]["exchange_flow"]
        )
    
    def _address_contribution(self, change: float, signal: str) -> FeatureContribution:
        """Calculate active addresses contribution"""
        if change > 0.1:
            direction = "bullish"
            contribution = min(change * 2, 0.4)
            explanation = f"Growing network activity ({change*100:.1f}% more addresses), healthy adoption"
        elif change < -0.1:
            direction = "bearish"
            contribution = max(change * 2, -0.4)
            explanation = f"Declining network activity ({change*100:.1f}% fewer addresses)"
        else:
            direction = "neutral"
            contribution = change
            explanation = f"Stable network activity ({change*100:.1f}% change)"
        
        return FeatureContribution(
            name="Active Addresses",
            value=change,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["on_chain"]["active_addresses"]
        )
    
    def _order_book_contribution(self, imbalance: float, signal: str) -> FeatureContribution:
        """Calculate order book imbalance contribution"""
        if imbalance > 0.2:
            direction = "bullish"
            contribution = min(imbalance, 0.5)
            explanation = f"Buy pressure dominant ({imbalance:.0%} bid-heavy), strong support below"
        elif imbalance < -0.2:
            direction = "bearish"
            contribution = max(imbalance, -0.5)
            explanation = f"Sell pressure dominant ({abs(imbalance):.0%} ask-heavy), resistance above"
        else:
            direction = "neutral"
            contribution = imbalance * 0.5
            explanation = f"Balanced order book ({imbalance:.0%} imbalance)"
        
        return FeatureContribution(
            name="Order Book",
            value=imbalance,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["market_structure"]["order_book_imbalance"]
        )
    
    def _spread_contribution(self, spread: float, signal: str) -> FeatureContribution:
        """Calculate spread contribution"""
        if spread > 0.005:
            direction = "neutral"
            contribution = -0.2
            explanation = f"Wide spread ({spread*100:.2f}%), low liquidity may increase slippage"
        elif spread < 0.001:
            direction = "neutral"
            contribution = 0.1
            explanation = f"Tight spread ({spread*100:.3f}%), high liquidity for efficient execution"
        else:
            direction = "neutral"
            contribution = 0
            explanation = f"Normal spread ({spread*100:.3f}%)"
        
        return FeatureContribution(
            name="Bid-Ask Spread",
            value=spread,
            contribution=contribution,
            direction=direction,
            explanation=explanation,
            importance=self.FEATURE_WEIGHTS["market_structure"]["bid_ask_spread"]
        )
    
    def _identify_key_drivers(
        self,
        contributions: Dict[str, List[FeatureContribution]]
    ) -> List[Dict[str, Any]]:
        """Identify the top 3-5 most influential factors"""
        all_contributions = []
        
        for category, features in contributions.items():
            for f in features:
                all_contributions.append({
                    "category": category,
                    "feature": f.name,
                    "contribution": abs(f.contribution) * f.importance,
                    "direction": f.direction,
                    "explanation": f.explanation,
                    "raw_contribution": f.contribution
                })
        
        # Sort by absolute contribution * importance
        all_contributions.sort(key=lambda x: x["contribution"], reverse=True)
        
        # Return top 5
        return all_contributions[:5]
    
    def _generate_explanation(
        self,
        symbol: str,
        confidence: float,
        signal: str,
        contributions: Dict[str, List[FeatureContribution]]
    ) -> str:
        """Generate a human-readable explanation"""
        key_drivers = self._identify_key_drivers(contributions)
        
        signal_word = {
            "buy": "bullish",
            "strong_buy": "strongly bullish",
            "sell": "bearish",
            "strong_sell": "strongly bearish",
            "hold": "neutral"
        }.get(signal, "neutral")
        
        confidence_word = "very high" if confidence > 0.8 else (
            "high" if confidence > 0.65 else (
                "moderate" if confidence > 0.5 else "low"
            )
        )
        
        # Build explanation
        explanation = f"The AI model is {signal_word} on {symbol} with {confidence_word} confidence ({confidence:.0%}). "
        
        if key_drivers:
            explanation += "Key factors driving this prediction: "
            driver_explanations = []
            for i, driver in enumerate(key_drivers[:3]):
                driver_explanations.append(driver["explanation"])
            explanation += "; ".join(driver_explanations) + "."
        
        # Add confidence context
        if confidence < 0.5:
            explanation += " Note: Low confidence suggests conflicting signals - exercise caution."
        elif confidence > 0.8:
            explanation += " Strong alignment across multiple indicators supports this view."
        
        return explanation
    
    def _generate_summary(
        self,
        confidence: float,
        signal: str,
        key_drivers: List[Dict]
    ) -> str:
        """Generate a one-line summary"""
        if not key_drivers:
            return f"{signal.upper()} signal with {confidence:.0%} confidence"
        
        top_driver = key_drivers[0]["feature"]
        return f"{signal.upper()} ({confidence:.0%}) - Primary driver: {top_driver}"
    
    def _generate_confidence_breakdown(
        self,
        confidence: float,
        signal: str,
        contributions: Dict[str, List[FeatureContribution]]
    ) -> Dict[str, Any]:
        """Break down confidence by category"""
        breakdown = {}
        
        for category, features in contributions.items():
            total_contrib = sum(f.contribution * f.importance for f in features)
            avg_importance = sum(f.importance for f in features) / len(features) if features else 0
            
            bullish_count = sum(1 for f in features if f.direction == "bullish")
            bearish_count = sum(1 for f in features if f.direction == "bearish")
            neutral_count = sum(1 for f in features if f.direction == "neutral")
            
            breakdown[category] = {
                "contribution": round(total_contrib, 3),
                "weight": round(avg_importance, 3),
                "bullish_signals": bullish_count,
                "bearish_signals": bearish_count,
                "neutral_signals": neutral_count,
                "dominant_direction": "bullish" if bullish_count > bearish_count else (
                    "bearish" if bearish_count > bullish_count else "neutral"
                )
            }
        
        return breakdown
    
    def _calculate_agreement(
        self,
        contributions: Dict[str, List[FeatureContribution]],
        signal: str
    ) -> float:
        """Calculate how many indicators agree with the signal"""
        target_direction = "bullish" if signal in ["buy", "strong_buy"] else (
            "bearish" if signal in ["sell", "strong_sell"] else "neutral"
        )
        
        total = 0
        agreeing = 0
        
        for features in contributions.values():
            for f in features:
                total += 1
                if f.direction == target_direction or f.direction == "neutral":
                    agreeing += 1
        
        return (agreeing / total * 100) if total > 0 else 50
    
    def _generate_insights(
        self,
        symbol: str,
        confidence: float,
        signal: str,
        contributions: Dict[str, List[FeatureContribution]],
        agreement: float
    ) -> List[Dict[str, str]]:
        """Generate actionable insights"""
        insights = []
        
        # Confidence-based insights
        if confidence > 0.75:
            insights.append({
                "type": "strength",
                "message": "High confidence - multiple indicators align with this signal",
                "action": f"Consider {'entering' if signal in ['buy', 'strong_buy'] else 'exiting'} positions"
            })
        elif confidence < 0.4:
            insights.append({
                "type": "warning",
                "message": "Low confidence - signals are conflicting",
                "action": "Wait for clearer signals or reduce position size"
            })
        
        # Agreement-based insights
        if agreement < 50:
            insights.append({
                "type": "caution",
                "message": f"Only {agreement:.0f}% of indicators support this signal",
                "action": "Consider the opposing factors before trading"
            })
        
        # Category-specific insights
        breakdown = self._generate_confidence_breakdown(confidence, signal, contributions)
        
        # Check for divergences
        tech_direction = breakdown.get("technical", {}).get("dominant_direction")
        sent_direction = breakdown.get("sentiment", {}).get("dominant_direction")
        
        if tech_direction and sent_direction and tech_direction != sent_direction:
            if tech_direction != "neutral" and sent_direction != "neutral":
                insights.append({
                    "type": "divergence",
                    "message": f"Technical ({tech_direction}) and sentiment ({sent_direction}) diverge",
                    "action": "This divergence often precedes trend reversals"
                })
        
        return insights
    
    def _assess_risk_factors(
        self,
        features: Dict[str, Any],
        contributions: Dict[str, List[FeatureContribution]]
    ) -> List[Dict[str, Any]]:
        """Identify risk factors in current market conditions"""
        risks = []
        
        # Volatility risk
        volatility = features.get("volatility", 0)
        if volatility > self.THRESHOLDS["volatility"]["high"]:
            risks.append({
                "factor": "High Volatility",
                "level": "high",
                "description": f"Market volatility at {volatility*100:.1f}% - use wider stops",
                "mitigation": "Reduce position size or wait for volatility to decrease"
            })
        
        # Liquidity risk
        spread = features.get("spread", 0)
        if spread > 0.005:
            risks.append({
                "factor": "Low Liquidity",
                "level": "medium",
                "description": f"Wide spread ({spread*100:.2f}%) may cause slippage",
                "mitigation": "Use limit orders instead of market orders"
            })
        
        # Conflicting signals risk
        bullish_count = sum(
            1 for feats in contributions.values()
            for f in feats if f.direction == "bullish"
        )
        bearish_count = sum(
            1 for feats in contributions.values()
            for f in feats if f.direction == "bearish"
        )
        
        if bullish_count > 0 and bearish_count > 0:
            if abs(bullish_count - bearish_count) < 2:
                risks.append({
                    "factor": "Conflicting Signals",
                    "level": "medium",
                    "description": f"Mixed signals ({bullish_count} bullish, {bearish_count} bearish)",
                    "mitigation": "Wait for clearer direction or use smaller position"
                })
        
        return risks
    
    def _classify_confidence(self, confidence: float) -> str:
        """Classify confidence level"""
        if confidence >= 0.8:
            return "very_high"
        elif confidence >= 0.65:
            return "high"
        elif confidence >= 0.5:
            return "moderate"
        elif confidence >= 0.35:
            return "low"
        else:
            return "very_low"


# Singleton instance
_explainer = None

def get_confidence_explainer(db=None) -> ConfidenceExplainer:
    global _explainer
    if _explainer is None:
        _explainer = ConfidenceExplainer(db)
    return _explainer
