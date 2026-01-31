"""
Reusable UI widgets and components
"""

import flet as ft
from typing import Callable, Optional


# Color scheme
COLORS = {
    "background": "#1a1a2e",
    "surface": "#16213e",
    "primary": "#0f3460",
    "accent": "#e94560",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "error": "#ef4444",
    "text": "#ffffff",
    "text_secondary": "#94a3b8",
}


def create_card(content: ft.Control, padding: int = 20) -> ft.Container:
    """Create a styled card container."""
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=12,
        bgcolor=COLORS["surface"],
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
        ),
    )


def create_stat_card(title: str, value: str, icon: str, color: str = None) -> ft.Container:
    """Create a statistics card."""
    return create_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icon, color=color or COLORS["accent"], size=24),
                        ft.Text(title, size=14, color=COLORS["text_secondary"]),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Text(
                    value,
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=COLORS["text"],
                ),
            ],
            spacing=10,
        ),
        padding=20,
    )


def create_button(
    text: str,
    on_click: Callable,
    icon: str = None,
    primary: bool = True,
    disabled: bool = False,
    width: int = None,
) -> ft.ElevatedButton:
    """Create a styled button."""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        width=width,
        style=ft.ButtonStyle(
            color=COLORS["text"] if primary else COLORS["text_secondary"],
            bgcolor=COLORS["accent"] if primary else COLORS["surface"],
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )


def create_text_field(
    label: str,
    value: str = "",
    password: bool = False,
    on_change: Callable = None,
    hint: str = None,
    width: int = None,
) -> ft.TextField:
    """Create a styled text field."""
    return ft.TextField(
        label=label,
        value=value,
        password=password,
        can_reveal_password=password,
        on_change=on_change,
        hint_text=hint,
        width=width,
        border_radius=8,
        border_color=COLORS["primary"],
        focused_border_color=COLORS["accent"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        text_style=ft.TextStyle(color=COLORS["text"]),
        cursor_color=COLORS["accent"],
    )


def create_checkbox(
    label: str,
    value: bool = False,
    on_change: Callable = None,
    disabled: bool = False,
) -> ft.Checkbox:
    """Create a styled checkbox."""
    return ft.Checkbox(
        label=label,
        value=value,
        on_change=on_change,
        disabled=disabled,
        active_color=COLORS["accent"],
        check_color=COLORS["text"],
        label_style=ft.TextStyle(color=COLORS["text"]),
    )


def create_dropdown(
    label: str,
    options: list,
    value: str = None,
    on_change: Callable = None,
    width: int = None,
) -> ft.Dropdown:
    """Create a styled dropdown."""
    return ft.Dropdown(
        label=label,
        value=value,
        options=[ft.dropdown.Option(opt) for opt in options],
        on_change=on_change,
        width=width,
        border_radius=8,
        border_color=COLORS["primary"],
        focused_border_color=COLORS["accent"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        text_style=ft.TextStyle(color=COLORS["text"]),
    )


def create_section_title(text: str) -> ft.Text:
    """Create a section title."""
    return ft.Text(
        text,
        size=20,
        weight=ft.FontWeight.BOLD,
        color=COLORS["text"],
    )


def create_progress_ring(value: float = None, size: int = 50) -> ft.ProgressRing:
    """Create a progress ring."""
    return ft.ProgressRing(
        value=value,
        width=size,
        height=size,
        stroke_width=4,
        color=COLORS["accent"],
    )


def create_snackbar(message: str, success: bool = True) -> ft.SnackBar:
    """Create a styled snackbar notification."""
    return ft.SnackBar(
        content=ft.Text(message, color=COLORS["text"]),
        bgcolor=COLORS["success"] if success else COLORS["error"],
        duration=3000,
    )


def create_job_list_item(job: dict) -> ft.Container:
    """Create a job list item."""
    status_color = {
        "applied": COLORS["success"],
        "likely_applied": COLORS["warning"],
        "partial": COLORS["error"],
    }.get(job.get("status", ""), COLORS["text_secondary"])

    return ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            job.get("title", "Unknown")[:50],
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=COLORS["text"],
                        ),
                        ft.Text(
                            job.get("company", "Unknown"),
                            size=12,
                            color=COLORS["text_secondary"],
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(
                        job.get("status", "").replace("_", " ").title(),
                        size=11,
                        color=COLORS["text"],
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=4,
                    bgcolor=status_color,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=12,
        border_radius=8,
        bgcolor=ft.colors.with_opacity(0.3, COLORS["primary"]),
        margin=ft.margin.only(bottom=8),
    )


def create_time_picker_row(
    label: str,
    hour: int = 9,
    minute: int = 0,
    on_change: Callable = None,
) -> ft.Row:
    """Create a time picker row."""
    hour_dropdown = ft.Dropdown(
        value=str(hour).zfill(2),
        options=[ft.dropdown.Option(str(i).zfill(2)) for i in range(24)],
        width=80,
        on_change=on_change,
        border_radius=8,
        border_color=COLORS["primary"],
        text_style=ft.TextStyle(color=COLORS["text"]),
    )

    minute_dropdown = ft.Dropdown(
        value=str(minute).zfill(2),
        options=[ft.dropdown.Option(str(i).zfill(2)) for i in range(0, 60, 5)],
        width=80,
        on_change=on_change,
        border_radius=8,
        border_color=COLORS["primary"],
        text_style=ft.TextStyle(color=COLORS["text"]),
    )

    return ft.Row(
        [
            ft.Text(label, color=COLORS["text"], size=14),
            hour_dropdown,
            ft.Text(":", color=COLORS["text"], size=20),
            minute_dropdown,
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10,
    )
