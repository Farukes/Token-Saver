//! Global Symbol Index & Blast Radius Reference Search in Rust.
//!
//! Enables instant repository-wide symbol lookup and blast radius analysis
//! without reading dozens of files or triggering context window compaction.

use std::collections::HashSet;
use std::path::Path;
use sha2::{Digest, Sha256};
use walkdir::WalkDir;

use crate::cache::persistent_cache::PersistentCache;
use crate::config::TokenSaverConfig;
use crate::models::{IndexedSymbol, ReferenceKind, SymbolReference};
use crate::parser::{detect_language, parse_code, SupportedLanguage};

/// Extracts all top-level and method symbols from source code using Tree-sitter.
pub fn extract_symbols_from_code(
    source_code: &str,
    lang: SupportedLanguage,
    rel_path: &str,
) -> Vec<IndexedSymbol> {
    let tree = match parse_code(source_code, lang) {
        Some(t) => t,
        None => return Vec::new(),
    };

    let mut symbols = Vec::new();
    let lines: Vec<&str> = source_code.lines().collect();
    let source_bytes = source_code.as_bytes();

    fn get_signature(node: tree_sitter::Node, lines: &[&str]) -> String {
        let line_idx = node.start_position().row;
        if line_idx < lines.len() {
            lines[line_idx].trim().to_string()
        } else {
            String::new()
        }
    }

    fn walk(
        node: tree_sitter::Node,
        lines: &[&str],
        source_bytes: &[u8],
        rel_path: &str,
        parent_kind: &str,
        symbols: &mut Vec<IndexedSymbol>,
    ) {
        let node_kind = node.kind();
        let mut kind = None;

        if matches!(node_kind, "function_definition" | "function_declaration" | "function_item") {
            kind = Some(if parent_kind == "class" || parent_kind == "impl" {
                "method"
            } else {
                "function"
            });
        } else if matches!(node_kind, "class_definition" | "class_declaration" | "class") {
            kind = Some("class");
        } else if matches!(node_kind, "method_definition" | "method_declaration") {
            kind = Some("method");
        } else if matches!(node_kind, "struct_item" | "struct_declaration") {
            kind = Some("struct");
        } else if matches!(node_kind, "enum_item") {
            kind = Some("enum");
        }

        if let Some(k) = kind {
            let mut name_node = None;
            for child in node.children(&mut node.walk()) {
                if matches!(
                    child.kind(),
                    "identifier" | "type_identifier" | "property_identifier" | "name" | "constant"
                ) {
                    name_node = Some(child);
                    break;
                }
            }

            if let Some(n) = name_node {
                if let Ok(name_str) = std::str::from_utf8(&source_bytes[n.start_byte()..n.end_byte()]) {
                    let line = node.start_position().row + 1;
                    let signature = get_signature(node, lines);
                    let body_slice = &source_bytes[node.start_byte()..node.end_byte()];
                    let mut hasher = Sha256::new();
                    hasher.update(body_slice);
                    let content_hash = format!("{:x}", hasher.finalize())[..16].to_string();

                    symbols.push(IndexedSymbol {
                        name: name_str.to_string(),
                        kind: k.to_string(),
                        file_path: rel_path.to_string(),
                        line,
                        signature,
                        content_hash,
                    });
                }
            }
        }

        let next_parent_kind = if kind == Some("class") {
            "class"
        } else if node_kind == "impl_item" {
            "impl"
        } else {
            parent_kind
        };

        for child in node.children(&mut node.walk()) {
            walk(child, lines, source_bytes, rel_path, next_parent_kind, symbols);
        }
    }

    walk(tree.root_node(), &lines, source_bytes, rel_path, "", &mut symbols);
    symbols
}

