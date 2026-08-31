// EduMatch PH — login/register demo logic.
// Frontend-only mock: "accounts" are stored in localStorage so the demo
// can simulate register -> login without a real backend.

const STORAGE_KEY = 'edumatch_demo_users';

function getUsers() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch (e) {
    return [];
  }
}

function saveUsers(users) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(users));
}

// ---------- Register modal ----------
const registerOverlay = document.getElementById('register-overlay');

function openRegister() {
  registerOverlay.hidden = false;
  hideBanner();
}

function closeRegister() {
  registerOverlay.hidden = true;
}

document.getElementById('open-register').addEventListener('click', openRegister);
document.getElementById('close-register').addEventListener('click', closeRegister);
document.getElementById('go-login').addEventListener('click', closeRegister);
registerOverlay.addEventListener('click', (e) => {
  if (e.target === registerOverlay) closeRegister();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !registerOverlay.hidden) closeRegister();
});

// ---------- Banner ----------
const banner = document.getElementById('form-banner');
function showBanner(message, type) {
  banner.textContent = message;
  banner.className = 'banner ' + type;
  banner.hidden = false;
}
function hideBanner() {
  banner.hidden = true;
}

// ---------- Password visibility ----------
document.querySelectorAll('.toggle-visibility').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = document.getElementById(btn.dataset.target);
    const showing = input.type === 'text';
    input.type = showing ? 'password' : 'text';
    btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
  });
});

// ---------- Validation helpers ----------
function setError(fieldId, message) {
  const errorEl = document.getElementById(fieldId + '-error');
  const inputEl = document.getElementById(fieldId);
  errorEl.textContent = message || '';
  inputEl.classList.toggle('invalid', Boolean(message));
}

function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

// ---------- Login ----------
document.getElementById('panel-login').addEventListener('submit', (e) => {
  e.preventDefault();
  hideBanner();

  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;

  let valid = true;
  setError('login-username', '');
  setError('login-password', '');

  if (!username) {
    setError('login-username', 'Enter your username.');
    valid = false;
  }
  if (!password) {
    setError('login-password', 'Enter your password.');
    valid = false;
  }
  if (!valid) return;

  const users = getUsers();
  const match = users.find(u => u.username === username && u.password === password);

  if (match) {
    showBanner(`Welcome back, ${match.fullname || username}.`, 'success');
    if (document.getElementById('remember-me').checked) {
      localStorage.setItem('edumatch_remember_username', username);
    }
    localStorage.setItem('edumatch_current_user', username);
    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 700);
  } else {
    showBanner('Username or password is incorrect.', 'error');
  }
});

// ---------- Register ----------
document.getElementById('panel-register').addEventListener('submit', (e) => {
  e.preventDefault();
  hideBanner();

  const fullname = document.getElementById('reg-fullname').value.trim();
  const username = document.getElementById('reg-username').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const confirm = document.getElementById('reg-confirm').value;

  ['reg-fullname', 'reg-username', 'reg-email', 'reg-password', 'reg-confirm'].forEach(id => setError(id, ''));

  let valid = true;

  if (!fullname) {
    setError('reg-fullname', 'Enter your full name.');
    valid = false;
  }
  if (!username) {
    setError('reg-username', 'Choose a username.');
    valid = false;
  } else if (getUsers().some(u => u.username === username)) {
    setError('reg-username', 'That username is taken.');
    valid = false;
  }
  if (!email) {
    setError('reg-email', 'Enter your email.');
    valid = false;
  } else if (!isEmail(email)) {
    setError('reg-email', 'Enter a valid email address.');
    valid = false;
  }
  if (!password) {
    setError('reg-password', 'Create a password.');
    valid = false;
  } else if (password.length < 8) {
    setError('reg-password', 'Use at least 8 characters.');
    valid = false;
  }
  if (confirm !== password) {
    setError('reg-confirm', 'Passwords do not match.');
    valid = false;
  }

  if (!valid) return;

  const users = getUsers();
  users.push({ fullname, username, email, password });
  saveUsers(users);

  document.getElementById('panel-register').reset();
  setTimeout(() => {
    closeRegister();
    document.getElementById('login-username').value = username;
    showBanner('Account created. You can log in now.', 'success');
  }, 900);
});

// ---------- Forgot password modal ----------
const forgotOverlay = document.getElementById('forgot-overlay');
const stepRequest = document.getElementById('forgot-step-request');
const stepSent = document.getElementById('forgot-step-sent');

function openForgot() {
  forgotOverlay.hidden = false;
  stepRequest.hidden = false;
  stepSent.hidden = true;
  setError('forgot-identifier', '');
  document.getElementById('forgot-identifier').value = '';
}

function closeForgot() {
  forgotOverlay.hidden = true;
}

document.getElementById('open-forgot').addEventListener('click', openForgot);
document.getElementById('close-forgot').addEventListener('click', closeForgot);
document.getElementById('close-forgot-sent').addEventListener('click', closeForgot);
forgotOverlay.addEventListener('click', (e) => {
  if (e.target === forgotOverlay) closeForgot();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !forgotOverlay.hidden) closeForgot();
});

document.getElementById('send-reset').addEventListener('click', () => {
  const identifier = document.getElementById('forgot-identifier').value.trim();
  setError('forgot-identifier', '');

  if (!identifier) {
    setError('forgot-identifier', 'Enter your username or email.');
    return;
  }

  stepRequest.hidden = true;
  stepSent.hidden = false;
});
