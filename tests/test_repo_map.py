import os
from pathlib import Path

from token_saver.tools.repo_map import get_repo_map, get_directory_tree, extract_symbols

def test_repo_map(tmp_path: Path):
    # Create a temp directory with Python files
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    # File 1: main.py
    main_file = src_dir / "main.py"
    main_file.write_text('''
import os
import sys

def main():
    print("Hello")
    
class App:
    def __init__(self):
        self.name = "Test"
        
    def run(self):
        pass
''')
    
    # File 2: utils.py
    utils_file = src_dir / "utils.py"
    utils_file.write_text('''
def helper():
    return True
''')
    
    # File 3: empty.py
    empty_file = src_dir / "empty.py"
    empty_file.write_text('')
    
    # Test extract symbols indirectly through get_repo_map
    repo_map = get_repo_map(str(tmp_path), max_tokens=10000)
    
    assert "class App" in repo_map
    assert "def run(self)" in repo_map
    assert "def main()" in repo_map
    assert "def helper()" in repo_map
    
    # Test token budget
    small_budget_map = get_repo_map(str(tmp_path), max_tokens=10) # very small budget
    assert "truncating remaining" in small_budget_map or "budget too small" in small_budget_map
    
    # Test focus files
    focus_map = get_repo_map(str(tmp_path), max_tokens=10000, focus_files=["src/utils.py"])
    
    # utils.py should be processed and appear
    assert "src/utils.py" in focus_map.replace("\\", "/")
    
    # Test empty directory
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    empty_map = get_repo_map(str(empty_dir), max_tokens=100)
    assert "0 files" in empty_map
    
    # Test directory tree
    tree = get_directory_tree(str(tmp_path))
    assert "src/" in tree
    assert "main.py" in tree
    assert "utils.py" in tree
    
    # Create a dummy skip dir to test it's skipped
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "skip.py").write_text('def skipped(): pass')
    
    tree_with_skip = get_directory_tree(str(tmp_path))
    assert "node_modules/" not in tree_with_skip
    assert "skip.py" not in tree_with_skip
