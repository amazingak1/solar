"""
Solar Vest — Pure In-Memory Database
=====================================
No MongoDB, no motor, no pymongo. All data lives in Python dicts keyed by uuid.
Data is reset on every server restart (by design for this prototype).
"""

import uuid
from datetime import datetime
from copy import deepcopy


# ── In-memory collections ─────────────────────────────────────────────────────
_store = {
    "users": {},           # id -> user_doc
    "panels": {},          # id -> panel_doc
    "sensor_readings": [], # list of dicts (append-only, queried by panel_id)
    "predictions": [],     # list of dicts (append-only, queried by panel_id)
}


def new_id() -> str:
    return str(uuid.uuid4())


# ── Collection wrappers (async-compatible thin API) ──────────────────────────

class _Collection:
    """Minimal async-compatible collection backed by in-memory _store."""

    def __init__(self, name: str):
        self._name = name

    def _data(self):
        return _store[self._name]

    # ── dict-style (users, panels) ──────────────────────────────────────────

    async def find_one(self, query: dict, sort=None) -> dict | None:
        data = self._data()
        if isinstance(data, dict):
            results = [deepcopy(v) for v in data.values() if _matches(v, query)]
        else:
            results = [deepcopy(v) for v in data if _matches(v, query)]
        if not results:
            return None
        if sort:
            key, direction = sort[0]
            results.sort(key=lambda x: x.get(key) or datetime.min, reverse=(direction == -1))
        return results[0]

    def find(self, query: dict, sort=None) -> "_CursorWrapper":
        return _CursorWrapper(self._name, query, sort)

    async def insert_one(self, doc: dict) -> "_InsertResult":
        doc = deepcopy(doc)
        doc_id = doc.get("id") or new_id()
        doc["id"] = doc_id
        data = self._data()
        if isinstance(data, dict):
            data[doc_id] = doc
        else:
            data.append(doc)
        return _InsertResult(doc_id)

    async def insert_many(self, docs: list) -> "_InsertManyResult":
        ids = []
        for doc in docs:
            result = await self.insert_one(doc)
            ids.append(result.inserted_id)
        return _InsertManyResult(ids)

    async def update_one(self, query: dict, update: dict):
        data = self._data()
        items = data.values() if isinstance(data, dict) else data
        for item in items:
            if _matches(item, query):
                if "$set" in update:
                    item.update(update["$set"])
                break

    async def delete_one(self, query: dict):
        data = self._data()
        if isinstance(data, dict):
            for k, v in list(data.items()):
                if _matches(v, query):
                    del data[k]
                    break
        else:
            for i, v in enumerate(data):
                if _matches(v, query):
                    data.pop(i)
                    break

    async def count_documents(self, query: dict) -> int:
        data = self._data()
        items = data.values() if isinstance(data, dict) else data
        return sum(1 for v in items if _matches(v, query))


class _CursorWrapper:
    def __init__(self, name, query, sort):
        self._name = name
        self._query = query
        self._sort = sort
        self._skip_n = 0
        self._limit_n = None

    def _items(self):
        data = _store[self._name]
        items = list(data.values()) if isinstance(data, dict) else list(data)
        results = [deepcopy(v) for v in items if _matches(v, self._query)]
        if self._sort:
            key, direction = self._sort[0]
            results.sort(key=lambda x: x.get(key) or datetime.min, reverse=(direction == -1))
        if self._skip_n:
            results = results[self._skip_n:]
        if self._limit_n is not None:
            results = results[:self._limit_n]
        return results

    def skip(self, n: int):
        self._skip_n = n
        return self

    def limit(self, n: int):
        self._limit_n = n
        return self

    async def to_list(self, length=None) -> list:
        results = self._items()
        if length is not None:
            results = results[:length]
        return results


class _InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _InsertManyResult:
    def __init__(self, inserted_ids):
        self.inserted_ids = inserted_ids


