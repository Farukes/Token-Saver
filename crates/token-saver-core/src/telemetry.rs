//! Multi-process persistent telemetry and savings tracker in Rust.
//!
//! Synchronizes with disk on mtime change to prevent clobbering resets across processes.

use std::fs::File;
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::SystemTime;
use chrono::Utc;
use crate::models::{CategoryStats, TelemetryData};

pub struct TelemetryTracker {
    file_path: PathBuf,
    last_mtime: Mutex<Option<SystemTime>>,
    last_size: Mutex<Option<u64>>,
    data: Mutex<TelemetryData>,
}

impl Default for TelemetryTracker {
    fn default() -> Self {
        Self::new()
    }
}

impl TelemetryTracker {
    pub fn new() -> Self {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        let dir = home.join(".token-saver");
        std::fs::create_dir_all(&dir).ok();
        let file_path = dir.join("telemetry.json");

        let tracker = Self {
            file_path,
            last_mtime: Mutex::new(None),
            last_size: Mutex::new(None),
            data: Mutex::new(TelemetryData::default()),
        };
        tracker.refresh_if_needed();
        tracker
    }

    pub fn with_path(file_path: PathBuf) -> Self {
        let tracker = Self {
            file_path,
            last_mtime: Mutex::new(None),
            last_size: Mutex::new(None),
            data: Mutex::new(TelemetryData::default()),
        };
        tracker.refresh_if_needed();
        tracker
    }

    fn refresh_if_needed(&self) {
        if !self.file_path.exists() {
            let mut data_lock = self.data.lock().unwrap();
            *data_lock = TelemetryData::default();
            *self.last_mtime.lock().unwrap() = None;
            *self.last_size.lock().unwrap() = None;
            return;
        }

        if let Ok(meta) = self.file_path.metadata() {
            let mtime = meta.modified().ok();
            let size = Some(meta.len());
            let mut last_mtime_lock = self.last_mtime.lock().unwrap();
            let mut last_size_lock = self.last_size.lock().unwrap();
            if mtime != *last_mtime_lock || size != *last_size_lock {
                if let Ok(text) = std::fs::read_to_string(&self.file_path) {
                    if let Ok(d) = serde_json::from_str::<TelemetryData>(&text) {
                        let mut data_lock = self.data.lock().unwrap();
                        *data_lock = d;
                        *last_mtime_lock = mtime;
                        *last_size_lock = size;
                    }
                }
            }
        }
    }

    fn save(&self, data: &TelemetryData) {
        let tmp_path = self.file_path.with_extension(format!("tmp.{}", std::process::id()));
        if let Ok(json_str) = serde_json::to_string_pretty(data) {
            if let Ok(mut f) = File::create(&tmp_path) {
                if f.write_all(json_str.as_bytes()).is_ok() {
                    let _ = std::fs::rename(&tmp_path, &self.file_path);
                    if let Ok(meta) = self.file_path.metadata() {
                        *self.last_mtime.lock().unwrap() = meta.modified().ok();
                        *self.last_size.lock().unwrap() = Some(meta.len());
                    }
                }
            }
        }
    }

    pub fn get_data(&self) -> TelemetryData {
        self.refresh_if_needed();
        self.data.lock().unwrap().clone()
    }

