"""Token-Saver persistent telemetry and statistics tracking.

Stores cumulative token and financial savings in ~/.token-saver/telemetry.json
so metrics persist across all sessions, commands, and MCP calls.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


def _get_storage_path() -> Path:
    """Return the cross-platform path to the telemetry storage file."""
    home = Path.home()
    data_dir = home / ".token-saver"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "telemetry.json"


@dataclass
class TelemetryData:
    """Cumulative metrics storage schema."""

    total_original_tokens: int = 0
    total_optimized_tokens: int = 0
    total_tokens_saved: int = 0
    total_commands_filtered: int = 0
    total_files_cached: int = 0
    total_skeletons_generated: int = 0
    total_repo_maps_generated: int = 0
    first_used_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_used_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def savings_pct(self) -> float:
        if self.total_original_tokens == 0:
            return 0.0
        return (self.total_tokens_saved / self.total_original_tokens) * 100

    @property
    def estimated_dollars_saved(self) -> float:
        # Industry standard blended input rate of $3.00 per 1M tokens (Claude 3.5 Sonnet / GPT-4o)
        return (self.total_tokens_saved / 1_000_000) * 3.00


class TelemetryTracker:
    """Singleton tracker for recording and querying token savings."""

    def __init__(self) -> None:
        self.file_path = _get_storage_path()
        self.data = self._load()

    def _load(self) -> TelemetryData:
        if not self.file_path.exists():
            return TelemetryData()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                return TelemetryData(**content)
        except Exception:
            return TelemetryData()

    def _save(self) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self.data), f, indent=2)
        except Exception:
            pass  # Non-fatal if telemetry writing fails

    def record_savings(
        self,
        category: str,
        original_tokens: int,
        optimized_tokens: int,
    ) -> None:
        """Record token savings for a specific operation."""
        if original_tokens <= 0:
            return

        saved = max(0, original_tokens - optimized_tokens)
        self.data.total_original_tokens += original_tokens
        self.data.total_optimized_tokens += optimized_tokens
        self.data.total_tokens_saved += saved
        self.data.last_used_at = datetime.utcnow().isoformat()

        if category == "command":
            self.data.total_commands_filtered += 1
        elif category == "cache":
            self.data.total_files_cached += 1
        elif category == "skeleton":
            self.data.total_skeletons_generated += 1
        elif category == "repo_map":
            self.data.total_repo_maps_generated += 1

        self._save()

    def reset(self) -> None:
        """Reset all telemetry metrics."""
        self.data = TelemetryData()
        self._save()

    def render_dashboard(self) -> str:
        """Format an ANSI/Unicode terminal dashboard of cumulative metrics."""
        d = self.data
        dollars = f"${d.estimated_dollars_saved:.2f}"
        pct = f"%{d.savings_pct:.1f}"

        orig_str = f"{d.total_original_tokens:,}"
        opt_str = f"{d.total_optimized_tokens:,}"
        saved_str = f"{d.total_tokens_saved:,}"

        lines = [
            "┌────────────────────────────────────────────────────────────────────────┐",
            "│ 🔋 TOKEN-SAVER TELEMETRY & SAVINGS DASHBOARD                           │",
            "├────────────────────────────────────────────────────────────────────────┤",
            f"│  Total Tokens Saved:       {saved_str:<18} ({pct} reduction)          │",
            f"│  Estimated Money Saved:    {dollars:<18} (at $3.00/1M rate)         │",
            "├────────────────────────────────────────────────────────────────────────┤",
            f"│  Raw Context Processed:    {orig_str:<18} tokens                      │",
            f"│  Optimized Sent to Model:  {opt_str:<18} tokens                      │",
            "├────────────────────────────────────────────────────────────────────────┤",
            f"│  Commands Filtered:        {d.total_commands_filtered:<18} executions                  │",
            f"│  File Cache Hits & Diffs:  {d.total_files_cached:<18} operations                  │",
            f"│  AST Skeletons Generated:  {d.total_skeletons_generated:<18} files                       │",
            f"│  Repo Maps Computed:       {d.total_repo_maps_generated:<18} times                       │",
            "└────────────────────────────────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)


# Global singleton instance
tracker = TelemetryTracker()
