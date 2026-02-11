"""
Email Digest Service
Sends daily/weekly summary emails to users with portfolio performance, trades, and AI insights
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os

logger = logging.getLogger(__name__)


class EmailDigestService:
    """Service for generating and sending email digests"""
    
    def __init__(self, db, smtp_config: Optional[Dict] = None):
        self.db = db
        
        # SMTP Configuration (can be overridden via environment variables)
        self.smtp_config = smtp_config or {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "from_email": os.getenv("SMTP_FROM_EMAIL", "noreply@aitrading.com"),
            "from_name": os.getenv("SMTP_FROM_NAME", "AI Trading Platform")
        }
    
    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user's email address from database"""
        try:
            user = await self.db.users.find_one({"user_id": user_id})
            return user.get("email") if user else None
        except Exception as e:
            logger.error(f"Error fetching user email: {str(e)}")
            return None
    
    async def _get_portfolio_summary(self, user_id: str) -> Dict[str, Any]:
        """Get portfolio summary data"""
        try:
            portfolio = await self.db.portfolios.find_one({"user_id": user_id})
            if not portfolio:
                return {}
            
            return {
                "total_value": portfolio.get("total_value", 0),
                "cash_balance": portfolio.get("cash_balance", 0),
                "assets_count": len(portfolio.get("assets", [])),
                "top_assets": portfolio.get("assets", [])[:5]
            }
        except Exception as e:
            logger.error(f"Error fetching portfolio summary: {str(e)}")
            return {}
    
    async def _get_recent_trades(self, user_id: str, days: int = 1) -> List[Dict]:
        """Get recent trades from the last N days"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            trades = await self.db.trades.find({
                "user_id": user_id,
                "timestamp": {"$gte": start_date}
            }).sort("timestamp", -1).to_list(length=20)
            
            return trades
        except Exception as e:
            logger.error(f"Error fetching recent trades: {str(e)}")
            return []
    
    async def _get_performance_stats(self, user_id: str, days: int = 1) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get performance records
            records = await self.db.performance_history.find({
                "user_id": user_id,
                "date": {"$gte": start_date}
            }).sort("date", 1).to_list(length=100)
            
            if not records:
                return {}
            
            # Calculate stats
            total_profit = sum(r.get("profit_loss", 0) for r in records)
            trades_count = sum(r.get("trades_count", 0) for r in records)
            win_count = sum(r.get("wins", 0) for r in records)
            
            return {
                "total_profit": total_profit,
                "trades_count": trades_count,
                "win_rate": (win_count / trades_count * 100) if trades_count > 0 else 0,
                "start_value": records[0].get("portfolio_value", 0) if records else 0,
                "end_value": records[-1].get("portfolio_value", 0) if records else 0
            }
        except Exception as e:
            logger.error(f"Error fetching performance stats: {str(e)}")
            return {}
    
    async def _get_active_strategies(self, user_id: str) -> List[Dict]:
        """Get active AI strategies"""
        try:
            strategies = await self.db.strategies.find({
                "user_id": user_id,
                "status": "active"
            }).sort("confidence", -1).to_list(length=5)
            
            return strategies
        except Exception as e:
            logger.error(f"Error fetching strategies: {str(e)}")
            return []
    
    def _format_currency(self, amount: float) -> str:
        """Format currency value"""
        return f"${amount:,.2f}"
    
    def _format_percentage(self, value: float) -> str:
        """Format percentage value"""
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.2f}%"
    
    def _generate_html_email(
        self,
        period: str,
        portfolio: Dict,
        trades: List[Dict],
        performance: Dict,
        strategies: List[Dict]
    ) -> str:
        """Generate HTML email content"""
        
        # Calculate changes
        profit_loss = performance.get("total_profit", 0)
        profit_color = "#00FF94" if profit_loss >= 0 else "#FF0055"
        
        portfolio_change = performance.get("end_value", 0) - performance.get("start_value", 0)
        portfolio_change_pct = (portfolio_change / performance.get("start_value", 1) * 100) if performance.get("start_value", 0) > 0 else 0
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Inter', -apple-system, sans-serif; background: #050505; color: #ffffff; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 16px; padding: 32px; border: 1px solid #333; }}
                .header {{ text-align: center; margin-bottom: 32px; }}
                .header h1 {{ color: #00FF94; margin: 0; font-size: 28px; }}
                .header p {{ color: #888; margin: 8px 0 0 0; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 24px; }}
                .stat-card {{ background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 16px; border: 1px solid rgba(255, 255, 255, 0.1); }}
                .stat-label {{ color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #fff; }}
                .section {{ margin-bottom: 24px; }}
                .section-title {{ color: #9D00FF; font-size: 18px; margin-bottom: 16px; border-bottom: 1px solid #333; padding-bottom: 8px; }}
                .trade-item {{ background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }}
                .trade-buy {{ border-left: 3px solid #00FF94; }}
                .trade-sell {{ border-left: 3px solid #FF0055; }}
                .strategy-item {{ background: rgba(157, 0, 255, 0.1); border-radius: 8px; padding: 12px; margin-bottom: 8px; }}
                .confidence {{ background: #9D00FF; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid #333; color: #666; font-size: 12px; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #00FF94, #9D00FF); color: white; text-decoration: none; padding: 12px 24px; border-radius: 8px; margin: 16px 0; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI Trading {period.title()} Digest</h1>
                    <p>{datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Portfolio Value</div>
                        <div class="stat-value">{self._format_currency(portfolio.get("total_value", 0))}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">{period.title()} P/L</div>
                        <div class="stat-value" style="color: {profit_color};">{self._format_currency(profit_loss)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Change</div>
                        <div class="stat-value" style="color: {profit_color};">{self._format_percentage(portfolio_change_pct)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Trades</div>
                        <div class="stat-value">{performance.get("trades_count", 0)}</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📊 Recent Trades</div>
                    {self._generate_trades_html(trades[:5])}
                </div>
                
                <div class="section">
                    <div class="section-title">🚀 Active AI Strategies</div>
                    {self._generate_strategies_html(strategies)}
                </div>
                
                <div style="text-align: center;">
                    <a href="https://modeltrainer.preview.emergentagent.com" class="cta-button">
                        View Full Dashboard →
                    </a>
                </div>
                
                <div class="footer">
                    <p>This is an automated {period} digest from your AI Trading Platform.</p>
                    <p>© 2026 AI Trading Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_trades_html(self, trades: List[Dict]) -> str:
        """Generate HTML for trades list"""
        if not trades:
            return "<p style='color: #888;'>No trades executed during this period.</p>"
        
        html = ""
        for trade in trades:
            action = trade.get("action", "").upper()
            trade_class = "trade-buy" if action == "BUY" else "trade-sell"
            
            html += f"""
            <div class="trade-item {trade_class}">
                <div>
                    <strong>{action}</strong> {trade.get("amount", 0):.4f} {trade.get("coin_pair", "")}
                    <br><small style="color: #888;">{trade.get("timestamp", "").strftime("%b %d, %I:%M %p") if isinstance(trade.get("timestamp"), datetime) else ""}</small>
                </div>
                <div style="text-align: right;">
                    <strong>{self._format_currency(trade.get("total_value", 0))}</strong>
                    <br><small style="color: #888;">@ {self._format_currency(trade.get("price", 0))}</small>
                </div>
            </div>
            """
        
        return html
    
    def _generate_strategies_html(self, strategies: List[Dict]) -> str:
        """Generate HTML for strategies list"""
        if not strategies:
            return "<p style='color: #888;'>No active strategies at the moment.</p>"
        
        html = ""
        for strategy in strategies:
            confidence = strategy.get("confidence", 0)
            
            html += f"""
            <div class="strategy-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{strategy.get("name", "Unnamed Strategy")}</strong>
                        <br><small style="color: #888;">{strategy.get("coin", "")} • {strategy.get("action", "").upper()}</small>
                    </div>
                    <span class="confidence">{confidence}% Confidence</span>
                </div>
            </div>
            """
        
        return html
    
    async def send_digest(
        self,
        user_id: str,
        period: str = "daily"
    ) -> Dict[str, Any]:
        """
        Send email digest to user
        
        Args:
            user_id: User ID
            period: 'daily' or 'weekly'
        
        Returns:
            Dict with status and message
        """
        try:
            # Get user email
            email = await self._get_user_email(user_id)
            if not email:
                return {"success": False, "error": "User email not found"}
            
            # Check if SMTP is configured
            if not self.smtp_config.get("username") or not self.smtp_config.get("password"):
                logger.warning("SMTP not configured, skipping email send")
                return {"success": False, "error": "SMTP not configured"}
            
            # Gather data
            days = 7 if period == "weekly" else 1
            portfolio = await self._get_portfolio_summary(user_id)
            trades = await self._get_recent_trades(user_id, days)
            performance = await self._get_performance_stats(user_id, days)
            strategies = await self._get_active_strategies(user_id)
            
            # Generate email content
            html_content = self._generate_html_email(period, portfolio, trades, performance, strategies)
            
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Your {period.title()} Trading Digest - {datetime.now().strftime('%b %d, %Y')}"
            msg["From"] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            msg["To"] = email
            
            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)
            
            logger.info(f"Sent {period} digest to {email}")
            
            return {
                "success": True,
                "message": f"{period.title()} digest sent successfully",
                "email": email
            }
            
        except Exception as e:
            logger.error(f"Error sending digest: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def schedule_digests(self):
        """Schedule daily and weekly digests (called by scheduler)"""
        try:
            # Get all users with digest preferences
            users = await self.db.users.find({
                "email_preferences.digest_enabled": True
            }).to_list(length=10000)
            
            now = datetime.now()
            
            for user in users:
                user_id = user.get("user_id")
                preferences = user.get("email_preferences", {})
                
                # Send daily digest
                if preferences.get("daily_digest", True):
                    await self.send_digest(user_id, "daily")
                
                # Send weekly digest (on Sundays)
                if preferences.get("weekly_digest", True) and now.weekday() == 6:
                    await self.send_digest(user_id, "weekly")
            
            logger.info(f"Scheduled digests sent to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error scheduling digests: {str(e)}")
