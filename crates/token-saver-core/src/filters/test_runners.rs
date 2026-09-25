//! Test runner and build output pruners (pytest, jest, cargo, npm, git).

use regex::Regex;
use std::sync::LazyLock;

static PYTEST_PROGRESS_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(?:tests[/\\].*?\s+\[\s*\d+%\]|[.sF]{5,})").unwrap()
});

/// Filter pytest output, pruning passing dots and retaining failure tracebacks.
pub fn filter_pytest(output: &str) -> String {
    let lines: Vec<&str> = output.lines().collect();
    let mut kept_lines = Vec::new();
    let mut in_failure = false;
    let mut passed_count = 0;
    let mut failed_count = 0;

    for line in &lines {
        let trimmed = line.trim();

        if trimmed.starts_with("FAILED ") {
            failed_count += 1;
        }

        if trimmed.starts_with("=== FAILURES ===") || trimmed.starts_with("=== ERRORS ===") {
            in_failure = true;
        } else if trimmed.starts_with("=== short test summary info ===") {
            in_failure = false;
        }

        if in_failure {
            kept_lines.push(*line);
            continue;
        }

        // Check for test session start or summary
        if trimmed.starts_with("===")
            || trimmed.starts_with("rootdir:")
            || trimmed.starts_with("collected ")
            || trimmed.starts_with("FAILED ")
            || trimmed.starts_with("ERROR ")
        {
            kept_lines.push(*line);
            continue;
        }

        // If it's repetitive passing progress, count and skip
        if PYTEST_PROGRESS_RE.is_match(trimmed) && trimmed.ends_with(".PASSED") || trimmed.ends_with("[100%]") && !trimmed.contains("FAILED") {
            passed_count += 1;
            continue;
        }

        // Keep warnings and other summary lines
        if trimmed.starts_with("warning:") || trimmed.starts_with("AssertionError") || trimmed.contains("passed in") {
            kept_lines.push(*line);
        }
    }

    if kept_lines.is_empty() {
        return output.to_string();
    }

    let summary = format!("pytest: {failed_count} FAILED, {passed_count} passed (repetitive logs pruned)");
    format!("{}\n{summary}", kept_lines.join("\n"))
}

/// Filter cargo test/build output.
pub fn filter_cargo(output: &str) -> String {
    let mut kept = Vec::new();
    let mut in_failure = false;

    for line in output.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("error") || trimmed.starts_with("error:") || trimmed.starts_with("failures:") {
            in_failure = true;
        } else if trimmed.starts_with("test result:") {
            in_failure = false;
        }

        if in_failure || trimmed.starts_with("test result:") || trimmed.starts_with("warning:") {
            kept.push(line);
        }
    }

    if kept.is_empty() {
        output.to_string()
    } else {
        kept.join("\n")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_filter_cargo() {
        let cargo_output = "\
Compiling foo v0.1.0\n\
Running unittests\n\
test result: ok. 5 passed; 0 failed\n";
        let filtered = filter_cargo(cargo_output);
        assert!(filtered.contains("test result: ok. 5 passed"));
    }
}
