use serde::{Deserialize, Serialize};
use std::path::Path;

pub const DEFAULT_IGNORE_PATTERNS: &[&str] = &[
    "*.env*",
    "*.pem",
    "*.key",
    "secrets/*",
    "*credentials*",
    "*id_rsa*",
    "*.pfx",
    "*.p12",
];

pub const DEFAULT_LOCKFILE_PATTERNS: &[&str] = &[
    "*package-lock.json",
    "*npm-shrinkwrap.json",
    "*yarn.lock",
    "*pnpm-lock.yaml",
    "*Cargo.lock",
    "*poetry.lock",
    "*Pipfile.lock",
    "*pdm.lock",
    "*composer.lock",
    "*Gemfile.lock",
    "*go.sum",
    "*.min.js",
    "*.min.css",
    "*.map",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenSaverConfig {
    #[serde(default = "default_ignore_patterns")]
    pub ignore_patterns: Vec<String>,

    #[serde(default = "default_lockfile_patterns")]
    pub lockfile_patterns: Vec<String>,

    #[serde(default = "default_true")]
    pub lockfile_shield: bool,

    #[serde(default = "default_max_bytes")]
    pub max_cacheable_bytes: usize,

    #[serde(default = "default_ttl")]
    pub cache_ttl_days: u32,

    #[serde(default = "default_max_entries")]
    pub max_cache_entries: usize,

    #[serde(default = "default_repo_budget")]
    pub repo_map_budget: usize,

    #[serde(default = "default_true")]
    pub compact_output: bool,

    #[serde(default = "default_true")]
    pub prevent_truncation: bool,

    #[serde(default = "default_max_source_files")]
    pub max_source_files: usize,
}

fn default_ignore_patterns() -> Vec<String> {
    DEFAULT_IGNORE_PATTERNS
        .iter()
        .map(|s| s.to_string())
        .collect()
}

fn default_lockfile_patterns() -> Vec<String> {
    DEFAULT_LOCKFILE_PATTERNS
        .iter()
        .map(|s| s.to_string())
        .collect()
}

fn default_true() -> bool {
    true
}

fn default_max_bytes() -> usize {
    5 * 1024 * 1024 // 5 MB
}

fn default_ttl() -> u32 {
    30
}

fn default_max_entries() -> usize {
    5000
}

fn default_repo_budget() -> usize {
    1000
}

fn default_max_source_files() -> usize {
    5000
}

impl Default for TokenSaverConfig {
    fn default() -> Self {
        Self {
            ignore_patterns: default_ignore_patterns(),
            lockfile_patterns: default_lockfile_patterns(),
            lockfile_shield: true,
            max_cacheable_bytes: default_max_bytes(),
            cache_ttl_days: default_ttl(),
            max_cache_entries: default_max_entries(),
            repo_map_budget: default_repo_budget(),
            compact_output: true,
            prevent_truncation: true,
            max_source_files: default_max_source_files(),
        }
    }
}

impl TokenSaverConfig {
    pub fn is_ignored(&self, file_path: &Path) -> bool {
        let p_str = file_path.to_string_lossy().replace('\\', "/");
        let file_name = file_path.file_name().and_then(|n| n.to_str()).unwrap_or("");

        for pattern in &self.ignore_patterns {
            let pat = pattern.replace('\\', "/");
            if glob_match(&pat, &p_str) || glob_match(&pat, file_name) {
                return true;
            }
        }
        false
    }

    pub fn is_lockfile(&self, file_path: &Path) -> bool {
        if !self.lockfile_shield {
            return false;
        }
        let p_str = file_path.to_string_lossy().replace('\\', "/");
        let file_name = file_path.file_name().and_then(|n| n.to_str()).unwrap_or("");

        for pattern in &self.lockfile_patterns {
            let pat = pattern.replace('\\', "/");
            if glob_match(&pat, &p_str) || glob_match(&pat, file_name) {
                return true;
            }
        }
        false
    }

    pub fn load_from_dir<P: AsRef<Path>>(root: P) -> Self {
        let root = root.as_ref();
        let candidates = [
            root.join("token-saver.toml"),
            root.join(".token-saver.toml"),
        ];

        for cand in &candidates {
            if cand.is_file() {
                if let Ok(text) = std::fs::read_to_string(cand) {
                    if let Ok(cfg) = toml::from_str::<TokenSaverConfig>(&text) {
                        return cfg;
                    }
                }
            }
        }

        let json_cand = root.join(".tokensaverrc");
        if json_cand.is_file() {
            if let Ok(text) = std::fs::read_to_string(json_cand) {
                if let Ok(cfg) = serde_json::from_str::<TokenSaverConfig>(&text) {
                    return cfg;
                }
            }
        }

        Self::default()
    }
}

/// Simple wildcard glob matching (supporting * and ?).
fn glob_match(pattern: &str, text: &str) -> bool {
    let mut p_chars = pattern.chars();
    let mut t_chars = text.chars();

    let mut p_next = p_chars.next();
    let mut t_next = t_chars.next();

    let mut star_p: Option<std::str::Chars> = None;
    let mut star_t: Option<std::str::Chars> = None;

    while t_next.is_some() {
        if p_next == Some('?') || p_next == t_next {
            p_next = p_chars.next();
            t_next = t_chars.next();
        } else if p_next == Some('*') {
            star_p = Some(p_chars.clone());
            star_t = Some(t_chars.clone());
            p_next = p_chars.next();
        } else if let (Some(sp), Some(st)) = (&star_p, &star_t) {
            p_chars = sp.clone();
            p_next = p_chars.next();
            t_chars = st.clone();
            t_next = t_chars.next();
            star_t = Some(t_chars.clone());
        } else {
            return false;
        }
    }

    while p_next == Some('*') {
        p_next = p_chars.next();
    }

    p_next.is_none()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_glob_match() {
        assert!(glob_match("*.env*", ".env.local"));
        assert!(glob_match(
            "*package-lock.json",
            "/path/to/package-lock.json"
        ));
        assert!(!glob_match("*.env*", "main.rs"));
    }

    #[test]
    fn test_is_ignored() {
        let cfg = TokenSaverConfig::default();
        assert!(cfg.is_ignored(Path::new(".env")));
        assert!(cfg.is_ignored(Path::new("secret.key")));
        assert!(!cfg.is_ignored(Path::new("src/main.rs")));
    }
}
