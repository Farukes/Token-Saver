"""Configuration manager for Token-Saver.

Supports optional project-level configuration via token-saver.toml,
.token-saver.toml, or .tokensaverrc (JSON).
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


@dataclass
class TokenSaverConfig:
    """Project-level configuration settings."""

    ignore_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_PATTERNS))
    max_cacheable_bytes: int = 5 * 1024 * 1024  # 5 MB
    cache_ttl_days: int = 30
    max_cache_entries: int = 5000
    repo_map_budget: int = 1000
    compact_output: bool = True
    prevent_truncation: bool = True

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


def load_config(root_path: str | Path = ".") -> TokenSaverConfig:
    """Load configuration from root directory, or return defaults."""
    root = Path(root_path).resolve()
    config = TokenSaverConfig()

    toml_candidates = [root / "token-saver.toml", root / ".token-saver.toml"]
    for cand in toml_candidates:
        if cand.is_file():
            try:
                data = _parse_toml(cand.read_text(encoding="utf-8"))
                if data:
                    _apply_dict_config(config, data)
                    return config
            except Exception:
                pass

    json_cand = root / ".tokensaverrc"
    if json_cand.is_file():
        try:
            data = json.loads(json_cand.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _apply_dict_config(config, data)
                return config
        except Exception:
            pass

    return config


def _apply_dict_config(config: TokenSaverConfig, data: dict) -> None:
    """Apply parsed dictionary values onto TokenSaverConfig."""
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