    pub fn record_savings(&self, category: &str, original_tokens: u64, optimized_tokens: u64) {
        if original_tokens == 0 {
            return;
        }

        self.refresh_if_needed();
        let mut data_lock = self.data.lock().unwrap();

        let saved = original_tokens.saturating_sub(optimized_tokens);
        data_lock.total_original_tokens += original_tokens;
        data_lock.total_optimized_tokens += optimized_tokens;
        data_lock.total_tokens_saved += saved;
        data_lock.last_used_at = Utc::now().to_rfc3339();

        let update_cat = |cat: &mut CategoryStats| {
            cat.original += original_tokens;
            cat.optimized += optimized_tokens;
            cat.saved += saved;
            cat.count += 1;
        };

        match category {
            "skeleton" => {
                data_lock.total_skeletons_generated += 1;
                update_cat(&mut data_lock.skeleton);
            }
            "cache" => {
                data_lock.total_files_cached += 1;
                update_cat(&mut data_lock.cache);
            }
            "repo_map" => {
                data_lock.total_repo_maps_generated += 1;
                update_cat(&mut data_lock.repo_map);
            }
            "command" => {
                data_lock.total_commands_filtered += 1;
                update_cat(&mut data_lock.command);
            }
            "symbol_search" => {
                update_cat(&mut data_lock.symbol_search);
            }
            "lockfile" => {
                update_cat(&mut data_lock.lockfile);
            }
            _ => {}
        }

        self.save(&data_lock);
    }

    pub fn reset(&self) {
        let mut data_lock = self.data.lock().unwrap();
        *data_lock = TelemetryData::default();
        self.save(&data_lock);
    }

    pub fn render_dashboard(&self) -> String {
        let d = self.get_data();
        let dollars = format!("${:.2}", d.estimated_dollars_saved());
        let pct = format!("%{:.1}", d.savings_pct());

        let fmt_cat = |name: &str, stat: &CategoryStats, unit: &str| -> String {
            format!(
                "│  • {:<22} {:>8} tokens saved ({:>5.1}%) │ {:>3} {:<8} │",
                name,
                stat.saved,
                stat.savings_pct(),
                stat.count,
                unit
            )
        };

        format!(
            "┌────────────────────────────────────────────────────────────────────────┐\n\
             │ 🔋 TOKEN-SAVER DETAILED PERFORMANCE & SAVINGS DASHBOARD (RUST)         │\n\
             ├────────────────────────────────────────────────────────────────────────┤\n\
             {}\n\
             {}\n\
             {}\n\
             {}\n\
             {}\n\
             {}\n\
             ├────────────────────────────────────────────────────────────────────────┤\n\
             │  TOTAL TOKENS SAVED:       {:<16} ({pct} optimized reduction)│\n\
             │  ESTIMATED MONEY SAVED:    {:<16} (at $3.00/1M blended rate) │\n\
             │  RAW CONTEXT PROCESSED:    {:<16} tokens total                  │\n\
             └────────────────────────────────────────────────────────────────────────┘",
            fmt_cat("AST Skeletonizer:", &d.skeleton, "files"),
            fmt_cat("Smart File Cache:", &d.cache, "reads"),
            fmt_cat("Lockfile Shield:", &d.lockfile, "shields"),
            fmt_cat("Repo Map Engine:", &d.repo_map, "maps"),
            fmt_cat("Global Symbol Search:", &d.symbol_search, "searches"),
            fmt_cat("Terminal Pruner:", &d.command, "runs"),
            d.total_tokens_saved,
            dollars,
            d.total_original_tokens,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_telemetry_tracker_cross_instance() {
        let temp = tempfile::NamedTempFile::new().unwrap();
        let tracker_a = TelemetryTracker::with_path(temp.path().to_path_buf());
        let tracker_b = TelemetryTracker::with_path(temp.path().to_path_buf());

        tracker_a.reset();
        tracker_a.record_savings("command", 1000, 200);
        assert_eq!(tracker_a.get_data().total_tokens_saved, 800);
        assert_eq!(tracker_b.get_data().total_tokens_saved, 800);

        tracker_b.reset();
        assert_eq!(tracker_b.get_data().total_tokens_saved, 0);

        std::thread::sleep(std::time::Duration::from_millis(25));

        // Tracker A records after reset: must NOT resurrect old 800 tokens
        tracker_a.record_savings("skeleton", 500, 100);
        assert_eq!(tracker_a.get_data().total_tokens_saved, 400);
        assert_eq!(tracker_b.get_data().total_tokens_saved, 400);
    }
}
