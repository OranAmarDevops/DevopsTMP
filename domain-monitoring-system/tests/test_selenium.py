"""
Selenium UI Tests for Domain Monitoring System
Based on Test Plan (test-plan.html)
"""
import pytest
import uuid
import time
import logging
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.insert(0, PROJECT_ROOT)

from settings import load_settings

selenium_settings = load_settings()["selenium"]

LOG_DIR = os.path.dirname(__file__)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "selenium.log"), encoding='utf-8'),
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = os.environ.get(
    "BASE_URL",
    selenium_settings["base_url"]
)
WAIT_TIMEOUT = int(os.environ.get(
    "WAIT_TIMEOUT_SECONDS",
    selenium_settings["wait_timeout_seconds"]
))
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")

HEADLESS = str(os.environ.get(
    "SELENIUM_HEADLESS",
    selenium_settings["headless"]
)).lower() in {"1", "true", "yes"}

IMPLICIT_WAIT = int(os.environ.get(
    "SELENIUM_IMPLICIT_WAIT_SECONDS",
    selenium_settings["implicit_wait_seconds"]
))

@pytest.fixture(scope="function")
def driver():
    logger.info("Setting up Chrome WebDriver...")
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if HEADLESS:
        options.add_argument("--headless=new")
   
    if CHROMEDRIVER_PATH:
        service = Service(executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
   
    driver.implicitly_wait(IMPLICIT_WAIT)
    yield driver
    logger.info("Tearing down WebDriver...")
    driver.quit()


@pytest.fixture
def unique_user():
    return f"sel_user_{uuid.uuid4().hex[:8]}"


def register_user(driver, username, password):
    driver.get(f"{BASE_URL}/register")
    driver.find_element(By.ID, "userInput").send_keys(username)
    driver.find_element(By.ID, "passwordInput").send_keys(password)
    driver.find_element(By.ID, "submitBtn").click()
    time.sleep(1)


def login_user(driver, username, password):
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.ID, "userInput").send_keys(username)
    driver.find_element(By.ID, "passwordInput").send_keys(password)
    driver.find_element(By.ID, "submitBtn").click()
    time.sleep(1)


class TestUserRegistration:
    def test_01_successful_registration(self, driver, unique_user):
        logger.info("Test 1: Successful registration - STARTED")
        driver.get(f"{BASE_URL}/register")
        driver.find_element(By.ID, "userInput").send_keys(unique_user)
        driver.find_element(By.ID, "passwordInput").send_keys("password123")
        driver.find_element(By.ID, "submitBtn").click()
        WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url
        logger.info("Test 1: Successful registration - PASSED")

    def test_03_empty_username(self, driver):
        logger.info("Test 3: Empty username - STARTED")
        driver.get(f"{BASE_URL}/register")
        
        # Remove HTML5 required attribute to test JS validation
        driver.execute_script("document.getElementById('userInput').removeAttribute('required')")
        
        driver.find_element(By.ID, "passwordInput").send_keys("password123")
        driver.find_element(By.ID, "submitBtn").click()
        time.sleep(0.5)
        user_error = driver.find_element(By.ID, "userError")
        assert user_error.is_displayed()
        assert "required" in user_error.text.lower()
        logger.info("Test 3: Empty username - PASSED")

    def test_04_short_password(self, driver, unique_user):
        logger.info("Test 4: Short password - STARTED")
        driver.get(f"{BASE_URL}/register")
        driver.find_element(By.ID, "userInput").send_keys(unique_user)
        driver.find_element(By.ID, "passwordInput").send_keys("abc")
        driver.find_element(By.ID, "submitBtn").click()
        time.sleep(0.5)
        password_error = driver.find_element(By.ID, "passwordError")
        assert password_error.is_displayed()
        assert "4 characters" in password_error.text
        logger.info("Test 4: Short password - PASSED")


class TestUserLogin:
    def test_05_successful_login(self, driver, unique_user):
        logger.info("Test 5: Successful login - STARTED")
        register_user(driver, unique_user, "password123")
        driver.get(f"{BASE_URL}/login")
        driver.find_element(By.ID, "userInput").send_keys(unique_user)
        driver.find_element(By.ID, "passwordInput").send_keys("password123")
        driver.find_element(By.ID, "submitBtn").click()
        WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url
        logger.info("Test 5: Successful login - PASSED")

    def test_06_wrong_password(self, driver, unique_user):
        logger.info("Test 6: Wrong password - STARTED")
        register_user(driver, unique_user, "password123")
        driver.get(f"{BASE_URL}/login")
        driver.find_element(By.ID, "userInput").send_keys(unique_user)
        driver.find_element(By.ID, "passwordInput").send_keys("wrongpass")
        driver.find_element(By.ID, "submitBtn").click()
        time.sleep(1)
        password_error = driver.find_element(By.ID, "passwordError")
        assert password_error.is_displayed()
        assert "invalid" in password_error.text.lower()
        logger.info("Test 6: Wrong password - PASSED")


class TestDomainManagement:
    def test_09_add_single_domain(self, driver, unique_user):
        logger.info("Test 9: Add single domain - STARTED")
        register_user(driver, unique_user, "password123")
        domain_input = driver.find_element(By.ID, "domainInput")
        domain_input.send_keys("example.com")
        driver.find_element(By.ID, "addBtn").click()
        time.sleep(1)
        driver.refresh()
        assert "example.com" in driver.page_source
        logger.info("Test 9: Add single domain - PASSED")

    def test_13_remove_all_domains(self, driver, unique_user):
        logger.info("Test 13: Remove all domains - STARTED")
        register_user(driver, unique_user, "password123")
        driver.find_element(By.ID, "domainInput").send_keys("test-domain.com")
        driver.find_element(By.ID, "addBtn").click()
        time.sleep(1)
        driver.find_element(By.ID, "removeAllBtn").click()
        time.sleep(1)
        driver.refresh()
        remove_buttons = driver.find_elements(By.CSS_SELECTOR, ".removeBtn")
        assert len(remove_buttons) == 0
        logger.info("Test 13: Remove all domains - PASSED")


class TestHealthCheck:
    def test_21_health_endpoint(self, driver):
        logger.info("Test 21: Health check - STARTED")
        driver.get(f"{BASE_URL}/health")
        assert "healthy" in driver.page_source
        logger.info("Test 21: Health check - PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
