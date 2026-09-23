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
    
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
    file_path = str(test_file)
    
    # 1. First read returns full content (status: first_read)
    content1 = read_file_smart(file_path)
    assert content1 == "line 1\nline 2\nline 3\n"
    
    # 2. Second read of unchanged file returns cached message (status: unchanged)
    content2 = read_file_smart(file_path)
    assert "[CACHED]" in content2
    assert "unchanged since last read" in content2
    assert "tokens (" in content2
    
    # 3. Modified file returns diff (status: changed)
    test_file.write_text("line 1\nline 2 modified\nline 3\n", encoding="utf-8")
    content3 = read_file_smart(file_path)
    assert "[DIFF]" in content3
    assert "line 2 modified" in content3
    assert "tokens (" in content3
    
    # 4. force_full bypasses cache
    content4 = read_file_smart(file_path, force_full=True)
    assert content4 == "line 1\nline 2 modified\nline 3\n"
    
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
