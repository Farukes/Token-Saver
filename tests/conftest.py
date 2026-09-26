"""Test configuration for TokenJar."""

import warnings

# Suppress tree-sitter FutureWarning about deprecated Language() API
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")
