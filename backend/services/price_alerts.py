from typing import Dict, Any, List
from datetime import datetime
import os

class PriceAlertService:
    """
    Manages price alerts and notifications for crypto assets
    """
    
    def __init__(self, db, notification_service=None):
        self.db = db
        self.notification_service = notification_service
        self.active_alerts = []
    
    async def create_alert(self, user_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new price alert"""
        alert = {
            'alert_id': f"alert_{datetime.now().timestamp()}",
            'user_id': user_id,
            'coin_id': alert_data.get('coin_id'),
            'condition': alert_data.get('condition', 'above'),  # above, below, percent_change
            'target_price': alert_data.get('target_price'),
            'percent_threshold': alert_data.get('percent_threshold'),
            'notification_type': alert_data.get('notification_type', 'push'),  # push, sms, both
            'active': True,
            'triggered': False,
            'triggered_at': None,
            'created_at': datetime.now().isoformat()
        }
        
        await self.db.price_alerts.insert_one(dict(alert))
        return alert
    
    async def get_user_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all alerts for a user"""
        alerts = await self.db.price_alerts.find(
            {'user_id': user_id},
            {'_id': 0}
        ).to_list(100)
        return alerts
    
    async def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert"""
        result = await self.db.price_alerts.delete_one({'alert_id': alert_id})
        return result.deleted_count > 0
    
    async def check_alerts(self, current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check all active alerts against current prices"""
        triggered = []
        
        alerts = await self.db.price_alerts.find(
            {'active': True, 'triggered': False},
            {'_id': 0}
        ).to_list(1000)
        
        for alert in alerts:
            coin_id = alert.get('coin_id', '').lower()
            current_price = current_prices.get(coin_id)
            
            if current_price is None:
                continue
            
            should_trigger = False
            condition = alert.get('condition')
            target = alert.get('target_price')
            
            if condition == 'above' and target and current_price >= target:
                should_trigger = True
            elif condition == 'below' and target and current_price <= target:
                should_trigger = True
            
            if should_trigger:
                # Mark as triggered
                await self.db.price_alerts.update_one(
                    {'alert_id': alert['alert_id']},
                    {'$set': {
                        'triggered': True,
                        'triggered_at': datetime.now().isoformat(),
                        'triggered_price': current_price
                    }}
                )
                
                # Send notification
                if self.notification_service:
                    await self._send_alert_notification(alert, current_price)
                
                triggered.append({**alert, 'triggered_price': current_price})
        
        return triggered
    
    async def _send_alert_notification(self, alert: Dict[str, Any], current_price: float):
        """Send notification for triggered alert"""
        coin_id = alert.get('coin_id', 'Unknown').upper()
        condition = alert.get('condition')
        target = alert.get('target_price', 0)
        
        title = f"🚨 Price Alert: {coin_id}"
        body = f"{coin_id} is now ${current_price:.2f} ({condition} ${target:.2f})"
        
        notification_type = alert.get('notification_type', 'push')
        
        if notification_type in ['push', 'both']:
            await self.notification_service.send_push_notification(
                title=title,
                body=body,
                data={'type': 'price_alert', 'coin_id': coin_id, 'price': current_price}
            )
        
        if notification_type in ['sms', 'both']:
            await self.notification_service.send_sms(f"{title}\n{body}")
    
    async def create_gem_alert(self, gem: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert from scanner gem detection"""
        if not self.notification_service:
            return {'success': False, 'error': 'Notification service not available'}
        
        priority = gem.get('alert_level', 'LOW')
        
        if priority == 'HIGH':
            # Send SMS for HIGH priority
            result = await self.notification_service.notify_high_priority_gem(gem)
            
            # Also send push notification
            await self.notification_service.send_push_notification(
                title=f"🚨 HIGH Priority Gem: {gem.get('symbol', 'Unknown')}",
                body=f"Score: {gem.get('match_score', 0)} | Potential: {gem.get('potential_multiplier', '?x')}",
                data={'type': 'gem_alert', 'gem': gem}
            )
            
            return result
        elif priority == 'MEDIUM':
            # Push notification only for MEDIUM
            return await self.notification_service.send_push_notification(
                title=f"⚠️ MEDIUM Priority: {gem.get('symbol', 'Unknown')}",
                body=f"Score: {gem.get('match_score', 0)} - Check scanner for details",
                data={'type': 'gem_alert', 'gem': gem}
            )
        
        return {'success': True, 'message': 'LOW priority - no notification sent'}
