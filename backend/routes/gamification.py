from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from database import get_db, User as DBUser, Badge as DBBadge
from sqlalchemy.orm import Session

router = APIRouter()

class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str

class UserStats(BaseModel):
    user_id: str
    points: int
    rank: str
    badges: List[Badge]
    level: int

# Badge definitions
BADGES = {
    "first_classification": Badge(
        id="first_class",
        name="First Step",
        description="Classify your first item",
        icon="🎯"
    ),
    "ten_classifications": Badge(
        id="ten_class",
        name="Active Recycler",
        description="Classify 10 items",
        icon="♻️"
    ),
    "fifty_classifications": Badge(
        id="fifty_class",
        name="Eco Warrior",
        description="Classify 50 items",
        icon="🌍"
    ),
    "hundred_classifications": Badge(
        id="hundred_class",
        name="Planet Protector",
        description="Classify 100 items",
        icon="🛡️"
    ),
}

# Rank system
RANKS = ["Novice", "Apprentice", "Expert", "Master", "Legendary"]

@router.post("/add-points/{user_id}/{points}")
async def add_points(user_id: str, points: int, db: Session = Depends(get_db)):
    """Add points to user and persist to DB (demo). Returns updated stats."""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        return {"error": "User not found", "user_id": user_id}

    try:
        user.points = (user.points or 0) + int(points)
        db.add(user)
        db.commit()
        # basic level/rank calculation (mirror gamification engine thresholds)
        thresholds = [0, 100, 300, 600, 1000, 1500]
        level = 1
        for i, t in enumerate(thresholds):
            if user.points >= t:
                level = i + 1
        ranks = ["Novice", "Apprentice", "Expert", "Master", "Legendary"]
        rank = ranks[min(level - 1, len(ranks) - 1)]
        return {"message": f"Added {points} points", "user_id": user_id, "points": user.points, "level": level, "rank": rank}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@router.get("/user-stats/{user_id}", response_model=UserStats)
async def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """Get user gamification stats from DB"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        return UserStats(user_id=user_id, points=0, rank="Novice", badges=[], level=1)

    # fetch badges (simple implementation)
    badge_rows = db.query(DBBadge).filter(DBBadge.user_id == user.id).all() if 'DBBadge' in globals() else []
    badges = []
    for b in badge_rows:
        badges.append({"id": b.id, "name": b.badge_name, "description": "", "icon": ""})

    # compute level/rank using thresholds
    thresholds = [0, 100, 300, 600, 1000, 1500]
    level = 1
    for i, t in enumerate(thresholds):
        if (user.points or 0) >= t:
            level = i + 1
    ranks = ["Novice", "Apprentice", "Expert", "Master", "Legendary"]
    rank = ranks[min(level - 1, len(ranks) - 1)]

    return UserStats(user_id=user.id, points=user.points or 0, rank=rank, badges=badges, level=level)


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Get top users leaderboard from real database"""
    top_users = db.query(DBUser).order_by(DBUser.points.desc()).limit(limit).all()
    leaderboard = []
    for i, user in enumerate(top_users):
        pts = user.points or 0
        thresholds = [0, 100, 300, 600, 1000, 1500]
        level = 1
        for j, t in enumerate(thresholds):
            if pts >= t:
                level = j + 1
        ranks = ["Novice", "Apprentice", "Expert", "Master", "Legendary"]
        rank_name = ranks[min(level - 1, len(ranks) - 1)]
        leaderboard.append({
            "rank": i + 1,
            "user": user.username,
            "points": pts,
            "level": level,
            "rank_name": rank_name,
        })
    return {"leaderboard": leaderboard}

@router.get("/badges")
async def get_all_badges():
    """Get all available badges"""
    return list(BADGES.values())

@router.get("/ranks")
async def get_ranks():
    """Get all rank levels"""
    return {"ranks": RANKS}
