"""AI Trading Copilot API

Provides conversational AI assistance for trading.
Powered by Venice.ai with DeepSeek R1 model.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-copilot", tags=["AI Copilot"])

# In-memory storage for chat sessions
_sessions: Dict[str, Dict] = {}


class ChatMessage(BaseModel):
    """A chat message."""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request to send a message to the AI copilot."""
    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    include_market_context: Optional[bool] = Field(default=True, description="Include current market data in context")


class ChatResponse(BaseModel):
    """Response from the AI copilot."""
    session_id: str
    response: str
    suggestions: Optional[List[str]] = None
    market_context: Optional[Dict] = None
    timestamp: str


async def _get_market_context() -> Dict[str, Any]:
    """Fetch current market context for AI."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Get market prices
            prices_resp = await client.get("http://localhost:8001/api/market/prices")
            prices = prices_resp.json() if prices_resp.status_code == 200 else {}
            
            # Get fear & greed
            fg_resp = await client.get("http://localhost:8001/api/tethys/fear-greed")
            fear_greed = fg_resp.json() if fg_resp.status_code == 200 else {}
            
            # Get sentiment
            sent_resp = await client.get("http://localhost:8001/api/sentiment/market")
            sentiment = sent_resp.json() if sent_resp.status_code == 200 else {}
            
            return {
                "prices": prices.get("prices", {})[:5] if isinstance(prices.get("prices"), list) else {},
                "fear_greed_index": fear_greed.get("value", "N/A"),
                "fear_greed_label": fear_greed.get("classification", "N/A"),
                "market_sentiment": sentiment.get("market_label", "N/A"),
                "sentiment_score": sentiment.get("market_score", "N/A"),
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.warning(f"Failed to fetch market context: {e}")
        return {"error": "Unable to fetch market data", "timestamp": datetime.utcnow().isoformat()}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI trading copilot."""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Initialize session if new
    if session_id not in _sessions:
        _sessions[session_id] = {
            "id": session_id,
            "messages": [],
            "created_at": datetime.utcnow().isoformat()
        }
    
    # Get market context if requested
    market_context = None
    if request.include_market_context:
        market_context = await _get_market_context()
    
    try:
        from services.venice_llm import get_venice_llm
        
        llm = get_venice_llm()
        if llm is None:
            # Fallback response
            return await _fallback_response(session_id, request.message, market_context)
        
        result = await llm.trading_copilot_response(
            user_message=request.message,
            session_id=session_id,
            market_context=market_context
        )
        
        if result.get("success"):
            # Store messages in session
            _sessions[session_id]["messages"].append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.utcnow().isoformat()
            })
            _sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": result["response"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return ChatResponse(
                session_id=session_id,
                response=result["response"],
                suggestions=_generate_followup_suggestions(request.message),
                market_context=market_context,
                timestamp=datetime.utcnow().isoformat()
            )
        else:
            return await _fallback_response(session_id, request.message, market_context)
            
    except Exception as e:
        logger.error(f"AI Copilot error: {e}")
        return await _fallback_response(session_id, request.message, market_context)


async def _fallback_response(
    session_id: str,
    message: str,
    market_context: Optional[Dict]
) -> ChatResponse:
    """Generate fallback response when AI is unavailable."""
    message_lower = message.lower()
    
    # Pattern-based responses
    if any(word in message_lower for word in ["buy", "long", "entry"]):
        response = """📊 **Entry Analysis Tips:**

1. **Check the trend** - Is the asset in an uptrend on higher timeframes?
2. **Wait for confirmation** - Look for RSI < 30 or MACD crossover
3. **Set a stop loss** - Always protect your capital (2-5% of position)
4. **Don't FOMO** - If you missed the move, wait for the next setup

Would you like me to analyze a specific coin?"""
    
    elif any(word in message_lower for word in ["sell", "exit", "short"]):
        response = """📉 **Exit Strategy Tips:**

1. **Trailing stops** - Lock in profits as price moves in your favor
2. **Take partials** - Sell 50% at first target, let rest run
3. **Watch for divergence** - RSI/price divergence often signals reversals
4. **Stick to your plan** - Don't let emotions override your strategy

What's your current position you're looking to exit?"""
    
    elif any(word in message_lower for word in ["risk", "stop loss", "position size"]):
        response = """🛡️ **Risk Management Rules:**

1. **1-2% Rule** - Never risk more than 1-2% of portfolio per trade
2. **Position sizing formula**: 
   `Size = (Portfolio × Risk%) / (Entry - StopLoss)`
3. **Risk-Reward** - Aim for at least 1:2 (risk 1 to make 2)
4. **Diversify** - Don't put all eggs in one basket

Want me to help calculate position size for a specific trade?"""
    
    elif any(word in message_lower for word in ["sentiment", "fear", "greed", "market"]):
        fg = market_context.get("fear_greed_index", "N/A") if market_context else "N/A"
        fg_label = market_context.get("fear_greed_label", "N/A") if market_context else "N/A"
        response = f"""📈 **Market Sentiment Analysis:**

**Fear & Greed Index:** {fg} ({fg_label})

- **Extreme Fear (0-25):** Often a buying opportunity
- **Fear (25-45):** Cautious accumulation zone
- **Neutral (45-55):** Wait for clearer signals
- **Greed (55-75):** Consider taking profits
- **Extreme Greed (75-100):** High risk of correction

Remember: "Be fearful when others are greedy, greedy when others are fearful.""""
    
    elif any(word in message_lower for word in ["help", "what can you", "capabilities"]):
        response = """🤖 **I'm Tethys AI, your trading copilot!**

I can help you with:

📊 **Analysis**
- Market sentiment and Fear & Greed index
- Technical indicator explanations
- Entry/exit point suggestions

📈 **Strategy**
- Risk management calculations
- Position sizing
- Portfolio review

🎯 **Learning**
- Explain trading concepts
- Review your trade ideas
- Suggest improvements

Try asking: "What's the current market sentiment?" or "Help me set up a stop loss for my BTC trade.""""
    
    else:
        response = """I'm here to help with your trading! You can ask me about:

• **Market analysis** - Current sentiment, price action
• **Entry/exit points** - When to buy or sell
• **Risk management** - Stop losses, position sizing
• **Strategy ideas** - Based on your goals

What would you like to know?"""
    
    # Store in session
    _sessions[session_id]["messages"].append({
        "role": "user",
        "content": message,
        "timestamp": datetime.utcnow().isoformat()
    })
    _sessions[session_id]["messages"].append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return ChatResponse(
        session_id=session_id,
        response=response,
        suggestions=_generate_followup_suggestions(message),
        market_context=market_context,
        timestamp=datetime.utcnow().isoformat()
    )


