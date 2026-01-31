"""
Built-in scheduler for running automation at scheduled times
Uses the `schedule` library for in-app scheduling
"""

import schedule
import threading
import time
from typing import Callable, Optional
from datetime import datetime


class BuiltInScheduler:
    """Built-in scheduler for running automation at scheduled times."""

    def __init__(
        self,
        run_callback: Callable[[], None],
        log_callback: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Initialize the scheduler.

        Args:
            run_callback: Function to call when scheduled time is reached
            log_callback: Function to call for logging (level, message)
        """
        self.run_callback = run_callback
        self.log_callback = log_callback
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _log(self, level: str, message: str):
        """Log a message."""
        if self.log_callback:
            self.log_callback(level, message)

    def _run_job(self):
        """Execute the scheduled job."""
        self._log("INFO", f"Scheduled job starting at {datetime.now().strftime('%H:%M:%S')}")
        try:
            self.run_callback()
            self._log("SUCCESS", "Scheduled job completed")
        except Exception as e:
            self._log("ERROR", f"Scheduled job failed: {str(e)}")

    def _scheduler_loop(self):
        """Main scheduler loop running in a background thread."""
        self._log("INFO", "Scheduler started")
        while not self._stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
        self._log("INFO", "Scheduler stopped")

    def set_schedule(self, hour: int, minute: int):
        """
        Set the daily schedule time.

        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
        """
        schedule.clear()
        time_str = f"{hour:02d}:{minute:02d}"
        schedule.every().day.at(time_str).do(self._run_job)
        self._log("INFO", f"Schedule set for daily at {time_str}")

    def start(self):
        """Start the scheduler."""
        if self.is_running:
            return

        self._stop_event.clear()
        self.is_running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="SchedulerThread",
        )
        self.scheduler_thread.start()

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self._stop_event.set()
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
            self.scheduler_thread = None
        schedule.clear()

    def get_next_run(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None

    def is_scheduled(self) -> bool:
        """Check if a job is scheduled."""
        return len(schedule.get_jobs()) > 0
