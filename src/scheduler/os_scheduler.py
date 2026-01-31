"""
OS-level scheduler for running automation even when the app is closed
Supports macOS (launchd) and Windows (Task Scheduler)
"""

import os
import sys
import platform
import subprocess
from typing import Optional, Tuple
from pathlib import Path


class OSScheduler:
    """OS-level scheduler for macOS and Windows."""

    def __init__(self, app_path: Optional[str] = None):
        """
        Initialize the OS scheduler.

        Args:
            app_path: Path to the application executable. If None, uses current script.
        """
        self.system = platform.system()
        self.app_path = app_path or sys.executable
        self.job_name = "com.diceautoapply.daily"

        # Paths for scheduler files
        if self.system == "Darwin":  # macOS
            self.plist_path = Path.home() / "Library/LaunchAgents" / f"{self.job_name}.plist"
        elif self.system == "Windows":
            self.task_name = "DiceAutoApply Daily Run"

    def _get_python_path(self) -> str:
        """Get the Python executable path."""
        return sys.executable

    def _get_script_path(self) -> str:
        """Get the main script path."""
        return str(Path(__file__).parent.parent / "main.py")

    def _create_macos_plist(self, hour: int, minute: int) -> str:
        """Create macOS launchd plist content."""
        python_path = self._get_python_path()
        script_path = self._get_script_path()
        log_path = Path.home() / "Library/Logs/DiceAutoApply"
        log_path.mkdir(parents=True, exist_ok=True)

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.job_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--scheduled-run</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{log_path}/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{log_path}/stderr.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""

    def install_macos(self, hour: int, minute: int) -> Tuple[bool, str]:
        """
        Install macOS launchd job.

        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Unload existing job if present
            self.uninstall_macos()

            # Create plist directory if needed
            self.plist_path.parent.mkdir(parents=True, exist_ok=True)

            # Write plist file
            plist_content = self._create_macos_plist(hour, minute)
            with open(self.plist_path, "w") as f:
                f.write(plist_content)

            # Load the job
            result = subprocess.run(
                ["launchctl", "load", str(self.plist_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True, f"Scheduled for {hour:02d}:{minute:02d} daily"
            else:
                return False, f"Failed to load job: {result.stderr}"

        except Exception as e:
            return False, f"Error installing scheduler: {str(e)}"

    def uninstall_macos(self) -> Tuple[bool, str]:
        """
        Uninstall macOS launchd job.

        Returns:
            Tuple of (success, message)
        """
        try:
            if self.plist_path.exists():
                # Unload the job
                subprocess.run(
                    ["launchctl", "unload", str(self.plist_path)],
                    capture_output=True,
                    text=True,
                )
                # Remove the plist file
                self.plist_path.unlink()

            return True, "Scheduler removed"
        except Exception as e:
            return False, f"Error uninstalling scheduler: {str(e)}"

    def is_installed_macos(self) -> bool:
        """Check if macOS job is installed."""
        return self.plist_path.exists()

    def install_windows(self, hour: int, minute: int) -> Tuple[bool, str]:
        """
        Install Windows Task Scheduler job.

        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Remove existing task if present
            self.uninstall_windows()

            python_path = self._get_python_path()
            script_path = self._get_script_path()
            time_str = f"{hour:02d}:{minute:02d}"

            # Create task using schtasks
            cmd = [
                "schtasks",
                "/create",
                "/tn", self.task_name,
                "/tr", f'"{python_path}" "{script_path}" --scheduled-run',
                "/sc", "daily",
                "/st", time_str,
                "/f",  # Force create (overwrite if exists)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True,
            )

            if result.returncode == 0:
                return True, f"Scheduled for {time_str} daily"
            else:
                return False, f"Failed to create task: {result.stderr}"

        except Exception as e:
            return False, f"Error installing scheduler: {str(e)}"

    def uninstall_windows(self) -> Tuple[bool, str]:
        """
        Uninstall Windows Task Scheduler job.

        Returns:
            Tuple of (success, message)
        """
        try:
            result = subprocess.run(
                ["schtasks", "/delete", "/tn", self.task_name, "/f"],
                capture_output=True,
                text=True,
                shell=True,
            )
            return True, "Scheduler removed"
        except Exception as e:
            return False, f"Error uninstalling scheduler: {str(e)}"

    def is_installed_windows(self) -> bool:
        """Check if Windows task is installed."""
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/tn", self.task_name],
                capture_output=True,
                text=True,
                shell=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install(self, hour: int, minute: int) -> Tuple[bool, str]:
        """
        Install OS scheduler for the current platform.

        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)

        Returns:
            Tuple of (success, message)
        """
        if self.system == "Darwin":
            return self.install_macos(hour, minute)
        elif self.system == "Windows":
            return self.install_windows(hour, minute)
        else:
            return False, f"Unsupported platform: {self.system}"

    def uninstall(self) -> Tuple[bool, str]:
        """
        Uninstall OS scheduler for the current platform.

        Returns:
            Tuple of (success, message)
        """
        if self.system == "Darwin":
            return self.uninstall_macos()
        elif self.system == "Windows":
            return self.uninstall_windows()
        else:
            return False, f"Unsupported platform: {self.system}"

    def is_installed(self) -> bool:
        """Check if OS scheduler is installed for the current platform."""
        if self.system == "Darwin":
            return self.is_installed_macos()
        elif self.system == "Windows":
            return self.is_installed_windows()
        else:
            return False

    def get_status(self) -> str:
        """Get the current scheduler status."""
        if self.is_installed():
            return "Installed and active"
        else:
            return "Not installed"
