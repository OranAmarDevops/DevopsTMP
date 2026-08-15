from flask import Flask, request, jsonify, render_template, session, redirect
import logging
import os
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from services import auth_service, domain_service, monitoring_service
from settings import load_settings


scheduler = BackgroundScheduler()
scheduler.start()

settings = load_settings()
app_settings = settings["app"]
storage_settings = settings["storage"]

app = Flask(__name__)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required")

app.config["SECRET_KEY"] = secret_key
app.permanent_session_lifetime = timedelta(
    minutes=app_settings["session_lifetime_minutes"]
)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route("/")
def index():
    if 'username' in session:
        return redirect('/dashboard')
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
   
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    success = auth_service.register_user(username, password)

    if success:
        session.permanent = True
        session['username'] = username
        logging.info(f"New user registered: {username}")
        return jsonify({'message': 'Registration successful'}), 201
    else:
        logging.warning(f"Registration failed - username already exists: {username}")
        return jsonify({'message': 'Username already exists'}), 409

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
   
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    success = auth_service.login_user(username, password)
   
    if success:
        session.permanent = True
        session['username'] = username
        logging.info(f"User logged in: {username}")
        return jsonify({'message': 'Login successful'}), 200
    else:
        logging.warning(f"Failed login attempt for username: {username}")
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/remove_all', methods=['POST'])
def remove_all():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    domain_service.remove_all_domains(session['username'])
    logging.info(f"All domains removed by {session['username']}")
    return jsonify({'message': 'All domains removed'}), 200

@app.route('/remove_domain', methods=['POST'])
def remove_domain():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.get_json()
    domain = data.get('domain')
    success = domain_service.remove_domain(session['username'], domain)
    if success:
        logging.info(f"Domain removed: {domain} by {session['username']}")
        return jsonify({'message': 'Domain removed'}), 200
    return jsonify({'message': 'Domain not found'}), 404

@app.route('/add_domain', methods=['POST'])
def add_domain():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.get_json()
    domain = data.get('domain')
    username = session['username']

    success = domain_service.add_domain(username, domain)

    if success:
        return jsonify({'message': 'Domain added successfully'}), 200
    else:
        return jsonify({'message': 'Domain already exists'}), 409

@app.route('/bulk_upload', methods=['POST'])
def bulk_upload():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    try:
        file = request.files.get('file')  
       
        if not file:
            return jsonify({'message': 'No file provided'}), 400

        content = file.read().decode('utf-8')  
        domains = content.splitlines()        
       
        username = session['username']
        added = 0
       
        for domain in domains:
            domain = domain.strip()            
            if domain:                        
                success = domain_service.add_domain(username, domain)
                if success:
                    added += 1
       
        logging.info(f"Bulk upload by {username}: {added} domains added")
        return jsonify({'message': f'Added {added} domains'}), 201
    except Exception as e:
        logging.exception(f"Bulk upload error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/logout')
def logout():
    username = session.pop('username', None)
    logging.info(f"User logged out: {username}")
    return redirect('/login')

@app.route('/scan_one', methods=['POST'])
def scan_one():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.get_json()
    domain = data.get('domain')
    domains = domain_service._load_domains(session['username'])
    entry = next((d for d in domains if d['domain'] == domain), None)
    if not entry:
        entry = {'domain': domain, 'status': 'Pending', 'ssl_expiration': 'N/A', 'ssl_issuer': 'N/A'}
    monitoring_service.check_domain(session['username'], entry)
    logging.info(f"Single scan for {domain} by {session['username']}")
    return jsonify({'message': f"Scan complete for {domain}"}), 200

@app.route('/schedule/start', methods=['POST'])
def schedule_start():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.get_json()
    interval_hours = data.get('interval_hours')
    daily_time = data.get('daily_time')
    username = session['username']
    job_id = f"scan_{username}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if interval_hours:
        scheduler.add_job(
            func=monitoring_service.scan_all,
            args=[username],
            trigger='interval',
            hours=int(interval_hours),
            id=job_id
        )
        next_run = scheduler.get_job(job_id).next_run_time.strftime('%Y-%m-%d %H:%M')
        return jsonify({'message': f'Schedule started every {interval_hours}h', 'next_run': next_run}), 200
    elif daily_time:
        hour, minute = daily_time.split(':')
        scheduler.add_job(
            func=monitoring_service.scan_all,
            args=[username],
            trigger='cron',
            hour=int(hour),
            minute=int(minute),
            id=job_id
        )
        next_run = scheduler.get_job(job_id).next_run_time.strftime('%Y-%m-%d %H:%M')
        return jsonify({'message': f'Schedule started daily at {daily_time}', 'next_run': next_run}), 200

    return jsonify({'message': 'No schedule config provided'}), 400

@app.route('/schedule/stop', methods=['POST'])
def schedule_stop():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    job_id = f"scan_{session['username']}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        return jsonify({'message': 'Schedule stopped'}), 200
    return jsonify({'message': 'No active schedule'}), 404

@app.route('/schedule/status', methods=['GET'])
def schedule_status():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    job_id = f"scan_{session['username']}"
    job = scheduler.get_job(job_id)
    if job:
        return jsonify({'active': True, 'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M')}), 200
    return jsonify({'active': False, 'next_run': None}), 200

@app.route('/scan', methods=['POST'])
def scan():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
   
    stats = monitoring_service.scan_all(session['username'])
    logging.info(f"Scan complete for {session['username']}: {stats['total']} domains in {stats['elapsed_sec']}s, {stats['error_pct']}% errors")
    return jsonify({
        'message': f"Scan complete in {stats['elapsed_sec']}s — {stats['total']} domains, {stats['error_pct']}% errors"
    }), 200

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
   
    domains = domain_service._load_domains(session['username'])
    return render_template('dashboard.html', domains=domains)


LOG_DIR = os.path.join(
    os.path.dirname(__file__),
    storage_settings["log_dir"]
)
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'app.log'),
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    app.run(
        host=app_settings["host"],
        port=app_settings["port"],
        debug=app_settings["debug"]
    )
