from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartbin.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    rank = Column(String, default="Novice")
    created_at = Column(DateTime, default=datetime.utcnow)

class Classification(Base):
    __tablename__ = "classifications"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    waste_type = Column(String)
    confidence = Column(Float)
    points_earned = Column(Integer)
    image_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    badge_name = Column(String)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    city = Column(String, nullable=True)
    society = Column(String, nullable=True)
    country = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)
