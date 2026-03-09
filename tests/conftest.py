"""Shared test fixtures."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses


@pytest.fixture
def mock_api() -> aioresponses:  # type: ignore[misc]
    """Provide a mock aiohttp session."""
    with aioresponses() as m:
        yield m


BASE_URL = "http://192.168.1.100/api/v1"
