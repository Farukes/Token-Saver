from __future__ import annotations

from token_saver.cache.session_cache import SessionCache


def test_semantic_diff_focus():
    old_py = """
def authenticate(user, password):
    return user == "admin"

def logout():
    pass
"""
    new_py = """
def authenticate(user, password):
    # added security check
    return user == "admin" and len(password) > 8

def logout():
    pass
"""
    diff_output = SessionCache._compute_diff(old_py, new_py, "auth_service.py")
    assert "[DIFF]" in diff_output
    assert "SEMANTIC FOCUS: authenticate" in diff_output
    assert "len(password) > 8" in diff_output
