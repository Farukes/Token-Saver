//! Ultra-fast ANSI terminal escape sequence stripper.

use regex::Regex;
use std::sync::LazyLock;

static ANSI_REGEX: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])").unwrap());

/// Strip all ANSI color and cursor escape sequences from terminal output.
pub fn strip_ansi(text: &str) -> String {
    ANSI_REGEX.replace_all(text, "").into_owned()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_strip_ansi() {
        let input = "\x1b[31mError:\x1b[0m Failed test";
        assert_eq!(strip_ansi(input), "Error: Failed test");
    }
}