/// Extracts all usages, calls, and imports of target_symbol in source code.
pub fn extract_references_from_code(
    source_code: &str,
    lang: SupportedLanguage,
    rel_path: &str,
    target_symbol: &str,
    def_locations: &HashSet<(String, usize)>,
) -> Vec<SymbolReference> {
    if !source_code.contains(target_symbol) {
        return Vec::new();
    }

    let lines: Vec<&str> = source_code.lines().collect();
    let mut refs = Vec::new();
    let source_bytes = source_code.as_bytes();

    if let Some(tree) = parse_code(source_code, lang) {
        fn walk(
            node: tree_sitter::Node,
            lines: &[&str],
            source_bytes: &[u8],
            rel_path: &str,
            target_symbol: &str,
            def_locations: &HashSet<(String, usize)>,
            refs: &mut Vec<SymbolReference>,
        ) {
            let kind = node.kind();
            if matches!(
                kind,
                "identifier" | "type_identifier" | "property_identifier" | "name" | "field_identifier"
            ) {
                if let Ok(text) = std::str::from_utf8(&source_bytes[node.start_byte()..node.end_byte()]) {
                    if text == target_symbol {
                        let line_no = node.start_position().row + 1;
                        if !def_locations.contains(&(rel_path.to_string(), line_no)) {
                            let mut ref_kind = ReferenceKind::Usage;
                            let mut parent = node.parent();
                            while let Some(p) = parent {
                                let ptype = p.kind();
                                if matches!(ptype, "call_expression" | "call" | "invocation_expression") {
                                    ref_kind = ReferenceKind::Call;
                                    break;
                                } else if matches!(
                                    ptype,
                                    "import_statement"
                                        | "import_from_statement"
                                        | "import_specifier"
                                        | "use_declaration"
                                        | "using_directive"
                                ) {
                                    ref_kind = ReferenceKind::Import;
                                    break;
                                } else if matches!(
                                    ptype,
                                    "class_inheritance" | "extends_clause" | "implements_clause" | "base_class_clause"
                                ) {
                                    ref_kind = ReferenceKind::Inheritance;
                                    break;
                                }
                                parent = p.parent();
                            }

                            let snippet = if line_no > 0 && line_no <= lines.len() {
                                lines[line_no - 1].trim().to_string()
                            } else {
                                String::new()
                            };

                            refs.push(SymbolReference {
                                symbol_name: target_symbol.to_string(),
                                file_path: rel_path.to_string(),
                                line: line_no,
                                kind: ref_kind,
                                snippet,
                            });
                        }
                    }
                }
            }

            for child in node.children(&mut node.walk()) {
                walk(child, lines, source_bytes, rel_path, target_symbol, def_locations, refs);
            }
        }

        walk(tree.root_node(), &lines, source_bytes, rel_path, target_symbol, def_locations, &mut refs);
    } else {
        // Fallback line scan
        for (idx, line) in lines.iter().enumerate() {
            let line_no = idx + 1;
            if def_locations.contains(&(rel_path.to_string(), line_no)) {
                continue;
            }
            if line.contains(target_symbol) {
                let trimmed = line.trim();
                let ref_kind = if trimmed.starts_with("import ") || trimmed.starts_with("use ") {
                    ReferenceKind::Import
                } else if trimmed.contains(&format!("{target_symbol}(")) {
                    ReferenceKind::Call
                } else {
                    ReferenceKind::Usage
                };

                refs.push(SymbolReference {
                    symbol_name: target_symbol.to_string(),
                    file_path: rel_path.to_string(),
                    line: line_no,
                    kind: ref_kind,
                    snippet: trimmed.to_string(),
                });
            }
        }
    }

    // Deduplicate references on identical (file_path, line)
    let mut seen = HashSet::new();
    let mut unique_refs = Vec::new();
    for r in refs {
        if seen.insert((r.file_path.clone(), r.line)) {
            unique_refs.push(r);
        }
    }

    unique_refs
}

fn is_skip_dir(entry: &walkdir::DirEntry) -> bool {
    if entry.depth() == 0 || !entry.file_type().is_dir() {
        return false;
    }
    let name = entry.file_name().to_string_lossy();
    name.starts_with('.')
        || name == "target"
        || name == "node_modules"
        || name == "__pycache__"
        || name == "venv"
        || name == ".venv"
        || name == "dist"
        || name == "build"
}

