from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.services.auth_service import require_role
from app.models.user import Role

router = APIRouter(prefix="/investor", tags=["Investor"])


@router.get("/portfolio")
async def get_portfolio(current_user: dict = Depends(require_role(Role.owner, Role.investor, Role.admin))):
    """Get all panels and their latest predictions."""
    db = get_db()
    if current_user["role"] == "owner":
        panels = await db.panels.find({"owner_id": current_user["id"]}).to_list(200)
    else:
        panels = await db.panels.find({}).to_list(200)
    portfolio = []
    for panel in panels:
        panel_id = panel["id"]
        latest_pred = await db.predictions.find_one(
            {"panel_id": panel_id},
            sort=[("created_at", -1)]
        )
        portfolio.append({
            "panel_id": panel_id,
            "name": panel.get("name"),
            "city": panel.get("city"),
            "panel_type": panel.get("panel_type"),
            "num_panels": panel.get("num_panels"),
            "installation_cost": panel.get("installation_cost"),
            "latest_prediction": latest_pred.get("roi") if latest_pred else None,
        })
    return {"portfolio": portfolio, "total_panels": len(portfolio)}


@router.get("/panel/{panel_id}/report")
async def panel_report(
    panel_id: str,
    current_user: dict = Depends(require_role(Role.owner, Role.investor, Role.admin))
):
    """Full investment report for a specific panel."""
    db = get_db()
    panel = await db.panels.find_one({"id": panel_id})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    if current_user["role"] == "owner" and panel["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    predictions = await db.predictions.find(
        {"panel_id": panel_id},
        sort=[("created_at", -1)]
    ).limit(12).to_list(12)

    latest_reading = await db.sensor_readings.find_one(
        {"panel_id": panel_id},
        sort=[("timestamp", -1)]
    )

    return {
        "panel": {
            "id": panel_id,
            "name": panel.get("name"),
            "city": panel.get("city"),
            "area_m2": panel.get("area_m2"),
            "num_panels": panel.get("num_panels"),
            "panel_type": panel.get("panel_type"),
            "installation_cost": panel.get("installation_cost"),
            "tilt_angle": panel.get("tilt_angle"),
            "azimuth_angle": panel.get("azimuth_angle"),
        },
        "predictions": [{"month": p.get("month"), **p.get("roi", {})} for p in predictions],
        "latest_live_reading": latest_reading,
    }
