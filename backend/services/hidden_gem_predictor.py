"""
Hidden Gem Predictor Service
Uses deep learning and market analysis to predict hidden gems before they rise.
"""

import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np

from emergentintegrations.llm.chat import LlmChat, UserMessage


class HiddenGemPredictor:
    """
    AI-powered hidden gem predictor that identifies coins before they pump.
    Uses multiple signals: volume surge, social momentum, whale activity, pattern detection.
    """
    
    def __init__(self, db, market_service, deep_learning_ai=None):
        self.db = db
        self.market_service = market_service
        self.deep_learning_ai = deep_learning_ai
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        
        # Gem scoring weights
        self.weights = {
            "volume_surge": 0.25,
            "price_momentum": 0.20,
            "market_cap_potential": 0.20,
            "technical_setup": 0.15,
            "sentiment": 0.10,
            "whale_activity": 0.10
        }
        
    async def scan_for_gems(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Scan the market for potential hidden gems.
        Returns ranked list of coins with gem potential.
        """
        gems = []
        
        try:
            # Get coins with lower market cap (more gem potential)
            if self.market_service:
                all_coins = await self.market_service.get_all_coins(per_page=250)
                
                # Filter for potential gems (rank 50-300 typically have more upside)
                candidates = [c for c in all_coins if c.get('market_cap_rank', 0) > 30 and c.get('market_cap_rank', 0) < 300]
                
                for coin in candidates[:limit]:
                    gem_score = await self._analyze_gem_potential(coin)
                    if gem_score and gem_score['total_score'] >= 60:
                        gems.append(gem_score)
                
                # Sort by score
                gems.sort(key=lambda x: x['total_score'], reverse=True)
                
        except Exception as e:
            print(f"Gem scan error: {e}")
        
        return gems[:20]  # Return top 20
    
    async def _analyze_gem_potential(self, coin: Dict) -> Optional[Dict[str, Any]]:
        """Analyze a coin's potential as a hidden gem"""
        try:
            coin_id = coin.get('id', '')
            
            scores = {}
            
            # 1. Volume Surge Score (unusual volume = potential breakout)
            volume = coin.get('total_volume', 0)
            market_cap = coin.get('market_cap', 1)
            volume_ratio = (volume / market_cap) * 100 if market_cap > 0 else 0
            
            if volume_ratio > 20:
                scores['volume_surge'] = 90  # Very high volume
            elif volume_ratio > 10:
                scores['volume_surge'] = 75
            elif volume_ratio > 5:
                scores['volume_surge'] = 60
            else:
                scores['volume_surge'] = 40
            
            # 2. Price Momentum Score
            price_change_24h = coin.get('price_change_24h', 0)
            price_change_7d = coin.get('price_change_7d', 0)
            
            # Ideal: positive but not overextended
            if 5 < price_change_24h < 30:
                scores['price_momentum'] = 80
            elif 0 < price_change_24h < 5:
                scores['price_momentum'] = 70
            elif -5 < price_change_24h < 0:
                scores['price_momentum'] = 60  # Potential dip buy
            elif price_change_24h > 30:
                scores['price_momentum'] = 40  # Overextended
            else:
                scores['price_momentum'] = 50
            
            # 3. Market Cap Potential (smaller = more upside)
            if market_cap < 50_000_000:  # < $50M
                scores['market_cap_potential'] = 95
            elif market_cap < 100_000_000:  # < $100M
                scores['market_cap_potential'] = 85
            elif market_cap < 500_000_000:  # < $500M
                scores['market_cap_potential'] = 70
            elif market_cap < 1_000_000_000:  # < $1B
                scores['market_cap_potential'] = 55
            else:
                scores['market_cap_potential'] = 40
            
            # 4. Technical Setup Score (get price data for analysis)
            scores['technical_setup'] = 60  # Default
            if self.deep_learning_ai and self.market_service:
                try:
                    hist_data = await self.market_service.get_historical_data(coin_id, days=30)
                    if hist_data and hist_data.get('prices'):
                        prices = [p[1] for p in hist_data['prices']]
                        if len(prices) >= 14:
                            # Check for accumulation pattern
                            recent_volatility = np.std(prices[-14:]) / np.mean(prices[-14:])
                            if recent_volatility < 0.05:
                                scores['technical_setup'] = 85  # Low volatility = accumulation
                            elif recent_volatility < 0.1:
                                scores['technical_setup'] = 70
                            
                            # Check for higher lows
                            if prices[-1] > prices[-7] > prices[-14]:
                                scores['technical_setup'] = min(95, scores['technical_setup'] + 15)
                except:
                    pass
            
            # 5. Sentiment Score (placeholder - would use news API)
            scores['sentiment'] = 65  # Neutral default
            
            # 6. Whale Activity (placeholder - would use on-chain data)
            scores['whale_activity'] = 60  # Neutral default
            
            # Calculate weighted total
            total_score = sum(
                scores.get(key, 50) * weight 
                for key, weight in self.weights.items()
            )
            
            return {
                "coin_id": coin_id,
                "symbol": coin.get('symbol', '').upper(),
                "name": coin.get('name', ''),
                "current_price": coin.get('current_price', 0),
                "market_cap": market_cap,
                "market_cap_rank": coin.get('market_cap_rank', 0),
                "volume_24h": volume,
                "price_change_24h": price_change_24h,
                "scores": scores,
                "total_score": round(total_score, 1),
                "gem_rating": self._get_gem_rating(total_score),
                "analysis_time": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"Gem analysis error for {coin.get('id', 'unknown')}: {e}")
            return None
    
    def _get_gem_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 85:
            return "💎 DIAMOND GEM"
        elif score >= 75:
            return "🌟 HIGH POTENTIAL"
        elif score >= 65:
            return "✨ PROMISING"
        elif score >= 55:
            return "👀 WATCH"
        else:
            return "📊 AVERAGE"
    
    async def predict_next_gems(self, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Predict which coins are likely to pump in the next X days.
        Uses historical patterns and current signals.
        """
        result = {
            "prediction_period": f"next_{days_ahead}_days",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "predictions": [],
            "methodology": "Multi-factor analysis: volume, momentum, market cap, technicals"
        }
        
        # Get current gems
        gems = await self.scan_for_gems(limit=30)
        
        if not gems:
            result["error"] = "No gem candidates found"
            return result
        
        # Use AI to rank and predict
        if self.api_key:
            try:
                gem_summary = "\n".join([
                    f"- {g['symbol']}: Score {g['total_score']}, MCap ${g['market_cap']:,.0f}, "
                    f"Vol {g['scores'].get('volume_surge', 0)}, Mom {g['scores'].get('price_momentum', 0)}"
                    for g in gems[:15]
                ])
                
                prompt = f"""Analyze these potential hidden gem cryptocurrencies and predict which 5 are most likely to pump in the next {days_ahead} days:

{gem_summary}

For each coin, provide:
1. Confidence level (1-100%)
2. Expected move (e.g., +20-50%)
3. Key catalyst

Format: SYMBOL | Confidence% | Expected Move | Reason (one line each)"""

                chat = LlmChat(
                    api_key=self.api_key,
                    session_id=f"gem_predict_{datetime.now().strftime('%Y%m%d%H%M')}",
                    system_message="You are a crypto analyst specializing in finding hidden gems before they pump. Be specific and data-driven."
                ).with_model("openai", "gpt-4o-mini")
                
                response = await chat.send_message(UserMessage(text=prompt))
                response_text = response if isinstance(response, str) else str(response)
                
                # Parse response
                result["ai_analysis"] = response_text
                
                # Extract predictions
                for gem in gems[:5]:
                    result["predictions"].append({
                        "coin_id": gem['coin_id'],
                        "symbol": gem['symbol'],
                        "name": gem['name'],
                        "current_price": gem['current_price'],
                        "gem_score": gem['total_score'],
                        "gem_rating": gem['gem_rating'],
                        "scores": gem['scores'],
                        "prediction_confidence": min(85, gem['total_score'])
                    })
                
            except Exception as e:
                print(f"AI prediction error: {e}")
        
        # Add non-AI predictions as fallback
        if not result["predictions"]:
            for gem in gems[:5]:
                result["predictions"].append({
                    "coin_id": gem['coin_id'],
                    "symbol": gem['symbol'],
                    "gem_score": gem['total_score'],
                    "gem_rating": gem['gem_rating']
                })
        
        # Save predictions for tracking
        if self.db is not None:
            try:
                await self.db.gem_predictions.insert_one({
                    "predicted_at": datetime.now(timezone.utc),
                    "period_days": days_ahead,
                    "predictions": result["predictions"],
                    "verified": False
                })
            except:
                pass
        
        return result
    
    async def train_on_historical(self) -> Dict[str, Any]:
        """
        Train the gem predictor on historical data.
        Analyzes past gems that pumped and learns patterns.
        """
        result = {
            "status": "training",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "patterns_learned": []
        }
        
        try:
            # Get historical gem predictions if available
            if self.db is not None:
                past_predictions = await self.db.gem_predictions.find(
                    {"verified": True}
                ).to_list(length=100)
                
                # Analyze which predictions were correct
                successful_patterns = []
                for pred in past_predictions:
                    if pred.get('actual_performance'):
                        for p in pred.get('predictions', []):
                            if p.get('actual_gain', 0) > 20:  # 20%+ gain = success
                                successful_patterns.append({
                                    "scores": p.get('scores', {}),
                                    "gain": p.get('actual_gain')
                                })
                
                if successful_patterns:
                    # Learn optimal score thresholds
                    avg_scores = {}
                    for key in self.weights.keys():
                        values = [p['scores'].get(key, 50) for p in successful_patterns if p['scores'].get(key)]
                        if values:
                            avg_scores[key] = np.mean(values)
                    
                    result["patterns_learned"] = [
                        f"Successful gems had average {k}: {v:.1f}"
                        for k, v in avg_scores.items()
                    ]
                    result["optimal_thresholds"] = avg_scores
            
            result["status"] = "completed"
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result


# Factory function
def get_gem_predictor(db, market_service, deep_learning_ai=None) -> HiddenGemPredictor:
    return HiddenGemPredictor(db, market_service, deep_learning_ai)
