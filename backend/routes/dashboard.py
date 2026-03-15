from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from database import get_db, Classification, User as DBUser
import jwt
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

# CO2 savings per item (kg) - approximate values
CO2_PER_ITEM = {
    "plastic": 0.5,
    "paper": 0.3,
    "metal": 1.2,
    "organic": 0.2,
}

# Weight per item (kg) - approximate
WEIGHT_PER_ITEM = {
    "plastic": 0.05,
    "paper": 0.1,
    "metal": 0.15,
    "organic": 0.2,
}

class ImpactData(BaseModel):
    total_items_recycled: int
    co2_saved: float
    plastic_recycled: float
    paper_recycled: float
    metal_recycled: float
    organic_waste: float
    last_updated: str

def _get_user_from_token(request: Request, db: Session):
    """Extract user from Bearer token, return None if not authenticated."""
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    try:
        token = auth.split(" ", 1)[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        return db.query(DBUser).filter(DBUser.username == username).first()
    except Exception:
        return None

@router.get("/impact/{user_id}", response_model=ImpactData)
async def get_user_impact(user_id: str, db: Session = Depends(get_db)):
    """Get user's environmental impact calculated from real classification history."""
    rows = db.query(Classification).filter(Classification.user_id == user_id).all()

    counts = {"plastic": 0, "paper": 0, "metal": 0, "organic": 0}
    for r in rows:
        wt = (r.waste_type or "").lower()
        if wt in counts:
            counts[wt] += 1

    total = sum(counts.values())
    co2 = sum(counts[wt] * CO2_PER_ITEM.get(wt, 0.3) for wt in counts)
    plastic_kg = counts["plastic"] * WEIGHT_PER_ITEM["plastic"]
    paper_kg = counts["paper"] * WEIGHT_PER_ITEM["paper"]
    metal_kg = counts["metal"] * WEIGHT_PER_ITEM["metal"]
    organic_kg = counts["organic"] * WEIGHT_PER_ITEM["organic"]

    return ImpactData(
        total_items_recycled=total,
        co2_saved=round(co2, 3),
        plastic_recycled=round(plastic_kg, 3),
        paper_recycled=round(paper_kg, 3),
        metal_recycled=round(metal_kg, 3),
        organic_waste=round(organic_kg, 3),
        last_updated=datetime.now().isoformat()
    )

@router.get("/me/impact", response_model=ImpactData)
async def get_my_impact(request: Request, db: Session = Depends(get_db)):
    """Get authenticated user's environmental impact."""
    user = _get_user_from_token(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await get_user_impact(user.id, db)

@router.get("/global-impact")
async def get_global_impact(db: Session = Depends(get_db)):
    """Get global environmental impact aggregated from all users."""
    rows = db.query(Classification).all()
    counts = {"plastic": 0, "paper": 0, "metal": 0, "organic": 0}
    for r in rows:
        wt = (r.waste_type or "").lower()
        if wt in counts:
            counts[wt] += 1

    total = sum(counts.values())
    co2 = sum(counts[wt] * CO2_PER_ITEM.get(wt, 0.3) for wt in counts)
    active_users = db.query(DBUser).count()

    return {
        "total_items_recycled": total,
        "total_co2_saved": round(co2, 3),
        "active_users": active_users,
        "total_plastic_recycled": round(counts["plastic"] * WEIGHT_PER_ITEM["plastic"], 3),
        "total_paper_recycled": round(counts["paper"] * WEIGHT_PER_ITEM["paper"], 3),
        "total_metal_recycled": round(counts["metal"] * WEIGHT_PER_ITEM["metal"], 3),
        "last_updated": datetime.now().isoformat()
    }

@router.get("/history/{user_id}")
async def get_user_history(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get user's classification history (from DB)"""
    rows = db.query(Classification).filter(Classification.user_id == user_id).order_by(Classification.created_at.desc()).limit(limit).all()
    history = []
    for r in rows:
        history.append({
            "id": r.id,
            "waste_type": r.waste_type,
            "points_earned": r.points_earned,
            "confidence": r.confidence,
            "timestamp": r.created_at.isoformat(),
            "image_path": r.image_path
        })
    return {"user_id": user_id, "history": history}

@router.get("/me/history")
async def get_my_history(request: Request, limit: int = 20, db: Session = Depends(get_db)):
    """Get authenticated user's classification history."""
    user = _get_user_from_token(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await get_user_history(user.id, limit, db)