/// Recursively scans and indexes the repository incrementally into SQLite.
pub fn index_repository(root_path: &Path) -> Vec<IndexedSymbol> {
    let root = root_path.canonicalize().unwrap_or_else(|_| root_path.to_path_buf());
    let root_str = root.to_string_lossy().to_string();
    let config = TokenSaverConfig::load_from_dir(&root);
    let cache = match PersistentCache::new() {
        Ok(c) => c,
        Err(_) => return Vec::new(),
    };

    let mut all_symbols = Vec::new();
    let mut file_count = 0;

    for entry in WalkDir::new(&root)
        .into_iter()
        .filter_entry(|e| !is_skip_dir(e))
        .filter_map(|e| e.ok())
    {
        if !entry.file_type().is_file() {
            continue;
        }

        let p = entry.path();
        let rel_path = match p.strip_prefix(&root) {
            Ok(rel) => rel.to_string_lossy().replace('\\', "/"),
            Err(_) => p.to_string_lossy().replace('\\', "/"),
        };

        if config.is_ignored(Path::new(&rel_path)) {
            continue;
        }

        let lang = match detect_language(p) {
            Some(l) => l,
            None => continue,
        };

        file_count += 1;
        if file_count > config.max_source_files {
            break;
        }

        let mtime = std::fs::metadata(p)
            .and_then(|m| m.modified())
            .map(|t| t.duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs_f64())
            .unwrap_or(0.0);

        // Incremental cache check: skip file if mtime is unchanged
        if let Ok(Some((_, cached_mtime))) = cache.get_file_meta(&root_str, &rel_path) {
            if (cached_mtime - mtime).abs() < 0.001 {
                continue;
            }
        }

        let content = match std::fs::read_to_string(p) {
            Ok(c) => c,
            Err(_) => continue,
        };

        let mut hasher = Sha256::new();
        hasher.update(content.as_bytes());
        let file_hash = format!("{:x}", hasher.finalize())[..16].to_string();

        let symbols = extract_symbols_from_code(&content, lang, &rel_path);
        let _ = cache.set_file_symbols(&root_str, &rel_path, &file_hash, mtime, &symbols);
        all_symbols.extend(symbols);
    }

    all_symbols
}

/// Searches for code symbols (classes, functions, methods, structs) across the repository.
pub fn find_symbol_global(
    query: &str,
    root_path: &Path,
    exact: bool,
    max_results: usize,
) -> String {
    let q = query.trim();
    if q.is_empty() {
        return "Error: Empty query provided.".to_string();
    }

    let root = root_path.canonicalize().unwrap_or_else(|_| root_path.to_path_buf());
    let root_str = root.to_string_lossy().to_string();

    // Ensure index is populated
    let _ = index_repository(&root);

    let cache = match PersistentCache::new() {
        Ok(c) => c,
        Err(e) => return format!("Cache Error: {e}"),
    };

    let matches = match cache.search_symbols(&root_str, q, exact, max_results) {
        Ok(m) => m,
        Err(e) => return format!("Search Error: {e}"),
    };

    if matches.is_empty() {
        return format!("No symbols found matching '{query}' across the codebase.");
    }

    let mut lines = Vec::new();
    lines.push(format!("[SYMBOLS] Found {} symbol(s) matching '{query}':", matches.len()));
    lines.push("----------------------------------------".to_string());

    for (i, m) in matches.iter().enumerate() {
        lines.push(format!("{}. [{}] {} -> {}:{}", i + 1, m.kind.to_uppercase(), m.name, m.file_path, m.line));
        if !m.signature.is_empty() {
            lines.push(format!("   Signature: {}", m.signature));
        }
    }

    lines.join("\n")
}

