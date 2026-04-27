"""
Backward-compatibility shim.
All actual implementations live in ui_helpers.py
This file just re-exports everything so old imports don't break.
"""
from pages_loha.ui_helpers import (
    page_header,
    stat_card,
    panel_open,
    panel_close,
    insight_card,
    subject_perf_bars,
    subject_perf_bars as subject_perf_html,   # renamed alias
    weak_warning,
    subject_grid,
    schedule_slots_html,
    heatmap_html,
    COLS,
    ICOS,
)

__all__ = [
    "page_header", "stat_card", "panel_open", "panel_close",
    "insight_card", "subject_perf_bars", "subject_perf_html",
    "weak_warning", "subject_grid", "schedule_slots_html",
    "heatmap_html", "COLS", "ICOS",
]