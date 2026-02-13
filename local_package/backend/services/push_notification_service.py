"""
Push Notification Service
Real-time alerts for trading events, gems, and regime changes
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Notification types"""
    GEM_ALERT = "gem_alert"
    REGIME_CHANGE = "regime_change"
    PRICE_ALERT = "price_alert"
    TRADE_EXECUTED = "trade_executed"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
    TAKE_PROFIT_TRIGGERED = "take_profit_triggered"
    WHALE_ALERT = "whale_alert"
    NEWS_ALERT = "news_alert"
    STRATEGY_SIGNAL = "strategy_signal"
    SYSTEM_ALERT = "system_alert"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PushNotificationService:
    """
    Push notification service for trading alerts:
    - Gem discovery alerts
    - Market regime changes
    - Price alerts
    - Trade execution notifications
    - Stop-loss/Take-profit triggers
    - Whale activity alerts
    - News alerts
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.subscribers = {}  # session_id -> preferences
        self.pending_notifications = []  # Queue for SSE
        
        # Default notification preferences
        self.default_preferences = {
            NotificationType.GEM_ALERT.value: True,
            NotificationType.REGIME_CHANGE.value: True,
            NotificationType.PRICE_ALERT.value: True,
            NotificationType.TRADE_EXECUTED.value: True,
            NotificationType.STOP_LOSS_TRIGGERED.value: True,
            NotificationType.TAKE_PROFIT_TRIGGERED.value: True,
            NotificationType.WHALE_ALERT.value: True,
            NotificationType.NEWS_ALERT.value: False,
            NotificationType.STRATEGY_SIGNAL.value: True,
            NotificationType.SYSTEM_ALERT.value: True
        }
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Dict = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        target_sessions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send a push notification
        
        Args:
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data payload
            priority: Notification priority
            target_sessions: Specific sessions to notify (None = all)
            
        Returns:
            Notification result with ID
        """
        try:
            notification = {
                'type': notification_type.value,
                'title': title,
                'message': message,
                'data': data or {},
                'priority': priority.value,
                'created_at': datetime.now(timezone.utc),
                'read': False,
                'dismissed': False
            }
            
            # Store in database
            result = await self.db.notifications.insert_one(notification)
            notification['_id'] = str(result.inserted_id)
            
            # Add to pending queue for real-time delivery
            self.pending_notifications.append({
                'id': str(result.inserted_id),
                'type': notification_type.value,
                'title': title,
                'message': message,
                'priority': priority.value,
                'timestamp': notification['created_at'].isoformat()
            })
            
            # Keep only last 100 pending
            if len(self.pending_notifications) > 100:
                self.pending_notifications = self.pending_notifications[-100:]
            
            logger.info(f"📢 Notification sent: [{priority.value.upper()}] {title}")
            
            return {
                'success': True,
                'notification_id': str(result.inserted_id),
                'type': notification_type.value,
                'priority': priority.value
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {'success': False, 'error': str(e)}
    
    async def send_gem_alert(
        self,
        coin_id: str,
        coin_symbol: str,
        gem_score: float,
        prediction: str,
        price: float = None,
        potential_return: float = None
    ) -> Dict[str, Any]:
        """Send gem discovery alert"""
        priority = NotificationPriority.HIGH if gem_score > 80 else NotificationPriority.MEDIUM
        
        message = f"🔮 {prediction.upper()} potential detected!"
        if potential_return:
            message += f" Est. return: {potential_return:.0f}%"
        
        return await self.send_notification(
            notification_type=NotificationType.GEM_ALERT,
            title=f"💎 Gem Alert: {coin_symbol}",
            message=message,
            data={
                'coin_id': coin_id,
                'symbol': coin_symbol,
                'gem_score': gem_score,
                'prediction': prediction,
                'price': price,
                'potential_return': potential_return
            },
            priority=priority
        )
    
    async def send_regime_change_alert(
        self,
        old_regime: str,
        new_regime: str,
        confidence: float,
        implications: str = None
    ) -> Dict[str, Any]:
        """Send market regime change alert"""
        # Determine priority based on regime change severity
        if new_regime in ['strong_bear', 'strong_bull']:
            priority = NotificationPriority.HIGH
        elif old_regime != new_regime:
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW
        
        return await self.send_notification(
            notification_type=NotificationType.REGIME_CHANGE,
            title=f"📊 Market Regime Change",
            message=f"Market shifted from {old_regime.upper()} to {new_regime.upper()} ({confidence:.1f}% confidence)",
            data={
                'old_regime': old_regime,
                'new_regime': new_regime,
                'confidence': confidence,
                'implications': implications
            },
            priority=priority
        )
    
    async def send_price_alert(
        self,
        coin_symbol: str,
        alert_type: str,  # 'above', 'below', 'change'
        current_price: float,
        target_price: float = None,
        change_pct: float = None
    ) -> Dict[str, Any]:
        """Send price alert"""
        if alert_type == 'above':
            message = f"Price crossed above ${target_price:,.2f}"
            priority = NotificationPriority.MEDIUM
        elif alert_type == 'below':
            message = f"Price dropped below ${target_price:,.2f}"
            priority = NotificationPriority.HIGH
        else:
            message = f"Price changed {change_pct:+.1f}%"
            priority = NotificationPriority.HIGH if abs(change_pct) > 10 else NotificationPriority.MEDIUM
        
        return await self.send_notification(
            notification_type=NotificationType.PRICE_ALERT,
            title=f"💰 {coin_symbol} Price Alert",
            message=message,
            data={
                'symbol': coin_symbol,
                'current_price': current_price,
                'target_price': target_price,
                'change_pct': change_pct
            },
            priority=priority
        )
    
    async def send_trade_notification(
        self,
        action: str,  # 'buy', 'sell'
        coin_symbol: str,
        amount: float,
        price: float,
        is_paper: bool = True,
        pnl: float = None,
        pnl_pct: float = None
    ) -> Dict[str, Any]:
        """Send trade execution notification"""
        if action == 'buy':
            emoji = "🟢"
            title = f"{emoji} Bought {coin_symbol}"
            message = f"{'[PAPER] ' if is_paper else ''}Bought ${amount:.2f} at ${price:,.2f}"
        else:
            emoji = "🔴"
            title = f"{emoji} Sold {coin_symbol}"
            pnl_str = f" | P&L: {pnl_pct:+.1f}%" if pnl_pct else ""
            message = f"{'[PAPER] ' if is_paper else ''}Sold ${amount:.2f} at ${price:,.2f}{pnl_str}"
        
        return await self.send_notification(
            notification_type=NotificationType.TRADE_EXECUTED,
            title=title,
            message=message,
            data={
                'action': action,
                'symbol': coin_symbol,
                'amount': amount,
                'price': price,
                'is_paper': is_paper,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            },
            priority=NotificationPriority.MEDIUM
        )
    
    async def send_stop_loss_alert(
        self,
        coin_symbol: str,
        trigger_price: float,
        stop_price: float,
        loss_pct: float
    ) -> Dict[str, Any]:
        """Send stop-loss trigger alert"""
        return await self.send_notification(
            notification_type=NotificationType.STOP_LOSS_TRIGGERED,
            title=f"🛑 Stop-Loss Triggered: {coin_symbol}",
            message=f"Position closed at ${trigger_price:,.2f} (Loss: {loss_pct:.1f}%)",
            data={
                'symbol': coin_symbol,
                'trigger_price': trigger_price,
                'stop_price': stop_price,
                'loss_pct': loss_pct
            },
            priority=NotificationPriority.HIGH
        )
    
    async def send_take_profit_alert(
        self,
        coin_symbol: str,
        trigger_price: float,
        target_price: float,
        profit_pct: float
    ) -> Dict[str, Any]:
        """Send take-profit trigger alert"""
        return await self.send_notification(
            notification_type=NotificationType.TAKE_PROFIT_TRIGGERED,
            title=f"🎯 Take-Profit Triggered: {coin_symbol}",
            message=f"Position closed at ${trigger_price:,.2f} (Profit: +{profit_pct:.1f}%)",
            data={
                'symbol': coin_symbol,
                'trigger_price': trigger_price,
                'target_price': target_price,
                'profit_pct': profit_pct
            },
            priority=NotificationPriority.HIGH
        )
    
    async def send_whale_alert(
        self,
        coin_symbol: str,
        action: str,  # 'accumulation', 'distribution'
        amount_usd: float,
        significance: str
    ) -> Dict[str, Any]:
        """Send whale activity alert"""
        emoji = "🐋"
        if action == 'accumulation':
            message = f"Large accumulation detected: ${amount_usd:,.0f}"
            priority = NotificationPriority.MEDIUM
        else:
            message = f"Large distribution detected: ${amount_usd:,.0f}"
            priority = NotificationPriority.HIGH
        
        return await self.send_notification(
            notification_type=NotificationType.WHALE_ALERT,
            title=f"{emoji} Whale Alert: {coin_symbol}",
            message=message,
            data={
                'symbol': coin_symbol,
                'action': action,
                'amount_usd': amount_usd,
                'significance': significance
            },
            priority=priority
        )
    
    async def send_strategy_signal(
        self,
        strategy_name: str,
        signal_type: str,  # 'entry', 'exit'
        coin_symbol: str,
        confidence: float,
        reason: str = None
    ) -> Dict[str, Any]:
        """Send custom strategy signal alert"""
        if signal_type == 'entry':
            title = f"🟢 {strategy_name}: Entry Signal"
            message = f"Entry signal for {coin_symbol} ({confidence:.0f}% confidence)"
        else:
            title = f"🔴 {strategy_name}: Exit Signal"
            message = f"Exit signal for {coin_symbol}"
        
        if reason:
            message += f" - {reason}"
        
        return await self.send_notification(
            notification_type=NotificationType.STRATEGY_SIGNAL,
            title=title,
            message=message,
            data={
                'strategy_name': strategy_name,
                'signal_type': signal_type,
                'symbol': coin_symbol,
                'confidence': confidence,
                'reason': reason
            },
            priority=NotificationPriority.HIGH if confidence > 80 else NotificationPriority.MEDIUM
        )
    
    async def get_notifications(
        self,
        limit: int = 50,
        unread_only: bool = False,
        notification_types: List[str] = None
    ) -> List[Dict]:
        """Get notifications"""
        query = {}
        
        if unread_only:
            query['read'] = False
        
        if notification_types:
            query['type'] = {'$in': notification_types}
        
        cursor = self.db.notifications.find(
            query,
            {'_id': 0}
        ).sort('created_at', -1).limit(limit)
        
        notifications = await cursor.to_list(length=limit)
        
        # Convert datetime to ISO string
        for n in notifications:
            if 'created_at' in n:
                n['created_at'] = n['created_at'].isoformat()
        
        return notifications
    
    async def mark_as_read(self, notification_ids: List[str]) -> Dict[str, Any]:
        """Mark notifications as read"""
        from bson import ObjectId
        
        try:
            object_ids = [ObjectId(nid) for nid in notification_ids]
            result = await self.db.notifications.update_many(
                {'_id': {'$in': object_ids}},
                {'$set': {'read': True, 'read_at': datetime.now(timezone.utc)}}
            )
            
            return {
                'success': True,
                'marked_count': result.modified_count
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def mark_all_as_read(self) -> Dict[str, Any]:
        """Mark all notifications as read"""
        result = await self.db.notifications.update_many(
            {'read': False},
            {'$set': {'read': True, 'read_at': datetime.now(timezone.utc)}}
        )
        
        return {
            'success': True,
            'marked_count': result.modified_count
        }
    
    async def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return await self.db.notifications.count_documents({'read': False})
    
    async def dismiss_notification(self, notification_id: str) -> Dict[str, Any]:
        """Dismiss a notification"""
        from bson import ObjectId
        
        try:
            result = await self.db.notifications.update_one(
                {'_id': ObjectId(notification_id)},
                {'$set': {'dismissed': True, 'dismissed_at': datetime.now(timezone.utc)}}
            )
            
            return {
                'success': result.modified_count > 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_pending_notifications(self) -> List[Dict]:
        """Get pending notifications for SSE delivery"""
        pending = self.pending_notifications.copy()
        self.pending_notifications.clear()
        return pending
    
    async def set_preferences(self, session_id: str, preferences: Dict) -> Dict[str, Any]:
        """Set notification preferences for a session"""
        self.subscribers[session_id] = {
            **self.default_preferences,
            **preferences
        }
        
        return {
            'success': True,
            'preferences': self.subscribers[session_id]
        }
    
    def get_preferences(self, session_id: str = 'default') -> Dict:
        """Get notification preferences for a session"""
        return self.subscribers.get(session_id, self.default_preferences)


# Singleton
_notification_service = None

def get_notification_service(db: AsyncIOMotorDatabase = None) -> PushNotificationService:
    global _notification_service
    if _notification_service is None and db is not None:
        _notification_service = PushNotificationService(db)
    return _notification_service
