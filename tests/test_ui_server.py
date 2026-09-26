"""Unit tests for TokenJar On-Demand Dashboard UI Server."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from http.server import HTTPServer

import pytest

from tokenjar.ui.server import DashboardHandler, get_system_status


@pytest.fixture(scope="module")
def ui_test_server():
    """Start local test server on a free port in a background thread."""
    server = None
    port = 4199
    for p in range(4199, 4210):
        try:
            server = HTTPServer(("127.0.0.1", p), DashboardHandler)
            port = p
            break
        except OSError:
            continue

    if not server:
        pytest.skip("Could not bind test server")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)  # Give server a moment to start
    base_url = f"http://127.0.0.1:{port}"

    yield base_url

    server.shutdown()
    server.server_close()


def test_get_system_status():
    """Test system status gathering function directly."""
    status = get_system_status()
    assert "active" in status
    assert "telemetry" in status
    assert "ides" in status
    assert "config" in status
    assert "total_saved" in status["telemetry"]
    assert "categories" in status["telemetry"]

    ide_names = [ide["name"] for ide in status["ides"]]
    assert "Antigravity (AGY)" in ide_names
    assert "Claude Desktop" in ide_names
    assert "Cursor" in ide_names


def test_ui_http_index(ui_test_server: str):
    """Test serving the dashboard HTML."""
    req = urllib.request.Request(f"{ui_test_server}/")
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        html = response.read().decode("utf-8")
        assert "TOKENJAR" in html
        assert "Total Tokens Saved" in html


def test_ui_http_api_status(ui_test_server: str):
    """Test /api/status endpoint."""
    req = urllib.request.Request(f"{ui_test_server}/api/status")
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode("utf-8"))
        assert "telemetry" in data
        assert "ides" in data
        assert isinstance(data["ides"], list)


def test_ui_http_toggle_output(ui_test_server: str):
    """Test toggling output mode via POST /api/toggle-output."""
    payload = json.dumps({"compact": True}).encode("utf-8")
    req = urllib.request.Request(
        f"{ui_test_server}/api/toggle-output",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode("utf-8"))
        assert data["ok"] is True
        assert "Compact" in data["msg"]


def test_ui_http_prune_cache(ui_test_server: str):
    """Test pruning cache via POST /api/prune-cache."""
    req = urllib.request.Request(
        f"{ui_test_server}/api/prune-cache",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode("utf-8"))
        assert data["ok"] is True


def test_ui_http_origin_security(ui_test_server: str):
    """Test that unauthorized cross-origin requests are rejected with 403 Forbidden."""
    # 1. External malicious origin must be rejected with HTTP 403
    evil_req = urllib.request.Request(
        f"{ui_test_server}/api/status",
        headers={"Origin": "https://evil-attacker.com"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(evil_req)
    assert exc_info.value.code == 403

    # 2. Local origin must be allowed with HTTP 200
    local_req = urllib.request.Request(
        f"{ui_test_server}/api/status",
        headers={"Origin": "http://127.0.0.1:4141"},
    )
    with urllib.request.urlopen(local_req) as response:
        assert response.status == 200
