from __future__ import annotations
import re

def filter_npm_yarn(output: str) -> str:
    """Remove individual package download lines, keep summary and warnings/errors."""
    lines = output.split('\n')
    filtered = []
    for line in lines:
        if re.match(r'^(npm |yarn |pnpm ).*(fetch|add|install)', line, re.IGNORECASE) or \
           re.match(r'^\s*\[[0-9/]+\]\s+', line) or \
           "GET" in line or "fetch" in line.lower() or "download" in line.lower():
            continue
        filtered.append(line)
    return '\n'.join(filtered)

def filter_cargo(output: str) -> str:
    """Remove successful compilation lines, keep warnings and errors."""
    lines = output.split('\n')
    filtered = []
    for line in lines:
        if re.match(r'^\s*Compiling\s+', line) or re.match(r'^\s*Downloaded\s+', line):
            continue
        filtered.append(line)
    return '\n'.join(filtered)

def filter_generic_build(output: str) -> str:
    """Remove progress indicators, keep errors."""
    lines = output.split('\n')
    filtered = []
    for line in lines:
        if re.match(r'^[\[\d+%\]|\.]', line.strip()) and len(line) < 20:
            continue
        filtered.append(line)
    return '\n'.join(filtered)

def detect_and_filter_build(output: str) -> str | None:
    """Auto-detects the build tool and applies the right filter."""
    if "npm" in output or "yarn" in output or "pnpm" in output or "node_modules" in output:
        return filter_npm_yarn(output)
    elif "Compiling" in output and "Cargo" in output:
        return filter_cargo(output)
    return None
