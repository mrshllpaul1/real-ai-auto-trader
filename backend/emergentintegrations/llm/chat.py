"""
Minimal fallback implementation of emergentintegrations.llm.chat
to keep the app working when the real package is unavailable.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
import json


@dataclass
class UserMessage:
    text: str


class LlmChat:
    FALLBACK_PAYLOAD = {
        # score and confidence follow a 0-100 scale to mirror real LLM outputs
        "score": 50,
        "label": "neutral",
        "confidence": 50,
        "summary": "Fallback response (LLM unavailable)",
        "key_factors": [],
        "bullish_signals": [],
        "bearish_signals": [],
    }
    FALLBACK_JSON = json.dumps(FALLBACK_PAYLOAD)

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
        """Mutates the instance to record the desired model and returns self for chaining."""
        self.model_provider = provider
        self.model_name = model
        return self

    async def send_message(self, _user_message: UserMessage) -> str:
        """
        Simple deterministic response to emulate an LLM call.
        Always returns neutral sentiment with a short summary.

        The async signature is preserved to remain drop-in compatible with the
        real LLM client, even though this stub performs no I/O.

        Args:
            _user_message: message payload (text only); ignored in this stub.

        Returns:
            JSON string containing keys: score, label, confidence, summary,
            key_factors, bullish_signals, bearish_signals.
        """
        return self.FALLBACK_JSON
