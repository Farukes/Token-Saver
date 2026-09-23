"""Agent steering rules manager for Token-Saver.

Generates and injects non-intrusive instructions into AGENTS.md, .cursorrules,
.windsurfrules, and CLAUDE.md to guarantee AI models actively prioritize
Token-Saver MCP tools over native, unoptimized tools.
"""

from __future__ import annotations

import re
from pathlib import Path

RULES_MARKER_START = "# >>> token-saver-rules >>>"
RULES_MARKER_END = "# <<< token-saver-rules <<<"


def generate_rules(compact_output: bool = True, prevent_truncation: bool = True) -> str:
    """Generate non-intrusive agent steering instructions with optional output optimization."""
    lines = [
        RULES_MARKER_START,
        "## 🔋 Token-Saver AI Optimization Guidelines (STRICT ENFORCEMENT)",
        "CRITICAL MANDATE: Do NOT use native file viewers (view_file, cat) or raw terminal commands when Token-Saver MCP tools are available. Bypassing Token-Saver wastes hundreds of thousands of tokens and triggers conversation context window compaction.",
        "",
        "1. **File Reading & Inspections (MANDATORY):**",
        "   - ALWAYS use `read_file_smart` instead of native file viewers. It caches file contents and returns compact diffs on edits.",
        "2. **Codebase Exploration & Symbol Search (MANDATORY):**",
        "   - ALWAYS use `find_symbol_global` to locate functions, classes, or methods instantly across the codebase.",
        "   - ALWAYS use `tool_get_code_skeleton` to inspect classes, signatures, and docstrings before reading full file implementations.",
        "   - ALWAYS use `get_repo_map_tool` to explore repository architecture instead of listing and reading multiple files.",
        "3. **Terminal & Test Execution (MANDATORY):**",
        "   - Use `run_command_smart` or `filter_output` for test runners (`pytest`, `npm test`, `cargo test`, `jest`) to prune repetitive passing logs.",
    ]
    if compact_output:
        lines.extend([
            "4. **Output Optimization & Code Quality Mandate (STRICT):**",
            "   - Surgical File Edits: When modifying code, use surgical replacement blocks targeting precise line ranges instead of rewriting entire unchanged files.",
        ])
        if prevent_truncation:
            lines.append(
                "   - ZERO TRUNCATION MANDATE (Anti-Lazy Coder): NEVER use placeholder comments (e.g. '// ... rest of code unchanged ...' or 'TODO: keep existing logic') or omit required logic. Every generated or replaced code block must be complete, functional, and syntactically valid."
            )
        lines.append(
            "   - High-Density Rationale: Omit conversational pleasantries, introductory filler, and restating line-by-line code changes. Prioritize direct, rigorous technical justification, architectural context, and concrete solutions."
        )
    lines.append(RULES_MARKER_END)
    return "\n".join(lines)


TOKEN_SAVER_AGENT_RULES = generate_rules(compact_output=True, prevent_truncation=True)


