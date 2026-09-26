from __future__ import annotations

import subprocess

from token_saver.filters.ansi import strip_ansi
from token_saver.filters.build_tools import detect_and_filter_build
from token_saver.filters.git import filter_git_output
from token_saver.filters.test_runners import detect_and_filter_tests
from token_saver.utils.token_counter import estimate_tokens

MAX_STREAM_BYTES = 2 * 1024 * 1024  # 2MB runaway output buffer ceiling
STREAM_HEAD_BYTES = 1024 * 1024  # Keep first 1MB
STREAM_TAIL_BYTES = 512 * 1024  # Keep last 512KB


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
    raw_output = raw_output or ""
    # Memory ceiling guard: protect host process against runaway infinite output streams
    if len(raw_output) > MAX_STREAM_BYTES:
        truncated_count = len(raw_output) - (STREAM_HEAD_BYTES + STREAM_TAIL_BYTES)
        raw_output = (
            raw_output[:STREAM_HEAD_BYTES]
            + f"\n\n... [Token-Saver Stream Guard: Truncated {truncated_count:,} bytes of runaway output to protect memory] ...\n\n"
            + raw_output[-STREAM_TAIL_BYTES:]
        )

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

    # Fallback Safety Guard:
    # If the command failed (exit_code != 0), guarantee critical error context is never lost.
    if exit_code != 0:
        error_keywords = (
            "traceback",
            "error",
            "failed",
            "exception",
            "fatal",
            "panic",
            "cannot",
            "syntaxerror",
            "importerror",
        )
        raw_has_error = any(kw in clean_output.lower() for kw in error_keywords)
        filtered_has_error = any(kw in filtered.lower() for kw in error_keywords)

        if (raw_has_error and not filtered_has_error) or not filtered.strip():
            filtered = clean_output.strip() + "\n[Token-Saver: Preserved full error context due to non-zero exit code]"

    if not filtered.strip() and clean_output.strip():
        filtered = clean_output.strip()

    orig_tokens = estimate_tokens(raw_output)
    new_tokens = estimate_tokens(filtered)
    pct = 0
    if orig_tokens > 0:
        pct = int((orig_tokens - new_tokens) / orig_tokens * 100)

    footer = f"\n[Token-Saver: {orig_tokens} -> {new_tokens} tokens ({pct}% saved)]"
    if orig_tokens > new_tokens:
        try:
            from token_saver.telemetry.stats import tracker

            tracker.record_savings("command", orig_tokens, new_tokens)
        except Exception:
            pass
    return filtered + footer


def register_output_pruner_tools(mcp):
    @mcp.tool()
    def run_command_smart(
        command: str,
        cwd: str = ".",
        timeout: int = 120,
        background: bool = False,
    ) -> str:
        """Executes a shell command and returns intelligently filtered output.
        Use this tool instead of raw shell commands when you want to minimize token usage
        from verbose CLI outputs like tests, builds, and package managers.

        Set background=True to launch dev servers, daemons, or long-running watchers
        without blocking the agent.
        """
        if background:
            try:
                proc = subprocess.Popen(
                    command,
                    cwd=cwd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return f"[BACKGROUND PROCESS LAUNCHED] PID: {proc.pid} | Command: {command}"
            except Exception as e:
                return f"Error launching background command: {e}"

        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                capture_output=True,
                timeout=timeout,
            )
            stdout_str = (result.stdout or b"").decode("utf-8", errors="replace")
            stderr_str = (result.stderr or b"").decode("utf-8", errors="replace")
            raw_output = f"{stdout_str}\n{stderr_str}".strip() if stderr_str else stdout_str
            exit_code = result.returncode
            filtered = filter_output_logic(raw_output, output_type="auto", exit_code=exit_code)
            return f"Exit Code: {exit_code}\n" + filtered
        except subprocess.TimeoutExpired as e:
            stdout_text = (
                e.stdout
                if isinstance(e.stdout, str)
                else (e.stdout.decode("utf-8", errors="replace") if e.stdout else "")
            )
            stderr_text = (
                e.stderr
                if isinstance(e.stderr, str)
                else (e.stderr.decode("utf-8", errors="replace") if e.stderr else "")
            )
            raw_output = f"{stdout_text}\n{stderr_text}".strip()
            filtered = filter_output_logic(raw_output, output_type="auto", exit_code=-1)
            return f"Command timed out after {timeout}s\n" + filtered
        except Exception as e:
            return f"Error executing command: {str(e)}"

    @mcp.tool()
    def filter_output(raw_output: str, output_type: str = "auto") -> str:
        """Filters raw text output to save tokens.
        output_type can be: "auto", "pytest", "jest", "npm", "cargo", "git", "generic".
        Useful when you already have output from another source.
        """
        return filter_output_logic(raw_output, output_type)
