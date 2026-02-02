"""
AI Coin Auto-Discovery Service
Proactively scans trending coins and discovers promising new additions to the universe.
Uses market data APIs and AI analysis to find hidden gems.
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import httpx

load_dotenv()


class AICoinDiscoveryService:
    """
    Autonomous coin discovery engine that:
    1. Fetches trending/new coins from CoinGecko
    2. Analyzes momentum, volume, and market metrics
    3. Uses AI to evaluate potential
    4. Automatically adds promising coins to the universe
    """
    
    def __init__(self, db, universe_manager=None):
        self.db = db
        self.universe_manager = universe_manager
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        
        # Discovery settings
        self.settings = {
            'enabled': True,
            'min_score': 70,  # Minimum score to auto-add
            'max_daily_additions': 5,  # Limit auto-additions per day
            'require_approval': False,  # If True, adds to pending instead of auto-adding
            'scan_categories': ['trending', 'new', 'gainers'],
            'min_market_cap': 1_000_000,  # $1M minimum
            'min_volume_24h': 500_000,  # $500K minimum volume
        }
        
        # Track discoveries to avoid spam
        self.recent_discoveries = {}
        self.daily_additions = 0
        self.last_reset = datetime.now().date()
    
    def set_universe_manager(self, manager):
        """Set the universe manager for adding coins"""
        self.universe_manager = manager
    
    async def load_settings(self):
        """Load discovery settings from database"""
        settings = await self.db.discovery_settings.find_one({'_id': 'default'})
        if settings:
            self.settings.update({k: v for k, v in settings.items() if k != '_id'})
        return self.settings
    
    async def save_settings(self, updates: Dict[str, Any]):
        """Save discovery settings"""
        self.settings.update(updates)
        await self.db.discovery_settings.update_one(
            {'_id': 'default'},
            {'$set': self.settings},
            upsert=True
        )
        return self.settings
    
    async def run_discovery_scan(self) -> Dict[str, Any]:
        """
        Main discovery scan - fetches and analyzes potential new coins
        """
        print("🔍 Starting AI coin discovery scan...")
        
        await self.load_settings()
        
        if not self.settings['enabled']:
            return {'success': False, 'error': 'Discovery is disabled'}
        
        # Reset daily counter if new day
        today = datetime.now().date()
        if today != self.last_reset:
            self.daily_additions = 0
            self.last_reset = today
        
        results = {
            'scan_time': datetime.now().isoformat(),
            'candidates_found': 0,
            'candidates_analyzed': [],
            'coins_added': [],
            'coins_pending': [],
            'errors': []
        }
        
        try:
            # Gather candidates from multiple sources
            candidates = []
            
            if 'trending' in self.settings['scan_categories']:
                trending = await self._fetch_trending_coins()
                candidates.extend(trending)
            
            if 'new' in self.settings['scan_categories']:
                new_coins = await self._fetch_new_coins()
                candidates.extend(new_coins)
            
            if 'gainers' in self.settings['scan_categories']:
                gainers = await self._fetch_top_gainers()
                candidates.extend(gainers)
            
            # Deduplicate
            seen = set()
            unique_candidates = []
            for c in candidates:
                if c['id'] not in seen:
                    seen.add(c['id'])
                    unique_candidates.append(c)
            
            results['candidates_found'] = len(unique_candidates)
            
            # Filter out coins already in universe
            existing_coins = set()
            if self.universe_manager:
                all_coins = await self.universe_manager.get_all_coins()
                existing_coins = {c['coin_id'] for c in all_coins}
            
            new_candidates = [c for c in unique_candidates if c['id'] not in existing_coins]
            
            # Analyze each candidate
            for candidate in new_candidates[:20]:  # Limit to 20 per scan
                try:
                    analysis = await self._analyze_candidate(candidate)
                    results['candidates_analyzed'].append(analysis)
                    
                    # Check if meets threshold
                    if analysis['score'] >= self.settings['min_score']:
                        if self.daily_additions < self.settings['max_daily_additions']:
                            if self.settings['require_approval']:
                                # Add to pending
                                await self._add_to_pending(analysis)
                                results['coins_pending'].append(analysis['coin_id'])
                            else:
                                # Auto-add to universe
                                add_result = await self._add_to_universe(analysis)
                                if add_result['success']:
                                    results['coins_added'].append(analysis['coin_id'])
                                    self.daily_additions += 1
                        
                except Exception as e:
                    results['errors'].append(f"{candidate.get('id')}: {str(e)}")
            
            # Log discovery run
            await self._log_discovery_run(results)
            
            print(f"✅ Discovery complete: {len(results['coins_added'])} added, {len(results['coins_pending'])} pending")
            
        except Exception as e:
            results['errors'].append(str(e))
            print(f"❌ Discovery error: {e}")
        
        return results
    
    async def _fetch_trending_coins(self) -> List[Dict]:
        """Fetch trending coins from CoinGecko"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.coingecko_base}/search/trending")
                if response.status_code == 200:
                    data = response.json()
                    coins = []
                    for item in data.get('coins', []):
                        coin = item.get('item', {})
                        coins.append({
                            'id': coin.get('id'),
                            'symbol': coin.get('symbol', '').upper(),
                            'name': coin.get('name'),
                            'market_cap_rank': coin.get('market_cap_rank'),
                            'source': 'trending'
                        })
                    return coins
        except Exception as e:
            print(f"Trending fetch error: {e}")
        return []
    
    async def _fetch_new_coins(self) -> List[Dict]:
        """Fetch recently added coins"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get coins sorted by newest
                response = await client.get(
                    f"{self.coingecko_base}/coins/markets",
                    params={
                        'vs_currency': 'usd',
                        'order': 'id_asc',
                        'per_page': 50,
                        'page': 1,
                        'sparkline': False
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    coins = []
                    for coin in data:
                        # Filter by market cap
                        if coin.get('market_cap', 0) >= self.settings['min_market_cap']:
                            coins.append({
                                'id': coin.get('id'),
                                'symbol': coin.get('symbol', '').upper(),
                                'name': coin.get('name'),
                                'market_cap': coin.get('market_cap'),
                                'volume_24h': coin.get('total_volume'),
                                'price_change_24h': coin.get('price_change_percentage_24h'),
                                'source': 'new'
                            })
                    return coins
        except Exception as e:
            print(f"New coins fetch error: {e}")
        return []
    
    async def _fetch_top_gainers(self) -> List[Dict]:
        """Fetch top gaining coins (24h)"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.coingecko_base}/coins/markets",
                    params={
                        'vs_currency': 'usd',
                        'order': 'percent_change_24h_desc',
                        'per_page': 30,
                        'page': 1,
                        'sparkline': False
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    coins = []
                    for coin in data:
                        pct_change = coin.get('price_change_percentage_24h', 0) or 0
                        if pct_change > 10:  # Only coins up >10%
                            coins.append({
                                'id': coin.get('id'),
                                'symbol': coin.get('symbol', '').upper(),
                                'name': coin.get('name'),
                                'market_cap': coin.get('market_cap'),
                                'volume_24h': coin.get('total_volume'),
                                'price_change_24h': pct_change,
                                'source': 'gainer'
                            })
                    return coins
        except Exception as e:
            print(f"Gainers fetch error: {e}")
        return []
    
    async def _analyze_candidate(self, candidate: Dict) -> Dict[str, Any]:
        """
        Analyze a candidate coin and score its potential
        """
        coin_id = candidate.get('id')
        symbol = candidate.get('symbol', '')
        
        # Fetch detailed data
        details = await self._get_coin_details(coin_id)
        
        # Calculate scores
        scores = {
            'market_cap_score': self._score_market_cap(details.get('market_cap', 0)),
            'volume_score': self._score_volume(details.get('volume_24h', 0), details.get('market_cap', 1)),
            'momentum_score': self._score_momentum(details.get('price_changes', {})),
            'community_score': self._score_community(details.get('community_data', {})),
            'development_score': self._score_development(details.get('developer_data', {})),
        }
        
        # Weighted total score
        weights = {
            'market_cap_score': 0.15,
            'volume_score': 0.25,
            'momentum_score': 0.30,
            'community_score': 0.15,
            'development_score': 0.15,
        }
        
        total_score = sum(scores[k] * weights[k] for k in scores)
        
        # Generate AI reason
        reason = self._generate_discovery_reason(candidate, details, scores, total_score)
        
        return {
            'coin_id': coin_id,
            'symbol': symbol,
            'name': candidate.get('name', ''),
            'source': candidate.get('source'),
            'score': round(total_score, 1),
            'scores': scores,
            'market_cap': details.get('market_cap'),
            'volume_24h': details.get('volume_24h'),
            'price_change_24h': details.get('price_changes', {}).get('24h', 0),
            'price_change_7d': details.get('price_changes', {}).get('7d', 0),
            'reason': reason,
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def _get_coin_details(self, coin_id: str) -> Dict:
        """Fetch detailed coin data"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.coingecko_base}/coins/{coin_id}",
                    params={
                        'localization': False,
                        'tickers': False,
                        'market_data': True,
                        'community_data': True,
                        'developer_data': True,
                        'sparkline': False
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    market_data = data.get('market_data', {})
                    return {
                        'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                        'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                        'price_changes': {
                            '24h': market_data.get('price_change_percentage_24h', 0),
                            '7d': market_data.get('price_change_percentage_7d', 0),
                            '30d': market_data.get('price_change_percentage_30d', 0),
                        },
                        'community_data': data.get('community_data', {}),
                        'developer_data': data.get('developer_data', {}),
                    }
        except Exception as e:
            print(f"Details fetch error for {coin_id}: {e}")
        return {}
    
    def _score_market_cap(self, market_cap: float) -> float:
        """Score based on market cap (prefer mid-cap for gem potential)"""
        if market_cap < 1_000_000:
            return 30  # Too small, risky
        elif market_cap < 10_000_000:
            return 70  # Small cap - high potential
        elif market_cap < 100_000_000:
            return 90  # Mid cap - sweet spot
        elif market_cap < 1_000_000_000:
            return 75  # Large cap - stable but less upside
        else:
            return 50  # Mega cap - limited growth potential
    
    def _score_volume(self, volume: float, market_cap: float) -> float:
        """Score based on volume relative to market cap"""
        if market_cap == 0:
            return 0
        ratio = volume / market_cap
        if ratio < 0.01:
            return 30  # Low liquidity
        elif ratio < 0.05:
            return 60  # Moderate
        elif ratio < 0.20:
            return 85  # Healthy volume
        elif ratio < 0.50:
            return 95  # High activity
        else:
            return 70  # Extremely high (could be manipulation)
    
    def _score_momentum(self, price_changes: Dict) -> float:
        """Score based on price momentum"""
        change_24h = price_changes.get('24h', 0) or 0
        change_7d = price_changes.get('7d', 0) or 0
        
        score = 50  # Base
        
        # 24h momentum
        if change_24h > 50:
            score += 25
        elif change_24h > 20:
            score += 20
        elif change_24h > 5:
            score += 10
        elif change_24h < -20:
            score -= 15
        
        # 7d trend
        if change_7d > 100:
            score += 25
        elif change_7d > 30:
            score += 15
        elif change_7d > 0:
            score += 5
        elif change_7d < -30:
            score -= 10
        
        return max(0, min(100, score))
    
    def _score_community(self, community_data: Dict) -> float:
        """Score based on community metrics"""
        twitter = community_data.get('twitter_followers', 0) or 0
        reddit = community_data.get('reddit_subscribers', 0) or 0
        
        score = 40  # Base
        
        if twitter > 100_000:
            score += 30
        elif twitter > 10_000:
            score += 20
        elif twitter > 1_000:
            score += 10
        
        if reddit > 50_000:
            score += 20
        elif reddit > 5_000:
            score += 10
        
        return min(100, score)
    
    def _score_development(self, dev_data: Dict) -> float:
        """Score based on development activity"""
        commits_4w = dev_data.get('commit_count_4_weeks', 0) or 0
        
        if commits_4w > 100:
            return 95
        elif commits_4w > 50:
            return 80
        elif commits_4w > 20:
            return 65
        elif commits_4w > 5:
            return 50
        else:
            return 30
    
    def _generate_discovery_reason(self, candidate: Dict, details: Dict, scores: Dict, total: float) -> str:
        """Generate a human-readable reason for the discovery"""
        reasons = []
        
        source = candidate.get('source', '')
        if source == 'trending':
            reasons.append("Currently trending on CoinGecko")
        elif source == 'gainer':
            reasons.append(f"Strong momentum (+{candidate.get('price_change_24h', 0):.1f}% 24h)")
        elif source == 'new':
            reasons.append("Recently listed with growing traction")
        
        if scores['volume_score'] > 80:
            reasons.append("High trading volume relative to market cap")
        
        if scores['momentum_score'] > 75:
            reasons.append("Strong upward price momentum")
        
        if scores['community_score'] > 70:
            reasons.append("Active community engagement")
        
        if scores['development_score'] > 70:
            reasons.append("Active development activity")
        
        market_cap = details.get('market_cap', 0)
        if 10_000_000 < market_cap < 100_000_000:
            reasons.append("Mid-cap with significant growth potential")
        
        return "; ".join(reasons) if reasons else "Meets discovery criteria"
    
    async def _add_to_universe(self, analysis: Dict) -> Dict:
        """Add discovered coin to the universe"""
        if not self.universe_manager:
            return {'success': False, 'error': 'Universe manager not available'}
        
        result = await self.universe_manager.ai_discover_coin(
            coin_id=analysis['coin_id'],
            symbol=analysis['symbol'],
            reason=analysis['reason'],
            potential_score=analysis['score'],
            market_cap=analysis.get('market_cap'),
            volume_24h=analysis.get('volume_24h')
        )
        
        # Send notification
        if result.get('success'):
            try:
                from services.notification_service import NotificationService
                notif_service = NotificationService(self.db)
                await notif_service.notify_ai_discovery({
                    'symbol': analysis['symbol'],
                    'reason': analysis['reason'],
                    'potential_score': analysis['score']
                })
            except Exception as e:
                print(f"Notification error: {e}")
        
        return result
    
    async def _add_to_pending(self, analysis: Dict) -> Dict:
        """Add to pending discoveries for approval"""
        pending = {
            'coin_id': analysis['coin_id'],
            'symbol': analysis['symbol'],
            'name': analysis.get('name', ''),
            'score': analysis['score'],
            'scores': analysis['scores'],
            'reason': analysis['reason'],
            'market_cap': analysis.get('market_cap'),
            'volume_24h': analysis.get('volume_24h'),
            'discovered_at': datetime.now().isoformat(),
            'status': 'pending',
            'source': analysis.get('source')
        }
        await self.db.pending_discoveries.insert_one(pending)
        return {'success': True}
    
    async def get_pending_discoveries(self) -> List[Dict]:
        """Get all pending discoveries awaiting approval"""
        pending = await self.db.pending_discoveries.find(
            {'status': 'pending'},
            {'_id': 0}
        ).sort('discovered_at', -1).to_list(100)
        return pending
    
    async def approve_discovery(self, coin_id: str) -> Dict:
        """Approve a pending discovery"""
        pending = await self.db.pending_discoveries.find_one({'coin_id': coin_id, 'status': 'pending'})
        if not pending:
            return {'success': False, 'error': 'Discovery not found'}
        
        # Add to universe
        result = await self._add_to_universe({
            'coin_id': pending['coin_id'],
            'symbol': pending['symbol'],
            'reason': pending['reason'],
            'score': pending['score'],
            'market_cap': pending.get('market_cap'),
            'volume_24h': pending.get('volume_24h')
        })
        
        if result.get('success'):
            await self.db.pending_discoveries.update_one(
                {'coin_id': coin_id},
                {'$set': {'status': 'approved', 'approved_at': datetime.now().isoformat()}}
            )
        
        return result
    
    async def reject_discovery(self, coin_id: str, reason: str = '') -> Dict:
        """Reject a pending discovery"""
        result = await self.db.pending_discoveries.update_one(
            {'coin_id': coin_id, 'status': 'pending'},
            {'$set': {
                'status': 'rejected',
                'rejected_at': datetime.now().isoformat(),
                'rejection_reason': reason
            }}
        )
        return {'success': result.modified_count > 0}
    
    async def _log_discovery_run(self, results: Dict):
        """Log discovery run results"""
        log = {
            'timestamp': results['scan_time'],
            'candidates_found': results['candidates_found'],
            'candidates_analyzed': len(results['candidates_analyzed']),
            'coins_added': results['coins_added'],
            'coins_pending': results['coins_pending'],
            'errors': results['errors']
        }
        await self.db.discovery_logs.insert_one(log)
    
    async def get_discovery_history(self, limit: int = 20) -> List[Dict]:
        """Get discovery run history"""
        history = await self.db.discovery_logs.find(
            {},
            {'_id': 0}
        ).sort('timestamp', -1).limit(limit).to_list(limit)
        return history
    
    async def get_stats(self) -> Dict:
        """Get discovery statistics"""
        total_discovered = await self.db.pending_discoveries.count_documents({})
        approved = await self.db.pending_discoveries.count_documents({'status': 'approved'})
        pending = await self.db.pending_discoveries.count_documents({'status': 'pending'})
        rejected = await self.db.pending_discoveries.count_documents({'status': 'rejected'})
        
        # Get recent discoveries
        recent = await self.db.discovery_logs.find(
            {},
            {'_id': 0}
        ).sort('timestamp', -1).limit(5).to_list(5)
        
        return {
            'total_discoveries': total_discovered,
            'approved': approved,
            'pending': pending,
            'rejected': rejected,
            'daily_additions_remaining': self.settings['max_daily_additions'] - self.daily_additions,
            'settings': self.settings,
            'recent_runs': recent
        }


# Global instance
_discovery_service = None

def get_discovery_service():
    global _discovery_service
    return _discovery_service

def set_discovery_service(service):
    global _discovery_service
    _discovery_service = service
