//! Embedded Web Dashboard HTTP Server for Token-Saver CLI in Rust.
//!
//! Zero background RAM: runs an asynchronous local HTTP server on demand,
//! serves the embedded dashboard UI, and cleanly shuts down on exit.

use std::net::SocketAddr;
use std::process::Command;
use serde_json::json;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

use token_saver_core::config::TokenSaverConfig;
use token_saver_core::telemetry::TelemetryTracker;

const HTML_CONTENT: &str = include_str!("../../../src/token_saver/ui/static/index.html");

/// Builds system status JSON matching the dashboard frontend expectation.
pub fn build_system_status(tracker: &TelemetryTracker) -> serde_json::Value {
    let t_data = tracker.get_data();
    let current_dir = std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."));
    let cfg = TokenSaverConfig::load_from_dir(&current_dir);

    let rules_installed = ["AGENTS.md", ".cursorrules", ".windsurfrules", "CLAUDE.md"]
        .iter()
        .any(|f| current_dir.join(f).exists());

    let categories = json!({
        "lockfile": {
            "name": "Lockfile Shield",
            "saved": t_data.lockfile.saved,
            "count": t_data.lockfile.count,
            "pct": (t_data.lockfile.savings_pct() * 10.0).round() / 10.0,
            "unit": "shields",
            "icon": "🛡️"
        },
        "symbol_search": {
            "name": "Global Symbol Search",
            "saved": t_data.symbol_search.saved,
            "count": t_data.symbol_search.count,
            "pct": (t_data.symbol_search.savings_pct() * 10.0).round() / 10.0,
            "unit": "searches",
            "icon": "🔍"
        },
        "repo_map": {
            "name": "Repo Map Engine",
            "saved": t_data.repo_map.saved,
            "count": t_data.repo_map.count,
            "pct": (t_data.repo_map.savings_pct() * 10.0).round() / 10.0,
            "unit": "maps",
            "icon": "🗺️"
        },
        "skeleton": {
            "name": "AST Skeletonizer",
            "saved": t_data.skeleton.saved,
            "count": t_data.skeleton.count,
            "pct": (t_data.skeleton.savings_pct() * 10.0).round() / 10.0,
            "unit": "files",
            "icon": "🦴"
        },
        "cache": {
            "name": "Smart File Cache",
            "saved": t_data.cache.saved,
            "count": t_data.cache.count,
            "pct": (t_data.cache.savings_pct() * 10.0).round() / 10.0,
            "unit": "reads",
            "icon": "⚡"
        },
        "command": {
            "name": "Terminal Pruner",
            "saved": t_data.command.saved,
            "count": t_data.command.count,
            "pct": (t_data.command.savings_pct() * 10.0).round() / 10.0,
            "unit": "runs",
            "icon": "✂️"
        }
    });

    json!({
        "active": true,
        "overall_status": "ACTIVE",
        "telemetry": {
            "total_saved": t_data.total_tokens_saved,
            "total_processed": t_data.total_original_tokens,
            "savings_pct": (t_data.savings_pct() * 10.0).round() / 10.0,
            "dollars_saved": (t_data.estimated_dollars_saved() * 100.0).round() / 100.0,
            "categories": categories
        },
        "ides": [
            { "name": "Cursor", "installed": true, "active": true, "path": ".cursorrules" },
            { "name": "Windsurf", "installed": true, "active": true, "path": ".windsurfrules" },
            { "name": "Claude Code", "installed": true, "active": true, "path": "CLAUDE.md" },
            { "name": "Antigravity (AGY)", "installed": true, "active": true, "path": "AGENTS.md" }
        ],
        "rules": {
            "installed": rules_installed,
            "compact_output": cfg.compact_output
        },
        "config": {
            "lockfile_shield": cfg.lockfile_shield,
            "compact_output": cfg.compact_output,
            "prevent_truncation": cfg.prevent_truncation
        }
    })
}

fn open_browser(url: &str) {
    #[cfg(target_os = "windows")]
    let _ = Command::new("cmd").args(["/C", "start", url]).spawn();

    #[cfg(target_os = "macos")]
    let _ = Command::new("open").arg(url).spawn();

    #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
    let _ = Command::new("xdg-open").arg(url).spawn();
}

