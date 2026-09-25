"""Lockfile and giant asset shield for Token-Saver.

Prevents context window compaction caused by accidental reads of massive
auto-generated files (package-lock.json, Cargo.lock, poetry.lock, yarn.lock, minified assets).
Provides surgical package queries, top-level dependency summaries, and zero-loss bypass.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from token_saver.utils.token_counter import estimate_tokens

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


def find_package_in_lockfile(base_name: str, content: str, query: str) -> str | None:
    """Surgically locate and extract a specific package or dependency entry."""
    q = query.strip()
    if not q:
        return None

    lower_name = base_name.lower()

    # 1. NPM / Node: package-lock.json, npm-shrinkwrap.json
    if "package-lock.json" in lower_name or "shrinkwrap" in lower_name:
        try:
            data = json.loads(content)
            # v2/v3: check "packages" dict
            packages = data.get("packages", {})
            if isinstance(packages, dict):
                # Try exact matches first
                candidates = [
                    f"node_modules/{q}",
                    f"node_modules/{q.lower()}",
                    q,
                    q.lower(),
                ]
                for cand in candidates:
                    if cand in packages:
                        return json.dumps({cand: packages[cand]}, indent=2)

                # Try partial match if no exact match
                matches = {}
                for k, v in packages.items():
                    if q.lower() in k.lower():
                        matches[k] = v
                        if len(matches) >= 3:
                            break
                if matches:
                    return json.dumps(matches, indent=2)

            # v1/v2: check "dependencies" dict
            deps = data.get("dependencies", {})
            if isinstance(deps, dict):
                for k, v in deps.items():
                    if k.lower() == q.lower():
                        return json.dumps({k: v}, indent=2)
                    if q.lower() in k.lower():
                        return json.dumps({k: v}, indent=2)
        except Exception:
            pass

    # 2. Rust: Cargo.lock or Python: poetry.lock
    if "cargo.lock" in lower_name or "poetry.lock" in lower_name:
        blocks = re.split(r'(?:\r?\n)(?=\[\[package\]\])', content)
        matches = []
        for block in blocks:
            b = block.strip()
            if not b.startswith("[[package]]"):
                continue
            m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', b)
            if m:
                pkg_name = m.group(1).strip()
                if pkg_name.lower() == q.lower() or q.lower() in pkg_name.lower():
                    matches.append(b)
                    if len(matches) >= 3:
                        break
        if matches:
            return "\n\n".join(matches)

    # 3. Yarn: yarn.lock
    if "yarn.lock" in lower_name:
        # Match blocks like: "pkg@^1.0.0", pkg@npm:...:
        pattern = re.compile(
            r'(?:^|\n)((?:(?:"?[^:\n]*' + re.escape(q) + r'[^:\n]*"?:?[ \t]*\n)+)(?:[ \t]+[^\n]+\n*)+)',
            re.IGNORECASE,
        )
        m = pattern.search(content)
        if m:
            return m.group(1).strip()

    # 4. PHP: composer.lock
    if "composer.lock" in lower_name:
        try:
            data = json.loads(content)
            for section in ("packages", "packages-dev"):
                for pkg in data.get(section, []):
                    if isinstance(pkg, dict):
                        p_name = pkg.get("name", "")
                        if q.lower() in p_name.lower():
                            return json.dumps(pkg, indent=2)
        except Exception:
            pass

    # 5. Generic / Minified / Regex Fallback
    lines = content.splitlines()
    if len(lines) > 1:
        matching_indices = [i for i, line in enumerate(lines) if q.lower() in line.lower()]
        if matching_indices:
            idx = matching_indices[0]
            start_idx = max(0, idx - 3)
            end_idx = min(len(lines), idx + 8)
            snippet = "\n".join(lines[start_idx:end_idx])
            return f"... [matching context lines {start_idx+1}-{end_idx}] ...\n{snippet}"
    else:
        # Single-line minified file
        idx = content.lower().find(q.lower())
        if idx != -1:
            start_pos = max(0, idx - 100)
            end_pos = min(len(content), idx + 200)
            return f"... [offset {start_pos}-{end_pos}] ...\n{content[start_pos:end_pos]}"

    return None


def extract_lockfile_summary(base_name: str, content: str) -> str:
    """Extract a high-level, human-readable summary of direct dependencies."""
    lower_name = base_name.lower()

    # 1. NPM: package-lock.json
    if "package-lock.json" in lower_name or "shrinkwrap" in lower_name:
        try:
            data = json.loads(content)
            version = data.get("lockfileVersion", "unknown")
            packages = data.get("packages", {})
            total_count = len(packages) if packages else len(data.get("dependencies", {}))

            # Find direct root dependencies
            direct_deps = {}
            if "" in packages and "dependencies" in packages[""]:
                direct_deps = packages[""]["dependencies"]
            elif "dependencies" in data:
                direct_deps = data["dependencies"]

            lines = [f"• Lockfile Version: v{version} (Total locked packages: {total_count:,})"]
            if direct_deps:
                dep_items = list(direct_deps.items())[:15]
                formatted = [
                    f"{k}@{v if isinstance(v, str) else v.get('version', '')}"
                    for k, v in dep_items
                ]
                lines.append(f"• Sample Direct Dependencies (first {len(dep_items)}):")
                lines.append("  " + ", ".join(formatted))
                if len(direct_deps) > 15:
                    lines.append(f"  ... (+ {len(direct_deps) - 15} more direct dependencies)")
            return "\n".join(lines)
        except Exception:
            pass

    # 2. Rust: Cargo.lock
    if "cargo.lock" in lower_name:
        pkgs = re.findall(r'name\s*=\s*["\']([^"\']+)["\']\s*\n\s*version\s*=\s*["\']([^"\']+)["\']', content)
        if pkgs:
            sample = [f"{n}@{v}" for n, v in pkgs[:15]]
            return (
                f"• Cargo locked packages: {len(pkgs):,}\n"
                f"• Sample packages (first {len(sample)}):\n"
                f"  " + ", ".join(sample) + (f"\n  ... (+ {len(pkgs) - 15} more packages)" if len(pkgs) > 15 else "")
            )

    # 3. Python: poetry.lock
    if "poetry.lock" in lower_name:
        pkgs = re.findall(r'name\s*=\s*["\']([^"\']+)["\']\s*\n\s*version\s*=\s*["\']([^"\']+)["\']', content)
        if pkgs:
            sample = [f"{n}@{v}" for n, v in pkgs[:15]]
            return (
                f"• Poetry locked packages: {len(pkgs):,}\n"
                f"• Sample packages (first {len(sample)}):\n"
                f"  " + ", ".join(sample) + (f"\n  ... (+ {len(pkgs) - 15} more packages)" if len(pkgs) > 15 else "")
            )

    # 4. Minified Assets
    if lower_name.endswith(".min.js") or lower_name.endswith(".min.css"):
        chars = len(content)
        return (
            f"• Production Minified Asset ({chars:,} characters, {len(content.splitlines())} lines).\n"
            f"• LLM/Human reading not advised; inspect unminified source code instead."
        )

    # Generic Fallback
    lines_count = len(content.splitlines())
    return f"• Auto-generated lock/asset file containing {lines_count:,} lines."


def process_lockfile(
    file_path: str | Path,
    content: str,
    query: str | None = None,
) -> str:
    """Process a lockfile, returning a surgical match or compact structural summary."""
    base_name = os.path.basename(str(file_path))
    file_size_bytes = len(content.encode("utf-8", errors="replace"))
    file_size_kb = file_size_bytes / 1024
    est_tok = estimate_tokens(content)

    # Case A: Surgical search requested
    if query and query.strip():
        q_clean = query.strip()
        match_snippet = find_package_in_lockfile(base_name, content, q_clean)
        if match_snippet:
            match_tok = estimate_tokens(match_snippet)
            saved = max(0, est_tok - match_tok)
            # Record savings in telemetry
            try:
                from token_saver.telemetry.stats import tracker

                tracker.record_savings("lockfile", est_tok, match_tok)
            except Exception:
                pass

            return (
                f"[TOKEN-SAVER SHIELD: {base_name}] Package match for '{q_clean}':\n"
                f"```\n{match_snippet}\n```\n\n"
                f"🛡️ Context Protected: {est_tok:,} -> {match_tok:,} tokens ({saved:,} tokens saved).\n"
                f"Pass force_full=True to read the entire raw file."
            )
        else:
            return (
                f"[TOKEN-SAVER SHIELD: {base_name}] Package '{q_clean}' was NOT found in {base_name}.\n"
                f"Total file size: {file_size_kb:.1f} KB (~{est_tok:,} tokens).\n"
                f"Pass force_full=True to read the entire raw file."
            )

    # Case B: No query provided -> Return compact structural summary
    summary_info = extract_lockfile_summary(base_name, content)
    summary_payload = (
        f"[TOKEN-SAVER SHIELD: {base_name}]\n"
        f"Auto-generated lockfile/asset detected ({file_size_kb:.1f} KB, ~{est_tok:,} tokens).\n"
        f"Body masked to protect context window from compaction.\n\n"
        f"{summary_info}\n\n"
        f"💡 HOW TO ACCESS SPECIFIC DATA:\n"
        f"• Check package version: call read_file_smart(file_path='{base_name}', query='<package_name>')\n"
        f"• Inspect direct dependencies: view manifest (package.json, Cargo.toml, pyproject.toml)\n"
        f"• Read raw entire file: call read_file_smart(file_path='{base_name}', force_full=True)"
    )

    opt_tok = estimate_tokens(summary_payload)
    try:
        from token_saver.telemetry.stats import tracker

        tracker.record_savings("lockfile", est_tok, opt_tok)
    except Exception:
        pass

    return summary_payload
