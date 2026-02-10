"""
Whale Alert Service
===================
Real-time alerts for significant whale movements and market events.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


class AlertType(str, Enum):
    WHALE_ACCUMULATION = "whale_accumulation"
    WHALE_DISTRIBUTION = "whale_distribution"
    LARGE_EXCHANGE_INFLOW = "large_exchange_inflow"
    LARGE_EXCHANGE_OUTFLOW = "large_exchange_outflow"
    WHALE_TRANSACTION = "whale_transaction"
    EXCHANGE_RESERVE_CHANGE = "exchange_reserve_change"
    NETWORK_ANOMALY = "network_anomaly"
    SENTIMENT_SHIFT = "sentiment_shift"
    REGIME_CHANGE = "regime_change"
    PREDICTED_EVENT_IMMINENT = "predicted_event_imminent"


@dataclass
class WhaleAlert:
    """A whale movement alert"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    details: Dict[str, Any]
    affected_coins: List[str]
    recommended_action: str
    created_at: str
    expires_at: str
    is_read: bool = False
    is_dismissed: bool = False
    
    # Metrics
    price_at_alert: float = 0.0
    price_impact_expected: str = ""  # 'bullish', 'bearish', 'neutral'


@dataclass
class AlertThreshold:
    """Configurable alert thresholds"""
    name: str
    metric: str
    warning_threshold: float
    critical_threshold: float
    urgent_threshold: float
    cooldown_minutes: int = 30


