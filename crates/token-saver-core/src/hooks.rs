//! Transparent Shell Hooking Manager for Token-Saver in Rust.
//!
//! Provides non-intrusive, transparent interception for terminal commands
//! across PowerShell, Bash, and Zsh.
//! Safely installs (hook) and cleanly uninstalls (unhook).

use std::fs;
use std::path::PathBuf;

pub const HOOK_MARKER_START: &str = "# >>> token-saver-hook >>>";
pub const HOOK_MARKER_END: &str = "# <<< token-saver-hook <<<";

pub const DEFAULT_WRAPPED_COMMANDS: &[&str] = &["pytest", "jest", "vitest", "npm", "cargo"];

#[derive(Debug, Clone)]
pub struct HookResult {
    pub shell: String,
    pub profile_path: PathBuf,
    pub success: bool,
    pub message: String,
}

/// Generates PowerShell profile hook functions.
pub fn generate_powershell_hook() -> String {
    let mut script = vec![
        HOOK_MARKER_START.to_string(),
        "# Token-Saver Transparent CLI Interceptor (PowerShell)".to_string(),
    ];

    for cmd in DEFAULT_WRAPPED_COMMANDS {
        script.push(format!(
            "function {cmd} {{\n    if ($env:RAW -eq '1' -or $env:TOKEN_SAVER_BYPASS -eq '1') {{\n        & (Get-Command -CommandType Application {cmd} | Select-Object -First 1).Source @args\n    }} else {{\n        token-saver run -- {cmd} @args\n    }}\n}}"
        ));
    }

    script.push(HOOK_MARKER_END.to_string());
    script.join("\n")
}

/// Generates Bash/Zsh profile hook functions.
pub fn generate_posix_hook() -> String {
    let mut script = vec![
        HOOK_MARKER_START.to_string(),
        "# Token-Saver Transparent CLI Interceptor (Bash/Zsh)".to_string(),
    ];

    for cmd in DEFAULT_WRAPPED_COMMANDS {
        script.push(format!(
            "{cmd}() {{\n    if [ \"$RAW\" = \"1\" ] || [ \"$TOKEN_SAVER_BYPASS\" = \"1\" ]; then\n        command {cmd} \"$@\"\n    else\n        token-saver run -- {cmd} \"$@\"\n    fi\n}}"
        ));
    }

    script.push(HOOK_MARKER_END.to_string());
    script.join("\n")
}

/// Returns list of shell profile paths to target.
pub fn get_profile_paths() -> Vec<(String, PathBuf)> {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let mut profiles = Vec::new();

    #[cfg(target_os = "windows")]
    {
        // PowerShell 7+ and Windows PowerShell 5.1
        let docs = dirs::document_dir().unwrap_or_else(|| home.join("Documents"));
        profiles.push((
            "PowerShell Core".to_string(),
            docs.join("PowerShell")
                .join("Microsoft.PowerShell_profile.ps1"),
        ));
        profiles.push((
            "Windows PowerShell".to_string(),
            docs.join("WindowsPowerShell")
                .join("Microsoft.PowerShell_profile.ps1"),
        ));
    }

    #[cfg(not(target_os = "windows"))]
    {
        profiles.push(("Bash".to_string(), home.join(".bashrc")));
        profiles.push(("Zsh".to_string(), home.join(".zshrc")));
    }

    profiles
}

/// Installs transparent hooks into shell profiles.
pub fn install_hooks() -> Vec<HookResult> {
    let mut results = Vec::new();

    for (shell_name, path) in get_profile_paths() {
        let hook_code = if shell_name.contains("PowerShell") {
            generate_powershell_hook()
        } else {
            generate_posix_hook()
        };

        if let Some(parent) = path.parent() {
            let _ = fs::create_dir_all(parent);
        }

        let existing = fs::read_to_string(&path).unwrap_or_default();
        let updated = if existing.contains(HOOK_MARKER_START) && existing.contains(HOOK_MARKER_END)
        {
            let re = regex::Regex::new(&format!(
                r"(?s){}.*?{}",
                regex::escape(HOOK_MARKER_START),
                regex::escape(HOOK_MARKER_END)
            ))
            .unwrap();
            re.replace(&existing, hook_code.as_str()).to_string()
        } else if !existing.is_empty() {
            format!("{existing}\n\n{hook_code}\n")
        } else {
            format!("{hook_code}\n")
        };

        match fs::write(&path, updated) {
            Ok(_) => results.push(HookResult {
                shell: shell_name,
                profile_path: path,
                success: true,
                message: "Hook installed successfully.".to_string(),
            }),
            Err(e) => results.push(HookResult {
                shell: shell_name,
                profile_path: path,
                success: false,
                message: format!("Failed to write: {e}"),
            }),
        }
    }

    results
}

/// Uninstalls transparent hooks from shell profiles.
pub fn remove_hooks() -> Vec<HookResult> {
    let mut results = Vec::new();

    for (shell_name, path) in get_profile_paths() {
        if !path.exists() {
            continue;
        }

        let existing = match fs::read_to_string(&path) {
            Ok(c) => c,
            Err(e) => {
                results.push(HookResult {
                    shell: shell_name,
                    profile_path: path,
                    success: false,
                    message: format!("Failed to read: {e}"),
                });
                continue;
            }
        };

        if existing.contains(HOOK_MARKER_START) && existing.contains(HOOK_MARKER_END) {
            let re = regex::Regex::new(&format!(
                r"(?s)\n*{}.*?{}\n*",
                regex::escape(HOOK_MARKER_START),
                regex::escape(HOOK_MARKER_END)
            ))
            .unwrap();
            let cleaned = re.replace(&existing, "\n").trim_matches('\n').to_string();
            let _ = fs::write(&path, format!("{cleaned}\n"));

            results.push(HookResult {
                shell: shell_name,
                profile_path: path,
                success: true,
                message: "Hook removed successfully.".to_string(),
            });
        }
    }

    results
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_powershell_hook() {
        let hook = generate_powershell_hook();
        assert!(hook.contains(HOOK_MARKER_START));
        assert!(hook.contains("function pytest"));
        assert!(hook.contains("token-saver run -- pytest"));
    }

    #[test]
    fn test_generate_posix_hook() {
        let hook = generate_posix_hook();
        assert!(hook.contains(HOOK_MARKER_START));
        assert!(hook.contains("pytest() {"));
        assert!(hook.contains("token-saver run -- pytest"));
    }
}
