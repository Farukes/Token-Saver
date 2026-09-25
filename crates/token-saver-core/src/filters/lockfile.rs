//! Lockfile and giant asset shield for Token-Saver.
//!
//! Intercepts massive auto-generated files (package-lock.json, Cargo.lock, minified bundles)
//! and provides surgical package queries and structural summaries to prevent context compaction.

use std::path::Path;
use serde_json::Value;

/// Locate a specific package or dependency entry in lockfile content.
pub fn find_package_in_lockfile(base_name: &str, content: &str, query: &str) -> Option<String> {
    let q = query.trim();
    if q.is_empty() {
        return None;
    }

    let lower_name = base_name.to_lowercase();

    // 1. NPM / Node: package-lock.json
    if lower_name.contains("package-lock") || lower_name.contains("shrinkwrap") {
        if let Ok(v) = serde_json::from_str::<Value>(content) {
            // v2/v3: check "packages"
            if let Some(packages) = v.get("packages").and_then(|p| p.as_object()) {
                let candidates = [
                    format!("node_modules/{q}"),
                    format!("node_modules/{}", q.to_lowercase()),
                    q.to_string(),
                    q.to_lowercase(),
                ];
                for cand in &candidates {
                    if let Some(pkg) = packages.get(cand) {
                        let mut map = serde_json::Map::new();
                        map.insert(cand.clone(), pkg.clone());
                        return serde_json::to_string_pretty(&Value::Object(map)).ok();
                    }
                }
                // Partial match
                let mut matches = serde_json::Map::new();
                for (k, val) in packages {
                    if k.to_lowercase().contains(&q.to_lowercase()) {
                        matches.insert(k.clone(), val.clone());
                        if matches.len() >= 3 {
                            break;
                        }
                    }
                }
                if !matches.is_empty() {
                    return serde_json::to_string_pretty(&Value::Object(matches)).ok();
                }
            }

            // v1: check "dependencies"
            if let Some(deps) = v.get("dependencies").and_then(|d| d.as_object()) {
                for (k, val) in deps {
                    if k.eq_ignore_ascii_case(q) || k.to_lowercase().contains(&q.to_lowercase()) {
                        let mut map = serde_json::Map::new();
                        map.insert(k.clone(), val.clone());
                        return serde_json::to_string_pretty(&Value::Object(map)).ok();
                    }
                }
            }
        }
    }

    // 2. Cargo.lock and poetry.lock (TOML [[package]] blocks)
    if lower_name.contains("cargo.lock") || lower_name.contains("poetry.lock") {
        let mut blocks = Vec::new();
        let mut current_block = Vec::new();
        let mut in_target = false;

        for line in content.lines() {
            if line.trim().starts_with("[[package]]") {
                if in_target && !current_block.is_empty() {
                    blocks.push(current_block.join("\n"));
                }
                current_block.clear();
                in_target = false;
            }
            current_block.push(line);
            if line.contains("name =") && line.to_lowercase().contains(&q.to_lowercase()) {
                in_target = true;
            }
        }
        if in_target && !current_block.is_empty() {
            blocks.push(current_block.join("\n"));
        }
        if !blocks.is_empty() {
            return Some(blocks.join("\n\n"));
        }
    }

    // 3. Fallback: line-based search for yarn, poetry, pnpm, etc.
    let lines: Vec<&str> = content.lines().collect();
    let mut matching_blocks = Vec::new();

    for (i, line) in lines.iter().enumerate() {
        if line.to_lowercase().contains(&q.to_lowercase()) {
            let start = i.saturating_sub(2);
            let end = (i + 12).min(lines.len());
            matching_blocks.push(lines[start..end].join("\n"));
            if matching_blocks.len() >= 3 {
                break;
            }
        }
    }

    if !matching_blocks.is_empty() {
        Some(matching_blocks.join("\n---\n"))
    } else {
        None
    }
}

/// Process a shielded lockfile or giant asset.
pub fn process_lockfile(file_path: &Path, content: &str, query: Option<&str>) -> String {
    let base_name = file_path.file_name().and_then(|n| n.to_str()).unwrap_or("lockfile");
    let total_lines = content.lines().count();
    let total_bytes = content.len();

    if let Some(q) = query.filter(|q| !q.trim().is_empty()) {
        let q = q.trim();
        if let Some(matched) = find_package_in_lockfile(base_name, content, q) {
            let match_lines = matched.lines().count();
            return format!(
                "[TOKEN-SAVER LOCKFILE SHIELD: Surgical Query for '{q}']\n\
                 File: {base_name} ({total_lines} total lines, {total_bytes} bytes)\n\
                 Matching dependency block ({match_lines} lines):\n\n\
                 {matched}\n\n\
                 [Tip: pass force_full=true to read the entire raw file without query filtering]"
            );
        } else {
            return format!(
                "[TOKEN-SAVER LOCKFILE SHIELD: Query Not Found]\n\
                 Package '{q}' was not located in {base_name} ({total_lines} lines).\n\
                 Pass force_full=true if you need to read the full file."
            );
        }
    }

    // No query provided: Return structural summary
    format!(
        "[TOKEN-SAVER SHIELD: Large Lockfile/Asset Intercepted]\n\
         File: {base_name} ({total_lines} lines, {total_bytes} bytes)\n\n\
         Reading this full file would consume an estimated ~{} tokens and degrade context window.\n\n\
         Options:\n\
         1. Surgical Query: read_file_smart(file_path=\"{base_name}\", query=\"<package-name>\")\n\
         2. Full Read (Bypass): read_file_smart(file_path=\"{base_name}\", force_full=true)",
        crate::token_counter::estimate_tokens(content)
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_find_package_in_npm_lockfile() {
        let lock = r#"{
          "name": "test-project",
          "packages": {
            "node_modules/express": {
              "version": "4.19.2",
              "resolved": "https://registry.npmjs.org/express/-/express-4.19.2.tgz"
            }
          }
        }"#;

        let result = find_package_in_lockfile("package-lock.json", lock, "express");
        assert!(result.is_some());
        let res = result.unwrap();
        assert!(res.contains("4.19.2"));
    }

    #[test]
    fn test_process_lockfile_summary() {
        let text = "a\n".repeat(1000);
        let summary = process_lockfile(Path::new("Cargo.lock"), &text, None);
        assert!(summary.contains("TOKEN-SAVER SHIELD"));
        assert!(summary.contains("Cargo.lock"));
    }
}
