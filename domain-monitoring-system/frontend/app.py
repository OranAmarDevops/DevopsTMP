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
from settings import load_settings


settings = load_settings()
frontend_settings = settings["frontend"]

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

secret_key = os.environ.get("SECRET_KEY")

if not secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is required"
    )

app.config["SECRET_KEY"] = secret_key

app.permanent_session_lifetime = timedelta(
    minutes=frontend_settings[
        "session_lifetime_minutes"
    ]
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
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    if result.get("success"):
        session["username"] = result["username"]
        session.permanent = bool(remember_me)

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
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

    if result.get("success"):
        session["username"] = result["username"]
        session.permanent = bool(remember_me)

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
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

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
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

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
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

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
        return jsonify({
            "success": False,
            "message": "No file provided"
        }), 400

    try:
        content = uploaded_file.read().decode(
            "utf-8-sig"
        )
    except UnicodeDecodeError:
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
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

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
        result, status_code = (
            backend_client.scan_all(username)
        )
    except backend_client.BackendUnavailable:
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

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
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

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
        result, status_code = (
            backend_client.start_schedule(
                username,
                interval_hours,
                daily_time
            )
        )
    except backend_client.BackendUnavailable:
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

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
        result, status_code = (
            backend_client.stop_schedule(username)
        )
    except backend_client.BackendUnavailable:
        return jsonify({
            "success": False,
            "message": "Backend service is unavailable"
        }), 503

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
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(
        host=frontend_settings["host"],
        port=frontend_settings["port"],
        debug=frontend_settings["debug"]
    )