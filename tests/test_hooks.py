from __future__ import annotations

import os
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
