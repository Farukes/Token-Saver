from __future__ import annotations

import re


def filter_git_output(output: str) -> str:
    """Filters git command outputs by stripping help hints and suggestion lines."""
    lines = output.split("\n")
    filtered = []

    for line in lines:
        stripped = line.strip()
        # Skip standalone hint lines
        if stripped.startswith('(use "git') or stripped.startswith("(use 'git"):
            continue
        if stripped.startswith("hint:"):
            continue
        # Remove inline hint parentheticals from lines
        # e.g., "nothing added to commit but untracked files present (use "git add" to track)"
        cleaned = re.sub(r'\s*\(use ["\']git\s[^)]*\)', "", line)
        filtered.append(cleaned)

    return "\n".join(filtered)
