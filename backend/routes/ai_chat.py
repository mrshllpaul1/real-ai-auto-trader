"""
AI Chat API Routes
Provides conversational AI interface for crypto trading queries.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/ai-chat", tags=["AI Chat"])

# Dependencies
_db = None
_chat_service = None

def set_dependencies(db, chat_service):
    """Set dependencies from server.py"""
    global _db, _chat_service
    _db = db
    _chat_service = chat_service


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    include_market_data: Optional[bool] = True
    include_news: Optional[bool] = True


class QuickAnalysisRequest(BaseModel):
    coin_id: str


class StrategyAdviceRequest(BaseModel):
    portfolio_value: float
    risk_tolerance: Optional[str] = "moderate"  # low, moderate, high, aggressive


class PatternExplainRequest(BaseModel):
    pattern_name: str
    coin_id: str


class DeepChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    context_hint: Optional[str] = ""
    include_predictions: Optional[bool] = True
    include_gems: Optional[bool] = True


@router.post("/ask-deep")
async def ask_ai_deep(request: DeepChatRequest):
    """
    Ask the AI with deep learning integration.
    
    Enhanced features:
    - LSTM price predictions
    - Pattern detection
    - Hidden gem analysis
    - Sentiment from news
    
    Use for:
    - Price predictions: "What's the prediction for Bitcoin?"
    - Hidden gems: "What are today's hidden gems?"
    - Pattern analysis: "What patterns do you see in ETH?"
    """
    if not _chat_service:
        raise HTTPException(status_code=503, detail="AI Chat service not initialized")
    
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")
    
    result = await _chat_service.chat_with_deep_learning(
        query=request.query,
        session_id=request.session_id,
        context_hint=request.context_hint,
        include_predictions=request.include_predictions,
        include_gems=request.include_gems
    )
    
    return result


@router.post("/ask")
async def ask_ai(request: ChatRequest):
    """
    Ask the AI a question about crypto trading.
    
    Supports questions about:
    - Specific coins (e.g., "What's your analysis of Bitcoin?")
    - Market conditions (e.g., "How is the market looking today?")
    - Trading strategies (e.g., "Should I buy or sell ETH?")
    - News sentiment (e.g., "What's the sentiment around Solana?")
    - Token comparisons (e.g., "Compare BTC and ETH")
    """
    if not _chat_service:
        raise HTTPException(status_code=503, detail="AI Chat service not initialized")
    
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")
    
    if len(request.query) > 1000:
        raise HTTPException(status_code=400, detail="Query must be less than 1000 characters")
    
    result = await _chat_service.chat(
        query=request.query,
        session_id=request.session_id,
        include_market_data=request.include_market_data,
        include_news=request.include_news
    )
    
    if result.get("error") and "not configured" in result.get("response", ""):
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    return result


@router.post("/quick-analysis")
async def get_quick_analysis(request: QuickAnalysisRequest):
    """Get a quick AI analysis for a specific cryptocurrency"""
    if not _chat_service:
        raise HTTPException(status_code=503, detail="AI Chat service not initialized")
    
    result = await _chat_service.get_quick_analysis(request.coin_id)
    return result


@router.post("/strategy-advice")
async def get_strategy_advice(request: StrategyAdviceRequest):
    """Get AI-powered trading strategy advice based on portfolio and risk tolerance"""
    if not _chat_service:
        raise HTTPException(status_code=503, detail="AI Chat service not initialized")
    
    if request.portfolio_value <= 0:
        raise HTTPException(status_code=400, detail="Portfolio value must be positive")
    
    if request.risk_tolerance not in ["low", "moderate", "high", "aggressive"]:
        raise HTTPException(status_code=400, detail="Risk tolerance must be: low, moderate, high, or aggressive")
    
    result = await _chat_service.get_strategy_advice(
        portfolio_value=request.portfolio_value,
        risk_tolerance=request.risk_tolerance
    )
    return result


@router.post("/explain-pattern")
async def explain_pattern(request: PatternExplainRequest):
    """Get AI explanation of a detected chart pattern"""
    if not _chat_service:
        raise HTTPException(status_code=503, detail="AI Chat service not initialized")
    
    result = await _chat_service.explain_pattern(
        pattern_name=request.pattern_name,
        coin_id=request.coin_id
    )
    return result


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 20):
    """Get chat history for a session"""
    if not _chat_service:
        raise HTTPException(status_code=503, detail="AI Chat service not initialized")
    
    if limit > 100:
        limit = 100
    
    history = await _chat_service.get_chat_history(session_id, limit)
    return {
        "session_id": session_id,
        "history": history,
        "count": len(history)
    }


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    if not _chat_service:
        raise HTTPException(status_code=503, detail="AI Chat service not initialized")
    
    _chat_service.clear_history(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.get("/suggestions")
async def get_query_suggestions():
    """Get suggested queries for the AI chat"""
    return {
        "suggestions": [
            {
                "category": "Coin Analysis",
                "queries": [
                    "What's your analysis of Bitcoin right now?",
                    "Is Ethereum a good buy at current prices?",
                    "Compare Solana and Cardano for me",
                    "What are the key support levels for BTC?"
                ]
            },
            {
                "category": "Market Overview",
                "queries": [
                    "How is the crypto market looking today?",
                    "What's the overall market sentiment?",
                    "Are we in a bull or bear market?",
                    "What coins are trending right now?"
                ]
            },
            {
                "category": "Trading Strategy",
                "queries": [
                    "What's a good entry point for ETH?",
                    "Should I take profits on my BTC position?",
                    "How should I diversify my crypto portfolio?",
                    "What's your recommended position size?"
                ]
            },
            {
                "category": "News & Sentiment",
                "queries": [
                    "What's the latest news affecting Bitcoin?",
                    "Any important crypto news I should know?",
                    "What's the sentiment around meme coins?",
                    "Are there any regulatory concerns right now?"
                ]
            },
            {
                "category": "Technical Analysis",
                "queries": [
                    "What patterns do you see on the BTC chart?",
                    "Is there a double top forming on ETH?",
                    "What do the RSI and MACD indicate for SOL?",
                    "Are we seeing bullish or bearish divergence?"
                ]
            }
        ]
    }
