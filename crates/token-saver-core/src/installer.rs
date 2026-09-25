//! Automatic 1-Click MCP Installer and Manager for AI Assistants in Rust.
//!
//! Automatically detects and configures Token-Saver MCP server in Claude Desktop,
//! Cursor, Windsurf, Claude Code, and VS Code (Cline / Roo Code).

use std::fs;
use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpInstallResult {
    pub ide_name: String,
    pub config_path: PathBuf,
    pub success: bool,
    pub message: String,
}

/// Returns list of supported AI assistant names and their standard MCP config file paths.
pub fn get_supported_ide_configs() -> Vec<(&'static str, PathBuf)> {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let mut configs = Vec::new();

    // 1. Claude Desktop
    #[cfg(target_os = "windows")]
    {
        if let Ok(appdata) = std::env::var("APPDATA") {
            configs.push(("Claude Desktop", PathBuf::from(appdata).join("Claude").join("claude_desktop_config.json")));
        } else {
            configs.push(("Claude Desktop", home.join("AppData").join("Roaming").join("Claude").join("claude_desktop_config.json")));
        }
    }
    #[cfg(target_os = "macos")]
    {
        configs.push(("Claude Desktop", home.join("Library").join("Application Support").join("Claude").join("claude_desktop_config.json")));
    }
    #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
    {
        configs.push(("Claude Desktop", home.join(".config").join("Claude").join("claude_desktop_config.json")));
    }

    // 2. Cursor
    configs.push(("Cursor", home.join(".cursor").join("mcp.json")));

    // 3. Windsurf
    configs.push(("Windsurf", home.join(".codeium").join("windsurf").join("mcp_config.json")));

    // 4. Claude Code
    configs.push(("Claude Code", home.join(".claude.json")));

    // 5. Antigravity (AGY)
    configs.push(("Antigravity (AGY)", home.join(".gemini").join("config").join("mcp_config.json")));

    // 6. VS Code (Cline / Roo Code)
    #[cfg(target_os = "windows")]
    if let Ok(appdata) = std::env::var("APPDATA") {
        let code_storage = PathBuf::from(appdata).join("Code").join("User").join("globalStorage");
        configs.push(("VS Code (Cline)", code_storage.join("saoudrizwan.claude-dev").join("settings").join("cline_mcp_settings.json")));
        configs.push(("VS Code (Roo)", code_storage.join("rooveterinaryinc.roo-cline").join("settings").join("cline_mcp_settings.json")));
    }
    #[cfg(target_os = "macos")]
    {
        let code_storage = home.join("Library").join("Application Support").join("Code").join("User").join("globalStorage");
        configs.push(("VS Code (Cline)", code_storage.join("saoudrizwan.claude-dev").join("settings").join("cline_mcp_settings.json")));
        configs.push(("VS Code (Roo)", code_storage.join("rooveterinaryinc.roo-cline").join("settings").join("cline_mcp_settings.json")));
    }
    #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
    {
        let code_storage = home.join(".config").join("Code").join("User").join("globalStorage");
        configs.push(("VS Code (Cline)", code_storage.join("saoudrizwan.claude-dev").join("settings").join("cline_mcp_settings.json")));
        configs.push(("VS Code (Roo)", code_storage.join("rooveterinaryinc.roo-cline").join("settings").join("cline_mcp_settings.json")));
    }

    configs
}

/// Checks if Claude Code CLI is genuinely installed on the host.
pub fn is_claude_code_installed() -> bool {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));

    // 1. Check if 'claude' CLI binary exists in PATH
    #[cfg(target_os = "windows")]
    let check_cmds = ["claude.cmd", "claude.exe", "claude.bat"];
    #[cfg(not(target_os = "windows"))]
    let check_cmds = ["claude"];

    if let Ok(path_var) = std::env::var("PATH") {
        for dir in std::env::split_paths(&path_var) {
            for cmd in &check_cmds {
                if dir.join(cmd).is_file() {
                    return true;
                }
            }
        }
    }

    // 2. Check if ~/.claude directory exists with actual files other than our own commands
    let claude_dir = home.join(".claude");
    if claude_dir.is_dir() {
        if let Ok(entries) = fs::read_dir(&claude_dir) {
            for entry in entries.flatten() {
                if entry.file_name() != "commands" {
                    return true;
                }
            }
        }
    }

    // 3. Check if ~/.claude.json exists and has configuration other than token-saver
    let cfg = home.join(".claude.json");
    if cfg.is_file() {
        if let Ok(content) = fs::read_to_string(&cfg) {
            if let Ok(val) = serde_json::from_str::<Value>(&content) {
                if let Some(obj) = val.as_object() {
                    if obj.keys().any(|k| k != "mcpServers") {
                        return true;
                    }
                    if let Some(servers) = obj.get("mcpServers").and_then(|s| s.as_object()) {
                        if servers.keys().any(|k| k != "token-saver") {
                            return true;
                        }
                    }
                }
            }
        }
    }

    false
}

