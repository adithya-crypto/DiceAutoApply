"""
Dashboard page - Main view with stats and run controls
"""

import flet as ft
import json
import os
from datetime import datetime
from typing import Callable, Dict, Optional
from ..components.widgets import (
    COLORS, create_card, create_button, create_stat_card,
    create_section_title, create_progress_ring, create_job_list_item
)


class DashboardPage(ft.UserControl):
    """Main dashboard with statistics and run controls."""

    def __init__(
        self,
        config: Dict,
        on_run: Callable,
        on_stop: Callable,
        data_dir: str,
        on_view_all: Callable = None,
    ):
        super().__init__()
        self.config = config
        self.on_run = on_run
        self.on_stop = on_stop
        self.data_dir = data_dir
        self.on_view_all = on_view_all
        self.applied_jobs_path = os.path.join(data_dir, "applied_jobs.json")

        # State
        self.is_running_state = False
        self.progress_message = ""
        self.progress_current = 0
        self.progress_total = 0
        self.session_applied = 0

        # Container references for refresh
        self.stats_row = None
        self.run_card = None
        self.recent_jobs_container = None
        self.main_container = None

    def _load_applied_jobs(self) -> Dict:
        """Load applied jobs data."""
        if os.path.exists(self.applied_jobs_path):
            try:
                with open(self.applied_jobs_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"jobs": [], "stats": {"total_applied": 0, "last_run": None}}

    def _get_stats(self) -> Dict:
        """Get application statistics."""
        data = self._load_applied_jobs()
        stats = data.get("stats", {})
        jobs = data.get("jobs", [])

        # Count today's applications
        today = datetime.now().date().isoformat()
        today_count = sum(1 for job in jobs
                        if job.get("applied_at", "").startswith(today))

        return {
            "total_applied": stats.get("total_applied", 0),
            "today_applied": today_count,
            "last_run": stats.get("last_run"),
            "jobs_applied": self.session_applied,
        }

    def _get_recent_jobs(self, limit: int = 5) -> list:
        """Get recent job applications."""
        data = self._load_applied_jobs()
        jobs = data.get("jobs", [])
        return jobs[-limit:][::-1]

    def _build_stats_controls(self) -> list:
        """Build the stat card controls."""
        stats = self._get_stats()
        return [
            ft.Container(
                content=create_stat_card(
                    "Total Applied",
                    str(stats.get("total_applied", 0)),
                    ft.icons.CHECK_CIRCLE,
                    COLORS["success"],
                ),
                expand=True,
            ),
            ft.Container(
                content=create_stat_card(
                    "Today",
                    str(stats.get("today_applied", 0)),
                    ft.icons.TODAY,
                    COLORS["accent"],
                ),
                expand=True,
            ),
            ft.Container(
                content=create_stat_card(
                    "This Session",
                    str(stats.get("jobs_applied", 0)),
                    ft.icons.TRENDING_UP,
                    COLORS["warning"],
                ),
                expand=True,
            ),
        ]

    def _create_stats_row(self) -> ft.Row:
        """Create the statistics cards row."""
        self.stats_row = ft.Row(
            self._build_stats_controls(),
            spacing=16,
        )
        return self.stats_row

    def _create_run_card(self) -> ft.Container:
        """Create the run automation card."""
        if self.is_running_state:
            content = ft.Column(
                [
                    ft.Row(
                        [
                            create_progress_ring(size=40),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Running...",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLORS["text"],
                                    ),
                                    ft.Text(
                                        self.progress_message or "Initializing...",
                                        size=14,
                                        color=COLORS["text_secondary"],
                                    ),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=16,
                    ),
                    ft.Container(height=12),
                    ft.ProgressBar(
                        value=self.progress_current / max(self.progress_total, 1) if self.progress_total > 0 else None,
                        color=COLORS["accent"],
                        bgcolor=COLORS["primary"],
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.Text(
                                f"{self.progress_current} / {self.progress_total} jobs" if self.progress_total > 0 else "",
                                size=12,
                                color=COLORS["text_secondary"],
                            ),
                            ft.Container(expand=True),
                            create_button(
                                "Stop",
                                on_click=self._handle_stop,
                                icon=ft.icons.STOP,
                                primary=False,
                            ),
                        ],
                    ),
                ],
            )
        else:
            stats = self._get_stats()
            last_run = stats.get("last_run", "Never")
            if last_run and last_run != "Never":
                try:
                    dt = datetime.fromisoformat(last_run)
                    last_run = dt.strftime("%b %d, %Y at %I:%M %p")
                except Exception:
                    pass

            content = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.PLAY_CIRCLE, size=48, color=COLORS["accent"]),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Ready to Apply",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLORS["text"],
                                    ),
                                    ft.Text(
                                        f"Last run: {last_run}",
                                        size=14,
                                        color=COLORS["text_secondary"],
                                    ),
                                ],
                                spacing=4,
                            ),
                            ft.Container(expand=True),
                            create_button(
                                "Run Now",
                                on_click=self._handle_run,
                                icon=ft.icons.PLAY_ARROW,
                            ),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
            )

        return create_card(content)

    def _build_recent_jobs_content(self) -> ft.Column:
        """Build the recent jobs content."""
        jobs = self._get_recent_jobs(5)

        if not jobs:
            job_content = ft.Column(
                [
                    ft.Icon(ft.icons.INBOX, size=48, color=COLORS["text_secondary"]),
                    ft.Text(
                        "No applications yet",
                        size=14,
                        color=COLORS["text_secondary"],
                    ),
                    ft.Text(
                        "Click 'Run Now' to start applying",
                        size=12,
                        color=COLORS["text_secondary"],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            )
        else:
            job_content = ft.Column(
                [create_job_list_item(job) for job in jobs],
                spacing=0,
            )

        return ft.Column(
            [
                ft.Row(
                    [
                        create_section_title("Recent Applications"),
                        ft.Container(expand=True),
                        ft.TextButton(
                            "View All",
                            on_click=self._handle_view_all,
                            style=ft.ButtonStyle(color=COLORS["accent"]),
                        ),
                    ],
                ),
                ft.Container(height=12),
                job_content,
            ],
        )

    def _create_recent_jobs(self) -> ft.Container:
        """Create recent jobs list."""
        self.recent_jobs_container = create_card(self._build_recent_jobs_content())
        return self.recent_jobs_container

    def _handle_view_all(self, e):
        """Handle View All button click."""
        if self.on_view_all:
            self.on_view_all()

    def _handle_run(self, e):
        """Handle run button click."""
        self.is_running_state = True
        self.session_applied = 0
        self.progress_message = "Starting..."
        self.progress_current = 0
        self.progress_total = 0
        self.update()
        if self.on_run:
            self.on_run()

    def _handle_stop(self, e):
        """Handle stop button click."""
        if self.on_stop:
            self.on_stop()
        self.is_running_state = False
        self.update()

    def set_running(self, running: bool):
        """Set running state externally."""
        self.is_running_state = running
        if not running:
            self.progress_message = ""
            self.progress_current = 0
            self.progress_total = 0

    def update_progress(self, message: str, current: int, total: int):
        """Update progress display."""
        self.progress_message = message
        self.progress_current = current
        self.progress_total = total
        self.session_applied = current

    def refresh(self):
        """Refresh the dashboard data and UI."""
        # Rebuild the stats row with fresh data
        if self.stats_row:
            self.stats_row.controls = self._build_stats_controls()
            self.stats_row.update()

        # Rebuild the recent jobs container with fresh data
        if self.recent_jobs_container:
            self.recent_jobs_container.content = self._build_recent_jobs_content()
            self.recent_jobs_container.update()

    def build(self):
        return ft.Container(
            content=ft.Column(
                [
                    # Header
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        "Dashboard",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLORS["text"],
                                    ),
                                    ft.Text(
                                        "Monitor your job applications",
                                        size=14,
                                        color=COLORS["text_secondary"],
                                    ),
                                ],
                                spacing=4,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.REFRESH,
                                icon_color=COLORS["text_secondary"],
                                on_click=lambda e: self.refresh(),
                                tooltip="Refresh",
                            ),
                        ],
                    ),
                    ft.Container(height=24),
                    # Stats row
                    self._create_stats_row(),
                    ft.Container(height=24),
                    # Run card
                    self._create_run_card(),
                    ft.Container(height=24),
                    # Recent jobs
                    self._create_recent_jobs(),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=30,
            expand=True,
        )
