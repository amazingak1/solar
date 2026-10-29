/**
 * Solar Vest — Main App Logic
 * Handles routing, UI state, charts, and API interactions.
 */

let currentUser = null;
let panels = [];
let charts = {};
let liveInterval = null;

// ── Initialization ────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("sv_token");
  if (token) {
    initDashboard();
  }
  // Set current month in predict dropdown
  const m = new Date().getMonth() + 1;
  document.getElementById("predict-month").value = m;
});

// ── Auth ──────────────────────────────────────────────────────
function switchTab(tab) {
  document.getElementById("form-login").classList.toggle("hidden", tab !== "login");
  document.getElementById("form-register").classList.toggle("hidden", tab !== "register");
  document.getElementById("tab-login").classList.toggle("active", tab === "login");
  document.getElementById("tab-register").classList.toggle("active", tab === "register");
}

async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById("login-btn");
  const errEl = document.getElementById("login-error");
  errEl.classList.add("hidden");
  btn.disabled = true;
  btn.innerHTML = "<span>Signing in…</span>";
  try {
    const data = await apiLogin(
      document.getElementById("login-email").value,
      document.getElementById("login-password").value
    );
    localStorage.setItem("sv_token", data.access_token);
    await initDashboard();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "<span>Sign In</span>";
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const btn = document.getElementById("register-btn");
  const errEl = document.getElementById("reg-error");
  errEl.classList.add("hidden");
  btn.disabled = true;
  try {
    await apiRegister(
      document.getElementById("reg-name").value,
      document.getElementById("reg-email").value,
      document.getElementById("reg-password").value,
      document.getElementById("reg-role").value
    );
    // Auto login
    const data = await apiLogin(
      document.getElementById("reg-email").value,
      document.getElementById("reg-password").value
    );
    localStorage.setItem("sv_token", data.access_token);
    await initDashboard();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove("hidden");
  } finally {
    btn.disabled = false;
  }
}

function logout() {
  localStorage.removeItem("sv_token");
  currentUser = null;
  panels = [];
  if (liveInterval) clearInterval(liveInterval);
  Object.values(charts).forEach(c => c.destroy());
  charts = {};
  document.getElementById("page-login").classList.remove("hidden");
  document.getElementById("page-login").classList.add("active");
  document.getElementById("page-dashboard").classList.add("hidden");
}

// ── Dashboard Init ────────────────────────────────────────────
async function initDashboard() {
  try {
    currentUser = await apiGetMe();
  } catch {
    logout();
    return;
  }

  document.getElementById("page-login").classList.add("hidden");
  document.getElementById("page-dashboard").classList.remove("hidden");

  document.getElementById("sidebar-username").textContent = currentUser.name;
  document.getElementById("sidebar-role").textContent = currentUser.role;
  document.getElementById("user-avatar").textContent = currentUser.name.charAt(0).toUpperCase();

  // Keep investor tab visible for all roles
  const navInvestor = document.getElementById("nav-investor");
  if (navInvestor) {
    navInvestor.style.display = "";
  }

  await loadPanels();
  showView("overview");
}

// ── Navigation ────────────────────────────────────────────────
function showView(name) {
  document.querySelectorAll(".view").forEach(v => {
    v.classList.remove("active");
    v.classList.remove("hidden");
  });
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  const targetView = document.getElementById(`view-${name}`);
  if (targetView) {
    targetView.classList.remove("hidden");
    targetView.classList.add("active");
  }
  const navEl = document.getElementById(`nav-${name}`);
  if (navEl) navEl.classList.add("active");

  if (liveInterval) { clearInterval(liveInterval); liveInterval = null; }

  if (name === "overview") renderOverview();
  if (name === "panels") renderPanels();
  if (name === "predict") populatePredictSelects();
  if (name === "investor") loadInvestorPortfolio();
  if (name === "live") { populateLiveSelect(); startLivePolling(); }
}

// ── Panels ────────────────────────────────────────────────────
async function loadPanels() {
  try {
    panels = await apiGetPanels();
  } catch {
    panels = [];
  }
}

function renderPanels() {
  const container = document.getElementById("panels-list");
  if (!panels.length) {
    container.innerHTML = `<div class="loading-state">No panels yet. Click "+ Add Panel" to get started.</div>`;
    return;
  }
  container.innerHTML = panels.map(p => panelCard(p)).join("");
}

