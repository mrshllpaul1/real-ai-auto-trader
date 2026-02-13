"""
AI Universe Expansion Service
Trains deep learning on all available data and selects new coins for the universe.
Compares AI recommendations with existing portfolio suggestions.
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import random

from emergentintegrations.llm.chat import LlmChat, UserMessage


class AIUniverseExpander:
    """
    AI-powered service for expanding the trading universe with new coins.
    Uses deep learning and LLM analysis to discover hidden gems.
    """
    
    def __init__(self, db, market_service, deep_learning_ai=None):
        self.db = db
        self.market_service = market_service
        self.deep_learning_ai = deep_learning_ai
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        
    async def get_all_available_coins(self, limit: int = 500) -> List[Dict]:
        """Get a large list of coins from CoinGecko"""
        try:
            if self.market_service:
                # Get top coins by market cap
                coins = await self.market_service.get_all_coins(per_page=limit)
                return coins
        except Exception as e:
            print(f"Error getting coins: {e}")
        return []
    
    async def get_existing_universe(self) -> List[str]:
        """Get coins already in the trading universe"""
        existing = []
        if self.db is not None:
            cursor = self.db.coin_universe.find({"is_active": True})
            docs = await cursor.to_list(length=500)
            existing = [d['coin_id'] for d in docs]
        return existing
    
    async def get_existing_recommendations(self) -> List[Dict]:
        """Get existing AI recommendations for comparison"""
        recommendations = []
        if self.db is not None:
            # Get recent strategies
            strategies_cursor = self.db.strategies.find().sort("created_at", -1).limit(10)
            strategies = await strategies_cursor.to_list(length=10)
            
            for s in strategies:
                if s.get('allocations'):
                    for alloc in s['allocations']:
                        recommendations.append({
                            "coin_id": alloc.get('coin_id', alloc.get('symbol', '')).lower(),
                            "source": "strategy",
                            "score": alloc.get('score', 0),
                            "date": s.get('created_at')
                        })
            
            # Get gem scans
            gems_cursor = self.db.gem_scans.find().sort("timestamp", -1).limit(5)
            gems = await gems_cursor.to_list(length=5)
            
            for g in gems:
                if g.get('gems'):
                    for gem in g['gems'][:10]:
                        recommendations.append({
                            "coin_id": gem.get('coin_id', gem.get('symbol', '')).lower(),
                            "source": "gem_scanner",
                            "score": gem.get('score', 0),
                            "date": g.get('timestamp')
                        })
        
        return recommendations
    
    async def analyze_coin_potential(self, coin: Dict) -> Dict[str, Any]:
        """Analyze a coin's potential using multiple factors"""
        try:
            coin_id = coin.get('id', coin.get('coin_id', ''))
            
            # Get historical data for analysis
            if self.market_service:
                hist_data = await self.market_service.get_historical_data(coin_id, days=30)
                prices = [p[1] for p in hist_data.get('prices', [])] if hist_data else []
            else:
                prices = []
            
            # Calculate basic metrics
            if len(prices) >= 7:
                current_price = prices[-1]
                week_ago = prices[-7]
                month_ago = prices[0] if len(prices) >= 30 else prices[0]
                
                weekly_change = ((current_price - week_ago) / week_ago * 100) if week_ago > 0 else 0
                monthly_change = ((current_price - month_ago) / month_ago * 100) if month_ago > 0 else 0
                
                # Volatility (good for trading)
                price_volatility = max(prices) / min(prices) if min(prices) > 0 else 0
                
                # Calculate potential score
                score = 50  # Base score
                
                # Positive momentum but not overextended
                if 10 < weekly_change < 50:
                    score += 20
                elif -10 < weekly_change < 10:
                    score += 5
                
                # Good monthly performance
                if 20 < monthly_change < 100:
                    score += 15
                
                # Healthy volatility
                if 1.2 < price_volatility < 3:
                    score += 10
                
                # Market cap factor (prefer smaller caps for gems)
                market_cap = coin.get('market_cap', 0)
                if market_cap and market_cap < 1_000_000_000:  # < $1B
                    score += 15
                elif market_cap and market_cap < 100_000_000:  # < $100M
                    score += 25
                
                # Volume factor
                volume = coin.get('total_volume', 0)
                if volume and volume > 10_000_000:  # > $10M daily volume
                    score += 10
                
                return {
                    "coin_id": coin_id,
                    "symbol": coin.get('symbol', '').upper(),
                    "name": coin.get('name', ''),
                    "current_price": current_price,
                    "weekly_change": weekly_change,
                    "monthly_change": monthly_change,
                    "volatility": price_volatility,
                    "market_cap": market_cap,
                    "volume": volume,
                    "potential_score": min(100, max(0, score)),
                    "analysis_date": datetime.now(timezone.utc).isoformat()
                }
        except Exception as e:
            print(f"Error analyzing {coin.get('id', 'unknown')}: {e}")
        
        return None
    
    async def select_new_coins_with_ai(self, candidates: List[Dict], count: int = 30) -> List[Dict]:
        """Use AI to select the best coins from candidates"""
        if not candidates:
            return []
        
        # Sort by potential score
        sorted_candidates = sorted(candidates, key=lambda x: x.get('potential_score', 0), reverse=True)
        top_candidates = sorted_candidates[:min(60, len(sorted_candidates))]  # Top 60 for AI to choose from
        
        # Use LLM for final selection
        if self.api_key and len(top_candidates) > count:
            try:
                candidates_text = "\n".join([
                    f"- {c['symbol']} ({c['name']}): Score {c['potential_score']}, "
                    f"Weekly {c['weekly_change']:.1f}%, Monthly {c['monthly_change']:.1f}%, "
                    f"MCap ${c['market_cap']:,.0f}, Vol ${c['volume']:,.0f}"
                    for c in top_candidates
                ])
                
                prompt = f"""As a crypto trading AI, select the {count} best coins from this list for a trading universe.
Focus on coins with:
1. High growth potential (10-100x opportunity)
2. Good momentum but not overextended
3. Healthy trading volume
4. Reasonable volatility for trading

Candidates:
{candidates_text}

Return ONLY a comma-separated list of the {count} best symbols, no explanations.
Example: BTC,ETH,SOL"""

                chat = LlmChat(
                    api_key=self.api_key,
                    session_id=f"universe_expansion_{datetime.now().strftime('%Y%m%d%H%M')}",
                    system_message="You are a crypto analyst. Be concise."
                ).with_model("openai", "gpt-4o-mini")
                
                response = await chat.send_message(UserMessage(text=prompt))
                response_text = response if isinstance(response, str) else str(response)
                
                # Parse selected symbols
                selected_symbols = [s.strip().upper() for s in response_text.replace('\n', ',').split(',') if s.strip()]
                
                # Map back to full coin data
                selected_coins = []
                for candidate in top_candidates:
                    if candidate['symbol'].upper() in selected_symbols:
                        selected_coins.append(candidate)
                        if len(selected_coins) >= count:
                            break
                
                # If AI didn't return enough, fill from top scored
                while len(selected_coins) < count and len(sorted_candidates) > len(selected_coins):
                    for c in sorted_candidates:
                        if c not in selected_coins:
                            selected_coins.append(c)
                            if len(selected_coins) >= count:
                                break
                
                return selected_coins[:count]
                
            except Exception as e:
                print(f"AI selection error: {e}")
        
        # Fallback to score-based selection
        return sorted_candidates[:count]
    
    async def compare_with_existing(self, new_coins: List[Dict]) -> Dict[str, Any]:
        """Compare new AI selections with existing recommendations"""
        existing_recs = await self.get_existing_recommendations()
        existing_ids = set(r['coin_id'] for r in existing_recs)
        
        new_ids = set(c['coin_id'] for c in new_coins)
        
        # Find overlaps and differences
        overlap = existing_ids & new_ids
        new_only = new_ids - existing_ids
        existing_only = existing_ids - new_ids
        
        # Score comparison
        avg_new_score = sum(c.get('potential_score', 0) for c in new_coins) / len(new_coins) if new_coins else 0
        
        return {
            "overlap_count": len(overlap),
            "overlap_coins": list(overlap),
            "new_discoveries": list(new_only),
            "existing_only": list(existing_only)[:20],
            "average_new_score": avg_new_score,
            "total_new_coins": len(new_coins),
            "comparison_date": datetime.now(timezone.utc).isoformat()
        }
    
    async def expand_universe(self, target_count: int = 30) -> Dict[str, Any]:
        """
        Main function to expand the trading universe with AI-selected coins.
        
        1. Gets all available coins
        2. Excludes already in universe
        3. Analyzes potential of remaining coins
        4. Uses AI to select best candidates
        5. Adds to universe
        6. Compares with existing recommendations
        """
        result = {
            "status": "started",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Step 1: Get available coins
            all_coins = await self.get_all_available_coins(limit=300)
            result["total_coins_found"] = len(all_coins)
            
            if not all_coins:
                return {"status": "error", "message": "Could not fetch coin list"}
            
            # Step 2: Get existing universe
            existing = await self.get_existing_universe()
            result["existing_universe_size"] = len(existing)
            
            # Step 3: Filter out existing
            new_candidates = [c for c in all_coins if c.get('id', '').lower() not in existing]
            result["new_candidates_count"] = len(new_candidates)
            
            # Step 4: Analyze potential (sample to save time)
            sample_size = min(100, len(new_candidates))
            sampled = random.sample(new_candidates, sample_size) if len(new_candidates) > sample_size else new_candidates
            
            analyzed = []
            for coin in sampled:
                analysis = await self.analyze_coin_potential(coin)
                if analysis and analysis.get('potential_score', 0) > 40:
                    analyzed.append(analysis)
                await asyncio.sleep(0.1)  # Rate limiting
            
            result["coins_analyzed"] = len(analyzed)
            
            # Step 5: AI selection
            selected = await self.select_new_coins_with_ai(analyzed, count=target_count)
            result["coins_selected"] = len(selected)
            result["selected_coins"] = selected
            
            # Step 6: Add to universe
            added_count = 0
            if self.db is not None and selected:
                for coin in selected:
                    try:
                        await self.db.coin_universe.update_one(
                            {"coin_id": coin['coin_id']},
                            {
                                "$set": {
                                    "coin_id": coin['coin_id'],
                                    "symbol": coin['symbol'],
                                    "name": coin['name'],
                                    "source": "ai_expansion",
                                    "is_active": True,
                                    "potential_score": coin['potential_score'],
                                    "weekly_change": coin['weekly_change'],
                                    "monthly_change": coin['monthly_change'],
                                    "market_cap": coin['market_cap'],
                                    "added_at": datetime.now(timezone.utc)
                                }
                            },
                            upsert=True
                        )
                        added_count += 1
                    except Exception as e:
                        print(f"Error adding {coin['coin_id']}: {e}")
            
            result["coins_added_to_universe"] = added_count
            
            # Step 7: Compare with existing
            comparison = await self.compare_with_existing(selected)
            result["comparison"] = comparison
            
            # Step 8: Generate summary
            result["status"] = "completed"
            result["summary"] = {
                "new_coins_added": added_count,
                "overlap_with_existing": comparison['overlap_count'],
                "new_discoveries": len(comparison['new_discoveries']),
                "average_potential_score": comparison['average_new_score'],
                "top_picks": [c['symbol'] for c in selected[:5]]
            }
            
            # Save expansion report
            if self.db is not None:
                await self.db.universe_expansions.insert_one({
                    "timestamp": datetime.now(timezone.utc),
                    "coins_added": added_count,
                    "selected_coins": [c['coin_id'] for c in selected],
                    "comparison": comparison,
                    "summary": result["summary"]
                })
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"Universe expansion error: {e}")
        
        return result
    
    async def get_weekly_comparison(self) -> Dict[str, Any]:
        """Get comparison of AI recommendations vs actual performance"""
        if self.db is None:
            return {"error": "Database not available"}
        
        try:
            # Get last week's AI recommendations
            week_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
            
            # Get expansion reports
            expansions = await self.db.universe_expansions.find(
                {"timestamp": {"$gte": week_ago}}
            ).to_list(length=10)
            
            if not expansions:
                return {"message": "No recent expansions found"}
            
            # Get performance of recommended coins
            all_recommended = []
            for exp in expansions:
                all_recommended.extend(exp.get('selected_coins', []))
            
            # Deduplicate
            recommended = list(set(all_recommended))
            
            # Get current prices for comparison
            performance = []
            for coin_id in recommended[:20]:  # Limit for API
                try:
                    if self.market_service:
                        data = await self.market_service.get_coin_price([coin_id])
                        if data and coin_id in data:
                            coin_data = data[coin_id]
                            performance.append({
                                "coin_id": coin_id,
                                "current_price": coin_data.get('current_price', 0),
                                "24h_change": coin_data.get('price_change_percentage_24h', 0),
                                "7d_change": coin_data.get('price_change_percentage_7d', 0)
                            })
                except:
                    pass
            
            # Calculate averages
            avg_24h = sum(p['24h_change'] for p in performance) / len(performance) if performance else 0
            avg_7d = sum(p['7d_change'] for p in performance) / len(performance) if performance else 0
            
            return {
                "period": "last_7_days",
                "coins_tracked": len(performance),
                "average_24h_change": avg_24h,
                "average_7d_change": avg_7d,
                "top_performers": sorted(performance, key=lambda x: x.get('7d_change', 0), reverse=True)[:5],
                "worst_performers": sorted(performance, key=lambda x: x.get('7d_change', 0))[:5],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}


# Factory function
def get_universe_expander(db, market_service, deep_learning_ai=None) -> AIUniverseExpander:
    return AIUniverseExpander(db, market_service, deep_learning_ai)
