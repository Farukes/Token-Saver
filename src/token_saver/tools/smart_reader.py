from __future__ import annotations

from token_saver.cache.session_cache import CacheStatus, SessionCache
from token_saver.config import load_config
from token_saver.utils.file_utils import read_file_text
from token_saver.utils.token_counter import format_savings

_cache = SessionCache()
_config = load_config()

def read_file_smart(
    file_path: str,
    force_full: bool = False,
    query: str | None = None,
) -> str:
    """Intelligently read a file with session-level caching and lockfile protection.

    Use this tool instead of native file reading for iterative editing workflows.
    It returns the full file content on the first read. On subsequent reads, if the
    file is unchanged, it returns a very short cached message. If changed, it returns
    a unified diff of the modifications, saving thousands of tokens.

    Auto-generated lockfiles (package-lock.json, Cargo.lock, poetry.lock, yarn.lock, etc.)
    and minified assets are automatically shielded to protect context windows from compaction.

    Args:
        file_path: Absolute or relative path to the file.
        force_full: If True, bypasses cache and lockfile shielding, returning raw full content.
        query: Optional package name or keyword to surgically query inside lockfiles or large assets.

    Returns:
        The full content, a short cached message, a unified diff, or a shielded summary.
    """
    if not force_full and _config.is_ignored(file_path):
        import os
        base_name = os.path.basename(file_path)
        return (
            f"[TOKEN-SAVER SECURITY] '{base_name}' matches security ignore patterns "
            f"(credentials/secrets/exclusions). Pass force_full=True if you explicitly "
            f"need to read this file."
        )

    try:
        content = read_file_text(file_path)
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

    if force_full:
        return content

    # Lockfile & giant asset protection
    if _config.is_lockfile(file_path):
        from token_saver.filters.lockfile import process_lockfile

        return process_lockfile(file_path, content, query=query)

    result = _cache.get(file_path, content)

    if result.status == CacheStatus.FIRST_READ:
        return result.content

    savings = format_savings(content, result.content)
    try:
        from token_saver.telemetry.stats import tracker
        tracker.record_savings("cache", result.original_tokens, result.optimized_tokens)
    except Exception:
        pass
    return f"{result.content}\n\nToken savings: {savings}"


def cache_stats() -> str:
    """Get a summary of the smart reader cache performance.

    Returns:
        A string detailing cache hits, misses, diffs, and overall reads.
    """
    return _cache.get_stats().summary()


def register_smart_reader_tools(mcp) -> None:
    """Register smart reader tools with the MCP server."""

    @mcp.tool()
    def read_file_smart(
        file_path: str,
        force_full: bool = False,
        query: str | None = None,
    ) -> str:
        """Intelligently read a file with session-level caching and lockfile protection."""
        return _cache_read_impl(file_path, force_full=force_full, query=query)

    @mcp.tool()
    def cache_stats() -> str:
        """Get a summary of the smart reader cache performance."""
        return _cache_stats_impl()


_cache_read_impl = read_file_smart
_cache_stats_impl = cache_stats


