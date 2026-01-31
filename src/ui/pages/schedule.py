"""
Schedule page - Configure automated job application schedules
"""

import flet as ft
from typing import Callable, Dict, Optional
from ..components.widgets import (
    COLORS, create_card, create_button, create_checkbox, create_section_title
)


class SchedulePage(ft.UserControl):
    """Schedule page for configuring automation schedules."""

    def __init__(
        self,
        config: Dict,
        on_save: Callable[[Dict], None],
        on_schedule_toggle: Optional[Callable[[bool], None]] = None,
        on_os_scheduler_toggle: Optional[Callable[[bool], None]] = None,
    ):
        super().__init__()
        self.config = config
        self.on_save = on_save
        self.on_schedule_toggle = on_schedule_toggle
        self.on_os_scheduler_toggle = on_os_scheduler_toggle

        # Initialize from config
        schedule_config = config.get("schedule", {})
        self.schedule_enabled = schedule_config.get("enabled", False)
        self.schedule_hour = schedule_config.get("hour", 9)
        self.schedule_minute = schedule_config.get("minute", 0)
        self.run_on_startup = schedule_config.get("run_on_startup", False)
        self.os_scheduler_enabled = schedule_config.get("os_scheduler", False)

    def _create_time_picker(self) -> ft.Container:
        """Create the time picker component."""
        hours = [str(i).zfill(2) for i in range(24)]
        minutes = [str(i).zfill(2) for i in range(0, 60, 5)]

        return ft.Container(
            content=ft.Row(
                [
                    ft.Dropdown(
                        label="Hour",
                        value=str(self.schedule_hour).zfill(2),
                        options=[ft.dropdown.Option(h) for h in hours],
                        width=100,
                        border_radius=8,
                        border_color=COLORS["primary"],
                        focused_border_color=COLORS["accent"],
                        text_style=ft.TextStyle(color=COLORS["text"]),
                        on_change=lambda e: setattr(self, "schedule_hour", int(e.control.value)),
                    ),
                    ft.Text(":", size=24, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ft.Dropdown(
                        label="Minute",
                        value=str(self.schedule_minute).zfill(2),
                        options=[ft.dropdown.Option(m) for m in minutes],
                        width=100,
                        border_radius=8,
                        border_color=COLORS["primary"],
                        focused_border_color=COLORS["accent"],
                        text_style=ft.TextStyle(color=COLORS["text"]),
                        on_change=lambda e: setattr(self, "schedule_minute", int(e.control.value)),
                    ),
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

    def _create_schedule_section(self) -> ft.Container:
        """Create the main schedule section."""
        return create_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.SCHEDULE, color=COLORS["accent"], size=24),
                            create_section_title("Daily Schedule"),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Set a time for the automation to run daily",
                        size=14,
                        color=COLORS["text_secondary"],
                    ),
                    ft.Container(height=16),
                    # Enable/disable toggle
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Switch(
                                    value=self.schedule_enabled,
                                    active_color=COLORS["accent"],
                                    on_change=self._handle_schedule_toggle,
                                ),
                                ft.Text(
                                    "Enable daily schedule",
                                    size=14,
                                    color=COLORS["text"],
                                    weight=ft.FontWeight.W_500,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=ft.padding.symmetric(vertical=8),
                    ),
                    ft.Container(height=16),
                    # Time picker (always visible)
                    ft.Text("Schedule Time", size=14, weight=ft.FontWeight.W_500, color=COLORS["text"]),
                    ft.Container(height=8),
                    ft.Container(
                        content=self._create_time_picker(),
                        bgcolor=ft.colors.with_opacity(0.3, COLORS["primary"]),
                        border_radius=12,
                    ),
                    ft.Container(height=16),
                    # Schedule info
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.icons.INFO_OUTLINE, size=16, color=COLORS["text_secondary"]),
                                        ft.Text(
                                            "The automation will start automatically in the background at the scheduled time",
                                            size=12,
                                            color=COLORS["text_secondary"],
                                            italic=True,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Row(
                                    [
                                        ft.Icon(ft.icons.WARNING_AMBER, size=16, color=COLORS["warning"]),
                                        ft.Text(
                                            "Note: App must be running. For scheduling when app is closed, enable OS-level scheduling below",
                                            size=12,
                                            color=COLORS["text_secondary"],
                                            italic=True,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=8,
                        ),
                    ),
                ],
            )
        )

    def _create_os_scheduler_section(self) -> ft.Container:
        """Create OS-level scheduler section."""
        return create_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.COMPUTER, color=COLORS["accent"], size=24),
                            create_section_title("System Scheduler"),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Run even when the app is closed using system scheduler",
                        size=14,
                        color=COLORS["text_secondary"],
                    ),
                    ft.Container(height=16),
                    create_checkbox(
                        "Enable OS-level scheduling",
                        value=self.os_scheduler_enabled,
                        on_change=self._handle_os_scheduler_toggle,
                    ),
                    ft.Container(height=12),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.icons.CHECK_CIRCLE, size=14, color=COLORS["success"]),
                                        ft.Text(
                                            "Runs automatically even if app is closed",
                                            size=12,
                                            color=COLORS["text_secondary"],
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Row(
                                    [
                                        ft.Icon(ft.icons.CHECK_CIRCLE, size=14, color=COLORS["success"]),
                                        ft.Text(
                                            "Uses macOS launchd or Windows Task Scheduler",
                                            size=12,
                                            color=COLORS["text_secondary"],
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Row(
                                    [
                                        ft.Icon(ft.icons.WARNING, size=14, color=COLORS["warning"]),
                                        ft.Text(
                                            "Requires app to stay installed in the same location",
                                            size=12,
                                            color=COLORS["text_secondary"],
                                        ),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=ft.padding.only(left=20),
                    ),
                ],
            )
        )

    def _create_options_section(self) -> ft.Container:
        """Create additional options section."""
        return create_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.TUNE, color=COLORS["accent"], size=24),
                            create_section_title("Options"),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=16),
                    create_checkbox(
                        "Run automation on app startup",
                        value=self.run_on_startup,
                        on_change=lambda e: setattr(self, "run_on_startup", e.control.value),
                    ),
                ],
            )
        )

    def _handle_schedule_toggle(self, e):
        """Handle schedule enable/disable toggle."""
        self.schedule_enabled = e.control.value
        if self.on_schedule_toggle:
            self.on_schedule_toggle(self.schedule_enabled)
        self.update()

    def _handle_os_scheduler_toggle(self, e):
        """Handle OS scheduler enable/disable toggle."""
        self.os_scheduler_enabled = e.control.value
        if self.on_os_scheduler_toggle:
            self.on_os_scheduler_toggle(self.os_scheduler_enabled)

    def _handle_save(self, e):
        """Handle save button click."""
        updated_config = {
            **self.config,
            "schedule": {
                "enabled": self.schedule_enabled,
                "hour": self.schedule_hour,
                "minute": self.schedule_minute,
                "run_on_startup": self.run_on_startup,
                "os_scheduler": self.os_scheduler_enabled,
            },
        }

        self.on_save(updated_config)

        # Show success message
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Schedule saved!", color=COLORS["text"]),
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
                                        "Schedule",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLORS["text"],
                                    ),
                                    ft.Text(
                                        "Configure automated runs",
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
                    self._create_schedule_section(),
                    ft.Container(height=16),
                    self._create_os_scheduler_section(),
                    ft.Container(height=16),
                    self._create_options_section(),
                    ft.Container(height=24),
                    # Save button
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            create_button(
                                "Save Schedule",
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
