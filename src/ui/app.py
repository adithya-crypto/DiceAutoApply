"""
Main Flet application with navigation
"""

import flet as ft
import os
import json
import threading
from typing import Optional
from pathlib import Path

from .components.widgets import COLORS
from .components.sidebar import Sidebar
from .pages.setup import SetupWizard
from .pages.dashboard import DashboardPage
from .pages.settings import SettingsPage
from .pages.schedule import SchedulePage
from .pages.logs import LogsPage

# Import schedulers and utils - use sys.path since they're sibling packages
import sys
_src_path = str(Path(__file__).parent.parent)
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from scheduler.builtin import BuiltInScheduler
from scheduler.os_scheduler import OSScheduler
from utils.credentials import store_credentials, get_credentials, has_keyring


class DiceAutoApplyApp:
    """Main application class."""

    def __init__(self):
        self.page: Optional[ft.Page] = None
        self.config = {}
        self.current_page = "dashboard"
        self.sidebar: Optional[Sidebar] = None
        self.content_area: Optional[ft.Container] = None
        self.automation = None
        self.automation_thread = None

        # Scheduler instances
        self.builtin_scheduler: Optional[BuiltInScheduler] = None
        self.os_scheduler: Optional[OSScheduler] = None

        # Page instances
        self.dashboard_page: Optional[DashboardPage] = None
        self.settings_page: Optional[SettingsPage] = None
        self.schedule_page: Optional[SchedulePage] = None
        self.logs_page: Optional[LogsPage] = None

        # Paths
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.base_dir / "config"
        self.data_dir = self.base_dir / "data"
        self.config_path = self.config_dir / "settings.yaml"

    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

    def _load_config(self) -> dict:
        """Load configuration from file."""
        config = {}

        if self.config_path.exists():
            try:
                import yaml
                with open(self.config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Try JSON as fallback
        if not config:
            json_path = self.config_dir / "settings.json"
            if json_path.exists():
                try:
                    with open(json_path, "r") as f:
                        config = json.load(f)
                except Exception:
                    pass

        # Try to load credentials from keyring
        if has_keyring():
            email, password = get_credentials()
            if email and password:
                if "login" not in config:
                    config["login"] = {}
                config["login"]["email"] = email
                config["login"]["password"] = password

        return config

    def _save_config(self, config: dict):
        """Save configuration to file."""
        self.config = config
        self._ensure_directories()

        # Try to store credentials in keyring
        config_to_save = config.copy()
        if has_keyring():
            login = config.get("login", {})
            email = login.get("email")
            password = login.get("password")
            if email and password:
                if store_credentials(email, password):
                    # Remove password from config file if stored in keyring
                    if "login" in config_to_save:
                        config_to_save["login"] = {"email": email}
                        # Add a flag indicating keyring is used
                        config_to_save["login"]["use_keyring"] = True

        # Save as YAML
        try:
            import yaml
            with open(self.config_path, "w") as f:
                yaml.safe_dump(config_to_save, f, default_flow_style=False)
        except ImportError:
            # Fallback to JSON if PyYAML not available
            json_path = self.config_dir / "settings.json"
            with open(json_path, "w") as f:
                json.dump(config_to_save, f, indent=2)

    def _is_first_run(self) -> bool:
        """Check if this is the first run (no config exists)."""
        return not self.config.get("login", {}).get("email")

    def _navigate_to(self, page_name: str):
        """Navigate to a specific page."""
        self.current_page = page_name
        self._update_content()
        if self.sidebar:
            self.sidebar.set_page(page_name)

    def _update_content(self):
        """Update the main content area based on current page."""
        if not self.content_area:
            return

        if self.current_page == "dashboard":
            if not self.dashboard_page:
                self.dashboard_page = DashboardPage(
                    config=self.config,
                    on_run=self._handle_run,
                    on_stop=self._handle_stop,
                    data_dir=str(self.data_dir),
                    on_view_all=lambda: self._navigate_to("logs"),
                )
            self.content_area.content = self.dashboard_page

        elif self.current_page == "settings":
            if not self.settings_page:
                self.settings_page = SettingsPage(
                    config=self.config,
                    on_save=self._save_config,
                )
            else:
                # Refresh settings page with latest config
                self.settings_page.config = self.config
            self.content_area.content = self.settings_page

        elif self.current_page == "schedule":
            if not self.schedule_page:
                self.schedule_page = SchedulePage(
                    config=self.config,
                    on_save=self._handle_schedule_save,
                    on_schedule_toggle=self._handle_schedule_toggle,
                    on_os_scheduler_toggle=self._handle_os_scheduler_toggle,
                )
            else:
                self.schedule_page.config = self.config
            self.content_area.content = self.schedule_page

        elif self.current_page == "logs":
            if not self.logs_page:
                self.logs_page = LogsPage(data_dir=str(self.data_dir))
            self.content_area.content = self.logs_page

        if self.page:
            self.page.update()

    def _handle_run(self):
        """Handle run automation request."""
        if self.automation_thread and self.automation_thread.is_alive():
            return  # Already running

        # Import automation module
        try:
            from dice_automation import DiceAutomation

            self.automation = DiceAutomation(
                config=self.config,
                data_dir=str(self.data_dir),
                progress_callback=self._on_progress,
                log_callback=self._on_log,
            )

            self.automation_thread = threading.Thread(
                target=self._run_automation,
                daemon=True,
            )
            self.automation_thread.start()

        except Exception as e:
            self._on_log("ERROR", f"Failed to start automation: {str(e)}")

    def _run_automation(self):
        """Run the automation in a background thread."""
        try:
            if self.automation:
                self.automation.run()
        except Exception as e:
            self._on_log("ERROR", f"Automation error: {str(e)}")
        finally:
            # Update dashboard when done
            if self.dashboard_page and self.page:
                self.dashboard_page.set_running(False)
                self.page.update()

    def _handle_stop(self):
        """Handle stop automation request."""
        if self.automation:
            self.automation.stop()

    def _handle_schedule_toggle(self, enabled: bool):
        """Handle schedule enable/disable."""
        schedule_config = self.config.get("schedule", {})
        hour = schedule_config.get("hour", 9)
        minute = schedule_config.get("minute", 0)

        if enabled:
            # Initialize and start built-in scheduler
            if not self.builtin_scheduler:
                self.builtin_scheduler = BuiltInScheduler(
                    run_callback=self._handle_run,
                    log_callback=self._on_log,
                )
            self.builtin_scheduler.set_schedule(hour, minute)
            self.builtin_scheduler.start()
            self._on_log("INFO", f"Scheduler enabled for {hour:02d}:{minute:02d} daily")
        else:
            # Stop the scheduler
            if self.builtin_scheduler:
                self.builtin_scheduler.stop()
            self._on_log("INFO", "Scheduler disabled")

    def _handle_os_scheduler_toggle(self, enabled: bool):
        """Handle OS-level scheduler enable/disable."""
        schedule_config = self.config.get("schedule", {})
        hour = schedule_config.get("hour", 9)
        minute = schedule_config.get("minute", 0)

        if not self.os_scheduler:
            self.os_scheduler = OSScheduler()

        if enabled:
            success, message = self.os_scheduler.install(hour, minute)
            if success:
                self._on_log("SUCCESS", f"OS scheduler installed: {message}")
            else:
                self._on_log("ERROR", f"Failed to install OS scheduler: {message}")
        else:
            success, message = self.os_scheduler.uninstall()
            if success:
                self._on_log("INFO", f"OS scheduler removed: {message}")
            else:
                self._on_log("ERROR", f"Failed to remove OS scheduler: {message}")

    def _init_scheduler_from_config(self):
        """Initialize scheduler based on saved config."""
        schedule_config = self.config.get("schedule", {})

        # Check if schedule is enabled
        if schedule_config.get("enabled", False):
            self._handle_schedule_toggle(True)

        # Check if run on startup is enabled
        if schedule_config.get("run_on_startup", False):
            # Run automation after a short delay to let UI load
            threading.Timer(2.0, self._handle_run).start()

    def _handle_schedule_save(self, config: dict):
        """Handle schedule configuration save and update schedulers."""
        # Save the config
        self._save_config(config)

        # Get schedule settings
        schedule_config = config.get("schedule", {})
        enabled = schedule_config.get("enabled", False)
        hour = schedule_config.get("hour", 9)
        minute = schedule_config.get("minute", 0)
        os_scheduler_enabled = schedule_config.get("os_scheduler", False)

        # Update built-in scheduler
        if enabled:
            if not self.builtin_scheduler:
                self.builtin_scheduler = BuiltInScheduler(
                    run_callback=self._handle_run,
                    log_callback=self._on_log,
                )
            self.builtin_scheduler.set_schedule(hour, minute)
            if not self.builtin_scheduler.is_running:
                self.builtin_scheduler.start()
        elif self.builtin_scheduler and self.builtin_scheduler.is_running:
            self.builtin_scheduler.stop()

        # Update OS scheduler
        if os_scheduler_enabled:
            if not self.os_scheduler:
                self.os_scheduler = OSScheduler()
            self.os_scheduler.install(hour, minute)
        elif self.os_scheduler and self.os_scheduler.is_installed():
            self.os_scheduler.uninstall()

    def _on_progress(self, status: str, current: int, total: int):
        """Callback for automation progress updates."""
        if self.dashboard_page:
            self.dashboard_page.update_progress(status, current, total)
            if self.page:
                self.page.update()

    def _on_log(self, level: str, message: str):
        """Callback for automation log messages."""
        if self.logs_page:
            self.logs_page.add_log(level, message)

    def _handle_setup_complete(self, config: dict):
        """Handle setup wizard completion."""
        self._save_config(config)
        self._show_main_app()

    def _show_setup_wizard(self):
        """Show the setup wizard."""
        wizard = SetupWizard(on_complete=self._handle_setup_complete)
        self.page.add(
            ft.Container(
                content=wizard,
                expand=True,
                bgcolor=COLORS["background"],
            )
        )

    def _show_main_app(self):
        """Show the main application."""
        self.page.clean()

        # Create sidebar
        self.sidebar = Sidebar(
            on_navigate=self._navigate_to,
            current_page=self.current_page,
        )

        # Create content area
        self.content_area = ft.Container(
            expand=True,
            bgcolor=COLORS["background"],
        )

        # Build layout
        main_layout = ft.Row(
            [
                self.sidebar,
                ft.VerticalDivider(width=1, color=ft.colors.with_opacity(0.1, COLORS["text"])),
                self.content_area,
            ],
            expand=True,
            spacing=0,
        )

        self.page.add(
            ft.Container(
                content=main_layout,
                expand=True,
                bgcolor=COLORS["background"],
            )
        )

        # Navigate to initial page
        self._update_content()

        # Initialize scheduler from config
        self._init_scheduler_from_config()

    def main(self, page: ft.Page):
        """Main entry point for the Flet app."""
        self.page = page

        # Configure page
        page.title = "DiceAutoApply"
        page.bgcolor = COLORS["background"]
        page.padding = 0
        page.spacing = 0
        page.window.width = 1100
        page.window.height = 700
        page.window.min_width = 900
        page.window.min_height = 600

        # Ensure directories
        self._ensure_directories()

        # Load config
        self.config = self._load_config()

        # Show setup wizard or main app
        if self._is_first_run():
            self._show_setup_wizard()
        else:
            self._show_main_app()


def run_app():
    """Run the Flet application."""
    app = DiceAutoApplyApp()
    ft.app(target=app.main, name="Dice AutoApply")


if __name__ == "__main__":
    run_app()