function panelCard(p) {
  const typeClass = { monocrystalline: "mono", polycrystalline: "poly", thin_film: "thin" }[p.panel_type] || "mono";
  const typeLabel = { monocrystalline: "Mono", polycrystalline: "Poly", thin_film: "Thin-film" }[p.panel_type] || p.panel_type;
  const cost = "₹" + Number(p.installation_cost).toLocaleString("en-IN");
  return `
    <div class="panel-card glass">
      <div class="panel-card-header">
        <span class="panel-name">${p.name}</span>
        <span class="panel-type-badge ${typeClass}">${typeLabel}</span>
      </div>
      <div class="panel-meta">
        <div class="panel-meta-row"><span>📍 City</span><span>${p.city}</span></div>
        <div class="panel-meta-row"><span>📐 Area</span><span>${p.area_m2} m² × ${p.num_panels} panels</span></div>
        <div class="panel-meta-row"><span>📐 Tilt</span><span>${p.tilt_angle}° / Az: ${p.azimuth_angle}°</span></div>
        <div class="panel-meta-row"><span>💰 Cost</span><span>${cost}</span></div>
      </div>
      <div class="panel-actions">
        <button onclick="quickPredict('${p.id}')">🤖 Predict</button>
        <button onclick="deletePanel('${p.id}')">🗑 Delete</button>
      </div>
    </div>`;
}

function openAddPanel() {
  document.getElementById("modal-add-panel").classList.remove("hidden");
}

function closeModal(e) {
  if (e.target === e.currentTarget)
    e.currentTarget.classList.add("hidden");
}

async function handleAddPanel(e) {
  e.preventDefault();
  const errEl = document.getElementById("panel-error");
  errEl.classList.add("hidden");
  try {
    const data = {
      name: document.getElementById("p-name").value,
      city: document.getElementById("p-city").value,
      area_m2: parseFloat(document.getElementById("p-area").value),
      num_panels: parseInt(document.getElementById("p-num").value),
      tilt_angle: parseFloat(document.getElementById("p-tilt").value),
      azimuth_angle: parseFloat(document.getElementById("p-azimuth").value),
      panel_type: document.getElementById("p-type").value,
      installation_cost: parseFloat(document.getElementById("p-cost").value),
    };
    const panel = await apiCreatePanel(data);
    panels.push(panel);
    document.getElementById("modal-add-panel").classList.add("hidden");
    renderPanels();
    updateStats();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove("hidden");
  }
}

async function deletePanel(id) {
  if (!confirm("Delete this panel?")) return;
  try {
    await apiDeletePanel(id);
    panels = panels.filter(p => p.id !== id);
    renderPanels();
    updateStats();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function quickPredict(panelId) {
  showView("predict");
  setTimeout(async () => {
    document.getElementById("predict-panel-select").value = panelId;
    await runPrediction();
  }, 100);
}

// ── Overview ─────────────────────────────────────────────────
function renderOverview() {
  updateStats();
  if (panels.length > 0) {
    renderMonthlyChart(panels[0].id);
    renderROIChart(panels[0].id);
  }
}

function updateStats() {
  document.getElementById("stat-panels").textContent = panels.length;
}

async function renderMonthlyChart(panelId) {
  try {
    const data = await apiMonthlyForecast(panelId);
    const labels = data.forecast.map(d => d.month);
    const values = data.forecast.map(d => d.monthly_kwh);

    if (charts.monthly) charts.monthly.destroy();
    const ctx = document.getElementById("chart-monthly").getContext("2d");
    charts.monthly = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Monthly kWh",
          data: values,
          backgroundColor: "rgba(245,166,35,0.7)",
          borderColor: "#f5a623",
          borderWidth: 1,
          borderRadius: 6,
        }]
      },
      options: chartOptions("kWh"),
    });

    // Update stats from forecast
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    document.getElementById("stat-kwh").textContent = avg.toFixed(0) + " kWh";
    document.getElementById("stat-revenue").textContent = "₹" + (avg * 7).toFixed(0);
  } catch (e) {
    console.warn("Monthly chart error:", e.message);
  }
}

