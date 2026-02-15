"""Venice.ai LLM Integration Service

Provides AI capabilities using Venice.ai API with DeepSeek R1 model.
Used for Natural Language Strategy Builder and AI Trading Copilot.
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

class VeniceLLM:
    """Venice.ai LLM Client for AI-powered trading features."""
    
    BASE_URL = "https://api.venice.ai/api/v1"
    DEFAULT_MODEL = "deepseek-ai-DeepSeek-R1"  # DeepSeek R1 reasoning model
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("VENICE_API_KEY")
        if not self.api_key:
            raise ValueError("VENICE_API_KEY not found in environment")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a chat completion request to Venice.ai."""
        model = model or self.DEFAULT_MODEL
        
        # Add conversation history if session exists
        if session_id and session_id in self.conversation_history:
            full_messages = self.conversation_history[session_id] + messages
        else:
            full_messages = messages
        
        payload = {
            "model": model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # Store conversation history
                if session_id:
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].extend(messages)
                    if result.get("choices"):
                        self.conversation_history[session_id].append(
                            result["choices"][0]["message"]
                        )
                
                return result
                
        except httpx.HTTPStatusError as e:
            return {
                "error": True,
                "message": f"API error: {e.response.status_code}",
                "details": str(e)
            }
        except Exception as e:
            return {
                "error": True,
                "message": "Connection error",
                "details": str(e)
            }
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
    
    async def parse_natural_language_strategy(self, user_input: str) -> Dict[str, Any]:
        """Parse natural language into a trading strategy."""
        system_prompt = """You are an expert crypto trading strategy parser. 
Convert natural language trading instructions into structured JSON strategies.

OUTPUT FORMAT (JSON only, no markdown):
{
    "strategy_name": "string",
    "description": "string",
    "entry_conditions": [
        {"indicator": "RSI", "operator": "<", "value": 30, "timeframe": "1h"}
    ],
    "exit_conditions": [
        {"indicator": "RSI", "operator": ">", "value": 70, "timeframe": "1h"}
    ],
    "risk_management": {
        "stop_loss_percent": 5,
        "take_profit_percent": 15,
        "position_size_percent": 10
    },
    "coins": ["BTC", "ETH"],
    "timeframe": "1h",
    "confidence": 0.85
}

Available indicators: RSI, MACD, MACD_SIGNAL, MACD_HISTOGRAM, SMA, EMA, BB_UPPER, BB_LOWER, BB_MIDDLE, VOLUME, PRICE, ATR, STOCH_K, STOCH_D, ADX, OBV, VWAP, FEAR_GREED_INDEX
Available operators: <, >, <=, >=, ==, crosses_above, crosses_below
Available timeframes: 1m, 5m, 15m, 1h, 4h, 1d, 1w

If the user input is unclear, make reasonable assumptions and set confidence lower.
Always return valid JSON."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Convert this to a trading strategy: {user_input}"}
        ]
        
        result = await self.chat_completion(messages, temperature=0.3)
        
        if result.get("error"):
            return result
        
        try:
            content = result["choices"][0]["message"]["content"]
            # Clean up markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            strategy = json.loads(content.strip())
            strategy["raw_input"] = user_input
            strategy["created_at"] = datetime.utcnow().isoformat()
            return {"success": True, "strategy": strategy}
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": "Failed to parse strategy",
                "raw_response": content if 'content' in locals() else str(result),
                "details": str(e)
            }
    
    async def trading_copilot_response(
        self,
        user_message: str,
        session_id: str,
        market_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate AI copilot response for trading assistance."""
        system_prompt = """You are Tethys AI, an expert crypto trading copilot assistant.
You help traders with:
- Market analysis and insights
- Strategy recommendations
- Risk management advice
- Technical indicator explanations
- Portfolio optimization suggestions
- Trading psychology and discipline

Be concise, actionable, and data-driven. Use emojis sparingly for key points.
Always consider risk management in your recommendations.
If you don't know something, say so rather than guessing.

Current capabilities you can help with:
- Explain why AI made a specific prediction
- Suggest entry/exit points
- Analyze market sentiment
- Review portfolio allocation
- Explain technical indicators
- Backtest strategy ideas
"""
        
        context_info = ""
        if market_context:
            context_info = f"\n\nCurrent Market Context:\n{json.dumps(market_context, indent=2)}"
        
        messages = [
            {"role": "system", "content": system_prompt + context_info},
            {"role": "user", "content": user_message}
        ]
        
        result = await self.chat_completion(
            messages,
            temperature=0.7,
            session_id=session_id
        )
        
        if result.get("error"):
            return result
        
        return {
            "success": True,
            "response": result["choices"][0]["message"]["content"],
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
_venice_llm: Optional[VeniceLLM] = None

def get_venice_llm() -> VeniceLLM:
    """Get or create Venice LLM instance."""
    global _venice_llm
    if _venice_llm is None:
        try:
            _venice_llm = VeniceLLM()
        except ValueError as e:
            # Return a dummy instance that returns errors
            return None
    return _venice_llm
