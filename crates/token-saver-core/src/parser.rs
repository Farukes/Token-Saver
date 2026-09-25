//! Tree-sitter Language Parser & Grammar Management for Token-Saver Core.

use std::path::Path;
use tree_sitter::{Language, Parser, Tree};

/// Supported language identifiers.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SupportedLanguage {
    Python,
    Rust,
    JavaScript,
    TypeScript,
    Go,
}

impl SupportedLanguage {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Python => "python",
            Self::Rust => "rust",
            Self::JavaScript => "javascript",
            Self::TypeScript => "typescript",
            Self::Go => "go",
        }
    }

    pub fn tree_sitter_language(&self) -> Language {
        match self {
            Self::Python => tree_sitter_python::LANGUAGE.into(),
            Self::Rust => tree_sitter_rust::LANGUAGE.into(),
            Self::JavaScript => tree_sitter_javascript::LANGUAGE.into(),
            Self::TypeScript => tree_sitter_typescript::LANGUAGE_TYPESCRIPT.into(),
            Self::Go => tree_sitter_go::LANGUAGE.into(),
        }
    }

    pub fn new_parser(&self) -> Option<Parser> {
        let mut parser = Parser::new();
        if parser.set_language(&self.tree_sitter_language()).is_ok() {
            Some(parser)
        } else {
            None
        }
    }
}

/// Detects language from file extension or path.
pub fn detect_language<P: AsRef<Path>>(path: P) -> Option<SupportedLanguage> {
    let p = path.as_ref();
    let ext = p.extension()?.to_str()?.to_lowercase();
    match ext.as_str() {
        "py" | "pyi" => Some(SupportedLanguage::Python),
        "rs" => Some(SupportedLanguage::Rust),
        "js" | "mjs" | "cjs" | "jsx" => Some(SupportedLanguage::JavaScript),
        "ts" | "mts" | "cts" | "tsx" => Some(SupportedLanguage::TypeScript),
        "go" => Some(SupportedLanguage::Go),
        _ => None,
    }
}

/// Parses source code with Tree-sitter for the given language.
pub fn parse_code(source: &str, lang: SupportedLanguage) -> Option<Tree> {
    let mut parser = lang.new_parser()?;
    parser.parse(source, None)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_python() {
        let code = "def hello(name: str):\n    return f'Hello, {name}'\n";
        let tree = parse_code(code, SupportedLanguage::Python).expect("Python parse should succeed");
        assert_eq!(tree.root_node().kind(), "module");
    }

    #[test]
    fn test_parse_rust() {
        let code = "fn hello(name: &str) -> String {\n    format!(\"Hello, {}\", name)\n}\n";
        let tree = parse_code(code, SupportedLanguage::Rust).expect("Rust parse should succeed");
        assert_eq!(tree.root_node().kind(), "source_file");
    }

    #[test]
    fn test_parse_javascript() {
        let code = "function hello(name) {\n    return 'Hello ' + name;\n}\n";
        let tree = parse_code(code, SupportedLanguage::JavaScript).expect("JS parse should succeed");
        assert_eq!(tree.root_node().kind(), "program");
    }

    #[test]
    fn test_parse_typescript() {
        let code = "function hello(name: string): string {\n    return `Hello ${name}`;\n}\n";
        let tree = parse_code(code, SupportedLanguage::TypeScript).expect("TS parse should succeed");
        assert_eq!(tree.root_node().kind(), "program");
    }

    #[test]
    fn test_parse_go() {
        let code = "package main\nfunc hello(name string) string {\n    return \"Hello \" + name\n}\n";
        let tree = parse_code(code, SupportedLanguage::Go).expect("Go parse should succeed");
        assert_eq!(tree.root_node().kind(), "source_file");
    }
}
