# ☀️ Solar Vest

> **IoT + ML platform for solar panel monitoring and ROI prediction.**  
> Backend: **FastAPI** · ML: **TensorFlow/Keras** · Storage: **Pure In-Memory Store** · Frontend: **Responsive Web Dashboard**

---

## About

Solar Vest is a full-stack system that:

1. **Monitors solar panels** — IoT sensor data (current, voltage, temperature, irradiance) via simulated physics-based feed or MQTT
2. **Predicts energy generation** — Keras neural network trained on physics-based data. Input: panel config + location. Output: monthly kWh
3. **Calculates investor ROI** — Predicted kWh × tariff rate → payback period, 10yr/25yr compounding ROI

All data is generated using real solar engineering formulas (GHI, tilt factor, temperature derating, degradation, and inflation curves).

---

## Public Cloud Deployment

### 1. Deploy Backend on Render (Free)

1. Sign up / log in to [Render](https://render.com).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository: `https://github.com/amazingak1/solar`.
4. Configure the service:
   - **Name:** `solar-backend` (or your choice)
   - **Environment:** `Python`
   - **Region:** `Oregon (US West)` or closest to you
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   - **Python Version:** Add environment variable `PYTHON_VERSION` = `3.11.9`
5. Click **Create Web Service**.
6. Once deployed, copy your Render URL: e.g. `https://solar-backend-xxxx.onrender.com`.

---

### 2. Deploy Frontend on Vercel (Free)

1. Sign up / log in to [Vercel](https://vercel.com).
2. Click **Add New** → **Project**.
3. Import your GitHub repository: `amazingak1/solar`.
4. In project configuration:
   - **Framework Preset:** `Other`
   - **Root Directory:** Edit and select `frontend` (or leave root since `vercel.json` is configured)
5. Click **Deploy**.
6. Open your live Vercel URL!
7. To connect your Vercel frontend to your Render backend:
   - Open browser developer tools Console on your Vercel site and run:
     ```javascript
     localStorage.setItem("sv_api_url", "https://your-backend.onrender.com");
     location.reload();
     ```
   - Or update `DEFAULT_PROD_API` in `frontend/src/api.js`.

---

## Local Development Quickstart

### Prerequisites

- **Python 3.11**
- **Git**

### Setup & Run

```bash
# 1. Clone repository
git clone https://github.com/amazingak1/solar.git
cd solar

# 2. Create virtual environment
py -3.11 -m venv .venv

# 3. Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run everything with one command
python run.py
```

This starts:
- **Frontend UI** → http://localhost:3000
- **Backend API** → http://localhost:8000 ([API Docs](http://localhost:8000/docs))
- **ML Microservice** → http://localhost:8001 ([API Docs](http://localhost:8001/docs))

### Default Accounts & Roles

| Feature / Action | ☀️ Panel Owner (`owner@...`) | 💰 Investor (`investor@...`) | 🛡️ Admin (`admin@...`) |
|---|:---:|:---:|:---:|
| **Default User** | Arjun Sharma (`owner@solarvest.com`) | Priya Investments (`investor@solarvest.com`) | Admin User (`admin@solarvest.com`) |
| **Password** | `password123` | `password123` | `password123` |
| **Sidebar Badge** | Avatar `A` · `owner` | Avatar `P` · `investor` | Avatar `A` · `admin` |
| **Asset Scope** | Only panels they own | **All panels across platform** | **All panels across platform** |
| **Register Panel (`+ Add Panel`)** | ✅ Allowed | ❌ Blocked (Read-only) | ✅ Allowed |
| **Delete / Edit Panels** | ✅ Only own panels | ❌ Blocked | ✅ Any panel |
| **AI Predictions** | ✅ Own panels | ✅ Any panel | ✅ Any panel |
| **Investor View Portfolio** | ✅ Own panels | ✅ Full cross-asset portfolio | ✅ Full cross-asset portfolio |

> See [ROLES.md](ROLES.md) for full role descriptions and permission boundaries.

> **Note:** In-memory database resets on every restart. These demo accounts and 2 sample panels are re-created automatically.

---

## API Reference

All endpoints return JSON. Authenticated endpoints require `Authorization: Bearer <token>` from `/auth/login`.

### Auth

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/auth/login` | `username=email&password=pass` (form-urlencoded) | Returns JWT token |
| POST | `/auth/register` | `{ name, email, password, role }` | Create account |
| GET | `/auth/me` | — | Get current user info |

### Panels (CRUD)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/panels/` | List panels (owner sees own, admin/investor sees all) |
| POST | `/panels/` | Create panel (owner/admin only) |
| GET | `/panels/{id}` | Get single panel |
| PUT | `/panels/{id}` | Update panel |
| DELETE | `/panels/{id}` | Delete panel |

**Create panel body:**
```json
{
  "name": "Rooftop Array",
  "city": "Delhi",
  "area_m2": 15.0,
  "num_panels": 12,
  "panel_type": "monocrystalline",
  "tilt_angle": 28.0,
  "azimuth_angle": 180.0,
  "installation_cost": 250000
}
```

Supported cities: Delhi, Mumbai, Bangalore, Chennai, Hyderabad, Kolkata, Jaipur, Ahmedabad.
If you don't provide `latitude`/`longitude`, they auto-fill from the city.

**Recommended tilt angles (India):**

| City | Tilt |
|---|---|
| Delhi | 28° |
| Mumbai | 19° |
| Bangalore | 13° |
| Chennai | 13° |
| Hyderabad | 17° |
| Kolkata | 22° |
| Jaipur | 27° |
| Ahmedabad | 23° |

### ML Predictions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/predict/?panel_id={id}&month={1-12}` | Predict kWh + ROI for one month |
| GET | `/predict/{id}/monthly` | 12-month forecast (all months) |
| GET | `/predict/{id}/roi` | ROI breakdown (25-year view) |

**Prediction response example:**
```json
{
  "panel_id": "...",
  "monthly_kwh": 5665.59,
  "monthly_revenue_inr": 39659.13,
  "annual_revenue_inr": 475909.56,
  "payback_years": 0.53,
  "roi_25yr_pct": 4659.10,
  "break_even_month": 7,
  "installation_cost": 250000.0
}
```

### Sensors (Simulated)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/sensors/{id}/live` | Latest reading (simulated if no MQTT) |
| GET | `/sensors/{id}/history` | Historical readings |
| POST | `/sensors/ingest` | Push a custom reading |

> Sensor data is **fully simulated** — it uses time-of-day (0W at night, peaks at 1pm), city-specific GHI data, and random noise to produce realistic-looking readings. No real IoT hardware is connected.

### Investor

| Method | Endpoint | Description |
|---|---|---|
| GET | `/investor/portfolio` | All panels + latest predictions (investor/admin only) |
| GET | `/investor/panel/{id}/report` | Full investment report for one panel |

---

## ML Model

- **Architecture**: Dense 128 → 64 → 32 → 1 (Keras)
- **Training data**: 10,000 **synthetic** records generated by `ml/data/dummy_data.py`
- **Accuracy**: R² ≈ 0.987, MAE ≈ 140 kWh/month
- **Inputs**: area, location, tilt, azimuth, panel type, count, month, GHI, temperature
- **Output**: predicted monthly kWh
- **ROI formula**: `monthly_kwh × ₹7/kWh` → payback period, 10yr/25yr returns

The training data is generated using real solar engineering formulas (tilt factor, temperature derating, azimuth factor, GHI by city/month) with ±5% noise — but it is **not measured from real panels**.

---

## Project Structure

```
solar-vest/
├── run.py                    ← Start everything with one command
├── requirements.txt          ← All Python dependencies
│
├── backend/                  ← FastAPI REST API (port 8000)
│   └── app/
│       ├── main.py           ← App entrypoint
│       ├── config.py         ← Settings (.env)
│       ├── database.py       ← In-memory DB + demo data seeding
│       ├── models/           ← Pydantic schemas (user, panel, reading)
│       ├── routers/          ← API endpoints (auth, panels, sensors, predictions, investors)
│       └── services/         ← Auth (JWT/bcrypt), ML client, MQTT listener
│
├── ml/                       ← Keras ML microservice (port 8001)
│   ├── app.py                ← FastAPI ML service (POST /predict)
│   ├── data/dummy_data.py    ← Synthetic data generator
│   └── model/
│       ├── train.py          ← Training script
│       ├── solar_model.keras ← Trained weights (generated by train.py)
│       └── scaler.pkl        ← Feature normalizer (generated by train.py)
│
├── frontend/                 ← Demo dashboard (plain HTML/CSS/JS)
│   ├── index.html
│   └── src/ (api.js, app.js, style.css)
│
└── mqtt_simulator/           ← Optional MQTT IoT simulator
    └── simulator.py
```

---

## For Frontend Developers

The backend is a **standard REST JSON API** with CORS enabled for all origins. Connect any frontend framework.

### Quick Integration

```javascript
const API = "http://localhost:8000";

// Login
const { access_token } = await fetch(`${API}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ username: "owner@solarvest.com", password: "password123" })
}).then(r => r.json());

