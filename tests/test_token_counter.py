from __future__ import annotations

from token_saver.utils.token_counter import estimate_tokens, format_savings


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0
    assert estimate_tokens(None) == 0


def test_model_calibrations():
    code_sample = "def calculate_discount(price: float, rate: float) -> float:\n    return price * (1.0 - rate)\n"
    # Claude calibration
    t_claude = estimate_tokens(code_sample, model_family="claude")
    # Gemini calibration
    t_gemini = estimate_tokens(code_sample, model_family="gemini")
    # OpenAI calibration
    t_openai = estimate_tokens(code_sample, model_family="openai")

    assert t_claude > 0
    assert t_gemini > 0
    assert t_openai > 0


def test_format_savings_ascii():
    res = format_savings("A" * 1000, "A" * 100)
    assert "->" in res
    assert "% saved" in res
