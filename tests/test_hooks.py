from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tokenjar.hooks.manager import (
    HOOK_MARKER_START,
    HookManager,
    is_bypass_active,
)


def test_is_bypass_active(monkeypatch):
    monkeypatch.delenv("RAW", raising=False)
    monkeypatch.delenv("TOKENJAR_BYPASS", raising=False)
    assert not is_bypass_active()

    monkeypatch.setenv("RAW", "1")
    assert is_bypass_active()

    monkeypatch.delenv("RAW", raising=False)
    monkeypatch.setenv("TOKENJAR_BYPASS", "1")
    assert is_bypass_active()


def test_hook_install_and_uninstall(tmp_path: Path):
    test_profile = tmp_path / "test_profile.ps1"

    with patch.object(HookManager, "get_powershell_profile_path", return_value=test_profile):
        # 1. Install
        success, msg = HookManager.install_shell_hook(target_shell="powershell")
        assert success
        assert test_profile.exists()
        content = test_profile.read_text(encoding="utf-8")
        assert HOOK_MARKER_START in content
        assert "function pytest" in content

        # 2. Re-install should be idempotent
        success2, msg2 = HookManager.install_shell_hook(target_shell="powershell")
        assert success2
        assert "already installed" in msg2

        # 3. Uninstall
        success3, msg3 = HookManager.uninstall_shell_hook()
        assert success3
        content_after = test_profile.read_text(encoding="utf-8")
        assert HOOK_MARKER_START not in content_after
        assert "function pytest" not in content_after


def test_enable_all_skips_uninstalled_clis(tmp_path: Path):
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()

    # Patch home and simulate that only AGY is installed, Claude/Cursor/Windsurf are not
    with patch("pathlib.Path.home", return_value=fake_home):

        def fake_is_installed(name):
            return name == "Antigravity (AGY)"

        with patch.object(HookManager, "is_cli_installed", side_effect=fake_is_installed):
            results = HookManager.enable_all(only_installed=True)

            agy_res = next(r for r in results if r[0] == "Antigravity (AGY)")
            claude_res = next(r for r in results if r[0] == "Claude Code")
            cursor_res = next(r for r in results if r[0] == "Cursor")
            windsurf_res = next(r for r in results if r[0] == "Windsurf")

            assert agy_res[1] is True
            assert (fake_home / ".gemini" / "config" / "mcp_config.json").exists()

            # Claude, Cursor, Windsurf must NOT be created
            assert "skipped" in claude_res[2].lower()
            assert not (fake_home / ".claude.json").exists()

            assert "skipped" in cursor_res[2].lower()
            assert not (fake_home / ".cursor").exists()

            assert "skipped" in windsurf_res[2].lower()
            assert not (fake_home / ".codeium").exists()


def test_mcp_config_uses_sys_executable(tmp_path: Path):
    import json
    import sys

    config_path = tmp_path / "mcp_config.json"
    ok, msg = HookManager._apply_mcp_config_with_backup(config_path)
    assert ok
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert "tokenjar" in data["mcpServers"]
    expected_python = sys.executable if sys.executable else "python"
    assert data["mcpServers"]["tokenjar"]["command"] == expected_python


def test_mcp_revert_restores_exact_original_state(tmp_path: Path):
    """Test that reverting MCP configuration restores the exact previous state bit-for-bit."""
    import json

    # Case 1: File already had another MCP server (e.g. postgres)
    orig_config = {
        "mcpServers": {
            "postgres": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres"],
            }
        }
    }
    config_file = tmp_path / "claude_desktop_config.json"
    orig_text = json.dumps(orig_config, indent=2)
    config_file.write_text(orig_text, encoding="utf-8")

    # Step 1: Install / Enable TokenJar
    ok, msg = HookManager._apply_mcp_config_with_backup(config_file)
    assert ok
    installed_data = json.loads(config_file.read_text(encoding="utf-8"))
    assert "tokenjar" in installed_data["mcpServers"]
    assert "postgres" in installed_data["mcpServers"]

    # Step 2: Uninstall / Revert
    revert_ok, revert_msg = HookManager._revert_mcp_config_with_backup(config_file)
    assert revert_ok
    # Must match original text exactly
    restored_text = config_file.read_text(encoding="utf-8")
    assert restored_text == orig_text
    assert not (config_file.with_name(config_file.name + ".ts_bak")).exists()

    # Case 2: File did not exist initially -> must be completely removed on revert
    fresh_file = tmp_path / "new_app" / "mcp.json"
    fresh_file.parent.mkdir(parents=True, exist_ok=True)
    assert not fresh_file.exists()

    ok2, msg2 = HookManager._apply_mcp_config_with_backup(fresh_file)
    assert ok2
    assert fresh_file.exists()

    revert_ok2, revert_msg2 = HookManager._revert_mcp_config_with_backup(fresh_file)
    assert revert_ok2
    # File must be deleted, leaving zero trace
    assert not fresh_file.exists()
    assert not (fresh_file.with_name(fresh_file.name + ".ts_bak")).exists()


def test_mcp_revert_preserves_newly_added_user_servers(tmp_path: Path):
    """Test that if the user adds a new MCP server while TokenJar was installed,
    reverting TokenJar removes ONLY tokenjar and preserves the user's new server!
    """
    import json

    config_file = tmp_path / "claude_desktop_config.json"

    # Step 1: TokenJar is installed on a fresh system
    ok, msg = HookManager._apply_mcp_config_with_backup(config_file)
    assert ok

    # Step 2: While TokenJar was running, the user manually adds GitHub MCP server
    data = json.loads(config_file.read_text(encoding="utf-8"))
    data["mcpServers"]["github"] = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
    }
    config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Step 3: User uninstalls / unticks TokenJar
    revert_ok, revert_msg = HookManager._revert_mcp_config_with_backup(config_file)
    assert revert_ok
    assert "preserved" in revert_msg.lower()

    # Step 4: Verify that tokenjar was removed, but github is 100% PRESERVED!
    assert config_file.exists()  # Must not be deleted!
    after_data = json.loads(config_file.read_text(encoding="utf-8"))
    assert "tokenjar" not in after_data["mcpServers"]
    assert "github" in after_data["mcpServers"]
    assert after_data["mcpServers"]["github"]["command"] == "npx"
