import os
import sys
import types
from datetime import datetime, timedelta

import pytest

# Stub the emergentintegrations.llm.chat module used by news_service to avoid external dependency
stub_chat = types.ModuleType("emergentintegrations.llm.chat")


class _DummyChat:
    def __init__(self, *_, **__):
        pass

    def with_model(self, *_, **__):
        return self

    async def send_message(self, *_):
        return "{}"


class _DummyUserMessage:
    def __init__(self, text: str):
        self.text = text


stub_chat.LlmChat = _DummyChat
stub_chat.UserMessage = _DummyUserMessage

sys.modules["emergentintegrations"] = types.ModuleType("emergentintegrations")
sys.modules["emergentintegrations.llm"] = types.ModuleType("emergentintegrations.llm")
sys.modules["emergentintegrations.llm.chat"] = stub_chat

# Ensure backend services are importable
BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_PATH not in sys.path:
    sys.path.append(BACKEND_PATH)

from services.news_service import CryptoNewsAggregator


class TestNewsSentimentScoring:
    def test_keywords_in_description_are_counted(self):
        service = CryptoNewsAggregator()
        item = {
            "title": "Bitcoin moves sideways",
            "description": "Major partnership and adoption news boosts outlook",
            "published_at": datetime.now().isoformat(),
            "sentiment": "neutral",
        }

        score, label = service._score_news_item(item)

        assert score > 0, "Positive keywords in description should raise sentiment score"
        assert label == "positive"

    def test_recent_negative_news_has_higher_weight(self):
        service = CryptoNewsAggregator()
        recent_item = {
            "title": "Exchange suffers major hack",
            "published_at": datetime.now().isoformat(),
            "sentiment": "negative",
        }
        old_item = {
            "title": "Exchange suffers major hack",
            "published_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "sentiment": "negative",
        }

        recent_score, _ = service._score_news_item(recent_item)
        old_score, _ = service._score_news_item(old_item)

        assert abs(recent_score) > abs(old_score), "Recent news should weigh more than older news"
