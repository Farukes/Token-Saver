"""Global symbol index and search for Token-Saver.

Enables instant repository-wide symbol lookup and blast radius reference
analysis without requiring the agent to guess file paths or read dozens of files.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path

from token_saver.cache.persistent_cache import PersistentCache
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


@dataclass
class SymbolReference:
    symbol_name: str
    file_path: str
    line: int
    kind: str  # CALL, IMPORT, INHERITANCE, USAGE
    snippet: str


def extract_references_from_code(
    source_code: str,
    language: str,
    rel_path: str,
    target_symbol: str,
    def_locations: set[tuple[str, int]],
) -> list[SymbolReference]:
    """Extract all usages, calls, and imports of target_symbol in source_code."""
    if target_symbol not in source_code:
        return []

    lines = source_code.splitlines()
    refs: list[SymbolReference] = []

    tree = parse_code(source_code, language)
    if tree:

        def walk(node):
            if node.type in (
                "identifier",
                "type_identifier",
                "property_identifier",
                "name",
                "field_identifier",
            ):
                node_text = source_code.encode("utf-8")[node.start_byte : node.end_byte].decode(
                    "utf-8", errors="replace"
                )
                if node_text == target_symbol:
                    line_no = node.start_point[0] + 1
                    # Skip if this is the definition site itself
                    if (rel_path, line_no) in def_locations:
                        return

                    # Determine reference kind from AST context
                    kind = "USAGE"
                    parent = node.parent
                    while parent is not None:
                        ptype = parent.type
                        if ptype in ("call_expression", "call", "invocation_expression"):
                            kind = "CALL"
                            break
                        elif ptype in (
                            "import_statement",
                            "import_from_statement",
                            "import_specifier",
                            "use_declaration",
                            "using_directive",
                        ):
                            kind = "IMPORT"
                            break
                        elif ptype in ("class_inheritance", "extends_clause", "implements_clause", "base_class_clause"):
                            kind = "INHERITANCE"
                            break
                        elif ptype in ("function_definition", "class_definition", "method_definition"):
                            # Check if this node is the name of the function/class being defined
                            for child in parent.children:
                                if child == node:
                                    # Definition site
                                    return
                            break
                        parent = parent.parent

                    snippet = lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else ""
                    refs.append(
                        SymbolReference(
                            symbol_name=target_symbol,
                            file_path=rel_path,
                            line=line_no,
                            kind=kind,
                            snippet=snippet,
                        )
                    )
            for child in node.children:
                walk(child)

        walk(tree.root_node)
    else:
        # Fallback for languages without tree-sitter or on parse failure
        pattern = re.compile(r"\b" + re.escape(target_symbol) + r"\b")
        for i, line in enumerate(lines, 1):
            if (rel_path, i) in def_locations:
                continue
            if pattern.search(line):
                trimmed = line.strip()
                if trimmed.startswith(("#", "//", "/*", "*")):
                    continue
                if any(kw in trimmed for kw in ("import ", "from ", "require(", "use ")):
                    kind = "IMPORT"
                elif f"{target_symbol}(" in trimmed:
                    kind = "CALL"
                else:
                    kind = "USAGE"
                refs.append(
                    SymbolReference(
                        symbol_name=target_symbol,
                        file_path=rel_path,
                        line=i,
                        kind=kind,
                        snippet=trimmed,
                    )
                )

    # De-duplicate references on the same line
    seen_lines = set()
    unique_refs = []
    for r in refs:
        key = (r.file_path, r.line)
        if key not in seen_lines:
            seen_lines.add(key)
            unique_refs.append(r)
    return unique_refs


class SymbolIndexer:
    """Extracts and indexes symbols across a codebase using Tree-sitter AST and SQLite caching."""

    @staticmethod
    def extract_symbols_from_code(source_code: str, language: str, rel_path: str) -> list[IndexedSymbol]:
        """Parse source code and return all top-level and method symbols."""
        tree = parse_code(source_code, language)
        if not tree:
            return []

        symbols: list[IndexedSymbol] = []
        lines = source_code.splitlines()
        source_bytes = source_code.encode("utf-8")

        def get_signature_text(node) -> str:
            start_l = node.start_point[0]
            if 0 <= start_l < len(lines):
                return lines[start_l].strip()
            return ""

        def walk(node, parent_kind: str = ""):
            kind = None
            if node.type in ("function_definition", "function_declaration", "function_item"):
                kind = "method" if parent_kind in ("class", "interface") else "function"
            elif node.type in ("class_definition", "class_declaration", "class", "class_specifier"):
                kind = "class"
            elif node.type in ("method_definition", "method_declaration", "method"):
                kind = "method"
            elif node.type in ("struct_item", "struct_declaration", "struct_specifier"):
                kind = "struct"
            elif node.type in ("module", "module_declaration"):
                kind = "module"
            elif node.type in ("interface_declaration", "interface"):
                kind = "interface"

            if kind:

                def get_symbol_name_node(n):
                    for child in n.children:
                        if child.type in (
                            "identifier",
                            "type_identifier",
                            "property_identifier",
                            "name",
                            "simple_identifier",
                            "constant",
                            "field_identifier",
                        ):
                            return child
                        elif child.type in ("function_declarator", "declarator"):
                            nested = get_symbol_name_node(child)
                            if nested:
                                return nested
                    return None

                name_node = get_symbol_name_node(node)

                if name_node:
                    sym_name = source_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8", errors="replace")
                    line_no = node.start_point[0] + 1
                    sig = get_signature_text(node)
                    body_bytes = source_bytes[node.start_byte : node.end_byte]
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

    _last_index_time: dict[str, float] = {}

    @classmethod
    def index_repository(cls, root_path: str = ".", min_interval: float = 3.0) -> list[IndexedSymbol]:
        """Scan and index all non-ignored source files in the repository incrementally using PersistentCache."""
        root = Path(root_path).resolve()
        root_str = str(root)

        now = time.time()
        if min_interval > 0 and (now - cls._last_index_time.get(root_str, 0.0)) < min_interval:
            return []
        cls._last_index_time[root_str] = now

        config = load_config(root)
        cache = PersistentCache()
        all_symbols: list[IndexedSymbol] = []
        valid_rel_paths: set[str] = set()

        for f_path_str in walk_source_files(str(root), max_files=config.max_source_files):
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

            valid_rel_paths.add(rel)

            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue

            meta = cache.get_indexed_file_meta(root_str, rel)
            if meta and meta[1] == mtime:
                # Cache hit on mtime! Fast skip, already indexed in SQLite
                continue

            text = read_file_text(f_path_str)
            if not text:
                continue

            f_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            if meta and meta[0] == f_hash:
                # Content unchanged even if mtime changed
                continue

            # Need re-parse
            symbols = cls.extract_symbols_from_code(text, lang, rel)
            sym_dicts = [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "file_path": s.file_path,
                    "line": s.line,
                    "signature": s.signature,
                }
                for s in symbols
            ]
            cache.set_file_symbols(root_str, rel, f_hash, mtime, sym_dicts)
            all_symbols.extend(symbols)

        # Clean up files that were deleted from disk
        cache.prune_project_deleted_files(root_str, valid_rel_paths)
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
    root = Path(root_path).resolve()
    # Ensure incremental index is up to date
    symbols = SymbolIndexer.index_repository(root_path)
    q = query.strip()
    if not q:
        return "Error: Empty query provided."

    cache = PersistentCache()
    cached_matches = cache.search_symbols(str(root), q, exact=exact, max_results=max_results)

    matches: list[IndexedSymbol] = []
    if cached_matches:
        for m in cached_matches:
            matches.append(
                IndexedSymbol(
                    name=m["name"],
                    kind=m["kind"],
                    file_path=m["file_path"],
                    line=m["line"],
                    signature=m["signature"],
                    content_hash=m["file_hash"],
                )
            )
    else:
        for s in symbols:
            if exact:
                if s.name == q:
                    matches.append(s)
            else:
                if q.lower() in s.name.lower():
                    matches.append(s)
        matches = matches[:max_results]

    if not matches:
        return f"No symbols found matching '{query}' across the codebase."

    lines = [
        f"[SYMBOLS] Found {len(matches)} symbol(s) matching '{query}':",
        "----------------------------------------",
    ]
    for i, m in enumerate(matches, 1):
        lines.append(f"{i}. [{m.kind.upper()}] {m.name} -> {m.file_path}:{m.line}")
        if m.signature:
            lines.append(f"   Signature: {m.signature}")

    result_text = "\n".join(lines)
    estimated_raw = max(len(symbols), 10) * 150
    estimated_opt = estimate_tokens(result_text)
    if estimated_raw > estimated_opt:
        try:
            from token_saver.telemetry.stats import tracker

            tracker.record_savings("symbol_search", estimated_raw, estimated_opt)
        except Exception:
            pass

    return result_text


def find_symbol_references(
    symbol_name: str,
    root_path: str = ".",
    max_results: int = 25,
) -> str:
    """Find all usages, calls, and imports of a symbol across the entire codebase.

    Use this tool before editing, refactoring, or deleting functions/classes to
    inspect blast radius and identify all dependent files and lines.

    Args:
        symbol_name: Exact or target symbol name (e.g. 'calculate_discount', 'UserAuth').
        root_path: Project root path.
        max_results: Maximum number of references to return.

    Returns:
        Formatted summary with definition sites, callers, imports, and line snippets.
    """
    sym = symbol_name.strip()
    if not sym:
        return "Error: Empty symbol_name provided."

    root = Path(root_path).resolve()
    # 1. Update incremental index in SQLite
    SymbolIndexer.index_repository(root_path)

    # 2. Query definition locations directly from indexed SQLite store (instant O(1))
    cache = PersistentCache()
    cached_defs = cache.search_symbols(str(root), sym, exact=True, max_results=10)
    def_locations = {(d["file_path"], d["line"]) for d in cached_defs}

    config = load_config(root)
    all_refs: list[SymbolReference] = []
    scanned_candidate_files = 0

    for f_path_str in walk_source_files(str(root), max_files=config.max_source_files):
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
        if not text or sym not in text:
            continue

        scanned_candidate_files += 1
        refs = extract_references_from_code(text, lang, rel, sym, def_locations)
        all_refs.extend(refs)

    if not all_refs and not cached_defs:
        return f"No references or definitions found for '{symbol_name}' across the codebase."

    lines = [f"[REFERENCES] Blast Radius Analysis for '{sym}':"]
    if cached_defs:
        def_strs = [f"{d['file_path']}:{d['line']} ({d['kind']})" for d in cached_defs[:3]]
        lines.append(f"• Defined at: {', '.join(def_strs)}")
    else:
        lines.append("• Defined at: External / Unindexed symbol")

    unique_files = len({r.file_path for r in all_refs})
    lines.append(f"• Total Usages: {len(all_refs)} reference(s) found across {unique_files} file(s):")
    lines.append("-" * 60)

    for i, r in enumerate(all_refs[:max_results], 1):
        lines.append(f"{i}. [{r.kind}] {r.file_path}:{r.line}")
        if r.snippet:
            lines.append(f"   Line {r.line}: {r.snippet}")

    if len(all_refs) > max_results:
        lines.append(f"\n... and {len(all_refs) - max_results} more reference(s) omitted.")

    result_text = "\n".join(lines)

    # Estimate savings: AI would have had to open and read candidate files
    estimated_raw = max(scanned_candidate_files, 1) * 800
    estimated_opt = estimate_tokens(result_text)
    if estimated_raw > estimated_opt:
        try:
            from token_saver.telemetry.stats import tracker

            tracker.record_savings("symbol_search", estimated_raw, estimated_opt)
        except Exception:
            pass

    return result_text


def register_symbol_index_tools(mcp) -> None:
    """Register global symbol search and blast radius reference tools with FastMCP."""

    @mcp.tool()
    def find_symbol_global(query: str, root_path: str = ".", exact: bool = False, max_results: int = 15) -> str:
        """Search for functions, methods, or classes across the entire codebase by name.
        Use this tool to instantly locate where a symbol is defined without reading
        multiple files or guessing paths.
        """
        return globals()["find_symbol_global"](query, root_path, exact, max_results)

    @mcp.tool()
    def find_symbol_references(symbol_name: str, root_path: str = ".", max_results: int = 25) -> str:
        """Search for all usages, calls, and imports of a symbol across the entire codebase.
        Use this tool before editing, refactoring, or deleting functions/classes to
        inspect blast radius and identify all dependent files and lines without reading full files.
        """
        return globals()["find_symbol_references"](symbol_name, root_path, max_results)
