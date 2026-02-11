import asyncio
import json
import os
import sys

import pytest

# Ensure local packages are importable when running from repository root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from emergentintegrations.llm.chat import LlmChat, UserMessage


def test_with_model_returns_self_and_sets_fields():
    chat = LlmChat(api_key="dummy", session_id="s1", system_message="sys")
    returned = chat.with_model("openai", "gpt-5.2")

    assert returned is chat
    assert chat.model_provider == "openai"
    assert chat.model_name == "gpt-5.2"


def test_send_message_returns_fallback_json():
    chat = LlmChat()
    raw = asyncio.run(chat.send_message(UserMessage(text="hello")))

    assert raw == chat.FALLBACK_JSON
    data = json.loads(raw)
    assert data["label"] == "neutral"
    assert 0 <= data["score"] <= 100
    assert 0 <= data["confidence"] <= 100
