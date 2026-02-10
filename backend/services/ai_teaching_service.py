"""
AI Teaching Service - Master Teacher for Crypto Trading
========================================================
Provides comprehensive educational responses using the Socratic method,
explaining WHO, WHAT, WHEN, WHERE, WHY, and HOW for any topic.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import LLM integration
LLM_AVAILABLE = False
try:
    from emergentintegrations.llm.chat import chat, LlmMessage
    LLM_AVAILABLE = True
except ImportError:
    logger.warning("LLM integration not available - using fallback responses")


class TeachingStyle(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class TopicCategory(str, Enum):
    BASICS = "basics"
    TRADING = "trading"
    TECHNICAL_ANALYSIS = "technical_analysis"
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    RISK_MANAGEMENT = "risk_management"
    DEFI = "defi"
    MARKET_PSYCHOLOGY = "market_psychology"
    BLOCKCHAIN = "blockchain"
    PLATFORM = "platform"


# Comprehensive knowledge base for fallback
KNOWLEDGE_BASE = {
    "what_is_bitcoin": {
        "title": "What is Bitcoin?",
        "who": "Bitcoin was created by an anonymous person or group using the pseudonym Satoshi Nakamoto in 2008.",
        "what": "Bitcoin is the first and largest cryptocurrency - a decentralized digital currency that operates on a peer-to-peer network without intermediaries like banks.",
        "when": "Bitcoin was introduced in 2008 (whitepaper) and launched on January 3, 2009 when the first block (Genesis Block) was mined.",
        "where": "Bitcoin exists on a global, decentralized network of computers (nodes) running the Bitcoin software across every continent.",
        "why": "Created to provide a censorship-resistant, borderless form of money that doesn't require trust in central authorities.",
        "how": "Bitcoin uses blockchain technology - a public ledger secured by cryptography. Miners validate transactions and are rewarded with new BTC.",
        "key_concepts": ["Blockchain", "Mining", "Halving", "Decentralization", "21M supply cap"],
        "practical_tips": [
            "Start by understanding that 1 BTC = 100,000,000 satoshis (sats)",
            "BTC is often called 'digital gold' due to its store of value properties",
            "The supply is capped at 21 million - making it deflationary"
        ]
    },
    "what_is_ethereum": {
        "title": "What is Ethereum?",
        "who": "Ethereum was proposed by Vitalik Buterin in 2013 and developed by a team including Gavin Wood, Charles Hoskinson, and others.",
        "what": "Ethereum is a programmable blockchain platform that enables smart contracts and decentralized applications (dApps). ETH is its native currency.",
        "when": "Ethereum launched on July 30, 2015. It transitioned to Proof of Stake (The Merge) on September 15, 2022.",
        "where": "Ethereum runs on a global network of nodes, with major validator concentrations in the US, Europe, and Asia.",
        "why": "Created to extend blockchain beyond just payments - enabling programmable money and decentralized computing.",
        "how": "Developers write smart contracts in Solidity. Users pay 'gas' fees in ETH to execute transactions and contracts.",
        "key_concepts": ["Smart Contracts", "Gas Fees", "ERC-20 Tokens", "DeFi", "NFTs", "Layer 2"],
        "practical_tips": [
            "ETH is used to pay for all transactions on Ethereum",
            "Gas prices fluctuate based on network demand",
            "Layer 2 solutions like Arbitrum and Optimism offer cheaper transactions"
        ]
    },
    "what_is_defi": {
        "title": "What is DeFi (Decentralized Finance)?",
        "who": "DeFi was pioneered by projects like MakerDAO (2017), Compound, Uniswap, and Aave, built by teams of developers worldwide.",
        "what": "DeFi is a movement to recreate traditional financial services (lending, borrowing, trading) on blockchain without intermediaries.",
        "when": "The 'DeFi Summer' of 2020 saw explosive growth, with TVL going from $1B to $15B in months.",
        "where": "Primarily on Ethereum, but also on Solana, Avalanche, BSC, Arbitrum, and other chains.",
        "why": "To provide open, permissionless, 24/7 financial services accessible to anyone with internet.",
        "how": "Smart contracts automate financial operations. Users interact directly with protocols via wallets.",
        "key_concepts": ["TVL (Total Value Locked)", "Yield Farming", "Liquidity Pools", "AMM", "Lending/Borrowing"],
        "practical_tips": [
            "Always verify smart contract addresses before interacting",
            "Start with small amounts to understand protocols",
            "Understand impermanent loss before providing liquidity"
        ]
    },
    "what_is_technical_analysis": {
        "title": "What is Technical Analysis?",
        "who": "Pioneered by Charles Dow (Dow Theory, 1900s), further developed by traders like William O'Neil, John Murphy, and many others.",
        "what": "Technical Analysis (TA) is the study of past price movements and trading volume to predict future price movements.",
        "when": "Use TA when entering/exiting trades, identifying trends, and setting stop-losses and take-profits.",
        "where": "Applied to any market with price history - stocks, crypto, forex, commodities.",
        "why": "Based on the belief that price action reflects all available information and history tends to repeat.",
        "how": "Analyze charts using indicators (RSI, MACD, Moving Averages), patterns (head & shoulders, triangles), and support/resistance.",
        "key_concepts": ["Support/Resistance", "Trend Lines", "Candlesticks", "RSI", "MACD", "Volume"],
        "practical_tips": [
            "Never rely on a single indicator - use confluence",
            "Higher timeframes are more reliable than lower ones",
            "Volume confirms price movements"
        ]
    },
    "what_is_rsi": {
        "title": "What is RSI (Relative Strength Index)?",
        "who": "Developed by J. Welles Wilder Jr. and introduced in his 1978 book 'New Concepts in Technical Trading Systems'.",
        "what": "RSI is a momentum oscillator measuring the speed and magnitude of price movements on a scale of 0-100.",
        "when": "Use RSI to identify overbought (>70) and oversold (<30) conditions, and potential trend reversals.",
        "where": "Available on all trading platforms and charting tools. Works on any timeframe.",
        "why": "Helps identify when an asset may be overextended and due for a pullback or bounce.",
        "how": "RSI = 100 - (100 / (1 + RS)), where RS = Average Gain / Average Loss over 14 periods (default).",
        "key_concepts": ["Overbought (>70)", "Oversold (<30)", "Divergence", "14-period default"],
        "practical_tips": [
            "RSI divergence (price vs RSI moving opposite) often signals reversals",
            "In strong trends, RSI can stay overbought/oversold for extended periods",
            "Combine with other indicators for confirmation"
        ]
    },
    "what_is_stop_loss": {
        "title": "What is a Stop Loss?",
        "who": "A fundamental risk management tool used by all professional traders and taught in every trading course.",
        "what": "A stop loss is an order to automatically sell an asset when it reaches a specified price, limiting potential losses.",
        "when": "Set a stop loss immediately when entering any trade - BEFORE you enter, not after.",
        "where": "Place stops at logical levels - below support for longs, above resistance for shorts.",
        "why": "To protect capital, remove emotion from exits, and ensure survival in trading.",
        "how": "Calculate position size based on how much you're willing to lose if stop is hit (typically 1-2% of portfolio).",
        "key_concepts": ["Risk/Reward Ratio", "Position Sizing", "ATR-based stops", "Trailing Stops"],
        "practical_tips": [
            "Never move your stop loss further from entry to 'give it room'",
            "A good rule: Risk 1-2% of portfolio per trade maximum",
            "Trailing stops lock in profits as price moves in your favor"
        ]
    },
    "what_is_market_cap": {
        "title": "What is Market Cap?",
        "who": "A standard metric used across all financial markets, adapted for crypto by early exchanges.",
        "what": "Market Cap = Current Price × Circulating Supply. It represents the total market value of a cryptocurrency.",
        "when": "Use market cap to compare relative sizes of cryptocurrencies and assess risk levels.",
        "where": "Displayed on CoinGecko, CoinMarketCap, and all major crypto data platforms.",
        "why": "Helps categorize coins: Large cap (>$10B) = more stable, Small cap (<$1B) = more volatile but higher potential.",
        "how": "Large caps like BTC/ETH are 'safer', while small caps are riskier but can provide 10-100x returns.",
        "key_concepts": ["Circulating Supply", "Fully Diluted Valuation (FDV)", "Large/Mid/Small Cap"],
        "practical_tips": [
            "Fully Diluted Valuation (FDV) accounts for all tokens that will ever exist",
            "Low float + high FDV = potential sell pressure from unlocks",
            "Market cap rank is a quick way to gauge a project's size"
        ]
    },
    "what_is_leverage": {
        "title": "What is Leverage Trading?",
        "who": "Used by professional traders and institutions; now available to retail through exchanges like Kraken, Binance, etc.",
        "what": "Leverage allows you to control a larger position with less capital. 10x leverage = $100 controls $1,000.",
        "when": "Use only when you have a high-conviction trade and solid risk management. NOT for beginners.",
        "where": "Perpetual futures exchanges, margin trading on CEXs. Different regions have different regulations.",
        "why": "To amplify gains (and losses). A 10% move with 10x leverage = 100% gain OR 100% loss.",
        "how": "Borrow funds from the exchange. Pay funding rates. Get liquidated if price moves too far against you.",
        "key_concepts": ["Margin", "Liquidation Price", "Funding Rate", "Cross vs Isolated Margin"],
        "practical_tips": [
            "Start with 2-3x maximum until you understand the risks",
            "Always know your liquidation price BEFORE entering",
            "Funding rates can eat profits in sideways markets"
        ]
    },
    "how_to_read_candlesticks": {
        "title": "How to Read Candlestick Charts",
        "who": "Japanese candlesticks were developed by Munehisa Homma, a Japanese rice trader, in the 1700s.",
        "what": "Candlesticks show Open, High, Low, Close (OHLC) prices for a time period in a visual format.",
        "when": "Used constantly when analyzing price action. Each candle represents one time period (1m, 1h, 1d, etc.).",
        "where": "Every trading platform uses candlestick charts as the default view.",
        "why": "Candlesticks reveal market psychology - who's winning (bulls vs bears) and momentum.",
        "how": "Green/white = close > open (bullish). Red/black = close < open (bearish). Wicks show range.",
        "key_concepts": ["Doji", "Hammer", "Engulfing", "Morning Star", "Evening Star"],
        "practical_tips": [
            "Long wicks show rejection of prices",
            "Body size shows conviction - large bodies = strong moves",
            "Context matters - same pattern means different things in different places"
        ]
    }
}


class AITeachingService:
    """
    Master AI Teacher for crypto trading education.
    Uses the 5W1H framework: Who, What, When, Where, Why, How.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self.llm_available = LLM_AVAILABLE and self.api_key
        
        # Conversation history for context
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Teaching system prompt
        self.system_prompt = """You are a MASTER TEACHER specializing in cryptocurrency, trading, and blockchain technology. 
Your teaching style is clear, engaging, and comprehensive.

For EVERY response, structure your teaching using the 5W1H framework:

📌 **WHO** - Who created it? Who uses it? Who are the key players?
📌 **WHAT** - What is it exactly? What does it do? What are its components?
📌 **WHEN** - When was it created? When should you use it? Timeline of events?
📌 **WHERE** - Where does it exist? Where is it used? Geographic/platform context?
📌 **WHY** - Why does it matter? Why was it created? Why should someone care?
📌 **HOW** - How does it work? How do you use it? Step-by-step explanation?

Additional teaching principles:
1. Use analogies and real-world comparisons
2. Provide practical examples and tips
3. Mention common mistakes to avoid
4. Include relevant numbers and data when helpful
5. Build from simple to complex concepts
6. Use emojis sparingly for visual breaks
7. End with actionable next steps or related topics to explore

Remember: You're teaching someone who wants to DEEPLY understand, not just get a surface-level answer.
Be thorough but engaging. Use formatting (bold, bullets, numbered lists) for readability.

Current market context will be provided when available. Use it to make your teaching relevant and timely."""
    
    async def teach(
        self,
        query: str,
        session_id: str = "default",
        level: TeachingStyle = TeachingStyle.INTERMEDIATE,
        market_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Main teaching method - answers questions with comprehensive explanations.
        """
        
        # Check for quick knowledge base match
        kb_response = self._check_knowledge_base(query)
        
        if self.llm_available:
            return await self._teach_with_llm(query, session_id, level, market_context, kb_response)
        else:
            return self._teach_with_fallback(query, kb_response)
    
    def _check_knowledge_base(self, query: str) -> Optional[Dict]:
        """Check if query matches knowledge base entry"""
        query_lower = query.lower()
        
        # Map common queries to knowledge base keys
        query_mappings = {
            "bitcoin": "what_is_bitcoin",
            "btc": "what_is_bitcoin",
            "ethereum": "what_is_ethereum",
            "eth": "what_is_ethereum",
            "defi": "what_is_defi",
            "technical analysis": "what_is_technical_analysis",
            "ta": "what_is_technical_analysis",
            "rsi": "what_is_rsi",
            "stop loss": "what_is_stop_loss",
            "stop-loss": "what_is_stop_loss",
            "market cap": "what_is_market_cap",
            "marketcap": "what_is_market_cap",
            "leverage": "what_is_leverage",
            "candlestick": "how_to_read_candlesticks",
            "candle": "how_to_read_candlesticks"
        }
        
        for keyword, kb_key in query_mappings.items():
            if keyword in query_lower:
                return KNOWLEDGE_BASE.get(kb_key)
        
        return None
    
    async def _teach_with_llm(
        self,
        query: str,
        session_id: str,
        level: TeachingStyle,
        market_context: Optional[Dict],
        kb_hint: Optional[Dict]
    ) -> Dict[str, Any]:
        """Use LLM for comprehensive teaching response"""
        
        # Build conversation history
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        history = self.conversations[session_id]
        
        # Build context message
        context_parts = []
        
        if market_context:
            context_parts.append(f"Current Market Context:\n- BTC Price: ${market_context.get('btc_price', 'N/A')}\n- Market Sentiment: {market_context.get('sentiment', 'N/A')}")
        
        if kb_hint:
            context_parts.append(f"Reference Information:\n{kb_hint.get('what', '')}")
        
        context_parts.append(f"Student Level: {level.value}")
        
        context = "\n\n".join(context_parts)
        
        # Build messages
        messages = [
            LlmMessage(role="system", content=self.system_prompt),
            LlmMessage(role="system", content=f"Context:\n{context}")
        ]
        
        # Add conversation history (last 6 exchanges)
        for msg in history[-12:]:
            messages.append(LlmMessage(role=msg["role"], content=msg["content"]))
        
        # Add current query
        messages.append(LlmMessage(role="user", content=query))
        
        try:
            response = await chat(
                api_key=self.api_key,
                messages=messages,
                model="gpt-4o-mini"  # Use GPT-4o-mini for teaching
            )
            
            assistant_response = response.content
            
            # Store in history
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": assistant_response})
            
            # Keep history manageable
            if len(history) > 20:
                self.conversations[session_id] = history[-20:]
            
            return {
                "response": assistant_response,
                "session_id": session_id,
                "level": level.value,
                "source": "llm",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "related_topics": self._extract_related_topics(query),
                "follow_up_questions": self._generate_follow_ups(query)
            }
            
        except Exception as e:
            logger.error(f"LLM teaching error: {e}")
            return self._teach_with_fallback(query, kb_hint)
    
    def _teach_with_fallback(self, query: str, kb_hint: Optional[Dict]) -> Dict[str, Any]:
        """Fallback when LLM is not available"""
        
        if kb_hint:
            # Format knowledge base response
            response = f"""# {kb_hint.get('title', 'Topic Overview')}

## 👤 WHO
{kb_hint.get('who', 'Information not available.')}

## 📋 WHAT
{kb_hint.get('what', 'Information not available.')}

## 🕐 WHEN
{kb_hint.get('when', 'Information not available.')}

## 📍 WHERE
{kb_hint.get('where', 'Information not available.')}

## ❓ WHY
{kb_hint.get('why', 'Information not available.')}

## ⚙️ HOW
{kb_hint.get('how', 'Information not available.')}

### 🔑 Key Concepts
{chr(10).join(['• ' + c for c in kb_hint.get('key_concepts', [])])}

### 💡 Practical Tips
{chr(10).join(['• ' + t for t in kb_hint.get('practical_tips', [])])}
"""
        else:
            response = """I can help you learn about many crypto and trading topics! Try asking me about:

**Basics:**
• What is Bitcoin?
• What is Ethereum?
• What is DeFi?
• What is market cap?

**Trading:**
• What is technical analysis?
• What is RSI?
• How to read candlesticks?
• What is a stop loss?
• What is leverage?

**Advanced:**
• How do smart contracts work?
• What are liquidity pools?
• How to analyze on-chain data?

Just ask your question and I'll explain using the 5W1H framework (Who, What, When, Where, Why, How)!
"""
        
        return {
            "response": response,
            "session_id": "default",
            "level": "intermediate",
            "source": "knowledge_base",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "related_topics": self._extract_related_topics(query),
            "follow_up_questions": self._generate_follow_ups(query)
        }
    
    def _extract_related_topics(self, query: str) -> List[str]:
        """Extract related topics for further learning"""
        query_lower = query.lower()
        
        topic_map = {
            "bitcoin": ["Blockchain", "Mining", "Halving", "Store of Value"],
            "ethereum": ["Smart Contracts", "Gas Fees", "DeFi", "Layer 2"],
            "defi": ["Yield Farming", "AMM", "Lending", "Liquidity Pools"],
            "trading": ["Technical Analysis", "Risk Management", "Position Sizing"],
            "rsi": ["MACD", "Moving Averages", "Divergence", "Momentum"],
            "leverage": ["Margin", "Liquidation", "Futures", "Risk Management"]
        }
        
        for keyword, topics in topic_map.items():
            if keyword in query_lower:
                return topics
        
        return ["Bitcoin Basics", "Trading Fundamentals", "Risk Management", "Market Analysis"]
    
    def _generate_follow_ups(self, query: str) -> List[str]:
        """Generate follow-up questions to deepen learning"""
        query_lower = query.lower()
        
        follow_up_map = {
            "bitcoin": [
                "How does Bitcoin mining work?",
                "What is the Bitcoin halving?",
                "How do I store Bitcoin safely?"
            ],
            "ethereum": [
                "What are smart contracts?",
                "How do gas fees work?",
                "What is Layer 2 scaling?"
            ],
            "trading": [
                "How do I manage risk in trading?",
                "What indicators should I learn first?",
                "How do I set stop losses?"
            ],
            "rsi": [
                "What is RSI divergence?",
                "How do I combine RSI with other indicators?",
                "What timeframe should I use for RSI?"
            ]
        }
        
        for keyword, questions in follow_up_map.items():
            if keyword in query_lower:
                return questions
        
        return [
            "What should I learn next?",
            "Can you give me a practical example?",
            "What are common mistakes to avoid?"
        ]
    
    async def get_lesson_plan(self, topic: str, level: TeachingStyle) -> Dict[str, Any]:
        """Generate a structured lesson plan for a topic"""
        
        lessons = {
            "trading_basics": {
                "title": "Trading Fundamentals",
                "modules": [
                    {"name": "Understanding Markets", "duration": "15 min", "topics": ["Supply & Demand", "Order Books", "Market vs Limit Orders"]},
                    {"name": "Reading Charts", "duration": "20 min", "topics": ["Candlesticks", "Timeframes", "Trends"]},
                    {"name": "Basic Indicators", "duration": "25 min", "topics": ["Moving Averages", "RSI", "Volume"]},
                    {"name": "Risk Management", "duration": "20 min", "topics": ["Stop Loss", "Position Sizing", "Risk/Reward"]},
                    {"name": "Your First Trade", "duration": "15 min", "topics": ["Paper Trading", "Trade Journal", "Psychology"]}
                ]
            },
            "technical_analysis": {
                "title": "Technical Analysis Mastery",
                "modules": [
                    {"name": "Price Action Basics", "duration": "20 min", "topics": ["Support/Resistance", "Trend Lines", "Channels"]},
                    {"name": "Candlestick Patterns", "duration": "25 min", "topics": ["Reversal Patterns", "Continuation Patterns", "Doji"]},
                    {"name": "Momentum Indicators", "duration": "25 min", "topics": ["RSI", "MACD", "Stochastic"]},
                    {"name": "Volume Analysis", "duration": "20 min", "topics": ["Volume Profile", "OBV", "Accumulation/Distribution"]},
                    {"name": "Chart Patterns", "duration": "30 min", "topics": ["Head & Shoulders", "Triangles", "Flags"]}
                ]
            },
            "defi": {
                "title": "DeFi Deep Dive",
                "modules": [
                    {"name": "DeFi Foundations", "duration": "20 min", "topics": ["What is DeFi", "Wallets", "Smart Contracts"]},
                    {"name": "DEX Trading", "duration": "25 min", "topics": ["Uniswap", "Slippage", "Liquidity"]},
                    {"name": "Lending & Borrowing", "duration": "25 min", "topics": ["Aave", "Compound", "Collateral"]},
                    {"name": "Yield Farming", "duration": "30 min", "topics": ["LP Tokens", "APY vs APR", "Impermanent Loss"]},
                    {"name": "DeFi Safety", "duration": "20 min", "topics": ["Smart Contract Risk", "Rug Pulls", "Audits"]}
                ]
            }
        }
        
        topic_key = topic.lower().replace(" ", "_")
        plan = lessons.get(topic_key, lessons["trading_basics"])
        
        return {
            "lesson_plan": plan,
            "estimated_time": sum(int(m["duration"].split()[0]) for m in plan["modules"]),
            "level": level.value,
            "prerequisites": self._get_prerequisites(topic_key),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_prerequisites(self, topic: str) -> List[str]:
        """Get prerequisites for a topic"""
        prereqs = {
            "trading_basics": ["Basic understanding of cryptocurrency", "Access to a trading platform"],
            "technical_analysis": ["Trading Basics", "Candlestick Reading"],
            "defi": ["Understanding of Ethereum", "Wallet Setup", "Basic Trading"]
        }
        return prereqs.get(topic, ["Basic crypto knowledge"])


# Global service instance
_teaching_service = None

def get_teaching_service(db=None) -> AITeachingService:
    """Get or create teaching service singleton"""
    global _teaching_service
    if _teaching_service is None:
        _teaching_service = AITeachingService(db)
    return _teaching_service
