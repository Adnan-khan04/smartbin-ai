from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
import bcrypt
import uuid
import re
import logging

logger = logging.getLogger(__name__)

# DB imports
from database import SessionLocal, User as DBUser, get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 chars)")
    password: str = Field(..., min_length=3, description="Password (min 3 chars)")
    email: Optional[str] = Field(None)

    @validator('username')
    def validate_username(cls, v):
        v = v.strip()
        if len(v) < 3:
             raise ValueError('Username must be at least 3 characters')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 3:
             raise ValueError('Password must be at least 3 characters')
        return v

class LoginRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, description="Username")
    email: Optional[str] = Field(None, description="Email address")
    password: str = Field(..., min_length=3, description="Password")

    @validator('username', 'email')
    def validate_identifier(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v

class Token(BaseModel):
    access_token: str
    token_type: str

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # support token 'sub' being either username or email for compatibility
    user = db.query(DBUser).filter((DBUser.email == subject) | (DBUser.username == subject)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/register", response_model=Token)
async def register(user: User, db: Session = Depends(get_db)):
    """Register a new user (username + password). Email is optional; if omitted we create a placeholder."""
    try:
        # ensure username uniqueness
        existing = db.query(DBUser).filter((DBUser.username == user.username) | (DBUser.email == user.email) if user.email else (DBUser.username == user.username)).first()
        if existing:
            logger.warning(f"Registration failed: username/email already exists - {user.username}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already in use")

        # hash password
        pw_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # provide a placeholder email when not provided to keep schema consistent
        email_value = user.email if user.email else f"{user.username}@local.invalid"

        new_user = DBUser(
            id=uuid.uuid4().hex,
            username=user.username,
            email=email_value,
            password_hash=pw_hash
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"New user registered: {user.username}")

        # token subject is username (backend authoritative)
        access_token = create_access_token(data={"sub": new_user.username})
        user_info = {
            'user_id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'points': new_user.points,
            'level': new_user.level,
            'rank': new_user.rank,
            'joined_date': new_user.created_at.isoformat()
        }
        return {"access_token": access_token, "token_type": "bearer", "user": user_info}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed") 


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login user by verifying password and returning JWT. Accepts username OR email (field `username` or `email`)."""
    try:
        identifier = credentials.username or credentials.email
        if not identifier:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email required")
        
        # allow users to enter username or email
        user = db.query(DBUser).filter((DBUser.email == identifier) | (DBUser.username == identifier)).first()
        if not user:
            logger.warning(f"Login failed: user not found - {identifier}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

        if not bcrypt.checkpw(credentials.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            logger.warning(f"Login failed: invalid password - {identifier}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

        logger.info(f"User logged in: {user.username}")

        # return token with subject set to username
        access_token = create_access_token(data={"sub": user.username})
        user_info = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'points': user.points,
            'level': user.level,
            'rank': user.rank,
            'joined_date': user.created_at.isoformat()
        }
        return {"access_token": access_token, "token_type": "bearer", "user": user_info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed") 


@router.post("/logout")
async def logout():
    """Logout user (client should delete token)"""
    return {"message": "Logged out successfully"}


@router.get('/me')
async def me(current_user: DBUser = Depends(get_current_user)):
    """Return current authenticated user's public profile"""
    return {
        'user_id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'points': current_user.points,
        'level': current_user.level,
        'rank': current_user.rank,
        'joined_date': current_user.created_at.isoformat()
    }
