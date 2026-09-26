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


def test_cli_update_subcommand(capsys):
    import sys

    from token_saver.__main__ import main

    # Simulate running 'token-saver update' when already up to date
    with patch.object(sys, "argv", ["token-saver", "update"]):
        with patch("urllib.request.urlopen") as mock_url:
            import json
            from unittest.mock import MagicMock

            from token_saver import __version__

            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"info": {"version": __version__}}).encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            main()

            captured = capsys.readouterr()
            assert "TOKEN-SAVER AUTOMATIC UPDATE MANAGER" in captured.out
            assert "already on the latest version" in captured.out
