from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from token_saver.telemetry.stats import TelemetryData, TelemetryTracker


def test_telemetry_tracker_record_and_reset(tmp_path: Path):
    test_storage = tmp_path / "telemetry_test.json"

    with patch("token_saver.telemetry.stats._get_storage_path", return_value=test_storage):
        tracker = TelemetryTracker()
        tracker.reset()

        tracker.record_savings("command", 1000, 200)
        assert tracker.data.total_tokens_saved == 800
        assert tracker.data.total_commands_filtered == 1
        assert tracker.data.total_original_tokens == 1000
        assert tracker.data.total_optimized_tokens == 200

        tracker.record_savings("skeleton", 500, 100)
        assert tracker.data.total_tokens_saved == 1200
        assert tracker.data.total_skeletons_generated == 1

        dashboard = tracker.render_dashboard()
        assert "TOKEN-SAVER TELEMETRY" in dashboard
        assert "1,200" in dashboard

        tracker.reset()
        assert tracker.data.total_tokens_saved == 0
        assert tracker.data.total_commands_filtered == 0
