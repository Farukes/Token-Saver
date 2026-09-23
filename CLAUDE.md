# Token-Saver Project Guidelines for Claude Code

This project is **Token-Saver**, a zero-cost MCP server that cuts 70-95% of tokens for AI coding assistants.

## Commands

- Run all tests: `python -m pytest tests/ -v`
- Run specific test: `python -m pytest tests/test_skeleton.py -v`
- Start MCP server: `python -m token_saver`
- Lint code: `ruff check src/ tests/`

## Coding Conventions

- Python 3.10+ with `from __future__ import annotations` at the top of every file.
- All MCP tools must register via FastMCP and provide concise, clear docstrings that help LLMs select the tool.
- Always output debug logs to `sys.stderr`, NEVER `sys.stdout` (as `stdout` is reserved for JSON-RPC MCP messages).
- All file reads, parsers, and filters must be deterministic and preserve critical information (types, signatures, error tracebacks, exit codes).
