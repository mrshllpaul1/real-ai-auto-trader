"""
Real-time Alert Service
Sends notifications for gem detections, trade executions, and position updates.
Supports in-app alerts, email (Resend), and SMS (Twilio).
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
    """
    
    def __init__(self, db):
        self.db = db
        self.resend_key = os.getenv('RESEND_API_KEY')
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
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
            channels: List of channels (app, email, sms). Defaults to ['app']
        """
        if channels is None:
            channels = ['app']
        
        alert = {
            'title': title,
            'message': message,
            'type': alert_type,
            'priority': priority,
            'channels': channels,
            'created_at': datetime.now().isoformat(),
            'read': False
        }
        
        results = {'app': False, 'email': False, 'sms': False}
        
        # Always store in app
        if 'app' in channels:
            await self.db.gem_alerts.insert_one(alert)
            results['app'] = True
        
        # Send email if configured
        if 'email' in channels and self.resend_key and self.alert_email:
            try:
                await self._send_email(title, message)
                results['email'] = True
            except Exception as e:
                print(f"Email alert error: {e}")
        
        # Send SMS if configured and high priority
        if 'sms' in channels and priority in ['high', 'critical']:
            if self.twilio_sid and self.twilio_token and self.twilio_phone:
                try:
                    await self._send_sms(f"{title}\n{message}")
                    results['sms'] = True
                except Exception as e:
                    print(f"SMS alert error: {e}")
        
        return {
            'success': any(results.values()),
            'results': results,
            'alert_id': str(alert.get('_id', ''))
        }
    
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
    
    async def _send_sms(self, message: str):
        """Send SMS via Twilio"""
        from twilio.rest import Client
        
        client = Client(self.twilio_sid, self.twilio_token)
        
        # Get user phone from settings
        user_phone = os.getenv('USER_PHONE')
        if not user_phone:
            return False
        
        client.messages.create(
            body=message[:160],  # SMS limit
            from_=self.twilio_phone,
            to=user_phone
        )
        return True
    
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
            channels=['app', 'email'] if priority == 'high' else ['app']
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
            channels=['app', 'email', 'sms']
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
