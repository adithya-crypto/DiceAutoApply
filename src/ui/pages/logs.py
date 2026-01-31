"""
Logs page - Session-based job application viewer
"""

import flet as ft
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from ..components.widgets import COLORS, create_card, create_button, create_section_title


class LogsPage(ft.UserControl):
    """Logs page for viewing job applications by session."""

    def __init__(self, data_dir: Optional[str] = None):
        super().__init__()
        self.data_dir = data_dir or str(Path(__file__).parent.parent.parent.parent / "data")
        self.applied_jobs_path = os.path.join(self.data_dir, "applied_jobs.json")
        self.sessions: List[Dict] = []  # List of sessions with jobs
        self.selected_session_index = 0
        self.jobs_column = None
        self.sessions_row = None  # Container for session chips

    def _load_sessions(self):
        """Load and organize jobs into sessions."""
        self.sessions = []

        if not os.path.exists(self.applied_jobs_path):
            return

        try:
            with open(self.applied_jobs_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return

        jobs = data.get("jobs", [])
        if not jobs:
            return

        # Group jobs by date
        sessions_dict = {}
        for job in jobs:
            applied_at = job.get("applied_at", "")
            if applied_at:
                try:
                    dt = datetime.fromisoformat(applied_at)
                    date_key = dt.strftime("%Y-%m-%d")
                    if date_key not in sessions_dict:
                        sessions_dict[date_key] = {
                            "date": date_key,
                            "display_date": dt.strftime("%B %d, %Y"),
                            "jobs": []
                        }
                    sessions_dict[date_key]["jobs"].append(job)
                except Exception:
                    pass

        # Convert to list and sort by date (most recent first)
        self.sessions = sorted(sessions_dict.values(), key=lambda x: x["date"], reverse=True)

    def _get_status_color(self, status: str) -> str:
        """Get color for job status."""
        status_colors = {
            "applied": COLORS["success"],
            "likely_applied": COLORS["warning"],
            "partial": COLORS["error"],
            "failed": COLORS["error"],
        }
        return status_colors.get(status, COLORS["text_secondary"])

    def _create_job_row(self, job: Dict) -> ft.Container:
        """Create a single job row widget."""
        status = job.get("status", "unknown")
        applied_at = job.get("applied_at", "")
        time_str = ""
        if applied_at:
            try:
                dt = datetime.fromisoformat(applied_at)
                time_str = dt.strftime("%I:%M %p")
            except Exception:
                pass

        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        time_str,
                        size=12,
                        color=COLORS["text_secondary"],
                        width=80,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                job.get("title", "Unknown Title")[:50],
                                size=13,
                                color=COLORS["text"],
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Text(
                                job.get("company", "Unknown Company"),
                                size=11,
                                color=COLORS["text_secondary"],
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text(
                            status.replace("_", " ").title(),
                            size=11,
                            color=COLORS["text"],
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=4,
                        bgcolor=self._get_status_color(status),
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.with_opacity(0.1, COLORS["text"]))),
        )

    def _update_jobs_display(self):
        """Update the jobs display for selected session."""
        if not self.jobs_column:
            return

        if not self.sessions or self.selected_session_index >= len(self.sessions):
            self.jobs_column.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.INBOX, size=48, color=COLORS["text_secondary"]),
                            ft.Text(
                                "No jobs in this session",
                                size=14,
                                color=COLORS["text_secondary"],
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            ]
        else:
            session = self.sessions[self.selected_session_index]
            self.jobs_column.controls = [
                self._create_job_row(job) for job in reversed(session["jobs"])
            ]

        if self.page:
            self.jobs_column.update()

    def _handle_session_change(self, index: int):
        """Handle session selection change."""
        self.selected_session_index = index
        self._update_sessions_display()
        self._update_jobs_display()

    def _update_sessions_display(self):
        """Update the session chips to reflect current selection."""
        if not self.sessions_row or not self.sessions_row.content:
            return

        # Rebuild session chips with new selection
        session_chips = [
            self._create_session_chip(session, i)
            for i, session in enumerate(self.sessions)
        ]
        self.sessions_row.content.controls = session_chips
        self.sessions_row.update()

    def _create_session_chip(self, session: Dict, index: int) -> ft.Container:
        """Create a session selection chip."""
        is_active = self.selected_session_index == index
        job_count = len(session["jobs"])

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        session["display_date"],
                        size=12,
                        color=COLORS["text"] if is_active else COLORS["text_secondary"],
                        weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL,
                    ),
                    ft.Text(
                        f"{job_count} job{'s' if job_count != 1 else ''}",
                        size=10,
                        color=COLORS["accent"] if is_active else COLORS["text_secondary"],
                    ),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=8,
            bgcolor=ft.colors.with_opacity(0.2, COLORS["accent"]) if is_active else ft.colors.with_opacity(0.1, COLORS["text"]),
            border=ft.border.all(1, COLORS["accent"] if is_active else "transparent"),
            on_click=lambda e, i=index: self._handle_session_change(i),
            ink=True,
        )

    def add_log(self, level: str, message: str):
        """Legacy method for compatibility - just refresh data."""
        self._load_sessions()
        if self.page:
            self.update()

    def _create_empty_state(self) -> ft.Container:
        """Create empty state widget."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.INBOX, size=64, color=COLORS["text_secondary"]),
                    ft.Text(
                        "No Job Applications Yet",
                        size=18,
                        weight=ft.FontWeight.W_500,
                        color=COLORS["text_secondary"],
                    ),
                    ft.Text(
                        "Run the automation to start applying for jobs",
                        size=14,
                        color=COLORS["text_secondary"],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=60,
            alignment=ft.alignment.center,
        )

    def build(self):
        # Load sessions data
        self._load_sessions()

        self.jobs_column = ft.Column(
            controls=[],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        # Build session chips
        session_chips = []
        if self.sessions:
            for i, session in enumerate(self.sessions):
                session_chips.append(self._create_session_chip(session, i))

        # Get stats
        total_jobs = sum(len(s["jobs"]) for s in self.sessions)
        total_sessions = len(self.sessions)

        return ft.Container(
            content=ft.Column(
                [
                    # Header
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        "Job Applications",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLORS["text"],
                                    ),
                                    ft.Text(
                                        f"{total_jobs} total applications across {total_sessions} session{'s' if total_sessions != 1 else ''}",
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
                                on_click=lambda e: self._refresh(),
                                tooltip="Refresh",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Container(height=20),
                    # Content
                    self._build_content(session_chips),
                ],
            ),
            padding=30,
            expand=True,
        )

    def _build_content(self, session_chips: List) -> ft.Control:
        """Build the main content area."""
        if not self.sessions:
            return self._create_empty_state()

        # Sessions row (scrollable) - store reference for updates
        self.sessions_row = ft.Container(
            content=ft.Row(
                session_chips,
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.only(bottom=16),
        )

        # Jobs table
        jobs_card = create_card(
            ft.Column(
                [
                    # Header row
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("Time", size=12, color=COLORS["text_secondary"], width=80),
                                ft.Text("Job Details", size=12, color=COLORS["text_secondary"], expand=True),
                                ft.Text("Status", size=12, color=COLORS["text_secondary"], width=80),
                            ],
                            spacing=12,
                        ),
                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                        bgcolor=ft.colors.with_opacity(0.3, COLORS["primary"]),
                    ),
                    # Jobs list
                    ft.Container(
                        content=self.jobs_column,
                        bgcolor=ft.colors.with_opacity(0.5, COLORS["background"]),
                        height=400,
                    ),
                ],
                spacing=0,
            ),
            padding=0,
        )

        # Populate jobs column (don't call update() yet - control not on page)
        if self.sessions and self.selected_session_index < len(self.sessions):
            session = self.sessions[self.selected_session_index]
            self.jobs_column.controls = [
                self._create_job_row(job) for job in reversed(session["jobs"])
            ]

        return ft.Column(
            [
                ft.Text("Sessions", size=14, weight=ft.FontWeight.W_500, color=COLORS["text"]),
                ft.Container(height=8),
                self.sessions_row,
                ft.Container(height=8),
                jobs_card,
            ],
            expand=True,
        )

    def _refresh(self):
        """Refresh the page data."""
        self._load_sessions()
        self.update()

    def did_mount(self):
        """Called when the control is added to the page."""
        self._load_sessions()
        self._update_jobs_display()
