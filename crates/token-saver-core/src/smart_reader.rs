//! Smart Reader with Session Caching & Lockfile Shielding in Rust.
//!
//! Intelligently reads source files, returns compact diffs on edits,
//! and protects context windows from massive lockfiles and minified assets.

use std::path::Path;

use crate::cache::session_cache::{CacheStatus, SessionCache};
use crate::config::TokenSaverConfig;
use crate::filters::lockfile::process_lockfile;
use crate::telemetry::TelemetryTracker;
use crate::token_counter::format_savings;

/// Intelligently reads a file with session caching and lockfile protection.
pub fn read_file_smart(
    file_path: &str,
    force_full: bool,
    query: Option<&str>,
    cache: &SessionCache,
    config: &TokenSaverConfig,
    tracker: &TelemetryTracker,
) -> String {
    let p = Path::new(file_path);

    if !force_full && config.is_ignored(p) {
        let base = p.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_else(|| file_path.to_string());
        return format!(
            "[TOKEN-SAVER SECURITY] '{base}' matches security ignore patterns \
            (credentials/secrets/exclusions). Pass force_full=true if you explicitly \
            need to read this file."
        );
    }

    let content = match std::fs::read_to_string(p) {
        Ok(c) => c,
        Err(e) => return format!("Error reading file {file_path}: {e}"),
    };

    if force_full {
        return content;
    }

    // Lockfile shielding
    if config.is_lockfile(p) {
        let shielded = process_lockfile(p, &content, query);
        let orig_tok = (content.len() / 4) as u64;
        let opt_tok = (shielded.len() / 4) as u64;
        tracker.record_savings("lockfile", orig_tok, opt_tok);
        return shielded;
    }

    // In-memory unified diff session cache
    let entry = cache.get(file_path, &content);

    if entry.status == CacheStatus::FirstRead {
        return entry.content;
    }

    let savings_msg = format_savings(&content, &entry.content);
    tracker.record_savings("cache", entry.original_tokens as u64, entry.optimized_tokens as u64);

    format!("{}\n\nToken savings: {savings_msg}", entry.content)
}

/// Returns formatted cache statistics.
pub fn cache_stats(cache: &SessionCache) -> String {
    cache.get_stats().summary()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_smart_reader_first_and_second_read() {
        let temp = tempfile::tempdir().unwrap();
        let file_path = temp.path().join("test.txt");
        std::fs::write(&file_path, "Hello world\n").unwrap();

        let cache = SessionCache::new();
        let config = TokenSaverConfig::default();
        let tracker = TelemetryTracker::new();

        let p_str = file_path.to_str().unwrap();

        // 1st read -> full content
        let r1 = read_file_smart(p_str, false, None, &cache, &config, &tracker);
        assert_eq!(r1, "Hello world\n");

        // 2nd read -> cached hit
        let r2 = read_file_smart(p_str, false, None, &cache, &config, &tracker);
        assert!(r2.contains("unchanged since last read"));
        assert!(r2.contains("Token savings:"));
    }
}
