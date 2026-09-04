import os
from datetime import timedelta

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
)

from frontend import backend_client
from logging_setup import configure_logging
from settings import load_settings
from elasticapm.contrib.flask import ElasticAPM


settings = load_settings("frontend")
frontend_settings = settings["server"]
frontend_root = os.path.dirname(os.path.abspath(__file__))

logger = configure_logging(
    "frontend",
    settings,
    frontend_root
)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

apm = ElasticAPM(app)

secret_key = os.environ.get("SECRET_KEY")

if not secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is required"
    )

app.config["SECRET_KEY"] = secret_key

app.permanent_session_lifetime = timedelta(
    minutes=settings["session"]["lifetime_minutes"]
)


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "frontend"
    }), 200


@app.get("/")
def index():
    if "username" in session:
        return redirect("/dashboard")

    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")
    remember_me = data.get("remember_me", False)

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    try:
        result, status_code = (
            backend_client.register_user(
                username,
                password
            )
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Registration failed; backend unavailable; username=%s",
            username
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    if result.get("success"):
        session["username"] = result["username"]
        session.permanent = bool(remember_me)
        logger.info(
            "Registration completed; username=%s",
            username
        )
    else:
        logger.warning(
            "Registration rejected; username=%s status=%s message=%s",
            username,
            status_code,
            result.get("message")
        )

    return jsonify(result), status_code


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")
    remember_me = data.get("remember_me", False)

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    try:
        result, status_code = (
            backend_client.login_user(
                username,
                password
            )
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Login failed; backend unavailable; username=%s",
            username
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    if result.get("success"):
        session["username"] = result["username"]
        session.permanent = bool(remember_me)
        logger.info(
            "Login completed; username=%s",
            username
        )
    else:
        logger.warning(
            "Login rejected; username=%s status=%s message=%s",
            username,
            status_code,
            result.get("message")
        )

    return jsonify(result), status_code


@app.get("/dashboard")
def dashboard():
    username = session.get("username")

    if not username:
        return redirect("/login")

    try:
        result, status_code = (
            backend_client.get_domains(username)
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Dashboard load failed; backend unavailable; username=%s",
            username
        )
        return render_template(
            "dashboard.html",
            domains=[],
            error="Backend service is unavailable"
        ), 503

    if status_code != 200:
        return render_template(
            "dashboard.html",
            domains=[],
            error=result.get("message")
        ), status_code

    return render_template(
        "dashboard.html",
        domains=result.get("domains", [])
    )


@app.post("/add_domain")
def add_domain():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "").strip()

    if not domain:
        return jsonify({
            "success": False,
            "message": "Domain is required"
        }), 400

    try:
        result, status_code = (
            backend_client.add_domain(
                username,
                domain
            )
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Domain add failed; backend unavailable; username=%s domain=%s",
            username,
            domain
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    logger.info(
        "Domain add completed; username=%s domain=%s status=%s success=%s",
        username,
        domain,
        status_code,
        result.get("success")
    )

    return jsonify(result), status_code


@app.post("/remove_domain")
def remove_domain():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "").strip()

    if not domain:
        return jsonify({
            "success": False,
            "message": "Domain is required"
        }), 400

    try:
        result, status_code = (
            backend_client.remove_domain(
                username,
                domain
            )
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Domain removal failed; backend unavailable; username=%s domain=%s",
            username,
            domain
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    logger.info(
        "Domain removal completed; username=%s domain=%s status=%s success=%s",
        username,
        domain,
        status_code,
        result.get("success")
    )

    return jsonify(result), status_code


@app.post("/remove_all")
def remove_all():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    try:
        result, status_code = (
            backend_client.remove_all_domains(
                username
            )
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Remove-all failed; backend unavailable; username=%s",
            username
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    logger.info(
        "Remove-all completed; username=%s status=%s success=%s",
        username,
        status_code,
        result.get("success")
    )

    return jsonify(result), status_code


@app.post("/bulk_upload")
def bulk_upload():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    uploaded_file = request.files.get("file")

    if not uploaded_file:
        logger.warning(
            "Bulk upload rejected; no file provided; username=%s",
            username
        )
        return jsonify({
            "success": False,
            "message": "No file provided"
        }), 400

    try:
        content = uploaded_file.read().decode(
            "utf-8-sig"
        )
    except UnicodeDecodeError:
        logger.warning(
            "Bulk upload rejected; invalid encoding; username=%s filename=%s",
            username,
            uploaded_file.filename
        )
        return jsonify({
            "success": False,
            "message": "The file must be a UTF-8 text file"
        }), 400

    domains = []

    for line in content.splitlines():
        domain = line.strip()

        if domain:
            domains.append(domain)

    if not domains:
        logger.warning(
            "Bulk upload rejected; no domains found; username=%s filename=%s",
            username,
            uploaded_file.filename
        )
        return jsonify({
            "success": False,
            "message": "The file does not contain domains"
        }), 400

    try:
        result, status_code = (
            backend_client.bulk_add_domains(
                username,
                domains
            )
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Bulk upload failed; backend unavailable; username=%s domain_count=%s",
            username,
            len(domains)
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    logger.info(
        "Bulk upload completed; username=%s domain_count=%s status=%s success=%s",
        username,
        len(domains),
        status_code,
        result.get("success")
    )

    return jsonify(result), status_code


@app.post("/scan")
def scan_all():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    try:
        logger.info(
            "Domain scan requested; username=%s",
            username
        )
        result, status_code = (
            backend_client.scan_all(username)
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Domain scan failed; backend unavailable; username=%s",
            username
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    logger.info(
        "Domain scan completed; username=%s status=%s success=%s",
        username,
        status_code,
        result.get("success")
    )

    return jsonify(result), status_code


@app.post("/scan_one")
def scan_one():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "").strip()

    if not domain:
        return jsonify({
            "success": False,
            "message": "Domain is required"
        }), 400

    try:
        result, status_code = (
            backend_client.scan_one(
                username,
                domain
            )
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Single domain scan failed; backend unavailable; username=%s domain=%s",
            username,
            domain
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    logger.info(
        "Single domain scan completed; username=%s domain=%s status=%s success=%s",
        username,
        domain,
        status_code,
        result.get("success")
    )

    return jsonify(result), status_code


@app.post("/schedule/start")
def schedule_start():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}

    interval_hours = data.get("interval_hours")
    daily_time = data.get("daily_time")

    try:
        logger.info(
            "Schedule start requested; username=%s interval_hours=%s daily_time=%s",
            username,
            interval_hours,
            daily_time
        )
        result, status_code = (
            backend_client.start_schedule(
                username,
                interval_hours,
                daily_time
            )
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Schedule start failed; backend unavailable; username=%s",
            username
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    logger.info(
        "Schedule start completed; username=%s status=%s success=%s",
        username,
        status_code,
        result.get("success")
    )

    return jsonify(result), status_code


@app.post("/schedule/stop")
def schedule_stop():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    try:
        logger.info(
            "Schedule stop requested; username=%s",
            username
        )
        result, status_code = (
            backend_client.stop_schedule(username)
        )
    except backend_client.BackendUnavailable:
        logger.error(
            "Schedule stop failed; backend unavailable; username=%s",
            username
        )
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    logger.info(
        "Schedule stop completed; username=%s status=%s success=%s",
        username,
        status_code,
        result.get("success")
    )

    return jsonify(result), status_code


@app.get("/schedule/status")
def schedule_status():
    username = session.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    try:
        result, status_code = (
            backend_client.get_schedule_status(
                username
            )
        )
    except backend_client.BackendUnavailable:
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    return jsonify(result), status_code


@app.get("/logout")
def logout():
    username = session.get("username")
    session.clear()
    logger.info(
        "User logged out; username=%s",
        username or "anonymous"
    )
    return redirect("/login")


if __name__ == "__main__":
    app.run(
        host=frontend_settings["host"],
        port=frontend_settings["port"],
        debug=frontend_settings["debug"]
    )
