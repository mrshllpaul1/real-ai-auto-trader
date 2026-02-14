"""
Error Alerting Service
Monitors error trends and sends email alerts via Resend when thresholds are exceeded
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Try to import resend
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend library not available - email alerts disabled")


class ErrorAlertingService:
    """Service to monitor errors and send alerts when thresholds are exceeded"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.config_collection = db.alert_config
        self.alert_history_collection = db.alert_history
        
        # Default thresholds
        self.default_config = {
            "resend_api_key": None,
            "sender_email": "alerts@yourdomain.com",
            "recipient_emails": [],
            "enabled": False,
            "thresholds": {
                "errors_per_hour": 50,
                "critical_errors_trigger": 5,
                "error_rate_increase_pct": 200  # 200% increase from baseline
            },
            "cooldown_minutes": 30,  # Don't send alerts more often than this
            "alert_on_critical": True,
            "alert_on_threshold": True,
            "include_error_details": True
        }
    
    async def get_config(self) -> Dict[str, Any]:
        """Get current alerting configuration"""
        config = await self.config_collection.find_one(
            {"_id": "error_alerting"},
            {"_id": 0}
        )
        if not config:
            return self.default_config.copy()
        return {**self.default_config, **config}
    
    async def save_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save alerting configuration"""
        config["updated_at"] = datetime.now(timezone.utc)
        await self.config_collection.update_one(
            {"_id": "error_alerting"},
            {"$set": config},
            upsert=True
        )
        return await self.get_config()
    
    async def test_connection(self, api_key: str, recipient_email: str) -> Dict[str, Any]:
        """Test Resend connection by sending a test email"""
        if not RESEND_AVAILABLE:
            return {"success": False, "error": "Resend library not installed"}
        
        try:
            resend.api_key = api_key
            
            params = {
                "from": "onboarding@resend.dev",
                "to": [recipient_email],
                "subject": "Tethys AI - Error Alerting Test",
                "html": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #9D00FF;">✅ Connection Successful!</h2>
                    <p>Your Resend API key is configured correctly.</p>
                    <p>You will receive error alerts at this email address when thresholds are exceeded.</p>
                    <hr style="border: 1px solid #333;">
                    <p style="color: #666; font-size: 12px;">Sent from Tethys AI Trading Platform</p>
                </div>
                """
            }
            
            result = await asyncio.to_thread(resend.Emails.send, params)
            return {
                "success": True,
                "email_id": result.get("id"),
                "message": f"Test email sent to {recipient_email}"
            }
        except Exception as e:
            logger.error(f"Failed to send test email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def check_thresholds(self) -> Dict[str, Any]:
        """Check if any alert thresholds have been exceeded"""
        config = await self.get_config()
        
        if not config.get("enabled"):
            return {"triggered": False, "reason": "Alerting disabled"}
        
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        
        # Get error counts from frontend_errors collection
        errors_collection = self.db.frontend_errors
        
        # Count errors in last hour
        errors_last_hour = await errors_collection.count_documents({
            "timestamp": {"$gte": hour_ago}
        })
        
        # Count critical errors in last hour
        critical_errors = await errors_collection.count_documents({
            "timestamp": {"$gte": hour_ago},
            "severity": "CRITICAL"
        })
        
        # Check thresholds
        thresholds = config.get("thresholds", self.default_config["thresholds"])
        triggers = []
        
        if errors_last_hour >= thresholds.get("errors_per_hour", 50):
            triggers.append({
                "type": "errors_per_hour",
                "threshold": thresholds["errors_per_hour"],
                "actual": errors_last_hour
            })
        
        if critical_errors >= thresholds.get("critical_errors_trigger", 5):
            triggers.append({
                "type": "critical_errors",
                "threshold": thresholds["critical_errors_trigger"],
                "actual": critical_errors
            })
        
        if not triggers:
            return {"triggered": False, "errors_last_hour": errors_last_hour, "critical_errors": critical_errors}
        
        # Check cooldown
        last_alert = await self.alert_history_collection.find_one(
            {"type": "threshold_alert"},
            sort=[("sent_at", -1)]
        )
        
        if last_alert:
            cooldown_minutes = config.get("cooldown_minutes", 30)
            cooldown_until = last_alert["sent_at"] + timedelta(minutes=cooldown_minutes)
            if now < cooldown_until:
                return {
                    "triggered": True,
                    "cooldown": True,
                    "cooldown_until": cooldown_until.isoformat(),
                    "triggers": triggers
                }
        
        return {
            "triggered": True,
            "cooldown": False,
            "triggers": triggers,
            "errors_last_hour": errors_last_hour,
            "critical_errors": critical_errors
        }
    
    async def send_alert(self, triggers: List[Dict], force: bool = False) -> Dict[str, Any]:
        """Send an alert email"""
        config = await self.get_config()
        
        if not config.get("enabled") and not force:
            return {"success": False, "error": "Alerting disabled"}
        
        api_key = config.get("resend_api_key")
        if not api_key:
            return {"success": False, "error": "Resend API key not configured"}
        
        recipients = config.get("recipient_emails", [])
        if not recipients:
            return {"success": False, "error": "No recipient emails configured"}
        
        if not RESEND_AVAILABLE:
            return {"success": False, "error": "Resend library not available"}
        
        try:
            resend.api_key = api_key
            
            # Build email content
            trigger_html = ""
            for t in triggers:
                trigger_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #333;">{t['type'].replace('_', ' ').title()}</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #FF0055;">{t['actual']}</td>
                    <td style="padding: 8px; border: 1px solid #333;">{t['threshold']}</td>
                </tr>
                """
            
            # Get recent errors for context
            recent_errors_html = ""
            if config.get("include_error_details", True):
                errors_collection = self.db.frontend_errors
                recent_errors = await errors_collection.find(
                    {},
                    {"_id": 0, "message": 1, "severity": 1, "component": 1, "timestamp": 1}
                ).sort("timestamp", -1).limit(5).to_list(5)
                
                for err in recent_errors:
                    severity_color = "#FF0055" if err.get("severity") == "CRITICAL" else "#FFB800"
                    recent_errors_html += f"""
                    <div style="background: #1F1F1F; padding: 10px; margin: 5px 0; border-radius: 4px;">
                        <span style="color: {severity_color}; font-weight: bold;">[{err.get('severity', 'UNKNOWN')}]</span>
                        <span style="color: #A1A1AA;">{err.get('component', 'Unknown')}</span><br>
                        <span style="color: #fff;">{err.get('message', 'No message')[:100]}</span>
                    </div>
                    """
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #fff; padding: 20px;">
                <div style="background: linear-gradient(135deg, #9D00FF20, #FF005520); padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h1 style="color: #FF0055; margin: 0;">⚠️ Error Alert Triggered</h1>
                    <p style="color: #A1A1AA; margin: 10px 0 0 0;">Tethys AI Trading Platform</p>
                </div>
                
                <h2 style="color: #9D00FF;">Threshold Exceeded</h2>
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr style="background: #1F1F1F;">
                        <th style="padding: 10px; border: 1px solid #333; text-align: left;">Metric</th>
                        <th style="padding: 10px; border: 1px solid #333; text-align: left;">Actual</th>
                        <th style="padding: 10px; border: 1px solid #333; text-align: left;">Threshold</th>
                    </tr>
                    {trigger_html}
                </table>
                
                {"<h3 style='color: #FFB800;'>Recent Errors</h3>" + recent_errors_html if recent_errors_html else ""}
                
                <div style="margin-top: 20px; padding: 15px; background: #1F1F1F; border-radius: 8px;">
                    <p style="margin: 0; color: #A1A1AA;">
                        <a href="https://cryptodash-43.preview.emergentagent.com/error-analytics" 
                           style="color: #00FF94; text-decoration: none;">
                            View Error Analytics Dashboard →
                        </a>
                    </p>
                </div>
                
                <hr style="border: 1px solid #333; margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    This alert was sent automatically. Configure alerting in Settings → Email.
                </p>
            </div>
            """
            
            params = {
                "from": config.get("sender_email", "onboarding@resend.dev"),
                "to": recipients,
                "subject": f"🚨 Tethys AI - Error Alert: {len(triggers)} threshold(s) exceeded",
                "html": html_content
            }
            
            result = await asyncio.to_thread(resend.Emails.send, params)
            
            # Record alert in history
            await self.alert_history_collection.insert_one({
                "type": "threshold_alert",
                "triggers": triggers,
                "recipients": recipients,
                "email_id": result.get("id"),
                "sent_at": datetime.now(timezone.utc)
            })
            
            logger.info(f"Error alert sent to {len(recipients)} recipients")
            return {
                "success": True,
                "email_id": result.get("id"),
                "recipients": recipients
            }
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_alert_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get alert history"""
        cursor = self.alert_history_collection.find(
            {},
            {"_id": 0}
        ).sort("sent_at", -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def run_check_and_alert(self) -> Dict[str, Any]:
        """Run threshold check and send alert if needed"""
        check_result = await self.check_thresholds()
        
        if not check_result.get("triggered"):
            return {"alerted": False, "check_result": check_result}
        
        if check_result.get("cooldown"):
            return {"alerted": False, "reason": "cooldown", "check_result": check_result}
        
        # Send alert
        alert_result = await self.send_alert(check_result.get("triggers", []))
        
        return {
            "alerted": alert_result.get("success", False),
            "check_result": check_result,
            "alert_result": alert_result
        }


# Global instance
_error_alerting_service: Optional[ErrorAlertingService] = None


def get_error_alerting_service() -> Optional[ErrorAlertingService]:
    return _error_alerting_service


def init_error_alerting_service(db: AsyncIOMotorDatabase) -> ErrorAlertingService:
    global _error_alerting_service
    _error_alerting_service = ErrorAlertingService(db)
    return _error_alerting_service
