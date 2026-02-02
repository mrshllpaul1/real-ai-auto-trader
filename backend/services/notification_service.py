import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class NotificationService:
    """
    Handles push notifications (browser/PWA) with vibration support
    for trade completions and high-priority alerts
    """
    
    def __init__(self, db):
        self.db = db
        
        # Track sent notifications to avoid spam
        self.recent_notifications = []
        self.notification_cooldown = 300  # 5 minutes between same type notifications
    
    async def send_push_notification(
        self, 
        title: str, 
        body: str, 
        data: Dict = None,
        priority: str = 'normal',
        vibrate: bool = True
    ) -> Dict[str, Any]:
        """
        Create push notification payload for browser/PWA with vibration
        The actual push is handled by the frontend service worker
        
        Args:
            title: Notification title
            body: Notification body text
            data: Additional data payload
            priority: 'high', 'normal', or 'low'
            vibrate: Enable vibration pattern
        """
        # Vibration patterns (in milliseconds)
        vibration_patterns = {
            'high': [200, 100, 200, 100, 400],  # Urgent pattern
            'normal': [200, 100, 200],          # Standard pattern
            'low': [100]                        # Subtle pattern
        }
        
        notification = {
            'id': str(datetime.now().timestamp()),
            'title': title,
            'body': body,
            'data': data or {},
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'priority': priority,
            'vibrate': vibrate,
            'vibration_pattern': vibration_patterns.get(priority, vibration_patterns['normal'])
        }
        
        # Store notification in database for frontend to poll
        await self.db.notifications.insert_one(dict(notification))
        
        # Log notification
        await self._log_notification('push', f"{title}: {body}", None, notification['id'])
        
        print(f"🔔 Push notification ({priority}): {title}")
        return {'success': True, 'notification': notification}
    
    async def notify_trade_completed(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Send push notification when a trade completes"""
        symbol = trade.get('symbol', 'Unknown')
        action = trade.get('action', 'TRADE')
        profit_pct = trade.get('profit_pct')
        close_reason = trade.get('close_reason', 'manual')
        entry_price = trade.get('entry_price', 0)
        exit_price = trade.get('exit_price', 0)
        mode = trade.get('mode', 'paper').upper()
        
        # Build notification message
        if profit_pct is not None:
            emoji = "🟢" if profit_pct > 0 else "🔴"
            profit_str = f"{'+' if profit_pct > 0 else ''}{profit_pct:.2f}%"
            title = f"{emoji} Trade Closed: {symbol}"
            body = f"{mode} {action} closed ({close_reason})\n" \
                   f"Entry: ${entry_price:.4f} → Exit: ${exit_price:.4f}\n" \
                   f"P/L: {profit_str}"
            # High priority if significant profit or loss
            priority = 'high' if abs(profit_pct) > 10 else 'normal'
        else:
            title = f"🚀 Trade Opened: {symbol}"
            body = f"{mode} {action} at ${entry_price:.4f}"
            priority = 'normal'
        
        # Send push notification with vibration
        result = await self.send_push_notification(
            title=title,
            body=body,
            data={
                'type': 'trade_completed',
                'trade_id': trade.get('trade_id'),
                'symbol': symbol,
                'profit_pct': profit_pct
            },
            priority=priority,
            vibrate=True
        )
        
        return result
    
    async def notify_high_priority_gem(self, gem: Dict[str, Any]) -> Dict[str, Any]:
        """Send HIGH priority push notification for gems (with urgent vibration)"""
        symbol = gem.get('symbol', 'Unknown')
        score = gem.get('match_score', 0)
        potential = gem.get('potential_multiplier', '?x')
        price = gem.get('current_price', 0)
        
        signals = gem.get('matching_signals', [])
        signal_names = [s.get('signal', s) if isinstance(s, dict) else s for s in signals[:3]]
        signals_str = ', '.join(signal_names)
        
        title = f"🚨 HIGH ALERT: {symbol}"
        body = f"Score: {score} | Potential: {potential}\n" \
               f"Price: ${price:.6f}\n" \
               f"Signals: {signals_str}"
        
        # Check cooldown to avoid spam
        cooldown_key = f"gem_{symbol}"
        if self._check_cooldown(cooldown_key):
            print(f"⏳ Skipping notification for {symbol} - in cooldown")
            return {'success': False, 'error': 'In cooldown period'}
        
        # Send HIGH priority push notification with urgent vibration
        result = await self.send_push_notification(
            title=title,
            body=body,
            data={
                'type': 'high_priority_gem',
                'symbol': symbol,
                'score': score,
                'potential': potential
            },
            priority='high',
            vibrate=True
        )
        
        if result.get('success'):
            self._set_cooldown(cooldown_key)
        
        return result
    
    async def notify_ai_discovery(self, coin: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification when AI discovers a new coin"""
        symbol = coin.get('symbol', 'Unknown')
        reason = coin.get('reason', 'Promising potential')
        potential_score = coin.get('potential_score', 0)
        
        title = f"🆕 AI Discovered: {symbol}"
        body = f"Added to universe!\n" \
               f"Potential: {potential_score}%\n" \
               f"Reason: {reason[:100]}"
        
        return await self.send_push_notification(
            title=title,
            body=body,
            data={
                'type': 'ai_discovery',
                'symbol': symbol,
                'potential_score': potential_score
            },
            priority='high',
            vibrate=True
        )
    
    def _check_cooldown(self, key: str) -> bool:
        """Check if a notification type is in cooldown"""
        now = datetime.now().timestamp()
        for notif in self.recent_notifications:
            if notif['key'] == key and (now - notif['time']) < self.notification_cooldown:
                return True
        return False
    
    def _set_cooldown(self, key: str):
        """Set cooldown for a notification type"""
        now = datetime.now().timestamp()
        # Clean old entries
        self.recent_notifications = [
            n for n in self.recent_notifications 
            if (now - n['time']) < self.notification_cooldown
        ]
        self.recent_notifications.append({'key': key, 'time': now})
    
    async def _log_notification(self, notif_type: str, message: str, recipient: str, ref_id: str):
        """Log notification to database"""
        log = {
            'type': notif_type,
            'message': message[:500],
            'recipient': recipient,
            'ref_id': ref_id,
            'timestamp': datetime.now().isoformat()
        }
        await self.db.notification_logs.insert_one(log)
    
    async def get_unread_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get unread push notifications"""
        notifications = await self.db.notifications.find(
            {'read': False},
            {'_id': 0}
        ).sort('timestamp', -1).limit(limit).to_list(limit)
        return notifications
    
    async def mark_notification_read(self, notification_id: str):
        """Mark a notification as read"""
        await self.db.notifications.update_one(
            {'id': notification_id},
            {'$set': {'read': True}}
        )
    
    async def mark_all_read(self):
        """Mark all notifications as read"""
        await self.db.notifications.update_many(
            {'read': False},
            {'$set': {'read': True}}
        )
    
    async def get_notification_settings(self, user_id: str = 'default') -> Dict[str, Any]:
        """Get user notification preferences"""
        settings = await self.db.notification_settings.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
        
        if not settings:
            settings = {
                'user_id': user_id,
                'push_enabled': True,
                'vibration_enabled': True,
                'notify_trade_open': True,
                'notify_trade_close': True,
                'notify_high_alerts': True,
                'notify_medium_alerts': False,
                'notify_ai_discoveries': True
            }
            await self.db.notification_settings.insert_one(dict(settings))
        
        return settings
    
    async def update_notification_settings(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update notification preferences"""
        await self.db.notification_settings.update_one(
            {'user_id': user_id},
            {'$set': updates},
            upsert=True
        )
        return await self.get_notification_settings(user_id)
