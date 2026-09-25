//! Output Pruner & Command Runner Engine in Rust.
//!
//! Intelligently filters command line outputs (pytest, cargo test, npm, jest)
//! and terminal logs to prevent token explosion.

use std::process::{Command, Stdio};

use crate::filters::ansi::strip_ansi;
use crate::filters::build_tools::{detect_and_filter_build, filter_npm_yarn};
use crate::filters::git::filter_git_output;
use crate::filters::test_runners::{filter_cargo, filter_pytest};
use crate::telemetry::TelemetryTracker;
use crate::token_counter::estimate_tokens;

const MAX_STREAM_BYTES: usize = 2 * 1024 * 1024; // 2MB
const STREAM_HEAD_BYTES: usize = 1024 * 1024;    // 1MB
const STREAM_TAIL_BYTES: usize = 512 * 1024;     // 512KB

/// Core output filtering logic.
pub fn filter_output_logic(
    raw_output: &str,
    output_type: &str,
    exit_code: i32,
    tracker: &TelemetryTracker,
) -> String {
    let mut clean_raw = raw_output.to_string();

    // Memory ceiling guard
    if clean_raw.len() > MAX_STREAM_BYTES {
        let truncated_count = clean_raw.len() - (STREAM_HEAD_BYTES + STREAM_TAIL_BYTES);
        let head = &clean_raw[..STREAM_HEAD_BYTES];
        let tail = &clean_raw[clean_raw.len() - STREAM_TAIL_BYTES..];
        clean_raw = format!(
            "{head}\n\n... [Token-Saver Stream Guard: Truncated {truncated_count} bytes of runaway output to protect memory] ...\n\n{tail}"
        );
    }

    let clean = strip_ansi(&clean_raw);

    let mut filtered = match output_type {
        "pytest" => filter_pytest(&clean),
        "cargo" => filter_cargo(&clean),
        "npm" | "yarn" | "pnpm" => filter_npm_yarn(&clean),
        "git" => filter_git_output(&clean),
        "generic" => clean.clone(),
        _ => {
            // Auto-detect
            if clean.contains("pytest") || clean.contains("=== test session starts ===") || clean.contains("passed in") {
                filter_pytest(&clean)
            } else if clean.contains("running ") && clean.contains("test result:") {
                filter_cargo(&clean)
            } else if let Some(b) = detect_and_filter_build(&clean) {
                b
            } else if clean.contains("git ") || clean.contains("On branch ") || clean.contains("Untracked files:") {
                filter_git_output(&clean)
            } else {
                clean.clone()
            }
        }
    };

    // Fallback safety guard: preserve full error context if exit_code != 0
    if exit_code != 0 {
        let error_keywords = [
            "traceback", "error", "failed", "exception", "fatal", "panic", "cannot",
            "syntaxerror", "importerror",
        ];
        let raw_lower = clean.to_lowercase();
        let filtered_lower = filtered.to_lowercase();
        let raw_has_error = error_keywords.iter().any(|&k| raw_lower.contains(k));
        let filtered_has_error = error_keywords.iter().any(|&k| filtered_lower.contains(k));

        if (raw_has_error && !filtered_has_error) || filtered.trim().is_empty() {
            filtered = format!(
                "{}\n[Token-Saver: Preserved full error context due to non-zero exit code]",
                clean.trim()
            );
        }
    }

    if filtered.trim().is_empty() && !clean.trim().is_empty() {
        filtered = clean.trim().to_string();
    }

    let orig_tokens = estimate_tokens(&clean_raw);
    let new_tokens = estimate_tokens(&filtered);
    let pct = if orig_tokens > 0 {
        ((orig_tokens.saturating_sub(new_tokens) as f64 / orig_tokens as f64) * 100.0) as usize
    } else {
        0
    };

    if orig_tokens > new_tokens {
        tracker.record_savings("command", orig_tokens as u64, new_tokens as u64);
    }

    format!("{filtered}\n[Token-Saver: {orig_tokens} -> {new_tokens} tokens ({pct}% saved)]")
}

/// Runs a command via the system shell with intelligent token filtering.
pub fn run_command_smart(
    command_str: &str,
    cwd: &str,
    _timeout_secs: u64,
    background: bool,
    tracker: &TelemetryTracker,
) -> String {
    if background {
        #[cfg(target_os = "windows")]
        let mut cmd = Command::new("cmd");
        #[cfg(target_os = "windows")]
        cmd.args(["/C", command_str]);

        #[cfg(not(target_os = "windows"))]
        let mut cmd = Command::new("sh");
        #[cfg(not(target_os = "windows"))]
        cmd.args(["-c", command_str]);

        cmd.current_dir(cwd)
            .stdout(Stdio::null())
            .stderr(Stdio::null());

        match cmd.spawn() {
            Ok(child) => format!("[BACKGROUND PROCESS LAUNCHED] PID: {} | Command: {command_str}", child.id()),
            Err(e) => format!("Error launching background command: {e}"),
        }
    } else {
        #[cfg(target_os = "windows")]
        let mut cmd = Command::new("cmd");
        #[cfg(target_os = "windows")]
        cmd.args(["/C", command_str]);

        #[cfg(not(target_os = "windows"))]
        let mut cmd = Command::new("sh");
        #[cfg(not(target_os = "windows"))]
        cmd.args(["-c", command_str]);

        cmd.current_dir(cwd);

        match cmd.output() {
            Ok(out) => {
                let stdout_str = String::from_utf8_lossy(&out.stdout).to_string();
                let stderr_str = String::from_utf8_lossy(&out.stderr).to_string();
                let combined = if stderr_str.is_empty() {
                    stdout_str
                } else if stdout_str.is_empty() {
                    stderr_str
                } else {
                    format!("{stdout_str}\n{stderr_str}")
                };

                let exit_code = out.status.code().unwrap_or(-1);
                let filtered = filter_output_logic(&combined, "auto", exit_code, tracker);
                format!("Exit Code: {exit_code}\n{filtered}")
            }
            Err(e) => format!("Error executing command: {e}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_filter_output_logic_cargo() {
        let raw = r#"
   Compiling token-saver v0.8.0
    Finished test [unoptimized + debuginfo] target(s) in 0.12s
     Running unittests src/lib.rs

running 3 tests
test test_a ... ok
test test_b ... ok
test test_c ... ok

test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
"#;
        let tracker = TelemetryTracker::new();
        let result = filter_output_logic(raw, "cargo", 0, &tracker);
        assert!(result.contains("test result: ok"));
        assert!(result.contains("Token-Saver:"));
    }
}
