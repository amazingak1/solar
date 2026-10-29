from fastapi import APIRouter, HTTPException, Depends, status
from app.database import get_db
from app.models.panel import PanelCreate, PanelOut, PanelUpdate, CITY_DEFAULTS
from app.services.auth_service import get_current_user, require_role
from app.models.user import Role
from datetime import datetime

router = APIRouter(prefix="/panels", tags=["Panels"])


def panel_to_out(doc: dict) -> PanelOut:
    return PanelOut(**{k: v for k, v in doc.items() if k != "hashed_password"})


@router.post("/", response_model=PanelOut, status_code=201)
async def create_panel(
    panel: PanelCreate,
    current_user: dict = Depends(require_role(Role.admin, Role.owner))
):
    db = get_db()
    city_info = CITY_DEFAULTS.get(panel.city, CITY_DEFAULTS["Delhi"])
    lat = panel.latitude or city_info["latitude"]
    lng = panel.longitude or city_info["longitude"]

    doc = {
        **panel.model_dump(),
        "latitude": lat,
        "longitude": lng,
        "owner_id": current_user["id"],
        "created_at": datetime.utcnow(),
    }
    result = await db.panels.insert_one(doc)
    doc["id"] = result.inserted_id
    return panel_to_out(doc)


@router.get("/", response_model=list[PanelOut])
async def list_panels(current_user: dict = Depends(get_current_user)):
    db = get_db()
    if current_user["role"] in ("admin", "investor"):
        panels = await db.panels.find({}).to_list(200)
    else:
        panels = await db.panels.find({"owner_id": current_user["id"]}).to_list(200)
    return [panel_to_out(p) for p in panels]


@router.get("/{panel_id}", response_model=PanelOut)
async def get_panel(panel_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    panel = await db.panels.find_one({"id": panel_id})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    if current_user["role"] != "admin" and panel["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return panel_to_out(panel)


@router.put("/{panel_id}", response_model=PanelOut)
async def update_panel(
    panel_id: str,
    updates: PanelUpdate,
    current_user: dict = Depends(require_role(Role.admin, Role.owner))
):
    db = get_db()
    panel = await db.panels.find_one({"id": panel_id})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    if current_user["role"] != "admin" and panel["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    await db.panels.update_one({"id": panel_id}, {"$set": update_data})
    updated = await db.panels.find_one({"id": panel_id})
    return panel_to_out(updated)


@router.delete("/{panel_id}", status_code=204)
async def delete_panel(
    panel_id: str,
    current_user: dict = Depends(require_role(Role.admin, Role.owner))
):
    db = get_db()
    panel = await db.panels.find_one({"id": panel_id})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    if current_user["role"] != "admin" and panel["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    await db.panels.delete_one({"id": panel_id})
