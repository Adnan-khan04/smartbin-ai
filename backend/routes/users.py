from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import get_db, User as DBUser
from sqlalchemy.orm import Session

router = APIRouter()

class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    avatar: Optional[str]
    bio: Optional[str]
    joined_date: str

class UserUpdate(BaseModel):
    username: Optional[str]
    bio: Optional[str]
    avatar: Optional[str]

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Get user profile from the database"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return UserProfile(
        user_id=user.id,
        username=user.username,
        email=user.email,
        avatar=None,
        bio=None,
        joined_date=user.created_at.date().isoformat()
    )

@router.put("/{user_id}")
async def update_user_profile(user_id: str, update: UserUpdate, db: Session = Depends(get_db)):
    """Update user profile in the database"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    if update.username:
        user.username = update.username
    db.commit()
    return {"message": "Profile updated successfully"}

@router.delete("/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Delete user account from database"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
