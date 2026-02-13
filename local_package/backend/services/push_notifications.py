"""
Push Notifications Service
==========================
Web Push notifications for trade alerts, stop-loss triggers, and portfolio updates.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class PushSubscription:
    """Web Push subscription data"""
    endpoint: str
    keys: Dict[str, str]
    user_id: str
    created_at: str
    device_info: Optional[str] = None


@dataclass
class Notification:
    """Notification payload"""
    title: str
    body: str
    icon: str = "/logo192.png"
    badge: str = "/badge.png"
    tag: Optional[str] = None
    data: Optional[Dict] = None
    actions: Optional[List[Dict]] = None
    require_interaction: bool = False
    timestamp: Optional[str] = None


class PushNotificationService:
    """
    Service for managing Web Push notifications.
    
    Features:
    - Subscribe/unsubscribe devices
    - Send notifications for trades, alerts, portfolio updates
    - Notification history and preferences
    """
    
    NOTIFICATION_TYPES = {
        'trade_pending': {
            'title': '🔔 Trade Pending Confirmation',
            'icon': '💰',
            'require_interaction': True
        },
        'trade_executed': {
            'title': '✅ Trade Executed',
            'icon': '📈',
            'require_interaction': False
        },
        'stop_loss_triggered': {
            'title': '🔴 Stop-Loss Triggered',
            'icon': '🛑',
            'require_interaction': True
        },
        'take_profit_triggered': {
            'title': '🟢 Take-Profit Hit',
            'icon': '🎯',
            'require_interaction': False
        },
        'price_alert': {
            'title': '📊 Price Alert',
            'icon': '💹',
            'require_interaction': False
        },
        'portfolio_milestone': {
            'title': '🏆 Portfolio Milestone',
            'icon': '🚀',
            'require_interaction': False
        },
        'arbitrage_opportunity': {
            'title': '⚡ Arbitrage Opportunity',
            'icon': '💎',
            'require_interaction': True
        },
        'rebalance_needed': {
            'title': '⚖️ Rebalance Recommended',
            'icon': '📊',
            'require_interaction': False
        },
        'whale_alert': {
            'title': '🐋 Whale Movement Detected',
            'icon': '🌊',
            'require_interaction': False
        },
        'sentiment_shift': {
            'title': '📰 Sentiment Shift',
            'icon': '📈',
            'require_interaction': False
        }
    }
    
    def __init__(self, db):
        self.db = db
        self.subscriptions: Dict[str, List[PushSubscription]] = {}
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.preferences: Dict[str, Dict[str, bool]] = {}
        self._worker_task = None
        logger.info("✅ Push Notification Service initialized")
    
    async def start(self):
        """Start the notification worker"""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._notification_worker())
            logger.info("📬 Push notification worker started")
    
    async def stop(self):
        """Stop the notification worker"""
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None
    
    async def _notification_worker(self):
        """Background worker to process notification queue"""
        while True:
            try:
                notification_data = await self.notification_queue.get()
                await self._send_notification(notification_data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Notification worker error: {e}")
    
    async def subscribe(
        self,
        user_id: str,
        subscription_data: Dict[str, Any],
        device_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """Subscribe a device for push notifications"""
        try:
            subscription = PushSubscription(
                endpoint=subscription_data['endpoint'],
                keys=subscription_data['keys'],
                user_id=user_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                device_info=device_info
            )
            
            # Store in database
            await self.db.push_subscriptions.update_one(
                {'endpoint': subscription.endpoint},
                {'$set': asdict(subscription)},
                upsert=True
            )
            
            # Cache subscription
            if user_id not in self.subscriptions:
                self.subscriptions[user_id] = []
            
            # Avoid duplicates
            existing = [s for s in self.subscriptions[user_id] if s.endpoint == subscription.endpoint]
            if not existing:
                self.subscriptions[user_id].append(subscription)
            
            logger.info(f"📱 Device subscribed for user {user_id}")
            
            return {
                'status': 'subscribed',
                'endpoint': subscription.endpoint[:50] + '...',
                'timestamp': subscription.created_at
            }
            
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def unsubscribe(self, user_id: str, endpoint: str) -> Dict[str, Any]:
        """Unsubscribe a device from push notifications"""
        try:
            await self.db.push_subscriptions.delete_one({'endpoint': endpoint})
            
            if user_id in self.subscriptions:
                self.subscriptions[user_id] = [
                    s for s in self.subscriptions[user_id] 
                    if s.endpoint != endpoint
                ]
            
            logger.info(f"📴 Device unsubscribed for user {user_id}")
            return {'status': 'unsubscribed'}
            
        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def set_preferences(
        self,
        user_id: str,
        preferences: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Set notification preferences for a user"""
        try:
            self.preferences[user_id] = preferences
            
            await self.db.notification_preferences.update_one(
                {'user_id': user_id},
                {'$set': {'preferences': preferences, 'updated_at': datetime.now(timezone.utc).isoformat()}},
                upsert=True
            )
            
            return {'status': 'updated', 'preferences': preferences}
            
        except Exception as e:
            logger.error(f"Set preferences error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def get_preferences(self, user_id: str) -> Dict[str, bool]:
        """Get notification preferences for a user"""
        if user_id in self.preferences:
            return self.preferences[user_id]
        
        doc = await self.db.notification_preferences.find_one({'user_id': user_id})
        if doc:
            self.preferences[user_id] = doc.get('preferences', {})
            return self.preferences[user_id]
        
        # Default: all enabled
        return {ntype: True for ntype in self.NOTIFICATION_TYPES}
    
    async def notify(
        self,
        user_id: str,
        notification_type: str,
        body: str,
        data: Optional[Dict] = None,
        actions: Optional[List[Dict]] = None
    ):
        """Queue a notification for sending"""
        # Check preferences
        prefs = await self.get_preferences(user_id)
        if not prefs.get(notification_type, True):
            logger.debug(f"Notification {notification_type} disabled for user {user_id}")
            return
        
        type_config = self.NOTIFICATION_TYPES.get(notification_type, {})
        
        notification = Notification(
            title=type_config.get('title', 'Notification'),
            body=body,
            tag=notification_type,
            data=data or {},
            actions=actions,
            require_interaction=type_config.get('require_interaction', False),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        await self.notification_queue.put({
            'user_id': user_id,
            'notification': notification
        })
        
        # Store in history
        await self.db.notification_history.insert_one({
            'user_id': user_id,
            'type': notification_type,
            'title': notification.title,
            'body': notification.body,
            'data': notification.data,
            'timestamp': notification.timestamp,
            'read': False
        })
    
    async def _send_notification(self, notification_data: Dict):
        """Send notification to all user's subscribed devices"""
        user_id = notification_data['user_id']
        notification = notification_data['notification']
        
        # Get subscriptions from cache or DB
        if user_id not in self.subscriptions:
            cursor = self.db.push_subscriptions.find({'user_id': user_id})
            subs = await cursor.to_list(100)
            self.subscriptions[user_id] = [
                PushSubscription(**{k: v for k, v in s.items() if k != '_id'})
                for s in subs
            ]
        
        subscriptions = self.subscriptions.get(user_id, [])
        
        if not subscriptions:
            logger.debug(f"No subscriptions for user {user_id}")
            return
        
        # In production, use pywebpush to send actual push notifications
        # For now, we store them for polling by the frontend
        payload = asdict(notification)
        
        for sub in subscriptions:
            try:
                # Store for SSE/polling delivery
                await self.db.pending_notifications.insert_one({
                    'user_id': user_id,
                    'endpoint': sub.endpoint,
                    'payload': payload,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'delivered': False
                })
                logger.info(f"📬 Notification queued: {notification.title}")
            except Exception as e:
                logger.error(f"Failed to queue notification: {e}")
    
    async def get_pending_notifications(self, user_id: str) -> List[Dict]:
        """Get pending notifications for a user (for polling)"""
        cursor = self.db.pending_notifications.find({
            'user_id': user_id,
            'delivered': False
        }).sort('created_at', -1).limit(50)
        
        notifications = await cursor.to_list(50)
        
        # Mark as delivered
        if notifications:
            ids = [n['_id'] for n in notifications]
            await self.db.pending_notifications.update_many(
                {'_id': {'$in': ids}},
                {'$set': {'delivered': True}}
            )
        
        return [
            {k: v for k, v in n.items() if k != '_id'}
            for n in notifications
        ]
    
    async def get_notification_history(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict]:
        """Get notification history for a user"""
        query = {'user_id': user_id}
        if unread_only:
            query['read'] = False
        
        cursor = self.db.notification_history.find(
            query, {'_id': 0}
        ).sort('timestamp', -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def mark_as_read(self, user_id: str, notification_ids: List[str] = None):
        """Mark notifications as read"""
        query = {'user_id': user_id}
        if notification_ids:
            query['_id'] = {'$in': notification_ids}
        
        await self.db.notification_history.update_many(
            query,
            {'$set': {'read': True}}
        )
    
    # Convenience methods for specific notification types
    async def notify_trade_pending(self, user_id: str, trade_data: Dict):
        """Notify about a trade pending confirmation"""
        await self.notify(
            user_id,
            'trade_pending',
            f"Trade pending: {trade_data.get('action', 'BUY')} {trade_data.get('amount', 0)} {trade_data.get('symbol', 'BTC')} @ ${trade_data.get('price', 0):,.2f}",
            data=trade_data,
            actions=[
                {'action': 'confirm', 'title': '✅ Confirm'},
                {'action': 'reject', 'title': '❌ Reject'}
            ]
        )
    
    async def notify_trade_executed(self, user_id: str, trade_data: Dict):
        """Notify about an executed trade"""
        await self.notify(
            user_id,
            'trade_executed',
            f"Executed: {trade_data.get('action', 'BUY')} {trade_data.get('amount', 0)} {trade_data.get('symbol', 'BTC')} @ ${trade_data.get('price', 0):,.2f}",
            data=trade_data
        )
    
    async def notify_stop_loss(self, user_id: str, symbol: str, price: float, pnl: float):
        """Notify about stop-loss trigger"""
        await self.notify(
            user_id,
            'stop_loss_triggered',
            f"Stop-loss triggered for {symbol} at ${price:,.2f} (P&L: ${pnl:+,.2f})",
            data={'symbol': symbol, 'price': price, 'pnl': pnl}
        )
    
    async def notify_arbitrage(self, user_id: str, opportunity: Dict):
        """Notify about arbitrage opportunity"""
        await self.notify(
            user_id,
            'arbitrage_opportunity',
            f"Arbitrage: {opportunity.get('symbol')} - Buy on {opportunity.get('buy_exchange')} @ ${opportunity.get('buy_price'):,.2f}, Sell on {opportunity.get('sell_exchange')} @ ${opportunity.get('sell_price'):,.2f} ({opportunity.get('spread_pct'):+.2f}%)",
            data=opportunity,
            actions=[
                {'action': 'execute', 'title': '⚡ Execute'},
                {'action': 'dismiss', 'title': '❌ Dismiss'}
            ]
        )
    
    async def notify_whale_alert(self, user_id: str, whale_data: Dict):
        """Notify about whale movement"""
        await self.notify(
            user_id,
            'whale_alert',
            f"🐋 {whale_data.get('amount'):,.0f} {whale_data.get('symbol')} moved ({whale_data.get('direction', 'transfer')})",
            data=whale_data
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        total_subs = await self.db.push_subscriptions.count_documents({})
        pending = await self.db.pending_notifications.count_documents({'delivered': False})
        
        return {
            'active': True,
            'total_subscriptions': total_subs,
            'pending_notifications': pending,
            'queue_size': self.notification_queue.qsize(),
            'notification_types': list(self.NOTIFICATION_TYPES.keys())
        }


# Singleton instance
_push_service: Optional[PushNotificationService] = None


def get_push_service(db=None) -> Optional[PushNotificationService]:
    """Get or create the push notification service"""
    global _push_service
    if _push_service is None and db is not None:
        _push_service = PushNotificationService(db)
    return _push_service
