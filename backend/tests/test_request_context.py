import logging

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
