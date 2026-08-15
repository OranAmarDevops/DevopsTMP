// Show/Hide Password
document.getElementById('togglePassword')?.addEventListener('click', function() {
    const pwd = document.getElementById('passwordInput');
    const isHidden = pwd.type === 'password';
    pwd.type = isHidden ? 'text' : 'password';
    this.textContent = isHidden ? 'Hide' : 'Show';
});

// Register
document.getElementById('registerForm')?.addEventListener('submit', function(event) {
    event.preventDefault();

    const user = document.getElementById('userInput').value.trim();
    const password = document.getElementById('passwordInput').value.trim();
    const rememberMe = document.getElementById('rememberMe')?.checked;
    const submitBtn = document.getElementById('submitBtn');
    const userError = document.getElementById('userError');
    const passwordError = document.getElementById('passwordError');

    userError.style.display = 'none';
    passwordError.style.display = 'none';

    if (!user) {
        userError.textContent = 'Username is required.';
        userError.style.display = 'block';
        return;
    }
    if (password.length < 4) {
        passwordError.textContent = 'Password must be at least 4 characters.';
        passwordError.style.display = 'block';
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Loading...';

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password, remember_me: rememberMe })
    })
    .then(response => {
        const status = response.status;
        return response.json().then(data => ({ status, data }));
    })
    .then(({ status, data }) => {
        if (status === 201) {
            window.location.href = '/dashboard';
        } else {
            userError.textContent = data.message;
            userError.style.display = 'block';
        }
    })
    .catch(() => {
        userError.textContent = '❌ An error occurred.';
        userError.style.display = 'block';
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Register';
    });
});

// Login
document.getElementById('loginForm')?.addEventListener('submit', function(event) {
    event.preventDefault();

    const user = document.getElementById('userInput').value.trim();
    const password = document.getElementById('passwordInput').value.trim();
    const rememberMe = document.getElementById('rememberMe')?.checked;
    const submitBtn = document.getElementById('submitBtn');
    const userError = document.getElementById('userError');
    const passwordError = document.getElementById('passwordError');

    userError.style.display = 'none';
    passwordError.style.display = 'none';

    if (!user) {
        userError.textContent = 'Username is required.';
        userError.style.display = 'block';
        return;
    }
    if (!password) {
        passwordError.textContent = 'Password is required.';
        passwordError.style.display = 'block';
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Loading...';

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password, remember_me: rememberMe })
    })
    .then(response => {
        const status = response.status;
        return response.json().then(data => ({ status, data }));
    })
    .then(({ status, data }) => {
        if (status === 200) {
            window.location.href = '/dashboard';
        } else {
            passwordError.textContent = data.message;
            passwordError.style.display = 'block';
        }
    })
    .catch(() => {
        passwordError.textContent = '❌ An error occurred.';
        passwordError.style.display = 'block';
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Login';
    });
});

// Remove All
document.getElementById('removeAllBtn')?.addEventListener('click', function() {
    fetch('/remove_all', { method: 'POST' })
    .then(() => window.location.reload())
    .catch(() => alert('❌ Failed to remove all domains.'));
});

// Remove Domain
document.querySelectorAll('.removeBtn').forEach(btn => {
    btn.addEventListener('click', function() {
        const domain = this.getAttribute('data-domain');
        fetch('/remove_domain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain })
        })
        .then(() => window.location.reload())
        .catch(() => alert('❌ Failed to remove domain.'));
    });
});

// Add Domain
document.getElementById('addBtn')?.addEventListener('click', function() {
    const domain = document.getElementById('domainInput').value.trim();
    if (!domain) return;

    fetch('/add_domain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain })
    })
    .then(() => window.location.reload())
    .catch(() => alert('❌ Failed to add domain.'));
});

// Scan All
document.getElementById('scanBtn')?.addEventListener('click', function() {
    fetch('/scan', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        document.getElementById('result').textContent = data.message;
        setTimeout(() => window.location.reload(), 1500);
    })
    .catch(() => alert('❌ Scan failed.'));
});

document.getElementById('uploadForm')?.addEventListener('submit', function(event) {
    event.preventDefault();
   
    const file = document.getElementById('fileInput').files[0];
    if (!file) return;
   
    const formData = new FormData();
    formData.append('file', file);  
   
    fetch('/bulk_upload', {
        method: 'POST',
        body: formData  
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('result').textContent = data.message;
        setTimeout(() => window.location.reload(), 1000);
    })
    .catch(() => {
    document.getElementById('result').textContent = "❌ An error occurred.";
})
});

// Schedule - load status on page load
if (document.getElementById('startScheduleBtn')) {
    fetch('/schedule/status')
    .then(r => r.json())
    .then(data => {
        if (data.active) {
            document.getElementById('nextCheck').textContent = `Next check: ${data.next_run}`;
        }
    });
}

// Start Schedule
document.getElementById('startScheduleBtn')?.addEventListener('click', function() {
    this.disabled = true;
    const scheduleType = document.querySelector('input[name="scheduleType"]:checked')?.value;
    const intervalHours = document.getElementById('intervalHours').value;
    const dailyTime = document.getElementById('dailyTime').value;

    const body = scheduleType === 'interval'
        ? { interval_hours: intervalHours }
        : { daily_time: dailyTime };

    fetch('/schedule/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('result').textContent = data.message;
        if (data.next_run) {
            document.getElementById('nextCheck').textContent = `Next check: ${data.next_run}`;
        }
        this.disabled = false;
    })
    .catch(() => {
        alert('❌ Failed to start schedule.');
        this.disabled = false;
    });
});

// Stop Schedule
document.getElementById('stopScheduleBtn')?.addEventListener('click', function() {
    fetch('/schedule/stop', { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        document.getElementById('result').textContent = data.message;
        document.getElementById('nextCheck').textContent = 'Next check: —';
    })
    .catch(() => alert('❌ Failed to stop schedule.'));
});
