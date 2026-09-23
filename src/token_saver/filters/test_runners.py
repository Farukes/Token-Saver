from __future__ import annotations
import re

def filter_pytest(output: str) -> str:
    """Summarize passing tests, show only failures with tracebacks."""
    lines = output.split('\n')
    filtered = []
    
    in_failures = False
    passed_count = 0
    failed_count = 0
    
    for line in lines:
        if "=== FAILURES ===" in line or "=== ERRORS ===" in line or "=== short test summary info ===" in line:
            in_failures = True
            filtered.append(line)
            continue
            
        if in_failures:
            filtered.append(line)
        else:
            if re.match(r'^.*?\s+PASSED\s*\[.*\]$', line) or re.match(r'^.*?\s+PASSED$', line) or " PASSED " in line:
                passed_count += 1
            elif re.match(r'^.*?\s+FAILED\s*\[.*\]$', line) or re.match(r'^.*?\s+FAILED$', line) or " FAILED " in line:
                failed_count += 1
            elif "collected " in line and " items" in line:
                filtered.append(line)
            elif "test session starts" in line or line.startswith("platform ") or line.startswith("rootdir:"):
                filtered.append(line)
    
    # Try to find the summary line to get stats if we missed them
    if not in_failures:
        filtered.append(f"pytest: {failed_count} FAILED, {passed_count} passed")
        
    return '\n'.join(filtered)

def filter_jest_vitest(output: str) -> str:
    """Summarize test suites, show only failures for jest/vitest."""
    lines = output.split('\n')
    filtered = []
    
    for line in lines:
        if line.strip().startswith('✓') or line.strip().startswith('PASS') or '✓' in line:
            continue
        filtered.append(line)
        
    return '\n'.join(filtered)

def filter_go_test(output: str) -> str:
    """Summarize passing, show only failures for go test."""
    lines = output.split('\n')
    filtered = []
    
    for line in lines:
        if line.strip().startswith('=== RUN') or line.strip().startswith('--- PASS:') or line.strip() == 'PASS':
            continue
        if re.match(r'^ok\s+', line):
            filtered.append(line)
            continue
        filtered.append(line)
            
    return '\n'.join(filtered)

def filter_generic_test(output: str) -> str:
    """Basic cleanup for generic test output."""
    return output

def detect_and_filter_tests(output: str) -> str | None:
    """Auto-detects the test runner and applies the right filter."""
    if "pytest" in output and ("test session starts" in output or "=== FAILURES ===" in output or "collected" in output):
        return filter_pytest(output)
    elif "Test Suites:" in output and ("jest" in output.lower() or "vitest" in output.lower() or "✓" in output or "✕" in output):
        return filter_jest_vitest(output)
    elif re.search(r'^=== RUN\s+', output, re.MULTILINE) or re.search(r'^--- (PASS|FAIL):', output, re.MULTILINE):
        return filter_go_test(output)
    return None
