"""
Real-time Alert Service
Sends push notifications for gem detections, trade executions, and position updates.
Supports in-app alerts, email (Resend), and push notifications with vibration.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class AlertService:
    """
    Multi-channel alert service for trading notifications.
    Uses push notifications with vibration instead of SMS.
    """
    
    def __init__(self, db):
        self.db = db
        self.resend_key = os.getenv('RESEND_API_KEY')
        self.alert_email = os.getenv('ALERT_EMAIL')
    
    async def send_alert(
        self,
        title: str,
        message: str,
        alert_type: str = "info",
        priority: str = "normal",
        channels: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send alert through configured channels.
        
        Args:
            title: Alert title
            message: Alert message
            alert_type: Type of alert (gem_detected, execution, position_close, etc.)
            priority: Alert priority (low, normal, high, critical)
            channels: List of channels (app, email, push). Defaults to ['app', 'push']
        """
        if channels is None:
            channels = ['app', 'push']
        
        alert = {
            'title': title,
            'message': message,
            'type': alert_type,
            'priority': priority,
            'channels': channels,
            'created_at': datetime.now().isoformat(),
            'read': False,
            'vibrate': priority in ['high', 'critical']
        }
        
        results = {'app': False, 'email': False, 'push': False}
        
        # Always store in app
        if 'app' in channels:
            await self.db.gem_alerts.insert_one(alert)
            results['app'] = True
        
        # Send push notification with vibration
        if 'push' in channels:
            push_result = await self._send_push_notification(
                title=title,
                message=message,
                priority=priority,
                alert_type=alert_type
            )
            results['push'] = push_result
        
        # Send email if configured
        if 'email' in channels and self.resend_key and self.alert_email:
            try:
                await self._send_email(title, message)
                results['email'] = True
            except Exception as e:
                print(f"Email alert error: {e}")
        
        return {
            'success': any(results.values()),
            'results': results,
            'alert_id': str(alert.get('_id', ''))
        }
    
    async def _send_push_notification(
        self, 
        title: str, 
        message: str, 
        priority: str,
        alert_type: str
    ) -> bool:
        """Send push notification with vibration"""
        # Vibration patterns (in milliseconds)
        vibration_patterns = {
            'critical': [200, 100, 200, 100, 200, 100, 400],  # Urgent pattern
            'high': [200, 100, 200, 100, 400],
            'normal': [200, 100, 200],
            'low': [100]
        }
        
        notification = {
            'id': str(datetime.now().timestamp()),
            'title': title,
            'body': message[:500],
            'data': {'type': alert_type},
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'priority': priority,
            'vibrate': priority in ['high', 'critical'],
            'vibration_pattern': vibration_patterns.get(priority, vibration_patterns['normal'])
        }
        
        try:
            await self.db.notifications.insert_one(dict(notification))
            print(f"🔔 Push alert ({priority}): {title}")
            return True
        except Exception as e:
            print(f"Push notification error: {e}")
            return False
    
    async def _send_email(self, subject: str, body: str):
        """Send email via Resend"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.resend_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": os.getenv('SENDER_EMAIL', 'onboarding@resend.dev'),
                    "to": [self.alert_email],
                    "subject": f"🤖 AI Trading: {subject}",
                    "text": body
                }
            )
            return response.status_code == 200
    
    async def send_gem_alert(self, gem: Dict[str, Any]):
        """Send alert for detected gem"""
        score = gem.get('total_score', 0)
        signal = gem.get('signal', '')
        coin_id = gem.get('coin_id', 'Unknown')
        
        # Determine priority based on score
        if score >= 80:
            priority = 'high'
        elif score >= 65:
            priority = 'normal'
        else:
            priority = 'low'
        
        channels = ['app', 'push']
        if priority == 'high':
            channels.append('email')
        
        await self.send_alert(
            title=f"💎 Gem Detected: {coin_id.upper()}",
            message=f"""
{signal}

Score: {score}/100
Volatility: {gem.get('scores', {}).get('volatility', 0)}
Momentum: {gem.get('scores', {}).get('momentum', 0)}
Volume Spike: {gem.get('scores', {}).get('volume_spike', 0)}

Price: ${gem.get('metrics', {}).get('current_price', 0):.6f}
Week Change: {gem.get('metrics', {}).get('week_change_pct', 0):.2f}%
            """,
            alert_type='gem_detected',
            priority=priority,
            channels=channels
        )
    
    async def send_moonshot_alert(self, trade: Dict[str, Any]):
        """Send alert for 100%+ gain"""
        await self.send_alert(
            title=f"🚀 MOONSHOT: {trade.get('coin_id', '').upper()}",
            message=f"""
MASSIVE GAIN DETECTED!

Coin: {trade.get('coin_id')}
P/L: +{trade.get('pnl_pct', 0):.2f}%
Profit: ${trade.get('pnl_usd', 0):,.2f}

Entry: ${trade.get('entry_price', 0):.6f}
Exit: ${trade.get('exit_price', 0):.6f}
            """,
            alert_type='moonshot',
            priority='critical',
            channels=['app', 'push', 'email']
        )
    
    async def get_unread_alerts(self, limit: int = 50) -> List[Dict]:
        """Get unread alerts"""
        alerts = await self.db.gem_alerts.find(
            {'read': False},
            {'_id': 0}
        ).sort('created_at', -1).limit(limit).to_list(limit)
        
        return alerts
    
    async def mark_alerts_read(self, alert_ids: List[str] = None):
        """Mark alerts as read"""
        if alert_ids:
            await self.db.gem_alerts.update_many(
                {'_id': {'$in': alert_ids}},
                {'$set': {'read': True}}
            )
        else:
            # Mark all as read
            await self.db.gem_alerts.update_many(
                {'read': False},
                {'$set': {'read': True}}
            )
