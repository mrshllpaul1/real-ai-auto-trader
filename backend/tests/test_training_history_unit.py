import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest
from bson import ObjectId

from services.training_history import TrainingHistoryService


class _FakeResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _FakeAggregateCursor:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = items

    async def to_list(self, length: int):
        return self._items[:length]


class _FakeFindCursor:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = items
        self._limit = None

    def sort(self, field, order):
        reverse = order == -1
        self._items.sort(key=lambda d: d.get(field), reverse=reverse)
        return self

    def limit(self, limit: int):
        self._limit = limit
        return self

    async def to_list(self, length: int):
        limit = self._limit or length
        return self._items[:limit]


class FakeCollection:
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []

    async def create_index(self, *args, **kwargs):
        return None

    async def insert_one(self, doc: Dict[str, Any]):
        doc = dict(doc)
        doc["_id"] = ObjectId()
        self.docs.append(doc)
        return _FakeResult(doc["_id"])

    async def find_one(self, query: Dict[str, Any], sort=None, **kwargs):
        MISSING = object()

        def get_nested(doc: Dict[str, Any], path: str, default=MISSING):
            """Retrieve nested dict value using dot notation, returning default when missing."""
            value: Any = doc
            for part in path.split("."):
                if not isinstance(value, dict):
                    return default
                value = value.get(part, MISSING)
                if value is MISSING:
                    return default
            return value

        def matches(doc: Dict[str, Any], key: str, expected: Any) -> bool:
            """Check if document matches expected value, supporting $exists semantics."""
            if isinstance(expected, dict) and "$exists" in expected:
                exists = expected["$exists"]
                return (get_nested(doc, key, MISSING) is not MISSING) == exists
            return get_nested(doc, key, MISSING) == expected

        filtered = [doc for doc in self.docs if all(matches(doc, k, v) for k, v in query.items())]
        if sort and filtered:
            def make_sort_key(field_name: str):
                """Create sort key treating missing values as greater (Mongo-like ordering)."""
                def sort_key(doc: Dict[str, Any]):
                    value = get_nested(doc, field_name, MISSING)
                    if value is MISSING:
                        return (1, None)
                    return (0, value)
                return sort_key

            for field, direction in reversed(sort):
                reverse = direction == -1
                sort_key = make_sort_key(field)
                filtered.sort(key=sort_key, reverse=reverse)
        return filtered[0] if filtered else None

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                sets = update.get("$set", {})
                doc.update(sets)
                return None
        return None

    def find(self, query: Dict[str, Any], projection: Dict[str, int]):
        filtered = []
        for doc in self.docs:
            matches = all(doc.get(k) == v for k, v in query.items())
            if matches:
                # Apply projection by excluding _id when requested
                if projection and projection.get("_id") == 0:
                    filtered.append({k: v for k, v in doc.items() if k != "_id"})
                else:
                    filtered.append(dict(doc))
        return _FakeFindCursor(filtered)

    def aggregate(self, pipeline: List[Dict[str, Any]]):
        # Very small subset to support stats aggregation used in service
        match_stage = pipeline[0].get("$match", {})
        grouped_docs = [d for d in self.docs if all(d.get(k) == v for k, v in match_stage.items())]

        stats = {}
        for doc in grouped_docs:
            status = doc.get("status")
            if status not in stats:
                stats[status] = {"count": 0, "durations": []}
            stats[status]["count"] += 1
            if doc.get("duration_seconds") is not None:
                stats[status]["durations"].append(doc["duration_seconds"])

        items = []
        for status, data in stats.items():
            avg = sum(data["durations"]) / len(data["durations"]) if data["durations"] else None
            items.append({"_id": status, "count": data["count"], "avg_duration": avg})

        return _FakeAggregateCursor(items)


class FakeDB:
    def __init__(self):
        self.training_history = FakeCollection()


@pytest.mark.asyncio
async def test_training_history_complete_flow():
    db = FakeDB()
    service = TrainingHistoryService(db)

    session_id = await service.start_training("rl_agent", {"episodes": 1})

    # Simulate time passing to get non-zero duration
    for doc in db.training_history.docs:
        if doc["_id"] == ObjectId(session_id):
            doc["started_at"] = datetime.now(timezone.utc) - timedelta(seconds=2)

    await service.complete_training(session_id, result={"status": "ok"}, metrics={"loss": 0.1})
    history = await service.get_history(model_type="rl_agent")
    stats = await service.get_model_stats("rl_agent")

    assert len(history) == 1
    entry = history[0]
    assert entry["status"] == "completed"
    assert entry["duration_seconds"] is not None
    assert entry["metrics"]["loss"] == 0.1

    assert stats["completed"] == 1
    assert stats["total_sessions"] == 1
    assert stats["avg_duration_seconds"] is not None
    assert stats["success_rate"] == 100.0


@pytest.mark.asyncio
async def test_training_history_best_result_and_stats():
    db = FakeDB()
    service = TrainingHistoryService(db)

    now = datetime.now(timezone.utc)
    db.training_history.docs.extend([
        {
            "_id": ObjectId(),
            "model_type": "rl_agent",
            "status": "completed",
            "duration_seconds": 5,
            "result": {"val_accuracy": 0.7},
            "completed_at": now
        },
        {
            "_id": ObjectId(),
            "model_type": "rl_agent",
            "status": "completed",
            "duration_seconds": 7,
            "result": {"val_accuracy": 0.9},
            "completed_at": now + timedelta(seconds=1)
        },
        {
            "_id": ObjectId(),
            "model_type": "rl_agent",
            "status": "failed",
            "duration_seconds": 3,
            "completed_at": now
        }
    ])

    stats = await service.get_model_stats("rl_agent")
    assert stats["best_result"]["val_accuracy"] == 0.9
    assert stats["completed"] == 2
    assert stats["failed"] == 1
    assert stats["total_sessions"] == 3
    assert stats["success_rate"] == pytest.approx(66.7, rel=1e-2)
