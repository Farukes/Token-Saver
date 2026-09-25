"""Token-Saver On-Demand UI & Control Dashboard.

Provides a lightweight, zero-background-RAM dashboard for managing IDE integrations,
viewing real-time token/financial savings, and toggling engine safeguards.
"""

from __future__ import annotations

from token_saver.ui.server import start_ui_server

__all__ = ["start_ui_server"]
