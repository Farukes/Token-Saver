from __future__ import annotations

import token_saver.utils.token_counter
from token_saver.filters.ansi import strip_ansi
from token_saver.filters.build_tools import filter_npm_yarn
from token_saver.filters.git import filter_git_output
from token_saver.filters.test_runners import filter_pytest
from token_saver.tools.output_pruner import filter_output_logic


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


def test_fallback_safety_guard():
    # An unhandled traceback from a failed command (exit_code != 0)
    raw_error = """Traceback (most recent call last):
  File "conftest.py", line 2, in <module>
    import non_existent_dependency
ModuleNotFoundError: No module named 'non_existent_dependency'
"""
    # Auto-filter with exit_code=1 must NOT swallow the error
    result = filter_output_logic(raw_error, output_type="auto", exit_code=1)
    assert "ModuleNotFoundError" in result
    assert "non_existent_dependency" in result
    assert "Traceback" in result


def test_stream_ceiling_guard():
    # Simulate runaway output (> 2MB)
    runaway_chunk = "INFO: processing line of infinite output...\n"
    repeat_count = (3 * 1024 * 1024) // len(runaway_chunk)
    huge_output = runaway_chunk * repeat_count
    assert len(huge_output) > 2 * 1024 * 1024

    filtered = filter_output_logic(huge_output, output_type="generic")
    assert "Token-Saver Stream Guard" in filtered
    assert "Truncated" in filtered
    # Length of filtered output should now be under 2MB
    assert len(filtered) < 2 * 1024 * 1024


def test_background_command_launch():
    from token_saver.tools.output_pruner import register_output_pruner_tools

    class DummyMCP:
        def __init__(self):
            self.tools = {}

        def tool(self):
            def dec(f):
                self.tools[f.__name__] = f
                return f

            return dec

    dummy = DummyMCP()
    register_output_pruner_tools(dummy)
    run_cmd = dummy.tools["run_command_smart"]

    res = run_cmd("echo background_test", background=True)
    assert "[BACKGROUND PROCESS LAUNCHED]" in res
    assert "PID:" in res

