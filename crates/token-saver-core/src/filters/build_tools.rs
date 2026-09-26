//! Build, package manager, and container output filters in Rust.
//!
//! Prunes npm/yarn/pnpm download noise, docker layer hashes, and build logs.

use regex::Regex;

/// Removes individual package download lines, keeping summary and warnings/errors.
pub fn filter_npm_yarn(output: &str) -> String {
    let re_fetch = Regex::new(r"(?i)^(npm |yarn |pnpm ).*(fetch|add|install)").unwrap();
    let re_progress = Regex::new(r"^\s*\[[0-9/]+\]\s+").unwrap();

    let mut filtered = Vec::new();
    for line in output.lines() {
        let lower = line.to_lowercase();
        if re_fetch.is_match(line)
            || re_progress.is_match(line)
            || line.contains("GET ")
            || lower.contains("fetch")
            || lower.contains("download")
        {
            continue;
        }
        filtered.push(line);
    }
    filtered.join("\n")
}

/// Removes docker build intermediate container noise and cache hints.
pub fn filter_docker(output: &str) -> String {
    let re_layer = Regex::new(r"^\s*--->\s+[a-f0-9]+").unwrap();

    let mut filtered = Vec::new();
    for line in output.lines() {
        let stripped = line.trim();
        if re_layer.is_match(stripped)
            || stripped == "---> Using cache"
            || stripped.starts_with("Removing intermediate container")
        {
            continue;
        }
        filtered.push(line);
    }
    filtered.join("\n")
}

/// Auto-detects build/package manager type and prunes verbose lines.
pub fn detect_and_filter_build(output: &str) -> Option<String> {
    if output.contains("npm ")
        || output.contains("yarn ")
        || output.contains("pnpm ")
        || output.contains("node_modules")
    {
        Some(filter_npm_yarn(output))
    } else if output.contains("Step ")
        && (output.contains("--->") || output.to_lowercase().contains("docker"))
    {
        Some(filter_docker(output))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_filter_npm_yarn() {
        let input = "npm WARN deprecated package@1.0.0\n\
npm fetch GET 200 https://registry.npmjs.org/package\n\
[1/4] Resolving packages...\n\
added 52 packages in 2.3s";

        let result = filter_npm_yarn(input);
        assert!(result.contains("npm WARN deprecated"));
        assert!(!result.contains("fetch GET 200"));
        assert!(!result.contains("[1/4] Resolving"));
        assert!(result.contains("added 52 packages in 2.3s"));
    }
}
