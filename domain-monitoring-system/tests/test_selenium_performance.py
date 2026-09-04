"""Small Selenium test used to compare UI performance with and without load."""

import json
import math
import os
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
RUN_LABEL = os.getenv("UI_PERF_RUN_LABEL", "baseline")
ITERATIONS = int(os.getenv("UI_PERF_ITERATIONS", "5"))
WAIT_TIMEOUT = int(os.getenv("WAIT_TIMEOUT_SECONDS", "15"))
MAX_PAGE_LOAD_MS = float(os.getenv("UI_PERF_MAX_PAGE_LOAD_MS", "15000"))

REPORT_DIR = Path(__file__).parent / "reports"


def percentile(values, percentile_value):
    """Return a nearest-rank percentile without external dependencies."""
    ordered = sorted(values)
    index = max(0, math.ceil((percentile_value / 100) * len(ordered)) - 1)
    return ordered[index]


def navigation_duration_ms(driver):
    """Read the browser's navigation duration for the current page."""
    duration = driver.execute_script(
        """
        const entry = performance.getEntriesByType('navigation')[0];
        return entry ? entry.duration : 0;
        """
    )
    return round(float(duration), 2)


def test_dashboard_performance():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1000")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    username = f"selenium_perf_{uuid.uuid4().hex[:10]}"
    password = "selenium-pass"
    dashboard_samples = []

    try:
        driver.get(f"{BASE_URL}/register")
        driver.find_element(By.ID, "userInput").send_keys(username)
        driver.find_element(By.ID, "passwordInput").send_keys(password)

        registration_started = time.perf_counter()
        driver.find_element(By.ID, "submitBtn").click()
        wait.until(EC.url_contains("/dashboard"))
        registration_ms = round(
            (time.perf_counter() - registration_started) * 1000,
            2,
        )

        for _ in range(ITERATIONS):
            started = time.perf_counter()
            driver.get(f"{BASE_URL}/dashboard")
            wait.until(EC.url_contains("/dashboard"))
            wall_clock_ms = round((time.perf_counter() - started) * 1000, 2)

            dashboard_samples.append({
                "wall_clock_ms": wall_clock_ms,
                "navigation_ms": navigation_duration_ms(driver),
            })

        screenshot_path = REPORT_DIR / f"selenium-{RUN_LABEL}-dashboard.png"
        driver.save_screenshot(str(screenshot_path))
    finally:
        driver.quit()

    wall_clock_values = [sample["wall_clock_ms"] for sample in dashboard_samples]
    navigation_values = [sample["navigation_ms"] for sample in dashboard_samples]

    report = {
        "run_label": RUN_LABEL,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "iterations": ITERATIONS,
        "registration_to_dashboard_ms": registration_ms,
        "dashboard_wall_clock_ms": {
            "average": round(statistics.mean(wall_clock_values), 2),
            "median": round(statistics.median(wall_clock_values), 2),
            "p95": percentile(wall_clock_values, 95),
            "maximum": max(wall_clock_values),
        },
        "dashboard_navigation_ms": {
            "average": round(statistics.mean(navigation_values), 2),
            "median": round(statistics.median(navigation_values), 2),
            "p95": percentile(navigation_values, 95),
            "maximum": max(navigation_values),
        },
        "samples": dashboard_samples,
    }

    report_path = REPORT_DIR / f"selenium-{RUN_LABEL}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))

    assert max(wall_clock_values) < MAX_PAGE_LOAD_MS
