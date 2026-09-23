"""Session-level file cache for Token-Saver.

Stores SHA-256 hashes and content of previously read files.
Enables differential reads (returning only diffs on re-reads)
and cache-hit detection (returning a compact reference for unchanged files).
"""

from __future__ import annotations

import difflib
import hashlib
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """A cached file entry with content and hash."""

    content: str
    hash: str
    read_count: int = 0


class SessionCache:
    """In-memory session cache for file content.

    Tracks file content by SHA-256 hash. When a file is re-read:
    - If unchanged: returns a compact '[CACHED] unchanged' message (~3 tokens)
    - If changed: returns a unified diff of the changes (~50-200 tokens)

    This replaces sending the full file content again (~thousands of tokens).
    """

    def __init__(self) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._stats = CacheStats()

    def get(self, file_path: str, current_content: str) -> CacheResult:
        """Check cache and return appropriate result.

        Args:
            file_path: Absolute or relative path to the file.
            current_content: The current content of the file.

        Returns:
            CacheResult with status and optimized content.
        """
        current_hash = self._compute_hash(current_content)
        normalized_path = self._normalize_path(file_path)

        if normalized_path not in self._cache:
            # First read — cache it and return full content
            self._cache[normalized_path] = CacheEntry(
                content=current_content,
                hash=current_hash,
                read_count=1,
            )
            self._stats.total_reads += 1
            self._stats.cache_misses += 1
            return CacheResult(
                status=CacheStatus.FIRST_READ,
                content=current_content,
                original_tokens=len(current_content) // 4,
                optimized_tokens=len(current_content) // 4,
            )

        entry = self._cache[normalized_path]
        entry.read_count += 1
        self._stats.total_reads += 1

        if entry.hash == current_hash:
            # Unchanged — return compact reference
            self._stats.cache_hits += 1
            compact = f"[CACHED] {file_path} — unchanged since last read (read #{entry.read_count})"
            return CacheResult(
                status=CacheStatus.UNCHANGED,
                content=compact,
                original_tokens=len(current_content) // 4,
                optimized_tokens=len(compact) // 4,
            )

        # Changed — compute and return diff
        self._stats.cache_diffs += 1
        diff = self._compute_diff(entry.content, current_content, file_path)

        # Update cache with new content
        entry.content = current_content
        entry.hash = current_hash

        return CacheResult(
            status=CacheStatus.CHANGED,
            content=diff,
            original_tokens=len(current_content) // 4,
            optimized_tokens=len(diff) // 4,
        )

    def invalidate(self, file_path: str) -> None:
        """Remove a file from the cache."""
        normalized = self._normalize_path(file_path)
        self._cache.pop(normalized, None)

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        self._stats = CacheStats()

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats

    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_path(file_path: str) -> str:
        """Normalize file path for consistent cache keys."""
        import os

        return os.path.normpath(os.path.abspath(file_path))

    @staticmethod
    def _compute_diff(old_content: str, new_content: str, file_path: str) -> str:
        """Compute a unified diff between old and new content."""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            n=3,  # 3 lines of context
        )

        diff_text = "".join(diff)
        if not diff_text:
            return f"[CACHED] {file_path} — no visible changes"

        return f"[DIFF] Changes in {file_path}:\n{diff_text}"


class CacheStatus:
    """Cache lookup result status."""

    FIRST_READ = "first_read"
    UNCHANGED = "unchanged"
    CHANGED = "changed"


@dataclass
class CacheResult:
    """Result of a cache lookup."""

    status: str
    content: str
    original_tokens: int
    optimized_tokens: int

    @property
    def savings_pct(self) -> float:
        """Calculate percentage of tokens saved."""
        if self.original_tokens == 0:
            return 0.0
        return (1 - self.optimized_tokens / self.original_tokens) * 100


@dataclass
class CacheStats:
    """Cumulative cache statistics."""

    total_reads: int = 0
    cache_hits: int = 0
    cache_diffs: int = 0
    cache_misses: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        if self.total_reads == 0:
            return 0.0
        return (self.cache_hits / self.total_reads) * 100

    def summary(self) -> str:
        """Human-readable summary of cache performance."""
        return (
            f"Cache: {self.total_reads} reads, "
            f"{self.cache_hits} hits ({self.hit_rate:.0f}%), "
            f"{self.cache_diffs} diffs, "
            f"{self.cache_misses} misses"
        )
