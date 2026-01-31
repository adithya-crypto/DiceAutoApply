"""
Navigation sidebar component
"""

import flet as ft
from .widgets import COLORS


class Sidebar(ft.UserControl):
    """Navigation sidebar with icons and labels."""

    def __init__(self, on_navigate: callable, current_page: str = "dashboard"):
        super().__init__()
        self.on_navigate = on_navigate
        self.current_page = current_page
        self.nav_items_container = None

    def _create_nav_item(self, icon: str, label: str, page: str) -> ft.Container:
        """Create a navigation item."""
        is_active = self.current_page == page

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        icon,
                        color=COLORS["accent"] if is_active else COLORS["text_secondary"],
                        size=22,
                    ),
                    ft.Text(
                        label,
                        color=COLORS["text"] if is_active else COLORS["text_secondary"],
                        size=14,
                        weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=8,
            bgcolor=ft.colors.with_opacity(0.2, COLORS["accent"]) if is_active else None,
            on_click=lambda e, p=page: self._handle_click(p),
            ink=True,
        )

    def _handle_click(self, page: str):
        """Handle navigation click."""
        self.current_page = page
        self._rebuild_nav_items()
        self.on_navigate(page)

    def _rebuild_nav_items(self):
        """Rebuild navigation items with updated active state."""
        if self.nav_items_container:
            self.nav_items_container.controls = [
                self._create_nav_item(ft.icons.DASHBOARD, "Dashboard", "dashboard"),
                self._create_nav_item(ft.icons.SETTINGS, "Settings", "settings"),
                self._create_nav_item(ft.icons.SCHEDULE, "Schedule", "schedule"),
                self._create_nav_item(ft.icons.LIST_ALT, "Logs", "logs"),
            ]
            if self.page:
                self.nav_items_container.update()

    def build(self):
        self.nav_items_container = ft.Column(
            [
                self._create_nav_item(ft.icons.DASHBOARD, "Dashboard", "dashboard"),
                self._create_nav_item(ft.icons.SETTINGS, "Settings", "settings"),
                self._create_nav_item(ft.icons.SCHEDULE, "Schedule", "schedule"),
                self._create_nav_item(ft.icons.LIST_ALT, "Logs", "logs"),
            ],
            spacing=4,
        )

        return ft.Container(
            content=ft.Column(
                [
                    # Logo/Brand
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.ROCKET_LAUNCH, color=COLORS["accent"], size=28),
                                ft.Text(
                                    "DiceAutoApply",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLORS["text"],
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=20),
                        margin=ft.margin.only(bottom=20),
                    ),
                    # Navigation items
                    self.nav_items_container,
                    # Spacer
                    ft.Container(expand=True),
                    # Version info
                    ft.Container(
                        content=ft.Text(
                            "v1.0.0",
                            size=12,
                            color=COLORS["text_secondary"],
                        ),
                        padding=ft.padding.all(16),
                    ),
                ],
                spacing=4,
                expand=True,
            ),
            width=220,
            bgcolor=COLORS["surface"],
            border_radius=ft.border_radius.only(top_right=12, bottom_right=12),
            padding=ft.padding.only(top=10, bottom=10),
        )

    def set_page(self, page: str):
        """Set the current page externally."""
        self.current_page = page
        self._rebuild_nav_items()
