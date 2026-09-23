"""Filters for build, package management, container, and infrastructure tool outputs."""

from __future__ import annotations

import re


def filter_npm_yarn(output: str) -> str:
    """Remove individual package download lines, keep summary and warnings/errors."""
    lines = output.split('\n')
    filtered = []
    for line in lines:
        if (
            re.match(r'^(npm |yarn |pnpm ).*(fetch|add|install)', line, re.IGNORECASE)
            or re.match(r'^\s*\[[0-9/]+\]\s+', line)
            or "GET" in line
            or "fetch" in line.lower()
            or "download" in line.lower()
        ):
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


def filter_docker(output: str) -> str:
    """Filter verbose docker build/compose logs, keeping step headers, warnings, and errors."""
    lines = output.split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        # Skip intermediate hash lines and cache notes
        if re.match(r'^\s*--->\s+[a-f0-9]+', stripped) or stripped == "---> Using cache":
            continue
        if stripped.startswith("Removing intermediate container"):
            continue
        filtered.append(line)
    return '\n'.join(filtered)


def filter_maven_gradle(output: str) -> str:
    """Filter Maven and Gradle build output, removing repetitive download/task logs."""
    lines = output.split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        # Skip downloading / downloaded artifacts
        if stripped.startswith("Downloading from") or stripped.startswith("Downloaded from"):
            continue
        if stripped.startswith("Download http"):
            continue
        # Skip intermediate task execution progress
        if re.match(r'^>\s*Task\s+:[a-zA-Z0-9_:]+\s+UP-TO-DATE$', stripped):
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
    elif ("Compiling" in output and "Cargo" in output) or "cargo" in output.lower():
        return filter_cargo(output)
    elif "Step " in output and ("--->" in output or "docker" in output.lower()):
        return filter_docker(output)
    elif "[INFO] Building" in output or "BUILD SUCCESS" in output or "BUILD FAILED" in output or "Gradle" in output:
        return filter_maven_gradle(output)
    return None
