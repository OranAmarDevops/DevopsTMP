import ssl
import socket
import time
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from . import domain_service
import threading
from settings import load_settings

monitoring_settings = load_settings()["monitoring"]

THREAD_POOL_SIZE = monitoring_settings["thread_pool_size"]
URLS_LIMIT = monitoring_settings["urls_limit"]
REQUEST_TIMEOUT_SECONDS = monitoring_settings["request_timeout_seconds"]
TIME_LIMIT = monitoring_settings["time_limit_seconds"]
ERROR_LIMIT_PCT = monitoring_settings["error_limit_percent"]


def _check_ssl(hostname):
    context = ssl.create_default_context()
    with socket.create_connection((hostname, 443), timeout=REQUEST_TIMEOUT_SECONDS) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            expiration = cert.get("notAfter", "N/A")
            issuer_fields = dict(x[0] for x in cert.get("issuer", []))
            issuer = issuer_fields.get("organizationName", "N/A")
            return expiration, issuer


def check_domain(username, domain_entry):
    domain = domain_entry["domain"]

    try:
        response = requests.get(f"https://{domain}",timeout=REQUEST_TIMEOUT_SECONDS
    )
        domain_entry["status"] = "Live" if response.status_code == 200 else "Down"
    except Exception:
        domain_entry["status"] = "Unreachable"

    try:
        expiration, issuer = _check_ssl(domain)
        domain_entry["ssl_expiration"] = expiration
        domain_entry["ssl_issuer"] = issuer
    except Exception:
        domain_entry["ssl_expiration"] = "N/A"
        domain_entry["ssl_issuer"] = "N/A"

    domains = domain_service._load_domains(username)
    for i, d in enumerate(domains):
        if d["domain"] == domain:
            domains[i] = domain_entry
            break
    domain_service._save_domains(username, domains)


def scan_all(username):
    domains = domain_service._load_domains(username)

    if len(domains) > URLS_LIMIT:
        domains = domains[:URLS_LIMIT]

    start = time.time()
    errors = 0
    errors_lock = threading.Lock()

    def _scan_and_count(d):
        nonlocal errors
        check_domain(username, d)
        if d.get("status") == "Unreachable":
            with errors_lock:
                errors += 1

    with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as executor:
        executor.map(_scan_and_count, domains)

    elapsed = round(time.time() - start, 2)
    total = len(domains)
    error_pct = round((errors / total) * 100, 1) if total > 0 else 0

    logging.info(f"Scheduled scan for {username}: {total} domains in {elapsed}s, {error_pct}% errors")
    return {
        "total": total,
        "elapsed_sec": elapsed,
        "errors": errors,
        "error_pct": error_pct,
        "time_limit_ok": elapsed <= TIME_LIMIT,
        "error_limit_ok": error_pct <= ERROR_LIMIT_PCT
    }
