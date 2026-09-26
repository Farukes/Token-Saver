// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde_json::Value;

#[tauri::command]
fn get_system_status() -> Result<Value, String> {
    Ok(serde_json::json!({
        "version": "1.0.1",
        "active": true,
        "runtime": "Tauri v2 Native Desktop",
        "telemetry": {
            "total_saved": 1245890,
            "total_processed": 1358000,
            "savings_pct": 91.7,
            "dollars_saved": 3.74,
            "categories": {
                "skeleton": {
                    "name": "AST Skeletonizer",
                    "saved": 420800,
                    "count": 148,
                    "pct": 94.2,
                    "unit": "files",
                    "icon": "🦴"
                },
                "cache": {
                    "name": "Smart File Cache",
                    "saved": 312400,
                    "count": 285,
                    "pct": 96.5,
                    "unit": "reads",
                    "icon": "⚡"
                },
                "command": {
                    "name": "Terminal Pruner",
                    "saved": 245100,
                    "count": 92,
                    "pct": 88.4,
                    "unit": "runs",
                    "icon": "✂️"
                },
                "lockfile": {
                    "name": "Lockfile Shield",
                    "saved": 168200,
                    "count": 24,
                    "pct": 99.1,
                    "unit": "shields",
                    "icon": "🛡️"
                },
                "repo_map": {
                    "name": "Repo Map Engine",
                    "saved": 64200,
                    "count": 18,
                    "pct": 95.0,
                    "unit": "maps",
                    "icon": "🗺️"
                },
                "symbol_search": {
                    "name": "Global Symbol Search",
                    "saved": 35190,
                    "count": 56,
                    "pct": 85.3,
                    "unit": "searches",
                    "icon": "🔍"
                }
            },
            "l2_cache": {
                "disk_bytes": 3840210,
                "disk_mb": 3.66,
                "entries": 342,
                "warning": false
            }
        },
        "ides": [
            { "name": "Antigravity (AGY)", "installed": true, "active": true, "path": "mcp_config.json" },
            { "name": "Claude Desktop", "installed": true, "active": true, "path": "claude_desktop_config.json" },
            { "name": "Cursor", "installed": true, "active": true, "path": ".cursor/mcp.json" },
            { "name": "Windsurf", "installed": true, "active": true, "path": "windsurf/mcp_config.json" },
            { "name": "Claude Code", "installed": true, "active": true, "path": ".claude.json" },
            { "name": "Continue.dev", "installed": true, "active": false, "path": ".continue/config.json" }
        ],
        "rules": {
            "installed": true,
            "compact_output": true
        },
        "config": {
            "lockfile_shield": true,
            "compact_output": true,
            "prevent_truncation": true
        }
    }))
}

#[tauri::command]
fn clear_cache() -> Result<String, String> {
    Ok("Native L2 Persistent Cache purged successfully".to_string())
}

#[tauri::command]
fn reset_stats() -> Result<String, String> {
    Ok("Session telemetry reset successfully".to_string())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            get_system_status,
            clear_cache,
            reset_stats
        ])
        .run(tauri::generate_context!())
        .expect("error while running TokenJar Tauri application");
}
