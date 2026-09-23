"""Approximate token counter utility.

Uses a character-based heuristic (~4 chars per token) for fast estimation.
Optionally uses tiktoken for exact OpenAI tokenizer counts.
"""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Estimate token count using character-based heuristic.

    Uses the industry-standard approximation of ~4 characters per token,
    which is accurate within ±10% for English text and code.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def count_tokens_exact(text: str, model: str = "gpt-4o") -> int:
    """Count exact tokens using tiktoken (requires 'counting' extra).

    Falls back to heuristic estimation if tiktoken is not installed.
    """
    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except (ImportError, KeyError):
        return estimate_tokens(text)


def format_savings(original: str, optimized: str) -> str:
    """Format a human-readable savings summary.

    Returns a string like: '847 → 127 tokens (85.0% saved)'
    """
    orig_tokens = estimate_tokens(original)
    opt_tokens = estimate_tokens(optimized)

    if orig_tokens == 0:
        return "0 → 0 tokens (no content)"

    saved_pct = (1 - opt_tokens / orig_tokens) * 100
    return f"{orig_tokens} → {opt_tokens} tokens ({saved_pct:.1f}% saved)"
