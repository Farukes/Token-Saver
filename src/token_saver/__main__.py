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
    subparsers.add_parser("server", help="Start the MCP server (stdio transport)")

    # Subcommand: stats
    subparsers.add_parser("stats", help="Display cumulative token and financial savings dashboard")

    # Subcommand: reset-stats
    subparsers.add_parser("reset-stats", help="Reset cumulative telemetry metrics")

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
    subparsers.add_parser("unhook", help="Safely remove all installed shell hooks")

    # Subcommand: on / enable
    subparsers.add_parser("on", help="Activate Token-Saver globally for AGY CLI")

    # Subcommand: off / disable
    subparsers.add_parser("off", help="Deactivate Token-Saver globally from AGY CLI")

    # Subcommand: setup-commands
    subparsers.add_parser(
        "setup-commands",
        help="Install /token-saver slash command definitions across AGY CLI and Claude Code",
    )

    # Subcommand: output (toggle compact output on/off/status)
    output_parser = subparsers.add_parser(
        "output",
        help="Manage AI output mode: 'token-saver output on' or 'token-saver output off'",
    )
    output_parser.add_argument(
        "state",
        nargs="?",
        choices=["on", "off", "status"],
        default="status",
        help="Output mode action: 'on' (compact surgical diffs), 'off' (default output), or 'status'",
    )
    output_parser.add_argument(
        "--path",
        default=".",
        help="Target project directory (default: current directory)",
    )

    # Subcommand: init-rules
    rules_parser = subparsers.add_parser(
        "init-rules",
        help="Install agent steering rules into AGENTS.md, .cursorrules, .windsurfrules, and CLAUDE.md",
    )
    rules_parser.add_argument(
        "--path",
        default=".",
        help="Target project directory (default: current directory)",
    )
    rules_parser.add_argument(
        "--compact",
        dest="compact_output",
        action="store_true",
        default=None,
        help="Enforce compact surgical output rules",
    )
    rules_parser.add_argument(
        "--no-compact",
        dest="compact_output",
        action="store_false",
        help="Disable compact output restrictions in agent rules",
    )

    # Subcommand: cache-prune
    prune_parser = subparsers.add_parser(
        "cache-prune",
        help="Prune expired or excess entries from L2 SQLite cache",
    )
    prune_parser.add_argument(
        "--max-entries",
        type=int,
        default=5000,
        help="Maximum cache entries to retain (default: 5000)",
    )
    prune_parser.add_argument(
        "--ttl-days",
        type=int,
        default=30,
        help="Evict entries older than N days (default: 30)",
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
        from token_saver.rules.manager import RulesManager
        results = HookManager.enable_all()
        for name, ok, msg in results:
            if "skipped" in msg.lower():
                status = "⚪"
            else:
                status = "🟢" if ok else "❌"
            print(f"{status} {name}: {msg}")
        rule_results = RulesManager.install_rules(".")
        for name, ok, msg in rule_results:
            print(f"🟢 Rules: {msg}")

    elif args.subcommand in ("off", "disable"):
        from token_saver.hooks.manager import HookManager
        from token_saver.rules.manager import RulesManager
        results = HookManager.disable_all()
        for name, ok, msg in results:
            if "skipped" in msg.lower():
                status = "⚪"
            else:
                status = "🔴" if ok else "❌"
            print(f"{status} {name}: {msg}")
        rule_results = RulesManager.remove_rules(".")
        for name, ok, msg in rule_results:
            print(f"🔴 Rules: {msg}")

    elif args.subcommand in ("setup-commands", "install-commands"):
        from token_saver.hooks.manager import HookManager
        results = HookManager.install_all_slash_commands(only_installed=True)
        all_ok = True
        for name, ok, msg in results:
            if "skipped" in msg.lower():
                status = "⚪"
            else:
                status = "✅" if ok else "❌"
                if not ok:
                    all_ok = False
            print(f"{status} {name}: {msg}")
        if not all_ok:
            sys.exit(1)

    elif args.subcommand == "init-rules":
        from token_saver.rules.manager import RulesManager
        results = RulesManager.install_rules(args.path, compact_output=args.compact_output)
        all_ok = True
        for name, ok, msg in results:
            status = "✅" if ok else "❌"
            print(f"{status} {name}: {msg}")
            if not ok:
                all_ok = False
        if not all_ok:
            sys.exit(1)

    elif args.subcommand == "output":
        from token_saver.rules.manager import RulesManager
        if args.state == "on":
            ok, msg, files = RulesManager.set_output_mode(args.path, enabled=True)
            if ok:
                print("🟢 Output Optimization: ON (Compact Mode Active)")
                print("   • Enforces surgical diffs and targeted block replacements.")
                print("   • ZERO TRUNCATION MANDATE active (no lazy comments).")
                print(f"   • Updated files: {', '.join(files)}")
            else:
                print(f"❌ Error: {msg}")
                sys.exit(1)
        elif args.state == "off":
            ok, msg, files = RulesManager.set_output_mode(args.path, enabled=False)
            if ok:
                print("⚪ Output Optimization: OFF (Default Output Restored)")
                print("   • AI assistant will use standard, unrestricted output.")
                print("   • Output format returned to default.")
                print(f"   • Updated files: {', '.join(files)}")
            else:
                print(f"❌ Error: {msg}")
                sys.exit(1)
        else:
            active = RulesManager.get_output_mode(args.path)
            state_str = "🟢 ON (Compact Mode Active)" if active else "⚪ OFF (Default Output)"
            print(f"Output Optimization Status: {state_str}")
            print("\nUsage:")
            print("  token-saver output on   -> Activate compact surgical diffs & zero-truncation")
            print("  token-saver output off  -> Revert to default normal/verbose output")

    elif args.subcommand == "cache-prune":
        from token_saver.cache.persistent_cache import PersistentCache
        p = PersistentCache()
        before = p.count_entries()
        deleted = p.prune(max_entries=args.max_entries, max_age_days=args.ttl_days)
        after = p.count_entries()
        print(f"L2 Cache Pruned: {deleted} entries removed. ({before} -> {after} entries remaining)")



if __name__ == "__main__":
    main()