def _generate_followup_suggestions(message: str) -> List[str]:
    """Generate relevant follow-up suggestions."""
    message_lower = message.lower()
    
    suggestions = []
    
    if any(word in message_lower for word in ["buy", "entry"]):
        suggestions = [
            "What's a good stop loss level?",
            "Should I DCA or enter all at once?",
            "What's the current market sentiment?"
        ]
    elif any(word in message_lower for word in ["sell", "exit"]):
        suggestions = [
            "Should I take partial profits?",
            "What are the key resistance levels?",
            "How do I set a trailing stop?"
        ]
    elif "risk" in message_lower:
        suggestions = [
            "Calculate position size for my trade",
            "What's a safe portfolio allocation?",
            "Explain the 1% rule"
        ]
    else:
        suggestions = [
            "What's the market sentiment today?",
            "Help me create a trading strategy",
            "Analyze BTC for entry points"
        ]
    
    return suggestions


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get chat session history."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return _sessions[session_id]


@router.get("/sessions")
async def list_sessions():
    """List all chat sessions."""
    return {
        "sessions": [
            {
                "id": s["id"],
                "message_count": len(s["messages"]),
                "created_at": s["created_at"],
                "last_message": s["messages"][-1] if s["messages"] else None
            }
            for s in _sessions.values()
        ],
        "total": len(_sessions)
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del _sessions[session_id]
    return {"message": "Session deleted", "session_id": session_id}


@router.post("/session/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear messages in a session but keep the session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    _sessions[session_id]["messages"] = []
    
    # Also clear LLM conversation history
    try:
        from services.venice_llm import get_venice_llm
        llm = get_venice_llm()
        if llm:
            llm.clear_session(session_id)
    except:
        pass
    
    return {"message": "Session cleared", "session_id": session_id}


@router.get("/quick-insights")
async def get_quick_insights():
    """Get quick AI insights about current market conditions."""
    market_context = await _get_market_context()
    
    insights = []
    
    # Fear & Greed insight
    fg = market_context.get("fear_greed_index")
    if fg and fg != "N/A":
        try:
            fg_value = int(fg)
            if fg_value < 25:
                insights.append({
                    "type": "opportunity",
                    "title": "Extreme Fear Detected",
                    "description": "Markets are fearful. Historically a good accumulation zone.",
                    "icon": "🎯"
                })
            elif fg_value > 75:
                insights.append({
                    "type": "warning",
                    "title": "Extreme Greed Alert",
                    "description": "Markets are greedy. Consider taking some profits.",
                    "icon": "⚠️"
                })
        except:
            pass
    
    # Sentiment insight
    sentiment = market_context.get("market_sentiment")
    if sentiment:
        if sentiment.lower() == "bullish":
            insights.append({
                "type": "info",
                "title": "Bullish Sentiment",
                "description": "Overall market sentiment is positive.",
                "icon": "📈"
            })
        elif sentiment.lower() == "bearish":
            insights.append({
                "type": "info",
                "title": "Bearish Sentiment",
                "description": "Overall market sentiment is negative. Trade with caution.",
                "icon": "📉"
            })
    
    # Default insight if none generated
    if not insights:
        insights.append({
            "type": "info",
            "title": "Market Neutral",
            "description": "No strong signals detected. Wait for better setups.",
            "icon": "⏸️"
        })
    
    return {
        "insights": insights,
        "market_context": market_context,
        "generated_at": datetime.utcnow().isoformat()
    }
