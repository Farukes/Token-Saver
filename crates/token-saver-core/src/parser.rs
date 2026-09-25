//! Tree-sitter Language Parser & Grammar Management for Token-Saver Core.

use std::path::Path;
use tree_sitter::{Language, Parser, Tree};

/// Supported language identifiers across 15 programming and data languages.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SupportedLanguage {
    Python,
    Rust,
    JavaScript,
    TypeScript,
    Go,
    C,
    Cpp,
    Java,
    CSharp,
    Ruby,
    Php,
    Bash,
    Html,
    Css,
    Json,
}

impl SupportedLanguage {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Python => "python",
            Self::Rust => "rust",
            Self::JavaScript => "javascript",
            Self::TypeScript => "typescript",
            Self::Go => "go",
            Self::C => "c",
            Self::Cpp => "cpp",
            Self::Java => "java",
            Self::CSharp => "c_sharp",
            Self::Ruby => "ruby",
            Self::Php => "php",
            Self::Bash => "bash",
            Self::Html => "html",
            Self::Css => "css",
            Self::Json => "json",
        }
    }

    pub fn tree_sitter_language(&self) -> Language {
        match self {
            Self::Python => tree_sitter_python::LANGUAGE.into(),
            Self::Rust => tree_sitter_rust::LANGUAGE.into(),
            Self::JavaScript => tree_sitter_javascript::LANGUAGE.into(),
            Self::TypeScript => tree_sitter_typescript::LANGUAGE_TYPESCRIPT.into(),
            Self::Go => tree_sitter_go::LANGUAGE.into(),
            Self::C => tree_sitter_c::LANGUAGE.into(),
            Self::Cpp => tree_sitter_cpp::LANGUAGE.into(),
            Self::Java => tree_sitter_java::LANGUAGE.into(),
            Self::CSharp => tree_sitter_c_sharp::LANGUAGE.into(),
            Self::Ruby => tree_sitter_ruby::LANGUAGE.into(),
            Self::Php => tree_sitter_php::LANGUAGE_PHP.into(),
            Self::Bash => tree_sitter_bash::LANGUAGE.into(),
            Self::Html => tree_sitter_html::LANGUAGE.into(),
            Self::Css => tree_sitter_css::LANGUAGE.into(),
            Self::Json => tree_sitter_json::LANGUAGE.into(),
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
        "c" | "h" => Some(SupportedLanguage::C),
        "cpp" | "cc" | "cxx" | "hpp" | "hxx" => Some(SupportedLanguage::Cpp),
        "java" => Some(SupportedLanguage::Java),
        "cs" => Some(SupportedLanguage::CSharp),
        "rb" => Some(SupportedLanguage::Ruby),
        "php" | "phtml" => Some(SupportedLanguage::Php),
        "sh" | "bash" | "zsh" => Some(SupportedLanguage::Bash),
        "html" | "htm" => Some(SupportedLanguage::Html),
        "css" | "scss" => Some(SupportedLanguage::Css),
        "json" => Some(SupportedLanguage::Json),
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
    fn test_parse_c_sharp() {
        let code = "class Program { static void Main() {} }\n";
        let tree = parse_code(code, SupportedLanguage::CSharp).expect("C# parse should succeed");
        assert_eq!(tree.root_node().kind(), "compilation_unit");
    }

    #[test]
    fn test_parse_ruby() {
        let code = "def hello\n  puts 'hello'\nend\n";
        let tree = parse_code(code, SupportedLanguage::Ruby).expect("Ruby parse should succeed");
        assert_eq!(tree.root_node().kind(), "program");
    }

    #[test]
    fn test_parse_php() {
        let code = "<?php function hello() { echo 'hi'; } ?>";
        let tree = parse_code(code, SupportedLanguage::Php).expect("PHP parse should succeed");
        assert_eq!(tree.root_node().kind(), "program");
    }

    #[test]
    fn test_parse_bash() {
        let code = "#!/bin/bash\nfunction run() { echo 1; }\n";
        let tree = parse_code(code, SupportedLanguage::Bash).expect("Bash parse should succeed");
        assert_eq!(tree.root_node().kind(), "program");
    }
}
