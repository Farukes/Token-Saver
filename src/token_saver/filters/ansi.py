from __future__ import annotations

import re

# Regex that matches ALL ANSI escape sequences (colors, cursor, etc.)
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b\([B0UK]|\r")


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape codes from text."""
    return ANSI_PATTERN.sub("", text)
