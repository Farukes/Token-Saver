"""Token-Saver CLI & MCP Entry Point.

Supports running both as an MCP server for AI coding assistants
and as a standalone CLI tool for developers (run, stats, hook, unhook).
"""

from __future__ import annotations

import argparse
import sys

# Configure stdout and stderr to handle UTF-8 cleanly on Windows/legacy terminals
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


def main() -> None:
    """Main CLI entry point for Token-Saver."""
    parser = argparse.ArgumentParser(
        prog="token-saver",
        description="Token-Saver: Zero-cost token optimization engine for AI coding assistants and developers.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Subcommand: server (default if no args)
    server_parser = subparsers.add_parser("server", help="Start the MCP server (stdio transport)")

    # Subcommand: stats
    stats_parser = subparsers.add_parser("stats", help="Display cumulative token and financial savings dashboard")

    # Subcommand: reset-stats
    reset_parser = subparsers.add_parser("reset-stats", help="Reset cumulative telemetry metrics")

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Execute a shell command with intelligent output filtering")
    run_parser.add_argument("command", nargs=argparse.REMAINDER, help="The command to execute (e.g. pytest, npm test)")

    # Subcommand: hook
    hook_parser = subparsers.add_parser("hook", help="Install non-intrusive transparent shell hooks")
    hook_parser.add_argument(
        "--shell",
        choices=["auto", "powershell", "bash"],
        default="auto",
        help="Target shell environment (default: auto)",
    )

    # Subcommand: unhook
    unhook_parser = subparsers.add_parser("unhook", help="Safely remove all installed shell hooks")

    # Subcommand: on / enable
    on_parser = subparsers.add_parser("on", help="Activate Token-Saver globally for AGY CLI")

    # Subcommand: off / disable
    off_parser = subparsers.add_parser("off", help="Deactivate Token-Saver globally from AGY CLI")

    # Subcommand: setup-commands
    setup_parser = subparsers.add_parser(
        "setup-commands",
        help="Install /token-saver slash command definitions across AGY CLI and Claude Code",
    )

    # If called with no arguments, default to launching the MCP server
    if len(sys.argv) == 1:
        from token_saver.server import mcp
        mcp.run(transport="stdio")
        return

    args = parser.parse_args()

    if args.subcommand in (None, "server"):
        from token_saver.server import mcp
        mcp.run(transport="stdio")

    elif args.subcommand == "stats":
        from token_saver.telemetry.stats import tracker
        print(tracker.render_dashboard())

    elif args.subcommand == "reset-stats":
        from token_saver.telemetry.stats import tracker
        tracker.reset()
        print("Telemetry metrics have been successfully reset.")

    elif args.subcommand == "run":
        if not args.command:
            print("Error: No command provided to run. Example: token-saver run pytest")
            sys.exit(1)
        from token_saver.hooks.manager import execute_filtered_command
        exit_code = execute_filtered_command(args.command)
        sys.exit(exit_code)

    elif args.subcommand == "hook":
        from token_saver.hooks.manager import HookManager
        success, msg = HookManager.install_shell_hook(target_shell=args.shell)
        print(msg)
        if not success:
            sys.exit(1)

    elif args.subcommand == "unhook":
        from token_saver.hooks.manager import HookManager
        success, msg = HookManager.uninstall_shell_hook()
        print(msg)
        if not success:
            sys.exit(1)

    elif args.subcommand in ("on", "enable"):
        from token_saver.hooks.manager import HookManager
        success, msg = HookManager.enable_agy()
        print(msg)
        if not success:
            sys.exit(1)

    elif args.subcommand in ("off", "disable"):
        from token_saver.hooks.manager import HookManager
        success, msg = HookManager.disable_agy()
        print(msg)
        if not success:
            sys.exit(1)

    elif args.subcommand in ("setup-commands", "install-commands"):
        from token_saver.hooks.manager import HookManager
        results = HookManager.install_all_slash_commands()
        all_ok = True
        for name, ok, msg in results:
            status = "✅" if ok else "❌"
            print(f"{status} {name}: {msg}")
            if not ok:
                all_ok = False
        if not all_ok:
            sys.exit(1)



if __name__ == "__main__":
    main()
