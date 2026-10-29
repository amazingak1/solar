/**
 * Solar Vest — API Client
 * Handles communication with the FastAPI backend.
 * Supports auto-detection between local development and cloud deployments (Render).
 */

const DEFAULT_PROD_API = "https://solar-backend-b4nm.onrender.com";

function getApiBase() {
  const custom = localStorage.getItem("sv_api_url");
  if (custom) return custom.replace(/\/$/, "");
  
  const isLocal = window.location.hostname === "localhost" || 
                  window.location.hostname === "127.0.0.1" || 
                  window.location.protocol === "file:";
  
  return isLocal ? "http://localhost:8000" : (window.ENV_API_URL || DEFAULT_PROD_API);
}

function setCustomApiUrl(url) {
  if (url) {
    localStorage.setItem("sv_api_url", url.trim().replace(/\/$/, ""));
  } else {
    localStorage.removeItem("sv_api_url");
  }
}

function getToken() {
  return localStorage.getItem("sv_token");
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${getToken()}`,
  };
}

async function apiFetch(path, options = {}) {
  const base = getApiBase();
  const res = await fetch(`${base}${path}`, {
    headers: authHeaders(),
    ...options,
  });
  if (res.status === 401) {
    logout();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") return null;
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────
async function apiLogin(email, password) {
  const base = getApiBase();
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const res = await fetch(`${base}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

async function apiRegister(name, email, password, role) {
  const base = getApiBase();
  const res = await fetch(`${base}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, role }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

async function apiGetMe() {
  return apiFetch("/auth/me");
}

// ── Panels ────────────────────────────────────────────────────
async function apiGetPanels() {
  return apiFetch("/panels/");
}

async function apiCreatePanel(data) {
  return apiFetch("/panels/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

async function apiDeletePanel(panelId) {
  return apiFetch(`/panels/${panelId}`, { method: "DELETE" });
}

// ── Sensors ───────────────────────────────────────────────────
async function apiGetLiveReading(panelId) {
  return apiFetch(`/sensors/${panelId}/live`);
}

// ── Predictions ───────────────────────────────────────────────
async function apiPredict(panelId, month) {
  return apiFetch(`/predict/?panel_id=${panelId}&month=${month}`, {
    method: "POST",
  });
}

async function apiMonthlyForecast(panelId) {
  return apiFetch(`/predict/${panelId}/monthly`);
}

async function apiGetROI(panelId) {
  return apiFetch(`/predict/${panelId}/roi`);
}

// ── Investor ──────────────────────────────────────────────────
async function apiGetPortfolio() {
  return apiFetch("/investor/portfolio");
}
