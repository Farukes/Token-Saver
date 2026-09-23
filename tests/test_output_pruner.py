from __future__ import annotations
import pytest
from token_saver.filters.ansi import strip_ansi
from token_saver.filters.test_runners import filter_pytest
from token_saver.filters.build_tools import filter_npm_yarn
from token_saver.filters.git import filter_git_output
from token_saver.tools.output_pruner import filter_output_logic
import token_saver.utils.token_counter

def test_strip_ansi():
    text_with_ansi = "\x1b[32mSuccess\x1b[0m"
    assert strip_ansi(text_with_ansi) == "Success"

def test_filter_pytest():
    pytest_out = """
test session starts
collected 3 items

test_1.py PASSED [ 33%]
test_2.py FAILED [ 66%]
test_3.py PASSED [100%]

=== FAILURES ===
_ test_2 _
def test_2():
>   assert False
E   assert False

=== short test summary info ===
FAILED test_2.py::test_2 - assert False
=== 1 failed, 2 passed in 0.12s ===
"""
    filtered = filter_pytest(pytest_out)
    assert "test_1.py PASSED" not in filtered
    assert "=== FAILURES ===" in filtered
    assert "assert False" in filtered

def test_filter_npm():
    npm_out = """
npm WARN deprecated request@2.88.2: request has been deprecated
npm fetch GET 200 https://registry.npmjs.org/lodash 50ms
[1/4] Resolving packages...
added 1 package, and audited 2 packages in 1s
"""
    filtered = filter_npm_yarn(npm_out)
    assert "npm fetch" not in filtered
    assert "[1/4]" not in filtered
    assert "added 1 package" in filtered
    assert "npm WARN" in filtered

def test_filter_git():
    git_out = """
On branch main
Your branch is up to date with 'origin/main'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	new_file.txt

nothing added to commit but untracked files present (use "git add" to track)
"""
    filtered = filter_git_output(git_out)
    assert '(use "git add <file>..."' not in filtered
    assert '(use "git add" to track)' not in filtered
    assert "Untracked files:" in filtered

def test_token_savings(monkeypatch):
    monkeypatch.setattr(token_saver.utils.token_counter, "estimate_tokens", lambda x: len(x) // 4)
    
    # Build a realistic verbose pytest output that the filter can detect and compress
    passed_lines = "\n".join([f"tests/test_{i}.py PASSED [{i}%]" for i in range(1, 100)])
    verbose_out = f"""test session starts
platform win32 -- Python 3.10.0, pytest-9.1.1
collected 100 items

{passed_lines}
tests/test_100.py FAILED [100%]

=== FAILURES ===
_ test_100 _
def test_100():
>   assert False
E   assert False

=== short test summary info ===
FAILED tests/test_100.py::test_100 - assert False
=== 1 failed, 99 passed in 0.12s ===
"""
    filtered = filter_output_logic(verbose_out, output_type="pytest")
    assert "Token-Saver" in filtered
    
    import re
    match = re.search(r'\((\d+)% saved\)', filtered)
    assert match is not None
    saved = int(match.group(1))
    assert saved >= 50
