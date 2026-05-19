(function () {
  const script = document.currentScript;
  const requiredRole = script?.dataset.role;
  if (!requiredRole) return;

  const API_BASE = window.HEMOCHAIN_API_BASE || (window.location.hostname === "localhost" ? "http://localhost:5000" : window.location.origin);
  const TOKEN_KEY = "hemochain_auth_token";
  const ROLE_KEY = "hemochain_auth_role";
  const REFRESH_TOKEN_KEY = "hemochain_refresh_token";
  const USER_KEY = "hemochain_auth_user";
  const SESSION_KEY = "hemochain_super_admin_session";

  function stored(key) {
    return localStorage.getItem(key) || sessionStorage.getItem(key);
  }

  function clearAuth() {
    [localStorage, sessionStorage].forEach((store) => {
      [TOKEN_KEY, ROLE_KEY, REFRESH_TOKEN_KEY, USER_KEY, SESSION_KEY].forEach((key) => store.removeItem(key));
    });
  }

  function loginTarget() {
    return script?.dataset.login || (requiredRole === "admin" ? "admin/" : "auth.html");
  }

  function redirectToLogin() {
    window.location.href = loginTarget();
  }

  const token = stored(TOKEN_KEY);
  const role = stored(ROLE_KEY);
  if (!token || role !== requiredRole) {
    redirectToLogin();
    return;
  }

  async function loadDashboardData() {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/${requiredRole}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json().catch(() => ({}));

      if (response.status === 401 || response.status === 422) {
        clearAuth();
        redirectToLogin();
        return;
      }

      if (response.ok && data.success) {
        window.HEMOCHAIN_DASHBOARD_DATA = data;
        document.dispatchEvent(new CustomEvent("hemochain:dashboard-data", { detail: data }));
      }
    } catch (error) {
      console.warn("Hemo Chain API is unavailable. Static dashboard fallback remains visible.");
    }
  }

  async function logout() {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (error) {
      console.warn("Logout token revoke request failed; local session cleared.");
    } finally {
      clearAuth();
      redirectToLogin();
    }
  }

  if (requiredRole !== "admin") {
    document.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      if (button.textContent.trim().toLowerCase().includes("logout")) {
        event.preventDefault();
        logout();
      }
    });
  }

  loadDashboardData();
})();
