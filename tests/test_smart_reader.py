from __future__ import annotations

import pytest

from token_saver.tools.smart_reader import _cache, register_smart_reader_tools


class MockMCP:
    def __init__(self) -> None:
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

@pytest.fixture(autouse=True)
def reset_cache():
    _cache.clear()
    yield
    _cache.clear()

def test_smart_reader(tmp_path):
    mcp = MockMCP()
    register_smart_reader_tools(mcp)

    read_file_smart = mcp.tools["read_file_smart"]
    cache_stats = mcp.tools["cache_stats"]

    # Create test file with realistic size (15 lines)
    initial_text = "\n".join([f"line {i} with some content" for i in range(1, 16)]) + "\n"
    test_file = tmp_path / "test.txt"
    test_file.write_text(initial_text, encoding="utf-8")
    file_path = str(test_file)

    # 1. First read returns full content (status: first_read)
    content1 = read_file_smart(file_path)
    assert content1 == initial_text

    # 2. Second read of unchanged file returns cached message (status: unchanged)
    content2 = read_file_smart(file_path)
    assert "[CACHED]" in content2
    assert "unchanged since last read" in content2
    assert "tokens (" in content2

    # 3. Modified file returns diff (status: changed)
    modified_text = initial_text.replace("line 2 with some content", "line 2 modified")
    test_file.write_text(modified_text, encoding="utf-8")
    content3 = read_file_smart(file_path)
    assert "[DIFF]" in content3
    assert "line 2 modified" in content3
    assert "tokens (" in content3

    # 4. force_full bypasses cache
    content4 = read_file_smart(file_path, force_full=True)
    assert content4 == modified_text

    # 5. Cache stats are accurate
    stats = cache_stats()
    assert "3 reads" in stats
    assert "1 hits" in stats
    assert "1 diffs" in stats
    assert "1 misses" in stats

    # 6. Non-existent file returns error message
    bad_path = str(tmp_path / "does_not_exist.txt")
    error_msg = read_file_smart(bad_path)
    assert "Error reading file" in error_msg

    # 7. Tiny file guardrail: if diff is larger than the file, returns full content without inflating tokens
    tiny_file = tmp_path / "tiny.txt"
    tiny_file.write_text("x = 1\n", encoding="utf-8")
    read_file_smart(str(tiny_file))
    tiny_file.write_text("x = 2\n", encoding="utf-8")
    content_tiny = read_file_smart(str(tiny_file))
    assert "[DIFF]" not in content_tiny
    assert "x = 2" in content_tiny


def test_persistent_cache(tmp_path):
    from token_saver.cache.session_cache import SessionCache
    db_file = tmp_path / "test_cache.db"

    # Session 1: Read a file
    cache1 = SessionCache(persistent=True, db_path=db_file)
    res1 = cache1.get("my_file.py", "print('hello world')")
    assert res1.status == "first_read"

    # Session 2: New SessionCache instance simulating process restart
    cache2 = SessionCache(persistent=True, db_path=db_file)
    res2 = cache2.get("my_file.py", "print('hello world')")
    # Must hit L2 persistent cache as unchanged even though memory was fresh
    assert res2.status == "unchanged"
    assert "[CACHED]" in res2.content


def test_large_file_cache_protection(tmp_path):
    from token_saver.cache.persistent_cache import PersistentCache
    from token_saver.cache.session_cache import SessionCache
    db_file = tmp_path / "large_cache.db"

    # Create content larger than MAX_CACHEABLE_BYTES (5MB)
    large_content = "A" * (6 * 1024 * 1024)

    cache1 = SessionCache(persistent=True, db_path=db_file)
    res1 = cache1.get("huge_bundle.js", large_content)
    assert res1.status == "first_read"

    import os
    norm_path = os.path.normpath(os.path.abspath("huge_bundle.js"))

    # Check that SQLite stored the marker rather than 6MB blob
    p_cache = PersistentCache(db_file)
    persisted = p_cache.get_entry(norm_path)
    assert persisted is not None
    p_hash, p_content, _ = persisted
    assert p_content.startswith("__TOKEN_SAVER_LARGE_FILE__:")
    assert len(p_content) < 100  # Saved database from 6MB bloat!

    # Second read in fresh session: still accurately detects unchanged!
    cache2 = SessionCache(persistent=True, db_path=db_file)
    res2 = cache2.get("huge_bundle.js", large_content)
    assert res2.status == "unchanged"
    assert "[CACHED]" in res2.content

