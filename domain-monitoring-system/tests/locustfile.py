from locust import HttpUser, task, between
import logging
import time
import uuid
import os

LOG_DIR = os.path.dirname(__file__)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "locust.log")),
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DomainMonitorUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.username = f"locust_{uuid.uuid4().hex}"
        self.password = "locust_pass"
        self.logged_in = False
       
        for attempt in range(3):
            res = self.client.post("/register", json={'username': self.username, 'password': self.password})
            logger.info(f"register attempt {attempt+1}: status={res.status_code}")
            if res.status_code in [201, 409]:
                break
            time.sleep(0.5)
       
        res = self.client.post("/login", json={'username': self.username, 'password': self.password})
        logger.info(f"login: status={res.status_code}")
        if res.status_code == 200:
            self.logged_in = True

    @task(3)
    def scan_domains(self):
        if not self.logged_in:
            return
        res = self.client.post("/scan")
        logger.info(f"scan_domains: status={res.status_code}")

    @task(1)
    def view_dashboard(self):
        if not self.logged_in:
            return
        res = self.client.get("/dashboard")
        logger.info(f"view_dashboard: status={res.status_code}")

    @task(2)
    def add_domain(self):
        if not self.logged_in:
            return
        domain = f"test-{uuid.uuid4().hex[:8]}.com"
        res = self.client.post("/add_domain", json={'domain': domain})
        logger.info(f"add_domain: status={res.status_code}")
