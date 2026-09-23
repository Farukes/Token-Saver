"""Test configuration for Token-Saver."""

import warnings

# Suppress tree-sitter FutureWarning about deprecated Language() API
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")
