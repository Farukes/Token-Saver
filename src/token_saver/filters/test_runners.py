from __future__ import annotations

import re


def filter_pytest(output: str) -> str:
    """Summarize passing tests, show only failures with tracebacks."""
    # Check if this is an unhandled collection error or raw Python traceback
    if (
        "Traceback (most recent call last):" in output
        and "=== FAILURES ===" not in output
        and "=== ERRORS ===" not in output
    ):
        return output.strip()

    lines = output.split("\n")
    filtered = []

    in_failures = False
    passed_count = 0
    failed_count = 0

    for line in lines:
        if (
            "=== FAILURES ===" in line
            or "=== ERRORS ===" in line
            or "=== short test summary info ===" in line
            or line.startswith("ERROR collecting ")
        ):
            in_failures = True
            filtered.append(line)
            continue

        if in_failures:
            filtered.append(line)
        else:
            if re.match(r"^.*?\s+PASSED\s*\[.*\]$", line) or re.match(r"^.*?\s+PASSED$", line) or " PASSED " in line:
                passed_count += 1
            elif re.match(r"^.*?\s+FAILED\s*\[.*\]$", line) or re.match(r"^.*?\s+FAILED$", line) or " FAILED " in line:
                failed_count += 1
            elif "collected " in line and " items" in line:
                filtered.append(line)
            elif "test session starts" in line or line.startswith("platform ") or line.startswith("rootdir:"):
                filtered.append(line)
            elif line.startswith("E   ") or "Error:" in line or "Exception:" in line:
                filtered.append(line)
            elif "passed in " in line or "failed in " in line or "passed," in line:
                m_pass = re.search(r"(\d+)\s+passed", line)
                if m_pass and passed_count == 0:
                    passed_count = int(m_pass.group(1))
                m_fail = re.search(r"(\d+)\s+failed", line)
                if m_fail and failed_count == 0:
                    failed_count = int(m_fail.group(1))

    # Try to find the summary line to get stats if we missed them
    if not in_failures:
        filtered.append(f"pytest: {failed_count} FAILED, {passed_count} passed")

    return "\n".join(filtered)


def filter_jest_vitest(output: str) -> str:
    """Summarize test suites, show only failures for jest/vitest."""
    lines = output.split("\n")
    filtered = []

    for line in lines:
        if line.strip().startswith("✓") or line.strip().startswith("PASS") or "✓" in line:
            continue
        filtered.append(line)

    return "\n".join(filtered)


def filter_go_test(output: str) -> str:
    """Summarize passing, show only failures for go test."""
    lines = output.split("\n")
    filtered = []

    for line in lines:
        if line.strip().startswith("=== RUN") or line.strip().startswith("--- PASS:") or line.strip() == "PASS":
            continue
        if re.match(r"^ok\s+", line):
            filtered.append(line)
            continue
        filtered.append(line)

    return "\n".join(filtered)


def filter_cargo(output: str) -> str:
    """Filter cargo test and build output, pruning passing tests and keeping summaries/failures."""
    lines = output.split("\n")
    kept = []
    in_failure = False

    for line in lines:
        trimmed = line.strip()
        if (
            trimmed.startswith("error")
            or trimmed.startswith("error:")
            or trimmed.startswith("failures:")
            or trimmed.startswith("----")
            or trimmed.startswith("FAILED")
        ):
            in_failure = True
        elif trimmed.startswith("test result:"):
            in_failure = False

        if in_failure or trimmed.startswith("test result:") or trimmed.startswith("warning:"):
            kept.append(line)

    if not kept:
        return output
    return "\n".join(kept)


def filter_generic_test(output: str) -> str:
    """Basic cleanup for generic test output."""
    return output


def detect_and_filter_tests(output: str) -> str | None:
    """Auto-detects the test runner and applies the right filter."""
    if "pytest" in output and (
        "test session starts" in output or "=== FAILURES ===" in output or "collected" in output
    ):
        return filter_pytest(output)
    elif "test result:" in output and ("passed" in output or "failed" in output):
        return filter_cargo(output)
    elif "Test Suites:" in output and (
        "jest" in output.lower() or "vitest" in output.lower() or "✓" in output or "✕" in output
    ):
        return filter_jest_vitest(output)
    elif re.search(r"^=== RUN\s+", output, re.MULTILINE) or re.search(r"^--- (PASS|FAIL):", output, re.MULTILINE):
        return filter_go_test(output)
    return None
