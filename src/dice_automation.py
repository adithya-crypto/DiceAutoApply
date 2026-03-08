"""
Dice Auto Apply - Core Automation Module
Handles the automated job application process on Dice.com
"""

import logging
import yaml
import os
import json
import subprocess
import sys
from urllib.parse import quote_plus
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
    WebDriverException,
    InvalidSessionIdException,
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
            "applied_at": datetime.now().isoformat(),
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
        return sum(
            1 for job in self.applied_jobs["jobs"] if job.get("applied_at", "").startswith(today)
        )


class DiceAutomation:
    """Main automation class for Dice.com job applications."""

    def __init__(
        self,
        config: Dict[str, Any],
        data_dir: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None,
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
        self.base_dir = os.path.abspath(os.path.join(data_dir, os.pardir))
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.should_stop = False
        self.is_running = False
        self.driver = None
        self.log_file_path = self._resolve_log_file_path()

        # Paths
        self.applied_jobs_path = os.path.join(data_dir, "applied_jobs.json")
        self.tracker = AppliedJobsTracker(self.applied_jobs_path)

        # Stats
        self.current_stats = {
            "jobs_applied": 0,
            "jobs_skipped": 0,
            "jobs_failed": 0,
            "current_page": 0,
            "status": "idle",
        }

    def _resolve_log_file_path(self) -> Optional[str]:
        """Resolve log file path from config, defaulting to logs/application.log."""
        log_file = self.config.get("logging", {}).get("log_file", "logs/application.log")
        if not log_file:
            return None
        if os.path.isabs(log_file):
            return log_file
        return os.path.join(self.base_dir, log_file)

    def _append_log_file(self, level: str, message: str) -> None:
        """Append a log line to the configured log file (best effort)."""
        if not self.log_file_path:
            return
        try:
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file_path, "a") as log_file:
                log_file.write(f"{timestamp} - {level.upper()} - {message}\n")
        except Exception:
            pass

    def _log(self, level: str, message: str):
        """Log a message and optionally send to callback."""
        log_func = getattr(logging, level.lower(), logging.info)
        log_func(message)
        self._append_log_file(level, message)
        if self.log_callback:
            self.log_callback(level, message)

    def _progress(self, message: str, current: int = 0, total: int = 0):
        """Report progress."""
        self._log("INFO", message)
        if self.progress_callback:
            self.progress_callback(message, current, total)

    def _wait_for_ready_state(self, timeout: int = 15) -> bool:
        """Wait until the document readyState is complete."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except (TimeoutException, WebDriverException, InvalidSessionIdException):
            return False

    def _is_driver_alive(self) -> bool:
        """Check if the active WebDriver session is still reachable."""
        if not self.driver:
            return False
        try:
            self.driver.execute_script("return 1")
            return True
        except NoSuchWindowException:
            # Current window may be gone while session is still alive.
            handles = self._safe_window_handles()
            if not handles:
                return False
            try:
                self.driver.switch_to.window(handles[0])
                self.driver.execute_script("return 1")
                return True
            except (WebDriverException, InvalidSessionIdException, NoSuchWindowException):
                return False
        except (WebDriverException, InvalidSessionIdException):
            return False

    def _ensure_page_ready(self, timeout: int = 15) -> bool:
        """Ensure the browser session is alive and page load is complete."""
        if not self._is_driver_alive():
            return False
        return self._wait_for_ready_state(timeout)

    def _safe_window_handles(self) -> list:
        """Safely read window handles without crashing on dead sessions."""
        if not self.driver:
            return []
        try:
            return self.driver.window_handles
        except (NoSuchWindowException, WebDriverException, InvalidSessionIdException):
            return []

    def _wait_for_job_listings(self, timeout: int = 15) -> bool:
        """Wait for job listings to appear on the page."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: any(
                    "/job-detail/" in (a.get_attribute("href") or "")
                    for a in d.find_elements(By.TAG_NAME, "a")
                )
            )
            return True
        except (TimeoutException, WebDriverException, InvalidSessionIdException):
            return False

    def _wait_for_apply_controls(self, timeout: int = 10) -> bool:
        """Wait for Apply/Next/Submit controls to appear."""
        def has_controls(d):
            for el in d.find_elements(By.TAG_NAME, "button") + d.find_elements(By.TAG_NAME, "a"):
                try:
                    if el.is_displayed() and el.is_enabled():
                        text = el.text.strip().lower()
                        if text in {"apply", "easy apply", "next", "submit"}:
                            return True
                except StaleElementReferenceException:
                    continue
            return False

        try:
            WebDriverWait(self.driver, timeout).until(has_controls)
            return True
        except (TimeoutException, WebDriverException, InvalidSessionIdException):
            return False

    def _title_matches_filter(self, title: str) -> bool:
        """Check whether a job title matches the configured keyword intent."""
        configured = (self.config.get("filters", {}).get("job_title") or "").strip().lower()
        if not configured:
            return True

        title_l = (title or "").strip().lower()
        if not title_l:
            return False

        tokens = [
            t
            for t in configured.replace("/", " ").replace("-", " ").split()
            if len(t) >= 3 or t in {"ai", "ml"}
        ]
        if not tokens:
            return True

        if len(tokens) <= 2:
            return all(token in title_l for token in tokens)

        matches = sum(1 for token in tokens if token in title_l)
        return matches >= max(2, len(tokens) // 2)

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
            "last_run": self.tracker.get_stats().get("last_run"),
        }

    def get_recent_jobs(self, limit: int = 10) -> list:
        """Get recent job applications."""
        return self.tracker.get_recent_jobs(limit)

    def _clear_quarantine(self, driver_path: str) -> None:
        """Best-effort removal of macOS quarantine flag on downloaded drivers."""
        if sys.platform != "darwin":
            return
        try:
            subprocess.run(
                ["xattr", "-d", "com.apple.quarantine", driver_path],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

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
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            # Prefer Selenium Manager to match the local Chrome version/architecture.
            driver = webdriver.Chrome(options=options)
        except Exception as exc:
            self._log(
                "WARNING", f"Selenium Manager init failed; falling back to webdriver_manager: {exc}"
            )
            driver_path = ChromeDriverManager().install()
            self._clear_quarantine(driver_path)
            driver = webdriver.Chrome(
                service=ChromeService(driver_path),
                options=options,
            )
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self._progress("Browser initialized")
        return driver

    def _login(self) -> bool:
        """Log in to Dice.com."""
        self._progress("Logging in to Dice.com...")
        self.driver.get("https://www.dice.com/dashboard/login")
        self._wait_for_ready_state(15)

        try:
            # Enter email
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            email_input.clear()
            email_input.send_keys(self.config["login"]["email"])

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

            # Enter password
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_input.clear()
            password_input.send_keys(self.config["login"]["password"])

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
            self._wait_for_ready_state(15)
            self._progress("Login successful!")
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
        job_title = self.config.get("filters", {}).get("job_title", "").strip()
        query_url = f"https://www.dice.com/jobs?q={quote_plus(job_title)}" if job_title else "https://www.dice.com/jobs"
        self.driver.get(query_url)
        self._wait_for_ready_state(15)

        try:
            self._progress(f"Searching for: {job_title or 'All jobs'}")
            if not self._wait_for_job_listings(15):
                self._log("WARNING", "No job listings detected after search query load")

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

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "label"))
            )

            def click_filter_by_text(search_text):
                labels = self.driver.find_elements(By.TAG_NAME, "label")
                for label in labels:
                    try:
                        if (
                            label.is_displayed()
                            and search_text.lower() in label.text.strip().lower()
                        ):
                            self.driver.execute_script("arguments[0].click();", label)
                            self._log("INFO", f"Applied filter: {label.text.strip()}")
                            return True
                    except StaleElementReferenceException:
                        continue
                return False

            # Easy Apply (always enabled)
            click_filter_by_text("easy apply")

            # Remote/Hybrid/On-Site filters
            for option in self.config.get("filters", {}).get("remote_option", []):
                # Try the exact option first, then variations
                if click_filter_by_text(option):
                    pass
                elif option.lower() == "on-site":
                    # Try alternative spellings for On-Site
                    if click_filter_by_text("onsite") or click_filter_by_text("on site"):
                        pass

            # Employment type filters
            for emp_type in self.config.get("filters", {}).get("employment_type", []):
                if click_filter_by_text(emp_type):
                    pass

            # Click Apply button
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

            self._wait_for_job_listings(15)
            self._progress("Filters applied")
            return True

        except Exception as e:
            self._log("ERROR", f"Filter error: {str(e)}")
            return False

    def _get_job_listings(self) -> list:
        """Get job listings from current page."""
        if not self._ensure_page_ready(15):
            return []

        try:
            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/job-detail/']")
            jobs = []
            seen_hrefs = set()
            skip_texts = {"easy apply", "applied", "apply", "apply now", "save", "share", "report"}
            skipped_nonmatching = 0

            for link in all_links:
                try:
                    href = (link.get_attribute("href") or "").strip()
                    if "/job-detail/" not in href:
                        continue

                    href = href.split("#")[0]
                    if href in seen_hrefs:
                        continue

                    title = (link.text or "").strip()
                    if not title:
                        title = (link.get_attribute("aria-label") or "").strip()

                    title_l = title.lower()
                    if (
                        not title
                        or len(title) < 6
                        or title_l in skip_texts
                        or title_l.startswith("apply")
                    ):
                        continue

                    if not self._title_matches_filter(title):
                        skipped_nonmatching += 1
                        continue

                    seen_hrefs.add(href)
                    jobs.append({"url": href, "title": title})
                except StaleElementReferenceException:
                    continue

            if skipped_nonmatching:
                self._log("INFO", f"Skipped {skipped_nonmatching} jobs not matching title filter")
            return jobs
        except Exception:
            return []

    def _click_apply_button(self) -> bool:
        """Click the Apply button on job detail page."""
        if not self._ensure_page_ready(15):
            return False

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
        if not self._ensure_page_ready(15):
            return False
        self._wait_for_apply_controls(10)

        for step in range(3):
            if self.should_stop:
                return False
            if not self._ensure_page_ready(15):
                return False

            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        text = button.text.strip().lower()
                        if text == "submit":
                            if not self._ensure_page_ready(15):
                                return False
                            self.driver.execute_script("arguments[0].click();", button)
                            self._wait_for_ready_state(10)
                            return True
                        if text == "next":
                            if not self._ensure_page_ready(15):
                                return False
                            self.driver.execute_script("arguments[0].click();", button)
                            self._wait_for_ready_state(10)
                            break
                except StaleElementReferenceException:
                    continue
            else:
                if self._check_success():
                    return True
                self._wait_for_apply_controls(5)

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
        if not self._ensure_page_ready(15):
            return False
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
                if not self._ensure_page_ready(15):
                    return False
                self.driver.execute_script("arguments[0].click();", next_btn)
                self._wait_for_ready_state(15)
                self._wait_for_job_listings(15)
                return True
            except (TimeoutException, NoSuchElementException, WebDriverException, InvalidSessionIdException):
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
            "status": "running",
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

            while (
                self.current_stats["jobs_applied"] < max_jobs
                and self.current_stats["current_page"] <= max_pages
            ):
                if self.should_stop:
                    break

                self._progress(
                    f"Processing page {self.current_stats['current_page']}...",
                    self.current_stats["jobs_applied"],
                    max_jobs,
                )

                job_listings = self._get_job_listings()
                if not job_listings:
                    break

                # Store job info
                jobs_to_process = []
                for job in job_listings:
                    job_url = (job.get("url") or "").strip()
                    job_title = (job.get("title") or "").strip() or "Unknown Title"
                    if job_url:
                        jobs_to_process.append({"url": job_url, "title": job_title})

                for job_info in jobs_to_process:
                    if self.should_stop or self.current_stats["jobs_applied"] >= max_jobs:
                        break

                    if not self._is_driver_alive():
                        self._log("ERROR", "Browser session ended unexpectedly")
                        self.current_stats["status"] = "browser_disconnected"
                        self.should_stop = True
                        break

                    job_url = job_info["url"]
                    job_title = job_info["title"]
                    job_id = self._extract_job_id(job_url)

                    if self.tracker.is_applied(job_id):
                        self.current_stats["jobs_skipped"] += 1
                        continue

                    self._progress(
                        f"Applying to: {job_title[:40]}...",
                        self.current_stats["jobs_applied"],
                        max_jobs,
                    )

                    job_window = None
                    try:
                        if not self._is_driver_alive():
                            raise WebDriverException("Browser session unavailable")
                        if not self._wait_for_ready_state(15):
                            raise TimeoutException("Listings page did not finish loading")
                        existing_handles = self._safe_window_handles()
                        if main_window not in existing_handles and existing_handles:
                            main_window = existing_handles[0]
                        self.driver.execute_script(f"window.open('{job_url}', '_blank');")
                        WebDriverWait(self.driver, 10).until(
                            lambda d: len(self._safe_window_handles()) >= len(existing_handles) + 1
                        )
                        handles = self._safe_window_handles()
                        if len(handles) <= len(existing_handles):
                            raise WebDriverException("No browser windows available")
                        new_handles = [h for h in handles if h not in existing_handles]
                        job_window = new_handles[0] if new_handles else handles[-1]
                        self.driver.switch_to.window(job_window)

                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        if not self._is_driver_alive():
                            raise WebDriverException("Browser session unavailable")
                        if not self._wait_for_ready_state(15):
                            raise TimeoutException("Job details page did not finish loading")

                        company = "Unknown Company"
                        for selector in [
                            "//a[contains(@data-cy, 'companyLink')]",
                            "//span[contains(@data-cy, 'company')]",
                        ]:
                            try:
                                elem = self.driver.find_element(By.XPATH, selector)
                                company = elem.text.strip()
                                break
                            except NoSuchElementException:
                                continue

                        if self._click_apply_button():
                            self._wait_for_apply_controls(10)
                            if self._handle_application_flow():
                                self.tracker.add_job(job_id, job_title, company, job_url, "applied")
                                self.current_stats["jobs_applied"] += 1
                                self._progress(
                                    f"Applied: {job_title[:40]}",
                                    self.current_stats["jobs_applied"],
                                    max_jobs,
                                )
                            else:
                                self.current_stats["jobs_failed"] += 1
                        else:
                            self.current_stats["jobs_failed"] += 1

                    except (WebDriverException, InvalidSessionIdException) as e:
                        self._log("ERROR", f"WebDriver session lost: {str(e)}")
                        self.current_stats["status"] = "browser_disconnected"
                        self.should_stop = True
                        self.current_stats["jobs_failed"] += 1
                        break
                    except TimeoutException as e:
                        self._log("WARNING", f"Skipping job due to load timeout: {str(e)}")
                        self.current_stats["jobs_failed"] += 1
                    except Exception as e:
                        self._log("ERROR", f"Error: {str(e)}")
                        self.current_stats["jobs_failed"] += 1

                    finally:
                        try:
                            handles = self._safe_window_handles()
                            if job_window and job_window in handles and job_window != main_window:
                                self.driver.switch_to.window(job_window)
                                self.driver.close()
                            handles = self._safe_window_handles()
                            if main_window in handles:
                                self.driver.switch_to.window(main_window)
                            elif handles:
                                self.driver.switch_to.window(handles[0])
                                main_window = self.driver.current_window_handle
                        except (NoSuchWindowException, WebDriverException, InvalidSessionIdException):
                            handles = self._safe_window_handles()
                            if handles:
                                try:
                                    self.driver.switch_to.window(handles[0])
                                    main_window = self.driver.current_window_handle
                                except (WebDriverException, InvalidSessionIdException):
                                    pass
                        self._ensure_page_ready(10)

                if self.current_stats["jobs_applied"] < max_jobs and not self.should_stop:
                    if self._go_to_next_page():
                        self.current_stats["current_page"] += 1
                    else:
                        break

            if self.current_stats["status"] == "running":
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

        self._progress(
            f"Complete! Applied to {self.current_stats['jobs_applied']} jobs",
            self.current_stats["jobs_applied"],
            self.config.get("preferences", {}).get("max_jobs", 50),
        )

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
        handlers=[logging.StreamHandler()],
    )

    # Determine paths
    if getattr(sys, "frozen", False):
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
