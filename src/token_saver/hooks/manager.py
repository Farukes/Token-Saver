"""Transparent hooking manager for Token-Saver.

Provides non-intrusive, transparent interception for terminal commands
across PowerShell, Bash, Zsh, and Claude Code environments.

Allows safe installation (hook) and clean, 100% reversible uninstallation (unhook).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HOOK_MARKER_START = "# >>> token-saver-hook >>>"
HOOK_MARKER_END = "# <<< token-saver-hook <<<"

# Commands that benefit most from output filtering
DEFAULT_WRAPPED_COMMANDS = ["pytest", "jest", "vitest", "npm", "cargo"]


def is_bypass_active() -> bool:
    """Check if transparent filtering should be bypassed."""
    return (
        os.environ.get("RAW") == "1"
        or os.environ.get("TOKEN_SAVER_BYPASS") == "1"
        or "--raw" in sys.argv
    )


def execute_filtered_command(command: str | list[str], cwd: str = ".") -> int:
    """Execute a command and print filtered output to stdout.

    Respects RAW=1 or --raw bypass to return raw output without modification.
    """
    if isinstance(command, list):
        cmd_str = " ".join(command)
    else:
        cmd_str = command

    # Check for --raw flag and strip it
    if "--raw" in cmd_str:
        cmd_str = cmd_str.replace("--raw", "").strip()
        bypass = True
    else:
        bypass = is_bypass_active()

    try:
        res = subprocess.run(
            cmd_str,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
        )
        combined_output = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
        exit_code = res.returncode

        if bypass:
            sys.stdout.write(combined_output)
            sys.stdout.flush()
            return exit_code

        from token_saver.tools.output_pruner import filter_output_logic

        filtered = filter_output_logic(combined_output, output_type="auto", exit_code=exit_code)
        sys.stdout.write(filtered + "\n")
        sys.stdout.flush()
        return exit_code
    except Exception as e:
        sys.stderr.write(f"[token-saver] Error executing '{cmd_str}': {e}\n")
        return 1


class HookManager:
    """Manages transparent shell and assistant hooks."""

    @staticmethod
    def get_powershell_profile_path() -> Path | None:
        """Find the PowerShell profile path on Windows or cross-platform."""
        home = Path.home()
        # Windows PowerShell standard profile location
        if os.name == "nt":
            docs = home / "Documents" / "WindowsPowerShell"
            if not docs.exists():
                docs = home / "OneDrive" / "Documents" / "WindowsPowerShell"
            profile = docs / "Microsoft.PowerShell_profile.ps1"
            return profile
        else:
            profile = home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1"
            return profile

    @staticmethod
    def get_bash_profile_path() -> Path:
        """Find bashrc or zshrc path."""
        home = Path.home()
        zshrc = home / ".zshrc"
        if zshrc.exists():
            return zshrc
        return home / ".bashrc"

    @classmethod
    def install_shell_hook(cls, target_shell: str = "auto") -> tuple[bool, str]:
        """Install transparent shell wrappers into user's profile."""
        if target_shell == "auto":
            is_win = os.name == "nt"
            target_shell = "powershell" if is_win else "bash"

        if target_shell == "powershell":
            profile_path = cls.get_powershell_profile_path()
            if not profile_path:
                return False, "Could not determine PowerShell profile directory."

            hook_code = f"""
{HOOK_MARKER_START}
# Token-Saver transparent output filters
function pytest {{ token-saver run "pytest $args" }}
function npm {{ if ($args[0] -eq "test") {{ token-saver run "npm $args" }} else {{ & (Get-Command -CommandType Application npm) @args }} }}
{HOOK_MARKER_END}
"""
        else:
            profile_path = cls.get_bash_profile_path()
            hook_code = f"""
{HOOK_MARKER_START}
# Token-Saver transparent output filters
pytest() {{ token-saver run "pytest $@" ; }}
npm() {{ if [ "$1" = "test" ]; then token-saver run "npm $@"; else command npm "$@"; fi ; }}
{HOOK_MARKER_END}
"""

        try:
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            current_content = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""

            if HOOK_MARKER_START in current_content:
                return True, f"Hook is already installed in {profile_path}"

            updated_content = current_content + "\n" + hook_code.strip() + "\n"
            profile_path.write_text(updated_content, encoding="utf-8")
            return True, f"Successfully installed transparent hook into {profile_path}"
        except Exception as e:
            return False, f"Failed to install shell hook: {e}"

    @classmethod
    def uninstall_shell_hook(cls) -> tuple[bool, str]:
        """Safely remove the transparent hook from all detected shell profiles."""
        removed_from = []

        # Check PowerShell
        ps_path = cls.get_powershell_profile_path()
        if ps_path and ps_path.exists():
            try:
                content = ps_path.read_text(encoding="utf-8")
                if HOOK_MARKER_START in content:
                    pattern = rf"{re.escape(HOOK_MARKER_START)}.*?{re.escape(HOOK_MARKER_END)}\s*"
                    clean = re.sub(pattern, "", content, flags=re.DOTALL)
                    ps_path.write_text(clean, encoding="utf-8")
                    removed_from.append(str(ps_path))
            except Exception:
                pass

        # Check Bash/Zsh
        bash_path = cls.get_bash_profile_path()
        if bash_path and bash_path.exists():
            try:
                content = bash_path.read_text(encoding="utf-8")
                if HOOK_MARKER_START in content:
                    pattern = rf"{re.escape(HOOK_MARKER_START)}.*?{re.escape(HOOK_MARKER_END)}\s*"
                    clean = re.sub(pattern, "", content, flags=re.DOTALL)
                    bash_path.write_text(clean, encoding="utf-8")
                    removed_from.append(str(bash_path))
            except Exception:
                pass

        if removed_from:
            return True, f"Successfully removed hooks from: {', '.join(removed_from)}"
        return True, "No active hooks were found to remove."

    @staticmethod
    def _apply_mcp_config_with_backup(config_path: Path) -> tuple[bool, str]:
        """Apply Token-Saver MCP configuration while safely creating a backup of original state."""
        import json
        config_path.parent.mkdir(parents=True, exist_ok=True)
        bak_path = config_path.with_name(config_path.name + ".ts_bak")

        # Save a backup of the original file if not already backed up
        if config_path.exists() and not bak_path.exists():
            try:
                content = config_path.read_text(encoding="utf-8")
                bak_path.write_text(content, encoding="utf-8")
            except Exception:
                pass
        elif not config_path.exists() and not bak_path.exists():
            # Mark that the file did not exist originally
            try:
                bak_path.write_text("__NON_EXISTENT__", encoding="utf-8")
            except Exception:
                pass

        config: dict = {}
        if config_path.exists() and config_path.stat().st_size > 0:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                config = {}

        if "mcpServers" not in config:
            config["mcpServers"] = {}

        config["mcpServers"]["token-saver"] = {
            "command": "python",
            "args": ["-m", "token_saver"],
            "env": {
                "PYTHONUNBUFFERED": "1"
            }
        }

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return True, f"Activated in {config_path}"
        except Exception as e:
            return False, f"Failed writing {config_path}: {e}"

    @staticmethod
    def _revert_mcp_config_with_backup(config_path: Path) -> tuple[bool, str]:
        """Revert MCP configuration back to its exact pre-activation state using backup."""
        import json
        bak_path = config_path.with_name(config_path.name + ".ts_bak")

        # Case 1: If backup exists, restore it completely
        if bak_path.exists():
            try:
                bak_content = bak_path.read_text(encoding="utf-8")
                if bak_content == "__NON_EXISTENT__":
                    if config_path.exists():
                        config_path.unlink()
                else:
                    config_path.write_text(bak_content, encoding="utf-8")
                bak_path.unlink(missing_ok=True)

                # Clean up empty parent directories if created by token-saver
                parent = config_path.parent
                try:
                    if parent.exists() and not any(parent.iterdir()):
                        parent.rmdir()
                        grandparent = parent.parent
                        if grandparent.exists() and not any(grandparent.iterdir()):
                            grandparent.rmdir()
                except Exception:
                    pass

                return True, f"Restored original config for {config_path.name}"
            except Exception as e:
                return False, f"Failed restoring backup for {config_path}: {e}"

        # Case 2: No backup file, just cleanly remove token-saver entry
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                if "mcpServers" in config and "token-saver" in config["mcpServers"]:
                    del config["mcpServers"]["token-saver"]
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2)
                    return True, f"Deactivated token-saver from {config_path.name}"
            except Exception as e:
                return False, f"Failed modifying {config_path}: {e}"

        return True, f"Token-Saver was already inactive in {config_path.name}"

    @classmethod
    def is_cli_installed(cls, name: str) -> bool:
        """Check if a specific AI coding CLI or assistant is installed on the host system."""
        import shutil
        home = Path.home()

        if name == "Antigravity (AGY)":
            return bool(
                shutil.which("agy")
                or shutil.which("antigravity")
                or (home / ".gemini").is_dir()
            )

        if name == "Claude Code":
            if shutil.which("claude") or shutil.which("claude.cmd"):
                return True
            claude_dir = home / ".claude"
            if claude_dir.is_dir():
                files = [p.name for p in claude_dir.iterdir() if p.name != "commands"]
                if files:
                    return True
            claude_cfg = home / ".claude.json"
            claude_bak = home / ".claude.json.ts_bak"
            if claude_cfg.exists():
                if claude_bak.exists():
                    try:
                        if claude_bak.read_text(encoding="utf-8").strip() == "__NON_EXISTENT__":
                            return False
                    except Exception:
                        pass
                return True
            return False

        if name == "Cursor":
            if shutil.which("cursor") or shutil.which("cursor.cmd"):
                return True
            if os.name == "nt":
                if (home / "AppData" / "Roaming" / "Cursor").is_dir() or (home / "AppData" / "Local" / "Programs" / "cursor").is_dir():
                    return True
            elif sys.platform == "darwin":
                if Path("/Applications/Cursor.app").is_dir() or (home / "Library" / "Application Support" / "Cursor").is_dir():
                    return True
            else:
                if (home / ".config" / "Cursor").is_dir():
                    return True
            cursor_cfg = home / ".cursor" / "mcp.json"
            cursor_bak = home / ".cursor" / "mcp.json.ts_bak"
            if cursor_cfg.exists():
                if cursor_bak.exists():
                    try:
                        if cursor_bak.read_text(encoding="utf-8").strip() == "__NON_EXISTENT__":
                            return False
                    except Exception:
                        pass
                return True
            return False

        if name == "Windsurf":
            if shutil.which("windsurf") or shutil.which("windsurf.cmd"):
                return True
            if os.name == "nt":
                if (home / "AppData" / "Roaming" / "Windsurf").is_dir() or (home / "AppData" / "Local" / "Programs" / "Windsurf").is_dir() or (home / "AppData" / "Roaming" / "Codeium").is_dir():
                    return True
            elif sys.platform == "darwin":
                if Path("/Applications/Windsurf.app").is_dir() or (home / "Library" / "Application Support" / "Windsurf").is_dir():
                    return True
            else:
                if (home / ".config" / "Windsurf").is_dir():
                    return True
            windsurf_cfg = home / ".codeium" / "windsurf" / "mcp_config.json"
            windsurf_bak = home / ".codeium" / "windsurf" / "mcp_config.json.ts_bak"
            if windsurf_cfg.exists():
                if windsurf_bak.exists():
                    try:
                        if windsurf_bak.read_text(encoding="utf-8").strip() == "__NON_EXISTENT__":
                            return False
                    except Exception:
                        pass
                return True
            return False

        return False

    @classmethod
    def get_supported_cli_configs(cls) -> dict[str, Path]:
        """Return paths to all supported AI coding assistant configuration files."""
        home = Path.home()
        return {
            "Antigravity (AGY)": home / ".gemini" / "config" / "mcp_config.json",
            "Claude Code": home / ".claude.json",
            "Cursor": home / ".cursor" / "mcp.json",
            "Windsurf": home / ".codeium" / "windsurf" / "mcp_config.json",
        }

    @classmethod
    def enable_all(cls, only_installed: bool = True) -> list[tuple[str, bool, str]]:
        """Universally activate Token-Saver across detected AI coding CLIs with backups."""
        results = []
        configs = cls.get_supported_cli_configs()

        for name, path in configs.items():
            if only_installed and not cls.is_cli_installed(name):
                results.append((name, False, "Not installed (skipped — no config created)"))
                continue
            ok, msg = cls._apply_mcp_config_with_backup(path)
            results.append((name, ok, msg))

        # Also install slash commands
        cls.install_all_slash_commands(only_installed=only_installed)
        return results

    @classmethod
    def disable_all(cls) -> list[tuple[str, bool, str]]:
        """Universally revert all AI coding CLIs back to their exact pre-activation settings."""
        results = []
        configs = cls.get_supported_cli_configs()

        for name, path in configs.items():
            bak_path = path.with_name(path.name + ".ts_bak")
            if not path.exists() and not bak_path.exists():
                continue
            ok, msg = cls._revert_mcp_config_with_backup(path)
            results.append((name, ok, msg))

        # Also clean up uninstalled Claude slash command if present
        home = Path.home()
        claude_cmd = home / ".claude" / "commands" / "token-saver.md"
        if claude_cmd.exists() and not cls.is_cli_installed("Claude Code"):
            try:
                claude_cmd.unlink()
                cmd_dir = claude_cmd.parent
                if cmd_dir.exists() and not any(cmd_dir.iterdir()):
                    cmd_dir.rmdir()
                claude_dir = home / ".claude"
                if claude_dir.exists() and not any(claude_dir.iterdir()):
                    claude_dir.rmdir()
            except Exception:
                pass

        return results

    @classmethod
    def get_agy_config_path(cls) -> Path:
        """Return the path to AGY CLI global mcp_config.json."""
        return cls.get_supported_cli_configs()["Antigravity (AGY)"]

    @classmethod
    def enable_agy(cls) -> tuple[bool, str]:
        """Activate Token-Saver in AGY CLI global configuration."""
        return cls._apply_mcp_config_with_backup(cls.get_agy_config_path())

    @classmethod
    def disable_agy(cls) -> tuple[bool, str]:
        """Deactivate Token-Saver from AGY CLI global configuration."""
        return cls._revert_mcp_config_with_backup(cls.get_agy_config_path())


    @classmethod
    def install_agy_slash_command(cls) -> tuple[bool, str]:
        """Install global slash command skill for Antigravity (AGY) CLI."""
        home = Path.home()
        skill_dir = home / ".gemini" / "config" / "skills" / "token-saver"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"

        content = """---
name: token-saver
description: >-
  Instant slash command controller for the Token-Saver token optimization engine.
  Use immediately when user types /token-saver, /token-saver on, /token-saver off,
  /token-saver output on, /token-saver output off, /token-saver stats, or requests to toggle token-saver state.
---

# Token-Saver Slash Command Controller

When this command is invoked with an argument:

1. **If argument is 'on' or 'enable':**
   Execute shell command: `token-saver on`
   Report confirmation that Token-Saver is active.

2. **If argument is 'off' or 'disable':**
   Execute shell command: `token-saver off`
   Report confirmation that Token-Saver is deactivated.

3. **If argument starts with 'output':**
   Execute shell command: `token-saver output <arg>` (e.g. `token-saver output on` or `token-saver output off`)
   Report confirmation of the output mode change.

4. **If argument is 'stats' or 'telemetry':**
   Execute shell command: `token-saver stats`
   Display the savings dashboard.

5. **If no argument or 'help':**
   Show options: `/token-saver on`, `/token-saver off`, `/token-saver output on`, `/token-saver output off`, `/token-saver stats`.
"""
        try:
            skill_file.write_text(content, encoding="utf-8")
            return True, f"Installed /token-saver command for AGY CLI at {skill_file}"
        except Exception as e:
            return False, f"Failed to install AGY slash command: {e}"

    @classmethod
    def install_claude_code_slash_command(cls) -> tuple[bool, str]:
        """Install native slash command definition for Claude Code."""
        home = Path.home()
        claude_dir = home / ".claude" / "commands"
        claude_dir.mkdir(parents=True, exist_ok=True)
        command_file = claude_dir / "token-saver.md"

        content = """---
description: Manage Token-Saver token optimization engine (on, off, output on/off, stats)
---

Execute the requested Token-Saver operation:
$ARGUMENTS

Instructions:
1. If argument is "on" or "enable", run `token-saver on` and confirm activation.
2. If argument is "off" or "disable", run `token-saver off` and confirm deactivation.
3. If argument starts with "output", run `token-saver output <args>` and report status.
4. If argument is "stats", run `token-saver stats` and show the telemetry dashboard.
5. If empty or help, show usage instructions.
"""
        try:
            command_file.write_text(content, encoding="utf-8")
            return True, f"Installed /token-saver command for Claude Code at {command_file}"
        except Exception as e:
            return False, f"Failed to install Claude Code slash command: {e}"

    @classmethod
    def install_all_slash_commands(cls, only_installed: bool = False) -> list[tuple[str, bool, str]]:
        """Install slash command definitions across supported AI coding CLIs."""
        results = []
        if not only_installed or cls.is_cli_installed("Antigravity (AGY)"):
            ok1, msg1 = cls.install_agy_slash_command()
            results.append(("Antigravity (AGY)", ok1, msg1))

        if not only_installed or cls.is_cli_installed("Claude Code"):
            ok2, msg2 = cls.install_claude_code_slash_command()
            results.append(("Claude Code", ok2, msg2))
        else:
            results.append(("Claude Code", False, "Not installed (skipped)"))

        return results


