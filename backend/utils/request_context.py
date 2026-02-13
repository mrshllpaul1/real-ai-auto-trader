"""
Request context helpers for debug logging.
Adds request_id correlation to logs without eager imports.
"""

from __future__ import annotations

import contextvars
import logging
from typing import Optional

_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    _request_id_var.set(request_id)


def clear_request_id() -> None:
    """Clear the request ID from the current context."""
    _request_id_var.set(None)


def get_request_id() -> Optional[str]:
    """Return the current request ID if available."""
    return _request_id_var.get()


class RequestIdFilter(logging.Filter):
    """Logging filter to inject request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True