def _matches(doc: dict, query: dict) -> bool:
    """Simple query matcher — supports equality and $or."""
    for key, val in query.items():
        if key == "$or":
            if not any(_matches(doc, sub) for sub in val):
                return False
        else:
            if doc.get(key) != val:
                return False
    return True


# ── Database object ───────────────────────────────────────────────────────────

class _Database:
    @property
    def users(self):
        return _Collection("users")

    @property
    def panels(self):
        return _Collection("panels")

    @property
    def sensor_readings(self):
        return _Collection("sensor_readings")

    @property
    def predictions(self):
        return _Collection("predictions")


_db = _Database()


def get_db() -> _Database:
    return _db


# ── Seed data ─────────────────────────────────────────────────────────────────

async def seed_demo_data():
    from app.services.auth_service import hash_password

    db = get_db()
    if await db.users.count_documents({}) > 0:
        return  # already seeded

    # Create users
    owner_id = new_id()
    investor_id = new_id()
    admin_id = new_id()

    now = datetime.utcnow()

    await db.users.insert_one({
        "id": owner_id,
        "email": "owner@solarvest.com",
        "hashed_password": hash_password("password123"),
        "name": "Arjun Sharma",
        "role": "owner",
        "created_at": now,
    })
    await db.users.insert_one({
        "id": investor_id,
        "email": "investor@solarvest.com",
        "hashed_password": hash_password("password123"),
        "name": "Priya Investments",
        "role": "investor",
        "created_at": now,
    })
    await db.users.insert_one({
        "id": admin_id,
        "email": "admin@solarvest.com",
        "hashed_password": hash_password("password123"),
        "name": "Admin User",
        "role": "admin",
        "created_at": now,
    })

    # Create panels owned by owner_id with realistic panel specs (1.7 - 2.0 m² per panel)
    panels = [
        {
            "name": "Delhi Rooftop Solar Array",
            "owner_id": owner_id,
            "city": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "area_m2": 1.8,
            "num_panels": 12,
            "panel_type": "monocrystalline",
            "tilt_angle": 28.5,
            "azimuth_angle": 182.0,
            "installation_cost": 210000.0,
            "created_at": now,
        },
        {
            "name": "Bangalore Tech Park Array",
            "owner_id": owner_id,
            "city": "Bangalore",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "area_m2": 1.9,
            "num_panels": 16,
            "panel_type": "polycrystalline",
            "tilt_angle": 12.5,
            "azimuth_angle": 178.0,
            "installation_cost": 285000.0,
            "created_at": now,
        },
        {
            "name": "Jaipur Industrial Solar Farm",
            "owner_id": owner_id,
            "city": "Jaipur",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "area_m2": 2.0,
            "num_panels": 24,
            "panel_type": "monocrystalline",
            "tilt_angle": 26.0,
            "azimuth_angle": 175.0,
            "installation_cost": 420000.0,
            "created_at": now,
        },
        {
            "name": "Mumbai Warehouse Rooftop",
            "owner_id": owner_id,
            "city": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "area_m2": 1.7,
            "num_panels": 10,
            "panel_type": "thin_film",
            "tilt_angle": 10.0,
            "azimuth_angle": 190.0,
            "installation_cost": 175000.0,
            "created_at": now,
        },
        {
            "name": "Hyderabad Residential Array",
            "owner_id": owner_id,
            "city": "Hyderabad",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "area_m2": 1.8,
            "num_panels": 8,
            "panel_type": "polycrystalline",
            "tilt_angle": 17.0,
            "azimuth_angle": 180.0,
            "installation_cost": 145000.0,
            "created_at": now,
        },
    ]
    for p in panels:
        await db.panels.insert_one(p)

    print("Seeded 3 users and 5 panels. Login: owner@solarvest.com / password123")


# ── Lifecycle hooks ───────────────────────────────────────────────────────────

async def connect_db():
    await seed_demo_data()
    print("In-memory database ready.")


async def close_db():
    pass  # nothing to close