class RulesManager:
    """Manages injection and removal of agent steering rules across projects."""

    RULES_CONTENT = TOKEN_SAVER_AGENT_RULES

    SUPPORTED_RULE_FILES = [
        "AGENTS.md",
        ".cursorrules",
        ".windsurfrules",
        "CLAUDE.md",
    ]

    @classmethod
    def install_rules(
        cls,
        target_dir: Path | str = ".",
        compact_output: bool | None = None,
        prevent_truncation: bool | None = None,
    ) -> list[tuple[str, bool, str]]:
        """Install or update Token-Saver steering rules in the specified project directory."""
        results = []
        project_path = Path(target_dir).resolve()

        if compact_output is None or prevent_truncation is None:
            from token_saver.config import load_config

            cfg = load_config(project_path)
            if compact_output is None:
                compact_output = cfg.compact_output
            if prevent_truncation is None:
                prevent_truncation = cfg.prevent_truncation

        rules_to_inject = generate_rules(compact_output=compact_output, prevent_truncation=prevent_truncation)

        for filename in cls.SUPPORTED_RULE_FILES:
            file_path = project_path / filename
            try:
                if file_path.exists():
                    current_content = file_path.read_text(encoding="utf-8")
                    if RULES_MARKER_START in current_content:
                        # Update existing block
                        pattern = rf"{re.escape(RULES_MARKER_START)}.*?{re.escape(RULES_MARKER_END)}"
                        updated = re.sub(pattern, rules_to_inject.strip(), current_content, flags=re.DOTALL)
                        file_path.write_text(updated, encoding="utf-8")
                        results.append((filename, True, f"Updated existing rules in {file_path.name}"))
                    else:
                        updated = current_content.rstrip() + "\n\n" + rules_to_inject.strip() + "\n"
                        file_path.write_text(updated, encoding="utf-8")
                        results.append((filename, True, f"Appended rules to {file_path.name}"))
                else:
                    file_path.write_text(rules_to_inject.strip() + "\n", encoding="utf-8")
                    results.append((filename, True, f"Created {file_path.name} with rules"))
            except Exception as e:
                results.append((filename, False, f"Failed updating {filename}: {e}"))

        return results

    @classmethod
    def remove_rules(cls, target_dir: Path | str = ".") -> list[tuple[str, bool, str]]:
        """Safely remove Token-Saver steering rules from all project rule files."""
        results = []
        project_path = Path(target_dir).resolve()

        for filename in cls.SUPPORTED_RULE_FILES:
            file_path = project_path / filename
            if not file_path.exists():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                if RULES_MARKER_START in content:
                    pattern = rf"{re.escape(RULES_MARKER_START)}.*?{re.escape(RULES_MARKER_END)}\s*"
                    clean = re.sub(pattern, "", content, flags=re.DOTALL).strip()
                    if not clean:
                        file_path.unlink()
                        results.append((filename, True, f"Removed empty {file_path.name}"))
                    else:
                        file_path.write_text(clean + "\n", encoding="utf-8")
                        results.append((filename, True, f"Removed rules block from {file_path.name}"))
            except Exception as e:
                results.append((filename, False, f"Failed cleaning {filename}: {e}"))

        return results

    @classmethod
    def set_output_mode(
        cls,
        target_dir: Path | str = ".",
        enabled: bool = True,
    ) -> tuple[bool, str, list[str]]:
        """Configure output optimization mode in token-saver.toml and refresh rule files."""
        project_path = Path(target_dir).resolve()
        updated_files = []

        # 1. Update or create token-saver.toml
        toml_path = project_path / "token-saver.toml"
        val_str = "true" if enabled else "false"
        try:
            if toml_path.exists():
                content = toml_path.read_text(encoding="utf-8")
                if "[output]" in content:
                    if re.search(r"compact_mode\s*=", content):
                        new_content = re.sub(
                            r"(compact_mode\s*=\s*)(true|false)",
                            rf"\g<1>{val_str}",
                            content,
                            flags=re.IGNORECASE,
                        )
                    else:
                        new_content = re.sub(
                            r"(\[output\]\s*)",
                            rf"\1compact_mode = {val_str}\n",
                            content,
                            count=1,
                        )
                else:
                    new_content = (
                        content.rstrip()
                        + f"\n\n[output]\ncompact_mode = {val_str}\nprevent_truncation = true\n"
                    )
                toml_path.write_text(new_content, encoding="utf-8")
            else:
                new_content = (
                    "# Token-Saver Project Configuration\n"
                    f"[output]\ncompact_mode = {val_str}\nprevent_truncation = true\n"
                )
                toml_path.write_text(new_content, encoding="utf-8")
            updated_files.append("token-saver.toml")
        except Exception as e:
            return False, f"Failed updating token-saver.toml: {e}", updated_files

        # 2. Update agent steering rule files
        rule_results = cls.install_rules(
            project_path,
            compact_output=enabled,
            prevent_truncation=True,
        )
        for fname, ok, _ in rule_results:
            if ok:
                updated_files.append(fname)

        mode_name = "COMPACT (Optimized)" if enabled else "DEFAULT (Normal/Verbose)"
        msg = f"Output optimization set to {mode_name}."
        return True, msg, updated_files

    @classmethod
    def get_output_mode(cls, target_dir: Path | str = ".") -> bool:
        """Get the current output optimization state from project configuration."""
        from token_saver.config import load_config

        cfg = load_config(Path(target_dir).resolve())
        return cfg.compact_output
