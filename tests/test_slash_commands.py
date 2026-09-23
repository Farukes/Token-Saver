from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from token_saver.hooks.manager import HookManager


def test_install_agy_slash_command(tmp_path: Path):
    fake_home = tmp_path / "user_home"

    with patch("pathlib.Path.home", return_value=fake_home):
        ok, msg = HookManager.install_agy_slash_command()
        assert ok
        assert "Installed /token-saver command for AGY CLI" in msg

        skill_file = fake_home / ".gemini" / "config" / "skills" / "token-saver" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text(encoding="utf-8")
        assert "name: token-saver" in content
        assert "/token-saver on" in content
        assert "/token-saver off" in content
        assert "/token-saver stats" in content


def test_install_claude_code_slash_command(tmp_path: Path):
    fake_home = tmp_path / "user_home"

    with patch("pathlib.Path.home", return_value=fake_home):
        ok, msg = HookManager.install_claude_code_slash_command()
        assert ok
        assert "Installed /token-saver command for Claude Code" in msg

        cmd_file = fake_home / ".claude" / "commands" / "token-saver.md"
        assert cmd_file.exists()

        content = cmd_file.read_text(encoding="utf-8")
        assert "token-saver on" in content
        assert "token-saver off" in content
        assert "$ARGUMENTS" in content


def test_install_all_slash_commands(tmp_path: Path):
    fake_home = tmp_path / "user_home"

    with patch("pathlib.Path.home", return_value=fake_home):
        results = HookManager.install_all_slash_commands()
        assert len(results) == 2
        for name, ok, msg in results:
            assert ok
