import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request

from logging_setup import configure_logging
from settings import load_settings
from elasticapm.contrib.flask import ElasticAPM


settings = load_settings("backend")
backend_settings = settings["server"]
backend_root = os.path.dirname(os.path.abspath(__file__))

logger = configure_logging(
    "backend",
    settings,
    backend_root
)

from backend.services import (  # noqa: E402
    auth_service,
    domain_service,
    monitoring_service,
)

app = Flask(__name__)
apm = ElasticAPM(app)

scheduler = BackgroundScheduler()
scheduler.start()


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "backend"
    }), 200


@app.post("/api/v1/auth/register")
def register():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    success = auth_service.register_user(
        username,
        password
    )

    if not success:
        logger.info(
            "Registration rejected; username already exists: %s",
            username
        )
        return jsonify({
            "success": False,
            "message": "Username already exists"
        }), 409

    logger.info(
        "New user registered: %s",
        username
    )

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "username": username
    }), 201


@app.post("/api/v1/auth/login")
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    success = auth_service.login_user(
        username,
        password
    )

    if not success:
        logger.warning(
            "Login failed for username: %s",
            username
        )
        return jsonify({
            "success": False,
            "message": "Invalid username or password"
        }), 401

    logger.info(
        "User logged in: %s",
        username
    )

    return jsonify({
        "success": True,
        "message": "Login successful",
        "username": username
    }), 200


@app.get("/api/v1/domains")
def get_domains():
    username = request.args.get(
        "username",
        ""
    ).strip()

    if not username:
        return jsonify({
            "success": False,
            "message": "Username is required"
        }), 400

    domains = domain_service.get_domains(username)

    return jsonify({
        "success": True,
        "domains": domains
    }), 200


@app.post("/api/v1/domains")
def add_domain():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    domain = data.get("domain", "").strip().lower()

    if not username or not domain:
        return jsonify({
            "success": False,
            "message": "Username and domain are required"
        }), 400

    success = domain_service.add_domain(
        username,
        domain
    )

    if not success:
        logger.info(
            "Domain add skipped; already exists; username=%s domain=%s",
            username,
            domain
        )
        return jsonify({
            "success": False,
            "message": "Domain already exists"
        }), 409

    logger.info(
        "Domain added; username=%s domain=%s",
        username,
        domain
    )

    return jsonify({
        "success": True,
        "message": "Domain added successfully",
        "domain": domain
    }), 201


@app.delete("/api/v1/domains/<path:domain>")
def remove_domain(domain):
    username = request.args.get(
        "username",
        ""
    ).strip()

    domain = domain.strip().lower()

    if not username:
        return jsonify({
            "success": False,
            "message": "Username is required"
        }), 400

    success = domain_service.remove_domain(
        username,
        domain
    )

    if not success:
        logger.warning(
            "Domain removal failed; not found; username=%s domain=%s",
            username,
            domain
        )
        return jsonify({
            "success": False,
            "message": "Domain not found"
        }), 404

    logger.info(
        "Domain removed; username=%s domain=%s",
        username,
        domain
    )

    return jsonify({
        "success": True,
        "message": "Domain removed"
    }), 200


@app.delete("/api/v1/domains")
def remove_all_domains():
    username = request.args.get(
        "username",
        ""
    ).strip()

    if not username:
        return jsonify({
            "success": False,
            "message": "Username is required"
        }), 400

    domain_service.remove_all_domains(username)

    logger.info(
        "All domains removed; username=%s",
        username
    )

    return jsonify({
        "success": True,
        "message": "All domains removed"
    }), 200


@app.post("/api/v1/domains/bulk")
def bulk_add_domains():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    domains = data.get("domains", [])

    if not username:
        return jsonify({
            "success": False,
            "message": "Username is required"
        }), 400

    if not isinstance(domains, list):
        return jsonify({
            "success": False,
            "message": "Domains must be a list"
        }), 400

    added = 0
    skipped = 0

    for domain in domains:
        if not isinstance(domain, str):
            skipped += 1
            continue

        domain = domain.strip().lower()

        if not domain:
            skipped += 1
            continue

        if domain_service.add_domain(
            username,
            domain
        ):
            added += 1
        else:
            skipped += 1

    logger.info(
        "Bulk domain upload completed; username=%s added=%s skipped=%s",
        username,
        added,
        skipped
    )

    return jsonify({
        "success": True,
        "message": f"Added {added} domains",
        "added": added,
        "skipped": skipped
    }), 201


