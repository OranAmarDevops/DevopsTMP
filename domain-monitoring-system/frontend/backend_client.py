import logging
import os
from urllib.parse import quote

import requests

from settings import load_settings


frontend_settings = load_settings("frontend")["backend"]
logger = logging.getLogger(__name__)

BACKEND_URL = os.environ.get(
    "BACKEND_URL",
    frontend_settings["base_url"]
).rstrip("/")

REQUEST_TIMEOUT = frontend_settings[
    "timeout_seconds"
]


class BackendUnavailable(Exception):
    """Raised when the frontend cannot contact the backend."""


def _request(method, path, **kwargs):
    url = f"{BACKEND_URL}{path}"

    try:
        response = requests.request(
            method=method,
            url=url,
            timeout=REQUEST_TIMEOUT,
            **kwargs
        )
    except requests.RequestException as exc:
        logger.exception(
            "Backend request failed; method=%s path=%s",
            method,
            path
        )
        raise BackendUnavailable(
            "Backend service is unavailable"
        ) from exc

    try:
        data = response.json()
    except ValueError:
        logger.error(
            "Backend returned invalid JSON; method=%s path=%s status=%s",
            method,
            path,
            response.status_code
        )
        return {
            "success": False,
            "message": "Backend returned an invalid response"
        }, 502

    return data, response.status_code


def register_user(username, password):
    return _request(
        "POST",
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": password
        }
    )


def login_user(username, password):
    return _request(
        "POST",
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": password
        }
    )


def get_domains(username):
    return _request(
        "GET",
        "/api/v1/domains",
        params={"username": username}
    )


def add_domain(username, domain):
    return _request(
        "POST",
        "/api/v1/domains",
        json={
            "username": username,
            "domain": domain
        }
    )


def remove_domain(username, domain):
    encoded_domain = quote(domain, safe="")

    return _request(
        "DELETE",
        f"/api/v1/domains/{encoded_domain}",
        params={"username": username}
    )


def remove_all_domains(username):
    return _request(
        "DELETE",
        "/api/v1/domains",
        params={"username": username}
    )


def bulk_add_domains(username, domains):
    return _request(
        "POST",
        "/api/v1/domains/bulk",
        json={
            "username": username,
            "domains": domains
        }
    )


def scan_all(username):
    return _request(
        "POST",
        "/api/v1/scan",
        json={"username": username}
    )


def scan_one(username, domain):
    encoded_domain = quote(domain, safe="")

    return _request(
        "POST",
        f"/api/v1/scan/{encoded_domain}",
        json={"username": username}
    )


def start_schedule(
    username,
    interval_hours=None,
    daily_time=None
):
    return _request(
        "POST",
        "/api/v1/schedule/start",
        json={
            "username": username,
            "interval_hours": interval_hours,
            "daily_time": daily_time
        }
    )


def stop_schedule(username):
    return _request(
        "POST",
        "/api/v1/schedule/stop",
        json={"username": username}
    )


def get_schedule_status(username):
    return _request(
        "GET",
        "/api/v1/schedule/status",
        params={"username": username}
    )
