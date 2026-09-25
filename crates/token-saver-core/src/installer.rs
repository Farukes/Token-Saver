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

/// Automatically configures Token-Saver MCP in detected or all AI assistants.
pub fn install_mcp_all(all_ides: bool, custom_exe: Option<&str>) -> Vec<McpInstallResult> {
    let exe_path = match custom_exe {
        Some(e) => e.to_string(),
        None => std::env::current_exe()
            .unwrap_or_else(|_| PathBuf::from("token-saver.exe"))
            .to_string_lossy()
            .to_string(),
    };

    let configs = get_supported_ide_configs();
    let mut results = Vec::new();

    for (ide_name, cfg_path) in configs {
        let parent_exists = cfg_path.parent().map(|p| p.exists()).unwrap_or(false);
        let file_exists = cfg_path.exists();

        // If not all_ides, only configure if IDE directory or config file exists on host
        if !all_ides && !parent_exists && !file_exists {
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
