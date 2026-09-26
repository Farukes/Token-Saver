from __future__ import annotations

from pathlib import Path

from tokenjar.rules.manager import RULES_MARKER_START, RulesManager


def test_rules_install_and_remove(tmp_path: Path):
    test_project = tmp_path / "my_project"
    test_project.mkdir()

    # Pre-create an existing .cursorrules with user content
    cursor_rules = test_project / ".cursorrules"
    cursor_rules.write_text("User custom rules line\n", encoding="utf-8")

    # 1. Install rules
    results = RulesManager.install_rules(test_project)
    assert len(results) == len(RulesManager.SUPPORTED_RULE_FILES)
    for _, ok, _ in results:
        assert ok

    # Check AGENTS.md was created
    agents_file = test_project / "AGENTS.md"
    assert agents_file.exists()
    assert RULES_MARKER_START in agents_file.read_text(encoding="utf-8")
    assert "read_file_smart" in agents_file.read_text(encoding="utf-8")

    # Check .cursorrules preserved existing content and added block
    cursor_content = cursor_rules.read_text(encoding="utf-8")
    assert "User custom rules line" in cursor_content
    assert RULES_MARKER_START in cursor_content

    # 2. Re-install should update idempotently
    results2 = RulesManager.install_rules(test_project)
    for _, ok, _ in results2:
        assert ok
    cursor_content2 = cursor_rules.read_text(encoding="utf-8")
    assert cursor_content2.count(RULES_MARKER_START) == 1

    # 3. Remove rules
    del_results = RulesManager.remove_rules(test_project)
    for _, ok, _ in del_results:
        assert ok

    # .cursorrules should have user content restored without marker
    cursor_after = cursor_rules.read_text(encoding="utf-8")
    assert "User custom rules line" in cursor_after
    assert RULES_MARKER_START not in cursor_after

    # AGENTS.md was only rules, so it should be unlinked
    assert not agents_file.exists()


def test_rules_compact_toggle(tmp_path: Path):
    test_project = tmp_path / "project_toggle"
    test_project.mkdir()

    # Install with compact output disabled
    RulesManager.install_rules(test_project, compact_output=False)
    agents_file = test_project / "AGENTS.md"
    content_no_compact = agents_file.read_text(encoding="utf-8")
    assert "Output Optimization" not in content_no_compact
    assert "ZERO TRUNCATION MANDATE" not in content_no_compact

    # Re-install with compact output enabled
    RulesManager.install_rules(test_project, compact_output=True, prevent_truncation=True)
    content_compact = agents_file.read_text(encoding="utf-8")
    assert "Output Optimization" in content_compact
    assert "ZERO TRUNCATION MANDATE" in content_compact
    assert "Surgical File Edits" in content_compact


def test_rules_respects_toml_config(tmp_path: Path):
    test_project = tmp_path / "project_toml"
    test_project.mkdir()

    # Place tokenjar.toml with compact_mode = false
    toml_file = test_project / "tokenjar.toml"
    toml_file.write_text("[output]\ncompact_mode = false\n", encoding="utf-8")

    # Install without explicit parameter -> should read toml
    RulesManager.install_rules(test_project)
    agents_file = test_project / "AGENTS.md"
    content = agents_file.read_text(encoding="utf-8")
    assert "Output Optimization" not in content


def test_rules_set_output_mode_toggle(tmp_path: Path):
    test_project = tmp_path / "project_set_output"
    test_project.mkdir()

    # 1. Turn output mode OFF (default output)
    ok, msg, files = RulesManager.set_output_mode(test_project, enabled=False)
    assert ok
    assert "tokenjar.toml" in files
    assert "AGENTS.md" in files
    assert RulesManager.get_output_mode(test_project) is False

    agents_file = test_project / "AGENTS.md"
    assert "Output Optimization" not in agents_file.read_text(encoding="utf-8")
    toml_file = test_project / "tokenjar.toml"
    assert "compact_mode = false" in toml_file.read_text(encoding="utf-8")

    # 2. Turn output mode ON (compact mode)
    ok2, msg2, files2 = RulesManager.set_output_mode(test_project, enabled=True)
    assert ok2
    assert RulesManager.get_output_mode(test_project) is True
    assert "Output Optimization" in agents_file.read_text(encoding="utf-8")
    assert "ZERO TRUNCATION MANDATE" in agents_file.read_text(encoding="utf-8")
    assert "compact_mode = true" in toml_file.read_text(encoding="utf-8")
