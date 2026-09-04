from locust import HttpUser, task, between, tag
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

    @tag("single")
    @task
    def single_domain_submission(self):
        if not self.logged_in:
            return

        domain = f"single-{uuid.uuid4().hex[:12]}.example.com"

        with self.client.post(
            "/add_domain",
            json={"domain": domain},
            name="Single domain submission",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(
                    f"Unexpected status {response.status_code}: "
                    f"{response.text[:200]}"
                )

        logger.info(
            "single_domain_submission: status=%s",
            response.status_code
        )

    @tag("bulk")
    @task
    def bulk_domain_submission(self):
        if not self.logged_in:
            return

        domains = [
            f"bulk-{uuid.uuid4().hex[:12]}.example.com"
            for _ in range(10)
        ]
        file_content = "\n".join(domains)

        with self.client.post(
            "/bulk_upload",
            files={
                "file": (
                    "domains.txt",
                    file_content,
                    "text/plain"
                )
            },
            name="Bulk domain submission",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(
                    f"Unexpected status {response.status_code}: "
                    f"{response.text[:200]}"
                )

        logger.info(
            "bulk_domain_submission: status=%s domains=%s",
            response.status_code,
            len(domains)
        )
