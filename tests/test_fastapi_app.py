"""Tests for FastAPI TokenJar application module."""

from __future__ import annotations

import pytest
from tokenjar.ui.fastapi_app import FASTAPI_AVAILABLE, create_app


def test_fastapi_app_factory():
    """Verify that create_app behaves appropriately based on FastAPI availability."""
    if FASTAPI_AVAILABLE:
        app = create_app()
        assert app is not None
        assert app.title == "TokenJar Dashboard API"
    else:
        with pytest.raises(ImportError):
            create_app()
