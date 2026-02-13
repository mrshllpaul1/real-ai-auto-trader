"""
AI Chat API Routes
Provides conversational AI interface for crypto trading queries.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/ai-chat", tags=["AI Chat"])

# Dependencies
_db = None
_chat_service = None
_kraken_service = None

def set_dependencies(db, chat_service):
    """Set dependencies from server.py"""
    global _db, _chat_service
    _db = db
    _chat_service = chat_service


def set_kraken_service(kraken_service):
    """Set Kraken service for trade execution"""
    global _kraken_service
    _kraken_service = kraken_service


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


class TradeExecutionRequest(BaseModel):
    action: str  # "buy" or "sell"
    coin: str  # BTC, ETH, etc.
    amount_usd: Optional[float] = None
    amount_coin: Optional[float] = None
    order_type: str = "market"  # "market" or "limit"
    limit_price: Optional[float] = None
    confirm: bool = False  # Must be True to execute


# Global gem predictor reference
_gem_predictor = None

def set_gem_predictor(predictor):
    global _gem_predictor
    _gem_predictor = predictor


# Pending trade confirmations (in-memory, for confirmation flow)
_pending_trades = {}


@router.post("/execute-trade")
async def execute_trade_command(request: TradeExecutionRequest):
    """
    Execute a real trade via AI chat command.
    
    IMPORTANT: This executes REAL trades on Kraken!
    
    Flow:
    1. First call with confirm=False to get trade preview
    2. Second call with confirm=True to execute the trade
    
    Example:
    - {"action": "buy", "coin": "BTC", "amount_usd": 100, "confirm": false} -> Preview
    - {"action": "buy", "coin": "BTC", "amount_usd": 100, "confirm": true} -> Execute
    """
    if not _kraken_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized. Kraken API not connected.")
    
    action = request.action.lower()
    if action not in ["buy", "sell"]:
        raise HTTPException(status_code=400, detail="Action must be 'buy' or 'sell'")
    
    coin = request.coin.upper()
    
    # Kraken pair mapping
    kraken_pairs = {
        "BTC": "XXBTZUSD", "ETH": "XETHZUSD", "SOL": "SOLUSD", "XRP": "XXRPZUSD",
        "ADA": "ADAUSD", "DOT": "DOTUSD", "AVAX": "AVAXUSD", "LINK": "LINKUSD",
        "MATIC": "MATICUSD", "UNI": "UNIUSD", "ATOM": "ATOMUSD", "LTC": "XLTCZUSD",
        "AAVE": "AAVEUSD", "APT": "APTUSD", "SUI": "SUIUSD", "DOGE": "XDGUSD"
    }
    
    pair = kraken_pairs.get(coin)
    if not pair:
        raise HTTPException(status_code=400, detail=f"Coin {coin} not supported for trading. Supported: {list(kraken_pairs.keys())}")
    
    try:
        # Get current price
        ticker = await _kraken_service.get_ticker(pair)
        if not ticker:
            raise HTTPException(status_code=400, detail=f"Could not get price for {coin}")
        
        current_price = float(ticker.get('c', [0])[0])  # 'c' is last trade close
        
        # Calculate volume
        if request.amount_usd:
            volume = request.amount_usd / current_price
        elif request.amount_coin:
            volume = request.amount_coin
        else:
            raise HTTPException(status_code=400, detail="Must specify amount_usd or amount_coin")
        
        # Minimum order check (Kraken has minimums)
        min_orders = {"BTC": 0.0001, "ETH": 0.01, "SOL": 0.1, "XRP": 10, "ADA": 10, "DOGE": 50}
        min_vol = min_orders.get(coin, 0.1)
        
        if volume < min_vol:
            raise HTTPException(status_code=400, detail=f"Order too small. Minimum for {coin}: {min_vol}")
        
        trade_preview = {
            "action": action,
            "coin": coin,
            "pair": pair,
            "volume": round(volume, 8),
            "price": current_price,
            "total_usd": round(volume * current_price, 2),
            "order_type": request.order_type,
            "limit_price": request.limit_price if request.order_type == "limit" else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not request.confirm:
            # Return preview, require confirmation
            trade_id = f"{action}_{coin}_{datetime.utcnow().timestamp()}"
            _pending_trades[trade_id] = trade_preview
            
            return {
                "status": "confirmation_required",
                "trade_id": trade_id,
                "preview": trade_preview,
                "message": f"⚠️ CONFIRM: {action.upper()} {volume:.6f} {coin} at ${current_price:.2f} = ${trade_preview['total_usd']:.2f} USD",
                "instruction": "Set confirm=true to execute this trade",
                "warning": "This will execute a REAL trade on your Kraken account!"
            }
        
        # Execute the trade
        order_result = await _kraken_service.create_order(
            symbol=pair,
            side=action,
            order_type=request.order_type,
            volume=volume,
            price=request.limit_price if request.order_type == "limit" else None
        )
        
        if not order_result:
            raise HTTPException(status_code=500, detail="Order execution failed")
        
        # Log trade to database
        trade_record = {
            "source": "ai_chat",
            "action": action,
            "coin": coin,
            "pair": pair,
            "volume": volume,
            "price": current_price,
            "total_usd": trade_preview['total_usd'],
            "order_type": request.order_type,
            "order_result": order_result,
            "executed_at": datetime.utcnow(),
            "success": True
        }
        
        if _db:
            await _db.ai_chat_trades.insert_one(trade_record)
        
        return {
            "status": "executed",
            "success": True,
            "trade": trade_preview,
            "order_result": order_result,
            "message": f"✅ Successfully {action.upper()} {volume:.6f} {coin} at ${current_price:.2f}",
            "total_usd": trade_preview['total_usd'],
            "txid": order_result.get('txid', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed trade attempt
        if _db:
            await _db.ai_chat_trades.insert_one({
                "source": "ai_chat",
                "action": action,
                "coin": coin,
                "error": str(e),
                "attempted_at": datetime.utcnow(),
                "success": False
            })
        raise HTTPException(status_code=500, detail=f"Trade execution error: {str(e)}")


@router.get("/trade-history")
async def get_ai_trade_history(limit: int = 20):
    """Get history of trades executed via AI chat"""
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    trades = await _db.ai_chat_trades.find(
        {}, {"_id": 0}
    ).sort("executed_at", -1).limit(limit).to_list(limit)
    
    return {
        "count": len(trades),
        "trades": trades
    }


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
    
    # 11. Event Detection intents
    event_data = None
    if any(word in query for word in ["what happened", "what caused", "why did", "event", "crash", "pump", "dump"]):
        try:
            from services.event_correlation_engine import get_correlation_engine
            from services.historical_events_db import get_historical_events_db
            
            correlation_engine = get_correlation_engine()
            events_db = get_historical_events_db()
            
            if correlation_engine and events_db:
                # Parse for date
                import re
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', query)
                
                # Parse for coin
                coin_pattern = r'\b(btc|eth|sol|ada|dot|avax|bnb|xrp|doge|shib|matic|link|uni|atom|ltc|luna|ftt)\b'
                coin_match = re.search(coin_pattern, query, re.IGNORECASE)
                coin = coin_match.group(1).upper() if coin_match else None
                
                if date_match:
                    # Query specific date
                    query_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    
                    if coin:
                        # Get what caused price change
                        movements = await correlation_engine.find_price_movements(
                            coin, 
                            query_date - timedelta(days=1),
                            query_date + timedelta(days=1),
                            threshold_pct=2.0
                        )
                        
                        if movements:
                            news = await correlation_engine.find_news_around_event(
                                coin, movements[0]["timestamp"], hours_before=48
                            )
                            correlation = await correlation_engine.correlate_event(movements[0], news)
                            event_data = {
                                "type": "price_event",
                                "coin": coin,
                                "date": date_match.group(1),
                                "price_change": f"{movements[0]['change_pct']:+.2f}%",
                                "likely_cause": correlation.get("likely_cause"),
                                "related_news": [n["title"] for n in correlation.get("correlated_news", [])[:3]]
                            }
                            actions_executed.append({"type": "event_detected", "data": event_data})
                    else:
                        # Get events on date
                        events = await correlation_engine.find_events_for_date(query_date)
                        if events.get("events"):
                            event_data = {
                                "type": "date_events",
                                "date": date_match.group(1),
                                "events_count": events.get("events_found", 0),
                                "top_events": [e["title"] for e in events.get("events", [])[:5]]
                            }
                            actions_executed.append({"type": "events_found", "count": events.get("events_found", 0)})
                
                elif coin:
                    # Get events for coin
                    events = await events_db.get_events_for_coin(coin, limit=10)
                    if events:
                        event_data = {
                            "type": "coin_events",
                            "coin": coin,
                            "events": [{"date": e["date"], "event": e["event"], "impact": e["impact"]} for e in events[:5]]
                        }
                        actions_executed.append({"type": "coin_events_fetched", "coin": coin, "count": len(events)})
                
                else:
                    # Search by keyword
                    keywords = ["elon", "ftx", "luna", "hack", "etf", "sec", "halving", "crash"]
                    for kw in keywords:
                        if kw in query.lower():
                            events = await events_db.search_events(kw, limit=10)
                            if events:
                                event_data = {
                                    "type": "keyword_events",
                                    "keyword": kw,
                                    "events": [{"date": e["date"], "event": e["event"]} for e in events[:5]]
                                }
                                actions_executed.append({"type": "event_search", "keyword": kw, "count": len(events)})
                            break
                            
        except Exception as e:
            print(f"Event detection error: {e}")
    
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
    
    # Add event data to response
    if event_data:
        if event_data["type"] == "price_event":
            likely_cause = event_data.get("likely_cause")
            event_summary = f"\n\n**📰 Event Analysis for {event_data['coin']} on {event_data['date']}:**\n"
            event_summary += f"• Price Change: {event_data['price_change']}\n"
            if likely_cause:
                event_summary += f"• Likely Cause: {likely_cause.get('title', 'Unknown')}\n"
                event_summary += f"• Category: {likely_cause.get('category', 'general').title()}\n"
                event_summary += f"• Confidence: {likely_cause.get('confidence', 0)}%\n"
            if event_data.get("related_news"):
                event_summary += "• Related News:\n" + "\n".join([f"  - {n}" for n in event_data["related_news"][:3]])
            response_text += event_summary
        
        elif event_data["type"] == "coin_events":
            event_summary = f"\n\n**📅 Major Events for {event_data['coin']}:**\n"
            for e in event_data.get("events", []):
                impact_emoji = "📈" if e["impact"] == "positive" else "📉" if e["impact"] == "negative" else "↔️"
                event_summary += f"• {e['date']}: {impact_emoji} {e['event']}\n"
            response_text += event_summary
        
        elif event_data["type"] == "keyword_events":
            event_summary = f"\n\n**🔍 Events matching '{event_data['keyword']}':**\n"
            for e in event_data.get("events", []):
                event_summary += f"• {e['date']}: {e['event']}\n"
            response_text += event_summary
    
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
        "event_data": event_data,
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