@app.post("/api/v1/scan")
def scan_all():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()

    if not username:
        return jsonify({
            "success": False,
            "message": "Username is required"
        }), 400

    logger.info(
        "Domain scan started; username=%s",
        username
    )

    stats = monitoring_service.scan_all(username)

    logger.info(
        "Domain scan completed; username=%s total=%s errors=%s elapsed=%ss",
        username,
        stats["total"],
        stats["errors"],
        stats["elapsed_sec"]
    )

    return jsonify({
        "success": True,
        "message": (
            f"Scan complete in {stats['elapsed_sec']}s - "
            f"{stats['total']} domains, "
            f"{stats['error_pct']}% errors"
        ),
        "stats": stats
    }), 200


@app.post("/api/v1/scan/<path:domain>")
def scan_one(domain):
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    domain = domain.strip().lower()

    if not username or not domain:
        return jsonify({
            "success": False,
            "message": "Username and domain are required"
        }), 400

    domains = domain_service.get_domains(username)

    domain_entry = None

    for current_domain in domains:
        if current_domain["domain"] == domain:
            domain_entry = current_domain.copy()
            break

    if domain_entry is None:
        return jsonify({
            "success": False,
            "message": "Domain not found"
        }), 404

    logger.info(
        "Single domain scan started; username=%s domain=%s",
        username,
        domain
    )

    monitoring_service.check_domain(
        username,
        domain_entry
    )

    logger.info(
        "Single domain scan completed; username=%s domain=%s status=%s",
        username,
        domain,
        domain_entry["status"]
    )

    return jsonify({
        "success": True,
        "message": f"Scan complete for {domain}",
        "domain": domain_entry
    }), 200


@app.post("/api/v1/schedule/start")
def schedule_start():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    interval_hours = data.get("interval_hours")
    daily_time = data.get("daily_time")

    if not username:
        return jsonify({
            "success": False,
            "message": "Username is required"
        }), 400

    job_id = f"scan_{username}"

    if interval_hours not in (None, ""):
        try:
            interval_hours = int(interval_hours)

            if interval_hours < 1:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "Interval must be a positive number"
            }), 400

        job = scheduler.add_job(
            func=monitoring_service.scan_all,
            args=[username],
            trigger="interval",
            hours=interval_hours,
            id=job_id,
            replace_existing=True
        )

        next_run = job.next_run_time.strftime(
            "%Y-%m-%d %H:%M"
        )

        logger.info(
            "Schedule started; username=%s interval_hours=%s next_run=%s",
            username,
            interval_hours,
            next_run
        )

        return jsonify({
            "success": True,
            "message": (
                f"Schedule started every "
                f"{interval_hours} hour(s)"
            ),
            "next_run": next_run
        }), 200

    if daily_time:
        try:
            parsed_time = datetime.strptime(
                daily_time,
                "%H:%M"
            )
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Daily time must use HH:MM format"
            }), 400

        job = scheduler.add_job(
            func=monitoring_service.scan_all,
            args=[username],
            trigger="cron",
            hour=parsed_time.hour,
            minute=parsed_time.minute,
            id=job_id,
            replace_existing=True
        )

        next_run = job.next_run_time.strftime(
            "%Y-%m-%d %H:%M"
        )

        logger.info(
            "Schedule started; username=%s daily_time=%s next_run=%s",
            username,
            daily_time,
            next_run
        )

        return jsonify({
            "success": True,
            "message": (
                f"Schedule started daily at "
                f"{daily_time}"
            ),
            "next_run": next_run
        }), 200

    return jsonify({
        "success": False,
        "message": "No schedule configuration provided"
    }), 400


@app.post("/api/v1/schedule/stop")
def schedule_stop():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()

    if not username:
        return jsonify({
            "success": False,
            "message": "Username is required"
        }), 400

    job_id = f"scan_{username}"
    job = scheduler.get_job(job_id)

    if job is None:
        logger.warning(
            "Schedule stop requested with no active schedule; username=%s",
            username
        )
        return jsonify({
            "success": False,
            "message": "No active schedule"
        }), 404

    scheduler.remove_job(job_id)

    logger.info(
        "Schedule stopped; username=%s",
        username
    )

    return jsonify({
        "success": True,
        "message": "Schedule stopped"
    }), 200


@app.get("/api/v1/schedule/status")
def schedule_status():
    username = request.args.get(
        "username",
        ""
    ).strip()

    if not username:
        return jsonify({
            "success": False,
            "message": "Username is required"
        }), 400

    job_id = f"scan_{username}"
    job = scheduler.get_job(job_id)

    if job:
        next_run = job.next_run_time.strftime(
            "%Y-%m-%d %H:%M"
        )

        return jsonify({
            "success": True,
            "active": True,
            "next_run": next_run
        }), 200

    return jsonify({
        "success": True,
        "active": False,
        "next_run": None
    }), 200


if __name__ == "__main__":
    app.run(
        host=backend_settings["host"],
        port=backend_settings["port"],
        debug=backend_settings["debug"]
    )