// Use token for all requests
const headers = { Authorization: `Bearer ${access_token}` };

// Get panels
const panels = await fetch(`${API}/panels/`, { headers }).then(r => r.json());

// Get prediction
const pred = await fetch(`${API}/predict/?panel_id=${panels[0].id}&month=6`, {
  method: "POST", headers
}).then(r => r.json());

// Get live sensor data (simulated)
const live = await fetch(`${API}/sensors/${panels[0].id}/live`, { headers }).then(r => r.json());
```

See [`frontend/src/api.js`](frontend/src/api.js) for a complete reference you can copy.

---

## Optional: Real MongoDB

To persist data across restarts, create a free cluster at [MongoDB Atlas](https://mongodb.com/atlas) and add a `.env` file:

```env
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/solar_vest
SECRET_KEY=your_random_secret
```

The backend auto-detects MongoDB. If it can't connect, it silently falls back to in-memory.

---

## Role Permissions

| Action | owner | investor | admin |
|---|---|---|---|
| Login / Register | ✅ | ✅ | ✅ |
| List panels | own only | all | all |
| Create / Delete panel | ✅ | ❌ | ✅ |
| ML Prediction / ROI | ✅ | ✅ | ✅ |
| Live sensor data | ✅ | ✅ | ✅ |
| Investor portfolio | ❌ | ✅ | ✅ |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `DLL load failed` on Windows | Don't install `pandas` — project works without it |
| `Model not loaded` | Run `python ml/model/train.py` first |
| Empty panel list | Restart backend — in-memory DB reseeds on start |
| Port in use | `Get-Process python \| Stop-Process` (PowerShell) |
| CORS error | Check `API_BASE` URL matches your backend |

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, Pydantic, PyJWT, Passlib/bcrypt |
| ML | TensorFlow/Keras, scikit-learn, NumPy |
| Database | In-memory (mongomock) or MongoDB Atlas |
| IoT | MQTT (Paho) — optional |
| Frontend | Vanilla HTML/CSS/JS, Chart.js (demo only) |
