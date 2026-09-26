"""FastAPI application for TokenJar modern web and desktop dashboard.

Provides high-performance typed REST endpoints, OpenAPI docs (/docs),
Server-Sent Events (SSE) for live telemetry streaming, and serves the
compiled standalone React 18 single-file HTML dashboard.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from tokenjar.cache.persistent_cache import PersistentCache
from tokenjar.config import TokenJarConfig, load_config
from tokenjar.hooks.manager import HookManager
from tokenjar.rules.manager import RulesManager
from tokenjar.telemetry.stats import tracker
from tokenjar.ui.server import STATIC_DIR, get_system_status

try:
    from fastapi import FastAPI, HTTPException, Request, Response, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
    from pydantic import BaseModel, Field

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = object  # type: ignore
    BaseModel = object  # type: ignore


if FASTAPI_AVAILABLE:
    class ToggleIdeRequest(BaseModel):
        ide: Optional[str] = None
        name: Optional[str] = None
        enable: Optional[bool] = None

    class ConfigUpdateRequest(BaseModel):
        lockfile_shield: Optional[bool] = None
        compact_output: Optional[bool] = None
        prevent_truncation: Optional[bool] = None


def create_app() -> Any:
    """Factory function creating the configured FastAPI application."""
    if not FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI is not installed. Install with `pip install fastapi uvicorn` or `pip install tokenjar[ui]`"
        )

    app = FastAPI(
        title="TokenJar Dashboard API",
        version="1.0.1",
        description="High-performance backend API and event stream for TokenJar AI Token Optimization Engine",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Local origin security / CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:*",
            "http://localhost:*",
            "https://127.0.0.1:*",
            "https://localhost:*",
            "tauri://localhost",
            "http://tauri.localhost",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse, summary="Serve standalone React 18 HTML Dashboard")
    async def serve_index() -> Response:
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file, media_type="text/html")
        return HTMLResponse("<h1>TokenJar UI Static Assets Not Found</h1>", status_code=404)

    @app.get("/api/status", summary="Get live system status, metrics, and IDE states")
    async def api_status() -> dict[str, Any]:
        return get_system_status()

    @app.post("/api/ides/toggle", summary="Toggle TokenJar MCP integration for a specific IDE")
    @app.post("/api/toggle-ide", summary="Toggle TokenJar MCP integration (compatibility alias)")
    async def api_toggle_ide(payload: ToggleIdeRequest) -> dict[str, Any]:
        target = payload.ide or payload.name
        if not target:
            raise HTTPException(status_code=400, detail="Missing 'ide' or 'name' parameter")

        configs = HookManager.get_supported_cli_configs()
        if target not in configs:
            raise HTTPException(status_code=404, detail=f"Unknown IDE: {target}")

        cfg_path = configs[target]
        is_active = False
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "tokenjar" in data.get("mcpServers", {}):
                    is_active = True
            except Exception:
                pass

        if payload.enable is not None:
            should_enable = payload.enable
        else:
            should_enable = not is_active

        if should_enable:
            ok, msg = HookManager._apply_mcp_config_with_backup(cfg_path)
        else:
            ok, msg = HookManager._revert_mcp_config_with_backup(cfg_path)

        return {
            "status": "success" if ok else "error",
            "message": msg,
            "system_status": get_system_status(),
        }

    @app.post("/api/config/update", summary="Dynamically update TokenJar runtime configuration")
    async def api_update_config(payload: ConfigUpdateRequest) -> dict[str, Any]:
        if payload.compact_output is not None:
            RulesManager.set_output_mode(".", enabled=payload.compact_output)

        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "system_status": get_system_status(),
        }

    @app.post("/api/cache/clear", summary="Purge L1 and L2 persistent SQLite cache")
    @app.post("/api/clear-cache", summary="Purge cache (compatibility alias)")
    async def api_clear_cache() -> dict[str, Any]:
        p_cache = PersistentCache()
        p_cache.clear()
        return {
            "status": "success",
            "message": "L2 Persistent Cache purged",
            "system_status": get_system_status(),
        }

    @app.post("/api/stats/reset", summary="Reset session telemetry metrics")
    @app.post("/api/reset-stats", summary="Reset session telemetry metrics (compatibility alias)")
    async def api_reset_stats() -> dict[str, Any]:
        tracker.reset()
        return {
            "status": "success",
            "message": "Telemetry metrics reset",
            "system_status": get_system_status(),
        }

    @app.get("/api/stream", summary="Server-Sent Events (SSE) live telemetry stream")
    async def api_stream_events(request: Request) -> StreamingResponse:
        async def event_generator() -> AsyncGenerator[str, None]:
            while True:
                if await request.is_disconnected():
                    break
                status_data = get_system_status()
                yield f"data: {json.dumps(status_data)}\n\n"
                await asyncio.sleep(2)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return app
