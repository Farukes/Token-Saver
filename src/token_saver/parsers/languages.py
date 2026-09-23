"""Tree-sitter language parser management.

Provides lazy-loaded Tree-sitter parsers and language grammars
for 130+ programming languages via tree-sitter-languages.
"""

from __future__ import annotations

import sys
import warnings
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tree_sitter


@lru_cache(maxsize=32)
def get_language(lang_name: str) -> tree_sitter.Language | None:
    """Get a Tree-sitter Language object by name.

    Uses tree-sitter-languages for precompiled grammars.
    Returns None if the language is not available.
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")
            from tree_sitter_languages import get_language as _get_lang

            return _get_lang(lang_name)
    except Exception:
        print(f"[token-saver] Language not available: {lang_name}", file=sys.stderr)
        return None


@lru_cache(maxsize=32)
def get_parser(lang_name: str) -> tree_sitter.Parser | None:
    """Get a Tree-sitter Parser configured for a specific language.

    Returns None if the language is not available.
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")
            from tree_sitter_languages import get_parser as _get_parser

            return _get_parser(lang_name)
    except Exception:
        print(f"[token-saver] Parser not available: {lang_name}", file=sys.stderr)
        return None


def parse_code(source: str, lang_name: str) -> tree_sitter.Tree | None:
    """Parse source code into a Tree-sitter syntax tree.

    Returns None if the language is not available or parsing fails.
    """
    parser = get_parser(lang_name)
    if parser is None:
        return None

    try:
        return parser.parse(source.encode("utf-8"))
    except Exception as e:
        print(f"[token-saver] Parse error for {lang_name}: {e}", file=sys.stderr)
        return None