/// Finds all usages, calls, and imports of a symbol across the entire codebase.
pub fn find_symbol_references(
    symbol_name: &str,
    root_path: &Path,
    max_results: usize,
) -> String {
    let sym = symbol_name.trim();
    if sym.is_empty() {
        return "Error: Empty symbol_name provided.".to_string();
    }

    let root = root_path.canonicalize().unwrap_or_else(|_| root_path.to_path_buf());
    let root_str = root.to_string_lossy().to_string();
    let _ = index_repository(&root);

    let cache = match PersistentCache::new() {
        Ok(c) => c,
        Err(e) => return format!("Cache Error: {e}"),
    };

    let cached_defs = cache.search_symbols(&root_str, sym, true, 10).unwrap_or_default();
    let def_locations: HashSet<(String, usize)> = cached_defs
        .iter()
        .map(|d| (d.file_path.clone(), d.line))
        .collect();

    let config = TokenSaverConfig::load_from_dir(&root);
    let mut all_refs = Vec::new();

    for entry in WalkDir::new(&root)
        .into_iter()
        .filter_entry(|e| !is_skip_dir(e))
        .filter_map(|e| e.ok())
    {
        if !entry.file_type().is_file() {
            continue;
        }

        let p = entry.path();
        let rel_path = match p.strip_prefix(&root) {
            Ok(rel) => rel.to_string_lossy().replace('\\', "/"),
            Err(_) => p.to_string_lossy().replace('\\', "/"),
        };

        if config.is_ignored(Path::new(&rel_path)) {
            continue;
        }

        let lang = match detect_language(p) {
            Some(l) => l,
            None => continue,
        };

        let content = match std::fs::read_to_string(p) {
            Ok(c) => c,
            Err(_) => continue,
        };

        if !content.contains(sym) {
            continue;
        }

        let refs = extract_references_from_code(&content, lang, &rel_path, sym, &def_locations);
        all_refs.extend(refs);
    }

    if all_refs.is_empty() && cached_defs.is_empty() {
        return format!("No references or definitions found for '{symbol_name}' across the codebase.");
    }

    let mut lines = Vec::new();
    lines.push(format!("[REFERENCES] Blast Radius Analysis for '{sym}':"));
    if !cached_defs.is_empty() {
        let def_strs: Vec<String> = cached_defs
            .iter()
            .take(3)
            .map(|d| format!("{}:{} ({})", d.file_path, d.line, d.kind))
            .collect();
        lines.push(format!("• Defined at: {}", def_strs.join(", ")));
    } else {
        lines.push("• Defined at: External / Unindexed symbol".to_string());
    }

    let unique_files: HashSet<&str> = all_refs.iter().map(|r| r.file_path.as_str()).collect();
    lines.push(format!(
        "• Total Usages: {} reference(s) found across {} file(s):",
        all_refs.len(),
        unique_files.len()
    ));
    lines.push("-".repeat(60));

    for (i, r) in all_refs.iter().take(max_results).enumerate() {
        lines.push(format!("{}. [{}] {}:{}", i + 1, r.kind, r.file_path, r.line));
        if !r.snippet.is_empty() {
            lines.push(format!("   Line {}: {}", r.line, r.snippet));
        }
    }

    if all_refs.len() > max_results {
        lines.push(format!("\n... and {} more reference(s) omitted.", all_refs.len() - max_results));
    }

    lines.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_symbols_rust() {
        let code = r#"
pub struct User {
    pub name: String,
}

impl User {
    pub fn new(name: &str) -> Self {
        Self { name: name.to_string() }
    }
}

pub fn greet() {
    println!("Hello");
}
"#;
        let syms = extract_symbols_from_code(code, SupportedLanguage::Rust, "src/user.rs");
        assert!(syms.iter().any(|s| s.name == "User" && s.kind == "struct"));
        assert!(syms.iter().any(|s| s.name == "new" && s.kind == "method"));
        assert!(syms.iter().any(|s| s.name == "greet" && s.kind == "function"));
    }

    #[test]
    fn test_extract_references_python() {
        let code = r#"
from auth import login_user

def process_login(user):
    token = login_user(user)
    return token
"#;
        let def_locs = HashSet::new();
        let refs = extract_references_from_code(code, SupportedLanguage::Python, "app.py", "login_user", &def_locs);
        assert_eq!(refs.len(), 2);
        assert!(refs.iter().any(|r| r.kind == ReferenceKind::Import));
        assert!(refs.iter().any(|r| r.kind == ReferenceKind::Call));
    }

    #[test]
    fn test_find_symbol_global_repo() {
        let temp = tempfile::tempdir().unwrap();
        let file = temp.path().join("service.rs");
        std::fs::write(&file, "pub struct PaymentService;\nimpl PaymentService {\n    pub fn pay() {}\n}\n").unwrap();

        let result = find_symbol_global("PaymentService", temp.path(), false, 10);
        assert!(result.contains("PaymentService"));
        assert!(result.contains("service.rs"));
    }
}
