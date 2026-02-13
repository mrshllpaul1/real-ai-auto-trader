"""
Consolidated Notification Service
=================================
Combines all notification and alerting:
- Email notifications
- Push notifications
- Price alerts
- Trading alerts
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    'NotificationService',
    'get_notification_service'
]


class NotificationService:
    """
    Unified notification service that consolidates:
    - notification_service
    - push_notification_service
    - push_notifications
    - alert_service
    - price_alerts
    - email_service
    - error_alerting_service
    """
    
    def __init__(self, db=None):
        self.db = db
        self._email = None
        self._push = None
        self._alerts = []
        self._active_price_alerts = {}
        logger.info("🔔 Notification Service initialized")
    
    @property
    def email(self):
        """Lazy load email service"""
        if self._email is None:
            try:
                from services.email_service import EmailService
                self._email = EmailService()
            except Exception as e:
                logger.warning(f"Could not load email service: {e}")
        return self._email
    
    @property
    def push(self):
        """Lazy load push notification service"""
        if self._push is None:
            try:
                from services.push_notification_service import PushNotificationService
                self._push = PushNotificationService(self.db)
            except Exception as e:
                logger.warning(f"Could not load push service: {e}")
        return self._push
    
    # === Email Notifications ===
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> Dict[str, Any]:
        """Send email notification"""
        if not self.email:
            return {"sent": False, "error": "Email service not available"}
        
        try:
            result = await self.email.send(to, subject, body, html)
            return {"sent": True, "result": result}
        except Exception as e:
            return {"sent": False, "error": str(e)}
    
    async def send_trade_notification(
        self,
        trade: Dict[str, Any],
        recipients: List[str] = None
    ) -> Dict[str, Any]:
        """Send trade execution notification"""
        subject = f"Trade Executed: {trade.get('side', 'UNKNOWN').upper()} {trade.get('symbol', 'N/A')}"
        body = f"""
Trade Details:
- Symbol: {trade.get('symbol')}
- Side: {trade.get('side')}
- Amount: {trade.get('amount')}
- Price: {trade.get('price')}
- Time: {datetime.now(timezone.utc).isoformat()}
"""
        
        if recipients:
            for recipient in recipients:
                await self.send_email(recipient, subject, body)
        
        return {"notified": True, "trade": trade}
    
    # === Push Notifications ===
    async def send_push(
        self,
        title: str,
        body: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send push notification"""
        if not self.push:
            return {"sent": False, "error": "Push service not available"}
        
        try:
            result = await self.push.send(title, body, data)
            return {"sent": True, "result": result}
        except Exception as e:
            return {"sent": False, "error": str(e)}
    
    # === Price Alerts ===
    async def create_price_alert(
        self,
        symbol: str,
        condition: str,  # "above" or "below"
        price: float,
        notification_method: str = "push"  # "push", "email", "both"
    ) -> Dict[str, Any]:
        """Create a price alert"""
        alert_id = f"{symbol}_{condition}_{price}_{datetime.now().timestamp()}"
        
        alert = {
            "id": alert_id,
            "symbol": symbol,
            "condition": condition,
            "target_price": price,
            "notification_method": notification_method,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "triggered": False
        }
        
        self._active_price_alerts[alert_id] = alert
        
        # Store in database if available
        if self.db:
            try:
                await self.db.price_alerts.insert_one(alert)
            except Exception as e:
                logger.warning(f"Could not save price alert: {e}")
        
        return {"created": True, "alert": alert}
    
    async def check_price_alerts(self, prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check and trigger price alerts"""
        triggered = []
        
        for alert_id, alert in list(self._active_price_alerts.items()):
            if alert["triggered"]:
                continue
            
            symbol = alert["symbol"]
            current_price = prices.get(symbol)
            
            if current_price is None:
                continue
            
            target = alert["target_price"]
            condition = alert["condition"]
            
            should_trigger = (
                (condition == "above" and current_price >= target) or
                (condition == "below" and current_price <= target)
            )
            
            if should_trigger:
                alert["triggered"] = True
                alert["triggered_at"] = datetime.now(timezone.utc).isoformat()
                alert["triggered_price"] = current_price
                
                # Send notification
                await self._send_price_alert_notification(alert)
                triggered.append(alert)
        
        return triggered
    
    async def _send_price_alert_notification(self, alert: Dict[str, Any]):
        """Send notification for triggered price alert"""
        title = f"Price Alert: {alert['symbol']}"
        body = f"{alert['symbol']} is now {alert['condition']} ${alert['target_price']:.2f} (Current: ${alert.get('triggered_price', 0):.2f})"
        
        method = alert.get("notification_method", "push")
        
        if method in ["push", "both"]:
            await self.send_push(title, body, {"alert": alert})
        
        if method in ["email", "both"]:
            # Would need recipient email from user settings
            pass
    
    async def delete_price_alert(self, alert_id: str) -> Dict[str, Any]:
        """Delete a price alert"""
        if alert_id in self._active_price_alerts:
            del self._active_price_alerts[alert_id]
            return {"deleted": True}
        return {"deleted": False, "error": "Alert not found"}
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active price alerts"""
        return [a for a in self._active_price_alerts.values() if not a.get("triggered")]
    
    # === In-App Notifications ===
    async def add_notification(
        self,
        type: str,
        title: str,
        message: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Add in-app notification"""
        notification = {
            "id": f"notif_{datetime.now().timestamp()}",
            "type": type,
            "title": title,
            "message": message,
            "data": data,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self._alerts.append(notification)
        
        # Keep only last 100 notifications
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]
        
        return notification
    
    def get_notifications(self, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get in-app notifications"""
        if unread_only:
            return [n for n in self._alerts if not n.get("read")]
        return self._alerts[-50:]  # Return last 50
    
    def mark_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        for n in self._alerts:
            if n.get("id") == notification_id:
                n["read"] = True
                return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "notification",
            "email": self._email is not None,
            "push": self._push is not None,
            "active_price_alerts": len(self._active_price_alerts),
            "pending_notifications": len([n for n in self._alerts if not n.get("read")]),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_notification_service = None

def get_notification_service(db=None) -> NotificationService:
    """Get or create notification service singleton"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(db)
    return _notification_service
