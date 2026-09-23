"""Persistent SQLite storage for Token-Saver file cache.

Enables cache persistence across MCP server restarts and independent CLI sessions.
Uses SQLite with WAL mode for fast, safe concurrent reads and writes.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

MAX_CACHEABLE_BYTES = 5 * 1024 * 1024  # 5 MB


class PersistentCache:
    """SQLite-backed persistent store for file hash and content cache."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            cache_dir = Path.home() / ".token-saver"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self._db_path = cache_dir / "cache.db"
        else:
            self._db_path = Path(db_path)
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Create cache table and indexes if they do not exist."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS file_cache (
                        path TEXT PRIMARY KEY,
                        hash TEXT NOT NULL,
                        content TEXT NOT NULL,
                        read_count INTEGER DEFAULT 1,
                        updated_at REAL NOT NULL
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_cache_updated ON file_cache(updated_at);"
                )
        except Exception:
            pass

    def get_entry(self, path: str) -> tuple[str, str, int] | None:
        """Fetch cached entry (hash, content, read_count) for a given path."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT hash, content, read_count FROM file_cache WHERE path = ?",
                    (path,),
                )
                row = cursor.fetchone()
                if row:
                    return str(row[0]), str(row[1]), int(row[2])
                return None
        except Exception:
            return None

    def set_entry(self, path: str, hash_val: str, content: str, read_count: int = 1) -> None:
        """Store or update a cached file entry. Protects SQLite from giant files > 5MB."""
        try:
            stored_content = content
            if len(content) > MAX_CACHEABLE_BYTES:
                stored_content = f"__TOKEN_SAVER_LARGE_FILE__:{len(content)}"

            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO file_cache (path, hash, content, read_count, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        hash = excluded.hash,
                        content = excluded.content,
                        read_count = excluded.read_count,
                        updated_at = excluded.updated_at
                    """,
                    (path, hash_val, stored_content, read_count, time.time()),
                )
        except Exception:
            pass

    def invalidate(self, path: str) -> None:
        """Remove an entry from the persistent cache."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM file_cache WHERE path = ?", (path,))
        except Exception:
            pass

    def clear(self) -> None:
        """Clear all entries in the persistent cache."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM file_cache")
        except Exception:
            pass

    def prune(self, max_entries: int = 5000, max_age_days: int = 7) -> int:
        """Prune old entries to prevent unbounded disk usage."""
        try:
            cutoff = time.time() - (max_age_days * 86400)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM file_cache WHERE updated_at < ?", (cutoff,))
                deleted = cursor.rowcount

                cursor.execute("SELECT COUNT(*) FROM file_cache")
                count = cursor.fetchone()[0]
                if count > max_entries:
                    excess = count - max_entries
                    cursor.execute(
                        """
                        DELETE FROM file_cache WHERE path IN (
                            SELECT path FROM file_cache ORDER BY updated_at ASC LIMIT ?
                        )
                        """,
                        (excess,),
                    )
                    deleted += cursor.rowcount
                return deleted
        except Exception:
            return 0

    def count_entries(self) -> int:
        """Return total number of cached entries."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM file_cache")
                row = cursor.fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0