async function renderROIChart(panelId) {
  try {
    const roi = await apiGetROI(panelId);
    document.getElementById("stat-roi").textContent = roi.roi_25yr_pct.toFixed(0) + "%";

    // Build realistic 25-year cumulative return curve with degradation and tariff escalation
    const labels = [];
    const cumulative = [];
    const breakeven = [];
    let cum = 0;
    const baseAnnual = roi.annual_revenue_inr;
    const cost = roi.installation_cost;

    for (let yr = 0; yr <= 25; yr++) {
      labels.push(`Yr ${yr}`);
      if (yr === 0) {
        cumulative.push(0);
        breakeven.push(cost);
      } else {
        // Solar panel degradation: ~0.6% reduction per year
        const degradation = Math.pow(1 - 0.006, yr - 1);
        // Grid tariff escalation: ~2.5% increase per year in energy value
        const tariffEscalation = Math.pow(1 + 0.025, yr - 1);
        // Year 12 inverter maintenance reserve (~8% of initial cost)
        const maintenance = (yr === 12) ? (cost * 0.08) : 0;

        const yrRevenue = (baseAnnual * degradation * tariffEscalation) - maintenance;
        cum += yrRevenue;
        cumulative.push(Math.round(cum));
        breakeven.push(cost);
      }
    }

    if (charts.roi) charts.roi.destroy();
    const ctx = document.getElementById("chart-roi").getContext("2d");
    charts.roi = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Cumulative Net Returns (₹)",
            data: cumulative,
            borderColor: "#00d4aa",
            backgroundColor: "rgba(0,212,170,0.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 2,
            pointHoverRadius: 5,
          },
          {
            label: "Initial Capital Cost (₹)",
            data: breakeven,
            borderColor: "#ff4757",
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
          }
        ]
      },
      options: {
        ...chartOptions("₹"),
        plugins: {
          legend: { labels: { color: "#7b8299", boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ₹${Number(ctx.parsed.y).toLocaleString("en-IN")}`
            }
          }
        }
      },
    });
  } catch (e) {
    console.warn("ROI chart error:", e.message);
  }
}

function chartOptions(unit) {
  return {
    responsive: true,
    plugins: {
      legend: { labels: { color: "#7b8299", boxWidth: 12 } },
      tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y.toFixed(1)} ${unit}` } }
    },
    scales: {
      x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#7b8299" } },
      y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#7b8299" } },
    },
  };
}

// ── Predict ───────────────────────────────────────────────────
function populatePredictSelects() {
  const sel1 = document.getElementById("predict-panel-select");
  sel1.innerHTML = panels.map(p => `<option value="${p.id}">${p.name} — ${p.city}</option>`).join("");
}

async function runPrediction() {
  const panelId = document.getElementById("predict-panel-select").value;
  const month = document.getElementById("predict-month").value;
  const out = document.getElementById("predict-output");
  if (!panelId) { alert("Please select a panel."); return; }
  out.innerHTML = `<div class="predict-placeholder"><div class="placeholder-icon">⏳</div><p>Running AI prediction…</p></div>`;
  try {
    const r = await apiPredict(panelId, month);
    out.innerHTML = `
      <h3 style="margin-bottom:16px">Prediction Results</h3>
      <div class="predict-result-grid">
        <div class="result-item">
          <div class="result-value">${r.monthly_kwh}</div>
          <div class="result-label">Monthly kWh</div>
        </div>
        <div class="result-item">
          <div class="result-value">₹${r.monthly_revenue_inr.toLocaleString("en-IN")}</div>
          <div class="result-label">Monthly Revenue</div>
        </div>
        <div class="result-item">
          <div class="result-value">${r.payback_years}y</div>
          <div class="result-label">Payback Period</div>
        </div>
        <div class="result-item">
          <div class="result-value" style="color:var(--success)">${r.roi_25yr_pct}%</div>
          <div class="result-label">ROI (25yr)</div>
        </div>
        <div class="result-item">
          <div class="result-value">${r.break_even_month}</div>
          <div class="result-label">Break-even Month</div>
        </div>
        <div class="result-item">
          <div class="result-value">₹${r.annual_revenue_inr.toLocaleString("en-IN")}</div>
          <div class="result-label">Annual Revenue</div>
        </div>
      </div>`;
  } catch (err) {
    out.innerHTML = `<div class="predict-placeholder"><div class="placeholder-icon">❌</div><p>${err.message}</p></div>`;
  }
}

