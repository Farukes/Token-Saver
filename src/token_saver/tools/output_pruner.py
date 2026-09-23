from __future__ import annotations
import subprocess

from token_saver.filters.ansi import strip_ansi
from token_saver.filters.test_runners import detect_and_filter_tests
from token_saver.filters.build_tools import detect_and_filter_build
from token_saver.filters.git import filter_git_output
from token_saver.utils.token_counter import estimate_tokens

def filter_generic(output: str) -> str:
    return output

def auto_filter(output: str, exit_code: int = 0) -> str:
    test_filtered = detect_and_filter_tests(output)
    if test_filtered is not None:
        return test_filtered
        
    build_filtered = detect_and_filter_build(output)
    if build_filtered is not None:
        return build_filtered
        
    if "git " in output[:100] or "commit" in output or "branch" in output:
        return filter_git_output(output)
        
    return filter_generic(output)

def filter_output_logic(raw_output: str, output_type: str = "auto", exit_code: int = 0) -> str:
    clean_output = strip_ansi(raw_output)
    
    if output_type == "auto":
        filtered = auto_filter(clean_output, exit_code)
    elif output_type == "pytest":
        from token_saver.filters.test_runners import filter_pytest
        filtered = filter_pytest(clean_output)
    elif output_type == "jest":
        from token_saver.filters.test_runners import filter_jest_vitest
        filtered = filter_jest_vitest(clean_output)
    elif output_type == "npm":
        from token_saver.filters.build_tools import filter_npm_yarn
        filtered = filter_npm_yarn(clean_output)
    elif output_type == "cargo":
        from token_saver.filters.build_tools import filter_cargo
        filtered = filter_cargo(clean_output)
    elif output_type == "git":
        filtered = filter_git_output(clean_output)
    elif output_type == "generic":
        filtered = filter_generic(clean_output)
    else:
        filtered = clean_output

    orig_tokens = estimate_tokens(raw_output)
    new_tokens = estimate_tokens(filtered)
    pct = 0
    if orig_tokens > 0:
        pct = int((orig_tokens - new_tokens) / orig_tokens * 100)
    
    footer = f"\n[Token-Saver: {orig_tokens} → {new_tokens} tokens ({pct}% saved)]"
    try:
        from token_saver.telemetry.stats import tracker
        tracker.record_savings("command", orig_tokens, new_tokens)
    except Exception:
        pass
    return filtered + footer

def register_output_pruner_tools(mcp):
    @mcp.tool()
    def run_command_smart(command: str, cwd: str = ".") -> str:
        """Executes a shell command and returns intelligently filtered output.
        Use this tool instead of raw shell commands when you want to minimize token usage
        from verbose CLI outputs like tests, builds, and package managers.
        """
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            raw_output = result.stdout + "\n" + result.stderr
            exit_code = result.returncode
            filtered = filter_output_logic(raw_output, output_type="auto", exit_code=exit_code)
            return f"Exit Code: {exit_code}\n" + filtered
        except subprocess.TimeoutExpired as e:
            raw_output = (e.stdout.decode('utf-8') if e.stdout else "") + "\n" + (e.stderr.decode('utf-8') if e.stderr else "")
            filtered = filter_output_logic(raw_output, output_type="auto", exit_code=-1)
            return f"Command timed out after 120s\n" + filtered
        except Exception as e:
            return f"Error executing command: {str(e)}"

    @mcp.tool()
    def filter_output(raw_output: str, output_type: str = "auto") -> str:
        """Filters raw text output to save tokens.
        output_type can be: "auto", "pytest", "jest", "npm", "cargo", "git", "generic".
        Useful when you already have output from another source.
        """
        return filter_output_logic(raw_output, output_type)
