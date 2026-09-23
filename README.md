# 🔋 Token-Saver

[![CI](https://github.com/Farukes/Token-Saver/actions/workflows/ci.yml/badge.svg)](https://github.com/Farukes/Token-Saver/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Zero Telemetry](https://img.shields.io/badge/telemetry-0%25%20(100%25%20local)-success.svg)](#-enterprise-privacy--security-guarantee)

**MCP server that saves 70-95% tokens for AI coding assistants — without losing functionality.**

Token-Saver sits between your AI coding assistant and your codebase, intelligently compressing code reads, terminal outputs, and file operations to dramatically reduce token consumption, context compaction, and latency.

Works with **Claude Code**, **Cursor**, **Antigravity (AGY)**, **Windsurf**, **Continue.dev**, and any MCP-compatible AI assistant.

---

## ✨ Features & Architecture

| Module | What It Does | Token Savings |
|:---|:---|:---|
| 🦴 **Code Skeletonizer** | Extracts structural skeleton (signatures, types, docstrings) via Tree-sitter AST | **80-95%** |
| 📖 **Smart File Reader** | L1 RAM + L2 Persistent SQLite cache with differential reads & diff headers | **90-99%** |
| 🖥️ **Terminal Pruner** | Compresses test/build/git terminal streams, keeps errors and summary info | **60-90%** |
| 🗺️ **Repo Map** | PageRank & Graph Centrality codebase overview fitted into custom token budgets | **Budget-fitted** |
| 🛡️ **Autonomous Guardrails** | Fallback safety on errors, tiny file protection, and runaway memory ceilings | **Guaranteed** |

### 🛡️ Built-in Guardrails & Reliability
- **L1 RAM + L2 SQLite Persistent Cache:** Survives MCP server restarts and IDE reboots (`~/.token-saver/cache.db` with WAL mode).
- **Fallback Safety Guard:** If a test or command fails (`exit_code != 0`), Token-Saver guarantees tracebacks and error contexts are preserved intact.
- **Tiny File Anomaly Guard:** If a diff header would consume more tokens than the file itself, the full content is returned to prevent token inflation.
- **Runaway Stream Protection:** Protects host memory from infinite loops by capping raw terminal buffers at 2MB with graceful truncation.
- **SQLite Database Bloat Guard:** Files larger than 5MB are cached by hash reference without bloating disk space.

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/Farukes/Token-Saver.git
cd Token-Saver
pip install -e .
```

### Auto-Configure Agent Steering Rules

Automatically inject Token-Saver optimization instructions into your repository rules:

```bash
# Injects rules into AGENTS.md, .cursorrules, .windsurfrules, and CLAUDE.md
token-saver init-rules
```

### 🎛️ Output Optimization Controls (CLI & Terminals)

Switch between compact surgical output and default unrestricted output with crystal-clear commands:

```bash
# 🟢 Enable compact surgical diffs & zero-truncation quality mandate
token-saver output on

# ⚪ Revert AI assistant to default unrestricted output settings
token-saver output off

# 📊 Check current output configuration status
token-saver output
```

Slash commands are also supported in your AI assistant chat (`/token-saver output on`, `/token-saver output off`).

---

## 🔌 Setup with Your AI Assistant

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add token-saver -- python -m token_saver
```
</details>

<details>
<summary><b>Cursor</b></summary>

Create or update `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "token-saver": {
      "command": "python",
      "args": ["-m", "token_saver"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```
</details>

<details>
<summary><b>Antigravity (AGY)</b></summary>

Add to `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "token-saver": {
      "command": "python",
      "args": ["-m", "token_saver"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```
</details>

<details>
<summary><b>Windsurf / Cascade</b></summary>

Add to `~/.codeium/windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "token-saver": {
      "command": "python",
      "args": ["-m", "token_saver"]
    }
  }
}
```
</details>

<details>
<summary><b>Continue.dev</b></summary>

Add to `.continue/config.yaml`:
```yaml
mcpServers:
  - name: token-saver
    command: python
    args: ["-m", "token_saver"]
```
</details>

---

## 🛠️ Available MCP Tools

- **`find_symbol_global(query, root_path=".", exact=False)`**: Search for functions, methods, or classes across the entire codebase by name without reading multiple files.
- **`get_code_skeleton(file_path)`**: Extract structural skeleton of a file — classes, function signatures, docstrings, and type annotations with bodies replaced by `...`. (Supports Python, JS/TS, Go, Rust, Java, C/C++, C#, Ruby, PHP, Kotlin).
- **`get_symbol(file_path, symbol_name)`**: Extract the full implementation of a specific class or function by name after inspecting its skeleton.
- **`read_file_smart(file_path, force_full=False)`**: Differential file reader. Identical files return `[CACHED] unchanged` (~3 tokens). Changed files return unified diffs. Protected against sensitive credential leaks.
- **`run_command_smart(command, cwd=".")`**: Executes shell commands and prunes verbose logs from pytest, jest, npm, cargo, and git.
- **`filter_output(output, output_type="auto")`**: Pure text filter for test runners, build pipelines, and version control logs without executing commands.
- **`get_repo_map_tool(root_path=".", max_tokens=1000)`**: Graph centrality codebase map prioritized by cross-file import relationships.
- **`get_directory_tree_tool(root_path=".", max_depth=4)`**: Lightweight directory tree honoring `.gitignore` and skipping binary folders.
- **`cache_stats()`**: Inspect session read hits, misses, diffs, and aggregate token savings.

### 📦 MCP Resources & Prompts

- **Resources:**
  - `token-saver://stats`: Live cumulative token and financial savings dashboard.
  - `token-saver://guide`: AI assistant best-practice optimization guidelines.
  - `token-saver://config`: Active project configuration and ignore settings.
- **Prompts:**
  - `optimize_coding_task(task_description)`: System prompt template steering assistants toward token-efficient workflows.

---

## ⚙️ Project Configuration (`token-saver.toml`)

Create an optional `token-saver.toml` in your repository root to customize exclusions and budgets:

```toml
[general]
ignore_patterns = ["tests/fixtures/*", "legacy/*", "*.bak"]
max_cacheable_bytes = 5242880 # 5 MB

[cache]
ttl_days = 30
max_entries = 5000

[repo_map]
default_budget = 1000
```

---

## 💻 CLI Commands & Shell Hooks

Token-Saver also functions as an interactive command-line utility for human developers and local shell automation:

```bash
# View cumulative savings dashboard (tokens saved, money saved, operations)
token-saver stats

# Run any shell command through intelligent filtering
token-saver run "pytest tests/ -v"
token-saver run "npm test"

# Temporary bypass: see 100% of raw output when you need full logs
RAW=1 token-saver run "pytest"
token-saver run "pytest --raw"

# Prune expired or excess entries from L2 SQLite cache
token-saver cache-prune --ttl-days 30 --max-entries 5000

# Install transparent shell hooks (so pytest/npm are automatically filtered)
token-saver hook

# Cleanly and safely uninstall all shell hooks
token-saver unhook

# Install steering rules across all AI assistant configurations
token-saver init-rules

# Install /token-saver slash commands for AGY CLI and Claude Code
token-saver setup-commands

# Reset metrics counter
token-saver reset-stats
```

---

## 🔒 Enterprise Privacy & Security Guarantee

Token-Saver is built strictly under a **Zero-Telemetry, 100% Localhost** design philosophy:

- **100% Local Execution:** All parsing (Tree-sitter), caching (SQLite), and output filtering happen locally in-process on your CPU.
- **Zero External Network Calls:** No telemetry servers, no analytical trackers, no outbound pings, and no cloud dependencies whatsoever.
- **Air-Gapped Compatible:** Safely operates in classified, offline, or air-gapped corporate enterprise environments.
- **Local Data Isolation:** Persistent cache (`~/.token-saver/cache.db`) and statistics (`~/.token-saver/telemetry.json`) reside exclusively in your user directory and can be purged at any time with `token-saver reset-stats` or by deleting the directory.
- **Non-Invasive Architecture:** Never modifies your project code without explicit assistant direction.

---

## 🌍 Supported Languages

Token-Saver uses Tree-sitter for AST parsing and supports **130+ programming languages** out of the box, including:

Python · TypeScript · JavaScript · Go · Rust · Java · C# · C / C++ · Ruby · PHP · Swift · Kotlin · Scala · Dart · Lua · Elixir · Haskell · and more.

---

## 🧪 Development & Quality Assurance

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run full test suite
pytest tests/ -v

# Code quality and style checks
ruff check .
```

---

## 📄 License & Intellectual Property

Copyright © 2026 Ömer Faruk Eskitürk. All rights reserved.

Proprietary software. Unauthorized copying, reverse engineering, redistribution, or modification of this source code and documentation is strictly prohibited. See [LICENSE](LICENSE) for details.
