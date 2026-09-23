# 🔋 Token-Saver

**MCP server that saves 70-95% tokens for AI coding assistants — without losing functionality.**

Token-Saver sits between your AI coding assistant and your codebase, intelligently compressing code reads, terminal outputs, and file operations to dramatically reduce token consumption.

Works with **Claude Code**, **Cursor**, **Antigravity (AGY)**, **Continue.dev**, and any MCP-compatible AI tool.

## ✨ Features

| Module | What It Does | Token Savings |
|:---|:---|:---|
| 🦴 **Code Skeletonizer** | Extracts structural skeleton (signatures, types, docstrings) via Tree-sitter AST | **80-95%** |
| 📖 **Smart File Reader** | Session-level SHA-256 caching with differential reads | **90-99%** |
| 🖥️ **Terminal Pruner** | Filters test/build/git output, keeps only errors & summaries | **60-90%** |
| 🗺️ **Repo Map** | PageRank-based codebase overview within token budget | **Budget-fitted** |

## 🚀 Quick Start

### Installation

```bash
pip install token-saver
```

Or from source:

```bash
git clone https://github.com/omere/Token-Saver.git
cd Token-Saver
pip install -e .
```

### Setup with Your AI Assistant

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add token-saver -- python -m token_saver
```
</details>

<details>
<summary><b>Cursor</b></summary>

Create `.cursor/mcp.json`:
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
<summary><b>Continue.dev</b></summary>

Add to `.continue/config.yaml`:
```yaml
mcpServers:
  - name: token-saver
    command: python
    args: ["-m", "token_saver"]
```
</details>

## 🛠️ Available Tools

### `get_code_skeleton`
Extract structural skeleton of a source file — classes, function signatures, type hints, docstrings, and imports. Bodies are replaced with `...`.

```
Before: 847 tokens (full file)
After:  127 tokens (skeleton)
Saved:  85%
```

### `get_symbol`
Extract the full implementation of a specific function or class by name. Use after viewing a skeleton to fetch only what you need.

### `read_file_smart`
Read files with automatic session caching. Unchanged files return `[CACHED]` (~3 tokens). Changed files return only the diff.

### `run_command_smart`
Execute shell commands with intelligent output filtering. Test results, build logs, and git output are automatically compressed.

### `get_repo_map`
Generate a structural map of the entire codebase fitted to a token budget. Uses Tree-sitter + importance scoring.

### `get_directory_tree`
Lightweight directory tree listing with smart filtering.

### `filter_output`
Pure filtering tool — apply test/build/git filters to any text without executing commands.

### `cache_stats`
View session cache performance metrics.

## 🌍 Supported Languages

Token-Saver uses Tree-sitter for parsing and supports **130+ programming languages** including:

Python · TypeScript · JavaScript · Go · Rust · Java · C# · C/C++ · Ruby · PHP · Swift · Kotlin · Scala · Dart · Lua · Elixir · Haskell · and many more.

## 📊 How It Works

```
┌─────────────────────────────────┐
│   AI Coding Assistant           │
│   (Claude Code / Cursor / AGY)  │
└──────────┬──────────────────────┘
           │ MCP (stdio / JSON-RPC 2.0)
           ▼
┌─────────────────────────────────┐
│   Token-Saver MCP Server        │
│                                  │
│   📄 Code Skeletonizer           │
│      └─ Tree-sitter AST → ...   │
│   📖 Smart File Reader           │
│      └─ SHA-256 Cache → Diff    │
│   🖥️ Terminal Pruner             │
│      └─ Heuristic Filters       │
│   🗺️ Repo Map                   │
│      └─ PageRank → Budget Map   │
└─────────────────────────────────┘
```

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

*Built with [FastMCP](https://github.com/jlowin/fastmcp) and [Tree-sitter](https://tree-sitter.github.io/tree-sitter/).*
