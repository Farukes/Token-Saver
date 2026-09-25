//! Git output filter for Token-Saver in Rust.
//!
//! Prunes verbose suggestions, hint lines, and redundant git CLI noise.

use regex::Regex;

/// Filters git command outputs by stripping help hints and suggestion lines.
pub fn filter_git_output(output: &str) -> String {
    let re_inline = Regex::new(r#"\s*\(use ["']git\s[^)]*\)"#).unwrap();
    let mut filtered = Vec::new();

    for line in output.lines() {
        let stripped = line.trim();
        // Skip standalone suggestion and hint lines
        if stripped.starts_with("(use \"git") || stripped.starts_with("(use 'git") {
            continue;
        }
        if stripped.starts_with("hint:") {
            continue;
        }

        // Clean inline parentheticals like:
        // "nothing added to commit but untracked files present (use \"git add\" to track)"
        let cleaned = re_inline.replace_all(line, "").to_string();
        filtered.push(cleaned);
    }

    filtered.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_filter_git_output() {
        let input = "On branch main\n\
Your branch is up to date with 'origin/main'.\n\
\n\
Changes not staged for commit:\n\
  (use \"git add <file>...\" to update what will be committed)\n\
  (use \"git restore <file>...\" to discard changes in working directory)\n\
\tmodified:   src/main.rs\n\
\n\
no changes added to commit (use \"git add\" and/or \"git commit -a\")";

        let result = filter_git_output(input);
        assert!(!result.contains("(use \"git add <file>...\")"));
        assert!(!result.contains("(use \"git restore <file>...\")"));
        assert!(result.contains("modified:   src/main.rs"));
        assert!(result.contains("no changes added to commit"));
    }
}
