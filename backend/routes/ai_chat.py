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


class CommandRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    context_hint: Optional[str] = ""


# Global gem predictor reference
_gem_predictor = None

def set_gem_predictor(predictor):
    global _gem_predictor
    _gem_predictor = predictor


@router.post("/execute-command")
async def execute_ai_command(request: CommandRequest):
    """
    AI Command Center - Execute actions across the app via natural language.
    
    Supported commands:
    - Navigation: "go to dashboard", "open analytics"
    - Search: "find hidden gems", "search for BTC"
    - Add: "add ETH to watchlist", "track SOL"
    - Analyze: "analyze Bitcoin", "predict ETH price"
    - Execute: "scan market", "get predictions"
    """
    if not _chat_service:
        raise HTTPException(status_code=503, detail="AI service not initialized")
    
    query = request.query.lower()
    actions_executed = []
    actions_to_execute = []
    gems_found = []
    predictions = None
    
    # Parse intent and execute actions
    
    # 1. Navigation intents
    nav_map = {
        "dashboard": "/",
        "home": "/",
        "growth": "/growth",
        "500": "/growth",
        "journal": "/journal",
        "scanner": "/scanner",
        "gem": "/scanner",
        "trading": "/trading",
        "analytics": "/analytics",
        "deep learning": "/deep-learning",
        "predict": "/deep-learning",
        "news": "/news",
        "settings": "/settings",
        "setup": "/setup"
    }
    
    if any(word in query for word in ["go to", "open", "show", "navigate"]):
        for key, path in nav_map.items():
            if key in query:
                actions_to_execute.append({"type": "navigate", "path": path})
                actions_executed.append({"type": "navigation", "destination": path})
                break
    
    # 2. Add/Track intents
    if any(word in query for word in ["add", "track", "watch", "save"]):
        # Extract coin symbols
        import re
        coin_pattern = r'\b(btc|eth|sol|ada|dot|avax|bnb|xrp|doge|shib|matic|link|uni|atom|ltc)\b'
        matches = re.findall(coin_pattern, query, re.IGNORECASE)
        
        if matches:
            coin_mapping = {
                "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
                "ada": "cardano", "dot": "polkadot", "avax": "avalanche-2",
                "bnb": "binancecoin", "xrp": "ripple", "doge": "dogecoin",
                "shib": "shiba-inu", "matic": "matic-network", "link": "chainlink",
                "uni": "uniswap", "atom": "cosmos", "ltc": "litecoin"
            }
            for match in matches:
                coin_id = coin_mapping.get(match.lower(), match.lower())
                actions_to_execute.append({"type": "add_coin", "coin": match.upper(), "coin_id": coin_id})
                actions_executed.append({"type": "add_to_watchlist", "coin": match.upper()})
    
    # 3. Find/Scan intents
    if any(word in query for word in ["find", "scan", "search", "discover"]):
        if any(word in query for word in ["gem", "hidden", "opportunity", "potential"]):
            # Execute gem scan
            if _gem_predictor:
                try:
                    gems = await _gem_predictor.scan_for_gems(limit=10)
                    gems_found = gems[:5]
                    actions_executed.append({"type": "gem_scan", "found": len(gems_found)})
                except Exception as e:
                    print(f"Gem scan error: {e}")
    
    # 4. Predict intents
    if any(word in query for word in ["predict", "forecast", "analysis"]):
        actions_to_execute.append({"type": "navigate", "path": "/deep-learning"})
    
    # 5. Trade/Buy/Sell intents
    if any(word in query for word in ["buy", "sell", "trade", "execute"]):
        import re
        coin_pattern = r'\b(btc|eth|sol|ada|dot|avax|bnb|xrp|doge|shib|matic|link|uni|atom|ltc|aave|sui|apt)\b'
        matches = re.findall(coin_pattern, query, re.IGNORECASE)
        
        if matches:
            action_type = "buy" if "buy" in query else "sell" if "sell" in query else "trade"
            for match in matches:
                actions_to_execute.append({
                    "type": f"trade_{action_type}",
                    "coin": match.upper(),
                    "message": f"Ready to {action_type} {match.upper()}. Go to Trading page to execute."
                })
                actions_executed.append({"type": f"{action_type}_intent", "coin": match.upper()})
            actions_to_execute.append({"type": "navigate", "path": "/trading"})
    
    # 6. Backtest intents
    if any(word in query for word in ["backtest", "simulate", "test strategy"]):
        actions_to_execute.append({"type": "navigate", "path": "/backtest"})
        actions_executed.append({"type": "backtest_requested"})
    
    # 7. Portfolio/Balance intents
    if any(word in query for word in ["portfolio", "balance", "holdings", "my coins"]):
        # Get Kraken portfolio if available
        try:
            from routes.trading import get_kraken_portfolio
            portfolio = await get_kraken_portfolio()
            if portfolio and portfolio.get("holdings"):
                holdings_summary = []
                for h in portfolio["holdings"][:5]:
                    holdings_summary.append({
                        "symbol": h["symbol"],
                        "value": h["value_usd"],
                        "change": h.get("price_change_24h", 0)
                    })
                actions_executed.append({
                    "type": "portfolio_fetched",
                    "total": portfolio.get("total_value_usd", 0),
                    "holdings": holdings_summary
                })
        except Exception as e:
            print(f"Portfolio fetch error: {e}")
    
    # 8. Train/Learn intents
    if any(word in query for word in ["train", "learn", "improve", "optimize"]):
        if any(word in query for word in ["gem", "hidden"]):
            try:
                from services.hidden_gem_predictor import get_gem_training_status
                status = get_gem_training_status()
                if not status.get("running"):
                    # Trigger training
                    if _gem_predictor:
                        await _gem_predictor.train_on_historical()
                        actions_executed.append({"type": "training_started", "model": "gem_predictor"})
                else:
                    actions_executed.append({
                        "type": "training_in_progress",
                        "progress": status.get("progress", 0)
                    })
            except Exception as e:
                print(f"Training error: {e}")
    
    # 9. Rebuild universe intents
    if any(word in query for word in ["rebuild", "universe", "optimize universe", "1000 coins"]):
        actions_to_execute.append({"type": "navigate", "path": "/ensemble"})
        actions_executed.append({"type": "universe_rebuild_suggested"})
    
    # 10. News/Sentiment intents
    if any(word in query for word in ["news", "sentiment", "headlines"]):
        try:
            from services.coindesk_service import get_coindesk_service
            coindesk = get_coindesk_service()
            sentiment = await coindesk.get_market_sentiment_summary()
            if sentiment and not sentiment.get("error"):
                actions_executed.append({
                    "type": "sentiment_fetched",
                    "overall": sentiment.get("overall_sentiment"),
                    "positive": sentiment.get("sentiment_distribution", {}).get("POSITIVE", 0),
                    "negative": sentiment.get("sentiment_distribution", {}).get("NEGATIVE", 0)
                })
        except Exception as e:
            print(f"Sentiment fetch error: {e}")
    
    # Get AI response with context
    ai_response = await _chat_service.chat_with_deep_learning(
        query=request.query,
        session_id=request.session_id,
        context_hint=request.context_hint,
        include_predictions=True,
        include_gems=True
    )
    
    # Build response
    response_text = ai_response.get("response", "I can help you with that.")
    
    # Add action summaries to response
    if actions_executed:
        action_summary = "\n\n**Actions Executed:**\n" + "\n".join([
            f"✓ {a['type'].replace('_', ' ').title()}: {a.get('coin', a.get('destination', a.get('found', '')))}"
            for a in actions_executed
        ])
        response_text += action_summary
    
    if gems_found:
        gem_summary = "\n\n**💎 Hidden Gems Found:**\n" + "\n".join([
            f"• **{g['symbol']}** - Score: {g['total_score']:.0f} ({g['gem_rating']})"
            for g in gems_found
        ])
        response_text += gem_summary
    
    return {
        "response": response_text,
        "query": request.query,
        "session_id": request.session_id,
        "actions_executed": actions_executed,
        "actions_to_execute": actions_to_execute,
        "coins_mentioned": ai_response.get("coins_mentioned", []),
        "predictions": ai_response.get("predictions"),
        "gems": [g['symbol'] for g in gems_found] if gems_found else ai_response.get("gems", []),
        "gems_data": gems_found,
        "timestamp": datetime.utcnow().isoformat(),
        "error": False
    }


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
