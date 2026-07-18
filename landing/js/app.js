/* ============================================================
   EcoTrace — Application Core & Authentication
   Supports email/password + GitHub/Google OAuth
   ============================================================ */

const BACKEND_URL = (
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1' ||
  window.location.protocol === 'file:'
) ? 'http://localhost:8000' : '';

/* ============================================================
   Scroll Progress Indicator
   ============================================================ */
const scrollProgressBar = document.getElementById('scrollProgress');
if (scrollProgressBar) {
  function updateScrollProgress() {
    const h = document.documentElement;
    const scrollTop = h.scrollTop || document.body.scrollTop;
    const scrollHeight = h.scrollHeight - h.clientHeight;
    const pct = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
    scrollProgressBar.style.width = pct + '%';
  }
  window.addEventListener('scroll', updateScrollProgress, { passive: true });
}

/* ============================================================
   Nav scroll state
   ============================================================ */
const nav = document.getElementById('nav');
if (nav) {
  const onScroll = () => nav.classList.toggle('is-scrolled', window.scrollY > 16);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

/* ============================================================
   Hamburger menu
   ============================================================ */
const hamburger = document.getElementById('hamburger');
const mobileNav = document.getElementById('mobileNav');
if (hamburger && mobileNav) {
  window.toggleMobileNav = function () {
    hamburger.classList.toggle('is-open');
    mobileNav.classList.toggle('is-open');
    document.body.style.overflow = mobileNav.classList.contains('is-open') ? 'hidden' : '';
  };
  window.closeMobileNav = function () {
    hamburger.classList.remove('is-open');
    mobileNav.classList.remove('is-open');
    document.body.style.overflow = '';
  };
}

/* ============================================================
   Tab switcher (quick start tabs)
   ============================================================ */
document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(x => x.classList.remove('is-active'));
    document.querySelectorAll('.tab__panel').forEach(p => p.classList.remove('is-active'));
    t.classList.add('is-active');
    const panel = document.querySelector(`[data-panel="${t.dataset.tab}"]`);
    if (panel) panel.classList.add('is-active');
  });
});

/* ============================================================
   Scroll reveal
   ============================================================ */
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
  });
}, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));

/* ============================================================
   Count-up animation
   ============================================================ */
const easeOut = (t) => 1 - Math.pow(1 - t, 3);
const countUp = (el) => {
  const target = parseFloat(el.dataset.count);
  const suffix = el.dataset.suffix || '';
  const duration = 1200;
  const start = performance.now();
  const tick = (now) => {
    const t = Math.min(1, (now - start) / duration);
    if (el.firstChild && el.firstChild.nodeType === 3) {
      el.firstChild.nodeValue = Math.round(target * easeOut(t)) + suffix;
    }
    if (t < 1) requestAnimationFrame(tick);
  };
  if (el.firstChild && el.firstChild.nodeType === 3) {
    requestAnimationFrame(tick);
  } else {
    el.insertBefore(document.createTextNode('0' + suffix), el.firstChild);
    requestAnimationFrame(tick);
  }
};
const countIO = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) { countUp(e.target); countIO.unobserve(e.target); }
  });
}, { threshold: 0.5 });
document.querySelectorAll('.stat__num[data-count]').forEach(el => countIO.observe(el));

/* ============================================================
   Auth Modal — open / close
   ============================================================ */
const authOverlay = document.getElementById('authOverlay');
const authError   = document.getElementById('authError');
const navAuthBtn  = document.getElementById('navAuthBtn');
const navUser     = document.getElementById('navUser');

window.openAuthModal = function () {
  if (authOverlay) {
    authOverlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
    if (authError) authError.classList.remove('is-visible');
  }
};

window.closeAuthModal = function () {
  if (authOverlay) {
    authOverlay.classList.remove('is-open');
    document.body.style.overflow = '';
  }
};

if (authOverlay) {
  authOverlay.addEventListener('click', (e) => { if (e.target === authOverlay) closeAuthModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAuthModal(); });
}

/* ============================================================
   Auth Modal — tab switcher (Sign In / Sign Up)
   ============================================================ */
window.switchAuthTab = function (tab) {
  const authTabs  = document.querySelectorAll('.auth-tab');
  const authForms = document.querySelectorAll('.auth-form');
  const title     = document.getElementById('authTitle');
  const subtitle  = document.getElementById('authSubtitle');
  if (authError) authError.classList.remove('is-visible');

  authTabs.forEach(t => t.classList.remove('is-active'));
  authForms.forEach(f => f.classList.remove('is-active'));

  if (tab === 'signin') {
    authTabs[0].classList.add('is-active');
    document.querySelector('[data-form="signin"]').classList.add('is-active');
    if (title)    title.textContent    = 'Welcome Back';
    if (subtitle) subtitle.textContent = 'Sign in to access your live dashboard';
  } else {
    authTabs[1].classList.add('is-active');
    document.querySelector('[data-form="signup"]').classList.add('is-active');
    if (title)    title.textContent    = 'Create Account';
    if (subtitle) subtitle.textContent = 'Join EcoTrace to start tracking your carbon';
  }
};

function showAuthError(msg) {
  if (authError) {
    authError.textContent = msg;
    authError.classList.add('is-visible');
  }
}

/* ============================================================
   Sign Up (email + password)
   ============================================================ */
