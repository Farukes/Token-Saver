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

    # Subcommand: status
    status_parser = subparsers.add_parser(
        "status",
        help="Check comprehensive live operational status of Token-Saver across all AI CLIs and project rules",
    )
    status_parser.add_argument(
        "--path",
        default=".",
        help="Target project directory to check rules for (default: current directory)",
    )

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
    subparsers.add_parser("on", help="Activate Token-Saver globally for AGY CLI and detected IDEs")

    # Subcommand: off / disable
    subparsers.add_parser("off", help="Deactivate Token-Saver globally and revert all settings")

    # Subcommand: install-mcp
    install_mcp_parser = subparsers.add_parser(
        "install-mcp",
        help="Configure Token-Saver MCP server in Claude Desktop, Cursor, Windsurf, VS Code with safe backup",
    )
    install_mcp_parser.add_argument(
        "--all",
        action="store_true",
        help="Configure for all supported IDEs even if not currently detected on system",
    )

    # Subcommand: uninstall-mcp
    subparsers.add_parser(
        "uninstall-mcp",
        help="Safely remove Token-Saver MCP configuration and restore exact original state from backup",
    )

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
    rules_parser.add_argument(
        "--all",
        action="store_true",
        help="Generate rule files for all AI coding assistants (default: auto-detect installed assistants)",
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

    elif args.subcommand == "status":
        import json
        from pathlib import Path

        from token_saver.cache.persistent_cache import PersistentCache
        from token_saver.hooks.manager import HookManager
        from token_saver.rules.manager import RULES_MARKER_START, RulesManager

        project_path = Path(args.path).resolve()
        configs = HookManager.get_supported_cli_configs()

        print("=" * 60)
        print("🔋 TOKEN-SAVER SYSTEM STATUS REPORT")
        print("=" * 60)

        # 1. Check CLI MCP Integrations
        active_clis = []
        inactive_clis = []
        for name, cfg_path in configs.items():
            is_inst = HookManager.is_cli_installed(name)
            is_active = False
            if cfg_path.exists():
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "token-saver" in data.get("mcpServers", {}):
                            is_active = True
                except Exception:
                    pass
            if is_active:
                active_clis.append(f"🟢 {name} (Active in {cfg_path.name})")
            elif is_inst:
                inactive_clis.append(f"🔴 {name} (Installed, but Token-Saver disabled)")
            else:
                inactive_clis.append(f"⚪ {name} (Not installed)")

        overall_active = len(active_clis) > 0
        overall_badge = "🟢 ACTIVE (Operational)" if overall_active else "🔴 INACTIVE (Turn on with 'token-saver on')"
        print(f"Overall Engine Status : {overall_badge}\n")

        print("AI Assistant Integrations:")
        for line in active_clis + inactive_clis:
            print(f"  • {line}")

        # 2. Check Output Optimization Status
        output_active = RulesManager.get_output_mode(project_path)
        out_badge = "🟢 ON (Compact surgical diffs & zero-truncation)" if output_active else "⚪ OFF (Default full output)"
        print(f"\nOutput Optimization   : {out_badge}")

        # 3. Check Project Steering Rules
        rule_files_found = []
        for r_name in RulesManager.SUPPORTED_RULE_FILES:
            r_path = project_path / r_name
            if r_path.exists():
                try:
                    content = r_path.read_text(encoding="utf-8")
                    if RULES_MARKER_START in content:
                        rule_files_found.append(r_name)
                except Exception:
                    pass
        if rule_files_found:
            print(f"Project Steering Rules: 🟢 INSTALLED ({', '.join(rule_files_found)})")
        else:
            print("Project Steering Rules: 🔴 NOT INSTALLED (Run 'token-saver init-rules')")

        # 4. Check L2 Persistent Cache
        try:
            cache = PersistentCache()
            entries = cache.count_entries()
            print(f"L2 Persistent Cache   : 🟢 ONLINE ({entries} cached entries in ~/.token-saver/cache.db)")
        except Exception as e:
            print(f"L2 Persistent Cache   : ⚠️ Error accessing DB: {e}")

        print("=" * 60)
        print("Useful Commands:")
        print("  token-saver on         -> Enable Token-Saver globally")
        print("  token-saver off        -> Disable Token-Saver globally")
        print("  token-saver output on  -> Enable compact surgical output")
        print("  token-saver output off -> Revert to standard verbose output")
        print("  token-saver stats      -> View live token and financial savings")
        print("=" * 60)
        if not overall_active:
            sys.exit(1)

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

    elif args.subcommand in ("install-mcp", "enable-mcp"):
        from token_saver.hooks.manager import HookManager
        results = HookManager.enable_all(only_installed=not getattr(args, "all", False))
        for name, ok, msg in results:
            if "skipped" in msg.lower():
                status = "⚪"
            else:
                status = "🟢" if ok else "❌"
            print(f"{status} {name}: {msg}")

    elif args.subcommand in ("uninstall-mcp", "disable-mcp"):
        from token_saver.hooks.manager import HookManager
        results = HookManager.disable_all()
        for name, ok, msg in results:
            if "skipped" in msg.lower():
                status = "⚪"
            else:
                status = "🔴" if ok else "❌"
            print(f"{status} {name}: {msg}")

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
        results = RulesManager.install_rules(
            args.path,
            compact_output=args.compact_output,
            only_installed=not args.all,
        )
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
