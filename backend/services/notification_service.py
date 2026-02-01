import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class NotificationService:
    """
    Handles push notifications (browser) and SMS notifications (Twilio)
    for trade completions and high-priority alerts
    """
    
    def __init__(self, db):
        self.db = db
        self.twilio_client = None
        self.twilio_phone = None
        self.user_phone = os.getenv('USER_PHONE_NUMBER', '2104412761')
        
        # Initialize Twilio
        self._init_twilio()
        
        # Track sent notifications to avoid spam
        self.recent_notifications = []
        self.notification_cooldown = 300  # 5 minutes between same type notifications
    
    def _init_twilio(self):
        """Initialize Twilio client"""
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            
            if account_sid and auth_token and self.twilio_phone:
                from twilio.rest import Client
                self.twilio_client = Client(account_sid, auth_token)
                print("✅ Twilio SMS notifications enabled")
            else:
                print("⚠️ Twilio credentials not configured - SMS disabled")
        except ImportError:
            print("⚠️ Twilio library not installed - SMS disabled")
        except Exception as e:
            print(f"⚠️ Twilio init error: {e}")
    
    async def send_sms(self, message: str, phone_number: str = None) -> Dict[str, Any]:
        """Send SMS notification via Twilio"""
        if not self.twilio_client:
            return {'success': False, 'error': 'Twilio not configured'}
        
        target_phone = phone_number or self.user_phone
        
        # Format phone number (ensure E.164 format)
        if not target_phone.startswith('+'):
            target_phone = '+1' + target_phone  # Assume US number
        
        try:
            sms = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=target_phone
            )
            
            # Log notification
            await self._log_notification('sms', message, target_phone, sms.sid)
            
            print(f"📱 SMS sent to {target_phone}: {message[:50]}...")
            return {'success': True, 'sid': sms.sid}
        except Exception as e:
            print(f"❌ SMS error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def send_push_notification(self, title: str, body: str, data: Dict = None) -> Dict[str, Any]:
        """
        Create push notification payload for browser/PWA
        The actual push is handled by the frontend service worker
        """
        notification = {
            'id': str(datetime.now().timestamp()),
            'title': title,
            'body': body,
            'data': data or {},
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        # Store notification in database for frontend to poll
        await self.db.notifications.insert_one(dict(notification))
        
        # Log notification
        await self._log_notification('push', f"{title}: {body}", None, notification['id'])
        
        print(f"🔔 Push notification: {title}")
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
        else:
            title = f"🚀 Trade Opened: {symbol}"
            body = f"{mode} {action} at ${entry_price:.4f}"
        
        # Send push notification
        result = await self.send_push_notification(
            title=title,
            body=body,
            data={
                'type': 'trade_completed',
                'trade_id': trade.get('trade_id'),
                'symbol': symbol,
                'profit_pct': profit_pct
            }
        )
        
        return result
    
    async def notify_high_priority_gem(self, gem: Dict[str, Any], phone_number: str = None) -> Dict[str, Any]:
        """Send SMS notification for HIGH priority gems"""
        symbol = gem.get('symbol', 'Unknown')
        score = gem.get('match_score', 0)
        potential = gem.get('potential_multiplier', '?x')
        price = gem.get('current_price', 0)
        
        signals = gem.get('matching_signals', [])
        signal_names = [s.get('signal', s) if isinstance(s, dict) else s for s in signals[:3]]
        signals_str = ', '.join(signal_names)
        
        message = f"🚨 HIGH ALERT: {symbol}\n" \
                  f"Score: {score} | Potential: {potential}\n" \
                  f"Price: ${price:.6f}\n" \
                  f"Signals: {signals_str}\n" \
                  f"Check app for details!"
        
        # Check cooldown to avoid spam
        cooldown_key = f"gem_{symbol}"
        if self._check_cooldown(cooldown_key):
            print(f"⏳ Skipping SMS for {symbol} - in cooldown")
            return {'success': False, 'error': 'In cooldown period'}
        
        # Send SMS
        result = await self.send_sms(message, phone_number)
        
        if result.get('success'):
            self._set_cooldown(cooldown_key)
        
        return result
    
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
                'sms_enabled': True,
                'sms_phone': self.user_phone,
                'notify_trade_open': True,
                'notify_trade_close': True,
                'notify_high_alerts': True,
                'notify_medium_alerts': False
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
