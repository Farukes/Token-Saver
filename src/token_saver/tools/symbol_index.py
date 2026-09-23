"""Global symbol index and search for Token-Saver.

Enables instant repository-wide symbol lookup without requiring the agent
to guess the file path or read dozens of files.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from token_saver.config import load_config
from token_saver.parsers.languages import parse_code
from token_saver.utils.file_utils import (
    detect_language,
    read_file_text,
    walk_source_files,
)
from token_saver.utils.token_counter import estimate_tokens


@dataclass
class IndexedSymbol:
    name: str
    kind: str  # class, function, method, struct, module
    file_path: str  # relative path
    line: int
    signature: str
    content_hash: str = ""


class SymbolIndexer:
    """Extracts and indexes symbols across a codebase using Tree-sitter AST."""

    @staticmethod
    def extract_symbols_from_code(source_code: str, language: str, rel_path: str) -> list[IndexedSymbol]:
        """Parse source code and return all top-level and method symbols."""
        tree = parse_code(source_code, language)
        if not tree:
            return []

        symbols: list[IndexedSymbol] = []
        lines = source_code.splitlines()

        def get_line_num(byte_offset: int) -> int:
            return source_code[:byte_offset].count("\n") + 1

        def get_signature_text(node) -> str:
            start_l = get_line_num(node.start_byte) - 1
            if 0 <= start_l < len(lines):
                return lines[start_l].strip()
            return ""

        def walk(node, parent_kind: str = ""):
            kind = None
            if node.type in ("function_definition", "function_declaration", "function_item"):
                kind = "method" if parent_kind in ("class", "interface") else "function"
            elif node.type in ("class_definition", "class_declaration", "class"):
                kind = "class"
            elif node.type in ("method_definition", "method_declaration", "method"):
                kind = "method"
            elif node.type in ("struct_item", "struct_declaration"):
                kind = "struct"
            elif node.type in ("module", "module_declaration"):
                kind = "module"

            if kind:
                name_node = None
                for child in node.children:
                    if child.type in (
                        "identifier",
                        "type_identifier",
                        "property_identifier",
                        "name",
                        "simple_identifier",
                        "constant",
                    ):
                        name_node = child
                        break

                if name_node:
                    sym_name = source_code.encode("utf-8")[name_node.start_byte : name_node.end_byte].decode("utf-8")
                    line_no = get_line_num(node.start_byte)
                    sig = get_signature_text(node)
                    body_bytes = source_code.encode("utf-8")[node.start_byte : node.end_byte]
                    c_hash = hashlib.sha256(body_bytes).hexdigest()[:16]
                    symbols.append(
                        IndexedSymbol(
                            name=sym_name,
                            kind=kind,
                            file_path=rel_path,
                            line=line_no,
                            signature=sig,
                            content_hash=c_hash,
                        )
                    )

            current_kind = kind if kind in ("class", "interface", "module") else parent_kind
            for child in node.children:
                walk(child, current_kind)

        walk(tree.root_node)
        return symbols

    @classmethod
    def index_repository(cls, root_path: str = ".") -> list[IndexedSymbol]:
        """Scan and index all non-ignored source files in the repository."""
        root = Path(root_path).resolve()
        config = load_config(root)
        all_symbols: list[IndexedSymbol] = []

        for f_path_str in walk_source_files(str(root)):
            p = Path(f_path_str)
            try:
                rel = p.relative_to(root).as_posix()
            except ValueError:
                rel = p.as_posix()

            if config.is_ignored(rel) or config.is_ignored(f_path_str):
                continue

            lang = detect_language(f_path_str)
            if not lang:
                continue

            text = read_file_text(f_path_str)
            if not text:
                continue

            symbols = cls.extract_symbols_from_code(text, lang, rel)
            all_symbols.extend(symbols)

        return all_symbols


def find_symbol_global(
    query: str,
    root_path: str = ".",
    exact: bool = False,
    max_results: int = 15,
) -> str:
    """Search for code symbols (classes, functions, methods) across the entire project.

    Args:
        query: Symbol name or substring to search for (e.g. 'AuthService', 'login').
        root_path: Project root path.
        exact: If True, only match exact symbol names (case-sensitive).
        max_results: Maximum number of matches to return.

    Returns:
        Formatted summary of matches with file locations and signatures.
    """
    symbols = SymbolIndexer.index_repository(root_path)
    q = query.strip()
    if not q:
        return "Error: Empty query provided."

    matches: list[IndexedSymbol] = []
    for s in symbols:
        if exact:
            if s.name == q:
                matches.append(s)
        else:
            if q.lower() in s.name.lower():
                matches.append(s)

    if not matches:
        return f"No symbols found matching '{query}' across the codebase."

    matches = matches[:max_results]
    lines = [f"[SYMBOLS] Found {len(matches)} symbol(s) matching '{query}':", "----------------------------------------"]
    for i, m in enumerate(matches, 1):
        lines.append(f"{i}. [{m.kind.upper()}] {m.name} -> {m.file_path}:{m.line}")
        if m.signature:
            lines.append(f"   Signature: {m.signature}")

    result_text = "\n".join(lines)
    # Estimate savings vs reading multiple full files
    estimated_raw = len(symbols) * 150
    estimated_opt = estimate_tokens(result_text)
    if estimated_raw > estimated_opt:
        try:
            from token_saver.telemetry.stats import tracker

            tracker.record_savings("symbol_search", estimated_raw, estimated_opt)
        except Exception:
            pass

    return result_text


def register_symbol_index_tools(mcp) -> None:
    """Register global symbol search tools with FastMCP."""

    @mcp.tool()
    def find_symbol_global(query: str, root_path: str = ".", exact: bool = False, max_results: int = 15) -> str:
        """Search for functions, methods, or classes across the entire codebase by name.
        Use this tool to instantly locate where a symbol is defined without reading
        multiple files or guessing paths.
        """
        return globals()["find_symbol_global"](query, root_path, exact, max_results)
