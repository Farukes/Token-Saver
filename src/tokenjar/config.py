"""Configuration manager for TokenJar.

Supports optional project-level configuration via tokenjar.toml,
.tokenjar.toml, or .tokenjarrc (JSON).
Provides pattern-based file ignoring (secrets, credentials, custom exclusions)
and configurable cache/repo-map limits.
"""

from __future__ import annotations

import fnmatch
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_IGNORE_PATTERNS = [
    "*.env*",
    "*.pem",
    "*.key",
    "secrets/*",
    "*credentials*",
    "*id_rsa*",
    "*.pfx",
    "*.p12",
]

DEFAULT_LOCKFILE_PATTERNS = [
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
]


@dataclass
class TokenJarConfig:
    """Project-level configuration settings."""

    ignore_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_PATTERNS))
    lockfile_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_LOCKFILE_PATTERNS))
    lockfile_shield: bool = True
    max_cacheable_bytes: int = 5 * 1024 * 1024  # 5 MB
    cache_ttl_days: int = 30
    max_cache_entries: int = 5000
    repo_map_budget: int = 1000
    compact_output: bool = True
    prevent_truncation: bool = True
    max_source_files: int = 5000

    def is_ignored(self, file_path: str | Path) -> bool:
        """Check whether a file path matches any ignore patterns."""
        p_str = str(file_path).replace("\\", "/")
        base_name = os.path.basename(p_str)

        for pattern in self.ignore_patterns:
            pat = pattern.replace("\\", "/")
            if fnmatch.fnmatch(p_str, pat) or fnmatch.fnmatch(base_name, pat):
                return True
            # Also check matching anywhere in path if pattern has wildcard or directory
            if "/" in pat and fnmatch.fnmatch(p_str, f"*/{pat.lstrip('/')}"):
                return True
        return False

    def is_lockfile(self, file_path: str | Path) -> bool:
        """Check whether a file path matches lockfile or giant asset patterns."""
        if not self.lockfile_shield:
            return False
        p_str = str(file_path).replace("\\", "/")
        base_name = os.path.basename(p_str)

        for pattern in self.lockfile_patterns:
            pat = pattern.replace("\\", "/")
            if fnmatch.fnmatch(p_str, pat) or fnmatch.fnmatch(base_name, pat):
                return True
            if "/" in pat and fnmatch.fnmatch(p_str, f"*/{pat.lstrip('/')}"):
                return True
        return False


def _parse_toml(content: str) -> dict:
    """Parse TOML string using tomllib or tomli if available."""
    try:
        import tomllib

        return tomllib.loads(content)
    except ImportError:
        try:
            import tomli

            return tomli.loads(content)
        except ImportError:
            return {}


def load_config(root_path: str | Path = ".") -> TokenJarConfig:
    """Load configuration from root directory, or return defaults."""
    root = Path(root_path).resolve()
    config = TokenJarConfig()

    toml_candidates = [root / "tokenjar.toml", root / ".tokenjar.toml"]
    for cand in toml_candidates:
        if cand.is_file():
            try:
                data = _parse_toml(cand.read_text(encoding="utf-8"))
                if data:
                    _apply_dict_config(config, data)
                    return config
            except Exception:
                pass

    json_cand = root / ".tokenjarrc"
    if json_cand.is_file():
        try:
            data = json.loads(json_cand.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _apply_dict_config(config, data)
                return config
        except Exception:
            pass

    return config


def _apply_dict_config(config: TokenJarConfig, data: dict) -> None:
    """Apply parsed dictionary values onto TokenJarConfig."""
    general = data.get("general", data)
    if "ignore_patterns" in general and isinstance(general["ignore_patterns"], list):
        custom = [str(x) for x in general["ignore_patterns"]]
        # Ensure default secret patterns are preserved
        config.ignore_patterns = list(dict.fromkeys(DEFAULT_IGNORE_PATTERNS + custom))

    if "max_cacheable_bytes" in general:
        try:
            config.max_cacheable_bytes = int(general["max_cacheable_bytes"])
        except (ValueError, TypeError):
            pass

    files_cfg = data.get("files", general)
    if "max_source_files" in files_cfg:
        try:
            config.max_source_files = int(files_cfg["max_source_files"])
        except (ValueError, TypeError):
            pass
    elif "max_files" in files_cfg:
        try:
            config.max_source_files = int(files_cfg["max_files"])
        except (ValueError, TypeError):
            pass

    cache_cfg = data.get("cache", data)
    if "ttl_days" in cache_cfg:
        try:
            config.cache_ttl_days = int(cache_cfg["ttl_days"])
        except (ValueError, TypeError):
            pass
    if "max_entries" in cache_cfg:
        try:
            config.max_cache_entries = int(cache_cfg["max_entries"])
        except (ValueError, TypeError):
            pass

    repo_cfg = data.get("repo_map", data)
    if "default_budget" in repo_cfg:
        try:
            config.repo_map_budget = int(repo_cfg["default_budget"])
        except (ValueError, TypeError):
            pass

    out_cfg = data.get("output", data)
    if "compact_mode" in out_cfg:
        config.compact_output = bool(out_cfg["compact_mode"])
    elif "compact_output" in out_cfg:
        config.compact_output = bool(out_cfg["compact_output"])
    if "prevent_truncation" in out_cfg:
        config.prevent_truncation = bool(out_cfg["prevent_truncation"])

    shield_cfg = data.get("lockfile", general)
    if "lockfile_shield" in shield_cfg:
        config.lockfile_shield = bool(shield_cfg["lockfile_shield"])
    elif "shield_enabled" in shield_cfg:
        config.lockfile_shield = bool(shield_cfg["shield_enabled"])
    if "lockfile_patterns" in shield_cfg and isinstance(shield_cfg["lockfile_patterns"], list):
        custom_lock = [str(x) for x in shield_cfg["lockfile_patterns"]]
        config.lockfile_patterns = list(dict.fromkeys(DEFAULT_LOCKFILE_PATTERNS + custom_lock))