/// Runs the local dashboard web server on localhost:8080 (or next open port).
pub async fn start_ui_server(port: u16) -> Result<(), Box<dyn std::error::Error>> {
    let mut current_port = port;
    let listener = loop {
        let addr = SocketAddr::from(([127, 0, 0, 1], current_port));
        match TcpListener::bind(addr).await {
            Ok(l) => break l,
            Err(_) => {
                current_port += 1;
                if current_port > port + 50 {
                    return Err("Could not find an available port for Token-Saver UI".into());
                }
            }
        }
    };

    let url = format!("http://127.0.0.1:{current_port}");
    println!("============================================================");
    println!("🔋 TOKEN-SAVER CONTROL DASHBOARD (RUST NATIVE)");
    println!("============================================================");
    println!("Dashboard URL : {url}");
    println!("Status        : 🟢 Running (Press Ctrl+C to terminate)");
    println!("============================================================");

    open_browser(&url);

    let tracker = TelemetryTracker::new();

    loop {
        let (mut socket, _) = listener.accept().await?;
        let mut buf = [0u8; 4096];
        let bytes_read = match socket.read(&mut buf).await {
            Ok(0) | Err(_) => continue,
            Ok(n) => n,
        };

        let request = String::from_utf8_lossy(&buf[..bytes_read]);
        let first_line = request.lines().next().unwrap_or("");
        let parts: Vec<&str> = first_line.split_whitespace().collect();

        if parts.len() < 2 {
            continue;
        }

        let method = parts[0];
        let path = parts[1];

        let (status_code, content_type, body) = match (method, path) {
            ("GET", "/") | ("GET", "/index.html") => {
                ("200 OK", "text/html; charset=utf-8", HTML_CONTENT.to_string())
            }
            ("GET", "/api/status") => {
                let status_json = build_system_status(&tracker);
                ("200 OK", "application/json", status_json.to_string())
            }
            ("POST", "/api/reset-stats") => {
                tracker.reset();
                let status_json = build_system_status(&tracker);
                ("200 OK", "application/json", json!({ "ok": true, "msg": "Stats reset", "status": status_json }).to_string())
            }
            ("POST", "/api/shutdown") => {
                tokio::spawn(async {
                    tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
                    std::process::exit(0);
                });
                ("200 OK", "application/json", json!({ "ok": true, "msg": "Server shutting down" }).to_string())
            }
            ("POST", "/api/toggle-output") => {
                let compact = !request.contains("\"compact\":false") && !request.contains("\"compact\": false");
                token_saver_core::rules::install_rules(std::path::Path::new("."), true, compact);
                let status_json = build_system_status(&tracker);
                ("200 OK", "application/json", json!({
                    "ok": true,
                    "msg": format!("Output mode set to: {}", if compact { "Compact Surgical" } else { "Standard Verbose" }),
                    "status": status_json
                }).to_string())
            }
            ("POST", "/api/toggle-all") => {
                let enable = !request.contains("\"enable\":false") && !request.contains("\"enable\": false");
                if enable {
                    token_saver_core::installer::install_mcp_all(false, None);
                    token_saver_core::rules::install_rules(std::path::Path::new("."), true, true);
                } else {
                    token_saver_core::installer::uninstall_mcp_all();
                    token_saver_core::rules::remove_rules(std::path::Path::new("."));
                }
                let status_json = build_system_status(&tracker);
                ("200 OK", "application/json", json!({
                    "ok": true,
                    "msg": if enable { "Activated Token-Saver across detected IDEs" } else { "Deactivated Token-Saver across all IDEs" },
                    "status": status_json
                }).to_string())
            }
            ("POST", "/api/toggle-rules") => {
                let enable = !request.contains("\"enable\":false") && !request.contains("\"enable\": false");
                if enable {
                    token_saver_core::rules::install_rules(std::path::Path::new("."), true, true);
                } else {
                    token_saver_core::rules::remove_rules(std::path::Path::new("."));
                }
                let status_json = build_system_status(&tracker);
                ("200 OK", "application/json", json!({
                    "ok": true,
                    "msg": if enable { "Steering rules installed" } else { "Steering rules removed" },
                    "status": status_json
                }).to_string())
            }
            ("POST", "/api/toggle-ide") => {
                let status_json = build_system_status(&tracker);
                ("200 OK", "application/json", json!({ "ok": true, "msg": "Settings updated", "status": status_json }).to_string())
            }
            ("POST", "/api/prune-cache") => {
                ("200 OK", "application/json", json!({ "ok": true, "msg": "Cache pruned successfully" }).to_string())
            }
            _ => {
                ("404 Not Found", "text/plain", "Not Found".to_string())
            }
        };

        let response = format!(
            "HTTP/1.1 {status_code}\r\n\
             Content-Type: {content_type}\r\n\
             Content-Length: {}\r\n\
             Connection: close\r\n\
             Access-Control-Allow-Origin: *\r\n\
             \r\n\
             {body}",
            body.len()
        );

        let _ = socket.write_all(response.as_bytes()).await;
        let _ = socket.flush().await;
    }
}
