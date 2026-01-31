"""
Settings page - Configure application preferences
"""

import flet as ft
from typing import Callable, Dict
from ..components.widgets import (
    COLORS, create_card, create_button, create_text_field,
    create_checkbox, create_section_title
)


class SettingsPage(ft.UserControl):
    """Settings page for configuring preferences."""

    def __init__(self, config: Dict, on_save: Callable[[Dict], None]):
        super().__init__()
        self.config = config
        self.on_save = on_save

        # Initialize form values from config
        self.email = config.get("login", {}).get("email", "")
        self.password = config.get("login", {}).get("password", "")
        self.job_title = config.get("filters", {}).get("job_title", "Data Engineer")

        remote_options = config.get("filters", {}).get("remote_option", [])
        self.remote_enabled = "Remote" in remote_options
        self.hybrid_enabled = "Hybrid" in remote_options
        self.onsite_enabled = "On-Site" in remote_options

        emp_types = config.get("filters", {}).get("employment_type", [])
        self.contract_enabled = "Contract" in emp_types
        self.fulltime_enabled = "Full-time" in emp_types

        self.max_jobs = str(config.get("preferences", {}).get("max_jobs", 50))
        self.headless = config.get("preferences", {}).get("headless", False)

    def _create_credentials_section(self) -> ft.Container:
        """Create credentials settings section."""
        return create_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.LOCK, color=COLORS["accent"], size=24),
                            create_section_title("Dice.com Credentials"),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=16),
                    create_text_field(
                        label="Email",
                        value=self.email,
                        on_change=lambda e: setattr(self, "email", e.control.value),
                        width=400,
                    ),
                    ft.Container(height=12),
                    create_text_field(
                        label="Password",
                        value=self.password,
                        password=True,
                        on_change=lambda e: setattr(self, "password", e.control.value),
                        width=400,
                    ),
                ],
            )
        )

    def _create_filters_section(self) -> ft.Container:
        """Create job filters settings section."""
        return create_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.FILTER_ALT, color=COLORS["accent"], size=24),
                            create_section_title("Job Filters"),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=16),
                    create_text_field(
                        label="Job Title / Role",
                        value=self.job_title,
                        on_change=lambda e: setattr(self, "job_title", e.control.value),
                        width=400,
                    ),
                    ft.Container(height=16),
                    ft.Text("Work Type", size=14, weight=ft.FontWeight.W_500, color=COLORS["text"]),
                    ft.Row(
                        [
                            create_checkbox(
                                "Remote",
                                value=self.remote_enabled,
                                on_change=lambda e: setattr(self, "remote_enabled", e.control.value),
                            ),
                            create_checkbox(
                                "Hybrid",
                                value=self.hybrid_enabled,
                                on_change=lambda e: setattr(self, "hybrid_enabled", e.control.value),
                            ),
                            create_checkbox(
                                "On-Site",
                                value=self.onsite_enabled,
                                on_change=lambda e: setattr(self, "onsite_enabled", e.control.value),
                            ),
                        ],
                        spacing=20,
                    ),
                    ft.Container(height=12),
                    ft.Text("Employment Type", size=14, weight=ft.FontWeight.W_500, color=COLORS["text"]),
                    ft.Row(
                        [
                            create_checkbox(
                                "Contract",
                                value=self.contract_enabled,
                                on_change=lambda e: setattr(self, "contract_enabled", e.control.value),
                            ),
                            create_checkbox(
                                "Full-time",
                                value=self.fulltime_enabled,
                                on_change=lambda e: setattr(self, "fulltime_enabled", e.control.value),
                            ),
                        ],
                        spacing=20,
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.Icon(ft.icons.CHECK_CIRCLE, size=16, color=COLORS["success"]),
                            ft.Text(
                                "Easy Apply filter is always enabled",
                                size=12,
                                color=COLORS["text_secondary"],
                                italic=True,
                            ),
                        ],
                        spacing=8,
                    ),
                ],
            )
        )

    def _create_preferences_section(self) -> ft.Container:
        """Create application preferences section."""
        return create_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.TUNE, color=COLORS["accent"], size=24),
                            create_section_title("Preferences"),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=16),
                    ft.Row(
                        [
                            ft.Text("Max jobs per session:", size=14, color=COLORS["text"]),
                            ft.TextField(
                                value=self.max_jobs,
                                width=80,
                                on_change=lambda e: setattr(self, "max_jobs", e.control.value),
                                border_radius=8,
                                border_color=COLORS["primary"],
                                text_style=ft.TextStyle(color=COLORS["text"]),
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=12),
                    create_checkbox(
                        "Run in headless mode (no visible browser)",
                        value=self.headless,
                        on_change=lambda e: setattr(self, "headless", e.control.value),
                    ),
                ],
            )
        )

    def _handle_save(self, e):
        """Handle save button click."""
        remote_options = []
        if self.remote_enabled:
            remote_options.append("Remote")
        if self.hybrid_enabled:
            remote_options.append("Hybrid")
        if self.onsite_enabled:
            remote_options.append("On-Site")

        employment_types = []
        if self.contract_enabled:
            employment_types.append("Contract")
        if self.fulltime_enabled:
            employment_types.append("Full-time")

        updated_config = {
            **self.config,
            "login": {
                "email": self.email,
                "password": self.password,
            },
            "filters": {
                **self.config.get("filters", {}),
                "job_title": self.job_title,
                "remote_option": remote_options,
                "employment_type": employment_types,
                "easy_apply_only": True,
            },
            "preferences": {
                **self.config.get("preferences", {}),
                "max_jobs": int(self.max_jobs) if self.max_jobs.isdigit() else 50,
                "headless": self.headless,
            },
        }

        self.on_save(updated_config)

        # Show success message
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Settings saved!", color=COLORS["text"]),
                bgcolor=COLORS["success"],
            )
            self.page.snack_bar.open = True
            self.page.update()

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
                                        "Settings",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLORS["text"],
                                    ),
                                    ft.Text(
                                        "Configure your preferences",
                                        size=14,
                                        color=COLORS["text_secondary"],
                                    ),
                                ],
                                spacing=4,
                            ),
                        ],
                    ),
                    ft.Container(height=24),
                    # Sections
                    self._create_credentials_section(),
                    ft.Container(height=16),
                    self._create_filters_section(),
                    ft.Container(height=16),
                    self._create_preferences_section(),
                    ft.Container(height=24),
                    # Save button
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            create_button(
                                "Save Settings",
                                on_click=self._handle_save,
                                icon=ft.icons.SAVE,
                            ),
                        ],
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=30,
            expand=True,
        )
