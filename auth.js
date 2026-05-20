document.addEventListener('DOMContentLoaded', () => {

  // ===== TICKER =====
  const msgs = [
    '<span class="material-symbols-rounded">emergency</span> URGENT: O- blood needed at AIIMS Delhi',
    '<span class="material-symbols-rounded">check_circle</span> 45 units donated today across Mumbai',
    '<span class="material-symbols-rounded">local_hospital</span> New hospital onboarded: Fortis Bangalore',
    '<span class="material-symbols-rounded">bolt</span> Emergency fulfilled in 8 min — Hyderabad',
    '<span class="material-symbols-rounded">link</span> 12,847 blockchain transactions verified',
    '<span class="material-symbols-rounded">bloodtype</span> Blood drive: Chennai — May 25, 2026',
  ];
  const tickerEl = document.getElementById('authTickerContent');
  const html = msgs.map(m => `<span><span class="pulse-dot"></span>${m}</span>`).join('');
  tickerEl.innerHTML = html + html;

  // ===== STATE =====
  let currentMode = 'login';
  let currentRole = 'donor';
  const API_BASE = window.HEMOCHAIN_API_BASE || (location.hostname === 'localhost' ? 'http://localhost:5000' : location.origin);
  const AUTH_TOKEN_KEY = 'hemochain_auth_token';
  const REFRESH_TOKEN_KEY = 'hemochain_refresh_token';
  const AUTH_ROLE_KEY = 'hemochain_auth_role';
  const AUTH_USER_KEY = 'hemochain_auth_user';
  const FRONTEND_ROUTES = {
    '/donor-dashboard': 'dashboard.html',
    '/hospital-dashboard': 'hospital.html',
    '/bloodbank-dashboard': 'bloodbank.html',
    '/admin-dashboard': 'admin/dashboard.html',
  };

  // ===== TABS =====
  const tabLogin = document.getElementById('tabLogin');
  const tabSignup = document.getElementById('tabSignup');
  const indicator = document.getElementById('tabIndicator');

  function setMode(mode) {
    currentMode = mode;
    tabLogin.classList.toggle('active', mode === 'login');
    tabSignup.classList.toggle('active', mode === 'signup');
    indicator.classList.toggle('right', mode === 'signup');
    showForm();
  }
  tabLogin.addEventListener('click', () => setMode('login'));
  tabSignup.addEventListener('click', () => setMode('signup'));

  // ===== ROLE SELECTION =====
  const roleCards = document.querySelectorAll('.role-card');
  roleCards.forEach(card => {
    card.addEventListener('click', () => {
      roleCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      currentRole = card.dataset.role;
      showForm();
    });
  });

  // ===== SHOW FORM =====
  function showForm() {
    const formId = `form-${currentMode}-${currentRole}`;
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    const target = document.getElementById(formId);
    if (target) {
      target.classList.add('active');
      target.style.animation = 'none';
      target.offsetHeight;
      target.style.animation = '';
    }
  }

  function resolveFrontendRedirect(redirect, role) {
    if (FRONTEND_ROUTES[redirect]) return FRONTEND_ROUTES[redirect];
    if (redirect) return redirect;
    return FRONTEND_ROUTES[`/${role}-dashboard`] || 'index.html';
  }

  function authStorage(remember) {
    return remember ? localStorage : sessionStorage;
  }

  function saveAuthSession(data, remember) {
    const storage = authStorage(remember);
    // Clear BOTH stores first to prevent stale role conflicts
    [localStorage, sessionStorage].forEach(s =>
      [AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, AUTH_ROLE_KEY, AUTH_USER_KEY].forEach(k => s.removeItem(k))
    );
    storage.setItem(AUTH_TOKEN_KEY, data.token);
    storage.setItem(REFRESH_TOKEN_KEY, data.refresh_token || '');
    storage.setItem(AUTH_ROLE_KEY, data.role);
    storage.setItem(AUTH_USER_KEY, JSON.stringify(data.user || {}));
  }

  function collectPayload(form) {
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((value, key) => {
      if (value instanceof File) return;
      payload[key] = typeof value === 'string' ? value.trim() : value;
    });
    return payload;
  }

  function showAuthMessage(message, type = 'error') {
    const formsWrapper = document.getElementById('formsWrapper');
    let messageBox = document.getElementById('authApiMessage');
    if (!messageBox && formsWrapper) {
      messageBox = document.createElement('div');
      messageBox.id = 'authApiMessage';
      messageBox.className = 'api-message';
      formsWrapper.before(messageBox);
    }
    if (!messageBox) {
      alert(message);
      return;
    }
    messageBox.textContent = message;
    messageBox.className = `api-message ${type}`;
  }

  function setSubmitting(form, loading) {
    const button = form.querySelector('button[type="submit"]');
    if (!button) return;
    if (!button.dataset.originalHtml) button.dataset.originalHtml = button.innerHTML;
    button.disabled = loading;
    button.innerHTML = loading
      ? '<span class="material-symbols-rounded">progress_activity</span> Processing...'
      : button.dataset.originalHtml;
  }

  async function submitAuthForm(form) {
    const payload = collectPayload(form);
    const endpoint = `${API_BASE}/api/auth/${currentRole}/${currentMode}`;
    setSubmitting(form, true);

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        showAuthMessage(data.message || 'Authentication failed. Please try again.');
        return;
      }

      if (currentMode === 'signup') {
        showAuthMessage('Signup successful. Please log in with your new account.', 'success');
        setMode('login');
        const emailInput = document.querySelector(`#form-login-${currentRole} input[name="email"]`);
        if (emailInput && payload.email) emailInput.value = payload.email;
        return;
      }

      const remember = Boolean(form.querySelector('input[type="checkbox"]')?.checked);
      saveAuthSession(data, remember);
      showAuthMessage('Login successful. Redirecting...', 'success');
      window.location.href = resolveFrontendRedirect(data.redirect, data.role);
    } catch (error) {
      showAuthMessage('Unable to reach the Hemo Chain API. Check that Flask is running on port 5000.');
    } finally {
      setSubmitting(form, false);
    }
  }

  // ===== TOGGLE PASSWORD =====
  document.querySelectorAll('.toggle-pass').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.parentElement.querySelector('input');
      const icon = btn.querySelector('.material-symbols-rounded');
      if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = 'visibility';
      } else {
        input.type = 'password';
        icon.textContent = 'visibility_off';
      }
    });
  });

  // ===== PASSWORD STRENGTH =====
  document.querySelectorAll('.pass-input[data-strength]').forEach(input => {
    const bar = input.closest('.auth-form').querySelector('.strength-fill');
    const text = input.closest('.auth-form').querySelector('.strength-text');

    input.addEventListener('input', () => {
      const val = input.value;
      let score = 0;
      if (val.length >= 6) score++;
      if (val.length >= 10) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;

      const levels = [
        { w: '0%', c: '', t: '' },
        { w: '20%', c: '#ef4444', t: 'Weak' },
        { w: '40%', c: '#f97316', t: 'Fair' },
        { w: '60%', c: '#eab308', t: 'Good' },
        { w: '80%', c: '#22c55e', t: 'Strong' },
        { w: '100%', c: '#16a34a', t: 'Very Strong' },
      ];
      const lvl = levels[score] || levels[0];
      if (bar) {
        bar.style.width = lvl.w;
        bar.style.background = lvl.c;
      }
      if (text) {
        text.textContent = val ? lvl.t : '';
        text.style.color = lvl.c;
      }
    });
  });

  // ===== FILE UPLOAD =====
  const fileInput = document.getElementById('licenseUpload');
  if (fileInput) {
    fileInput.addEventListener('change', () => {
      const label = fileInput.closest('.file-label');
      const nameSpan = label.querySelector('.file-text');
      nameSpan.textContent = fileInput.files[0] ? fileInput.files[0].name : 'Upload License Document';
      if (fileInput.files[0]) nameSpan.style.color = '#1a1a2e';
    });
  }

  // ===== FORM SUBMIT → BACKEND API =====
  document.querySelectorAll('.auth-form').forEach(form => {
    form.addEventListener('submit', e => {
      e.preventDefault();
      submitAuthForm(form);
    });
  });

  // ===== OTP MODAL =====
  const otpModal = document.getElementById('otpModal');
  const otpClose = document.getElementById('otpClose');
  const otpInputs = document.querySelectorAll('.otp-box');

  function showOtpModal() {
    otpModal.classList.add('active');
    otpInputs.forEach(i => i.value = '');
    otpInputs[0].focus();
    startOtpTimer();
  }

  otpClose.addEventListener('click', () => otpModal.classList.remove('active'));
  otpModal.addEventListener('click', e => { if (e.target === otpModal) otpModal.classList.remove('active'); });

  // OTP auto-tab
  otpInputs.forEach((input, i) => {
    input.addEventListener('input', e => {
      const val = e.target.value.replace(/\D/g, '');
      e.target.value = val;
      if (val && i < otpInputs.length - 1) otpInputs[i + 1].focus();
    });
    input.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !input.value && i > 0) otpInputs[i - 1].focus();
    });
    input.addEventListener('paste', e => {
      e.preventDefault();
      const data = (e.clipboardData.getData('text') || '').replace(/\D/g, '').slice(0, 6);
      data.split('').forEach((ch, idx) => { if (otpInputs[idx]) otpInputs[idx].value = ch; });
      if (data.length > 0) otpInputs[Math.min(data.length, 5)].focus();
    });
  });

  // OTP Verify
  document.getElementById('otpVerifyBtn').addEventListener('click', () => {
    const code = Array.from(otpInputs).map(i => i.value).join('');
    if (code.length === 6) {
      otpModal.classList.remove('active');
      alert('Verification successful! Redirecting to dashboard...');
    }
  });

  // OTP Timer
  function startOtpTimer() {
    const timerEl = document.getElementById('otpTimer');
    let sec = 30;
    timerEl.textContent = `(${sec}s)`;
    const resendLink = document.getElementById('resendOtp');
    resendLink.style.pointerEvents = 'none';
    resendLink.style.opacity = '0.5';
    const interval = setInterval(() => {
      sec--;
      timerEl.textContent = sec > 0 ? `(${sec}s)` : '';
      if (sec <= 0) {
        clearInterval(interval);
        resendLink.style.pointerEvents = 'auto';
        resendLink.style.opacity = '1';
      }
    }, 1000);
  }

  document.getElementById('resendOtp').addEventListener('click', e => {
    e.preventDefault();
    startOtpTimer();
  });

  // ===== EMERGENCY BUTTON =====
  document.getElementById('emergencyBtn').addEventListener('click', () => {
    window.location.href = 'index.html#emergency';
  });

  // ===== PARTICLE CANVAS =====
  const canvas = document.getElementById('particleCanvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let w, h;
    const particles = [];
    const PARTICLE_COUNT = 50;

    function resize() {
      w = canvas.width = canvas.offsetWidth;
      h = canvas.height = canvas.offsetHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 2 + 0.5,
        dx: (Math.random() - 0.5) * 0.4,
        dy: (Math.random() - 0.5) * 0.4,
        opacity: Math.random() * 0.4 + 0.1,
      });
    }

    function drawParticles() {
      ctx.clearRect(0, 0, w, h);
      particles.forEach(p => {
        p.x += p.dx;
        p.y += p.dy;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(220, 20, 60, ${p.opacity})`;
        ctx.fill();
      });

      // Connect nearby particles
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(220, 20, 60, ${0.06 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(drawParticles);
    }
    drawParticles();
  }
});
