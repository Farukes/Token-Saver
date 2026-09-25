from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from token_saver.hooks.manager import (
    HOOK_MARKER_START,
    HookManager,
    is_bypass_active,
)


def test_is_bypass_active(monkeypatch):
    monkeypatch.delenv("RAW", raising=False)
    monkeypatch.delenv("TOKEN_SAVER_BYPASS", raising=False)
    assert not is_bypass_active()

    monkeypatch.setenv("RAW", "1")
    assert is_bypass_active()

    monkeypatch.delenv("RAW", raising=False)
    monkeypatch.setenv("TOKEN_SAVER_BYPASS", "1")
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
    assert "token-saver" in data["mcpServers"]
    expected_python = sys.executable if sys.executable else "python"
    assert data["mcpServers"]["token-saver"]["command"] == expected_python


