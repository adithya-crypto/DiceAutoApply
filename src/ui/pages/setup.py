"""
Setup Wizard - First-time configuration
"""

import flet as ft
from typing import Callable
from ..components.widgets import (
    COLORS, create_card, create_button, create_text_field,
    create_checkbox, create_section_title, create_time_picker_row
)


class SetupWizard(ft.UserControl):
    """Multi-step setup wizard for first-time configuration."""

    def __init__(self, on_complete: Callable[[dict], None]):
        super().__init__()
        self.on_complete = on_complete
        self.current_step = 0
        self.total_steps = 4

        # Form data
        self.email = ""
        self.password = ""
        self.job_title = "Data Engineer"
        self.remote_enabled = True
        self.hybrid_enabled = True
        self.contract_enabled = True
        self.fulltime_enabled = False
        self.max_jobs = "50"
        self.schedule_hour = "09"
        self.schedule_minute = "00"
        self.schedule_enabled = True

    def _create_step_indicator(self) -> ft.Row:
        """Create step progress indicator."""
        steps = []
        for i in range(self.total_steps):
            is_active = i == self.current_step
            is_complete = i < self.current_step

            step_color = COLORS["accent"] if is_active or is_complete else COLORS["primary"]
            text_color = COLORS["text"] if is_active or is_complete else COLORS["text_secondary"]

            steps.append(
                ft.Container(
                    content=ft.Text(
                        str(i + 1) if not is_complete else "✓",
                        size=14,
                        color=text_color,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    width=32,
                    height=32,
                    border_radius=16,
                    bgcolor=step_color,
                    alignment=ft.alignment.center,
                )
            )

            if i < self.total_steps - 1:
                steps.append(
                    ft.Container(
                        width=40,
                        height=2,
                        bgcolor=COLORS["accent"] if is_complete else COLORS["primary"],
                    )
                )

        return ft.Row(steps, alignment=ft.MainAxisAlignment.CENTER)

    def _create_welcome_step(self) -> ft.Column:
        """Create welcome step content."""
        return ft.Column(
            [
                ft.Icon(ft.icons.ROCKET_LAUNCH, size=80, color=COLORS["accent"]),
                ft.Text(
                    "Welcome to DiceAutoApply",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=COLORS["text"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Automate your job applications on Dice.com",
                    size=16,
                    color=COLORS["text_secondary"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                ft.Column(
                    [
                        self._create_feature_item(ft.icons.AUTO_AWESOME, "Auto-apply to Easy Apply jobs"),
                        self._create_feature_item(ft.icons.FILTER_ALT, "Smart filtering by your preferences"),
                        self._create_feature_item(ft.icons.SCHEDULE, "Schedule daily automated runs"),
                        self._create_feature_item(ft.icons.TRACK_CHANGES, "Track all your applications"),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
        )

    def _create_feature_item(self, icon: str, text: str) -> ft.Row:
        """Create a feature list item."""
        return ft.Row(
            [
                ft.Icon(icon, color=COLORS["accent"], size=20),
                ft.Text(text, size=14, color=COLORS["text"]),
            ],
            spacing=12,
        )

    def _create_credentials_step(self) -> ft.Column:
        """Create credentials step content."""
        email_field = create_text_field(
            label="Dice.com Email",
            value=self.email,
            hint="Enter your Dice.com login email",
            width=400,
            on_change=lambda e: setattr(self, "email", e.control.value),
        )

        password_field = create_text_field(
            label="Password",
            value=self.password,
            password=True,
            hint="Enter your Dice.com password",
            width=400,
            on_change=lambda e: setattr(self, "password", e.control.value),
        )

        return ft.Column(
            [
                ft.Icon(ft.icons.LOCK, size=48, color=COLORS["accent"]),
                create_section_title("Dice.com Credentials"),
                ft.Text(
                    "Enter your Dice.com login credentials",
                    size=14,
                    color=COLORS["text_secondary"],
                ),
                ft.Container(height=20),
                email_field,
                ft.Container(height=12),
                password_field,
                ft.Container(height=12),
                ft.Row(
                    [
                        ft.Icon(ft.icons.SECURITY, size=16, color=COLORS["text_secondary"]),
                        ft.Text(
                            "Credentials are stored securely on your device",
                            size=12,
                            color=COLORS["text_secondary"],
                        ),
                    ],
                    spacing=8,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

    def _create_preferences_step(self) -> ft.Column:
        """Create job preferences step content."""
        job_title_field = create_text_field(
            label="Job Title / Role",
            value=self.job_title,
            hint="e.g., Data Engineer, Software Developer",
            width=400,
            on_change=lambda e: setattr(self, "job_title", e.control.value),
        )

        return ft.Column(
            [
                ft.Icon(ft.icons.WORK, size=48, color=COLORS["accent"]),
                create_section_title("Job Preferences"),
                ft.Text(
                    "Configure what types of jobs to apply for",
                    size=14,
                    color=COLORS["text_secondary"],
                ),
                ft.Container(height=20),
                job_title_field,
                ft.Container(height=20),
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
                ft.Container(height=20),
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
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

    def _create_schedule_step(self) -> ft.Column:
        """Create schedule step content."""
        return ft.Column(
            [
                ft.Icon(ft.icons.SCHEDULE, size=48, color=COLORS["accent"]),
                create_section_title("Daily Schedule"),
                ft.Text(
                    "Set up automatic daily job applications",
                    size=14,
                    color=COLORS["text_secondary"],
                ),
                ft.Container(height=20),
                create_checkbox(
                    "Enable daily scheduled runs",
                    value=self.schedule_enabled,
                    on_change=lambda e: setattr(self, "schedule_enabled", e.control.value),
                ),
                ft.Container(height=16),
                ft.Row(
                    [
                        ft.Text("Run daily at:", size=14, color=COLORS["text"]),
                        ft.Dropdown(
                            value=self.schedule_hour,
                            options=[ft.dropdown.Option(str(i).zfill(2)) for i in range(24)],
                            width=80,
                            on_change=lambda e: setattr(self, "schedule_hour", e.control.value),
                            border_radius=8,
                            border_color=COLORS["primary"],
                            text_style=ft.TextStyle(color=COLORS["text"]),
                        ),
                        ft.Text(":", size=20, color=COLORS["text"]),
                        ft.Dropdown(
                            value=self.schedule_minute,
                            options=[ft.dropdown.Option(str(i).zfill(2)) for i in range(0, 60, 5)],
                            width=80,
                            on_change=lambda e: setattr(self, "schedule_minute", e.control.value),
                            border_radius=8,
                            border_color=COLORS["primary"],
                            text_style=ft.TextStyle(color=COLORS["text"]),
                        ),
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=30),
                create_card(
                    ft.Column(
                        [
                            ft.Text("You're all set!", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                            ft.Text(
                                "Click 'Complete Setup' to start using DiceAutoApply",
                                size=14,
                                color=COLORS["text_secondary"],
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    )
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

    def _get_step_content(self) -> ft.Control:
        """Get content for current step."""
        steps = [
            self._create_welcome_step,
            self._create_credentials_step,
            self._create_preferences_step,
            self._create_schedule_step,
        ]
        return steps[self.current_step]()

    def _next_step(self, e):
        """Go to next step."""
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self._refresh()

    def _prev_step(self, e):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._refresh()

    def _complete_setup(self, e):
        """Complete the setup wizard."""
        # Build configuration
        remote_options = []
        if self.remote_enabled:
            remote_options.append("Remote")
        if self.hybrid_enabled:
            remote_options.append("Hybrid")

        employment_types = []
        if self.contract_enabled:
            employment_types.append("Contract")
        if self.fulltime_enabled:
            employment_types.append("Full-time")

        config = {
            "login": {
                "email": self.email,
                "password": self.password,
            },
            "filters": {
                "job_title": self.job_title,
                "remote_option": remote_options,
                "employment_type": employment_types,
                "easy_apply_only": True,
            },
            "preferences": {
                "max_jobs": int(self.max_jobs) if self.max_jobs.isdigit() else 50,
                "max_pages": 10,
                "headless": False,
            },
            "schedule": {
                "enabled": self.schedule_enabled,
                "hour": int(self.schedule_hour),
                "minute": int(self.schedule_minute),
            },
        }

        self.on_complete(config)

    def _build_content(self) -> ft.Column:
        """Build the wizard content for the current step."""
        return ft.Column(
            [
                # Step indicator
                self._create_step_indicator(),
                ft.Container(height=30),
                # Step content
                ft.Container(
                    content=self._get_step_content(),
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                # Navigation buttons
                ft.Row(
                    [
                        create_button(
                            "Back",
                            on_click=self._prev_step,
                            primary=False,
                            disabled=self.current_step == 0,
                        ) if self.current_step > 0 else ft.Container(),
                        ft.Container(expand=True),
                        create_button(
                            "Complete Setup" if self.current_step == self.total_steps - 1 else "Next",
                            on_click=self._complete_setup if self.current_step == self.total_steps - 1 else self._next_step,
                            icon=ft.icons.CHECK if self.current_step == self.total_steps - 1 else ft.icons.ARROW_FORWARD,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            expand=True,
        )

    def _refresh(self):
        """Refresh wizard UI after step changes."""
        if hasattr(self, "root") and self.root:
            self.root.content = self._build_content()
        self.update()

    def build(self):
        self.root = ft.Container(
            content=self._build_content(),
            padding=40,
            expand=True,
        )
        return self.root
