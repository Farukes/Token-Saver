"""Token counter utility with multi-provider calibration.

Supports model-specific calibrations (Claude, OpenAI, Gemini) and code-density
adjustments (~3.2 chars/token for code vs ~4.0 for prose).
Optionally uses tiktoken for exact OpenAI counts.
"""

from __future__ import annotations

import os


def get_active_model_family() -> str:
    """Detect active model family from environment variables or defaults."""
    env_model = os.environ.get("TOKEN_SAVER_MODEL", "").lower()
    if any(k in env_model for k in ("claude", "anthropic")):
        return "claude"
    if any(k in env_model for k in ("gemini", "google")):
        return "gemini"
    if any(k in env_model for k in ("gpt", "openai", "o1", "o3")):
        return "openai"
    return "auto"


def estimate_tokens(text: str, model_family: str | None = None) -> int:
    """Estimate token count using model-calibrated heuristic.

    Source code has higher token density than prose due to operators,
    indentation, and camelCase identifiers (~3.2 chars per token).
    """
    if not text:
        return 0

    family = model_family or get_active_model_family()

    # Try exact counting if tiktoken is available and OpenAI family is selected
    if family == "openai":
        try:
            import tiktoken

            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            pass

    # Model calibrations for code
    if family == "claude":
        # Anthropic Claude code token ratio ~3.3 chars per token
        ratio = 3.3
    elif family == "gemini":
        # Google Gemini code token ratio ~3.4 chars per token
        ratio = 3.4
    elif family == "openai":
        # OpenAI code token ratio ~3.2 chars per token
        ratio = 3.2
    else:
        # Auto/code heuristic: detects code vs prose
        is_code = any(c in text[:500] for c in ("def ", "function ", "class ", "{", "}", "import ", ";"))
        ratio = 3.2 if is_code else 3.8

    return max(1, int(len(text) / ratio))


def count_tokens_exact(text: str, model: str = "gpt-4o") -> int:
    """Count exact tokens using tiktoken if available, else heuristic."""
    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except (ImportError, KeyError):
        return estimate_tokens(text, model_family="openai")


def format_savings(original: str, optimized: str, model_family: str | None = None) -> str:
    """Format a human-readable savings summary (ASCII safe for all OS code pages).

    Returns a string like: '847 -> 127 tokens (85.0% saved)'
    """
    orig_tokens = estimate_tokens(original, model_family)
    opt_tokens = estimate_tokens(optimized, model_family)

    if orig_tokens == 0:
        return "0 -> 0 tokens (no content)"

    saved_pct = (1 - opt_tokens / orig_tokens) * 100
    return f"{orig_tokens} -> {opt_tokens} tokens ({saved_pct:.1f}% saved)"
