from __future__ import annotations

from tokenjar.server import (
    prompt_optimize_task,
    resource_config,
    resource_guide,
    resource_stats,
)


def test_mcp_resources():
    stats_out = resource_stats()
    assert "TokenJar" in stats_out or "No telemetry" in stats_out or "tokens" in stats_out.lower()

    guide_out = resource_guide()
    assert "TokenJar AI Optimization Guidelines" in guide_out
    assert "read_file_smart" in guide_out

    config_out = resource_config()
    assert "ignore_patterns" in config_out
    assert "max_cacheable_bytes" in config_out


def test_mcp_prompt():
    prompt_text = prompt_optimize_task("Refactor authentication module")
    assert "Refactor authentication module" in prompt_text
    assert "TokenJar AI Optimization Guidelines" in prompt_text
    assert "find_symbol_global" in prompt_text
    assert "read_file_smart" in prompt_text
