from __future__ import annotations

from token_saver.cache.session_cache import SessionCache, CacheStatus
from token_saver.utils.file_utils import read_file_text
from token_saver.utils.token_counter import format_savings

_cache = SessionCache()

def read_file_smart(file_path: str, force_full: bool = False) -> str:
    """Intelligently read a file with session-level caching.

    Use this tool instead of native file reading for iterative editing workflows.
    It returns the full file content on the first read. On subsequent reads, if the
    file is unchanged, it returns a very short cached message. If changed, it returns
    a unified diff of the modifications, saving thousands of tokens.

    Args:
        file_path: Absolute or relative path to the file.
        force_full: If True, bypasses the cache and returns the full content.

    Returns:
        The full content, a short cached message, or a unified diff.
    """
    try:
        content = read_file_text(file_path)
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

    if force_full:
        return content

    result = _cache.get(file_path, content)
    
    if result.status == CacheStatus.FIRST_READ:
        return result.content
        
    savings = format_savings(content, result.content)
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
    def read_file_smart(file_path: str, force_full: bool = False) -> str:
        """Intelligently read a file with session-level caching."""
        return _cache_read_impl(file_path, force_full=force_full)

    @mcp.tool()
    def cache_stats() -> str:
        """Get a summary of the smart reader cache performance."""
        return _cache_stats_impl()


_cache_read_impl = read_file_smart
_cache_stats_impl = cache_stats