/// Automatically configures Token-Saver MCP in detected or all AI assistants.
pub fn install_mcp_all(all_ides: bool, custom_exe: Option<&str>) -> Vec<McpInstallResult> {
    let exe_path = match custom_exe {
        Some(e) => e.to_string(),
        None => std::env::current_exe()
            .unwrap_or_else(|_| PathBuf::from("token-saver.exe"))
            .to_string_lossy()
            .to_string(),
    };

    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let configs = get_supported_ide_configs();
    let mut results = Vec::new();

    for (ide_name, cfg_path) in configs {
        let file_exists = cfg_path.exists();
        let is_detected = if ide_name == "Claude Code" {
            is_claude_code_installed()
        } else {
            let parent_exists = cfg_path.parent().map(|p| p.exists() && p != &home).unwrap_or(false);
            parent_exists || file_exists
        };

        // If not all_ides, only configure if IDE directory or config file exists on host
        if !all_ides && !is_detected {
            results.push(McpInstallResult {
                ide_name: ide_name.to_string(),
                config_path: cfg_path,
                success: false,
                message: "Skipped (IDE not detected on system)".to_string(),
            });
            continue;
        }

        // Ensure parent directory exists
        if let Some(parent) = cfg_path.parent() {
            let _ = fs::create_dir_all(parent);
        }

        // Read or initialize JSON
        let mut json_data = if file_exists {
            match fs::read_to_string(&cfg_path) {
                Ok(content) => serde_json::from_str::<Value>(&content).unwrap_or_else(|_| json!({})),
                Err(_) => json!({}),
            }
        } else {
            json!({})
        };

        if !json_data.is_object() {
            json_data = json!({});
        }

        // Ensure mcpServers exists
        if json_data.get("mcpServers").is_none() || !json_data["mcpServers"].is_object() {
            json_data["mcpServers"] = json!({});
        }

        // Insert or update token-saver configuration
        json_data["mcpServers"]["token-saver"] = json!({
            "command": exe_path
        });

        match serde_json::to_string_pretty(&json_data) {
            Ok(formatted) => match fs::write(&cfg_path, formatted) {
                Ok(_) => {
                    results.push(McpInstallResult {
                        ide_name: ide_name.to_string(),
                        config_path: cfg_path,
                        success: true,
                        message: format!("Successfully configured in {}", ide_name),
                    });
                }
                Err(e) => {
                    results.push(McpInstallResult {
                        ide_name: ide_name.to_string(),
                        config_path: cfg_path,
                        success: false,
                        message: format!("Failed writing file: {e}"),
                    });
                }
            },
            Err(e) => {
                results.push(McpInstallResult {
                    ide_name: ide_name.to_string(),
                    config_path: cfg_path,
                    success: false,
                    message: format!("Failed serializing config: {e}"),
                });
            }
        }
    }

    // Auto-install /token-saver slash commands into AGY CLI and Claude Code
    let _ = install_all_slash_commands(true);

    results
}

/// Safely removes Token-Saver from all AI assistant MCP configurations.
pub fn uninstall_mcp_all() -> Vec<McpInstallResult> {
    let configs = get_supported_ide_configs();
    let mut results = Vec::new();

    for (ide_name, cfg_path) in configs {
        if !cfg_path.exists() {
            results.push(McpInstallResult {
                ide_name: ide_name.to_string(),
                config_path: cfg_path,
                success: true,
                message: "Already inactive (config not present)".to_string(),
            });
            continue;
        }

        let content = match fs::read_to_string(&cfg_path) {
            Ok(c) => c,
            Err(e) => {
                results.push(McpInstallResult {
                    ide_name: ide_name.to_string(),
                    config_path: cfg_path,
                    success: false,
                    message: format!("Failed reading config: {e}"),
                });
                continue;
            }
        };

        let mut json_data: Value = match serde_json::from_str(&content) {
            Ok(v) => v,
            Err(e) => {
                results.push(McpInstallResult {
                    ide_name: ide_name.to_string(),
                    config_path: cfg_path,
                    success: false,
                    message: format!("Invalid JSON in config: {e}"),
                });
                continue;
            }
        };

        let mut modified = false;
        if let Some(servers) = json_data.get_mut("mcpServers").and_then(|s| s.as_object_mut()) {
            if servers.remove("token-saver").is_some() {
                modified = true;
            }
        }

        if modified {
            match serde_json::to_string_pretty(&json_data) {
                Ok(formatted) => match fs::write(&cfg_path, formatted) {
                    Ok(_) => {
                        results.push(McpInstallResult {
                            ide_name: ide_name.to_string(),
                            config_path: cfg_path,
                            success: true,
                            message: format!("Deactivated token-saver from {ide_name}"),
                        });
                    }
                    Err(e) => {
                        results.push(McpInstallResult {
                            ide_name: ide_name.to_string(),
                            config_path: cfg_path,
                            success: false,
                            message: format!("Failed saving config: {e}"),
                        });
                    }
                },
                Err(e) => {
                    results.push(McpInstallResult {
                        ide_name: ide_name.to_string(),
                        config_path: cfg_path,
                        success: false,
                        message: format!("Failed serializing config: {e}"),
                    });
                }
            }
        } else {
            results.push(McpInstallResult {
                ide_name: ide_name.to_string(),
                config_path: cfg_path,
                success: true,
                message: format!("Token-Saver was already inactive in {ide_name}"),
            });
        }
    }

    results
}

