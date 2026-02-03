"""
AI Chat Service
Provides conversational AI capabilities for crypto trading queries.
Users can ask about coins, strategies, market conditions, news, and more.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import asyncio

from emergentintegrations.llm.chat import LlmChat, UserMessage


class AIChatService:
    """
    AI-powered chat service for crypto trading queries.
    Uses GPT to answer questions about coins, strategies, market, and news.
    """
    
    def __init__(self, db=None, market_service=None, news_service=None):
        self.db = db
        self.market_service = market_service
        self.news_service = news_service
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        self.conversation_history = {}  # Store conversations by session_id
        
        # System prompt for the AI
        self.system_prompt = """You are an expert AI crypto trading assistant for the AICryptoTrade platform. 
You help users with:
- Cryptocurrency analysis and price predictions
- Trading strategies and recommendations
- Market sentiment and news analysis
- Token/coin information and comparisons
- Portfolio advice and risk management

Guidelines:
- Be concise but informative
- Always mention that crypto is volatile and risky
- Provide data-driven insights when available
- If you don't have real-time data, say so
- Format responses with bullet points for readability
- Include confidence levels when making predictions
- Never guarantee profits or specific returns

You have access to:
- Real-time market data from CoinGecko
- News from CryptoPanic
- Deep learning models (LSTM, sentiment analysis, pattern recognition)
- Historical price data and trading patterns
"""

    async def _get_market_context(self, coin_ids: List[str] = None) -> str:
        """Get current market context for the AI"""
        context_parts = []
        
        if not coin_ids:
            coin_ids = ['bitcoin', 'ethereum', 'solana']
        
        if self.market_service:
            try:
                prices = await self.market_service.get_coin_price(coin_ids)
                if prices:
                    price_info = []
                    for coin_id, data in prices.items():
                        if isinstance(data, dict) and 'current_price' in data:
                            price_info.append(
                                f"- {coin_id.title()}: ${data['current_price']:,.2f} "
                                f"(24h: {data.get('price_change_percentage_24h', 0):+.2f}%)"
                            )
                    if price_info:
                        context_parts.append("Current Prices:\n" + "\n".join(price_info))
            except Exception as e:
                print(f"Error getting market context: {e}")
        
        return "\n\n".join(context_parts) if context_parts else ""

    async def _get_news_context(self, limit: int = 5) -> str:
        """Get recent news context for the AI"""
        if self.news_service:
            try:
                news = await self.news_service.get_free_crypto_news(limit=limit)
                if news:
                    news_items = []
                    for item in news[:5]:
                        title = item.get('title', '')[:100]
                        sentiment = item.get('sentiment', 'neutral')
                        news_items.append(f"- [{sentiment.upper()}] {title}")
                    return "Recent News:\n" + "\n".join(news_items)
            except Exception as e:
                print(f"Error getting news context: {e}")
        return ""

    def _extract_coin_mentions(self, query: str) -> List[str]:
        """Extract coin IDs mentioned in the query"""
        query_lower = query.lower()
        coin_mapping = {
            'btc': 'bitcoin', 'bitcoin': 'bitcoin',
            'eth': 'ethereum', 'ethereum': 'ethereum',
            'sol': 'solana', 'solana': 'solana',
            'ada': 'cardano', 'cardano': 'cardano',
            'dot': 'polkadot', 'polkadot': 'polkadot',
            'avax': 'avalanche-2', 'avalanche': 'avalanche-2',
            'bnb': 'binancecoin', 'binance': 'binancecoin',
            'xrp': 'ripple', 'ripple': 'ripple',
            'doge': 'dogecoin', 'dogecoin': 'dogecoin',
            'shib': 'shiba-inu', 'shiba': 'shiba-inu',
            'matic': 'matic-network', 'polygon': 'matic-network',
            'link': 'chainlink', 'chainlink': 'chainlink',
            'uni': 'uniswap', 'uniswap': 'uniswap',
            'atom': 'cosmos', 'cosmos': 'cosmos',
            'ltc': 'litecoin', 'litecoin': 'litecoin',
        }
        
        mentioned = []
        for keyword, coin_id in coin_mapping.items():
            if keyword in query_lower and coin_id not in mentioned:
                mentioned.append(coin_id)
        
        return mentioned if mentioned else ['bitcoin', 'ethereum']

    async def chat(
        self, 
        query: str, 
        session_id: str = "default",
        include_market_data: bool = True,
        include_news: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query and return AI response.
        
        Args:
            query: User's question
            session_id: Session ID for conversation history
            include_market_data: Whether to include current market prices
            include_news: Whether to include recent news
            
        Returns:
            Dict with response, context used, and metadata
        """
        if not self.api_key:
            return {
                "response": "AI service is not configured. Please set up the EMERGENT_LLM_KEY.",
                "error": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        try:
            # Build context
            context_parts = []
            
            # Extract mentioned coins
            mentioned_coins = self._extract_coin_mentions(query)
            
            # Get market context
            if include_market_data:
                market_context = await self._get_market_context(mentioned_coins)
                if market_context:
                    context_parts.append(market_context)
            
            # Get news context
            if include_news and any(kw in query.lower() for kw in ['news', 'sentiment', 'market', 'happening', 'trend']):
                news_context = await self._get_news_context()
                if news_context:
                    context_parts.append(news_context)
            
            # Build the full prompt
            context_str = "\n\n".join(context_parts) if context_parts else ""
            
            full_prompt = f"""User Question: {query}

{f"Current Market Data:{chr(10)}{context_str}" if context_str else ""}

Please provide a helpful, accurate response. If the question is about specific prices or data you don't have, acknowledge that limitation."""

            # Build conversation context for the prompt
            history = self.conversation_history.get(session_id, [])
            history_context = ""
            if history:
                recent_history = history[-4:]  # Last 2 exchanges
                for h in recent_history:
                    history_context += f"\nUser: {h['query']}\nAssistant: {h['response']}\n"
            
            # Build final prompt with history
            if history_context:
                full_prompt = f"""Previous conversation:
{history_context}

Current question: {query}

{f"Current Market Data:{chr(10)}{context_str}" if context_str else ""}

Please provide a helpful, accurate response based on the conversation context."""
            
            # Create LLM chat with system message
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"ai_chat_{session_id}_{datetime.now().strftime('%Y%m%d%H%M')}",
                system_message=self.system_prompt
            ).with_model("openai", "gpt-4o-mini")
            
            # Send message and get response
            response = await chat.send_message(UserMessage(text=full_prompt))
            
            response_text = response if isinstance(response, str) else str(response)
            
            # Update conversation history
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            self.conversation_history[session_id].append({
                "query": query,
                "response": response_text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Keep only last 20 messages
            if len(self.conversation_history[session_id]) > 20:
                self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
            
            # Store in database if available
            if self.db is not None:
                try:
                    await self.db.ai_chat_history.insert_one({
                        "session_id": session_id,
                        "query": query,
                        "response": response_text,
                        "coins_mentioned": mentioned_coins,
                        "context_used": {
                            "market_data": include_market_data,
                            "news": include_news
                        },
                        "timestamp": datetime.now(timezone.utc)
                    })
                except Exception as e:
                    print(f"Error saving chat to DB: {e}")
            
            return {
                "response": response_text,
                "query": query,
                "session_id": session_id,
                "coins_mentioned": mentioned_coins,
                "context": {
                    "market_data_included": include_market_data and len(context_str) > 0,
                    "news_included": include_news
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": False
            }
            
        except Exception as e:
            print(f"AI Chat error: {e}")
            return {
                "response": f"I encountered an error processing your question. Please try again or rephrase your query.",
                "error": True,
                "error_details": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def get_quick_analysis(self, coin_id: str) -> Dict[str, Any]:
        """Get a quick AI analysis for a specific coin"""
        query = f"Give me a brief analysis of {coin_id} including current sentiment, key levels to watch, and short-term outlook."
        return await self.chat(query, session_id=f"quick_{coin_id}", include_news=True)

    async def get_strategy_advice(self, portfolio_value: float, risk_tolerance: str = "moderate") -> Dict[str, Any]:
        """Get AI strategy advice based on portfolio and risk tolerance"""
        query = f"""I have a portfolio worth ${portfolio_value:,.2f} and my risk tolerance is {risk_tolerance}. 
What trading strategy would you recommend for the current market conditions? 
Consider position sizing, diversification, and entry/exit points."""
        return await self.chat(query, session_id="strategy_advice", include_market_data=True, include_news=True)

    async def explain_pattern(self, pattern_name: str, coin_id: str) -> Dict[str, Any]:
        """Get AI explanation of a detected chart pattern"""
        query = f"""Explain the {pattern_name} pattern that was detected for {coin_id}. 
What does this pattern typically indicate? What are the key levels to watch? 
What's the typical success rate and risk/reward ratio?"""
        return await self.chat(query, session_id=f"pattern_{coin_id}")

    def clear_history(self, session_id: str = None):
        """Clear conversation history"""
        if session_id:
            if session_id in self.conversation_history:
                del self.conversation_history[session_id]
        else:
            self.conversation_history = {}

    async def get_chat_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get chat history for a session"""
        if self.db:
            cursor = self.db.ai_chat_history.find(
                {"session_id": session_id}
            ).sort("timestamp", -1).limit(limit)
            history = await cursor.to_list(length=limit)
            # Remove MongoDB _id
            for h in history:
                h.pop('_id', None)
            return list(reversed(history))
        return self.conversation_history.get(session_id, [])


# Singleton instance
_ai_chat_service = None

def get_ai_chat_service(db=None, market_service=None, news_service=None) -> AIChatService:
    """Get or create the AI chat service instance"""
    global _ai_chat_service
    if _ai_chat_service is None:
        _ai_chat_service = AIChatService(db, market_service, news_service)
    return _ai_chat_service

def set_ai_chat_service(service: AIChatService):
    """Set the AI chat service instance"""
    global _ai_chat_service
    _ai_chat_service = service
