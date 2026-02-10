"""
AI Teaching API Routes
======================
Endpoints for the AI Master Teacher functionality.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-teach", tags=["AI Teaching"])

# Dependencies
_db = None
_teaching_service = None


def set_dependencies(db):
    """Set dependencies from server.py"""
    global _db, _teaching_service
    _db = db
    
    from services.ai_teaching_service import get_teaching_service
    _teaching_service = get_teaching_service(db)


class TeachRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    level: Optional[str] = "intermediate"  # beginner, intermediate, advanced, expert
    include_market_context: Optional[bool] = True


class LessonPlanRequest(BaseModel):
    topic: str
    level: Optional[str] = "intermediate"


@router.post("/ask")
async def ask_teacher(request: TeachRequest):
    """
    Ask the AI Teacher anything about crypto, trading, or blockchain.
    
    The teacher will respond using the 5W1H framework:
    - WHO: Who created it? Who uses it?
    - WHAT: What is it? What does it do?
    - WHEN: When was it created? When to use it?
    - WHERE: Where does it exist? Where is it used?
    - WHY: Why does it matter? Why was it created?
    - HOW: How does it work? How to use it?
    """
    if not _teaching_service:
        raise HTTPException(status_code=503, detail="Teaching service not initialized")
    
    # Get market context if requested
    market_context = None
    if request.include_market_context:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Get BTC price
                response = await client.get(
                    "https://api.kraken.com/0/public/Ticker",
                    params={"pair": "XXBTZUSD"}
                )
                data = response.json()
                if data.get("result"):
                    for key, ticker in data["result"].items():
                        btc_price = float(ticker['c'][0])
                        break
                else:
                    btc_price = None
                
                # Get Fear & Greed
                fg_response = await client.get("https://api.alternative.me/fng/?limit=1")
                fg_data = fg_response.json()
                sentiment = fg_data.get("data", [{}])[0].get("value_classification", "Unknown")
                
                market_context = {
                    "btc_price": btc_price,
                    "sentiment": sentiment
                }
        except Exception as e:
            logger.debug(f"Could not fetch market context: {e}")
    
    # Map level string to enum
    from services.ai_teaching_service import TeachingStyle
    level_map = {
        "beginner": TeachingStyle.BEGINNER,
        "intermediate": TeachingStyle.INTERMEDIATE,
        "advanced": TeachingStyle.ADVANCED,
        "expert": TeachingStyle.EXPERT
    }
    level = level_map.get(request.level, TeachingStyle.INTERMEDIATE)
    
    # Get teaching response
    result = await _teaching_service.teach(
        query=request.query,
        session_id=request.session_id,
        level=level,
        market_context=market_context
    )
    
    # Store in history
    if _db:
        try:
            await _db.teaching_history.insert_one({
                "session_id": request.session_id,
                "query": request.query,
                "response_preview": result.get("response", "")[:200],
                "level": request.level,
                "source": result.get("source"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.debug(f"Could not store teaching history: {e}")
    
    return result


@router.get("/topics")
async def get_available_topics():
    """Get list of available learning topics"""
    return {
        "topics": [
            {
                "category": "Basics",
                "items": [
                    {"id": "bitcoin", "title": "What is Bitcoin?", "difficulty": "beginner"},
                    {"id": "ethereum", "title": "What is Ethereum?", "difficulty": "beginner"},
                    {"id": "blockchain", "title": "How does blockchain work?", "difficulty": "beginner"},
                    {"id": "wallets", "title": "Crypto wallets explained", "difficulty": "beginner"},
                    {"id": "exchanges", "title": "Understanding exchanges", "difficulty": "beginner"}
                ]
            },
            {
                "category": "Trading",
                "items": [
                    {"id": "technical_analysis", "title": "Technical Analysis Basics", "difficulty": "intermediate"},
                    {"id": "candlesticks", "title": "Reading Candlestick Charts", "difficulty": "intermediate"},
                    {"id": "indicators", "title": "Trading Indicators (RSI, MACD)", "difficulty": "intermediate"},
                    {"id": "risk_management", "title": "Risk Management Essentials", "difficulty": "intermediate"},
                    {"id": "leverage", "title": "Leverage Trading", "difficulty": "advanced"}
                ]
            },
            {
                "category": "DeFi",
                "items": [
                    {"id": "defi_basics", "title": "What is DeFi?", "difficulty": "intermediate"},
                    {"id": "yield_farming", "title": "Yield Farming Explained", "difficulty": "advanced"},
                    {"id": "liquidity_pools", "title": "Liquidity Pools & AMMs", "difficulty": "advanced"},
                    {"id": "lending", "title": "DeFi Lending & Borrowing", "difficulty": "advanced"},
                    {"id": "impermanent_loss", "title": "Understanding Impermanent Loss", "difficulty": "expert"}
                ]
            },
            {
                "category": "Advanced",
                "items": [
                    {"id": "onchain", "title": "On-Chain Analysis", "difficulty": "advanced"},
                    {"id": "tokenomics", "title": "Tokenomics Deep Dive", "difficulty": "advanced"},
                    {"id": "market_psychology", "title": "Market Psychology", "difficulty": "advanced"},
                    {"id": "quant_trading", "title": "Quantitative Trading", "difficulty": "expert"},
                    {"id": "mev", "title": "MEV & Arbitrage", "difficulty": "expert"}
                ]
            }
        ],
        "quick_questions": [
            "What is Bitcoin and why does it matter?",
            "How do I read candlestick charts?",
            "What is RSI and how do I use it?",
            "Explain DeFi like I'm 5",
            "What's the difference between market cap and fully diluted value?",
            "How do stop losses work?",
            "What is leverage trading and is it risky?",
            "How do liquidity pools work?",
            "What causes crypto bull and bear markets?",
            "How do I manage risk in trading?"
        ]
    }


@router.post("/lesson-plan")
async def get_lesson_plan(request: LessonPlanRequest):
    """Get a structured lesson plan for a topic"""
    if not _teaching_service:
        raise HTTPException(status_code=503, detail="Teaching service not initialized")
    
    from services.ai_teaching_service import TeachingStyle
    level_map = {
        "beginner": TeachingStyle.BEGINNER,
        "intermediate": TeachingStyle.INTERMEDIATE,
        "advanced": TeachingStyle.ADVANCED,
        "expert": TeachingStyle.EXPERT
    }
    level = level_map.get(request.level, TeachingStyle.INTERMEDIATE)
    
    return await _teaching_service.get_lesson_plan(request.topic, level)


@router.get("/glossary")
async def get_crypto_glossary(
    letter: Optional[str] = Query(None, description="Filter by first letter"),
    search: Optional[str] = Query(None, description="Search term")
):
    """Get crypto glossary terms"""
    
    glossary = [
        {"term": "ATH", "definition": "All-Time High - The highest price ever reached by an asset."},
        {"term": "ATL", "definition": "All-Time Low - The lowest price ever reached by an asset."},
        {"term": "Airdrop", "definition": "Free distribution of tokens to wallet addresses, often as a marketing strategy."},
        {"term": "AMM", "definition": "Automated Market Maker - A DEX mechanism using liquidity pools instead of order books."},
        {"term": "APR", "definition": "Annual Percentage Rate - Simple interest rate per year without compounding."},
        {"term": "APY", "definition": "Annual Percentage Yield - Interest rate accounting for compound interest."},
        {"term": "Arbitrage", "definition": "Profiting from price differences of the same asset across different markets."},
        {"term": "Bag", "definition": "A significant holding of a particular cryptocurrency."},
        {"term": "Bear Market", "definition": "Extended period of declining prices, typically 20%+ from recent highs."},
        {"term": "Bull Market", "definition": "Extended period of rising prices and positive sentiment."},
        {"term": "CEX", "definition": "Centralized Exchange - Trading platform operated by a company (e.g., Kraken, Coinbase)."},
        {"term": "Cold Wallet", "definition": "Offline storage for crypto, more secure against hacking."},
        {"term": "DCA", "definition": "Dollar Cost Averaging - Investing fixed amounts at regular intervals."},
        {"term": "DEX", "definition": "Decentralized Exchange - Peer-to-peer trading without intermediaries (e.g., Uniswap)."},
        {"term": "DYOR", "definition": "Do Your Own Research - Reminder to investigate before investing."},
        {"term": "FDV", "definition": "Fully Diluted Valuation - Market cap if all tokens were in circulation."},
        {"term": "FOMO", "definition": "Fear Of Missing Out - Anxiety that drives impulsive buying."},
        {"term": "FUD", "definition": "Fear, Uncertainty, Doubt - Negative information/sentiment, sometimes manipulative."},
        {"term": "Gas", "definition": "Fee paid to execute transactions on Ethereum and similar blockchains."},
        {"term": "HODL", "definition": "Hold On for Dear Life - Long-term holding strategy, originally a typo."},
        {"term": "Impermanent Loss", "definition": "Temporary loss from providing liquidity vs. simply holding."},
        {"term": "Leverage", "definition": "Borrowing to amplify trading positions and potential gains/losses."},
        {"term": "Liquidation", "definition": "Forced closure of a leveraged position when margin is insufficient."},
        {"term": "Liquidity", "definition": "Ease of buying/selling without significant price impact."},
        {"term": "LP Token", "definition": "Token received when providing liquidity to a pool."},
        {"term": "Market Cap", "definition": "Total value = Price × Circulating Supply."},
        {"term": "MEV", "definition": "Maximal Extractable Value - Profit from reordering transactions."},
        {"term": "Moon", "definition": "Dramatic price increase ('going to the moon')."},
        {"term": "NFT", "definition": "Non-Fungible Token - Unique digital asset on blockchain."},
        {"term": "Paper Hands", "definition": "Investor who sells quickly at first sign of trouble."},
        {"term": "Pump and Dump", "definition": "Scheme to inflate price then sell, leaving others with losses."},
        {"term": "RSI", "definition": "Relative Strength Index - Momentum indicator (0-100 scale)."},
        {"term": "Rug Pull", "definition": "Scam where developers abandon project and take funds."},
        {"term": "Slippage", "definition": "Difference between expected and actual trade price."},
        {"term": "Smart Contract", "definition": "Self-executing code on blockchain that enforces agreements."},
        {"term": "Staking", "definition": "Locking crypto to support network operations for rewards."},
        {"term": "TVL", "definition": "Total Value Locked - Assets deposited in a DeFi protocol."},
        {"term": "Whale", "definition": "Large holder who can significantly influence market prices."},
        {"term": "Yield Farming", "definition": "Maximizing returns by moving assets between DeFi protocols."}
    ]
    
    # Filter by letter
    if letter:
        glossary = [g for g in glossary if g["term"].upper().startswith(letter.upper())]
    
    # Filter by search
    if search:
        search_lower = search.lower()
        glossary = [g for g in glossary if search_lower in g["term"].lower() or search_lower in g["definition"].lower()]
    
    return {
        "terms": glossary,
        "count": len(glossary)
    }


@router.get("/quiz/{topic}")
async def get_quiz(topic: str, difficulty: str = "intermediate"):
    """Get a quiz to test knowledge on a topic"""
    
    quizzes = {
        "bitcoin": {
            "title": "Bitcoin Basics Quiz",
            "questions": [
                {
                    "question": "What is the maximum supply of Bitcoin?",
                    "options": ["21 million", "100 million", "1 billion", "Unlimited"],
                    "correct": 0,
                    "explanation": "Bitcoin's supply is capped at 21 million coins, making it deflationary."
                },
                {
                    "question": "Who created Bitcoin?",
                    "options": ["Vitalik Buterin", "Satoshi Nakamoto", "Charles Hoskinson", "Elon Musk"],
                    "correct": 1,
                    "explanation": "Satoshi Nakamoto is the pseudonym of Bitcoin's anonymous creator."
                },
                {
                    "question": "What is a Bitcoin halving?",
                    "options": ["Price dropping 50%", "Mining reward cut in half", "Transaction fees halving", "Block size reduction"],
                    "correct": 1,
                    "explanation": "Halving reduces the mining reward by 50% every ~4 years, controlling supply."
                },
                {
                    "question": "How many satoshis are in 1 Bitcoin?",
                    "options": ["1,000", "1,000,000", "100,000,000", "1,000,000,000"],
                    "correct": 2,
                    "explanation": "1 BTC = 100 million satoshis, the smallest Bitcoin unit."
                }
            ]
        },
        "trading": {
            "title": "Trading Fundamentals Quiz",
            "questions": [
                {
                    "question": "What does RSI measure?",
                    "options": ["Volume", "Momentum/Overbought/Oversold", "Trend direction", "Volatility"],
                    "correct": 1,
                    "explanation": "RSI (Relative Strength Index) measures momentum and identifies overbought (>70) or oversold (<30) conditions."
                },
                {
                    "question": "What is a stop loss?",
                    "options": ["Profit target", "Order to limit losses", "Trading fee", "Position size"],
                    "correct": 1,
                    "explanation": "A stop loss automatically sells when price hits a level to limit losses."
                },
                {
                    "question": "In a candlestick, what does a long upper wick indicate?",
                    "options": ["Strong buying pressure", "Rejection of higher prices", "Low volume", "Trend continuation"],
                    "correct": 1,
                    "explanation": "Long upper wicks show price was rejected at higher levels (selling pressure)."
                },
                {
                    "question": "What's a good risk/reward ratio for trades?",
                    "options": ["1:0.5", "1:1", "1:2 or higher", "Doesn't matter"],
                    "correct": 2,
                    "explanation": "Aim for 1:2+ ratio - risking $1 to potentially make $2+ ensures profitability even with <50% win rate."
                }
            ]
        },
        "defi": {
            "title": "DeFi Knowledge Quiz",
            "questions": [
                {
                    "question": "What does TVL stand for?",
                    "options": ["Total Volume Locked", "Total Value Locked", "Token Value Listed", "Trading Volume Limit"],
                    "correct": 1,
                    "explanation": "TVL (Total Value Locked) measures assets deposited in a DeFi protocol."
                },
                {
                    "question": "What is impermanent loss?",
                    "options": ["Transaction fees", "Loss from holding vs providing liquidity", "Smart contract bug", "Network congestion cost"],
                    "correct": 1,
                    "explanation": "Impermanent loss occurs when providing liquidity and the ratio of tokens changes."
                },
                {
                    "question": "What is an AMM?",
                    "options": ["Advanced Market Maker", "Automated Market Maker", "Annual Management Model", "Asset Money Manager"],
                    "correct": 1,
                    "explanation": "AMM (Automated Market Maker) uses liquidity pools and algorithms instead of order books."
                },
                {
                    "question": "What's the main risk in DeFi?",
                    "options": ["High fees", "Smart contract vulnerabilities", "Slow transactions", "Limited tokens"],
                    "correct": 1,
                    "explanation": "Smart contract bugs/exploits are the primary DeFi risk - always check audits!"
                }
            ]
        }
    }
    
    quiz = quizzes.get(topic.lower(), quizzes.get("bitcoin"))
    
    return {
        "topic": topic,
        "difficulty": difficulty,
        "quiz": quiz
    }


@router.delete("/history/{session_id}")
async def clear_session_history(session_id: str):
    """Clear teaching history for a session"""
    if _teaching_service:
        if session_id in _teaching_service.conversations:
            del _teaching_service.conversations[session_id]
    
    if _db:
        await _db.teaching_history.delete_many({"session_id": session_id})
    
    return {"status": "cleared", "session_id": session_id}
