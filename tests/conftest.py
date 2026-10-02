"""Shared test fixtures."""

from __future__ import annotations

import inspect
from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock

import pytest
from aiohttp import ClientResponse
from aioresponses import aioresponses

_NEEDS_STREAM_WRITER = (
    "stream_writer" in inspect.signature(ClientResponse.__init__).parameters
)


class _CompatClientResponse(ClientResponse):
    """ClientResponse that aioresponses can build on aiohttp >= 3.14.

    aiohttp 3.14 added the required ``stream_writer`` argument, which
    aioresponses does not pass yet.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        if _NEEDS_STREAM_WRITER:
            kwargs.setdefault("stream_writer", Mock(output_size=0))
        super().__init__(*args, **kwargs)


@pytest.fixture
def mock_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[aioresponses]:
    """Provide a mock aiohttp session."""
    monkeypatch.setattr("aioresponses.core.ClientResponse", _CompatClientResponse)
    with aioresponses() as m:
        yield m


BASE_URL = "http://192.168.1.100/api/v1"