class WhaleAlertService:
    """
    Real-time whale movement alert system with:
    1. Configurable thresholds for different alert types
    2. Multi-severity alerts (info, warning, critical, urgent)
    3. Cooldown periods to prevent alert fatigue
    4. Historical alert tracking
    5. Webhook/callback support for notifications
    """
    
    # Default alert thresholds
    DEFAULT_THRESHOLDS = {
        "exchange_inflow_btc": AlertThreshold(
            name="Exchange Inflow",
            metric="exchange_inflow_btc",
            warning_threshold=500,
            critical_threshold=1000,
            urgent_threshold=2000,
            cooldown_minutes=30
        ),
        "exchange_outflow_btc": AlertThreshold(
            name="Exchange Outflow",
            metric="exchange_outflow_btc",
            warning_threshold=500,
            critical_threshold=1000,
            urgent_threshold=2000,
            cooldown_minutes=30
        ),
        "single_tx_btc": AlertThreshold(
            name="Single Transaction",
            metric="single_tx_btc",
            warning_threshold=500,
            critical_threshold=1000,
            urgent_threshold=2500,
            cooldown_minutes=15
        ),
        "whale_wallet_change": AlertThreshold(
            name="Whale Wallet Change",
            metric="whale_wallet_change",
            warning_threshold=10,
            critical_threshold=25,
            urgent_threshold=50,
            cooldown_minutes=60
        ),
        "net_flow_btc": AlertThreshold(
            name="Net Exchange Flow",
            metric="net_flow_btc",
            warning_threshold=300,
            critical_threshold=700,
            urgent_threshold=1500,
            cooldown_minutes=30
        ),
        "accumulation_score_change": AlertThreshold(
            name="Accumulation Score Change",
            metric="accumulation_score_change",
            warning_threshold=10,
            critical_threshold=20,
            urgent_threshold=30,
            cooldown_minutes=60
        )
    }
    
    def __init__(self, db):
        self.db = db
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        self.alerts: List[WhaleAlert] = []
        self.alert_history: List[WhaleAlert] = []
        self.last_alert_time: Dict[str, datetime] = {}
        self.is_monitoring = False
        self._monitoring_task = None
        self._callbacks: List[Callable] = []
        
        # State tracking for change detection
        self._previous_state: Dict[str, Any] = {}
        self._btc_price = 95000
        
        logger.info("✅ Whale Alert Service initialized")
    
    def register_callback(self, callback: Callable):
        """Register a callback function for new alerts"""
        self._callbacks.append(callback)
    
    async def check_for_alerts(self, onchain_data: Dict[str, Any]) -> List[WhaleAlert]:
        """
        Check on-chain data against thresholds and generate alerts.
        """
        new_alerts = []
        now = datetime.now(timezone.utc)
        
        # Update price
        self._btc_price = onchain_data.get("btc_price", self._btc_price)
        
        # Check exchange flows
        exchange_flows = onchain_data.get("exchange_flows", {})
        
        # Check total inflow
        total_inflow = exchange_flows.get("total_inflow_btc", 0)
        inflow_alert = self._check_threshold(
            "exchange_inflow_btc",
            total_inflow,
            AlertType.LARGE_EXCHANGE_INFLOW,
            f"{total_inflow:.0f} BTC flowing into exchanges",
            "Large exchange inflows often precede selling pressure",
            {"total_inflow_btc": total_inflow, "total_inflow_usd": total_inflow * self._btc_price},
            "bearish"
        )
        if inflow_alert:
            new_alerts.append(inflow_alert)
        
        # Check total outflow
        total_outflow = exchange_flows.get("total_outflow_btc", 0)
        outflow_alert = self._check_threshold(
            "exchange_outflow_btc",
            total_outflow,
            AlertType.LARGE_EXCHANGE_OUTFLOW,
            f"{total_outflow:.0f} BTC leaving exchanges",
            "Large exchange outflows indicate accumulation/long-term holding",
            {"total_outflow_btc": total_outflow, "total_outflow_usd": total_outflow * self._btc_price},
            "bullish"
        )
        if outflow_alert:
            new_alerts.append(outflow_alert)
        
        # Check net flow
        net_flow = exchange_flows.get("net_flow_btc", 0)
        if abs(net_flow) > self.thresholds["net_flow_btc"].warning_threshold:
            impact = "bullish" if net_flow > 0 else "bearish"
            flow_type = "accumulation" if net_flow > 0 else "distribution"
            
            net_alert = self._check_threshold(
                "net_flow_btc",
                abs(net_flow),
                AlertType.WHALE_ACCUMULATION if net_flow > 0 else AlertType.WHALE_DISTRIBUTION,
                f"Strong {flow_type}: Net {abs(net_flow):.0f} BTC",
                f"Net exchange flow indicates {flow_type} phase",
                {"net_flow_btc": net_flow, "signal": exchange_flows.get("signal")},
                impact
            )
            if net_alert:
                new_alerts.append(net_alert)
        
        # Check whale transactions
        recent_txs = onchain_data.get("recent_large_transactions", [])
        for tx in recent_txs[:5]:  # Check top 5 recent
            tx_amount = tx.get("amount_btc", 0)
            tx_alert = self._check_threshold(
                "single_tx_btc",
                tx_amount,
                AlertType.WHALE_TRANSACTION,
                f"Large whale transaction: {tx_amount:.0f} BTC (${tx.get('amount_usd', 0):,.0f})",
                f"From {tx.get('from_type', 'unknown')} to {tx.get('to_type', 'unknown')}",
                {
                    "amount_btc": tx_amount,
                    "amount_usd": tx.get("amount_usd", 0),
                    "from_type": tx.get("from_type"),
                    "to_type": tx.get("to_type"),
                    "tx_hash": tx.get("tx_hash", "")[:20] + "..."
                },
                tx.get("impact", "neutral")
            )
            if tx_alert:
                new_alerts.append(tx_alert)
        
        # Check whale wallet changes
        whale_wallets = onchain_data.get("whale_wallets", {})
        wallet_change = whale_wallets.get("change_7d", 0)
        if abs(wallet_change) > 0:
            wallet_alert = self._check_threshold(
                "whale_wallet_change",
                abs(wallet_change),
                AlertType.WHALE_ACCUMULATION if wallet_change > 0 else AlertType.WHALE_DISTRIBUTION,
                f"Whale wallet count {'increased' if wallet_change > 0 else 'decreased'} by {abs(wallet_change)}",
                f"Total whale wallets: {whale_wallets.get('total_whale_wallets', 0)}",
                {
                    "change_7d": wallet_change,
                    "total_wallets": whale_wallets.get("total_whale_wallets", 0),
                    "total_btc": whale_wallets.get("total_whale_btc", 0)
                },
                "bullish" if wallet_change > 0 else "bearish"
            )
            if wallet_alert:
                new_alerts.append(wallet_alert)
        
        # Check accumulation score changes
        analysis = onchain_data.get("analysis", {})
        current_acc_score = analysis.get("accumulation_score", 50)
        prev_acc_score = self._previous_state.get("accumulation_score", 50)
        score_change = abs(current_acc_score - prev_acc_score)
        
        if score_change > self.thresholds["accumulation_score_change"].warning_threshold:
            direction = "up" if current_acc_score > prev_acc_score else "down"
            acc_alert = self._check_threshold(
                "accumulation_score_change",
                score_change,
                AlertType.SENTIMENT_SHIFT,
                f"Accumulation score shifted {direction}: {prev_acc_score:.0f} → {current_acc_score:.0f}",
                f"Change of {score_change:.1f} points indicates sentiment shift",
                {
                    "previous_score": prev_acc_score,
                    "current_score": current_acc_score,
                    "change": score_change,
                    "direction": direction
                },
                "bullish" if direction == "up" else "bearish"
            )
            if acc_alert:
                new_alerts.append(acc_alert)
        
        # Update previous state
        self._previous_state["accumulation_score"] = current_acc_score
        
        # Store new alerts
        for alert in new_alerts:
            self.alerts.append(alert)
            self.alert_history.append(alert)
            
            # Save to database
            await self.db.whale_alerts.insert_one(asdict(alert))
            
            # Trigger callbacks
            for callback in self._callbacks:
                try:
                    await callback(alert) if asyncio.iscoroutinefunction(callback) else callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
        
        # Cleanup old alerts (keep last 100)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        return new_alerts
    
    def _check_threshold(
        self,
        metric_name: str,
        value: float,
        alert_type: AlertType,
        title: str,
        description: str,
        details: Dict,
        impact: str
    ) -> Optional[WhaleAlert]:
        """Check if value exceeds threshold and create alert if needed"""
        threshold = self.thresholds.get(metric_name)
        if not threshold:
            return None
        
        # Check cooldown
        last_time = self.last_alert_time.get(f"{metric_name}_{alert_type.value}")
        if last_time:
            cooldown_end = last_time + timedelta(minutes=threshold.cooldown_minutes)
            if datetime.now(timezone.utc) < cooldown_end:
                return None
        
        # Determine severity
        if value >= threshold.urgent_threshold:
            severity = AlertSeverity.URGENT
        elif value >= threshold.critical_threshold:
            severity = AlertSeverity.CRITICAL
        elif value >= threshold.warning_threshold:
            severity = AlertSeverity.WARNING
        else:
            return None
        
        # Create alert
        now = datetime.now(timezone.utc)
        alert = WhaleAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            details=details,
            affected_coins=["BTC", "ETH"],
            recommended_action=self._get_recommended_action(alert_type, severity, impact),
            created_at=now.isoformat(),
            expires_at=(now + timedelta(hours=4)).isoformat(),
            price_at_alert=self._btc_price,
            price_impact_expected=impact
        )
        
        # Update cooldown
        self.last_alert_time[f"{metric_name}_{alert_type.value}"] = now
        
        logger.warning(f"🚨 WHALE ALERT [{severity.value.upper()}]: {title}")
        
        return alert
    
    def _get_recommended_action(self, alert_type: AlertType, severity: AlertSeverity, impact: str) -> str:
        """Get recommended action based on alert type and severity"""
        actions = {
            (AlertType.LARGE_EXCHANGE_INFLOW, AlertSeverity.URGENT): "Consider reducing long positions. Major sell pressure imminent.",
            (AlertType.LARGE_EXCHANGE_INFLOW, AlertSeverity.CRITICAL): "Monitor closely. Potential correction incoming.",
            (AlertType.LARGE_EXCHANGE_INFLOW, AlertSeverity.WARNING): "Be cautious with new long entries.",
            
            (AlertType.LARGE_EXCHANGE_OUTFLOW, AlertSeverity.URGENT): "Strong accumulation signal. Consider adding to positions.",
            (AlertType.LARGE_EXCHANGE_OUTFLOW, AlertSeverity.CRITICAL): "Bullish signal. Watch for continuation.",
            (AlertType.LARGE_EXCHANGE_OUTFLOW, AlertSeverity.WARNING): "Positive sign. Monitor for follow-through.",
            
            (AlertType.WHALE_ACCUMULATION, AlertSeverity.URGENT): "Major accumulation detected. Potential rally ahead.",
            (AlertType.WHALE_ACCUMULATION, AlertSeverity.CRITICAL): "Strong buying detected. Consider long positions.",
            (AlertType.WHALE_ACCUMULATION, AlertSeverity.WARNING): "Accumulation underway. Monitor trend.",
            
            (AlertType.WHALE_DISTRIBUTION, AlertSeverity.URGENT): "Major distribution detected. Consider taking profits.",
            (AlertType.WHALE_DISTRIBUTION, AlertSeverity.CRITICAL): "Strong selling detected. Reduce exposure.",
            (AlertType.WHALE_DISTRIBUTION, AlertSeverity.WARNING): "Distribution ongoing. Be cautious.",
            
            (AlertType.WHALE_TRANSACTION, AlertSeverity.URGENT): "Massive whale move. Expect volatility.",
            (AlertType.WHALE_TRANSACTION, AlertSeverity.CRITICAL): "Large whale transaction. Monitor impact.",
            (AlertType.WHALE_TRANSACTION, AlertSeverity.WARNING): "Notable whale activity. Stay alert.",
        }
        
        default_action = f"Monitor {impact} impact on market."
        return actions.get((alert_type, severity), default_action)
    
    async def get_active_alerts(self, severity_filter: Optional[str] = None) -> List[Dict]:
        """Get active (non-expired, non-dismissed) alerts"""
        now = datetime.now(timezone.utc)
        active = []
        
        for alert in self.alerts:
            if alert.is_dismissed:
                continue
            
            expires = datetime.fromisoformat(alert.expires_at.replace('Z', '+00:00'))
            if now > expires:
                continue
            
            if severity_filter and alert.severity.value != severity_filter:
                continue
            
            active.append(asdict(alert))
        
        # Sort by severity (urgent first) then by time
        severity_order = {"urgent": 0, "critical": 1, "warning": 2, "info": 3}
        active.sort(key=lambda x: (severity_order.get(x["severity"], 4), x["created_at"]), reverse=True)
        
        return active
    
    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alerts"""
        active = await self.get_active_alerts()
        
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        by_impact = defaultdict(int)
        
        for alert in active:
            by_severity[alert["severity"]] += 1
            by_type[alert["alert_type"]] += 1
            by_impact[alert["price_impact_expected"]] += 1
        
        return {
            "total_active": len(active),
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "by_impact": dict(by_impact),
            "most_recent": active[0] if active else None,
            "is_monitoring": self.is_monitoring
        }
    
    async def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.is_dismissed = True
                await self.db.whale_alerts.update_one(
                    {"alert_id": alert_id},
                    {"$set": {"is_dismissed": True}}
                )
                return True
        return False
    
    async def mark_alert_read(self, alert_id: str) -> bool:
        """Mark an alert as read"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.is_read = True
                await self.db.whale_alerts.update_one(
                    {"alert_id": alert_id},
                    {"$set": {"is_read": True}}
                )
                return True
        return False
    
    async def update_threshold(self, metric: str, warning: float = None, critical: float = None, urgent: float = None) -> Dict:
        """Update alert thresholds"""
        if metric not in self.thresholds:
            return {"error": f"Unknown metric: {metric}"}
        
        threshold = self.thresholds[metric]
        if warning is not None:
            threshold.warning_threshold = warning
        if critical is not None:
            threshold.critical_threshold = critical
        if urgent is not None:
            threshold.urgent_threshold = urgent
        
        return {
            "status": "updated",
            "metric": metric,
            "thresholds": {
                "warning": threshold.warning_threshold,
                "critical": threshold.critical_threshold,
                "urgent": threshold.urgent_threshold
            }
        }
    
    async def start_monitoring(self):
        """Start alert monitoring"""
        if self.is_monitoring:
            return {"status": "already_running"}
        
        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("🚨 Whale alert monitoring started")
        return {"status": "started"}
    
    async def stop_monitoring(self):
        """Stop alert monitoring"""
        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        return {"status": "stopped"}
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.is_monitoring:
            try:
                # Get latest on-chain data
                from services.onchain_data_service import get_onchain_service
                onchain_service = get_onchain_service(self.db)
                
                if onchain_service:
                    data = await onchain_service.get_whale_activity()
                    await self.check_for_alerts(data)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert monitoring error: {e}")
                await asyncio.sleep(60)


# Singleton instance
_whale_alert_service = None


def get_whale_alert_service(db=None):
    """Get or create whale alert service instance"""
    global _whale_alert_service
    
    if _whale_alert_service is None and db is not None:
        _whale_alert_service = WhaleAlertService(db)
    
    return _whale_alert_service
