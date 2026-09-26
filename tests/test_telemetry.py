from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from token_saver.telemetry.stats import TelemetryTracker


def test_telemetry_tracker_record_and_reset(tmp_path: Path):
    test_storage = tmp_path / "telemetry_test.json"

    with patch("token_saver.telemetry.stats._get_storage_path", return_value=test_storage):
        tracker = TelemetryTracker()
        tracker.reset()

        tracker.record_savings("command", 1000, 200)
        assert tracker.data.total_tokens_saved == 800
        assert tracker.data.total_commands_filtered == 1
        assert tracker.data.command.saved == 800
        assert tracker.data.command.count == 1

        tracker.record_savings("skeleton", 500, 100)
        assert tracker.data.total_tokens_saved == 1200
        assert tracker.data.total_skeletons_generated == 1
        assert tracker.data.skeleton.saved == 400
        assert tracker.data.skeleton.count == 1

        dashboard = tracker.render_dashboard()
        assert "TOKEN-SAVER" in dashboard
        assert "1,200" in dashboard
        assert "AST Skeletonizer" in dashboard
        assert "Terminal Pruner" in dashboard
        assert "L2 CACHE DISK USAGE" in dashboard

        tracker.reset()
        assert tracker.data.total_tokens_saved == 0
        assert tracker.data.total_commands_filtered == 0
        assert tracker.data.skeleton.saved == 0


def test_telemetry_cross_instance_reset_sync(tmp_path: Path):
    import time

    test_storage = tmp_path / "telemetry_cross_test.json"

    with patch("token_saver.telemetry.stats._get_storage_path", return_value=test_storage):
        tracker_a = TelemetryTracker()
        tracker_a.reset()
        tracker_a.record_savings("command", 1000, 200)
        assert tracker_a.data.total_tokens_saved == 800

        # Simulate second process (e.g. UI server or CLI)
        tracker_b = TelemetryTracker()
        assert tracker_b.data.total_tokens_saved == 800

        # Process B resets telemetry
        time.sleep(0.02)
        tracker_b.reset()
        assert tracker_b.data.total_tokens_saved == 0

        # Process A records a new operation - must NOT resurrect the old 800 tokens!
        time.sleep(0.02)
        tracker_a.record_savings("skeleton", 500, 100)
        assert tracker_a.data.total_tokens_saved == 400
        assert tracker_b.data.total_tokens_saved == 400
