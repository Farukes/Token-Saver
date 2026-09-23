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

    @classmethod
    def get_agy_config_path(cls) -> Path:
        """Return the path to AGY CLI global mcp_config.json."""
        home = Path.home()
        return home / ".gemini" / "config" / "mcp_config.json"

    @classmethod
    def enable_agy(cls) -> tuple[bool, str]:
        """Activate Token-Saver in AGY CLI global configuration."""
        import json
        config_path = cls.get_agy_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

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
            return True, f"Token-Saver successfully activated for AGY CLI! ({config_path})"
        except Exception as e:
            return False, f"Failed to update AGY config: {e}"

    @classmethod
    def disable_agy(cls) -> tuple[bool, str]:
        """Deactivate Token-Saver from AGY CLI global configuration."""
        import json
        config_path = cls.get_agy_config_path()
        if not config_path.exists():
            return True, "AGY config does not exist, nothing to disable."

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}

        if "mcpServers" in config and "token-saver" in config["mcpServers"]:
            del config["mcpServers"]["token-saver"]
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                return True, f"Token-Saver successfully deactivated from AGY CLI! ({config_path})"
            except Exception as e:
                return False, f"Failed to write AGY config: {e}"

        return True, "Token-Saver was already inactive in AGY config."

