import os
import asyncio
import logging
import resend
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """
    Email notification service for high priority crypto trade alerts
    using Resend API
    """
    
    def __init__(self):
        self.api_key = os.getenv('RESEND_API_KEY')
        self.sender_email = os.getenv('SENDER_EMAIL', 'onboarding@resend.dev')
        self.default_recipient = os.getenv('ALERT_EMAIL')  # No fallback - must be configured
        
        if self.api_key:
            resend.api_key = self.api_key
            print("✅ Email notifications enabled via Resend")
        else:
            print("⚠️ RESEND_API_KEY not configured - email notifications disabled")
    
    def _generate_gem_email_html(self, gem: Dict[str, Any]) -> str:
        """Generate beautiful HTML email for gem alert"""
        symbol = gem.get('symbol', 'Unknown').upper()
        score = gem.get('match_score', 0)
        alert_level = gem.get('alert_level', 'HIGH')
        potential = gem.get('potential_multiplier', '?x')
        current_price = gem.get('current_price', 0)
        price_change_24h = gem.get('price_change_24h', 0)
        volume_change = gem.get('volume_change_24h', 0)
        
        # Extract signals and reasons
        signals = gem.get('matching_signals', [])
        reasons = gem.get('reasons', [])
        
        # Build key factors list
        key_factors_html = ""
        
        # Add matching signals as factors
        signal_explanations = {
            'EXTREME_VOLUME': ('📊 Extreme Volume Spike', 'Trading volume has increased significantly, indicating strong market interest and potential breakout'),
            'OVERSOLD_ACCUMULATION': ('📉 Oversold Accumulation', 'RSI indicates oversold conditions while accumulation is occurring - classic reversal pattern'),
            'MACD_BULLISH': ('📈 MACD Bullish Crossover', 'MACD line crossed above signal line, indicating bullish momentum building'),
            'MOMENTUM_BUILDING': ('🚀 Momentum Building', 'Price momentum indicators show increasing buying pressure'),
            'BREAKOUT_FORMING': ('💥 Breakout Forming', 'Price approaching key resistance with increasing volume - potential breakout imminent'),
            'WHALE_ACTIVITY': ('🐋 Whale Activity Detected', 'Large wallet movements detected, indicating institutional interest'),
            'SOCIAL_BUZZ': ('🔥 Social Media Buzz', 'Increased mentions across social platforms correlating with price action'),
            'UNDERVALUED_METRICS': ('💎 Undervalued Metrics', 'Fundamental analysis shows token is trading below fair value estimates'),
            'SUPPORT_BOUNCE': ('🛡️ Strong Support Bounce', 'Price bounced off key support level with conviction'),
            'GOLDEN_CROSS': ('✨ Golden Cross Pattern', '50-day MA crossed above 200-day MA - historically bullish long-term signal'),
        }
        
        for signal in signals[:5]:
            signal_name = signal.get('signal', signal) if isinstance(signal, dict) else signal
            if signal_name in signal_explanations:
                emoji, explanation = signal_explanations[signal_name]
                key_factors_html += f"""
                <tr>
                    <td style="padding: 12px; background: #1a1a2e; border-radius: 8px; margin-bottom: 8px;">
                        <div style="color: #00ff94; font-weight: bold; font-size: 14px;">{emoji} {signal_name.replace('_', ' ').title()}</div>
                        <div style="color: #a1a1aa; font-size: 13px; margin-top: 4px;">{explanation}</div>
                    </td>
                </tr>
                <tr><td style="height: 8px;"></td></tr>
                """
            else:
                key_factors_html += f"""
                <tr>
                    <td style="padding: 12px; background: #1a1a2e; border-radius: 8px;">
                        <div style="color: #00ff94; font-weight: bold; font-size: 14px;">✓ {signal_name.replace('_', ' ').title()}</div>
                    </td>
                </tr>
                <tr><td style="height: 8px;"></td></tr>
                """
        
        # Add additional reasons
        for reason in reasons[:3]:
            key_factors_html += f"""
            <tr>
                <td style="padding: 12px; background: #1a1a2e; border-radius: 8px;">
                    <div style="color: #ffb800; font-size: 13px;">💡 {reason}</div>
                </td>
            </tr>
            <tr><td style="height: 8px;"></td></tr>
            """
        
        # Price change color
        price_color = "#00ff94" if price_change_24h >= 0 else "#ff0055"
        price_arrow = "↑" if price_change_24h >= 0 else "↓"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%); border-radius: 16px; overflow: hidden; border: 1px solid #2a2a4a;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(90deg, #ff0055 0%, #9d00ff 100%); padding: 20px; text-align: center;">
                            <div style="font-size: 28px; font-weight: bold; color: white;">🚨 {alert_level} PRIORITY ALERT</div>
                            <div style="font-size: 14px; color: rgba(255,255,255,0.8); margin-top: 8px;">AI Crypto Trading System</div>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 30px;">
                            
                            <!-- Coin Header -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>
                                        <div style="font-size: 36px; font-weight: bold; color: white;">{symbol}</div>
                                        <div style="font-size: 14px; color: #a1a1aa; margin-top: 4px;">Hidden Gem Detected</div>
                                    </td>
                                    <td align="right">
                                        <div style="background: #00ff94; color: #000; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 18px;">
                                            Score: {score}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Price Info -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 20px; background: #1a1a2e; border-radius: 12px; padding: 20px;">
                                <tr>
                                    <td width="50%" style="padding: 15px;">
                                        <div style="color: #a1a1aa; font-size: 12px;">CURRENT PRICE</div>
                                        <div style="color: white; font-size: 24px; font-weight: bold; margin-top: 4px;">${current_price:.6f}</div>
                                    </td>
                                    <td width="50%" style="padding: 15px;">
                                        <div style="color: #a1a1aa; font-size: 12px;">24H CHANGE</div>
                                        <div style="color: {price_color}; font-size: 24px; font-weight: bold; margin-top: 4px;">{price_arrow} {abs(price_change_24h):.2f}%</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td width="50%" style="padding: 15px;">
                                        <div style="color: #a1a1aa; font-size: 12px;">POTENTIAL</div>
                                        <div style="color: #ffb800; font-size: 24px; font-weight: bold; margin-top: 4px;">{potential}</div>
                                    </td>
                                    <td width="50%" style="padding: 15px;">
                                        <div style="color: #a1a1aa; font-size: 12px;">VOLUME CHANGE</div>
                                        <div style="color: #9d00ff; font-size: 24px; font-weight: bold; margin-top: 4px;">+{volume_change:.0f}%</div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Key Factors Section -->
                            <div style="margin-top: 30px;">
                                <div style="font-size: 18px; font-weight: bold; color: white; margin-bottom: 16px;">
                                    🔑 KEY FACTORS & REASONING
                                </div>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    {key_factors_html}
                                </table>
                            </div>
                            
                            <!-- Risk Warning -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 25px;">
                                <tr>
                                    <td style="background: rgba(255,0,85,0.1); border: 1px solid rgba(255,0,85,0.3); border-radius: 8px; padding: 15px;">
                                        <div style="color: #ff0055; font-size: 12px; font-weight: bold;">⚠️ RISK DISCLAIMER</div>
                                        <div style="color: #a1a1aa; font-size: 11px; margin-top: 4px;">
                                            This alert is AI-generated and not financial advice. Always do your own research. 
                                            Crypto investments are highly volatile and you may lose your entire investment.
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #0f0f1a; padding: 20px; text-align: center; border-top: 1px solid #2a2a4a;">
                            <div style="color: #a1a1aa; font-size: 12px;">
                                AI Crypto Trading System • Alert generated at {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
                            </div>
                            <div style="color: #666; font-size: 11px; margin-top: 8px;">
                                To manage your notification preferences, visit the Settings page in the app.
                            </div>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return html
    
    async def send_email(
        self, 
        recipient: str, 
        subject: str, 
        html_content: str
    ) -> Dict[str, Any]:
        """Send email via Resend API"""
        if not self.api_key:
            return {'success': False, 'error': 'Resend API key not configured'}
        
        params = {
            "from": self.sender_email,
            "to": [recipient],
            "subject": subject,
            "html": html_content
        }
        
        try:
            # Run sync SDK in thread to keep FastAPI non-blocking
            email = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"📧 Email sent to {recipient}: {subject}")
            print(f"📧 Email sent to {recipient}")
            return {
                'success': True,
                'email_id': email.get('id'),
                'recipient': recipient
            }
        except Exception as e:
            logger.error(f"❌ Email failed: {str(e)}")
            print(f"❌ Email failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def send_high_priority_gem_alert(
        self, 
        gem: Dict[str, Any], 
        recipient: str = None
    ) -> Dict[str, Any]:
        """Send email alert for HIGH priority gem detection"""
        email_to = recipient or self.default_recipient
        
        symbol = gem.get('symbol', 'Unknown').upper()
        score = gem.get('match_score', 0)
        potential = gem.get('potential_multiplier', '?x')
        
        subject = f"🚨 HIGH PRIORITY: {symbol} - Score {score} - Potential {potential}"
        
        html_content = self._generate_gem_email_html(gem)
        
        result = await self.send_email(email_to, subject, html_content)
        
        return result
    
    async def send_trade_completion_email(
        self,
        trade: Dict[str, Any],
        recipient: str = None
    ) -> Dict[str, Any]:
        """Send email when a trade completes"""
        email_to = recipient or self.default_recipient
        
        symbol = trade.get('symbol', 'Unknown')
        action = trade.get('action', 'TRADE')
        profit_pct = trade.get('profit_pct')
        mode = trade.get('mode', 'paper').upper()
        
        if profit_pct is not None:
            emoji = "🟢" if profit_pct > 0 else "🔴"
            profit_str = f"{'+' if profit_pct > 0 else ''}{profit_pct:.2f}%"
            subject = f"{emoji} Trade Closed: {symbol} | {profit_str} | {mode}"
        else:
            subject = f"🚀 Trade Opened: {symbol} | {mode}"
        
        # Simple trade notification HTML
        html_content = f"""
        <html>
        <body style="background: #0a0a0a; color: white; font-family: sans-serif; padding: 20px;">
            <h2>Trade Notification</h2>
            <p><strong>Symbol:</strong> {symbol}</p>
            <p><strong>Action:</strong> {action}</p>
            <p><strong>Mode:</strong> {mode}</p>
            {"<p><strong>P/L:</strong> " + profit_str + "</p>" if profit_pct else ""}
            <p><small>AI Crypto Trading System</small></p>
        </body>
        </html>
        """
        
        return await self.send_email(email_to, subject, html_content)


# Singleton instance
_email_service = None

def get_email_service() -> EmailNotificationService:
    global _email_service
    if _email_service is None:
        _email_service = EmailNotificationService()
    return _email_service
