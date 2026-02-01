import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv

load_dotenv()

class SocialTradingService:
    """
    Social trading platform - follow top traders, copy trades, share strategies
    """
    
    def __init__(self, db):
        self.db = db
    
    # ============= TRADER PROFILES =============
    
    async def create_trader_profile(
        self,
        user_id: str,
        display_name: str,
        bio: str = "",
        is_public: bool = True
    ) -> Dict[str, Any]:
        """Create or update trader profile"""
        profile = {
            'user_id': user_id,
            'display_name': display_name,
            'bio': bio,
            'is_public': is_public,
            'followers': 0,
            'following': 0,
            'total_trades': 0,
            'win_rate': 0,
            'total_profit_pct': 0,
            'rank': 0,
            'badges': [],
            'joined_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        await self.db.trader_profiles.update_one(
            {'user_id': user_id},
            {'$set': profile},
            upsert=True
        )
        
        return profile
    
    async def get_trader_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get trader profile"""
        return await self.db.trader_profiles.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
    
    async def update_trader_stats(self, user_id: str, trade_result: Dict[str, Any]):
        """Update trader statistics after a trade"""
        profile = await self.get_trader_profile(user_id)
        if not profile:
            return
        
        total_trades = profile.get('total_trades', 0) + 1
        wins = profile.get('wins', 0)
        if trade_result.get('profit_pct', 0) > 0:
            wins += 1
        
        total_profit = profile.get('total_profit_pct', 0) + trade_result.get('profit_pct', 0)
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        
        await self.db.trader_profiles.update_one(
            {'user_id': user_id},
            {'$set': {
                'total_trades': total_trades,
                'wins': wins,
                'win_rate': win_rate,
                'total_profit_pct': total_profit,
                'updated_at': datetime.now().isoformat()
            }}
        )
        
        # Check for badges
        await self._check_badges(user_id, total_trades, win_rate, total_profit)
    
    async def _check_badges(self, user_id: str, trades: int, win_rate: float, profit: float):
        """Award badges based on achievements"""
        badges = []
        
        if trades >= 10:
            badges.append({'name': 'Rookie', 'icon': '🌱', 'earned': True})
        if trades >= 50:
            badges.append({'name': 'Experienced', 'icon': '⭐', 'earned': True})
        if trades >= 100:
            badges.append({'name': 'Veteran', 'icon': '🏆', 'earned': True})
        if win_rate >= 60:
            badges.append({'name': 'Sharp Shooter', 'icon': '🎯', 'earned': True})
        if win_rate >= 75:
            badges.append({'name': 'Sniper', 'icon': '🔫', 'earned': True})
        if profit >= 50:
            badges.append({'name': 'Money Maker', 'icon': '💰', 'earned': True})
        if profit >= 100:
            badges.append({'name': 'Whale', 'icon': '🐋', 'earned': True})
        
        if badges:
            await self.db.trader_profiles.update_one(
                {'user_id': user_id},
                {'$set': {'badges': badges}}
            )
    
    # ============= LEADERBOARD =============
    
    async def get_leaderboard(
        self,
        sort_by: str = 'total_profit_pct',
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get top traders leaderboard"""
        traders = await self.db.trader_profiles.find(
            {'is_public': True, 'total_trades': {'$gte': 5}},
            {'_id': 0}
        ).sort(sort_by, -1).limit(limit).to_list(limit)
        
        # Add rank
        for i, trader in enumerate(traders, 1):
            trader['rank'] = i
        
        return traders
    
    async def get_weekly_top_performers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performers from the last week"""
        week_ago = datetime.now() - timedelta(days=7)
        
        # Aggregate weekly performance
        pipeline = [
            {'$match': {'executed_at': {'$gte': week_ago.isoformat()}}},
            {'$group': {
                '_id': '$user_id',
                'trades': {'$sum': 1},
                'profit': {'$sum': '$profit_pct'}
            }},
            {'$sort': {'profit': -1}},
            {'$limit': limit}
        ]
        
        results = await self.db.social_trades.aggregate(pipeline).to_list(limit)
        
        # Batch fetch all profiles to avoid N+1 queries
        user_ids = [r['_id'] for r in results]
        if user_ids:
            profiles_list = await self.db.trader_profiles.find(
                {'user_id': {'$in': user_ids}},
                {'_id': 0}
            ).to_list(len(user_ids))
            profile_map = {p['user_id']: p for p in profiles_list}
            
            for result in results:
                profile = profile_map.get(result['_id'], {})
                result['display_name'] = profile.get('display_name', 'Anonymous')
                result['badges'] = profile.get('badges', [])
        
        return results
    
    # ============= FOLLOWING =============
    
    async def follow_trader(self, follower_id: str, trader_id: str) -> Dict[str, Any]:
        """Follow a trader"""
        if follower_id == trader_id:
            return {'error': 'Cannot follow yourself'}
        
        # Check if already following
        existing = await self.db.follows.find_one({
            'follower_id': follower_id,
            'trader_id': trader_id
        })
        
        if existing:
            return {'error': 'Already following this trader'}
        
        # Create follow relationship
        await self.db.follows.insert_one({
            'follower_id': follower_id,
            'trader_id': trader_id,
            'followed_at': datetime.now().isoformat()
        })
        
        # Update counts
        await self.db.trader_profiles.update_one(
            {'user_id': trader_id},
            {'$inc': {'followers': 1}}
        )
        await self.db.trader_profiles.update_one(
            {'user_id': follower_id},
            {'$inc': {'following': 1}}
        )
        
        return {'message': 'Now following trader', 'trader_id': trader_id}
    
    async def unfollow_trader(self, follower_id: str, trader_id: str) -> Dict[str, Any]:
        """Unfollow a trader"""
        result = await self.db.follows.delete_one({
            'follower_id': follower_id,
            'trader_id': trader_id
        })
        
        if result.deleted_count > 0:
            await self.db.trader_profiles.update_one(
                {'user_id': trader_id},
                {'$inc': {'followers': -1}}
            )
            await self.db.trader_profiles.update_one(
                {'user_id': follower_id},
                {'$inc': {'following': -1}}
            )
            return {'message': 'Unfollowed trader'}
        
        return {'error': 'Not following this trader'}
    
    async def get_following(self, user_id: str) -> List[Dict[str, Any]]:
        """Get list of traders a user follows"""
        follows = await self.db.follows.find(
            {'follower_id': user_id},
            {'_id': 0}
        ).to_list(100)
        
        # Batch fetch all profiles to avoid N+1 queries
        trader_ids = [f['trader_id'] for f in follows]
        if not trader_ids:
            return []
        
        profiles = await self.db.trader_profiles.find(
            {'user_id': {'$in': trader_ids}},
            {'_id': 0}
        ).to_list(len(trader_ids))
        
        return profiles
    
    async def get_followers(self, user_id: str) -> List[Dict[str, Any]]:
        """Get list of followers"""
        follows = await self.db.follows.find(
            {'trader_id': user_id},
            {'_id': 0}
        ).to_list(100)
        
        # Batch fetch all profiles to avoid N+1 queries
        follower_ids = [f['follower_id'] for f in follows]
        if not follower_ids:
            return []
        
        profiles = await self.db.trader_profiles.find(
            {'user_id': {'$in': follower_ids}},
            {'_id': 0}
        ).to_list(len(follower_ids))
        
        return profiles
    
    # ============= COPY TRADING =============
    
    async def enable_copy_trading(
        self,
        user_id: str,
        trader_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enable copy trading for a trader"""
        config = {
            'user_id': user_id,
            'trader_id': trader_id,
            'enabled': True,
            'max_position_pct': settings.get('max_position_pct', 10),
            'max_daily_trades': settings.get('max_daily_trades', 5),
            'copy_stop_loss': settings.get('copy_stop_loss', True),
            'copy_take_profit': settings.get('copy_take_profit', True),
            'mode': settings.get('mode', 'paper'),
            'created_at': datetime.now().isoformat()
        }
        
        await self.db.copy_trading.update_one(
            {'user_id': user_id, 'trader_id': trader_id},
            {'$set': config},
            upsert=True
        )
        
        return config
    
    async def disable_copy_trading(self, user_id: str, trader_id: str) -> Dict[str, Any]:
        """Disable copy trading for a trader"""
        await self.db.copy_trading.update_one(
            {'user_id': user_id, 'trader_id': trader_id},
            {'$set': {'enabled': False}}
        )
        return {'message': 'Copy trading disabled'}
    
    async def get_copy_settings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all copy trading settings for a user"""
        return await self.db.copy_trading.find(
            {'user_id': user_id},
            {'_id': 0}
        ).to_list(50)
    
    async def copy_trade(
        self,
        trader_id: str,
        trade: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Copy a trade to all copiers"""
        # Find all users copying this trader
        copiers = await self.db.copy_trading.find({
            'trader_id': trader_id,
            'enabled': True
        }).to_list(100)
        
        copied_trades = []
        for copier in copiers:
            copy_trade = {
                'trade_id': str(uuid.uuid4())[:8],
                'user_id': copier['user_id'],
                'original_trader_id': trader_id,
                'coin_id': trade.get('coin_id'),
                'symbol': trade.get('symbol'),
                'action': trade.get('action'),
                'entry_price': trade.get('entry_price'),
                'amount': trade.get('amount') * (copier.get('max_position_pct', 10) / 100),
                'mode': copier.get('mode', 'paper'),
                'type': 'COPY',
                'copied_at': datetime.now().isoformat()
            }
            
            await self.db.social_trades.insert_one(dict(copy_trade))
            copied_trades.append(copy_trade)
        
        return copied_trades
    
    # ============= STRATEGY SHARING =============
    
    async def share_strategy(
        self,
        user_id: str,
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Share a trading strategy"""
        shared = {
            'strategy_id': str(uuid.uuid4())[:8],
            'user_id': user_id,
            'name': strategy.get('name', 'Unnamed Strategy'),
            'description': strategy.get('description', ''),
            'parameters': strategy.get('parameters', {}),
            'backtest_results': strategy.get('backtest_results', {}),
            'likes': 0,
            'copies': 0,
            'is_public': strategy.get('is_public', True),
            'shared_at': datetime.now().isoformat()
        }
        
        await self.db.shared_strategies.insert_one(dict(shared))
        return shared
    
    async def get_shared_strategies(
        self,
        sort_by: str = 'likes',
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get public shared strategies"""
        strategies = await self.db.shared_strategies.find(
            {'is_public': True},
            {'_id': 0}
        ).sort(sort_by, -1).limit(limit).to_list(limit)
        
        # Enrich with creator info
        for strat in strategies:
            profile = await self.get_trader_profile(strat['user_id'])
            if profile:
                strat['creator_name'] = profile.get('display_name', 'Anonymous')
        
        return strategies
    
    async def like_strategy(self, user_id: str, strategy_id: str) -> Dict[str, Any]:
        """Like a strategy"""
        await self.db.shared_strategies.update_one(
            {'strategy_id': strategy_id},
            {'$inc': {'likes': 1}}
        )
        
        await self.db.strategy_likes.insert_one({
            'user_id': user_id,
            'strategy_id': strategy_id,
            'liked_at': datetime.now().isoformat()
        })
        
        return {'message': 'Strategy liked'}
    
    async def copy_strategy(self, user_id: str, strategy_id: str) -> Dict[str, Any]:
        """Copy a strategy to your own strategies"""
        original = await self.db.shared_strategies.find_one(
            {'strategy_id': strategy_id},
            {'_id': 0}
        )
        
        if not original:
            return {'error': 'Strategy not found'}
        
        copied = {
            'user_id': user_id,
            'copied_from': strategy_id,
            'original_creator': original['user_id'],
            'name': f"Copy of {original['name']}",
            'parameters': original['parameters'],
            'copied_at': datetime.now().isoformat()
        }
        
        await self.db.user_strategies.insert_one(dict(copied))
        await self.db.shared_strategies.update_one(
            {'strategy_id': strategy_id},
            {'$inc': {'copies': 1}}
        )
        
        return {'message': 'Strategy copied', 'strategy': copied}
    
    # ============= ACTIVITY FEED =============
    
    async def get_activity_feed(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get activity feed from followed traders"""
        # Get followed traders
        follows = await self.db.follows.find(
            {'follower_id': user_id}
        ).to_list(100)
        
        trader_ids = [f['trader_id'] for f in follows]
        
        if not trader_ids:
            return []
        
        # Get recent trades from followed traders
        activities = await self.db.social_trades.find(
            {'user_id': {'$in': trader_ids}},
            {'_id': 0}
        ).sort('executed_at', -1).limit(limit).to_list(limit)
        
        # Enrich with trader info
        for activity in activities:
            profile = await self.get_trader_profile(activity['user_id'])
            if profile:
                activity['trader_name'] = profile.get('display_name', 'Anonymous')
        
        return activities
