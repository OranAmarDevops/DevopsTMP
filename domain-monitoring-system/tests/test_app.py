import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
TEST_USERS = ['testuser_new', 'dupuser', 'loginuser', 'loginuser2',
              'domainuser', 'dupdomainuser', 'removeuser', 'removealluser']

@pytest.fixture(autouse=True)
def cleanup_test_users():
    def do_cleanup():
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
            users = [u for u in users if u['username'] not in TEST_USERS]
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f, indent=2)
        for username in TEST_USERS:
            domain_file = os.path.join(DATA_DIR, f'{username}_domains.json')
            if os.path.exists(domain_file):
                os.remove(domain_file)

    do_cleanup()
    yield
    do_cleanup()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    with app.test_client() as client:
        yield client


def test_register_success(client):
    res = client.post('/register', json={'username': 'testuser_new', 'password': 'pass1234'})
    assert res.status_code == 201

def test_register_duplicate(client):
    client.post('/register', json={'username': 'dupuser', 'password': 'pass1234'})
    res = client.post('/register', json={'username': 'dupuser', 'password': 'pass1234'})
    assert res.status_code == 409

def test_login_success(client):
    client.post('/register', json={'username': 'loginuser', 'password': 'pass1234'})
    res = client.post('/login', json={'username': 'loginuser', 'password': 'pass1234'})
    assert res.status_code == 200

def test_login_wrong_password(client):
    client.post('/register', json={'username': 'loginuser2', 'password': 'pass1234'})
    res = client.post('/login', json={'username': 'loginuser2', 'password': 'wrongpass'})
    assert res.status_code == 401

def test_health_check(client):
    res = client.get('/health')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['status'] == 'healthy'

def _login(client, username='domainuser', password='pass1234'):
    client.post('/register', json={'username': username, 'password': password})
    client.post('/login', json={'username': username, 'password': password})

def test_add_domain_success(client):
    _login(client)
    res = client.post('/add_domain', json={'domain': 'google.com'})
    assert res.status_code == 200

def test_add_domain_unauthorized(client):
    res = client.post('/add_domain', json={'domain': 'google.com'})
    assert res.status_code == 401
