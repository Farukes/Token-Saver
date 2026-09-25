from __future__ import annotations

from token_saver.config import TokenSaverConfig, load_config
from token_saver.tools.smart_reader import read_file_smart


def test_default_config():
    config = TokenSaverConfig()
    assert config.max_cacheable_bytes == 5 * 1024 * 1024
    assert config.cache_ttl_days == 30
    assert config.is_ignored(".env")
    assert config.is_ignored("prod.env")
    assert config.is_ignored("secret.pem")
    assert config.is_ignored("id_rsa")
    assert not config.is_ignored("main.py")


def test_load_toml_config(tmp_path):
    config_file = tmp_path / "token-saver.toml"
    config_file.write_text(
        """
[general]
ignore_patterns = ["custom_secret/*", "*.bak"]
max_cacheable_bytes = 1048576

[cache]
ttl_days = 15
max_entries = 2000

[repo_map]
default_budget = 500
""",
        encoding="utf-8",
    )

    loaded = load_config(tmp_path)
    assert loaded.max_cacheable_bytes == 1048576
    assert loaded.cache_ttl_days == 15
    assert loaded.max_cache_entries == 2000
    assert loaded.repo_map_budget == 500
    assert loaded.is_ignored("custom_secret/file.txt")
    assert loaded.is_ignored("archive.bak")
    assert loaded.is_ignored(".env")  # Default security pattern preserved


def test_output_config(tmp_path):
    config_file = tmp_path / "token-saver.toml"
    config_file.write_text(
        """
[output]
compact_mode = false
prevent_truncation = false
""",
        encoding="utf-8",
    )
    loaded = load_config(tmp_path)
    assert loaded.compact_output is False
    assert loaded.prevent_truncation is False


def test_smart_reader_security_guard(tmp_path):
    secret_file = tmp_path / ".env.production"
    secret_file.write_text("API_KEY=sk_secret_12345\n", encoding="utf-8")

    # Reading sensitive file should return security warning by default
    result = read_file_smart(str(secret_file))
    assert "[TOKEN-SAVER SECURITY]" in result
    assert "matches security ignore patterns" in result

    # When force_full=True is passed, reading is permitted
    result_forced = read_file_smart(str(secret_file), force_full=True)
    assert "API_KEY=sk_secret_12345" in result_forced


def test_max_source_files_config(tmp_path):
    config_file = tmp_path / "token-saver.toml"
    config_file.write_text(
        """
[general]
max_source_files = 15000
""",
        encoding="utf-8",
    )
    loaded = load_config(tmp_path)
    assert loaded.max_source_files == 15000


def test_walk_source_files_respects_custom_limit(tmp_path):
    from token_saver.utils.file_utils import walk_source_files

    for i in range(10):
        (tmp_path / f"test_{i}.py").write_text("x = 1\n", encoding="utf-8")

    # Limit to 3 files
    files = walk_source_files(str(tmp_path), max_files=3)
    assert len(files) == 3

    # Limit via token-saver.toml
    (tmp_path / "token-saver.toml").write_text(
        """
[general]
max_source_files = 4
""",
        encoding="utf-8",
    )
    files_configured = walk_source_files(str(tmp_path))
    assert len(files_configured) == 4

