"""
Dice Auto Apply - Core Automation Module
Handles the automated job application process on Dice.com
"""

import logging
import yaml
import time
import os
import json
import random
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchWindowException,
)


class AppliedJobsTracker:
    """Tracks applied jobs to prevent duplicates."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.applied_jobs = self._load()

    def _load(self) -> Dict:
        """Load applied jobs from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"jobs": [], "stats": {"total_applied": 0, "last_run": None}}
        return {"jobs": [], "stats": {"total_applied": 0, "last_run": None}}

    def _save(self):
        """Save applied jobs to JSON file."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.applied_jobs["stats"]["last_run"] = datetime.now().isoformat()
        with open(self.filepath, "w") as f:
            json.dump(self.applied_jobs, f, indent=2)

    def is_applied(self, job_id: str) -> bool:
        """Check if a job has already been applied to."""
        return any(job.get("job_id") == job_id for job in self.applied_jobs["jobs"])

    def add_job(self, job_id: str, job_title: str, company: str, url: str, status: str = "applied"):
        """Add a job to the applied list."""
        job_entry = {
            "job_id": job_id,
            "title": job_title,
            "company": company,
            "url": url,
            "status": status,
            "applied_at": datetime.now().isoformat()
        }
        self.applied_jobs["jobs"].append(job_entry)
        self.applied_jobs["stats"]["total_applied"] += 1
        self._save()

    def get_stats(self) -> Dict:
        """Get application statistics."""
        return self.applied_jobs["stats"]

    def get_recent_jobs(self, limit: int = 10) -> list:
        """Get recent job applications."""
        return self.applied_jobs["jobs"][-limit:][::-1]

    def get_today_count(self) -> int:
        """Get count of jobs applied today."""
        today = datetime.now().date().isoformat()
        return sum(1 for job in self.applied_jobs["jobs"]
                   if job.get("applied_at", "").startswith(today))


class DiceAutomation:
    """Main automation class for Dice.com job applications."""

    def __init__(
        self,
        config: Dict[str, Any],
        data_dir: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None
    ):
        """
        Initialize the automation.

        Args:
            config: Configuration dictionary with login, filters, preferences
            data_dir: Directory for storing data files
            progress_callback: Callback(message, current, total) for progress updates
            log_callback: Callback(level, message) for log messages
        """
        self.config = config
        self.data_dir = data_dir
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.should_stop = False
        self.is_running = False
        self.driver = None

        # Paths
        self.applied_jobs_path = os.path.join(data_dir, "applied_jobs.json")
        self.tracker = AppliedJobsTracker(self.applied_jobs_path)

        # Stats
        self.current_stats = {
            "jobs_applied": 0,
            "jobs_skipped": 0,
            "jobs_failed": 0,
            "current_page": 0,
            "status": "idle"
        }

    def _log(self, level: str, message: str):
        """Log a message and optionally send to callback."""
        log_func = getattr(logging, level.lower(), logging.info)
        log_func(message)
        if self.log_callback:
            self.log_callback(level, message)

    def _progress(self, message: str, current: int = 0, total: int = 0):
        """Report progress."""
        self._log("INFO", message)
        if self.progress_callback:
            self.progress_callback(message, current, total)

    def _rate_limit_delay(self, min_seconds: float = 2, max_seconds: float = 5):
        """Add random delay to mimic human behavior."""
        if self.should_stop:
            return
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def stop(self):
        """Request the automation to stop."""
        self.should_stop = True
        self._log("INFO", "Stop requested...")

    def get_stats(self) -> Dict:
        """Get current session stats."""
        return {
            **self.current_stats,
            "total_applied": self.tracker.get_stats()["total_applied"],
            "today_applied": self.tracker.get_today_count(),
            "last_run": self.tracker.get_stats().get("last_run")
        }

    def get_recent_jobs(self, limit: int = 10) -> list:
        """Get recent job applications."""
        return self.tracker.get_recent_jobs(limit)

    def _init_driver(self) -> webdriver.Chrome:
        """Initialize WebDriver with anti-detection options."""
        self._progress("Initializing browser...")
        options = webdriver.ChromeOptions()

        if self.config.get("preferences", {}).get("headless", False):
            options.add_argument("--headless=new")

        # Anti-detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self._progress("Browser initialized")
        return driver

    def _login(self) -> bool:
        """Log in to Dice.com."""
        self._progress("Logging in to Dice.com...")
        self.driver.get("https://www.dice.com/dashboard/login")
        self._rate_limit_delay(2, 4)

        try:
            # Enter email
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            email_input.clear()
            email_input.send_keys(self.config["login"]["email"])
            self._rate_limit_delay(1, 2)

            # Click Continue
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.is_displayed() and "Continue" in button.text:
                    self.driver.execute_script("arguments[0].click();", button)
                    break
            else:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                except NoSuchElementException:
                    self._log("ERROR", "Could not find continue button for email")
                    return False

            self._rate_limit_delay(2, 3)

            # Enter password
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_input.clear()
            password_input.send_keys(self.config["login"]["password"])
            self._rate_limit_delay(1, 2)

            # Click Continue
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.is_displayed() and "Continue" in button.text:
                    self.driver.execute_script("arguments[0].click();", button)
                    break
            else:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                except NoSuchElementException:
                    self._log("ERROR", "Could not find continue button for password")
                    return False

            WebDriverWait(self.driver, 20).until(EC.url_contains("dashboard"))
            self._progress("Login successful!")
            self._rate_limit_delay(2, 4)
            return True

        except TimeoutException:
            self._log("ERROR", "Login timed out")
            return False
        except Exception as e:
            self._log("ERROR", f"Login error: {str(e)}")
            return False

    def _apply_filters(self) -> bool:
        """Apply job search filters."""
        self._progress("Applying filters...")
        self.driver.get("https://www.dice.com/jobs")
        self._rate_limit_delay(2, 3)

        try:
            job_title = self.config["filters"]["job_title"]
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search'], input[type='text']"))
            )
            search_input.clear()
            search_input.send_keys(job_title)
            search_input.send_keys("\n")
            self._progress(f"Searching for: {job_title}")
            self._rate_limit_delay(2, 3)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )

            # Click filter button
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if button.is_displayed() and "filter" in button.text.strip().lower():
                        self.driver.execute_script("arguments[0].click();", button)
                        self._log("INFO", f"Clicked filter button")
                        break
                except StaleElementReferenceException:
                    continue
            else:
                self._log("WARNING", "Could not find filter button")
                return False

            self._rate_limit_delay(1, 1.5)

            def click_filter_by_text(search_text):
                labels = self.driver.find_elements(By.TAG_NAME, "label")
                for label in labels:
                    try:
                        if label.is_displayed() and search_text.lower() in label.text.strip().lower():
                            self.driver.execute_script("arguments[0].click();", label)
                            self._log("INFO", f"Applied filter: {label.text.strip()}")
                            return True
                    except StaleElementReferenceException:
                        continue
                return False

            # Easy Apply (always enabled)
            self._rate_limit_delay(0.5, 1)
            click_filter_by_text("easy apply")
            self._rate_limit_delay(0.3, 0.5)

            # Remote/Hybrid/On-Site filters
            for option in self.config.get("filters", {}).get("remote_option", []):
                # Try the exact option first, then variations
                if click_filter_by_text(option):
                    self._rate_limit_delay(0.3, 0.5)
                elif option.lower() == "on-site":
                    # Try alternative spellings for On-Site
                    if click_filter_by_text("onsite") or click_filter_by_text("on site"):
                        self._rate_limit_delay(0.3, 0.5)

            # Employment type filters
            for emp_type in self.config.get("filters", {}).get("employment_type", []):
                if click_filter_by_text(emp_type):
                    self._rate_limit_delay(0.3, 0.5)

            # Click Apply button
            self._rate_limit_delay(0.5, 1)
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        text = button.text.strip().lower()
                        if text in ("apply", "search", "apply filters"):
                            self.driver.execute_script("arguments[0].click();", button)
                            break
                except StaleElementReferenceException:
                    continue

            self._rate_limit_delay(2, 3)
            self._progress("Filters applied")
            return True

        except Exception as e:
            self._log("ERROR", f"Filter error: {str(e)}")
            return False

    def _get_job_listings(self) -> list:
        """Get job listings from current page."""
        try:
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            job_links = []
            seen_hrefs = set()
            skip_texts = {"easy apply", "applied", "apply", "save", "share", "report"}

            for link in all_links:
                try:
                    href = link.get_attribute("href") or ""
                    if "/job-detail/" in href and href not in seen_hrefs:
                        text = link.text.strip()
                        if text and len(text) > 5 and text.lower() not in skip_texts:
                            seen_hrefs.add(href)
                            job_links.append(link)
                except StaleElementReferenceException:
                    continue

            return job_links
        except Exception:
            return []

    def _click_apply_button(self) -> bool:
        """Click the Apply button on job detail page."""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    if link.is_displayed() and link.text.strip().lower() == "apply":
                        self.driver.execute_script("arguments[0].click();", link)
                        return True
                except StaleElementReferenceException:
                    continue
        except Exception:
            pass

        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        text = button.text.strip().lower()
                        if text in ("apply", "easy apply"):
                            self.driver.execute_script("arguments[0].click();", button)
                            return True
                except StaleElementReferenceException:
                    continue
        except Exception:
            pass

        return False

    def _handle_application_flow(self) -> bool:
        """Handle the application modal flow."""
        self._rate_limit_delay(1.5, 2)

        for step in range(3):
            if self.should_stop:
                return False

            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        text = button.text.strip().lower()
                        if text == "submit":
                            self.driver.execute_script("arguments[0].click();", button)
                            self._rate_limit_delay(2, 3)
                            return True
                        if text == "next":
                            self.driver.execute_script("arguments[0].click();", button)
                            self._rate_limit_delay(1.5, 2)
                            break
                except StaleElementReferenceException:
                    continue
            else:
                if self._check_success():
                    return True
                self._rate_limit_delay(1, 1.5)

        return self._check_success()

    def _check_success(self) -> bool:
        """Check if application was successful."""
        try:
            page_source = self.driver.page_source.lower()
            success_phrases = [
                "your application is on its way",
                "application submitted",
                "successfully applied",
                "you have applied",
                "already applied",
            ]
            return any(phrase in page_source for phrase in success_phrases)
        except Exception:
            return False

    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from URL."""
        try:
            if "/job-detail/" in url:
                return url.split("/job-detail/")[-1].split("?")[0]
            return url
        except Exception:
            return url

    def _go_to_next_page(self) -> bool:
        """Navigate to next page of results."""
        selectors = [
            "//button[contains(@aria-label, 'Next')]",
            "//a[contains(@aria-label, 'Next')]",
            "//button[contains(text(), 'Next')]",
        ]

        for selector in selectors:
            try:
                next_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if next_btn.get_attribute("disabled"):
                    return False
                self.driver.execute_script("arguments[0].click();", next_btn)
                self._rate_limit_delay(3, 5)
                return True
            except (TimeoutException, NoSuchElementException):
                continue

        return False

    def run(self) -> Dict:
        """
        Run the automation process.

        Returns:
            Dict with stats about the run
        """
        if self.is_running:
            return {"error": "Already running"}

        self.is_running = True
        self.should_stop = False
        self.current_stats = {
            "jobs_applied": 0,
            "jobs_skipped": 0,
            "jobs_failed": 0,
            "current_page": 1,
            "status": "running"
        }

        try:
            self.driver = self._init_driver()

            if not self._login():
                self.current_stats["status"] = "login_failed"
                return self.current_stats

            if self.should_stop:
                self.current_stats["status"] = "stopped"
                return self.current_stats

            if not self._apply_filters():
                self.current_stats["status"] = "filter_failed"
                return self.current_stats

            max_jobs = self.config.get("preferences", {}).get("max_jobs", 50)
            max_pages = self.config.get("preferences", {}).get("max_pages", 10)
            main_window = self.driver.current_window_handle

            while self.current_stats["jobs_applied"] < max_jobs and self.current_stats["current_page"] <= max_pages:
                if self.should_stop:
                    break

                self._progress(f"Processing page {self.current_stats['current_page']}...",
                               self.current_stats["jobs_applied"], max_jobs)

                job_listings = self._get_job_listings()
                if not job_listings:
                    break

                # Store job info
                jobs_to_process = []
                for job in job_listings:
                    try:
                        job_url = job.get_attribute("href")
                        job_title = job.text.strip() or "Unknown Title"
                        if job_url:
                            jobs_to_process.append({"url": job_url, "title": job_title})
                    except StaleElementReferenceException:
                        continue

                for job_info in jobs_to_process:
                    if self.should_stop or self.current_stats["jobs_applied"] >= max_jobs:
                        break

                    job_url = job_info["url"]
                    job_title = job_info["title"]
                    job_id = self._extract_job_id(job_url)

                    if self.tracker.is_applied(job_id):
                        self.current_stats["jobs_skipped"] += 1
                        continue

                    self._progress(f"Applying to: {job_title[:40]}...",
                                   self.current_stats["jobs_applied"], max_jobs)

                    try:
                        self.driver.execute_script(f"window.open('{job_url}', '_blank');")
                        self._rate_limit_delay(1.5, 2)
                        self.driver.switch_to.window(self.driver.window_handles[-1])

                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        self._rate_limit_delay(1.5, 2)

                        company = "Unknown Company"
                        for selector in ["//a[contains(@data-cy, 'companyLink')]", "//span[contains(@data-cy, 'company')]"]:
                            try:
                                elem = self.driver.find_element(By.XPATH, selector)
                                company = elem.text.strip()
                                break
                            except NoSuchElementException:
                                continue

                        if self._click_apply_button():
                            self._rate_limit_delay(3.5, 4)
                            if self._handle_application_flow():
                                self.tracker.add_job(job_id, job_title, company, job_url, "applied")
                                self.current_stats["jobs_applied"] += 1
                                self._progress(f"Applied: {job_title[:40]}",
                                               self.current_stats["jobs_applied"], max_jobs)
                            else:
                                self.current_stats["jobs_failed"] += 1
                        else:
                            self.current_stats["jobs_failed"] += 1

                    except Exception as e:
                        self._log("ERROR", f"Error: {str(e)}")
                        self.current_stats["jobs_failed"] += 1

                    finally:
                        try:
                            if len(self.driver.window_handles) > 1:
                                self.driver.close()
                            self.driver.switch_to.window(main_window)
                        except NoSuchWindowException:
                            if self.driver.window_handles:
                                self.driver.switch_to.window(self.driver.window_handles[0])
                                main_window = self.driver.current_window_handle

                        self._rate_limit_delay(0.5, 1)

                if self.current_stats["jobs_applied"] < max_jobs and not self.should_stop:
                    if self._go_to_next_page():
                        self.current_stats["current_page"] += 1
                    else:
                        break

            self.current_stats["status"] = "completed" if not self.should_stop else "stopped"

        except Exception as e:
            self._log("ERROR", f"Automation error: {str(e)}")
            self.current_stats["status"] = "error"

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            self.is_running = False

        self._progress(f"Complete! Applied to {self.current_stats['jobs_applied']} jobs",
                       self.current_stats["jobs_applied"],
                       self.config.get("preferences", {}).get("max_jobs", 50))

        return self.current_stats


# Standalone execution support
def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    """Main entry point for CLI usage."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )

    # Determine paths
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    config_path = os.path.join(base_dir, "config", "settings.yaml")
    data_dir = os.path.join(base_dir, "data")

    if not os.path.exists(config_path):
        logging.error(f"Config not found: {config_path}")
        return

    config = load_config(config_path)

    # Override with env vars if available
    if os.environ.get("DICE_EMAIL"):
        config["login"]["email"] = os.environ.get("DICE_EMAIL")
    if os.environ.get("DICE_PASSWORD"):
        config["login"]["password"] = os.environ.get("DICE_PASSWORD")

    automation = DiceAutomation(config, data_dir)
    stats = automation.run()

    logging.info(f"Results: {stats}")


if __name__ == "__main__":
    main()
