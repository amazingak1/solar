# 👥 Solar Vest — User Roles & Permissions

Solar Vest includes role-based access control (RBAC) across three distinct user roles: **Panel Owner**, **Investor**, and **Administrator**.

---

### Role Comparison Matrix

| Feature / Action | ☀️ Panel Owner (`owner@...`) | 💰 Investor (`investor@...`) | 🛡️ Admin (`admin@...`) |
|---|:---:|:---:|:---:|
| **Default User** | Arjun Sharma (`owner@solarvest.com`) | Priya Investments (`investor@solarvest.com`) | Admin User (`admin@solarvest.com`) |
| **Sidebar Badge** | Avatar `A` · `owner` (orange) | Avatar `P` · `investor` (green) | Avatar `A` · `admin` (purple) |
| **Asset Scope** | Only panels they own | **All panels across the platform** | **All panels across the platform** |
| **Overview & Stats Cards** | Stats for their own installations | Aggregated stats across the entire market | Aggregated system-wide stats |
| **Register New Panel (`+ Add Panel`)** | ✅ Allowed | ❌ Blocked (Read-only investor) | ✅ Allowed |
| **Delete / Edit Panels** | ✅ Only their own panels | ❌ Blocked | ✅ Any panel across all owners |
| **Run AI Energy Predictions** | ✅ For their own panels | ✅ For any asset on the platform | ✅ For any asset on the platform |
| **Investor View (Portfolio & ROI)** | ✅ Shows ROI for their own panels | ✅ Full cross-asset due diligence | ✅ Full cross-asset due diligence |
| **Live IoT Telemetry** | ✅ Live readings for their panels | ✅ Live readings for all panels | ✅ Live readings for all panels |

---

### Role Details & Capabilities

#### 1. ☀️ Panel Owner (`owner@solarvest.com` / `password123`)
* **Target User:** Rooftop solar owner or private plant operator.
* **Scope:** Restricted to panels they own.
* **Permissions:** Full asset lifecycle management:
  - Register new solar arrays via the UI (`+ Add Panel`).
  - Edit technical parameters (tilt angle, azimuth, panel type, capacity).
  - Delete retired or decommissioning panels.
  - Run AI generation predictions and review monthly energy yield & savings.

#### 2. 💰 Investor (`investor@solarvest.com` / `password123`)
* **Target User:** Clean energy fund manager, angel investor, or financial analyst.
* **Scope:** System-wide visibility across all assets and cities (Delhi, Bangalore, Jaipur, Mumbai, Hyderabad).
* **Permissions:** Financial analytics and due diligence (Read-Only):
  - Access the **Investor View** ranking all assets by 25-year ROI, payback period, and revenue.
  - Run AI generation predictions on any panel to assess yield potential.
  - Inspect live IoT sensor metrics (power, voltage, irradiance).
  - *Restricted:* Cannot create, modify, or delete physical panel records (`403 Forbidden`).

#### 3. 🛡️ Administrator (`admin@solarvest.com` / `password123`)
* **Target User:** Platform operator or system administrator.
* **Scope:** Complete, unrestricted access.
* **Permissions:**
  - View, manage, edit, and delete any panel across all accounts.
  - Full access to all prediction models and sensor feeds.
  - User and asset oversight.