window.handleSignUp = async function (e) {
  e.preventDefault();
  const name  = document.getElementById('signup-name').value.trim();
  const email = document.getElementById('signup-email').value.trim();
  const pw    = document.getElementById('signup-password').value;

  try {
    const res  = await fetch(`${BACKEND_URL}/api/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password: pw }),
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('ecotrace_token', data.access_token);
      closeAuthModal();
      await checkUserAuth();
      window.location.href = './dashboard.html';
    } else {
      showAuthError(data.detail || 'Sign up failed. Please try again.');
    }
  } catch {
    showAuthError('Could not reach the server. Please try again.');
  }
};

/* ============================================================
   Sign In (email + password)
   ============================================================ */
window.handleSignIn = async function (e) {
  e.preventDefault();
  const email = document.getElementById('signin-email').value.trim();
  const pw    = document.getElementById('signin-password').value;

  try {
    const body = new URLSearchParams();
    body.append('username', email);
    body.append('password', pw);

    const res  = await fetch(`${BACKEND_URL}/api/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('ecotrace_token', data.access_token);
      closeAuthModal();
      await checkUserAuth();
      window.location.href = './dashboard.html';
    } else {
      showAuthError(data.detail || 'Incorrect email or password.');
    }
  } catch {
    showAuthError('Could not reach the server. Please try again.');
  }
};

/* ============================================================
   OAuth — GitHub / Google
   ============================================================ */
window.socialAuth = function (provider) {
  window.location.href = `${BACKEND_URL}/login/${provider}`;
};

/* ============================================================
   Sign Out
   ============================================================ */
window.signOut = function () {
  localStorage.removeItem('ecotrace_token');
  updateAuthUI(null);
  if (window.location.pathname.includes('dashboard.html')) {
    window.location.href = './index.html';
  }
};

/* ============================================================
   Password visibility toggle
   ============================================================ */
window.togglePassword = function (inputId, btn) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
  } else {
    input.type = 'password';
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
  }
};

/* ============================================================
   Auth state check via /api/me
   ============================================================ */
window.checkUserAuth = async function () {
  const token = localStorage.getItem('ecotrace_token');
  if (!token) { updateAuthUI(null); return null; }

  try {
    const res = await fetch(`${BACKEND_URL}/api/me`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (res.ok) {
      const user = await res.json();
      updateAuthUI(user);
      return user;
    }
    localStorage.removeItem('ecotrace_token');
    updateAuthUI(null);
    return null;
  } catch {
    updateAuthUI(null);
    return null;
  }
};

/* ============================================================
   Nav UI — update based on auth state
   ============================================================ */
function updateAuthUI(user) {
  if (user) {
    if (navAuthBtn) navAuthBtn.style.display = 'none';
    if (navUser)    navUser.classList.add('is-visible');
    const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    const avatar   = document.getElementById('navUserAvatar');
    const nameSpan = document.getElementById('navUserName');
    if (avatar)   avatar.textContent   = initials;
    if (nameSpan) nameSpan.textContent = user.name.split(' ')[0];
  } else {
    if (navAuthBtn) navAuthBtn.style.display = '';
    if (navUser)    navUser.classList.remove('is-visible');
  }
}

/* ============================================================
   User dropdown toggle
   ============================================================ */
window.toggleUserDropdown = function () {
  const dropdown = document.getElementById('navUserDropdown');
  if (dropdown) dropdown.classList.toggle('is-open');
};

document.addEventListener('click', (e) => {
  const user     = document.getElementById('navUser');
  const dropdown = document.getElementById('navUserDropdown');
  if (user && !user.contains(e.target) && dropdown) {
    dropdown.classList.remove('is-open');
  }
});

/* ============================================================
   Particle system (shared by index + dashboard)
   ============================================================ */
window.initParticles = function (canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let w, h, particles = [];
  const count = 40;

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    w = canvas.width  = rect.width;
    h = canvas.height = rect.height;
  }
  function createParticle() {
    return {
      x: Math.random() * w, y: Math.random() * h,
      r: Math.random() * 2 + 0.5,
      dx: (Math.random() - 0.5) * 0.3, dy: (Math.random() - 0.5) * 0.3,
      alpha: Math.random() * 0.4 + 0.1,
      color: Math.random() > 0.5 ? '62,123,87' : '212,160,74',
    };
  }
  function init() { resize(); particles = []; for (let i = 0; i < count; i++) particles.push(createParticle()); }
  function draw() {
    ctx.clearRect(0, 0, w, h);
    particles.forEach(p => {
      p.x += p.dx; p.y += p.dy;
      if (p.x < 0 || p.x > w) p.dx *= -1;
      if (p.y < 0 || p.y > h) p.dy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.color},${p.alpha})`;
      ctx.fill();
    });
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(62,123,87,${0.08 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  init();
  window.addEventListener('resize', resize);
  draw();
};

/* ============================================================
   OAuth Callback — extract #token from redirect fragment.
   Runs synchronously before checkUserAuth so there's no
   flash of signed-out state on the dashboard page.
   ============================================================ */
(function handleOAuthCallback() {
  const params = new URLSearchParams(window.location.hash.slice(1));
  const token  = params.get('token');
  if (token) {
    localStorage.setItem('ecotrace_token', token);
    // Remove fragment so it never appears in logs or history
    window.history.replaceState({}, document.title, window.location.pathname);
    window.location.replace('./dashboard.html');
  }
})();

// Run auth check on every page load
checkUserAuth();
