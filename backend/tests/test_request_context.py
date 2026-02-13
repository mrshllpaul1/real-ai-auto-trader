import logging

import pytest
from starlette.requests import Request
from starlette.responses import Response

from middleware.error_monitoring import ErrorMonitoringMiddleware
from utils.request_context import (
    RequestIdFilter,
    clear_request_id,
    get_request_id,
    set_request_id,
)


def test_request_id_set_and_clear():
    clear_request_id()
    assert get_request_id() is None
    set_request_id("req-123")
    assert get_request_id() == "req-123"
    clear_request_id()
    assert get_request_id() is None


def test_request_id_filter_defaults():
    clear_request_id()
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "msg", (), None)
    RequestIdFilter().filter(record)
    assert record.request_id == "-"


def test_request_id_filter_uses_context():
    set_request_id("req-456")
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "msg", (), None)
    RequestIdFilter().filter(record)
    assert record.request_id == "req-456"
    clear_request_id()


def _build_request():
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/health",
            "raw_path": b"/api/health",
            "query_string": b"foo=bar",
            "headers": [(b"user-agent", b"pytest")],
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


@pytest.mark.asyncio
async def test_request_id_cleared_after_dispatch_success():
    middleware = ErrorMonitoringMiddleware(app=object())

    async def call_next(_request):
        assert get_request_id() is not None
        return Response("ok")

    response = await middleware.dispatch(_build_request(), call_next)
    assert response.status_code == 200
    assert get_request_id() is None


@pytest.mark.asyncio
async def test_request_id_cleared_after_dispatch_error():
    middleware = ErrorMonitoringMiddleware(app=object())

    async def call_next(_request):
        assert get_request_id() is not None
        raise RuntimeError("boom")

    response = await middleware.dispatch(_build_request(), call_next)
    assert response.status_code == 500
    assert get_request_id() is None