pub fn install_agy_slash_command() -> (bool, String) {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let skill_dir = home.join(".gemini").join("config").join("skills").join("token-saver");
    if let Err(e) = fs::create_dir_all(&skill_dir) {
        return (false, format!("Failed creating directory: {e}"));
    }
    let skill_file = skill_dir.join("SKILL.md");
    let content = r#"---
name: token-saver
description: >-
  Instant slash command controller for the Token-Saver token optimization engine.
  Use immediately when user types /token-saver, /token-saver on, /token-saver off,
  /token-saver output on, /token-saver output off, /token-saver stats, or requests to toggle token-saver state.
---

# Token-Saver Slash Command Controller

When this command is invoked with an argument:

1. **If argument is 'on' or 'enable':**
   Execute shell command: `token-saver on`
   Report confirmation that Token-Saver is active.

2. **If argument is 'off' or 'disable':**
   Execute shell command: `token-saver off`
   Report confirmation that Token-Saver is deactivated.

3. **If argument starts with 'output':**
   Execute shell command: `token-saver output <arg>` (e.g. `token-saver output on` or `token-saver output off`)
   Report confirmation of the output mode change.

4. **If argument is 'status':**
   Execute shell command: `token-saver status`
   Display the overall operational status report.

5. **If argument is 'stats' or 'telemetry':**
   Execute shell command: `token-saver stats`
   Display the savings dashboard.

6. **If no argument or 'help':**
   Show options: `/token-saver status`, `/token-saver on`, `/token-saver off`, `/token-saver output on`, `/token-saver output off`, `/token-saver stats`.
"#;
    match fs::write(&skill_file, content) {
        Ok(_) => (true, format!("Installed /token-saver command for AGY CLI at {:?}", skill_file)),
        Err(e) => (false, format!("Failed writing skill file: {e}")),
    }
}

pub fn install_claude_code_slash_command() -> (bool, String) {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let claude_dir = home.join(".claude").join("commands");
    if let Err(e) = fs::create_dir_all(&claude_dir) {
        return (false, format!("Failed creating directory: {e}"));
    }
    let command_file = claude_dir.join("token-saver.md");
    let content = r#"---
description: Manage Token-Saver token optimization engine (on, off, output on/off, stats)
---

Execute the requested Token-Saver operation:
$ARGUMENTS

Instructions:
1. If argument is "on" or "enable", run `token-saver on` and confirm activation.
2. If argument is "off" or "disable", run `token-saver off` and confirm deactivation.
3. If argument starts with "output", run `token-saver output <args>` and report status.
4. If argument is "stats", run `token-saver stats` and show the telemetry dashboard.
5. If empty or help, show usage instructions.
"#;
    match fs::write(&command_file, content) {
        Ok(_) => (true, format!("Installed /token-saver command for Claude Code at {:?}", command_file)),
        Err(e) => (false, format!("Failed writing command file: {e}")),
    }
}

pub fn install_all_slash_commands(only_installed: bool) -> Vec<(&'static str, bool, String)> {
    let mut results = Vec::new();
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));

    let agy_config = home.join(".gemini").join("config").join("mcp_config.json");
    if !only_installed || agy_config.exists() {
        let (ok, msg) = install_agy_slash_command();
        results.push(("Antigravity (AGY)", ok, msg));
    }

    if !only_installed || is_claude_code_installed() {
        let (ok, msg) = install_claude_code_slash_command();
        results.push(("Claude Code", ok, msg));
    } else {
        results.push(("Claude Code", false, "Not installed (skipped)".to_string()));
    }

    results
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ide_configs_not_empty() {
        let configs = get_supported_ide_configs();
        assert!(!configs.is_empty());
        assert!(configs.iter().any(|(name, _)| *name == "Cursor"));
    }
}
