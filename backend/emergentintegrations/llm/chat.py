"""
Minimal fallback implementation of emergentintegrations.llm.chat
to keep the app working when the real package is unavailable.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
import asyncio


@dataclass
class UserMessage:
    text: str


class LlmChat:
    def __init__(
        self,
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
        system_message: Optional[str] = None,
    ):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message
        self.model_provider = None
        self.model_name = None

    def with_model(self, provider: str, model: str) -> "LlmChat":
        self.model_provider = provider
        self.model_name = model
        return self

    async def send_message(self, user_message: UserMessage) -> str:
        """
        Simple deterministic response to emulate an LLM call.
        Always returns neutral sentiment with a short summary.
        """
        # Simulate minimal latency to preserve async expectations
        await asyncio.sleep(0)
        return (
            '{"score": 50, "label": "neutral", "confidence": 50, '
            '"summary": "Fallback response (LLM unavailable)", '
            '"key_factors": [], "bullish_signals": [], "bearish_signals": []}'
        )

