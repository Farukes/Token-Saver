//! Fast heuristic token estimation matching OpenAI / Claude approximations.

/// Estimate tokens for a given string slice (~4 chars per token).
pub fn estimate_tokens(text: &str) -> usize {
    if text.is_empty() {
        return 0;
    }
    let char_count = text.chars().count();
    (char_count / 4).max(1)
}

/// Format token savings summary string.
pub fn format_savings(original: &str, optimized: &str) -> String {
    let orig = estimate_tokens(original);
    let opt = estimate_tokens(optimized);
    let saved = orig.saturating_sub(opt);
    let pct = if orig > 0 {
        ((saved as f64 / orig as f64) * 100.0) as u32
    } else {
        0
    };
    format!("{orig} -> {opt} tokens ({pct}% saved)")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_estimate_tokens() {
        assert_eq!(estimate_tokens(""), 0);
        assert_eq!(estimate_tokens("hello"), 1);
        assert_eq!(estimate_tokens(&"a".repeat(400)), 100);
    }

    #[test]
    fn test_format_savings() {
        let orig = "a".repeat(400);
        let opt = "a".repeat(40);
        let res = format_savings(&orig, &opt);
        assert!(res.contains("100 -> 10"));
        assert!(res.contains("90% saved"));
    }
}