async function runYearlyForecast() {
  const panelId = document.getElementById("predict-panel-select").value;
  if (!panelId) { alert("Please select a panel."); return; }
  const wrap = document.getElementById("forecast-chart-wrap");
  wrap.classList.remove("hidden");
  try {
    const data = await apiMonthlyForecast(panelId);
    if (charts.forecast) charts.forecast.destroy();
    const ctx = document.getElementById("chart-forecast").getContext("2d");
    charts.forecast = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.forecast.map(d => d.month),
        datasets: [{
          label: "Monthly kWh",
          data: data.forecast.map(d => d.monthly_kwh),
          borderColor: "#f5a623",
          backgroundColor: "rgba(245,166,35,0.1)",
          fill: true,
          tension: 0.4,
          pointBackgroundColor: "#f5a623",
          pointRadius: 5,
        }]
      },
      options: chartOptions("kWh"),
    });
  } catch (err) {
    wrap.innerHTML = `<p style="color:var(--danger);padding:24px">${err.message}</p>`;
  }
}

// ── Investor ──────────────────────────────────────────────────
async function loadInvestorPortfolio() {
  const container = document.getElementById("investor-portfolio");
  container.innerHTML = `<div class="loading-state">Loading portfolio…</div>`;
  try {
    const data = await apiGetPortfolio();
    if (!data.portfolio.length) {
      container.innerHTML = `<div class="loading-state">No panels in portfolio yet.</div>`;
      return;
    }
    container.innerHTML = data.portfolio.map(item => {
      const pred = item.latest_prediction;
      return `
        <div class="investor-card glass">
          <div class="panel-name">${item.name}</div>
          <div style="color:var(--text-muted);font-size:0.8rem;margin-bottom:8px">${item.city} · ${item.panel_type}</div>
          ${pred ? `
            <div class="roi-highlight">${pred.roi_25yr_pct?.toFixed(1) || "—"}%</div>
            <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:16px">25-Year ROI</div>
            <div class="investor-stat"><span>Monthly kWh</span><span>${pred.monthly_kwh} kWh</span></div>
            <div class="investor-stat"><span>Monthly Revenue</span><span>₹${pred.monthly_revenue_inr?.toLocaleString("en-IN")}</span></div>
            <div class="investor-stat"><span>Payback Period</span><span>${pred.payback_years} years</span></div>
            <div class="investor-stat"><span>Installation Cost</span><span>₹${Number(item.installation_cost).toLocaleString("en-IN")}</span></div>
          ` : `<div style="color:var(--text-muted);font-size:0.85rem">No prediction data yet. Run AI Predict first.</div>`}
        </div>`;
    }).join("");
  } catch (err) {
    container.innerHTML = `<div class="loading-state" style="color:var(--danger)">${err.message}</div>`;
  }
}

// ── Live Sensors ──────────────────────────────────────────────
function populateLiveSelect() {
  const sel = document.getElementById("live-panel-select");
  sel.innerHTML = panels.map(p => `<option value="${p.id}">${p.name} — ${p.city}</option>`).join("");
  if (panels.length) loadLiveData();
}

async function loadLiveData() {
  const panelId = document.getElementById("live-panel-select").value;
  if (!panelId) return;
  try {
    const r = await apiGetLiveReading(panelId);
    document.getElementById("live-current").textContent = r.current_amps != null ? r.current_amps.toFixed(2) : "—";
    document.getElementById("live-voltage").textContent = r.voltage_volts != null ? r.voltage_volts.toFixed(1) : "—";
    document.getElementById("live-power").textContent = r.power_watts != null ? r.power_watts.toFixed(1) : "—";
    document.getElementById("live-temp").textContent = r.temperature_celsius != null ? r.temperature_celsius.toFixed(1) : "—";
    document.getElementById("live-irr").textContent = r.irradiance_wm2 != null ? r.irradiance_wm2.toFixed(0) : "—";
    const ts = r.timestamp ? new Date(r.timestamp) : new Date();
    document.getElementById("live-time").textContent = ts.toLocaleTimeString();
    // Show simulated badge if applicable
    const simBadge = document.getElementById("live-sim-badge");
    if (simBadge) simBadge.style.display = r.simulated ? "inline-block" : "none";
  } catch(err) {
    console.warn("Live reading error:", err.message);
  }
}

function startLivePolling() {
  liveInterval = setInterval(loadLiveData, 5000);
}
